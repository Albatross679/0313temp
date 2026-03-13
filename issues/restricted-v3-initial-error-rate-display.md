---
name: restricted-v3-initial-error-rate-display
description: W&B run t5_ft_restricted_v3 appears to start with error rate < 1 due to eval frequency skipping epoch 0
type: issue
status: resolved
severity: low
subtype: evaluation
created: 2026-03-11
updated: 2026-03-11
tags:
  - wandb
  - eval
  - restricted-vocab
  - part1
aliases: []
---

# t5_ft_restricted_v3 starts with error rate != 1 on W&B

## Symptom

The W&B run `t5_ft_restricted_v3` (multi-config training batch) shows the first
logged error rate well below 1.0, which is unexpected for a model that hasn't
seen SQL training data yet.

## Root Cause

Two factors combine:

1. **Eval frequency**: `eval_every_n_epochs = 4` means the first evaluation (and
   first W&B data point) is at epoch 3 (0-indexed). Epochs 0–2 have no logged
   metrics.

2. **Pretrained weights**: With `finetune=True`, the model starts from pretrained
   T5-small. After just 1–2 training epochs, the model already generates enough
   valid SQL to drop the error rate significantly.

## Evidence

The earlier killed run of the same config (`restricted-finetune-v3-run.md`)
evaluated every epoch and showed the true trajectory:

| Epoch | Error Rate |
|-------|-----------|
| 0     | 100%      |
| 1     | 19.1%     |
| 2     | 89.1%     |

By epoch 3 (the first eval point in the multi-config run), the model has already
learned basic SQL syntax from pretrained representations + fine-tuning.

## Resolution

Display artifact only — no code fix needed. The training pipeline is correct;
the apparent non-unity start is simply because the first plotted point reflects
a model already trained for 4 epochs.
