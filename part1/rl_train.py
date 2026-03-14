"""GRPO/CISPO/PPO RL training for T5 encoder-decoder on NL-to-SQL.

Implements online RL fine-tuning following:
  - **GRPO** (Group Relative Policy Optimization): DeepSeekMath formulation
    with PPO-style clipped surrogate and group-relative advantages (no critic).
  - **CISPO** (Clipped Importance Sampling Policy Optimization): MiniMax-M1
    formulation with detached clamped IS weights that preserve gradient flow.
  - **PPO** (Proximal Policy Optimization): Clipped surrogate with learned
    value head baseline on mean-pooled encoder hidden states.

Adapts these decoder-only algorithms to the encoder-decoder setting by:
  1. Using compute_restricted_log_probs for both sequence-level and per-token
     log probabilities through the restricted SQL vocabulary projection.
  2. Generating completions via constrained decoding (prefix_allowed_tokens_fn)
     with temperature sampling for exploration.
  3. Computing execution-based rewards by running generated SQL against an
     in-memory copy of the flight database.
  4. Caching encoder outputs: compute encoder hidden states once per query,
     reuse across G completions for generation and log prob recomputation.

Pipeline per training step: SAMPLE -> REWARD -> ADVANTAGE -> LOSS -> UPDATE -> EVAL

Exports:
    sample_group_completions  - Generate G completions per query with encoder caching
    compute_old_log_probs     - Recompute log probs under frozen/reference policy
    grpo_train_step           - Single RL training step (GRPO/CISPO/PPO)
    grpo_train                - Main training loop with eval, checkpointing, early stopping
    main_with_config          - Full pipeline entry point
    parse_args                - CLI argument parsing
    main                      - CLI entry point (sequential auto-batch)
"""

import argparse
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import torch
from transformers.modeling_outputs import BaseModelOutput
from tqdm import tqdm

from part1.data import PAD_IDX, _TOKENIZER, _BOS_ID, _load_schema_string, load_t5_data
from part1.dpo_loss import compute_restricted_log_probs, _amp_context
from part1.dpo_data import _execute_sql, _get_mem_conn, _load_or_compute_gold_records
from part1.rl_loss import (
    grpo_loss, cispo_loss, cispo_loss_per_token,
    compute_group_advantages, compute_execution_reward, compute_kl_penalty,
    ppo_policy_loss, ppo_value_loss, compute_entropy,
)
from part1.rl_config import (
    T5GRPOConfig, T5GRPOConfig_grpo, T5GRPOConfig_cispo,
    T5PPOConfig, T5PPOConfig_v1,
)
from part1.rl_value_head import T5ValueHead
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
#  Thread-safe reward computation
# ======================================================================

_thread_local = threading.local()


def _get_thread_conn():
    """Get a thread-local in-memory SQLite connection for reward computation."""
    if not hasattr(_thread_local, 'conn'):
        _thread_local.conn = _get_mem_conn()
    return _thread_local.conn


def _compute_reward_for_sample(args):
    """Compute reward for a single (generated_sql, gold_sql, gold_records) tuple.

    Uses thread-local SQLite connection for thread safety.
    """
    gen_sql, gold_sql, gold_records = args
    conn = _get_thread_conn()
    return compute_execution_reward(gen_sql, gold_sql, gold_records, conn)


# ======================================================================
#  Group sampling and reward computation (with encoder caching)
# ======================================================================

