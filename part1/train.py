"""Part 1 training: train loop, eval, test inference for T5 fine-tune."""

import argparse
import bisect
import gc
import os
import re
import signal
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from pathlib import Path

import torch
import torch.nn as nn


# ── Graceful stop ────────────────────────────────────────────────────────
# Two mechanisms:
#   1. SIGTERM handler (e.g. `kill <pid>`) — sets flag, current epoch finishes
#   2. Stop file (e.g. `touch STOP`) — checked between epochs and between configs
# Both allow the current epoch to complete, save checkpoint, then exit cleanly.

_STOP_REQUESTED = False
STOP_FILE = Path("STOP")


def _handle_sigterm(signum, frame):
    global _STOP_REQUESTED
    _STOP_REQUESTED = True
    print("\nSIGTERM received — finishing current epoch then stopping gracefully...")


signal.signal(signal.SIGTERM, _handle_sigterm)


def stop_requested():
    """Check if a graceful stop has been requested (signal or stop file)."""
    global _STOP_REQUESTED
    if _STOP_REQUESTED:
        return True
    if STOP_FILE.exists():
        _STOP_REQUESTED = True
        print(f"\nStop file detected ({STOP_FILE}) — stopping gracefully...")
        return True
    return False
from tqdm import tqdm

from part1.data import PAD_IDX, _TOKENIZER, load_t5_data
from part1.model import (
    initialize_model,
    load_model_from_checkpoint,
    load_training_state,
    save_model,
    save_training_state,
)
from part1.model_flightdb import FlightSQLVocab, T5ForFlightSQL, T5ForFlightSQLWithMLP
from src.wandb_utils import (
    end_run,
    log_epoch_metrics,
    log_extra_params,
    log_model_artifact,
    setup_run,
)
from src.utils.system_metrics import collect_hardware_info, collect_system_metrics
from t5_utils import initialize_optimizer_and_scheduler
from utils import compute_metrics, save_queries_and_records, set_random_seeds

def _make_criterion(cfg):
    """Build loss function from config, with optional label smoothing."""
    ls = getattr(cfg, "label_smoothing", 0.0)
    if cfg.loss_fn == "cross_entropy":
        return nn.CrossEntropyLoss(label_smoothing=ls)
    raise ValueError(f"Unknown loss_fn: {cfg.loss_fn}")


def _amp_context(use_amp, device):
    """Return bf16 autocast context if AMP enabled and on CUDA, else no-op."""
    if use_amp and 'cuda' in str(device):
        return torch.amp.autocast('cuda', dtype=torch.bfloat16)
    return nullcontext()


def cleanup_vram():
    """Force-release all GPU memory between training runs.

    Clears all CUDA tensors from the current process, including any
    leaked references from crashed training runs.
    """
    # Force-clear all local frames that might hold model/optimizer refs
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        # Nuclear option: reset CUDA memory allocator state
        torch.cuda.reset_accumulated_memory_stats()


def auto_batch_size(cfg, model, train_loader, device, target_vram_pct=0.85):
    """Try to find a batch size that fills ~target_vram_pct of GPU memory.

    Strategy: run a single forward+backward pass with increasing batch sizes.
    Returns the largest batch size that fits, or falls back to cfg.batch_size.
    """
    if not torch.cuda.is_available():
        return cfg.batch_size

    total_vram = torch.cuda.get_device_properties(0).total_memory
    target_bytes = total_vram * target_vram_pct

    # Get one batch to know sequence length
    sample_batch = next(iter(train_loader))
    seq_len_enc = sample_batch[0].shape[1]
    seq_len_dec = sample_batch[2].shape[1]

    criterion = _make_criterion(cfg)
    best_bs = cfg.batch_size

    # Try doubling from current batch size
    candidates = [cfg.batch_size]
    bs = cfg.batch_size * 2
    while bs <= 256:
        candidates.append(bs)
        bs *= 2

    # For restricted-vocab models, probe with the inner HF model to avoid
    # remap_targets failing on random synthetic data.
    if isinstance(model, T5ForFlightSQL):
        probe_model = model.model
    else:
        probe_model = model

    use_amp = getattr(cfg, 'use_amp', False)
    for bs in candidates:
        try:
            cleanup_vram()
            # Synthetic batch
            enc_in = torch.randint(0, 100, (bs, seq_len_enc), device=device)
            enc_mask = torch.ones(bs, seq_len_enc, dtype=torch.long, device=device)
            dec_in = torch.randint(0, 100, (bs, seq_len_dec), device=device)
            dec_tgt = torch.randint(0, 100, (bs, seq_len_dec), device=device)

            with _amp_context(use_amp, device):
                logits = probe_model(
                    input_ids=enc_in,
                    attention_mask=enc_mask,
                    decoder_input_ids=dec_in,
                )["logits"]
                non_pad = dec_tgt != PAD_IDX
                loss = criterion(logits[non_pad], dec_tgt[non_pad])
            loss.backward()

            used = torch.cuda.memory_allocated()
            del enc_in, enc_mask, dec_in, dec_tgt, loss
            cleanup_vram()

            if used < target_bytes:
                best_bs = bs
            else:
                break
        except (RuntimeError, Exception):
            # OOM or other error — use previous best
            del enc_in, enc_mask, dec_in, dec_tgt
            cleanup_vram()
            break

    probe_model.zero_grad(set_to_none=True)
    cleanup_vram()
    return best_bs


