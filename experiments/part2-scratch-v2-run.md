---
name: part2-scratch-v2-run
description: T5ScratchConfig v2 run — early stopped at epoch 25, SQL-like output but missing SELECT
type: experiment
status: complete
created: 2026-03-11
updated: 2026-03-11
tags:
  - part2
  - t5-scratch
  - training
aliases: []
---

# Part 2 Run 2: T5ScratchConfig_v2

| Field | Value |
|---|---|
| **Run directory** | `output/t5_scr_v2_20260303_164334` |
| **Config class** | `T5ScratchConfig_v2` |
| **Outcome** | Early stopped at epoch 25 |

## Hyperparameters (Changes from v1)

| Parameter | v1 | v2 |
|---|---|---|
| learning_rate | 1e-3 | **3e-4** |
| num_epochs | 50 | **200** |
| patience_epochs | 10 | **25** |
| num_warmup_epochs | 3 | **8** |
| include_schema | False | **True** |
| num_beams | 1 | **4** |
| repetition_penalty | 1.0 | **2.5** |
| no_repeat_ngram_size | 0 | **3** |
| label_smoothing | 0.0 | **0.1** |

## Metrics

| Epoch | Train Loss | Dev Loss | F1 | SQL EM | Error Rate |
|-------|-----------|----------|------|--------|------------|
| 0 | 5.6929 | 2.6122 | 0.1180 | 0.0000 | 100.0% |
| 5 | 1.6489 | 1.5868 | 0.1180 | 0.0000 | 100.0% |
| 10 | 1.4888 | 1.4713 | 0.1180 | 0.0000 | 100.0% |
| 15 | 1.4527 | 1.4396 | 0.1180 | 0.0000 | 100.0% |
| 20 | 1.4368 | 1.4287 | 0.1180 | 0.0000 | 100.0% |
| 25 | 1.4261 | 1.4227 | 0.1180 | 0.0000 | 100.0% |

**Final:** F1=0.1180, EM=0.1180, SQL_EM=0.0000, err=100.0%

## Improvements Over v1

- **No repetition loops**: Anti-repetition penalty + beam search eliminated the
  degenerate outputs from v1.
- **SQL-like structure**: By epoch 7+, predictions showed recognizable SQL fragments
  with table names, WHERE clauses, JOINs, and city string literals.
- **Stable loss curve**: Lower learning rate produced smooth loss decrease without
  the oscillation seen in v1's later epochs.

## Remaining Problems

1. **Missing SELECT keyword**: Predictions consistently start mid-query
   (`_1, airport_2 WHERE...` instead of `SELECT ... FROM ...`). See
   [bos-token-mismatch](../issues/bos-token-mismatch.md).
2. **100% SQL execution error rate**: No prediction was valid enough to execute.
3. **Loss plateaued high**: Dev loss converged to ~1.42 — much higher than v1's
   ~0.30. Label smoothing raises the floor, but the gap suggests the model
   isn't fitting the training distribution well with the lower LR.
4. **Anti-repetition settings block valid SQL**: See
   [no-repeat-ngram-blocks-sql](../issues/no-repeat-ngram-blocks-sql.md) and
   [repetition-penalty-too-aggressive](../issues/repetition-penalty-too-aggressive.md).

## Launch Command

```bash
HF_HOME=/home/coder/.cache/huggingface python3 -u -m part2.train --config T5ScratchConfig_v2
```
