---
name: restricted-finetune-v2-run
description: T5FineTuneConfig_restricted_v2 run — killed at epoch 11, tracking behind v1
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

# Restricted Vocab Fine-Tune v2: T5FineTuneConfig_restricted_v2

| Field | Value |
|---|---|
| **Config** | `T5FineTuneConfig_restricted_v2` (part1) |
| **Best F1** | 0.3479 (epoch 5) |
| **SQL EM** | 0.0150 |
| **Error Rate** | 49.4% |
| **Status** | KILLED @ epoch 11 |

## Hyperparameters

Conservative fix over v1 — higher LR + label smoothing + EOS fix, no schema change.
LR: 1e-4 (3.3x v1), label_smoothing=0.1, min_new_tokens=10, 60 epochs, patience 12, beam=4.

## Rationale

Address v1's three root causes:
- Higher LR to fight pretrained priors (1e-4 vs 3e-5)
- Label smoothing to reduce date memorization
- min_new_tokens=10 to prevent premature EOS / truncation

## Results

**F1 trajectory:** ep 0: 0.1180 -> ep 1: 0.1183 -> ep 2: 0.1194 -> ep 3: 0.1654 -> ep 4: 0.2427 -> **ep 5: 0.3479** -> ep 6: 0.2944 -> ep 7: 0.3331 -> ep 8: 0.3324 -> ep 9: 0.3409 -> ep 10: 0.3292 -> ep 11: 0.3088

## Observations

- Learned faster than v1 in early epochs (0.35 at ep 5 vs v1's 0.28 at ep 5) but
  the oscillation between 0.29-0.35 after ep 5 was concerning
- Error rate dropped faster: 99.6% -> 43.8% in 5 epochs
- **Killed by user** to move on to v3; was tracking behind v1's eventual 0.47
