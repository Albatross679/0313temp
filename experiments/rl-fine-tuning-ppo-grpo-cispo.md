---
name: RL Fine-Tuning Comparison (PPO, GRPO, CISPO)
description: Three RL algorithms applied to best T5-base checkpoint via LoRA
type: experiment
status: complete
created: 2026-03-14
updated: 2026-03-15
tags: [rl, ppo, grpo, cispo, t5-base, lora, part1]
aliases: [rl-comparison]
---

# RL Fine-Tuning Comparison (PPO, GRPO, CISPO)

## Setup

- **Base model**: T5-base fine-tuned checkpoint (dev F1=0.8596)
- **Adapter**: LoRA r=32, alpha=64, target=q,k,v,o (7.08M trainable / 229.98M total = 3.08%)
- **Reward**: Execution-based graded (+1.0 exact match, +0.5 partial overlap, -0.5 no overlap, -1.0 SQL error)
- **Generation**: temperature=0.7, top_k=50, group_size=4, max_tokens=512
- **Training**: Adam W optimizer, lr=5e-6, bf16 autocast
- **Data subsampling**: 200-500 queries per epoch (on-policy: re-sample each epoch)
- **Early stopping**: patience=3-5 epochs on dev Record F1
- **Bug fixes applied** (issues/rl-policy-collapse-three-bugs.md):
  1. IS ratio computed from current vs old (same policy, different time) -- not policy vs reference
  2. eval() mode during log prob computation to disable dropout noise
  3. Value head zero-initialized for stable PPO start

## Results

### PPO (Proximal Policy Optimization with Learned Value Head)

- Hyperparameters: kl_beta=0.02, value_coef=0.5, entropy_coef=0.01, advantage_type=learned
- Train subset: 200 queries/epoch
- Training time: 46.3 minutes

| Epoch | Loss | Mean Reward | clip_frac | dead_groups | KL | Dev F1 | Dev EM | SQL EM |
|-------|------|-------------|-----------|-------------|------|--------|--------|--------|
| 0 | -0.28 | 0.536 | 0.000 | 0.640 | +0.02 | 0.8596 | 0.8476 | 0.7339 |
| 1 | -0.22 | 0.541 | 0.000 | 0.530 | -0.41 | 0.8596 | 0.8476 | 0.7339 |
| 2 | -0.26 | 0.539 | 0.000 | 0.590 | -2.59 | 0.8575 | 0.8455 | 0.7318 |
| 3 | -0.39 | 0.455 | 0.000 | 0.525 | -6.55 | 0.8567 | 0.8433 | 0.7318 |

Early stopped at epoch 3. Best dev F1 = 0.8596 (epoch 0). Final eval: F1=0.7661.

### GRPO (Group Relative Policy Optimization)

- Hyperparameters: kl_beta=0.05, use_std_normalization=True
- Train subset: 500 queries/epoch
- Training time: ~35 minutes (killed during epoch 2)

| Epoch | Loss | Mean Reward | clip_frac | dead_groups | KL | Dev F1 | Dev EM | SQL EM |
|-------|------|-------------|-----------|-------------|-------|--------|--------|--------|
| 0 | -0.09 | 0.559 | 0.000 | 0.580 | -1.87 | 0.8596 | 0.8476 | 0.7339 |
| 1 | -0.49 | 0.411 | 0.000 | 0.490 | -9.88 | 0.8596 | 0.8476 | 0.7339 |

Killed during epoch 2 batch 51/125. Same pattern: KL diverging, reward declining, F1 flat.

### CISPO (Clipped Importance Sampling Policy Optimization)

- Hyperparameters: kl_beta=0.0, epsilon_high=0.3
- Train subset: 200 queries/epoch
- Training time: 45.3 minutes

