---
name: restricted-scratch-run
description: T5ScratchConfig_restricted run — best F1=0.6612, best overall result
type: experiment
status: complete
created: 2026-03-11
updated: 2026-03-11
tags:
  - training
  - restricted-vocab
  - part2
aliases: []
---

# Restricted Vocab From-Scratch: T5ScratchConfig_restricted

| Field | Value |
|---|---|
| **Config** | `T5ScratchConfig_restricted` (part2) |
| **Best F1** | **0.6612** (epoch 173) |
| **Record EM** | 0.6352 |
| **SQL EM** | 0.0322 |
| **Error Rate** | 7.5% |
| **Status** | FINISHED |

## Hyperparameters

LR: 3e-4, 200 epochs, patience 25, eval every 3 epochs, label_smoothing=0.1, beam=4.
Random-init T5-small with restricted SQL vocabulary.

## Training Curve

- Heavy F1 oscillation in early epochs (ep 0-60), stabilized after ep 80
- Consistent upward trend since ep 65
- Key milestones: ep 95: 0.6140 -> ep 128: 0.6418 -> ep 140: 0.6468 -> ep 146: 0.6559 -> ep 173: 0.6612
- Late F1 trajectory (ep 155-197): 0.6383, 0.6457, 0.6522, 0.6474, 0.6370, 0.6484, **0.6612**, 0.6456, 0.6530, 0.6447, 0.6487, 0.6450, 0.6480, 0.6502, 0.6502
- Ran all 200 epochs (patience never exhausted)

**Verified with evaluate.py:** F1=0.6612, Record EM=0.6352, SQL EM=0.0322.

**Output files:** `results/t5_scr_dev.sql`, `results/t5_scr_test.sql`, `records/t5_scr_dev.pkl`, `records/t5_scr_test.pkl`

## Why From-Scratch Outperforms Fine-Tune

1. **No pretrained priors to fight:** The restricted SQL vocabulary head projects
   against only ~600 embedding rows. A pretrained T5 has 32K embedding rows trained
   on English — the restricted projection conflicts with these strong priors. A
   from-scratch model learns embeddings optimized purely for SQL generation.

2. **Higher learning rate (3e-4 vs 3e-5):** The 10x higher LR lets the from-scratch
   model adapt much more aggressively to the SQL task, including learning the date
   mapping correctly.

3. **More training time:** 200 epochs with patience 25 (vs 30 epochs, patience 7)
   gives the from-scratch model far more time to learn complex SQL patterns.

4. **Label smoothing (0.1):** Encourages the from-scratch model to spread probability
   mass, potentially helping with diverse SQL constructs.
