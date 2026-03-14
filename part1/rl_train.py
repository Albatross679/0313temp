"""GRPO/CISPO RL training for T5 encoder-decoder on NL-to-SQL.

Implements online RL fine-tuning following:
  - **GRPO** (Group Relative Policy Optimization): DeepSeekMath formulation
    with PPO-style clipped surrogate and group-relative advantages (no critic).
  - **CISPO** (Clipped Importance Sampling Policy Optimization): MiniMax-M1
    formulation with detached clamped IS weights that preserve gradient flow.

Adapts these decoder-only algorithms to the encoder-decoder setting by:
  1. Using compute_restricted_log_probs for both sequence-level and per-token
     log probabilities through the restricted SQL vocabulary projection.
  2. Generating completions via constrained decoding (prefix_allowed_tokens_fn)
     with temperature sampling for exploration.
  3. Computing execution-based rewards by running generated SQL against an
     in-memory copy of the flight database.

Pipeline per training step: SAMPLE -> REWARD -> ADVANTAGE -> LOSS -> UPDATE -> EVAL

Exports:
    sample_group_completions  - Generate G completions per query with constrained decoding
    compute_old_log_probs     - Recompute log probs under frozen/reference policy
    grpo_train_step           - Single RL training step (all phases combined)
    grpo_train                - Main training loop with eval, checkpointing, early stopping
    main_with_config          - Full pipeline entry point
    parse_args                - CLI argument parsing
    main                      - CLI entry point
"""

import argparse
import json
import os
import re
import time

import torch
from tqdm import tqdm

from part1.data import PAD_IDX, _TOKENIZER, _BOS_ID, _load_schema_string, load_t5_data
from part1.dpo_loss import compute_restricted_log_probs, _amp_context
from part1.dpo_data import _execute_sql, _get_mem_conn, _load_or_compute_gold_records
from part1.rl_loss import (
    grpo_loss, cispo_loss, cispo_loss_per_token,
    compute_group_advantages, compute_execution_reward, compute_kl_penalty,
)
from part1.rl_config import T5GRPOConfig, T5GRPOConfig_grpo, T5GRPOConfig_cispo
from part1.model import initialize_model, load_model_from_checkpoint, save_model
from part1.model_flightdb import FlightSQLVocab, T5ForFlightSQL
from part1.train import (
    eval_epoch_gpu, eval_epoch_sql, eval_epoch,
    cleanup_vram, stop_requested, test_inference,
)
from src.wandb_utils import (
    end_run, log_epoch_metrics, log_extra_params, log_model_artifact, setup_run,
)
from utils import compute_metrics, save_queries_and_records, set_random_seeds


# ======================================================================
#  Group sampling and reward computation
# ======================================================================

