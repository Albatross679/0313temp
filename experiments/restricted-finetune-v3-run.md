---
name: restricted-finetune-v3-run
description: T5FineTuneConfig_restricted_v3 run — killed at epoch 8, extreme LR oscillation
type: experiment
status: complete
created: 2026-03-11
updated: 2026-03-11
tags:
  - training
  - restricted-vocab
  - part1
aliases: []
---

# Restricted Vocab Fine-Tune v3: T5FineTuneConfig_restricted_v3

| Field | Value |
|---|---|
| **Config** | `T5FineTuneConfig_restricted_v3` (part1) |
| **Best F1** | 0.3861 (epoch 5) |
| **SQL EM** | 0.0107 |
| **Error Rate** | 39.7% |
| **Status** | KILLED @ epoch 8 |

## Hyperparameters

Aggressive fix — high LR matching from-scratch + schema context.
LR: 3e-4, label_smoothing=0.1, include_schema=True, schema_mode="top8_cols" (~221 tokens),
80 epochs, patience 15, beam=4, min_new_tokens=10.

## Rationale

Match the from-scratch model's successful LR (3e-4) and add schema context to help
with missing WHERE conditions. The top-8 tables with columns gives the model column
names to reference when generating SQL.

## Results

**F1 trajectory:** ep 0: 0.1180 -> ep 1: 0.2923 -> ep 2: 0.1459 -> ep 3: 0.1491 -> ep 4: 0.1920 -> **ep 5: 0.3861** -> ep 6: 0.3652 -> ep 7: 0.3120 -> ep 8: 0.3646

## Observations

- **Extreme oscillation**: LR=3e-4 on a pretrained model caused F1 to swing wildly
  (0.29 -> 0.15 -> 0.15 -> 0.19 -> 0.39)
- Epoch 1 showed impressive F1=0.29 immediately, but epochs 2-4 crashed to 0.15
  before recovering
- The high LR may be catastrophically disrupting pretrained weights before the model
  can re-learn them for SQL
- Error rate: 100% (ep 0) -> 19.1% (ep 1) -> 89.1% (ep 2) — evidence of catastrophic
  forgetting cycles
- Schema input (221 extra tokens per query) did not seem to help at this early stage
- **Killed by user** after 8 epochs (~1h wall clock)
