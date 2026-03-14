"""DPO training loop for T5 encoder-decoder with restricted SQL vocabulary.

Implements:
  - DPODataset: preference triplet dataset (prompt, chosen, rejected)
  - dpo_collate_fn: dynamic padding + decoder input construction
  - dpo_train: training loop with W&B, early stopping, checkpointing
  - main: entry point (load config, models, data; train; evaluate)
"""

import argparse
import json
import os
import time
from pathlib import Path

import torch
import transformers
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from part1.data import PAD_IDX, _TOKENIZER, _load_schema_string, load_t5_data
from part1.dpo_loss import dpo_train_step, dpo_train_step_lora, _amp_context
from part1.model import initialize_model, load_model_from_checkpoint, save_model
from part1.model_flightdb import FlightSQLVocab, T5ForFlightSQL
from part1.train import (
    _generate_predictions,
    cleanup_vram,
    eval_epoch_gpu,
    eval_epoch_sql,
    stop_requested,
    test_inference,
)
from src.wandb_utils import (
    end_run, log_epoch_metrics, log_extra_params, log_model_artifact, setup_run,
)
from utils import compute_metrics, save_queries_and_records, set_random_seeds

_BOS_ID = _TOKENIZER.convert_tokens_to_ids("<extra_id_0>")


# ── Dataset ──────────────────────────────────────────────────────────────────


class DPODataset(Dataset):
    """Dataset of (prompt, chosen, rejected) triplets for DPO training."""

    def __init__(self, triplets, tokenizer, include_schema=True,
                 schema_mode="tables", max_length=512):
        """
        Args:
            triplets: list of (nl_text, chosen_sql, rejected_sql) tuples
            tokenizer: T5TokenizerFast instance
            include_schema: whether to prepend schema string to NL input
            schema_mode: schema format ("tables", "top8_cols", etc.)
            max_length: max token length for truncation
        """
        self.tokenizer = tokenizer
        schema_str = _load_schema_string(mode=schema_mode) if include_schema else ""

        self.prompts = tokenizer(
            [schema_str + t[0] for t in triplets],
            padding=False, truncation=True, max_length=max_length,
            return_attention_mask=False,
        )["input_ids"]
        self.chosen = tokenizer(
            [t[1] for t in triplets],
            padding=False, truncation=True, max_length=max_length,
            return_attention_mask=False,
        )["input_ids"]
        self.rejected = tokenizer(
            [t[2] for t in triplets],
            padding=False, truncation=True, max_length=max_length,
            return_attention_mask=False,
        )["input_ids"]

    def __len__(self):
        return len(self.prompts)

    def __getitem__(self, idx):
        return (
            torch.tensor(self.prompts[idx], dtype=torch.long),
            torch.tensor(self.chosen[idx], dtype=torch.long),
            torch.tensor(self.rejected[idx], dtype=torch.long),
        )


# ── Collation ────────────────────────────────────────────────────────────────


def dpo_collate_fn(batch):
    """Collate for DPO: pad prompt, chosen, rejected independently.

    Builds decoder inputs as [BOS] + targets[:-1] (teacher forcing shift).

    Returns:
        (prompt_ids, prompt_mask, chosen_dec_input, chosen_targets,
         rejected_dec_input, rejected_targets)
    """
    prompts, chosens, rejecteds = zip(*batch)

    # Pad prompts (encoder inputs)
    prompt_ids = pad_sequence(prompts, batch_first=True, padding_value=PAD_IDX)
    prompt_mask = (prompt_ids != PAD_IDX).long()

    # Pad chosen and rejected (decoder targets)
    chosen_ids = pad_sequence(chosens, batch_first=True, padding_value=PAD_IDX)
    rejected_ids = pad_sequence(rejecteds, batch_first=True, padding_value=PAD_IDX)

    # Build decoder inputs: [BOS] + targets[:-1]
    B = prompt_ids.size(0)
    bos = torch.full((B, 1), _BOS_ID, dtype=torch.long)

    chosen_dec_input = torch.cat([bos, chosen_ids[:, :-1]], dim=1)
    rejected_dec_input = torch.cat([bos.clone(), rejected_ids[:, :-1]], dim=1)

    return (prompt_ids, prompt_mask,
            chosen_dec_input, chosen_ids,
            rejected_dec_input, rejected_ids)