# ── Helpers ─────────────────────────────────────────────────────────────

def _forward_and_loss(model, encoder_input, encoder_mask, decoder_input,
                      decoder_targets, criterion):
    """Compute logits and loss, dispatching to restricted vocab when applicable."""
    if isinstance(model, T5ForFlightSQL):
        logits = model.restricted_forward(encoder_input, encoder_mask, decoder_input)
        remapped = model.remap_targets(decoder_targets)
        non_pad = decoder_targets != PAD_IDX
        loss = criterion(logits[non_pad], remapped[non_pad])
    else:
        logits = model(
            input_ids=encoder_input,
            attention_mask=encoder_mask,
            decoder_input_ids=decoder_input,
        )["logits"]
        non_pad = decoder_targets != PAD_IDX
        loss = criterion(logits[non_pad], decoder_targets[non_pad])
    return loss, non_pad


# ── Shared generation helper ────────────────────────────────────────────

def _generate_predictions(model, loader, max_new_tokens, num_beams, device,
                          min_new_tokens=None, length_penalty=None,
                          early_stopping=True, use_amp=False):
    """Run model.generate on every batch; return list of decoded strings."""
    all_preds = []
    gen_kwargs = dict(
        max_new_tokens=max_new_tokens,
        num_beams=num_beams,
        early_stopping=early_stopping if num_beams > 1 else False,
        decoder_start_token_id=32099,  # <extra_id_0>, matches training BOS
    )
    if min_new_tokens is not None and min_new_tokens > 0:
        gen_kwargs["min_new_tokens"] = min_new_tokens
    if length_penalty is not None:
        gen_kwargs["length_penalty"] = length_penalty
    # Constrained decoding for restricted vocab models
    if isinstance(model, T5ForFlightSQL):
        gen_kwargs["prefix_allowed_tokens_fn"] = model.vocab.get_prefix_allowed_tokens_fn()
        gen_model = model.model  # inner HF model
    else:
        gen_model = model
    with torch.inference_mode(), _amp_context(use_amp, device):
        for batch in tqdm(loader):
            encoder_input = batch[0].to(device)
            encoder_mask = batch[1].to(device)
            outputs = gen_model.generate(
                input_ids=encoder_input,
                attention_mask=encoder_mask,
                **gen_kwargs,
            )
            preds = _TOKENIZER.batch_decode(outputs, skip_special_tokens=True)
            preds = [re.sub(r'(?<=[a-zA-Z0-9_)])\s*,\s*', ' , ', s) for s in preds]
            all_preds.extend(preds)
    return all_preds


# ── Training ────────────────────────────────────────────────────────────────

def _collect_async_sql(pending, cfg, ckpt_dir, model, best_val, best_metrics,
                       epochs_since_improvement, optimizer):
    """Collect results from a background SQL future; log, checkpoint, early-stop.

    Returns (best_val, best_metrics, epochs_since_improvement, should_stop).
    """
    future, p_epoch, p_tr_loss, p_dev_loss, p_avg_grad_norm, p_lr, \
        p_train_epoch_seconds, p_train_tokens, p_epoch_gpu_end, p_epoch_start, train_start = pending

    record_f1, record_em, sql_em, error_rate = future.result()
    epoch_time = time.time() - p_epoch_start
    wall_clock = time.time() - train_start

    print(f"Epoch {p_epoch}: F1 = {record_f1:.4f}, "
          f"EM = {record_em:.4f}, SQL_EM = {sql_em:.4f}, err = {error_rate*100:.1f}%")

    log_epoch_metrics({
        "epoch": p_epoch,
        "train_loss": p_tr_loss,
        "dev_loss": p_dev_loss,
        "record_f1": record_f1,
        "record_em": record_em,
        "sql_em": sql_em,
        "error_rate": error_rate,
        "gradient_norm": p_avg_grad_norm,
        "lr": p_lr,
    }, step=p_epoch)

    log_epoch_metrics({
        "timing/epoch_seconds": epoch_time,
        "timing/wall_clock_seconds": wall_clock,
        "timing/train_epoch_seconds": p_train_epoch_seconds,
        "timing/train_tokens_per_sec": p_train_tokens / p_train_epoch_seconds if p_train_epoch_seconds > 0 else 0,
    }, step=p_epoch)

    tol = getattr(cfg, 'patience_tolerance', 0.0)
    improved = (record_f1 > best_val + tol) if cfg.checkpointing.mode == "max" else (record_f1 < best_val - tol)
    log_epoch_metrics({
        "tracking/best_record_f1": record_f1 if improved else best_val,
        "tracking/epochs_since_improvement": 0 if improved else epochs_since_improvement + 1,
    }, step=p_epoch)

    if improved:
        best_val = record_f1
        best_metrics = {
            "record_f1": record_f1, "record_em": record_em,
            "sql_em": sql_em, "error_rate": error_rate,
        }
        epochs_since_improvement = 0
        if cfg.checkpointing.enabled and cfg.checkpointing.save_best:
            save_model(ckpt_dir, model, best=True,
                       best_filename=cfg.checkpointing.best_filename,
                       last_filename=cfg.checkpointing.last_filename)
    else:
        epochs_since_improvement += 1

    should_stop = (cfg.patience_epochs > 0 and epochs_since_improvement >= cfg.patience_epochs)
    if should_stop:
        print(f"Early stopping at epoch {p_epoch} (patience={cfg.patience_epochs})")

    return best_val, best_metrics, epochs_since_improvement, should_stop


