---
name: graceful-stop-and-extra-configs
description: Graceful stop, 10 config variants (LoRA/MLP/full), auto batch size, VRAM cleanup, early stopping tuning
type: log
status: complete
subtype: feature
created: 2026-03-11
updated: 2026-03-11
tags: [part1, training, config, graceful-stop, lora, mlp, batch-size]
aliases: []
---

# Graceful Stop, Config Variants, and Training Infrastructure

## Graceful Stop Mechanism

Added to `part1/train.py`:

1. **SIGTERM handler** — catches `kill <pid>`, sets `_STOP_REQUESTED` flag
2. **Stop file** — `touch STOP` checked between epochs and between configs
3. **`stop_requested()` function** — importable, usable between configs in executor

Both allow the current epoch to finish, drain pending async SQL, save checkpoint, then exit.

## 10 Config Variants (priority order)

| # | Config Class | Type | LR | Schema | Special |
|---|-------------|------|-----|--------|---------|
| 1 | lora_v1 | LoRA | 3e-4 | none | r=16, alpha=32, q+v |
| 2 | lora_v2 | LoRA | 3e-4 | tables | r=16, alpha=32, q+v |
| 3 | lora_v3 | LoRA | 2e-4 | none | r=32, alpha=64, q+k+v+o |
| 4 | restricted_v2 | Full FT | 1e-4 | none | baseline fix |
| 5 | restricted_v3 | Full FT | 3e-4 | tables | aggressive |
| 6 | mlp_v1 | MLP head | 1e-4 | none | 1024-dim post-decoder MLP |
| 7 | mlp_v2 | MLP head | 1e-4 | tables | MLP + schema |
| 8 | lora_freeze_enc | LoRA | 5e-4 | none | frozen encoder + LoRA |
| 9 | restricted_v5 | Full FT | 3e-4 | none | frozen encoder |
| 10 | restricted_v7 | Full FT | 1e-4 | tables | dropout=0.2 |

All use restricted vocabulary. LoRA variants run first (fastest, most promising).

## T5ForFlightSQLWithMLP

New wrapper class in `part1/model_flightdb.py`:
- Adds LayerNorm → Linear(d, 1024) → GELU → Dropout → Linear(1024, d) → residual
- Between decoder hidden states and restricted subset projection
- Zero-init output layer so residual starts as identity (safe initialization)

## Auto Batch Size

`auto_batch_size: bool = True` in base config. At startup, runs a synthetic forward+backward
pass with doubling batch sizes to find the largest that fits in ~85% VRAM.

## VRAM Cleanup

`cleanup_vram()` replaces scattered `gc.collect() + torch.cuda.empty_cache()` calls.
Also calls `reset_peak_memory_stats()` for clean monitoring between runs.

## Early Stopping Tuning

- `eval_every_n_epochs`: 8 → 4 (eval twice as often)
- `patience_epochs`: 5 → 7 (counts eval cycles)
- Effective patience: 7 × 4 = 28 training epochs (was 5 × 8 = 40)
- More responsive: detects stagnation in ~28 epochs instead of ~40