# ── Preference data loading ─────────────────────────────────────────────────


def load_preference_data(path):
    """Load preference triplets from JSON file.

    Expected format: list of {"nl": str, "chosen": str, "rejected": str}

    Returns:
        list of (nl_text, chosen_sql, rejected_sql) tuples
    """
    with open(path) as f:
        data = json.load(f)
    triplets = [(item["nl"], item["chosen"], item["rejected"]) for item in data]
    return triplets


# ── Auto batch size ──────────────────────────────────────────────────────────


def dpo_auto_batch_size(cfg, policy_model, ref_model, dpo_dataset,
                        device, target_vram_pct=0.85):
    """Find the largest DPO batch size that fits in GPU VRAM.

    Strategy: binary search between powers-of-2 coarse scan, then fine-tune.
    Uses max_memory_allocated (peak) with a 15% safety margin (target=0.85)
    to account for variable-length batches and runtime overhead.

    Args:
        cfg: T5DPOConfig instance
        policy_model: T5ForFlightSQL (policy, possibly with LoRA)
        ref_model: T5ForFlightSQL (frozen reference) or None for LoRA
        dpo_dataset: DPODataset instance
        device: torch device
        target_vram_pct: fraction of total VRAM to target

    Returns:
        optimal batch size (int)
    """
    if not torch.cuda.is_available():
        return cfg.batch_size

    total_vram = torch.cuda.get_device_properties(0).total_memory
    target_bytes = total_vram * target_vram_pct
    use_lora = getattr(cfg, "use_lora", False)
    use_amp = getattr(cfg, "use_amp", True)
    best_bs = cfg.batch_size

    # Phase 1: coarse scan with powers of 2 to find ceiling
    coarse = [cfg.batch_size]
    bs = cfg.batch_size * 2
    while bs <= 256:
        coarse.append(bs)
        bs *= 2
    candidates = coarse

    # Find the longest samples to build a worst-case probe batch.
    # Activation memory scales with sequence length, so probing with
    # the longest sequences prevents OOM on worst-case batches during training.
    sample_lens = [
        len(dpo_dataset.chosen[i]) + len(dpo_dataset.rejected[i])
        for i in range(len(dpo_dataset))
    ]
    longest_indices = sorted(range(len(sample_lens)),
                             key=lambda i: sample_lens[i], reverse=True)

    for bs in candidates:
        try:
            cleanup_vram()
            torch.cuda.reset_peak_memory_stats()

            # Build a worst-case batch from the longest samples
            worst_case_samples = [dpo_dataset[longest_indices[i]]
                                  for i in range(min(bs, len(longest_indices)))]
            batch = dpo_collate_fn(worst_case_samples)

            # Run actual DPO train step (forward + backward + optimizer step)
            probe_opt = torch.optim.AdamW(
                [p for p in policy_model.parameters() if p.requires_grad],
                lr=1e-6,
            )
            if use_lora:
                dpo_train_step_lora(
                    policy_model, batch, probe_opt,
                    beta=cfg.dpo_beta, grad_clip_norm=cfg.grad_clip_norm,
                    device=device, use_amp=use_amp,
                )
            else:
                dpo_train_step(
                    policy_model, ref_model, batch, probe_opt,
                    beta=cfg.dpo_beta, grad_clip_norm=cfg.grad_clip_norm,
                    device=device, use_amp=use_amp,
                )

            # Use PEAK memory, not current — peak captures intermediate activations
            peak = torch.cuda.max_memory_allocated()
            del batch, probe_opt
            cleanup_vram()

            if peak < target_bytes:
                best_bs = bs
            else:
                break
        except RuntimeError:
            # OOM — use previous best
            cleanup_vram()
            break

    # Phase 2: fine-tune between best_bs and the next power-of-2 that failed
    if best_bs < coarse[-1]:
        failed_bs = best_bs * 2
        # Try midpoints: best_bs + step, stepping by batch_size increments
        step = max(cfg.batch_size, 4)
        fine_bs = best_bs + step
        while fine_bs < failed_bs:
            try:
                cleanup_vram()
                torch.cuda.reset_peak_memory_stats()
                worst_case_samples = [dpo_dataset[longest_indices[i]]
                                      for i in range(min(fine_bs, len(longest_indices)))]
                batch = dpo_collate_fn(worst_case_samples)
                probe_opt = torch.optim.AdamW(
                    [p for p in policy_model.parameters() if p.requires_grad],
                    lr=1e-6,
                )
                if use_lora:
                    dpo_train_step_lora(
                        policy_model, batch, probe_opt,
                        beta=cfg.dpo_beta, grad_clip_norm=cfg.grad_clip_norm,
                        device=device, use_amp=use_amp,
                    )
                else:
                    dpo_train_step(
                        policy_model, ref_model, batch, probe_opt,
                        beta=cfg.dpo_beta, grad_clip_norm=cfg.grad_clip_norm,
                        device=device, use_amp=use_amp,
                    )
                peak = torch.cuda.max_memory_allocated()
                del batch, probe_opt
                cleanup_vram()

                if peak < target_bytes:
                    best_bs = fine_bs
                else:
                    break
            except RuntimeError:
                cleanup_vram()
                break
            fine_bs += step

    # Clean up probe state
    policy_model.zero_grad(set_to_none=True)
    cleanup_vram()
    return best_bs