def train(cfg, model, train_loader, dev_loader, optimizer, scheduler, run_dir,
          start_epoch=0, best_val=None, epochs_since_improvement=0):
    if best_val is None:
        best_val = -1 if cfg.checkpointing.mode == "max" else float("inf")
    best_metrics = {}
    ckpt_dir = str(run_dir / "checkpoints")
    train_start = time.time()
    epoch_times = []
    device = cfg.device

    gt_sql_path = "data/dev.sql"
    gt_record_path = "records/ground_truth_dev.pkl"

    global_step = start_epoch * len(train_loader)
    _interrupted = False
    _pred_cache = {}
    _sql_pool = ThreadPoolExecutor(max_workers=1)
    _pending_list = []  # background SQL futures + metadata
    try:
      for epoch in range(start_epoch, cfg.num_epochs):
        # Non-blocking: collect any completed background SQL results
        _should_stop = False
        while _pending_list and _pending_list[0][0].done():
            p = _pending_list.pop(0)
            best_val, best_metrics, epochs_since_improvement, _should_stop = _collect_async_sql(
                p, cfg, ckpt_dir, model, best_val, best_metrics,
                epochs_since_improvement, optimizer,
            )
            if _should_stop:
                break
        if _should_stop:
            break

        epoch_start = time.time()
        train_t0 = time.time()
        tr_loss, avg_grad_norm, train_tokens, global_step = train_epoch(
            cfg, model, train_loader, optimizer, scheduler, device, global_step
        )
        train_epoch_seconds = time.time() - train_t0

        # ── Evaluate every N epochs (and always on the last epoch) ──
        is_last_epoch = (epoch == cfg.num_epochs - 1)
        should_eval = is_last_epoch or ((epoch + 1) % cfg.eval_every_n_epochs == 0)

        if should_eval:
            dev_loss, all_preds = eval_epoch_gpu(cfg, model, dev_loader, device, is_final=is_last_epoch)
            epoch_gpu_end = time.time()

            # Epoch-specific paths to avoid file conflicts during overlap
            model_sql_path = str(run_dir / f"dev_pred_e{epoch}.sql")
            model_record_path = str(run_dir / f"dev_pred_e{epoch}.pkl")

            if is_last_epoch:
                # Drain all pending SQL before final sync eval
                for p in _pending_list:
                    best_val, best_metrics, epochs_since_improvement, _ = _collect_async_sql(
                        p, cfg, ckpt_dir, model, best_val, best_metrics,
                        epochs_since_improvement, optimizer,
                    )
                _pending_list.clear()
                # Last epoch: run SQL synchronously (no next epoch to overlap with)
                record_f1, record_em, sql_em, error_rate = eval_epoch_sql(
                    all_preds, cfg, gt_sql_path, model_sql_path,
                    gt_record_path, model_record_path, _pred_cache,
                )
                epoch_time = time.time() - epoch_start
                epoch_times.append(epoch_time)
                wall_clock = time.time() - train_start

                print(f"Epoch {epoch}: train loss = {tr_loss:.4f}, dev loss = {dev_loss:.4f}")
                print(f"Epoch {epoch}: F1 = {record_f1:.4f}, "
                      f"EM = {record_em:.4f}, SQL_EM = {sql_em:.4f}, err = {error_rate*100:.1f}%")

                log_epoch_metrics({
                    "epoch": epoch, "train_loss": tr_loss, "dev_loss": dev_loss,
                    "record_f1": record_f1, "record_em": record_em,
                    "sql_em": sql_em, "error_rate": error_rate,
                    "gradient_norm": avg_grad_norm,
                    "lr": optimizer.param_groups[0]["lr"],
                }, step=epoch)
                log_epoch_metrics({
                    "timing/epoch_seconds": epoch_time,
                    "timing/wall_clock_seconds": wall_clock,
                    "timing/train_epoch_seconds": train_epoch_seconds,
                    "timing/train_tokens_per_sec": train_tokens / train_epoch_seconds if train_epoch_seconds > 0 else 0,
                }, step=epoch)

                tol = getattr(cfg, 'patience_tolerance', 0.0)
                improved = (record_f1 > best_val + tol) if cfg.checkpointing.mode == "max" else (record_f1 < best_val - tol)
                log_epoch_metrics({
                    "tracking/best_record_f1": record_f1 if improved else best_val,
                    "tracking/epochs_since_improvement": 0 if improved else epochs_since_improvement + 1,
                }, step=epoch)
                if improved:
                    best_val = record_f1
                    best_metrics = {"record_f1": record_f1, "record_em": record_em,
                                    "sql_em": sql_em, "error_rate": error_rate}
                    epochs_since_improvement = 0
                    if cfg.checkpointing.enabled and cfg.checkpointing.save_best:
                        save_model(ckpt_dir, model, best=True,
                                   best_filename=cfg.checkpointing.best_filename,
                                   last_filename=cfg.checkpointing.last_filename)
                else:
                    epochs_since_improvement += 1

                if cfg.log_system_metrics:
                    system = collect_system_metrics(device)
                    log_epoch_metrics({f"system/{k}": v for k, v in system.items()}, step=epoch)
            else:
                # Not last epoch: launch SQL in background, overlap with next train
                print(f"Epoch {epoch}: train loss = {tr_loss:.4f}, SQL metrics pending (async)...")
                future = _sql_pool.submit(
                    eval_epoch_sql, all_preds, cfg, gt_sql_path, model_sql_path,
                    gt_record_path, model_record_path, _pred_cache,
                )
                _pending_list.append((future, epoch, tr_loss, dev_loss, avg_grad_norm,
                            optimizer.param_groups[0]["lr"],
                            train_epoch_seconds, train_tokens, epoch_gpu_end,
                            epoch_start, train_start))
                epoch_times.append(time.time() - epoch_start)

                if cfg.log_system_metrics:
                    system = collect_system_metrics(device)
                    log_epoch_metrics({f"system/{k}": v for k, v in system.items()}, step=epoch)
        else:
            epoch_time = time.time() - epoch_start
            epoch_times.append(epoch_time)
            wall_clock = time.time() - train_start

            print(f"Epoch {epoch}: train loss = {tr_loss:.4f}")
            print(f"Epoch {epoch}: eval skipped (every {cfg.eval_every_n_epochs} epochs)")

            log_epoch_metrics({
                "epoch": epoch, "train_loss": tr_loss,
                "gradient_norm": avg_grad_norm,
                "lr": optimizer.param_groups[0]["lr"],
            }, step=epoch)
            log_epoch_metrics({
                "timing/epoch_seconds": epoch_time,
                "timing/wall_clock_seconds": wall_clock,
                "timing/train_epoch_seconds": train_epoch_seconds,
                "timing/train_tokens_per_sec": train_tokens / train_epoch_seconds if train_epoch_seconds > 0 else 0,
            }, step=epoch)
            if cfg.log_system_metrics:
                system = collect_system_metrics(device)
                log_epoch_metrics({f"system/{k}": v for k, v in system.items()}, step=epoch)

        if cfg.checkpointing.enabled and cfg.checkpointing.save_every_n > 0 and (epoch + 1) % cfg.checkpointing.save_every_n == 0:
            save_model(ckpt_dir, model, best=False,
                       last_filename=f"model_epoch_{epoch}.pt")

        if cfg.checkpointing.save_training_state:
            save_training_state(ckpt_dir, model, optimizer, scheduler,
                                epoch + 1, best_val, epochs_since_improvement,
                                )

        wall_clock = time.time() - train_start
        if cfg.max_wall_clock_hours and wall_clock >= cfg.max_wall_clock_hours * 3600:
            # Drain all pending SQL before stopping
            for p in _pending_list:
                best_val, best_metrics, epochs_since_improvement, _ = _collect_async_sql(
                    p, cfg, ckpt_dir, model, best_val, best_metrics,
                    epochs_since_improvement, optimizer,
                )
            _pending_list.clear()
            print(f"Time budget reached ({wall_clock/3600:.2f}h / {cfg.max_wall_clock_hours:.2f}h). Stopping after epoch {epoch}.")
            break

        if stop_requested():
            # Drain pending SQL before stopping
            for p in _pending_list:
                best_val, best_metrics, epochs_since_improvement, _ = _collect_async_sql(
                    p, cfg, ckpt_dir, model, best_val, best_metrics,
                    epochs_since_improvement, optimizer,
                )
            _pending_list.clear()
            print(f"Graceful stop after epoch {epoch}.")
            break

    except KeyboardInterrupt:
        _interrupted = True
        # Drain pending SQL if possible
        for p in _pending_list:
            try:
                best_val, best_metrics, epochs_since_improvement, _ = _collect_async_sql(
                    p, cfg, ckpt_dir, model, best_val, best_metrics,
                    epochs_since_improvement, optimizer,
                )
            except Exception:
                pass
        _pending_list.clear()
        print(f"\nInterrupted at epoch {epoch}. Saving training state...")
        if cfg.checkpointing.save_training_state:
            save_training_state(ckpt_dir, model, optimizer, scheduler,
                                epoch, best_val, epochs_since_improvement,
                                )
            print(f"State saved to {ckpt_dir}. Resume with --resume {run_dir}")
        else:
            print("Training state saving disabled (checkpointing.save_training_state=False). Resume not available.")
    finally:
        _sql_pool.shutdown(wait=False)

    if epoch_times:
        log_extra_params({"avg_epoch_seconds": round(sum(epoch_times) / len(epoch_times), 2)})

    return best_val, _interrupted


