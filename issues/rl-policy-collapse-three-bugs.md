---
name: rl-policy-collapse-three-bugs
description: RL training collapsed due to wrong IS ratio, dropout noise, and value head init
type: issue
status: resolved
severity: critical
subtype: training
created: 2026-03-15
updated: 2026-03-15
tags: [rl, ppo, grpo, cispo, is-ratio, dropout, value-head, policy-collapse]
aliases: [rl-clip-frac-bug, dropout-ratio-bug, value-head-spike]
---

# RL Policy Collapse: Three Compounding Bugs

## Symptom

RL training (PPO/GRPO/CISPO) showed immediate policy collapse:
- clip_frac = 0.914 at epoch 0, → 0.999 by epoch 3
- KL divergence rapidly negative: -0.73 → -14.19 in 4 epochs
- Mean reward declining after epoch 1
- Loss spikes to 25,000+ on specific batches
- Dev F1 completely flat at base model score (0.8596)

## Root Causes

### Bug 1: IS Ratio Computed Against Reference Instead of Old Policy

`compute_old_log_probs()` disabled LoRA adapters to get base model (reference) log probs.
The IS ratio `pi_current / pi_old` was actually `pi_lora / pi_base`, which diverges as
LoRA trains. By epoch 3, the accumulated divergence made ratio ≫ 1.0 everywhere.

**Correct design**: IS ratio uses `pi_current(detached) / pi_current(with_grad)` — should
start at 1.0 each step. Reference log probs used only for KL penalty.

**Fix**: Added `use_reference` parameter to `compute_old_log_probs()`:
- `use_reference=True` → disables LoRA (for KL penalty)
- `use_reference=False` → keeps LoRA enabled (for IS ratio)

### Bug 2: Dropout Noise Making Ratio ≠ 1.0

Even with Bug 1 fixed, clip_frac was still 0.92. Both old_log_probs and current_log_probs
were computed with the model in `train()` mode, so different dropout masks produced different
outputs from the same weights. With T5-base (12 layers × 2 dropouts × 300+ tokens), the
accumulated noise was enormous — enough to push ratios far outside [0.8, 1.2].

**Fix**: Set `policy_model.eval()` before computing both old and current log probs (disables
dropout/batchnorm but preserves gradient computation). Restore `train()` after optimizer step.

### Bug 3: Value Head Random Init Causing Loss Spikes

The PPO value head output layer was Kaiming-initialized, producing wildly off predictions
(vs reward range [-1, 1]). This caused:
- Huge advantages: A = R - V(s) where V(s) could be ±100+
- Huge policy loss spikes: loss = 25,864 on individual batches
- Grad norm spikes (caught by spike detector but still noisy)

**Fix**: Zero-initialize the output layer weights and bias in `T5ValueHead.__init__()` so
initial V(s) ≈ 0.

## Files Modified

- `part1/rl_train.py`:
  - `compute_old_log_probs()` — added `use_reference` parameter
  - `grpo_train_step()` — separated old_log_probs (IS ratio) from ref_log_probs (KL);
    added eval() mode wrapper around log prob computations
- `part1/rl_value_head.py` — zero-init output layer

## Results After Fix

| Metric | v8 (broken) | v11 (fixed) |
|--------|-------------|-------------|
| clip_frac | 0.914 → 0.999 | **0.000** |
| KL | -0.73 → -14.19 | **+0.019** |
| loss | 3.95 → -0.74 | **-0.28** |
| loss spikes | 25,864 | **none** |
| mean_reward | 0.477 | 0.536 |

Training is now stable. Dev F1 still flat at 0.8596 after 2 epochs, but this is expected
early — the policy hasn't diverged enough from base to affect greedy decoding.

## Note on Single-Step PPO

With clip_frac=0.000, the IS ratio is always exactly 1.0 (no clipping activates). This means
PPO reduces to REINFORCE with a learned baseline. For PPO clipping to matter, we'd need
`num_updates_per_rollout > 1` (multiple gradient steps on same rollouts). This is a future
enhancement, not a bug.
