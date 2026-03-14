"""DPO loss computation for T5 encoder-decoder with restricted SQL vocabulary.

Implements:
  - compute_restricted_log_probs: sequence-level log probs via restricted_forward()
  - dpo_loss: standard DPO sigmoid loss over log-probability ratios
  - dpo_train_step: single training step combining forward, loss, backward
"""

import torch
import torch.nn.functional as F


def compute_restricted_log_probs(model, encoder_input, encoder_mask,
                                  decoder_input, decoder_targets, pad_idx=0):
    """Compute per-sequence log probability using restricted vocab forward pass.

    Args:
        model: T5ForFlightSQL instance (policy or reference)
        encoder_input: (B, T_enc) tokenized NL query
        encoder_mask: (B, T_enc) attention mask
        decoder_input: (B, T_dec) = [BOS] + targets[:-1]
        decoder_targets: (B, T_dec) original token IDs (not remapped)
        pad_idx: padding token ID (0 for T5)

    Returns:
        seq_log_probs: (B,) SUM of per-token log probs for each sequence
    """
    # restricted_forward returns logits in restricted vocab space: (B, T, V_sql)
    logits = model.restricted_forward(encoder_input, encoder_mask, decoder_input)

    # Remap targets to restricted vocab indices
    remapped_targets = model.remap_targets(decoder_targets)  # (B, T)

    # Per-token log probs: gather log_softmax at target positions
    log_probs = logits.log_softmax(dim=-1)  # (B, T, V_sql)
    per_token = torch.gather(
        log_probs, dim=2, index=remapped_targets.unsqueeze(2)
    ).squeeze(2)  # (B, T)

    # Mask padding tokens (use ORIGINAL targets for pad detection, not remapped)
    mask = (decoder_targets != pad_idx).float()

    # Sum per-token log probs for sequence-level log probability
    seq_log_probs = (per_token * mask).sum(dim=-1)  # (B,)
    return seq_log_probs


def dpo_loss(policy_chosen_logps, policy_rejected_logps,
             ref_chosen_logps, ref_rejected_logps, beta=0.1):
    """Standard DPO sigmoid loss.

    L = -log(sigmoid(beta * ((pi_chosen - ref_chosen) - (pi_rejected - ref_rejected))))

    Args:
        policy_chosen_logps: (B,) log probs of chosen under policy
        policy_rejected_logps: (B,) log probs of rejected under policy
        ref_chosen_logps: (B,) log probs of chosen under reference
        ref_rejected_logps: (B,) log probs of rejected under reference
        beta: temperature parameter controlling divergence from reference

    Returns:
        (loss, chosen_rewards_mean, rejected_rewards_mean)
    """
    chosen_rewards = beta * (policy_chosen_logps - ref_chosen_logps)
    rejected_rewards = beta * (policy_rejected_logps - ref_rejected_logps)
    logits = chosen_rewards - rejected_rewards
    loss = -F.logsigmoid(logits).mean()
    return loss, chosen_rewards.mean(), rejected_rewards.mean()