| Epoch | Loss | Mean Reward | clip_frac | dead_groups | KL | Dev F1 | Dev EM | SQL EM |
|-------|------|-------------|-----------|-------------|------|--------|--------|--------|
| 0 | -0.009 | 0.532 | 0.000 | 0.590 | -0.01 | 0.8596 | 0.8476 | 0.7339 |
| 1 | -0.007 | 0.549 | 0.000 | 0.640 | -0.03 | 0.8596 | 0.8476 | 0.7339 |
| 2 | -0.007 | 0.604 | 0.000 | 0.620 | +0.06 | 0.8596 | 0.8476 | 0.7339 |
| 3 | -0.009 | 0.592 | 0.000 | 0.590 | +0.21 | 0.8596 | 0.8476 | 0.7339 |

Early stopped at epoch 3. Best dev F1 = 0.8596. Final eval: F1=0.7575.
CISPO showed the most stable KL (stayed near zero) but made the smallest policy updates.

## Comparison Summary

| Algorithm | Best Dev F1 | Best Dev EM | Best SQL EM | Epochs | KL Drift | Training Min |
|-----------|------------|-------------|-------------|--------|----------|-------------|
| SFT Baseline | 0.8596 | 0.8476 | 0.7339 | 79 | -- | ~180 |
| PPO + Value Head | 0.8596 | 0.8476 | 0.7339 | 4 | -6.55 | 46.3 |
| GRPO | 0.8596 | 0.8476 | 0.7339 | 2+ | -9.88 | ~35 |
| CISPO | 0.8596 | 0.8476 | 0.7339 | 4 | +0.21 | 45.3 |

**None of the three RL algorithms improved over the SFT baseline.**

## Analysis

### Why RL Failed to Improve

1. **Single-step ratio equals 1.0 (REINFORCE reduction)**: With one gradient step per rollout batch, the importance sampling ratio is always 1.0. PPO's clipping never activates (clip_frac=0.000 across all runs). All three algorithms effectively reduce to vanilla REINFORCE with different advantage baselines.

2. **Reward landscape too flat (dead groups)**: The base model already achieves F1=0.86. Most generated SQL completions receive +1.0 reward (exact match), creating 50-64% "dead groups" with zero reward variance. The RL gradient signal is too sparse to improve an already-strong model.

3. **KL diverges for PPO/GRPO**: The policy explores lower-probability regions without finding better outputs. KL divergence grows negative (policy assigns less probability to reference-model-preferred outputs) without dev F1 improvement. CISPO's detached clipping keeps KL near zero but also makes essentially zero policy updates.

4. **Coarse reward granularity**: Four reward levels (+1, +0.5, -0.5, -1) cannot distinguish "almost correct" from "completely wrong" SQL. No gradient signal for partial improvements.

### Algorithm-Specific Observations

- **PPO**: Value head learned to predict mean reward (~0.5) but advantage estimates didn't help. Entropy decreased steadily. Policy drifted despite KL penalty (kl_beta=0.02 too weak).
- **GRPO**: Group-relative advantage normalization more aggressive than PPO learned baseline. KL diverged fastest (-9.88 by epoch 1). Mean reward declined (0.559 -> 0.411).
- **CISPO**: Most conservative of the three. Detached IS clipping resulted in near-zero effective gradients (loss ~-0.008 vs PPO ~-0.3). Policy barely moved from the reference. Most stable but least able to learn.

## Recommendations (If Revisiting RL for NL-to-SQL)

- **Rejection sampling fine-tuning (RFT)**: Generate N completions, filter by reward >= threshold, SFT on filtered set. More stable for already-strong base models.
- **Multi-step updates** (num_updates_per_rollout > 1): Makes IS ratio != 1.0, activates PPO clipping, extracts more signal per rollout.
- **Finer reward signal**: Use Jaccard similarity as continuous reward instead of 4 discrete buckets.
- **Focus on hard queries**: Only train on queries where base model fails (reward < 1.0).
- **Larger model + more data**: RL benefits typically require scale (both model and dataset) that exceeds our T5-base + 4K training set.