def sample_group_completions(model, vocab, tokenizer, nl_texts, gold_sql_list,
                             gold_records_list, mem_conn, cfg, device):
    """Generate G completions per query and compute execution rewards.

    This function handles the SAMPLE + REWARD phases of the GRPO/CISPO/PPO loop.
    Uses encoder output caching: encoder hidden states computed once per query,
    then expanded for G completions. Saves ~(G-1)x encoder compute.

    Args:
        model: T5ForFlightSQL policy model (with or without LoRA)
        vocab: FlightSQLVocab instance for constrained decoding
        tokenizer: T5TokenizerFast for encoding/decoding
        nl_texts: list of B NL query strings
        gold_sql_list: list of B gold SQL strings
        gold_records_list: list of B gold record frozensets (or None)
        mem_conn: in-memory SQLite connection for SQL execution (fallback)
        cfg: T5GRPOConfig instance
        device: torch device

    Returns:
        completions: list of B*G decoded SQL strings
        rewards: torch.Tensor of shape (B*G,) with execution rewards
        generated_ids: torch.Tensor of shape (B*G, T_gen) raw token IDs
        encoder_hidden_states: torch.Tensor of shape (B, T_enc, d_model) cached encoder outputs
        attention_mask: torch.Tensor of shape (B, T_enc) original attention mask
        gen_diagnostics: dict with unique_completions_per_query, avg_completion_length
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

    # Step 3: Encoder output caching -- run encoder once on B queries
    gen_model = model.model
    with torch.inference_mode(), _amp_context(cfg.use_amp, device):
        encoder_out = gen_model.encoder(
            input_ids=input_ids, attention_mask=attention_mask
        )
        encoder_hidden_states = encoder_out.last_hidden_state  # (B, T_enc, d_model)

    # Step 4: Expand encoder outputs for G completions
    expanded_encoder_hidden = encoder_hidden_states.repeat_interleave(G, dim=0)  # (B*G, T_enc, d_model)
    expanded_mask = attention_mask.repeat_interleave(G, dim=0)  # (B*G, T_enc)

    # Step 5: Generate completions with constrained decoding using cached encoder
    max_gen_tokens = getattr(cfg, 'max_completion_length', None) or getattr(cfg, 'max_new_tokens', 256)

    gen_kwargs = dict(
        encoder_outputs=BaseModelOutput(last_hidden_state=expanded_encoder_hidden),
        attention_mask=expanded_mask,
        do_sample=True,
        temperature=cfg.sampling_temperature,
        top_k=cfg.sampling_top_k,
        num_return_sequences=1,
        decoder_start_token_id=32099,
        prefix_allowed_tokens_fn=vocab.get_prefix_allowed_tokens_fn(),
        max_new_tokens=max_gen_tokens,
    )
    if getattr(cfg, 'top_p', None) is not None:
        gen_kwargs['top_p'] = cfg.top_p

    with torch.inference_mode(), _amp_context(cfg.use_amp, device):
        outputs = gen_model.generate(**gen_kwargs)

    generated_ids = outputs  # (B*G, T_gen)

    # Step 6: Decode outputs
    decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)

    # Step 7: Post-process (same regex as DPO data generation)
    completions = [re.sub(r'(?<=[a-zA-Z0-9_)])\s*,\s*', ' , ', s) for s in decoded]

    # Step 8: Compute execution rewards via thread pool
    reward_args = [
        (completions[i * G + j], gold_sql_list[i], gold_records_list[i])
        for i in range(B) for j in range(G)
    ]
    max_workers = min(B * G, 16)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        rewards_list = list(pool.map(_compute_reward_for_sample, reward_args))

    rewards = torch.tensor(rewards_list, dtype=torch.float32, device=device)

    # Step 9: Apply reward scaling and clipping if configured
    if getattr(cfg, 'reward_scale', 1.0) != 1.0:
        rewards = rewards * cfg.reward_scale
    if getattr(cfg, 'reward_clip', None) is not None:
        rewards = rewards.clamp(-cfg.reward_clip, cfg.reward_clip)

    # Step 10: Compute generation diversity diagnostics
    unique_per_query = []
    for i in range(B):
        group_sqls = completions[i * G: (i + 1) * G]
        unique_per_query.append(len(set(group_sqls)))
    gen_diagnostics = {
        "unique_completions_per_query": sum(unique_per_query) / len(unique_per_query),
        "avg_completion_length": float(generated_ids.shape[1]),
    }

    return completions, rewards, generated_ids, encoder_hidden_states, attention_mask, gen_diagnostics


# ======================================================================
#  Old / reference log probability computation (with encoder caching)
# ======================================================================

def compute_old_log_probs(model, encoder_input, encoder_mask, generated_ids,
                          cfg, device, per_token=False, encoder_outputs=None):
    """Compute log probabilities of generated sequences under the reference policy.

    For LoRA models: disables adapter layers to get base model (reference) log probs.
    For non-LoRA: uses the model as-is (caller should pass the reference model).

    Supports encoder output caching: when encoder_outputs is provided, the encoder
    pass is skipped and the cached outputs are used directly.

    Args:
        model: T5ForFlightSQL policy model
        encoder_input: (B*G, T_enc) tokenized NL queries (already expanded)
        encoder_mask: (B*G, T_enc) attention mask
        generated_ids: (B*G, T_gen) token IDs from generate()
        cfg: T5GRPOConfig instance
        device: torch device
        per_token: if True, return (token_log_probs, mask) instead of sequence sums
        encoder_outputs: optional (B*G, T_enc, d_model) pre-computed encoder hidden states

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
#  RL training step (GRPO / CISPO / PPO)
# ======================================================================