def sample_group_completions(model, vocab, tokenizer, nl_texts, gold_sql_list,
                             gold_records_list, mem_conn, cfg, device):
    """Generate G completions per query and compute execution rewards.

    This function handles the SAMPLE + REWARD phases of the GRPO/CISPO loop.

    Args:
        model: T5ForFlightSQL policy model (with or without LoRA)
        vocab: FlightSQLVocab instance for constrained decoding
        tokenizer: T5TokenizerFast for encoding/decoding
        nl_texts: list of B NL query strings
        gold_sql_list: list of B gold SQL strings
        gold_records_list: list of B gold record frozensets (or None)
        mem_conn: in-memory SQLite connection for SQL execution
        cfg: T5GRPOConfig instance
        device: torch device

    Returns:
        completions: list of B*G decoded SQL strings
        rewards: torch.Tensor of shape (B*G,) with execution rewards
        generated_ids: torch.Tensor of shape (B*G, T_gen) raw token IDs
    """
    B = len(nl_texts)
    G = cfg.group_size

    # Step 1: Prepend schema string to NL texts
    schema_str = _load_schema_string(mode=cfg.schema_mode)
    prefixed = [schema_str + t for t in nl_texts]

    # Step 2: Tokenize
    encoded = tokenizer(
        prefixed, padding=True, truncation=True, return_tensors="pt"
    )
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)

    # Step 4: Expand by group_size for group sampling
    expanded_input_ids = input_ids.repeat_interleave(G, dim=0)      # (B*G, T_enc)
    expanded_mask = attention_mask.repeat_interleave(G, dim=0)       # (B*G, T_enc)

    # Step 5: Generate completions with constrained decoding
    # Use inner HF model for .generate()
    gen_model = model.model
    with torch.inference_mode(), _amp_context(cfg.use_amp, device):
        outputs = gen_model.generate(
            input_ids=expanded_input_ids,
            attention_mask=expanded_mask,
            do_sample=True,
            temperature=cfg.sampling_temperature,
            top_k=cfg.sampling_top_k,
            num_return_sequences=1,
            decoder_start_token_id=32099,
            prefix_allowed_tokens_fn=vocab.get_prefix_allowed_tokens_fn(),
            max_new_tokens=cfg.max_new_tokens,
        )

    generated_ids = outputs  # (B*G, T_gen)

    # Step 6: Decode outputs
    decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)

    # Step 7: Post-process (same regex as DPO data generation)
    completions = [re.sub(r'(?<=[a-zA-Z0-9_)])\s*,\s*', ' , ', s) for s in decoded]

    # Step 8: Compute execution rewards
    # Expand gold data to match B*G flat structure
    rewards = []
    for i in range(B):
        for j in range(G):
            flat_idx = i * G + j
            reward = compute_execution_reward(
                completions[flat_idx],
                gold_sql_list[i],
                gold_records_list[i],
                mem_conn,
            )
            rewards.append(reward)

    rewards = torch.tensor(rewards, dtype=torch.float32, device=device)

    return completions, rewards, generated_ids


# ======================================================================
#  Old / reference log probability computation
# ======================================================================

def compute_old_log_probs(model, encoder_input, encoder_mask, generated_ids,
                          cfg, device, per_token=False):
    """Compute log probabilities of generated sequences under the reference policy.

    For LoRA models: disables adapter layers to get base model (reference) log probs.
    For non-LoRA: uses the model as-is (caller should pass the reference model).

    Args:
        model: T5ForFlightSQL policy model
        encoder_input: (B*G, T_enc) tokenized NL queries (already expanded)
        encoder_mask: (B*G, T_enc) attention mask
        generated_ids: (B*G, T_gen) token IDs from generate()
        cfg: T5GRPOConfig instance
        device: torch device
        per_token: if True, return (token_log_probs, mask) instead of sequence sums

    Returns:
        If per_token=False: (B*G,) sequence-level log probs (detached)
        If per_token=True: ((B*G, T) token_log_probs, (B*G, T) mask) (detached)
    """
    # Build decoder_input: prepend BOS to generated_ids[:, :-1]
    B_G = generated_ids.shape[0]
    bos = torch.full((B_G, 1), _BOS_ID, dtype=torch.long, device=device)
    decoder_input = torch.cat([bos, generated_ids[:, :-1]], dim=1)
    decoder_targets = generated_ids

    # Disable LoRA adapters to get reference policy log probs
    has_lora = cfg.use_lora and hasattr(model.model, 'disable_adapter_layers')
    if has_lora:
        model.model.disable_adapter_layers()

    with torch.no_grad(), _amp_context(cfg.use_amp, device):
        result = compute_restricted_log_probs(
            model, encoder_input, encoder_mask,
            decoder_input, decoder_targets,
            pad_idx=PAD_IDX, per_token=per_token,
        )

    # Re-enable LoRA adapters
    if has_lora:
        model.model.enable_adapter_layers()

    if per_token:
        token_logps, mask = result
        return token_logps.detach(), mask.detach()
    else:
        return result.detach()


# ======================================================================
#  RL training step
# ======================================================================