def train_epoch(cfg, model, train_loader, optimizer, scheduler, device, global_step=0):
    model.train()
    total_loss = 0
    total_tokens = 0
    total_grad_norm = 0.0
    num_batches = 0
    criterion = _make_criterion(cfg)
    use_amp = getattr(cfg, 'use_amp', False)

    # Batch metric rank tracking (per-epoch running history)
    loss_history = []
    grad_norm_history = []

    for encoder_input, encoder_mask, decoder_input, decoder_targets, _ in tqdm(train_loader):
        optimizer.zero_grad()
        encoder_input = encoder_input.to(device)
        encoder_mask = encoder_mask.to(device)
        decoder_input = decoder_input.to(device)
        decoder_targets = decoder_targets.to(device)

        with _amp_context(use_amp, device):
            loss, non_pad = _forward_and_loss(
                model, encoder_input, encoder_mask, decoder_input, decoder_targets, criterion,
            )
        loss.backward()

        # clip_grad_norm_ returns the total (unclipped) gradient norm
        clip_val = cfg.grad_clip_norm if cfg.grad_clip_norm is not None else float("inf")
        grad_norm = nn.utils.clip_grad_norm_(model.parameters(), clip_val).item()
        total_grad_norm += grad_norm
        num_batches += 1

        optimizer.step()
        if scheduler is not None:
            scheduler.step()

        num_tokens = torch.sum(non_pad).item()
        total_loss += loss.item() * num_tokens
        total_tokens += num_tokens

        # Track rank of current batch metrics relative to epoch history
        loss_val = loss.item()
        bisect.insort(loss_history, loss_val)
        loss_rank = loss_history.index(loss_val) / max(len(loss_history) - 1, 1)

        bisect.insort(grad_norm_history, grad_norm)
        grad_norm_rank = grad_norm_history.index(grad_norm) / max(len(grad_norm_history) - 1, 1)

        log_epoch_metrics({
            "batch/loss": loss.item(),
            "batch/gradient_norm": grad_norm,
            "batch/lr": optimizer.param_groups[0]["lr"],
            "batch/loss_rank": loss_rank,
            "batch/gradient_norm_rank": grad_norm_rank,
        }, step=global_step)
        global_step += 1

    avg_loss = total_loss / total_tokens
    avg_grad_norm = total_grad_norm / num_batches
    return avg_loss, avg_grad_norm, total_tokens, global_step


