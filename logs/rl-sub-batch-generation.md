---
name: rl-sub-batch-generation
description: Add sub-batch generation to RL training to decouple VRAM from batch_size and fix batch loop bug
type: log
status: complete
subtype: fix
created: 2026-03-14
updated: 2026-03-14
tags: [rl, ppo, grpo, cispo, generation, vram, sub-batch]
aliases: []
---

## Context

RL training (PPO/GRPO/CISPO) hung silently when `model.generate()` tried to
allocate KV cache for all B×G sequences at once. With batch_size=8, group_size=8,
that meant 64 concurrent sequences — the KV cache consumed 23 GB and caused a
silent CUDA deadlock.

## Changes

### 1. Sub-batch generation (`part1/rl_train.py`)

`sample_group_completions()` now chunks `gen_model.generate()` into sub-batches
of `gen_batch_size` (default 16). Peak generation VRAM is bounded regardless of
training batch_size. Sub-batch outputs are padded to equal length and concatenated.

### 2. Batch loop fix (`part1/rl_train.py:651`)

Fixed `range(0, num_train, ...)` → `range(0, effective_train, ...)` to respect
`train_subset_size`. Previously iterated over 1056 batches when only 125 had data.

### 3. Config field (`part1/rl_config.py`)

Added `gen_batch_size: int = 16` to `T5GRPOConfig` with CLI override
(`--gen_batch_size`).

## Impact

- Training batch_size can now be increased freely without VRAM risk (generation
  is always chunked to gen_batch_size sequences)
- Current config: batch_size=4, group_size=4, gen_batch_size=16 → ~3.6s/batch,
  ~7.5 min/epoch, 5.8 GB VRAM
- Enables future batch_size increase for larger effective optimization batches

## Related

- Issue: `issues/rl-ppo-hang-batch-size-8.md`
