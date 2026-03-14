"""RL loss functions for GRPO and CISPO training on T5 encoder-decoder.

Implements the mathematical core for online RL fine-tuning:

  - **GRPO** (Group Relative Policy Optimization): PPO-style clipped surrogate
    objective operating at the sequence level. Follows the DeepSeekMath
    formulation where advantages are group-relative (no critic network).

  - **CISPO** (Clipped Importance Sampling Policy Optimization): From the
    MiniMax-M1 paper. Instead of PPO's min(ratio*A, clip(ratio)*A) which zeros
    gradients for clipped tokens, CISPO uses detach(clamp(ratio)) * A * log_pi.
    The .detach() ensures gradient always flows through log_pi, so no token's
    gradient is ever masked out entirely.

Both algorithms share the same advantage computation and reward functions.
The training loop (Plan 02) will call these functions with precomputed
log probs from compute_restricted_log_probs in dpo_loss.py.

Exports:
    grpo_loss           - Sequence-level GRPO with PPO-style clipping
    cispo_loss          - Sequence-level CISPO with detached IS weight clipping
    cispo_loss_per_token - Per-token CISPO (MiniMax-M1 Equation 4)
    compute_group_advantages - Group-relative advantage normalization
    compute_execution_reward - Graded SQL execution reward (+1/+0.5/-0.5/-1)
    compute_kl_penalty  - KL divergence penalty between policy and reference
"""

from typing import Dict, Optional, Tuple

import torch

from part1.dpo_data import _execute_sql


# ======================================================================
#  GRPO loss (sequence-level, PPO-style clipped surrogate)
# ======================================================================