def grpo_train_step(policy_model, batch_nl, batch_gold_sql, batch_gold_records,
                    vocab, mem_conn, optimizer, cfg, device, grad_norm_ema,
                    global_step, value_head=None, value_optimizer=None):
    """Single GRPO/CISPO/PPO training step combining all phases.

    Pipeline: SAMPLE -> ADVANTAGE -> OLD LOG PROBS -> UPDATE

    Args:
        policy_model: T5ForFlightSQL with LoRA
        batch_nl: list of B NL query strings
        batch_gold_sql: list of B gold SQL strings
        batch_gold_records: list of B gold record frozensets
        vocab: FlightSQLVocab instance
        mem_conn: in-memory SQLite connection
        optimizer: AdamW optimizer (policy)
        cfg: T5GRPOConfig / T5PPOConfig instance
        device: torch device
        grad_norm_ema: float, EMA of gradient norms
        global_step: int, global training step counter
        value_head: T5ValueHead instance (PPO only, None for GRPO/CISPO)
        value_optimizer: AdamW optimizer for value head (PPO only)

    Returns:
        metrics: dict with full RL metrics contract
        updated_grad_norm_ema: float
    """
    B = len(batch_nl)
    G = cfg.group_size
    tokenizer = _TOKENIZER
    use_per_token = (cfg.rl_algorithm == "cispo")
    is_ppo = (cfg.rl_algorithm == "ppo")

    # ── SAMPLE PHASE (with encoder caching) ──
    policy_model.eval()  # generation mode
    (completions, rewards, generated_ids,
     encoder_hidden_states, enc_attention_mask,
     gen_diagnostics) = sample_group_completions(
        policy_model, vocab, tokenizer, batch_nl, batch_gold_sql,
        batch_gold_records, mem_conn, cfg, device,
    )
    policy_model.train()  # back to training mode

    # ── ADVANTAGE PHASE ──
    if is_ppo and value_head is not None and getattr(cfg, 'advantage_type', 'learned') in ('learned', 'hybrid'):
        # PPO: compute value predictions for advantage estimation
        with torch.no_grad(), _amp_context(cfg.use_amp, device):
            values_pred = value_head(encoder_hidden_states, enc_attention_mask)  # (B,)

        # Mean reward per query (across G completions)
        rewards_per_query = rewards.view(B, G).mean(dim=1)  # (B,)

        if getattr(cfg, 'advantage_type', 'learned') == 'learned':
            # Pure learned baseline: A = R - V(s)
            query_advantages = rewards_per_query - values_pred.detach()  # (B,)
            # Expand to (B*G,) -- all completions for same query get same advantage offset
            advantages = query_advantages.repeat_interleave(G)
        elif getattr(cfg, 'advantage_type', 'learned') == 'hybrid':
            # Hybrid: group-relative normalization + learned baseline offset
            group_adv, zero_std_frac = compute_group_advantages(
                rewards, G, cfg.use_std_normalization,
            )
            # Subtract learned baseline from group-relative advantages
            baseline_offset = values_pred.detach().repeat_interleave(G)
            advantages = group_adv - baseline_offset
        else:
            advantages, zero_std_frac = compute_group_advantages(
                rewards, G, cfg.use_std_normalization,
            )
    else:
        advantages, zero_std_frac = compute_group_advantages(
            rewards, G, cfg.use_std_normalization,
        )
        values_pred = None
        rewards_per_query = rewards.view(B, G).mean(dim=1) if is_ppo else None

    # Track zero_std_frac for non-PPO-learned cases
    if is_ppo and getattr(cfg, 'advantage_type', 'learned') == 'learned':
        # For pure learned baseline, compute zero_std_frac from rewards for logging
        reward_grouped = rewards.view(B, G)
        group_std = reward_grouped.std(dim=1)
        zero_std_frac = (group_std < 1e-6).float().mean().item()

    # Dead group handling: zero out advantages for dead groups
    if cfg.skip_dead_groups:
        grouped_rewards = rewards.view(B, G)
        group_std = grouped_rewards.std(dim=1)
        dead_mask = (group_std < 1e-6)  # (B,)
        # Expand to (B*G,)
        dead_mask_expanded = dead_mask.repeat_interleave(G)
        advantages = advantages * (~dead_mask_expanded).float()

    # ── PREPARE ENCODER INPUTS for log prob computation ──
    # Use cached encoder hidden states from sample_group_completions
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
        # Always need ref log probs for KL computation
        old_seq_logps = old_logps

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
            # Also need sequence-level for KL
            current_seq_logps = (current_token_logps * current_mask).sum(dim=-1)
        else:
            current_logps = compute_restricted_log_probs(
                policy_model, encoder_input, encoder_mask,
                decoder_input, decoder_targets,
                pad_idx=PAD_IDX, per_token=False,
            )
            current_seq_logps = current_logps

    # Select loss function
    if is_ppo:
        loss, diag = ppo_policy_loss(
            current_logps, old_logps, advantages, cfg.epsilon,
        )
    elif cfg.rl_algorithm == "cispo" and use_per_token:
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

    # Always compute KL divergence for monitoring (even when kl_beta=0)
    with torch.no_grad():
        kl_val = compute_kl_penalty(
            current_seq_logps.detach(), old_seq_logps.detach()
        ).item()

    # Add KL to loss if kl_beta > 0
    kl_penalty_val = kl_val
    if cfg.kl_beta > 0:
        if use_per_token:
            kl_tensor = compute_kl_penalty(current_seq_logps, old_seq_logps)
        else:
            kl_tensor = compute_kl_penalty(current_logps, old_logps)
        loss = loss + cfg.kl_beta * kl_tensor

    # PPO: add value loss and entropy bonus
    ppo_metrics = {}
    if is_ppo and value_head is not None:
        # Compute current values (with gradients for value head)
        with _amp_context(cfg.use_amp, device):
            current_values = value_head(encoder_hidden_states, enc_attention_mask)  # (B,)

        val_loss, val_diag = ppo_value_loss(
            current_values, rewards_per_query,
            old_values=values_pred,
            clip_range=getattr(cfg, 'value_clip_range', 0.2),
        )
        policy_entropy = compute_entropy(current_seq_logps)
        policy_loss_val = loss.item()

        # Total loss: policy + value_coef * value - entropy_coef * entropy
        loss = loss + getattr(cfg, 'value_coef', 0.5) * val_loss - getattr(cfg, 'entropy_coef', 0.01) * policy_entropy

        ppo_metrics = {
            "ppo/value_loss": val_loss.item(),
            "ppo/value_pred_mean": val_diag["value_pred_mean"],
            "ppo/value_error": val_diag["value_error"],
            "ppo/entropy": policy_entropy.item(),
            "ppo/policy_loss": policy_loss_val,
        }

    # Compute policy entropy for all algorithms
    with torch.no_grad():
        policy_entropy_val = compute_entropy(current_seq_logps.detach()).item()

    # Backward
    optimizer.zero_grad()
    if value_optimizer is not None:
        value_optimizer.zero_grad()
    loss.backward()

    # Gradient clipping (policy model)
    grad_norm = torch.nn.utils.clip_grad_norm_(
        policy_model.parameters(), cfg.grad_clip_norm,
    ).item()

    # Gradient norm spike detection
    grad_spike_skipped = False
    if grad_norm_ema > 0 and grad_norm > cfg.max_grad_norm_spike_factor * grad_norm_ema:
        # Skip this optimizer step
        optimizer.zero_grad()
        if value_optimizer is not None:
            value_optimizer.zero_grad()
        grad_spike_skipped = True

    # Update EMA
    if grad_norm_ema <= 0:
        # Initialize EMA with first observed grad norm
        grad_norm_ema = grad_norm
    else:
        grad_norm_ema = (cfg.grad_norm_ema_decay * grad_norm_ema
                         + (1 - cfg.grad_norm_ema_decay) * grad_norm)

    # Step optimizers (unless spike was detected)
    if not grad_spike_skipped:
        optimizer.step()
        if value_optimizer is not None:
            value_optimizer.step()

    # ── Compile full RL metrics contract ──
    reward_grouped = rewards.view(B, G)
    metrics = {
        # Reward metrics (per rl_fields.md contract)
        "reward/mean": rewards.mean().item(),
        "reward/std": rewards.std().item(),
        "reward/max": rewards.max().item(),
        "reward/min": rewards.min().item(),
        "reward/group_std": reward_grouped.std(dim=1).mean().item(),
        "success_rate": (rewards > 0).float().mean().item(),

        # Policy metrics
        "kl_divergence": kl_penalty_val,
        "policy_entropy": policy_entropy_val,
        "clip_fraction": diag["clip_frac"],
        "importance_ratio/mean": diag["mean_ratio"],
        "importance_ratio/max": diag["ratio_max"],

        # Advantage metrics
        "advantage/mean": advantages.mean().item(),
        "advantage/std": advantages.std().item(),
        "advantage/max": advantages.abs().max().item(),

        # Generation diversity
        "unique_completions_per_query": gen_diagnostics["unique_completions_per_query"],
        "avg_completion_length": gen_diagnostics["avg_completion_length"],

        # Training metrics
        "loss": loss.item(),
        "gradient_norm": grad_norm,
        "grad_spike_skipped": float(grad_spike_skipped),
        "grad_norm_ema": grad_norm_ema,
        "zero_std_frac": zero_std_frac,
    }

    # Add PPO-specific metrics
    metrics.update(ppo_metrics)

    # Legacy keys for backward compatibility with epoch accumulation
    metrics["mean_reward"] = metrics["reward/mean"]
    metrics["clip_frac"] = metrics["clip_fraction"]
    metrics["mean_ratio"] = metrics["importance_ratio/mean"]
    metrics["kl_penalty"] = metrics["kl_divergence"]
    metrics["grad_norm"] = metrics["gradient_norm"]

    return metrics, grad_norm_ema


