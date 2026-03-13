---
name: part2-scratch-v1-run
description: T5ScratchConfig v1 baseline run — early stopped at epoch 10 with degenerate outputs
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

# Part 2 Run 1: T5ScratchConfig (v1 Baseline)

| Field | Value |
|---|---|
| **Run directory** | `output/t5_scr_v1_20260303_160516` |
| **Config class** | `T5ScratchConfig` |
| **Outcome** | Early stopped at epoch 10 |

## Hyperparameters

| Parameter | Value |
|---|---|
| learning_rate | 1e-3 |
| batch_size | 32 |
| scheduler | cosine (3 warmup epochs) |
| num_beams | 1 (greedy) |
| patience_epochs | 10 |
| include_schema | False |
| label_smoothing | 0.0 |

## Metrics

| Epoch | Train Loss | Dev Loss | F1 | SQL EM | Error Rate |
|-------|-----------|----------|------|--------|------------|
| 0 | 3.0817 | 0.9665 | 0.1180 | 0.0000 | 100.0% |
| 1 | 0.7150 | 0.4936 | 0.1180 | 0.0000 | 94.6% |
| 5 | 0.3947 | 0.3019 | 0.1180 | 0.0000 | 100.0% |
| 6 | 0.3816 | 0.2897 | 0.1180 | 0.0000 | 100.0% |
| 10 | 0.4105 | 0.3011 | 0.1180 | 0.0000 | 100.0% |

**Final:** F1=0.1180, EM=0.1180, SQL_EM=0.0000, err=100.0%

## Failure Analysis

1. **Greedy decoding (`num_beams=1`) caused repetition loops**: The model generated
   garbage like `"flight_id AND flight_id AND flight_id..."` or `"days days days..."`.
   By epoch 10 output collapsed to all underscores.
2. **Early stopping too aggressive**: Loss was still decreasing but F1 never exceeded
   baseline (0.1180), so patience=10 killed the run at epoch 10.
3. **No schema context**: Without table/column names in the input, the model had to
   memorize the entire schema from training examples alone.

## Launch Command

```bash
HF_HOME=/home/coder/.cache/huggingface python3 -u -m part2.train --config T5ScratchConfig
```