def grpo_loss(
    current_log_probs: torch.Tensor,
    old_log_probs: torch.Tensor,
    advantages: torch.Tensor,
    epsilon: float = 0.2,
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """Sequence-level GRPO loss with PPO-style min(ratio*A, clip(ratio)*A).

    Args:
        current_log_probs: (N,) log probs under current policy (sequence-level)
        old_log_probs: (N,) log probs under old/reference policy (detached)
        advantages: (N,) group-relative advantages
        epsilon: symmetric clipping range [1-eps, 1+eps]

    Returns:
        loss: scalar (negated, ready for .backward())
        diagnostics: dict with clip_frac, mean_ratio
    """
    # Importance sampling ratio: pi_theta / pi_old
    log_ratio = current_log_probs - old_log_probs.detach()
    ratio = torch.exp(log_ratio)

    # PPO-style clipped surrogate
    surr1 = ratio * advantages.detach()
    surr2 = torch.clamp(ratio, 1.0 - epsilon, 1.0 + epsilon) * advantages.detach()
    loss = -torch.min(surr1, surr2).mean()

    # Diagnostics (detached, no grad needed)
    with torch.no_grad():
        clip_frac = ((ratio < 1.0 - epsilon) | (ratio > 1.0 + epsilon)).float().mean().item()
        mean_ratio = ratio.mean().item()

    return loss, {"clip_frac": clip_frac, "mean_ratio": mean_ratio}


# ======================================================================
#  CISPO loss (sequence-level, detached clamped IS weights)
# ======================================================================

def cispo_loss(
    current_log_probs: torch.Tensor,
    old_log_probs: torch.Tensor,
    advantages: torch.Tensor,
    epsilon_high: float = 0.3,
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """Sequence-level CISPO: detach(clamp(ratio, max=1+eps)) * A * log_pi.

    The .detach() on the clamped ratio is the core CISPO innovation --
    gradient always flows through log_pi (current_log_probs), never through
    the clamped weight. This means no token's gradient is ever zeroed out.

    Args:
        current_log_probs: (N,) log probs under current policy
        old_log_probs: (N,) log probs under old/reference policy
        advantages: (N,) group-relative advantages
        epsilon_high: upper IS weight clipping bound

    Returns:
        loss: scalar (negated, ready for .backward())
        diagnostics: dict with clip_frac, mean_ratio
    """
    # Importance sampling ratio
    log_ratio = current_log_probs - old_log_probs.detach()
    ratio = torch.exp(log_ratio)

    # Clamp IS weight and DETACH -- gradient flows through current_log_probs only
    clamped_weight = torch.clamp(ratio, max=1.0 + epsilon_high).detach()

    # Loss: weighted policy gradient
    loss = -(clamped_weight * advantages.detach() * current_log_probs).mean()

    # Diagnostics
    with torch.no_grad():
        clip_frac = (ratio > 1.0 + epsilon_high).float().mean().item()
        mean_ratio = ratio.mean().item()

    return loss, {"clip_frac": clip_frac, "mean_ratio": mean_ratio}


# ======================================================================
#  CISPO loss (per-token, MiniMax-M1 Equation 4)
# ======================================================================

def cispo_loss_per_token(
    per_token_logps: torch.Tensor,
    old_per_token_logps: torch.Tensor,
    advantages: torch.Tensor,
    completion_mask: torch.Tensor,
    epsilon_high: float = 0.3,
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """Per-token CISPO matching MiniMax-M1 paper Equation 4.

    Computes per-token IS ratios and clips them individually, then weights
    each token's log_pi by the clamped ratio and the sequence-level advantage.
    Normalized by total valid tokens across all sequences.

    Args:
        per_token_logps: (B*G, T) per-token log probs under current policy
        old_per_token_logps: (B*G, T) per-token log probs under old policy
        advantages: (B*G,) sequence-level advantages (broadcast to tokens)
        completion_mask: (B*G, T) binary mask (1 for valid tokens, 0 for padding)
        epsilon_high: upper IS weight clipping bound

    Returns:
        loss: scalar (negated, ready for .backward())
        diagnostics: dict with clip_frac, mean_ratio
    """
    # Per-token IS ratio
    log_ratio = per_token_logps - old_per_token_logps.detach()
    ratio = torch.exp(log_ratio)

    # Clamp and detach per-token IS weights
    clamped_weight = torch.clamp(ratio, max=1.0 + epsilon_high).detach()

    # Broadcast advantages from (B*G,) to (B*G, T)
    adv_expanded = advantages.detach().unsqueeze(1)

    # Per-token loss: clamped_weight * advantage * log_pi
    token_loss = clamped_weight * adv_expanded * per_token_logps

    # Mask and normalize by total valid tokens
    masked_loss = token_loss * completion_mask
    total_tokens = completion_mask.sum().clamp(min=1.0)
    loss = -masked_loss.sum() / total_tokens

    # Diagnostics
    with torch.no_grad():
        valid_ratios = ratio[completion_mask.bool()]
        if valid_ratios.numel() > 0:
            clip_frac = (valid_ratios > 1.0 + epsilon_high).float().mean().item()
            mean_ratio = valid_ratios.mean().item()
        else:
            clip_frac = 0.0
            mean_ratio = 1.0

    return loss, {"clip_frac": clip_frac, "mean_ratio": mean_ratio}


# ======================================================================
#  Group-relative advantage computation
# ======================================================================

def compute_group_advantages(
    rewards: torch.Tensor,
    group_size: int,
    use_std: bool = True,
) -> Tuple[torch.Tensor, float]:
    """Group-relative advantage normalization.

    Reshapes flat rewards (B*G,) into groups (B, G), computes per-group
    mean and optionally std, normalizes within each group.

    Args:
        rewards: (B*G,) flat reward tensor
        group_size: G, number of completions per query
        use_std: True = standard GRPO (divide by std), False = Dr.GRPO (mean-only)

    Returns:
        advantages: (B*G,) normalized advantages (same shape as input)
        zero_std_frac: fraction of groups with std < 1e-6 (dead groups)
    """
    B_times_G = rewards.shape[0]
    B = B_times_G // group_size
    assert B * group_size == B_times_G, (
        f"rewards size {B_times_G} not divisible by group_size {group_size}"
    )

    # Reshape to (B, G)
    grouped = rewards.view(B, group_size)

    # Per-group statistics
    group_mean = grouped.mean(dim=1, keepdim=True)  # (B, 1)
    group_std = grouped.std(dim=1, keepdim=True)     # (B, 1)

    # Fraction of dead groups (all same reward -> zero std)
    zero_std_mask = (group_std.squeeze(1) < 1e-6)
    zero_std_frac = zero_std_mask.float().mean().item()

    if use_std:
        # Standard GRPO: (R - mean) / std
        advantages = (grouped - group_mean) / group_std.clamp(min=1e-8)
    else:
        # Dr. GRPO variant: (R - mean) only
        advantages = grouped - group_mean

    # Flatten back to (B*G,)
    return advantages.view(-1), zero_std_frac


# ======================================================================
#  Execution-based reward
# ======================================================================

def compute_execution_reward(
    generated_sql: str,
    gold_sql: str,
    gold_records: Optional[frozenset],
    mem_conn,
) -> float:
    """Graded execution reward for a single generated SQL query.

    Reward scheme (per user decision):
        +1.0: generated records exactly match gold records
        +0.5: partial overlap (Jaccard > 0, not exact)
        -0.5: executes successfully but zero overlap with gold
        -1.0: SQL execution error (returns None)
         0.0: gold SQL itself failed (gold_records is None) -- skip this sample

    Args:
        generated_sql: SQL string produced by the model
        gold_sql: gold-standard SQL string (unused directly, kept for signature)
        gold_records: frozenset of gold records, or None if gold failed
        mem_conn: in-memory SQLite connection for execution

    Returns:
        reward: float in {-1.0, -0.5, 0.0, 0.5, 1.0}
    """
    # Skip if gold SQL itself failed
    if gold_records is None:
        return 0.0

    # Execute generated SQL
    gen_records = _execute_sql(generated_sql, conn=mem_conn)

    # SQL execution error
    if gen_records is None:
        return -1.0

    # Exact match
    if gen_records == gold_records:
        return 1.0

    # Partial overlap (Jaccard > 0)
    if len(gen_records & gold_records) > 0:
        return 0.5

    # Executes but no overlap
    return -0.5


# ======================================================================
#  KL penalty
# ======================================================================

def compute_kl_penalty(
    current_log_probs: torch.Tensor,
    ref_log_probs: torch.Tensor,
) -> torch.Tensor:
    """Simple KL divergence estimate between current and reference policies.

    Uses the approximation KL(pi || ref) ~ E[log pi - log ref] which is
    the mean of the log-ratio. This is exact for the samples drawn from pi.

    Args:
        current_log_probs: (N,) log probs under current policy
        ref_log_probs: (N,) log probs under reference policy

    Returns:
        kl: scalar tensor (to be multiplied by kl_beta in the training loop)
    """
    return (current_log_probs - ref_log_probs).mean()