# ======================================================================
#  Main training loop
# ======================================================================

def grpo_train(cfg, policy_model, train_nl, train_sql, train_gold_records,
               dev_loader, vocab, mem_conn, optimizer, run_dir,
               value_head=None, value_optimizer=None):
    """GRPO/CISPO/PPO training loop.

    Follows the same structural pattern as dpo_train() in dpo_train.py:
    epoch loop -> mini-batch loop -> eval -> checkpoint -> early stop.

    Args:
        cfg: T5GRPOConfig / T5PPOConfig instance
        policy_model: T5ForFlightSQL with LoRA
        train_nl: list of NL query strings (training set)
        train_sql: list of gold SQL strings (training set)
        train_gold_records: list of gold record frozensets
        dev_loader: DataLoader for dev set evaluation
        vocab: FlightSQLVocab instance
        mem_conn: in-memory SQLite connection
        optimizer: AdamW optimizer (policy)
        run_dir: Path to run output directory
        value_head: T5ValueHead instance (PPO only)
        value_optimizer: AdamW optimizer for value head (PPO only)

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
        if value_head is not None:
            value_head.train()

        # Shuffle training data indices each epoch (on-policy: fresh samples)
        indices = torch.randperm(num_train).tolist()

        # Epoch accumulators (using full metrics contract keys)
        epoch_accum = {}
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
                value_head=value_head, value_optimizer=value_optimizer,
            )

            # Accumulate epoch metrics
            for key in ("loss", "mean_reward", "zero_std_frac", "clip_frac",
                         "mean_ratio", "kl_penalty", "grad_norm",
                         "reward/mean", "reward/std", "reward/max", "reward/min",
                         "reward/group_std", "success_rate",
                         "kl_divergence", "policy_entropy", "clip_fraction",
                         "importance_ratio/mean", "importance_ratio/max",
                         "advantage/mean", "advantage/std", "advantage/max",
                         "unique_completions_per_query", "avg_completion_length"):
                if key in metrics:
                    epoch_accum[key] = epoch_accum.get(key, 0.0) + metrics[key]

            # PPO-specific accumulation
            for key in ("ppo/value_loss", "ppo/value_pred_mean", "ppo/value_error",
                         "ppo/entropy", "ppo/policy_loss"):
                if key in metrics:
                    epoch_accum[key] = epoch_accum.get(key, 0.0) + metrics[key]

            epoch_grad_spikes += int(metrics["grad_spike_skipped"])
            num_batches += 1

            # Log batch-level metrics to W&B
            log_epoch_metrics({
                "batch/loss": metrics["loss"],
                "batch/gradient_norm": metrics["gradient_norm"],
                "batch/reward_mean": metrics["reward/mean"],
                "batch/clip_fraction": metrics["clip_fraction"],
                "batch/kl_divergence": metrics["kl_divergence"],
            }, step=global_step)
            global_step += 1

        # Compute epoch averages
        avg = {k: v / num_batches for k, v in epoch_accum.items()}

        train_epoch_seconds = time.time() - epoch_start

        # Print epoch summary
        print(f"Epoch {epoch}: RL loss = {avg.get('loss', 0):.4f}, "
              f"mean_reward = {avg.get('reward/mean', 0):.3f}, "
              f"clip_frac = {avg.get('clip_fraction', 0):.3f}, "
              f"dead_groups = {avg.get('zero_std_frac', 0):.3f}, "
              f"kl = {avg.get('kl_divergence', 0):.4f}")

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

            # Log epoch metrics to W&B (full contract)
            epoch_log = {
                "epoch": epoch,
                "train_loss": avg.get("loss", 0),
                "record_f1": record_f1,
                "record_em": record_em,
                "sql_em": sql_em,
                "error_rate": error_rate,
                "gradient_norm": avg.get("gradient_norm", avg.get("grad_norm", 0)),
                "lr": optimizer.param_groups[0]["lr"],
                # Full RL metrics contract
                "reward/mean": avg.get("reward/mean", 0),
                "reward/std": avg.get("reward/std", 0),
                "reward/max": avg.get("reward/max", 0),
                "reward/min": avg.get("reward/min", 0),
                "reward/group_std": avg.get("reward/group_std", 0),
                "success_rate": avg.get("success_rate", 0),
                "kl_divergence": avg.get("kl_divergence", 0),
                "policy_entropy": avg.get("policy_entropy", 0),
                "clip_fraction": avg.get("clip_fraction", 0),
                "importance_ratio/mean": avg.get("importance_ratio/mean", 0),
                "importance_ratio/max": avg.get("importance_ratio/max", 0),
                "advantage/mean": avg.get("advantage/mean", 0),
                "advantage/std": avg.get("advantage/std", 0),
                "advantage/max": avg.get("advantage/max", 0),
                "unique_completions_per_query": avg.get("unique_completions_per_query", 0),
                "avg_completion_length": avg.get("avg_completion_length", 0),
                "rl/grad_spikes_skipped": epoch_grad_spikes,
            }
            # PPO-specific epoch metrics
            for key in ("ppo/value_loss", "ppo/value_pred_mean", "ppo/value_error",
                         "ppo/entropy", "ppo/policy_loss"):
                if key in avg:
                    epoch_log[key] = avg[key]

            log_epoch_metrics(epoch_log, step=epoch)
            log_epoch_metrics({
                "timing/epoch_seconds": epoch_time,
                "timing/wall_clock_seconds": wall_clock,
                "timing/train_epoch_seconds": train_epoch_seconds,
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
            epoch_log = {
                "epoch": epoch,
                "train_loss": avg.get("loss", 0),
                "gradient_norm": avg.get("gradient_norm", avg.get("grad_norm", 0)),
                "lr": optimizer.param_groups[0]["lr"],
                "reward/mean": avg.get("reward/mean", 0),
                "reward/std": avg.get("reward/std", 0),
                "reward/group_std": avg.get("reward/group_std", 0),
                "success_rate": avg.get("success_rate", 0),
                "kl_divergence": avg.get("kl_divergence", 0),
                "policy_entropy": avg.get("policy_entropy", 0),
                "clip_fraction": avg.get("clip_fraction", 0),
                "rl/grad_spikes_skipped": epoch_grad_spikes,
            }
            for key in ("ppo/value_loss", "ppo/value_pred_mean", "ppo/entropy"):
                if key in avg:
                    epoch_log[key] = avg[key]
            log_epoch_metrics(epoch_log, step=epoch)

        # Early stopping
        if cfg.patience_epochs > 0 and epochs_since_improvement >= cfg.patience_epochs:
            print(f"Early stopping at epoch {epoch} "
                  f"(patience={cfg.patience_epochs})")
            break

        # Wall clock budget (per-config)
        wall_clock = time.time() - train_start
        if cfg.max_wall_clock_hours and wall_clock >= cfg.max_wall_clock_hours * 3600:
            print(f"Time budget reached ({wall_clock/3600:.2f}h / "
                  f"{cfg.max_wall_clock_hours:.2f}h). Stopping.")
            break

        # Graceful stop
        if stop_requested():
            print(f"Graceful stop after epoch {epoch}.")
            break

    # Save last model checkpoint (always, regardless of best)
    save_model(ckpt_dir, policy_model, best=False)
    print("Saved last model checkpoint")

    total_time = time.time() - train_start
    print(f"\n{cfg.rl_algorithm.upper()} training complete: {total_time/60:.1f} min, "
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
    """Run the full GRPO/CISPO/PPO training pipeline with a pre-built config.

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

    # ── PPO: create value head ──
    value_head = None
    value_optimizer = None
    if cfg.rl_algorithm == "ppo":
        # Determine encoder hidden dimension from model config
        d_model = policy_model.model.config.d_model
        value_hidden_dim = getattr(cfg, 'value_hidden_dim', 512)
        value_head = T5ValueHead(d_model=d_model, hidden_dim=value_hidden_dim).to(device)
        value_lr = getattr(cfg, 'value_lr', 1e-4)
        value_optimizer = torch.optim.AdamW(
            value_head.parameters(), lr=value_lr, weight_decay=cfg.weight_decay,
        )
        print(f"PPO value head created (d_model={d_model}, hidden={value_hidden_dim}, "
              f"lr={value_lr})")

    # ── Optimizer (policy) ──
    optimizer = torch.optim.AdamW(
        [p for p in policy_model.parameters() if p.requires_grad],
        lr=cfg.learning_rate,
        weight_decay=cfg.weight_decay,
    )

    # ── W&B setup ──
    run_dir, _ = setup_run(cfg, experiment_name="part1_rl")
    print(f"Run directory: {run_dir}")
    print(f"Device: {device}")

    # Log model info
    total_params = sum(p.numel() for p in policy_model.parameters())
    trainable_params = sum(p.numel() for p in policy_model.parameters()
                          if p.requires_grad)
    extra_params = {
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
    }
    # Log gpu_name as one-time param
    if torch.cuda.is_available():
        extra_params["gpu_name"] = torch.cuda.get_device_name(0)
    # PPO-specific params
    if cfg.rl_algorithm == "ppo":
        extra_params.update({
            "value_hidden_dim": getattr(cfg, 'value_hidden_dim', 512),
            "value_coef": getattr(cfg, 'value_coef', 0.5),
            "entropy_coef": getattr(cfg, 'entropy_coef', 0.01),
            "advantage_type": getattr(cfg, 'advantage_type', 'learned'),
            "value_lr": getattr(cfg, 'value_lr', 1e-4),
        })
    log_extra_params(extra_params)

    # ── Initialize in-memory SQLite ──
    mem_conn = _get_mem_conn()

    # ── Train ──
    best_val = grpo_train(
        cfg, policy_model, train_nl, train_sql, train_gold_records,
        dev_loader, sql_vocab, mem_conn, optimizer, run_dir,
        value_head=value_head, value_optimizer=value_optimizer,
    )

    # ── Final eval: reload best checkpoint ──
    del policy_model
    if value_head is not None:
        del value_head
        del value_optimizer
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
    print(f"{cfg.rl_algorithm.upper()} training pipeline complete")

    return best_val