# ── Evaluation ──────────────────────────────────────────────────────────

def _maybe_subset_loader(dev_loader, subset_size):
    """Wrap dev_loader to yield only the first `subset_size` examples."""
    if subset_size is None or subset_size <= 0:
        return dev_loader
    from torch.utils.data import DataLoader, Subset
    ds = dev_loader.dataset
    n = min(subset_size, len(ds))
    if n == len(ds):
        return dev_loader
    subset = Subset(ds, list(range(n)))
    return DataLoader(subset, batch_size=dev_loader.batch_size,
                      shuffle=False, collate_fn=dev_loader.collate_fn,
                      num_workers=dev_loader.num_workers)


def _compute_dev_loss(model, loader, criterion, device, use_amp=False):
    """Cheap teacher-forced loss on the (possibly subsetted) dev loader."""
    total_loss = 0.0
    total_tokens = 0
    with torch.inference_mode(), _amp_context(use_amp, device):
        for batch in loader:
            enc_in = batch[0].to(device)
            enc_mask = batch[1].to(device)
            dec_in = batch[2].to(device)
            dec_tgt = batch[3].to(device)
            loss, non_pad = _forward_and_loss(model, enc_in, enc_mask, dec_in, dec_tgt, criterion)
            n = non_pad.sum().item()
            total_loss += loss.item() * n
            total_tokens += n
    return total_loss / total_tokens if total_tokens > 0 else 0.0


def eval_epoch_gpu(cfg, model, dev_loader, device, *, is_final=False):
    """Phase A (GPU): compute dev loss + generate predictions.

    During training eval: uses eval_num_beams (greedy) and eval_subset_size.
    During final eval (is_final=True): uses full num_beams on all examples.
    Returns (dev_loss, all_preds).
    """
    model.eval()
    if is_final:
        num_beams = cfg.num_beams
        loader = dev_loader
    else:
        num_beams = cfg.eval_num_beams if cfg.eval_num_beams is not None else cfg.num_beams
        loader = _maybe_subset_loader(dev_loader, getattr(cfg, 'eval_subset_size', None))

    # Teacher-forced dev loss (cheap: single parallel forward pass)
    ls = getattr(cfg, "label_smoothing", 0.0)
    criterion = nn.CrossEntropyLoss(label_smoothing=ls)
    use_amp = getattr(cfg, 'use_amp', False)
    dev_loss = _compute_dev_loss(model, loader, criterion, device, use_amp=use_amp)

    all_preds = _generate_predictions(
        model, loader, cfg.max_new_tokens, num_beams, device,
        min_new_tokens=getattr(cfg, "min_new_tokens", None),
        length_penalty=getattr(cfg, "length_penalty", None),
        early_stopping=getattr(cfg, 'beam_early_stopping', True),
        use_amp=use_amp,
    )
    return dev_loss, all_preds


