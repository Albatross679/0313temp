---
name: rl-config-and-loss-functions
description: Created T5GRPOConfig dataclass and GRPO/CISPO loss functions for RL fine-tuning pipeline
type: log
created: 2026-03-14
updated: 2026-03-14
tags: [rl, grpo, cispo, loss-functions, config, part1]
aliases: []
status: complete
subtype: feature
---

# RL Config and Loss Functions

Created the foundational layer for GRPO/CISPO RL training on T5.

## Changes

### part1/rl_config.py (new)
- `T5GRPOConfig` inheriting `T5FineTuneConfig` with RL-specific fields
- RL algorithm selection (grpo/cispo), group_size=8, graded reward
- LoRA r=32 alpha=64 on q,k,v,o attention projections
- Stability params: grad norm spike detection, EMA tracking, dead group skip
- Two variant configs: `T5GRPOConfig_grpo` (KL=0.02) and `T5GRPOConfig_cispo` (no KL)

### part1/rl_loss.py (new)
- `grpo_loss`: sequence-level PPO-style clipped surrogate
- `cispo_loss`: sequence-level with detached clamped IS weights
- `cispo_loss_per_token`: per-token IS ratios per MiniMax-M1 Eq.4
- `compute_group_advantages`: group-relative normalization with dead group detection
- `compute_execution_reward`: graded scheme (+1/+0.5/-0.5/-1)
- `compute_kl_penalty`: KL divergence estimate for reference regularization

### part1/dpo_loss.py (modified)
- Added `per_token=False` parameter to `compute_restricted_log_probs`
- When True, returns (token_log_probs, mask) tuple of (B, T) tensors
- Backward compatible: existing DPO callers unaffected

## Key Design Decisions
- CISPO uses `.detach()` on clamped ratio so gradient always flows through log_pi
- Graded reward (not binary) per user decision for better gradient signal
- Dr.GRPO variant supported via `use_std_normalization=False`