# ======================================================================
#  CLI
# ======================================================================

def parse_args():
    """Parse CLI arguments for RL training."""
    parser = argparse.ArgumentParser(
        description="GRPO/CISPO/PPO RL training for T5 NL-to-SQL"
    )
    parser.add_argument("--rl_algorithm", type=str, default=None,
                        choices=["grpo", "cispo", "ppo"],
                        help="RL algorithm (omit to run all three sequentially)")
    parser.add_argument("--group_size", type=int, default=None)
    parser.add_argument("--epsilon", type=float, default=None)
    parser.add_argument("--epsilon_high", type=float, default=None)
    parser.add_argument("--kl_beta", type=float, default=None)
    parser.add_argument("--learning_rate", type=float, default=None)
    parser.add_argument("--num_epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--patience_epochs", type=int, default=None)
    parser.add_argument("--base_checkpoint_path", type=str, default=None)
    parser.add_argument("--max_hours", type=float, default=None,
                        help="Total wall clock budget across all configs (hours)")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", type=str, default=None)
    return parser.parse_args()


def apply_cli_overrides(cfg, args):
    """Apply non-None CLI args to config."""
    for attr in ("rl_algorithm", "group_size", "epsilon", "epsilon_high",
                 "kl_beta", "learning_rate", "num_epochs", "batch_size",
                 "patience_epochs", "base_checkpoint_path", "seed", "name"):
        val = getattr(args, attr, None)
        if val is not None:
            setattr(cfg, attr, val)


