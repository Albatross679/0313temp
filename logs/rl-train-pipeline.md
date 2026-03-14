---
name: GRPO/CISPO RL Training Pipeline
description: Complete RL training pipeline for T5 encoder-decoder NL-to-SQL with group sampling, execution reward, and GRPO/CISPO loss
type: log
created: 2026-03-14
updated: 2026-03-14
tags: [rl, grpo, cispo, training, t5, part1, lora]
aliases: [rl_train, grpo_train, cispo_train]
status: complete
subtype: feature
---

# GRPO/CISPO RL Training Pipeline

## What Changed

Created `part1/rl_train.py` -- standalone RL training entry point implementing the full GRPO/CISPO pipeline for T5 encoder-decoder NL-to-SQL fine-tuning.

## Architecture

The pipeline follows the standard RL training loop:

```
SAMPLE -> REWARD -> ADVANTAGE -> OLD LOG PROBS -> UPDATE -> EVAL
```

### Key Functions

1. **`sample_group_completions()`** -- Generates G=8 SQL completions per query using constrained decoding with temperature sampling. Computes graded execution rewards by running SQL against in-memory flight database.

2. **`compute_old_log_probs()`** -- Recomputes log probabilities under the reference policy. For LoRA models, disables adapter layers to get base model predictions (same pattern as `dpo_train_step_lora`).

3. **`grpo_train_step()`** -- Single training step combining all phases. Handles both GRPO (PPO-style clipping) and CISPO (per-token detached IS weights). Includes gradient norm spike detection.

4. **`grpo_train()`** -- Main training loop with W&B logging, early stopping, wall clock budget, graceful stop, and checkpointing on dev Record F1.

5. **`main_with_config()`** -- Full pipeline: load data, build model, apply LoRA, train, final eval, test inference, artifact upload.

6. **`main()`** / `parse_args()` -- CLI entry point with `--rl_algorithm` flag to select GRPO vs CISPO configs.

### Key Design Decisions

- Log probs are **recomputed** via `compute_restricted_log_probs()` rather than using `.generate()` scores to avoid precision mismatches (per research pitfall #3).
- Dead groups (all-same reward) have their advantages zeroed out per DAPO convention, contributing zero gradient.
- Gradient norm spike detection: if `grad_norm > factor * EMA`, optimizer step is skipped.
- LoRA reference policy uses `disable_adapter_layers()` / `enable_adapter_layers()` toggle (single model, no separate ref copy).

### W&B Metric Namespacing

- Standard: `epoch, train_loss, record_f1, record_em, sql_em, error_rate, gradient_norm, lr`
- RL-specific: `rl/mean_reward, rl/zero_std_frac, rl/clip_frac, rl/mean_ratio, rl/kl_penalty, rl/grad_spikes_skipped`
- Batch: `batch/loss, batch/gradient_norm, batch/mean_reward, batch/clip_frac`
- Timing: `timing/epoch_seconds, timing/wall_clock_seconds`
- Tracking: `tracking/best_record_f1, tracking/epochs_since_improvement`

## Usage

```bash
# GRPO training
python3 -m part1.rl_train --rl_algorithm grpo --num_epochs 10 --batch_size 4

# CISPO training
python3 -m part1.rl_train --rl_algorithm cispo --num_epochs 10 --batch_size 4
```

## Files

- Created: `part1/rl_train.py` (811 lines)
- Depends on: `part1/rl_config.py`, `part1/rl_loss.py`, `part1/dpo_loss.py`, `part1/dpo_data.py`, `part1/model_flightdb.py`