def grpo_train_step(policy_model, batch_nl, batch_gold_sql, batch_gold_records,
                    vocab, mem_conn, optimizer, cfg, device, grad_norm_ema,
                    global_step):
    """Single GRPO/CISPO training step combining all phases.

    Pipeline: SAMPLE -> ADVANTAGE -> OLD LOG PROBS -> UPDATE

    Args:
        policy_model: T5ForFlightSQL with LoRA
        batch_nl: list of B NL query strings
        batch_gold_sql: list of B gold SQL strings
        batch_gold_records: list of B gold record frozensets
        vocab: FlightSQLVocab instance
        mem_conn: in-memory SQLite connection
        optimizer: AdamW optimizer
        cfg: T5GRPOConfig instance
        device: torch device
        grad_norm_ema: float, EMA of gradient norms
        global_step: int, global training step counter

    Returns:
        metrics: dict with loss, grad_norm, mean_reward, zero_std_frac,
                 clip_frac, mean_ratio, kl_penalty, grad_spike_skipped,
                 grad_norm_ema
        updated_grad_norm_ema: float
    """
    B = len(batch_nl)
    G = cfg.group_size
    tokenizer = _TOKENIZER
    use_per_token = (cfg.rl_algorithm == "cispo")

    # ── SAMPLE PHASE ──
    policy_model.eval()  # generation mode
    completions, rewards, generated_ids = sample_group_completions(
        policy_model, vocab, tokenizer, batch_nl, batch_gold_sql,
        batch_gold_records, mem_conn, cfg, device,
    )
    policy_model.train()  # back to training mode

    # ── ADVANTAGE PHASE ──
    advantages, zero_std_frac = compute_group_advantages(
        rewards, G, cfg.use_std_normalization,
    )

    # Dead group handling: zero out advantages for dead groups
    if cfg.skip_dead_groups:
        grouped_rewards = rewards.view(B, G)
        group_std = grouped_rewards.std(dim=1)
        dead_mask = (group_std < 1e-6)  # (B,)
        # Expand to (B*G,)
        dead_mask_expanded = dead_mask.repeat_interleave(G)
        advantages = advantages * (~dead_mask_expanded).float()

    # ── PREPARE ENCODER INPUTS for log prob computation ──
    schema_str = _load_schema_string(mode=cfg.schema_mode)
    prefixed = [schema_str + t for t in batch_nl]
    encoded = tokenizer(prefixed, padding=True, truncation=True, return_tensors="pt")
    encoder_input = encoded["input_ids"].to(device).repeat_interleave(G, dim=0)
    encoder_mask = encoded["attention_mask"].to(device).repeat_interleave(G, dim=0)

    # ── OLD LOG PROB PHASE (reference policy) ──
    if use_per_token:
        old_logps, old_mask = compute_old_log_probs(
            policy_model, encoder_input, encoder_mask, generated_ids,
            cfg, device, per_token=True,
        )
        old_seq_logps = compute_old_log_probs(
            policy_model, encoder_input, encoder_mask, generated_ids,
            cfg, device, per_token=False,
        )
    else:
        old_logps = compute_old_log_probs(
            policy_model, encoder_input, encoder_mask, generated_ids,
            cfg, device, per_token=False,
        )

    # ── UPDATE PHASE (gradients enabled) ──
    B_G = generated_ids.shape[0]
    bos = torch.full((B_G, 1), _BOS_ID, dtype=torch.long, device=device)
    decoder_input = torch.cat([bos, generated_ids[:, :-1]], dim=1)
    decoder_targets = generated_ids

    # Current policy log probs (with gradients)
    with _amp_context(cfg.use_amp, device):
        if use_per_token:
            current_token_logps, current_mask = compute_restricted_log_probs(
                policy_model, encoder_input, encoder_mask,
                decoder_input, decoder_targets,
                pad_idx=PAD_IDX, per_token=True,
            )
            # Also need sequence-level for KL if needed
            current_seq_logps = (current_token_logps * current_mask).sum(dim=-1)
        else:
            current_logps = compute_restricted_log_probs(
                policy_model, encoder_input, encoder_mask,
                decoder_input, decoder_targets,
                pad_idx=PAD_IDX, per_token=False,
            )

    # Select loss function
    if cfg.rl_algorithm == "cispo" and use_per_token:
        loss, diag = cispo_loss_per_token(
            current_token_logps, old_logps, advantages,
            current_mask, cfg.epsilon_high,
        )
    elif cfg.rl_algorithm == "cispo":
        loss, diag = cispo_loss(
            current_logps, old_logps, advantages, cfg.epsilon_high,
        )
    else:
        # GRPO
        loss, diag = grpo_loss(
            current_logps, old_logps, advantages, cfg.epsilon,
        )

    # KL penalty
    kl_penalty_val = 0.0
    if cfg.kl_beta > 0:
        if use_per_token:
            kl = compute_kl_penalty(current_seq_logps, old_seq_logps)
        else:
            kl = compute_kl_penalty(current_logps, old_logps)
        loss = loss + cfg.kl_beta * kl
        kl_penalty_val = kl.item()

    # Backward
    optimizer.zero_grad()
    loss.backward()

    # Gradient clipping
    grad_norm = torch.nn.utils.clip_grad_norm_(
        policy_model.parameters(), cfg.grad_clip_norm,
    ).item()

    # Gradient norm spike detection
    grad_spike_skipped = False
    if grad_norm_ema > 0 and grad_norm > cfg.max_grad_norm_spike_factor * grad_norm_ema:
        # Skip this optimizer step
        optimizer.zero_grad()
        grad_spike_skipped = True

    # Update EMA
    if grad_norm_ema <= 0:
        # Initialize EMA with first observed grad norm
        grad_norm_ema = grad_norm
    else:
        grad_norm_ema = (cfg.grad_norm_ema_decay * grad_norm_ema
                         + (1 - cfg.grad_norm_ema_decay) * grad_norm)

    # Step optimizer (unless spike was detected)
    if not grad_spike_skipped:
        optimizer.step()

    # Compile metrics
    metrics = {
        "loss": loss.item(),
        "grad_norm": grad_norm,
        "mean_reward": rewards.mean().item(),
        "zero_std_frac": zero_std_frac,
        "clip_frac": diag["clip_frac"],
        "mean_ratio": diag["mean_ratio"],
        "kl_penalty": kl_penalty_val,
        "grad_spike_skipped": float(grad_spike_skipped),
        "grad_norm_ema": grad_norm_ema,
    }

    return metrics, grad_norm_ema