def eval_epoch_sql(all_preds, cfg, gt_sql_path, model_sql_path,
                   gt_record_path, model_record_path, pred_cache=None):
    """Phase B (CPU): run SQL queries and compute metrics."""
    preds_key = hash(tuple(all_preds))
    if pred_cache is not None and pred_cache.get("key") == preds_key:
        print("Predictions unchanged — reusing cached SQL metrics")
        sql_em, record_em, record_f1, error_msgs = pred_cache["metrics"]
    else:
        save_queries_and_records(all_preds, model_sql_path, model_record_path,
                                 num_threads=cfg.sql_num_threads)
        sql_em, record_em, record_f1, error_msgs = compute_metrics(
            gt_sql_path, model_sql_path, gt_record_path, model_record_path
        )
        if pred_cache is not None:
            pred_cache["key"] = preds_key
            pred_cache["metrics"] = (sql_em, record_em, record_f1, error_msgs)

    error_rate = sum(1 for m in error_msgs if m) / len(error_msgs) if error_msgs else 0
    return record_f1, record_em, sql_em, error_rate


def eval_epoch(cfg, model, dev_loader, gt_sql_path, model_sql_path, gt_record_path, model_record_path, device, pred_cache=None):
    """Full eval (synchronous). Used for final eval and backward compat."""
    _dev_loss, all_preds = eval_epoch_gpu(cfg, model, dev_loader, device, is_final=True)
    record_f1, record_em, sql_em, error_rate = eval_epoch_sql(
        all_preds, cfg, gt_sql_path, model_sql_path, gt_record_path, model_record_path, pred_cache,
    )
    return record_f1, record_em, sql_em, error_rate


# ── Test inference ──────────────────────────────────────────────────────

def test_inference(cfg, model, test_loader, model_sql_path, model_record_path, device):
    model.eval()
    all_preds = _generate_predictions(
        model, test_loader, cfg.max_new_tokens, cfg.num_beams, device,
        min_new_tokens=getattr(cfg, "min_new_tokens", None),
        length_penalty=getattr(cfg, "length_penalty", None),
        early_stopping=getattr(cfg, 'beam_early_stopping', True),
        use_amp=getattr(cfg, 'use_amp', False),
    )
    save_queries_and_records(all_preds, model_sql_path, model_record_path,
                             num_threads=cfg.sql_num_threads)
    print(f"Test predictions saved to {model_sql_path}")


# ── Entry point ─────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Part 1: T5 fine-tune training")

    # ── Config variant (class name in part1.config) ──
    parser.add_argument("--config", type=str, default="T5FineTuneConfig",
                        help="Config class name in part1.config (e.g. 'T5FineTuneConfig_freeze_encoder')")

    # ── Training hyperparameters ──
    parser.add_argument("--num_epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--test_batch_size", type=int, default=None)
    parser.add_argument("--learning_rate", type=float, default=None)
    parser.add_argument("--weight_decay", type=float, default=None)
    parser.add_argument("--scheduler", type=str, default=None, choices=["cosine", "linear", "none"])
    parser.add_argument("--patience_epochs", type=int, default=None)
    parser.add_argument("--optimizer", type=str, default=None, choices=["AdamW"])
    parser.add_argument("--num_warmup_epochs", type=int, default=None)
    parser.add_argument("--grad_clip_norm", type=float, default=None)
    parser.add_argument("--dropout", type=float, default=None)

    # ── Layer freezing ──
    parser.add_argument("--freeze_encoder", action="store_true", default=None)
    parser.add_argument("--freeze_embeddings", action="store_true", default=None)
    parser.add_argument("--unfreeze_last_n_decoder", type=int, default=None)

    # ── Input formatting ──
    parser.add_argument("--input_prefix", type=str, default=None)
    parser.add_argument("--include_schema", action="store_true", default=None)

    # ── Resume / time budget ──
    parser.add_argument("--resume", type=str, default=None, help="Run dir to resume from")
    parser.add_argument("--max_time", type=float, default=None, help="Max wall clock hours")

    # ── Decoding ──
    parser.add_argument("--max_new_tokens", type=int, default=None)
    parser.add_argument("--num_beams", type=int, default=None)

    # ── Misc ──
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", type=str, default=None)

    return parser.parse_args()


_CLI_TO_CFG = {
    "num_epochs": "num_epochs",
    "batch_size": "batch_size",
    "test_batch_size": "test_batch_size",
    "learning_rate": "learning_rate",
    "weight_decay": "weight_decay",
    "scheduler": "scheduler",
    "patience_epochs": "patience_epochs",
    "optimizer": "optimizer",
    "num_warmup_epochs": "num_warmup_epochs",
    "grad_clip_norm": "grad_clip_norm",
    "dropout": "dropout",
    "freeze_encoder": "freeze_encoder",
    "freeze_embeddings": "freeze_embeddings",
    "unfreeze_last_n_decoder": "unfreeze_last_n_decoder",
    "input_prefix": "input_prefix",
    "include_schema": "include_schema",
    "resume": "resume_run_dir",
    "max_time": "max_wall_clock_hours",
    "max_new_tokens": "max_new_tokens",
    "num_beams": "num_beams",
    "seed": "seed",
    "name": "name",
}


