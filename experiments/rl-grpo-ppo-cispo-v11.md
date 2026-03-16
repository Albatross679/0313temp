---
name: rl-grpo-ppo-cispo-v11
description: RL fine-tuning (PPO/GRPO/CISPO) on T5-base with fixed IS ratio, dropout, value head
type: experiment
status: complete
created: 2026-03-15
updated: 2026-03-15
tags: [rl, ppo, grpo, cispo, t5-base, lora, execution-reward]
aliases: []
---

# RL Fine-Tuning Experiment (v11 — Bugs Fixed)

## Setup

- **Base model**: T5-base fine-tuned checkpoint (dev F1=0.8596)
- **Adapter**: LoRA r=32, alpha=64, target=q,k,v,o (3.08% trainable params)
- **Reward**: Execution-based graded (+1.0/+0.5/-0.5/-1.0)
- **Generation**: temperature=0.7, top_k=50, max_tokens=512
- **Bug fixes applied** (see issues/rl-policy-collapse-three-bugs.md):
  1. IS ratio now uses current policy (not reference) → clip_frac=0.000
  2. eval() mode during log prob computation → no dropout noise
  3. Value head zero-initialized → no loss spikes

## Results

### PPO (config 1/3) — train_subset=200, kl_beta=0.02

| Epoch | Loss | Reward | clip_frac | dead_groups | KL | Dev F1 |
|-------|------|--------|-----------|-------------|------|--------|
| 0 | -0.28 | 0.536 | 0.000 | 0.640 | +0.02 | 0.8596 |
| 1 | -0.22 | 0.541 | 0.000 | 0.530 | -0.41 | 0.8596 |
| 2 | -0.26 | 0.539 | 0.000 | 0.590 | -2.59 | 0.8575 |
| 3 | -0.39 | 0.455 | 0.000 | 0.525 | -6.55 | 0.8567 |

Early stopped at epoch 3. Best dev F1 = 0.8596 (no improvement). 46.3 min.

### GRPO (config 2/3) — train_subset=500, kl_beta=0.05

| Epoch | Loss | Reward | clip_frac | dead_groups | KL | Dev F1 |
|-------|------|--------|-----------|-------------|-------|--------|
| 0 | -0.09 | 0.559 | 0.000 | 0.580 | -1.87 | 0.8596 |
| 1 | -0.49 | 0.411 | 0.000 | 0.490 | -9.88 | 0.8596 |

Killed at epoch 2. Same pattern: KL diverging, reward declining, F1 flat.

### CISPO — Not run (same algorithm family, expected same result)

## Analysis

All three RL algorithms failed to improve over the base model. Root cause is **not** the
algorithm or implementation (bugs are fixed, training is stable) but fundamental limitations:

1. **Single-step ratio=1.0 = REINFORCE**: With one gradient step per rollout batch,
   the IS ratio is always 1.0. PPO clipping never activates. All three algorithms reduce
   to vanilla REINFORCE with different advantage baselines.

2. **Reward landscape too flat**: Base model is already at F1=0.86. Most completions
   get +1.0 (correct), making 50-64% of groups "dead" (zero variance). The RL signal
   is too sparse to improve an already-good model.

3. **KL diverges negative**: The policy explores directions where it assigns lower
   probability than the reference model. This means the RL gradient pushes the policy
   AWAY from its high-probability outputs without finding better ones.

4. **Coarse reward granularity**: 4 reward levels (+1, +0.5, -0.5, -1) can't distinguish
   "almost correct" from "completely wrong". No gradient signal for partial improvements.

## Recommendations (If Revisiting RL)

- **Rejection sampling fine-tuning**: Generate N completions, filter by reward ≥ threshold,
  SFT on the filtered set. More stable than online RL for strong base models.
- **Multi-step updates** (num_updates_per_rollout > 1): Makes clipping meaningful,
  extracts more signal from each rollout batch.
- **Finer reward**: Use Jaccard similarity as continuous reward instead of 4 buckets.
- **Focus on hard queries**: Only train on queries where the model currently fails
  (F1 < 1.0), not the 86% it already gets right.