# ======================================================================
#  Main training loop
# ======================================================================

def grpo_train(cfg, policy_model, train_nl, train_sql, train_gold_records,
               dev_loader, vocab, mem_conn, optimizer, run_dir):
    """GRPO/CISPO training loop.

    Follows the same structural pattern as dpo_train() in dpo_train.py:
    epoch loop -> mini-batch loop -> eval -> checkpoint -> early stop.

    Args:
        cfg: T5GRPOConfig instance
        policy_model: T5ForFlightSQL with LoRA
        train_nl: list of NL query strings (training set)
        train_sql: list of gold SQL strings (training set)
        train_gold_records: list of gold record frozensets
        dev_loader: DataLoader for dev set evaluation
        vocab: FlightSQLVocab instance
        mem_conn: in-memory SQLite connection
        optimizer: AdamW optimizer
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

    gt_sql_path = "data/dev.sql"
    gt_record_path = "records/ground_truth_dev.pkl"
    global_step = 0
    grad_norm_ema = 0.0

    num_train = len(train_nl)

    for epoch in range(cfg.num_epochs):
        epoch_start = time.time()
        policy_model.train()

        # Shuffle training data indices each epoch (on-policy: fresh samples)
        indices = torch.randperm(num_train).tolist()

        # Epoch accumulators
        epoch_loss = 0.0
        epoch_mean_reward = 0.0
        epoch_zero_std_frac = 0.0
        epoch_clip_frac = 0.0
        epoch_mean_ratio = 0.0
        epoch_kl_penalty = 0.0
        epoch_grad_norm = 0.0
        epoch_grad_spikes = 0
        num_batches = 0

        # ── Mini-batch loop ──
        for batch_start in range(0, num_train, cfg.batch_size):
            batch_end = min(batch_start + cfg.batch_size, num_train)
            batch_indices = indices[batch_start:batch_end]

            batch_nl = [train_nl[i] for i in batch_indices]
            batch_gold_sql = [train_sql[i] for i in batch_indices]
            batch_gold_records = [train_gold_records[i] for i in batch_indices]

            metrics, grad_norm_ema = grpo_train_step(
                policy_model, batch_nl, batch_gold_sql, batch_gold_records,
                vocab, mem_conn, optimizer, cfg, device,
                grad_norm_ema, global_step,
            )

            # Accumulate epoch metrics
            epoch_loss += metrics["loss"]
            epoch_mean_reward += metrics["mean_reward"]
            epoch_zero_std_frac += metrics["zero_std_frac"]
            epoch_clip_frac += metrics["clip_frac"]
            epoch_mean_ratio += metrics["mean_ratio"]
            epoch_kl_penalty += metrics["kl_penalty"]
            epoch_grad_norm += metrics["grad_norm"]
            epoch_grad_spikes += int(metrics["grad_spike_skipped"])
            num_batches += 1

            # Log batch-level metrics to W&B
            log_epoch_metrics({
                "batch/loss": metrics["loss"],
                "batch/gradient_norm": metrics["grad_norm"],
                "batch/mean_reward": metrics["mean_reward"],
                "batch/clip_frac": metrics["clip_frac"],
            }, step=global_step)
            global_step += 1

        # Compute epoch averages
        avg_loss = epoch_loss / num_batches
        avg_mean_reward = epoch_mean_reward / num_batches
        avg_zero_std_frac = epoch_zero_std_frac / num_batches
        avg_clip_frac = epoch_clip_frac / num_batches
        avg_mean_ratio = epoch_mean_ratio / num_batches
        avg_kl_penalty = epoch_kl_penalty / num_batches
        avg_grad_norm = epoch_grad_norm / num_batches

        train_epoch_seconds = time.time() - epoch_start

        # Print epoch summary
        print(f"Epoch {epoch}: RL loss = {avg_loss:.4f}, "
              f"mean_reward = {avg_mean_reward:.3f}, "
              f"clip_frac = {avg_clip_frac:.3f}, "
              f"dead_groups = {avg_zero_std_frac:.3f}")

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

            # Log epoch metrics to W&B
            log_epoch_metrics({
                "epoch": epoch,
                "train_loss": avg_loss,
                "record_f1": record_f1,
                "record_em": record_em,
                "sql_em": sql_em,
                "error_rate": error_rate,
                "gradient_norm": avg_grad_norm,
                "lr": optimizer.param_groups[0]["lr"],
                "rl/mean_reward": avg_mean_reward,
                "rl/zero_std_frac": avg_zero_std_frac,
                "rl/clip_frac": avg_clip_frac,
                "rl/mean_ratio": avg_mean_ratio,
                "rl/kl_penalty": avg_kl_penalty,
                "rl/grad_spikes_skipped": epoch_grad_spikes,
            }, step=epoch)
            log_epoch_metrics({
                "timing/epoch_seconds": epoch_time,
                "timing/wall_clock_seconds": wall_clock,
            }, step=epoch)

            # Checkpointing on dev Record F1
            improved = record_f1 > best_val
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
        else:
            # Non-eval epoch: just log training metrics
            log_epoch_metrics({
                "epoch": epoch,
                "train_loss": avg_loss,
                "gradient_norm": avg_grad_norm,
                "lr": optimizer.param_groups[0]["lr"],
                "rl/mean_reward": avg_mean_reward,
                "rl/zero_std_frac": avg_zero_std_frac,
                "rl/clip_frac": avg_clip_frac,
                "rl/mean_ratio": avg_mean_ratio,
                "rl/kl_penalty": avg_kl_penalty,
                "rl/grad_spikes_skipped": epoch_grad_spikes,
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
    print(f"\nGRPO/CISPO training complete: {total_time/60:.1f} min, "
          f"best dev F1 = {best_val:.4f}")

    if best_metrics:
        print(f"Best metrics: F1={best_metrics['record_f1']:.4f}, "
              f"EM={best_metrics['record_em']:.4f}, "
              f"SQL_EM={best_metrics['sql_em']:.4f}")

    return best_val


# ======================================================================
#  Entry point
# ======================================================================

def main_with_config(cfg):
    """Run the full GRPO/CISPO training pipeline with a pre-built config.

    Used by: main() (CLI entry), sweep scripts, and any programmatic caller
    that constructs a config object directly.
    """
    set_random_seeds(cfg.seed)
    device = cfg.device

    # ── Load training data (NL + SQL) ──
    with open("data/train.nl") as f:
        train_nl = [line.strip() for line in f.readlines()]
    with open("data/train.sql") as f:
        train_sql = [line.strip() for line in f.readlines()]
    assert len(train_nl) == len(train_sql), (
        f"NL/SQL mismatch: {len(train_nl)} vs {len(train_sql)}"
    )
    print(f"Loaded {len(train_nl)} training examples")

    # ── Load gold records (cached) ──
    train_gold_records = _load_or_compute_gold_records(train_sql)

    # ── Load dev data (for evaluation via DataLoader) ──
    _, dev_loader, test_loader = load_t5_data(
        cfg.batch_size, cfg.test_batch_size,
        input_prefix=cfg.input_prefix,
        include_schema=cfg.include_schema,
        schema_mode=getattr(cfg, "schema_mode", "tables"),
    )

    # ── Build restricted vocab ──
    sql_vocab = FlightSQLVocab()
    sql_vocab.to(device)
    print(f"Restricted SQL vocab: {sql_vocab.vocab_size} tokens")

    # ── Load base checkpoint ──
    print(f"Loading base checkpoint: {cfg.base_checkpoint_path}")
    assert os.path.exists(cfg.base_checkpoint_path), \
        f"Base checkpoint not found: {cfg.base_checkpoint_path}"

    policy_base = initialize_model(
        finetune=True, model_checkpoint=cfg.model_checkpoint,
        dropout=cfg.dropout, device=device,
    )
    policy_state = torch.load(
        cfg.base_checkpoint_path, map_location=device, weights_only=True,
    )
    policy_base.load_state_dict(policy_state)
    policy_model = T5ForFlightSQL(policy_base, sql_vocab)
    print("Policy model loaded from base checkpoint")

    # ── Apply LoRA ──
    if cfg.use_lora:
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
        print(f"LoRA applied (r={cfg.lora_r}, alpha={cfg.lora_alpha}): "
              f"{trainable:,} trainable / {total:,} total params "
              f"({100*trainable/total:.2f}%)")

    # ── Optimizer ──
    optimizer = torch.optim.AdamW(
        [p for p in policy_model.parameters() if p.requires_grad],
        lr=cfg.learning_rate,
        weight_decay=cfg.weight_decay,
    )

    # ── W&B setup ──
    run_dir, _ = setup_run(cfg, experiment_name="part1_grpo")
    print(f"Run directory: {run_dir}")
    print(f"Device: {device}")

    # Log model info
    total_params = sum(p.numel() for p in policy_model.parameters())
    trainable_params = sum(p.numel() for p in policy_model.parameters()
                          if p.requires_grad)
    log_extra_params({
        "total_params": total_params,
        "trainable_params": trainable_params,
        "num_train_samples": len(train_nl),
        "num_dev_samples": len(dev_loader.dataset),
        "group_size": cfg.group_size,
        "rl_algorithm": cfg.rl_algorithm,
        "kl_beta": cfg.kl_beta,
        "epsilon": cfg.epsilon,
        "epsilon_high": cfg.epsilon_high,
        "base_checkpoint": cfg.base_checkpoint_path,
    })

    # ── Initialize in-memory SQLite ──
    mem_conn = _get_mem_conn()

    # ── Train ──
    best_val = grpo_train(
        cfg, policy_model, train_nl, train_sql, train_gold_records,
        dev_loader, sql_vocab, mem_conn, optimizer, run_dir,
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
        print("\nNo best checkpoint saved; skipping final evaluation")
        end_run()
        cleanup_vram()
        return best_val

    # Final dev eval (full beam search)
    f1, em, sql_em, err = eval_epoch(
        cfg, final_model, dev_loader,
        "data/dev.sql", "results/t5_grpo_dev.sql",
        "records/ground_truth_dev.pkl", "records/t5_grpo_dev.pkl",
        device,
    )
    print(f"Final dev: F1={f1:.4f}, EM={em:.4f}, "
          f"SQL_EM={sql_em:.4f}, err={err*100:.1f}%")

    # Test inference
    test_inference(
        cfg, final_model, test_loader,
        "results/t5_grpo_test.sql", "records/t5_grpo_test.pkl",
        device,
    )

    # ── Upload best model artifact to W&B ──
    if os.path.exists(best_ckpt):
        log_model_artifact(
            best_ckpt,
            artifact_name=f"{cfg.name}-best",
            metadata={
                "record_f1": best_val,
                "rl_algorithm": cfg.rl_algorithm,
                "group_size": cfg.group_size,
            },
        )

    # ── Cleanup ──
    end_run()
    del final_model
    cleanup_vram()
    print("GRPO/CISPO training pipeline complete")

    return best_val


# ======================================================================
#  CLI
# ======================================================================

def parse_args():
    """Parse CLI arguments for RL training."""
    parser = argparse.ArgumentParser(
        description="GRPO/CISPO RL training for T5 NL-to-SQL"
    )
    parser.add_argument("--rl_algorithm", type=str, default=None,
                        choices=["grpo", "cispo"],
                        help="RL algorithm: grpo or cispo")
    parser.add_argument("--group_size", type=int, default=None)
    parser.add_argument("--epsilon", type=float, default=None)
    parser.add_argument("--epsilon_high", type=float, default=None)
    parser.add_argument("--kl_beta", type=float, default=None)
    parser.add_argument("--learning_rate", type=float, default=None)
    parser.add_argument("--num_epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--patience_epochs", type=int, default=None)
    parser.add_argument("--base_checkpoint_path", type=str, default=None)
    parser.add_argument("--max_wall_clock_hours", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", type=str, default=None)
    return parser.parse_args()


def apply_cli_overrides(cfg, args):
    """Apply non-None CLI args to config."""
    for attr in ("rl_algorithm", "group_size", "epsilon", "epsilon_high",
                 "kl_beta", "learning_rate", "num_epochs", "batch_size",
                 "patience_epochs", "base_checkpoint_path",
                 "max_wall_clock_hours", "seed", "name"):
        val = getattr(args, attr, None)
        if val is not None:
            setattr(cfg, attr, val)


def main():
    """CLI entry point: parse args, select config variant, run pipeline."""
    args = parse_args()
    if args.rl_algorithm == "cispo":
        cfg = T5GRPOConfig_cispo()
    else:
        cfg = T5GRPOConfig_grpo()
    apply_cli_overrides(cfg, args)
    main_with_config(cfg)


if __name__ == "__main__":
    from src.utils.gpu_lock import GpuLock
    with GpuLock():
        main()