def apply_cli_overrides(cfg, cli):
    """Apply non-None CLI arguments to the config object."""
    for cli_name, cfg_name in _CLI_TO_CFG.items():
        val = getattr(cli, cli_name)
        if val is not None:
            setattr(cfg, cfg_name, val)


def load_config(class_name):
    """Look up a config class by name in part1.config and return an instance."""
    import part1.config as cfg_mod
    cls = getattr(cfg_mod, class_name, None)
    if cls is None:
        available = [n for n in dir(cfg_mod) if not n.startswith("_") and isinstance(getattr(cfg_mod, n), type)]
        raise ValueError(f"Unknown config class '{class_name}'. Available: {available}")
    return cls()


def main_with_config(cfg):
    """Run the full training pipeline with a pre-built config.

    Used by: main() (CLI entry), sweep scripts (W&B sweeps), and any
    programmatic caller that constructs a config object directly.
    """
    set_random_seeds(cfg.seed)
    device = cfg.device

    # Data
    train_loader, dev_loader, test_loader = load_t5_data(
        cfg.batch_size, cfg.test_batch_size,
        input_prefix=cfg.input_prefix, include_schema=cfg.include_schema,
        schema_mode=getattr(cfg, "schema_mode", "tables"),
    )

    # Model
    model = initialize_model(
        finetune=cfg.finetune,
        model_checkpoint=cfg.model_checkpoint,
        dropout=cfg.dropout,
        freeze_encoder=cfg.freeze_encoder,
        freeze_embeddings=cfg.freeze_embeddings,
        unfreeze_last_n_decoder=cfg.unfreeze_last_n_decoder,
        device=device,
    )

    # Wrap with restricted SQL vocabulary if configured
    sql_vocab = None
    use_mlp_head = getattr(cfg, "use_mlp_head", False)
    mlp_dim = getattr(cfg, "mlp_dim", 1024)
    mlp_dropout = getattr(cfg, "mlp_dropout", 0.1)
    if getattr(cfg, "use_restricted_vocab", False):
        sql_vocab = FlightSQLVocab()
        sql_vocab.to(device)
        if use_mlp_head:
            model = T5ForFlightSQLWithMLP(model, sql_vocab,
                                          mlp_dim=mlp_dim, mlp_dropout=mlp_dropout)
            model = model.to(device)  # Move MLP layers to GPU
            print(f"Restricted SQL vocab + MLP head (dim={mlp_dim}): "
                  f"{sql_vocab.vocab_size} tokens (vs {sql_vocab.full_vocab_size} full)")
        else:
            model = T5ForFlightSQL(model, sql_vocab)
            print(f"Restricted SQL vocab: {sql_vocab.vocab_size} tokens "
                  f"(vs {sql_vocab.full_vocab_size} full)")

    # Load warm-start base checkpoint if configured (BEFORE LoRA application)
    base_ckpt_path = getattr(cfg, 'base_checkpoint_path', None)
    if base_ckpt_path is None and 'warmstart' in getattr(cfg, 'name', ''):
        import glob
        matches = glob.glob("output/t5_ft_restricted_v3_*/checkpoints/model_best.pt")
        if matches:
            base_ckpt_path = sorted(matches)[-1]
    if base_ckpt_path:
        assert os.path.exists(base_ckpt_path), f"Base checkpoint not found: {base_ckpt_path}"
        print(f"Loading warm-start base from: {base_ckpt_path}")
        base_state = torch.load(base_ckpt_path, map_location=device, weights_only=True)
        # Load into the inner HF model (unwrapping T5ForFlightSQL if present)
        if isinstance(model, (T5ForFlightSQL, T5ForFlightSQLWithMLP)):
            inner = model.model if isinstance(model, T5ForFlightSQL) else model.model
            inner.load_state_dict(base_state)
        else:
            model.load_state_dict(base_state)
        print("Warm-start base checkpoint loaded successfully")

    # Apply LoRA if configured
    use_lora = getattr(cfg, "use_lora", False)
    if use_lora:
        from peft import LoraConfig, get_peft_model, TaskType
        lora_r = getattr(cfg, "lora_r", 16)
        lora_alpha = getattr(cfg, "lora_alpha", 32)
        lora_dropout = getattr(cfg, "lora_dropout", 0.05)
        lora_target = getattr(cfg, "lora_target_modules", ["q", "v"])
        lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            target_modules=lora_target,
            task_type=TaskType.SEQ_2_SEQ_LM,
        )
        # Apply to the inner HF model if wrapped
        if isinstance(model, T5ForFlightSQL):
            model.model = get_peft_model(model.model, lora_config)
            trainable = sum(p.numel() for p in model.model.parameters() if p.requires_grad)
            total = sum(p.numel() for p in model.model.parameters())
        else:
            model = get_peft_model(model, lora_config)
            trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
            total = sum(p.numel() for p in model.parameters())
        print(f"LoRA applied (r={lora_r}, alpha={lora_alpha}): "
              f"{trainable:,} trainable / {total:,} total params "
              f"({trainable/total*100:.1f}%)")

    # Auto batch size: try to maximize VRAM usage
    if getattr(cfg, "auto_batch_size", False) and torch.cuda.is_available():
        optimal_bs = auto_batch_size(cfg, model, train_loader, device)
        if optimal_bs != cfg.batch_size:
            print(f"Auto batch size: {cfg.batch_size} → {optimal_bs}")
            cfg.batch_size = optimal_bs
            # Reload data with new batch size
            train_loader, dev_loader, test_loader = load_t5_data(
                cfg.batch_size, cfg.test_batch_size,
                input_prefix=cfg.input_prefix, include_schema=cfg.include_schema,
                schema_mode=getattr(cfg, "schema_mode", "tables"),
            )

    # Optimizer & scheduler
    args = argparse.Namespace(
        optimizer_type=cfg.optimizer,
        learning_rate=cfg.learning_rate,
        weight_decay=cfg.weight_decay,
        scheduler_type=cfg.scheduler or "none",
        num_warmup_epochs=cfg.num_warmup_epochs,
        max_n_epochs=cfg.num_epochs,
    )
    optimizer, scheduler = initialize_optimizer_and_scheduler(args, model, len(train_loader))

    # Resume: load training state
    start_epoch, best_val, epochs_since_imp = 0, None, 0
    if cfg.resume_run_dir:
        resume_ckpt = str(Path(cfg.resume_run_dir) / "checkpoints")
        start_epoch, best_val, epochs_since_imp = load_training_state(
            resume_ckpt, model, optimizer, scheduler, device
        )
        print(f"Resumed from epoch {start_epoch}, best_val={best_val:.4f}")

    # Single setup: creates run directory + starts W&B run
    run_dir, _ = setup_run(cfg, experiment_name="part1_t5_finetune")
    print(f"Run directory: {run_dir}")
    print(f"Device: {device}")

    # Log one-time model & data params (skip on resume — already logged)
    if not cfg.resume_run_dir:
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        extra_params = {
            "total_params": total_params,
            "trainable_params": trainable_params,
            "num_train_samples": len(train_loader.dataset),
            "num_dev_samples": len(dev_loader.dataset),
            **collect_hardware_info(),
        }
        log_extra_params(extra_params)

    # Train
    _, interrupted = train(cfg, model, train_loader, dev_loader, optimizer, scheduler, run_dir,
                           start_epoch=start_epoch, best_val=best_val, epochs_since_improvement=epochs_since_imp)

    if interrupted:
        end_run()
        print("Training was interrupted. Skipping final eval and test inference.")
        return

    # Free training objects and reload best checkpoint for final eval
    del model, optimizer, scheduler
    cleanup_vram()

    ckpt_dir = str(run_dir / "checkpoints")
    model = load_model_from_checkpoint(
        ckpt_dir, finetune=cfg.finetune, model_checkpoint=cfg.model_checkpoint,
        dropout=cfg.dropout, best=True, device=device,
        best_filename=cfg.checkpointing.best_filename,
        last_filename=cfg.checkpointing.last_filename,
    )
    if sql_vocab is not None:
        if use_mlp_head:
            model = T5ForFlightSQLWithMLP(model, sql_vocab,
                                          mlp_dim=mlp_dim, mlp_dropout=mlp_dropout)
            model = model.to(device)  # Move MLP layers to GPU
        else:
            model = T5ForFlightSQL(model, sql_vocab)
    # NOTE: No LoRA re-application needed. save_model now uses merge_and_unload,
    # so the saved checkpoint is a vanilla T5 state_dict that loads directly.
    model.eval()

    # Final dev eval
    f1, em, sql_em, err = eval_epoch(
        cfg, model, dev_loader, "data/dev.sql", "results/t5_ft_dev.sql",
        "records/ground_truth_dev.pkl", "records/t5_ft_dev.pkl", device,
    )
    print(f"Final dev: F1={f1:.4f}, EM={em:.4f}, SQL_EM={sql_em:.4f}, err={err*100:.1f}%")

    # Test
    test_inference(cfg, model, test_loader, "results/t5_ft_test.sql", "records/t5_ft_test.pkl", device)

    # Upload final best checkpoint to W&B
    best_ckpt = os.path.join(ckpt_dir, cfg.checkpointing.best_filename)
    if os.path.exists(best_ckpt):
        log_model_artifact(best_ckpt, artifact_name=f"{cfg.name}-best",
                           metadata={"final_dev_f1": f1, "final_dev_em": em,
                                     "final_dev_sql_em": sql_em})
    end_run()

    del model
    cleanup_vram()


def main():
    """CLI entry point: parse args, build config, delegate to main_with_config."""
    cli = parse_args()
    cfg = load_config(cli.config)
    apply_cli_overrides(cfg, cli)
    main_with_config(cfg)


if __name__ == "__main__":
    from src.utils.gpu_lock import GpuLock
    with GpuLock():
        main()