def dpo_train_step(policy_model, ref_model, batch, optimizer,
                   beta=0.1, grad_clip_norm=1.0, device="cuda"):
    """Single DPO training step.

    Args:
        policy_model: T5ForFlightSQL being trained
        ref_model: frozen T5ForFlightSQL reference
        batch: (prompt_ids, prompt_mask, chosen_dec_in, chosen_tgt,
                rej_dec_in, rej_tgt) from dpo_collate_fn
        optimizer: optimizer for policy_model parameters
        beta: DPO temperature
        grad_clip_norm: max gradient norm for clipping
        device: target device

    Returns:
        dict with: loss, reward_margin, reward_accuracy,
                   chosen_reward, rejected_reward, grad_norm
    """
    prompt_ids, prompt_mask, chosen_dec_in, chosen_tgt, rej_dec_in, rej_tgt = [
        t.to(device) for t in batch
    ]

    # Policy model forward (with gradients)
    policy_chosen_logps = compute_restricted_log_probs(
        policy_model, prompt_ids, prompt_mask, chosen_dec_in, chosen_tgt)
    policy_rejected_logps = compute_restricted_log_probs(
        policy_model, prompt_ids, prompt_mask, rej_dec_in, rej_tgt)

    # Reference model forward (no gradients)
    with torch.no_grad():
        ref_chosen_logps = compute_restricted_log_probs(
            ref_model, prompt_ids, prompt_mask, chosen_dec_in, chosen_tgt)
        ref_rejected_logps = compute_restricted_log_probs(
            ref_model, prompt_ids, prompt_mask, rej_dec_in, rej_tgt)

    # DPO loss
    loss, chosen_reward_mean, rejected_reward_mean = dpo_loss(
        policy_chosen_logps, policy_rejected_logps,
        ref_chosen_logps, ref_rejected_logps, beta=beta)

    # Backward + grad clip + optimizer step
    optimizer.zero_grad()
    loss.backward()
    grad_norm = torch.nn.utils.clip_grad_norm_(
        policy_model.parameters(), grad_clip_norm).item()
    optimizer.step()

    # Metrics for logging
    with torch.no_grad():
        chosen_rewards = beta * (policy_chosen_logps - ref_chosen_logps)
        rejected_rewards = beta * (policy_rejected_logps - ref_rejected_logps)
        reward_margin = (chosen_rewards - rejected_rewards).mean().item()
        reward_accuracy = (chosen_rewards > rejected_rewards).float().mean().item()

    return {
        "loss": loss.item(),
        "reward_margin": reward_margin,
        "reward_accuracy": reward_accuracy,
        "chosen_reward": chosen_reward_mean.item(),
        "rejected_reward": rejected_reward_mean.item(),
        "grad_norm": grad_norm,
    }


def dpo_train_step_lora(policy_model, batch, optimizer,
                        beta=0.1, grad_clip_norm=1.0, device="cuda"):
    """Single DPO training step for LoRA policy (single model, no separate ref).

    Uses peft disable_adapter_layers() to get reference logprobs from the
    base model with LoRA temporarily disabled.

    Args:
        policy_model: T5ForFlightSQL with peft-wrapped inner model
        batch: (prompt_ids, prompt_mask, chosen_dec_in, chosen_tgt,
                rej_dec_in, rej_tgt) from dpo_collate_fn
        optimizer: optimizer for LoRA parameters only
        beta: DPO temperature
        grad_clip_norm: max gradient norm for clipping
        device: target device

    Returns:
        dict with: loss, reward_margin, reward_accuracy,
                   chosen_reward, rejected_reward, grad_norm
    """
    prompt_ids, prompt_mask, chosen_dec_in, chosen_tgt, rej_dec_in, rej_tgt = [
        t.to(device) for t in batch
    ]

    # Policy forward (LoRA active)
    policy_chosen_logps = compute_restricted_log_probs(
        policy_model, prompt_ids, prompt_mask, chosen_dec_in, chosen_tgt)
    policy_rejected_logps = compute_restricted_log_probs(
        policy_model, prompt_ids, prompt_mask, rej_dec_in, rej_tgt)

    # Reference forward (LoRA disabled = base model)
    with torch.no_grad():
        policy_model.model.disable_adapter_layers()
        ref_chosen_logps = compute_restricted_log_probs(
            policy_model, prompt_ids, prompt_mask, chosen_dec_in, chosen_tgt)
        ref_rejected_logps = compute_restricted_log_probs(
            policy_model, prompt_ids, prompt_mask, rej_dec_in, rej_tgt)
        policy_model.model.enable_adapter_layers()

    # DPO loss
    loss, chosen_reward_mean, rejected_reward_mean = dpo_loss(
        policy_chosen_logps, policy_rejected_logps,
        ref_chosen_logps, ref_rejected_logps, beta=beta)

    # Backward + grad clip + optimizer step
    optimizer.zero_grad()
    loss.backward()
    grad_norm = torch.nn.utils.clip_grad_norm_(
        policy_model.parameters(), grad_clip_norm).item()
    optimizer.step()

    # Metrics for logging
    with torch.no_grad():
        chosen_rewards = beta * (policy_chosen_logps - ref_chosen_logps)
        rejected_rewards = beta * (policy_rejected_logps - ref_rejected_logps)
        reward_margin = (chosen_rewards - rejected_rewards).mean().item()
        reward_accuracy = (chosen_rewards > rejected_rewards).float().mean().item()

    return {
        "loss": loss.item(),
        "reward_margin": reward_margin,
        "reward_accuracy": reward_accuracy,
        "chosen_reward": chosen_reward_mean.item(),
        "rejected_reward": rejected_reward_mean.item(),
        "grad_norm": grad_norm,
    }