# ── Training loop ────────────────────────────────────────────────────────────


def dpo_train(cfg, policy_model, ref_model, train_loader, dev_loader,
              optimizer, scheduler, run_dir):
    """DPO training loop following part1/train.py patterns.

    Args:
        cfg: T5DPOConfig instance
        policy_model: T5ForFlightSQL being trained
        ref_model: frozen T5ForFlightSQL reference
        train_loader: DataLoader of DPO preference batches
        dev_loader: standard T5 dev DataLoader for evaluation
        optimizer: optimizer for policy_model parameters
        scheduler: LR scheduler (or None for fixed LR)
        run_dir: Path to run output directory

    Returns:
        best_val: best dev Record F1 achieved
    """
    device = cfg.device
    ckpt_dir = str(run_dir / "checkpoints")
    os.makedirs(ckpt_dir, exist_ok=True)

    best_val = -1.0
    best_metrics = {}
    epochs_since_improvement = 0
    train_start = time.time()
    patience_tolerance = getattr(cfg, "patience_tolerance", 0.0)

    gt_sql_path = "data/dev.sql"
    gt_record_path = "records/ground_truth_dev.pkl"
    global_step = 0

    grad_accum_steps = getattr(cfg, "gradient_accumulation_steps", 1)
    use_lora = getattr(cfg, "use_lora", False)
    use_amp = getattr(cfg, "use_amp", True)

    for epoch in range(cfg.num_epochs):
        epoch_start = time.time()

        # ── Train epoch ──
        policy_model.train()
        epoch_loss = 0.0
        epoch_reward_margin = 0.0
        epoch_reward_accuracy = 0.0
        epoch_grad_norm = 0.0
        num_batches = 0
        optimizer.zero_grad()

        for batch_idx, batch in enumerate(tqdm(train_loader, desc=f"DPO Epoch {epoch}")):
            if use_lora:
                metrics = dpo_train_step_lora(
                    policy_model, batch, optimizer,
                    beta=cfg.dpo_beta, grad_clip_norm=cfg.grad_clip_norm,
                    device=device, use_amp=use_amp,
                    accumulate=(grad_accum_steps > 1),
                    accum_scale=1.0 / grad_accum_steps,
                )
            else:
                metrics = dpo_train_step(
                    policy_model, ref_model, batch, optimizer,
                    beta=cfg.dpo_beta, grad_clip_norm=cfg.grad_clip_norm,
                    device=device, use_amp=use_amp,
                    accumulate=(grad_accum_steps > 1),
                    accum_scale=1.0 / grad_accum_steps,
                )

            epoch_loss += metrics["loss"]
            epoch_reward_margin += metrics["reward_margin"]
            epoch_reward_accuracy += metrics["reward_accuracy"]
            num_batches += 1

            # Optimizer step every grad_accum_steps or at end of epoch
            if (batch_idx + 1) % grad_accum_steps == 0 or (batch_idx + 1) == len(train_loader):
                grad_norm = torch.nn.utils.clip_grad_norm_(
                    policy_model.parameters(), cfg.grad_clip_norm).item()
                optimizer.step()
                optimizer.zero_grad()
                epoch_grad_norm += grad_norm

                # Step the scheduler per optimizer step
                if scheduler is not None:
                    scheduler.step()

            # Log batch-level metrics
            log_epoch_metrics({
                "batch/loss": metrics["loss"],
                "batch/reward_margin": metrics["reward_margin"],
                "batch/reward_accuracy": metrics["reward_accuracy"],
                "batch/gradient_norm": metrics.get("grad_norm", 0.0),
            }, step=global_step)
            global_step += 1

        avg_loss = epoch_loss / num_batches
        avg_reward_margin = epoch_reward_margin / num_batches
        avg_reward_accuracy = epoch_reward_accuracy / num_batches
        num_opt_steps = max(1, num_batches // grad_accum_steps)
        avg_grad_norm = epoch_grad_norm / num_opt_steps

        train_epoch_seconds = time.time() - epoch_start
        print(f"Epoch {epoch}: DPO loss = {avg_loss:.4f}, "
              f"reward_margin = {avg_reward_margin:.4f}, "
              f"reward_accuracy = {avg_reward_accuracy:.3f}")

        # ── Evaluate on dev set ──
        should_eval = ((epoch + 1) % cfg.eval_every_n_epochs == 0) or \
                      (epoch == cfg.num_epochs - 1)

        if should_eval:
            dev_loss, all_preds = eval_epoch_gpu(
                cfg, policy_model, dev_loader, device, is_final=False)

            model_sql_path = str(run_dir / f"dev_pred_e{epoch}.sql")
            model_record_path = str(run_dir / f"dev_pred_e{epoch}.pkl")

            record_f1, record_em, sql_em, error_rate = eval_epoch_sql(
                all_preds, cfg, gt_sql_path, model_sql_path,
                gt_record_path, model_record_path,
            )

            epoch_time = time.time() - epoch_start
            wall_clock = time.time() - train_start

            print(f"Epoch {epoch}: dev F1 = {record_f1:.4f}, "
                  f"EM = {record_em:.4f}, SQL_EM = {sql_em:.4f}, "
                  f"err = {error_rate*100:.1f}%")

            # Log epoch metrics
            log_epoch_metrics({
                "epoch": epoch,
                "train_loss": avg_loss,
                "dev_loss": dev_loss,
                "record_f1": record_f1,
                "record_em": record_em,
                "sql_em": sql_em,
                "error_rate": error_rate,
                "dpo/reward_margin": avg_reward_margin,
                "dpo/reward_accuracy": avg_reward_accuracy,
                "gradient_norm": avg_grad_norm,
                "lr": optimizer.param_groups[0]["lr"],
            }, step=epoch)
            log_epoch_metrics({
                "timing/epoch_seconds": epoch_time,
                "timing/wall_clock_seconds": wall_clock,
                "timing/train_epoch_seconds": train_epoch_seconds,
            }, step=epoch)

            # Checkpointing on dev Record F1 (with patience_tolerance)
            improved = record_f1 > best_val + patience_tolerance
            log_epoch_metrics({
                "tracking/best_record_f1": record_f1 if improved else best_val,
                "tracking/epochs_since_improvement": 0 if improved else epochs_since_improvement + 1,
            }, step=epoch)

            if improved:
                best_val = record_f1
                best_metrics = {
                    "record_f1": record_f1, "record_em": record_em,
                    "sql_em": sql_em, "error_rate": error_rate,
                }
                epochs_since_improvement = 0
                save_model(ckpt_dir, policy_model, best=True)
                print(f"  -> New best dev F1: {best_val:.4f} (saved)")
            else:
                epochs_since_improvement += 1

            # Always save last checkpoint
            save_model(ckpt_dir, policy_model, best=False)
        else:
            # Non-eval epoch: just log training metrics
            log_epoch_metrics({
                "epoch": epoch,
                "train_loss": avg_loss,
                "dpo/reward_margin": avg_reward_margin,
                "dpo/reward_accuracy": avg_reward_accuracy,
                "gradient_norm": avg_grad_norm,
                "lr": optimizer.param_groups[0]["lr"],
            }, step=epoch)

        # Early stopping
        if cfg.patience_epochs > 0 and epochs_since_improvement >= cfg.patience_epochs:
            print(f"Early stopping at epoch {epoch} "
                  f"(patience={cfg.patience_epochs})")
            break

        # Wall clock budget
        wall_clock = time.time() - train_start
        if cfg.max_wall_clock_hours and wall_clock >= cfg.max_wall_clock_hours * 3600:
            print(f"Time budget reached ({wall_clock/3600:.2f}h / "
                  f"{cfg.max_wall_clock_hours:.2f}h). Stopping.")
            break

        # Graceful stop
        if stop_requested():
            print(f"Graceful stop after epoch {epoch}.")
            break

    total_time = time.time() - train_start
    print(f"\nDPO training complete: {total_time/60:.1f} min, "
          f"best dev F1 = {best_val:.4f}")

    if best_metrics:
        print(f"Best metrics: F1={best_metrics['record_f1']:.4f}, "
              f"EM={best_metrics['record_em']:.4f}, "
              f"SQL_EM={best_metrics['sql_em']:.4f}")

    return best_val


# ── Entry point ──────────────────────────────────────────────────────────────


def parse_args():
    parser = argparse.ArgumentParser(description="DPO training for T5 NL-to-SQL")
    parser.add_argument("--learning_rate", type=float, default=None)
    parser.add_argument("--dpo_beta", type=float, default=None)
    parser.add_argument("--num_epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--patience_epochs", type=int, default=None)
    parser.add_argument("--preference_data_path", type=str, default=None)
    parser.add_argument("--base_checkpoint_path", type=str, default=None)
    parser.add_argument("--grad_clip_norm", type=float, default=None)
    parser.add_argument("--num_beams", type=int, default=None)
    parser.add_argument("--max_wall_clock_hours", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", type=str, default=None)
    parser.add_argument("--use_lora", action="store_true", default=False)
    return parser.parse_args()


def apply_cli_overrides(cfg, args):
    """Apply non-None CLI args to config."""
    for attr in ("learning_rate", "dpo_beta", "num_epochs", "batch_size",
                 "patience_epochs", "preference_data_path",
                 "base_checkpoint_path", "grad_clip_norm", "num_beams",
                 "max_wall_clock_hours", "seed", "name"):
        val = getattr(args, attr, None)
        if val is not None:
            setattr(cfg, attr, val)


def _build_scheduler(cfg, optimizer, steps_per_epoch):
    """Build LR scheduler from config fields (cosine/linear with warmup)."""
    scheduler_type = getattr(cfg, "scheduler", "none") or "none"
    if scheduler_type == "none":
        return None

    num_training_steps = steps_per_epoch * cfg.num_epochs
    num_warmup_steps = steps_per_epoch * getattr(cfg, "num_warmup_epochs", 0)

    if scheduler_type == "cosine":
        return transformers.get_cosine_schedule_with_warmup(
            optimizer, num_warmup_steps, num_training_steps)
    elif scheduler_type == "linear":
        return transformers.get_linear_schedule_with_warmup(
            optimizer, num_warmup_steps, num_training_steps)
    else:
        raise ValueError(f"Unknown scheduler: {scheduler_type}")


def main_with_config(cfg):
    """Run the full DPO training pipeline with a pre-built config.

    Used by: main() (CLI entry), sweep scripts (W&B sweeps), and any
    programmatic caller that constructs a config object directly.
    """
    set_random_seeds(cfg.seed)
    device = cfg.device

    # ── Load preference data ──
    print(f"Loading preference data from: {cfg.preference_data_path}")
    triplets = load_preference_data(cfg.preference_data_path)
    print(f"Loaded {len(triplets)} preference pairs")

    # ── Build DPO dataset + loader ──
    dpo_ds = DPODataset(
        triplets, _TOKENIZER,
        include_schema=cfg.include_schema,
        schema_mode=cfg.schema_mode,
    )
    dpo_loader = DataLoader(
        dpo_ds, batch_size=cfg.batch_size,
        shuffle=True, collate_fn=dpo_collate_fn,
    )

    # ── Load dev data (for evaluation) ──
    _, dev_loader, test_loader = load_t5_data(
        cfg.batch_size, cfg.test_batch_size,
        input_prefix=cfg.input_prefix,
        include_schema=cfg.include_schema,
        schema_mode=getattr(cfg, "schema_mode", "tables"),
    )

    # ── Load base checkpoint and create policy + reference models ──
    print(f"Loading base checkpoint: {cfg.base_checkpoint_path}")
    assert os.path.exists(cfg.base_checkpoint_path), \
        f"Base checkpoint not found: {cfg.base_checkpoint_path}"

    # Build shared restricted vocab
    sql_vocab = FlightSQLVocab()
    sql_vocab.to(device)
    print(f"Restricted SQL vocab: {sql_vocab.vocab_size} tokens")

    # Policy model
    policy_base = initialize_model(
        finetune=True, model_checkpoint=cfg.model_checkpoint,
        dropout=cfg.dropout, device=device,
    )
    policy_state = torch.load(cfg.base_checkpoint_path,
                               map_location=device, weights_only=True)
    policy_base.load_state_dict(policy_state)
    policy_model = T5ForFlightSQL(policy_base, sql_vocab)
    print("Policy model loaded")

    # Apply LoRA if configured
    use_lora = getattr(cfg, "use_lora", False)
    if use_lora:
        from peft import LoraConfig as PeftLoraConfig, get_peft_model, TaskType
        lora_config = PeftLoraConfig(
            r=cfg.lora_r,
            lora_alpha=cfg.lora_alpha,
            lora_dropout=cfg.lora_dropout,
            target_modules=cfg.lora_target_modules,
            task_type=TaskType.SEQ_2_SEQ_LM,
        )
        policy_model.model = get_peft_model(policy_model.model, lora_config)
        trainable = sum(p.numel() for p in policy_model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in policy_model.parameters())
        print(f"LoRA applied: {trainable:,} trainable / {total:,} total params ({100*trainable/total:.2f}%)")
        ref_model = None  # LoRA uses disable_adapter instead of separate ref
    else:
        # Reference model (frozen copy)
        ref_base = initialize_model(
            finetune=True, model_checkpoint=cfg.model_checkpoint,
            dropout=cfg.dropout, device=device,
        )
        ref_state = torch.load(cfg.base_checkpoint_path,
                                map_location=device, weights_only=True)
        ref_base.load_state_dict(ref_state)
        ref_model = T5ForFlightSQL(ref_base, sql_vocab)
        ref_model.eval()
        for p in ref_model.parameters():
            p.requires_grad = False
        assert not any(p.requires_grad for p in ref_model.parameters()), \
            "Reference model has trainable parameters!"
        print("Reference model loaded and frozen")

    # ── Auto batch size ──
    if getattr(cfg, "auto_batch_size", False) and torch.cuda.is_available():
        optimal_bs = dpo_auto_batch_size(
            cfg, policy_model, ref_model, dpo_ds, device,
        )
        if optimal_bs != cfg.batch_size:
            print(f"Auto batch size: {cfg.batch_size} → {optimal_bs}")
            cfg.batch_size = optimal_bs
            # Rebuild loaders with optimal batch size
            dpo_loader = DataLoader(
                dpo_ds, batch_size=cfg.batch_size,
                shuffle=True, collate_fn=dpo_collate_fn,
            )
            _, dev_loader, test_loader = load_t5_data(
                cfg.batch_size, cfg.test_batch_size,
                input_prefix=cfg.input_prefix,
                include_schema=cfg.include_schema,
                schema_mode=getattr(cfg, "schema_mode", "tables"),
            )

    # ── Optimizer (policy only) ──
    optimizer = torch.optim.AdamW(
        policy_model.parameters(),
        lr=cfg.learning_rate,
        weight_decay=cfg.weight_decay,
    )

    # ── LR scheduler ──
    scheduler = _build_scheduler(cfg, optimizer, len(dpo_loader))

    # ── W&B setup ──
    run_dir, _ = setup_run(cfg, experiment_name="part1_dpo")
    print(f"Run directory: {run_dir}")
    print(f"Device: {device}")

    # Log model info
    total_params = sum(p.numel() for p in policy_model.parameters())
    trainable_params = sum(p.numel() for p in policy_model.parameters()
                          if p.requires_grad)
    log_extra_params({
        "total_params": total_params,
        "trainable_params": trainable_params,
        "num_preference_pairs": len(triplets),
        "num_dev_samples": len(dev_loader.dataset),
        "dpo_beta": cfg.dpo_beta,
        "base_checkpoint": cfg.base_checkpoint_path,
    })

    # ── Train ──
    best_val = dpo_train(
        cfg, policy_model, ref_model, dpo_loader, dev_loader,
        optimizer, scheduler, run_dir,
    )

    # ── Final eval: reload best checkpoint ──
    del policy_model
    cleanup_vram()

    ckpt_dir = str(run_dir / "checkpoints")
    best_ckpt = os.path.join(ckpt_dir, "model_best.pt")
    if os.path.exists(best_ckpt):
        final_base = load_model_from_checkpoint(
            ckpt_dir, finetune=True, model_checkpoint=cfg.model_checkpoint,
            dropout=cfg.dropout, best=True, device=device,
        )
        final_model = T5ForFlightSQL(final_base, sql_vocab)
        final_model.eval()
        print("\nReloaded best checkpoint for final evaluation")
    else:
        print("\nNo best checkpoint saved; using current model state")
        final_model = ref_model  # fallback
        final_model.eval()

    # Final dev eval (full beam search)
    from part1.train import eval_epoch
    f1, em, sql_em, err = eval_epoch(
        cfg, final_model, dev_loader,
        "data/dev.sql", "results/t5_dpo_dev.sql",
        "records/ground_truth_dev.pkl", "records/t5_dpo_dev.pkl",
        device,
    )
    print(f"Final dev: F1={f1:.4f}, EM={em:.4f}, "
          f"SQL_EM={sql_em:.4f}, err={err*100:.1f}%")

    # Test inference
    test_inference(
        cfg, final_model, test_loader,
        "results/t5_dpo_test.sql", "records/t5_dpo_test.pkl",
        device,
    )

    # ── Upload best model artifact to W&B ──
    if os.path.exists(best_ckpt):
        log_model_artifact(
            best_ckpt,
            artifact_name=f"{cfg.name}-best",
            metadata={"record_f1": best_val, "dpo_beta": cfg.dpo_beta},
        )

    # ── Cleanup ──
    end_run()
    del final_model, ref_model
    cleanup_vram()
    print("DPO training pipeline complete")


def main():
    from part1.config import T5DPOConfig, T5DPOConfig_lora

    args = parse_args()
    if args.use_lora:
        cfg = T5DPOConfig_lora()
    else:
        cfg = T5DPOConfig()
    apply_cli_overrides(cfg, args)
    main_with_config(cfg)


if __name__ == "__main__":
    from src.utils.gpu_lock import GpuLock
    with GpuLock():
        main()