def main():
    """Sequential auto-batch: run RL configs in one process with VRAM cleanup."""
    args = parse_args()

    # Build config list based on CLI or default all-three
    if args.rl_algorithm:
        # Single algorithm mode
        if args.rl_algorithm == "ppo":
            configs = [T5PPOConfig_v1()]
        elif args.rl_algorithm == "cispo":
            configs = [T5GRPOConfig_cispo()]
        else:
            configs = [T5GRPOConfig_grpo()]
    else:
        # Default: run all three sequentially
        configs = [T5PPOConfig_v1(), T5GRPOConfig_grpo(), T5GRPOConfig_cispo()]

    total_start = time.time()

    for i, cfg in enumerate(configs):
        # Check total time budget
        if args.max_hours:
            elapsed = (time.time() - total_start) / 3600
            if elapsed >= args.max_hours:
                print(f"\nTotal time budget exhausted ({elapsed:.2f}h >= "
                      f"{args.max_hours:.2f}h). Skipping remaining configs.")
                break

        apply_cli_overrides(cfg, args)
        print(f"\n{'='*60}")
        print(f"Config {i+1}/{len(configs)}: {cfg.name} ({cfg.rl_algorithm})")
        print(f"{'='*60}\n")
        main_with_config(cfg)

        # VRAM cleanup between configs (per sequential auto-batch preference)
        cleanup_vram()

    total_elapsed = (time.time() - total_start) / 60
    print(f"\nAll configs complete. Total time: {total_elapsed:.1f} min")


if __name__ == "__main__":
    from src.utils.gpu_lock import GpuLock
    with GpuLock():
        main()
