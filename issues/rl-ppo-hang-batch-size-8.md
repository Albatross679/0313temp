---
name: rl-ppo-hang-batch-size-8
description: PPO training hangs silently when model.generate() allocates too much VRAM for KV cache
type: issue
status: resolved
severity: high
subtype: training
created: 2026-03-14
updated: 2026-03-14
tags: [rl, ppo, generate, hang, vram, deadlock, sub-batch]
aliases: [ppo-generate-hang, batch-size-8-deadlock]
---

## Symptom

PPO training (config `t5_ft_ppo_v1`) hangs silently immediately after setup.
Process prints "Device: cuda" then produces no further output for 10+ minutes.

**Observable state during hang:**
- GPU memory: 23 GB / 32 GB allocated (71%)
- GPU utilization: 0% consistently (sampled 10× over 10 seconds)
- CPU utilization: 0%
- All 136 threads in `futex_wait_queue` (kernel wait state)
- W&B filestream still sending system metrics (every 15s)
- No training output, no error, no traceback

## Root Cause

Two issues combined:

### 1. Silent VRAM deadlock in model.generate()

`sample_group_completions()` called `gen_model.generate()` on all B×G sequences
at once. With the original config (batch_size=8, group_size=8), this meant 64
concurrent sequences with max_new_tokens=256. The KV cache allocation (~23 GB)
left insufficient headroom, causing a silent CUDA memory allocation failure that
deadlocked instead of throwing OOM.

### 2. Batch loop iterating over wrong range

After the executor added `train_subset_size=500` (subsampling), the batch loop
still iterated over `num_train=4225` instead of `effective_train=500`:

```python
# BUG: iterates 1056 batches, but only 125 have data
for batch_start in range(0, num_train, cfg.batch_size):
    batch_indices = indices[batch_start:batch_end]  # indices has only 500 elements
```

Batches 126-1056 would get empty `batch_indices`, causing downstream failures
(empty tensor generation, division by zero in reward computation).

## Fix Applied

### Sub-batch generation (rl_train.py:151-196)

Chunk `model.generate()` into sub-batches of `gen_batch_size` (default 16)
to bound peak VRAM from KV cache allocation. This decouples training batch_size
from generation VRAM:

```python
gen_bs = getattr(cfg, 'gen_batch_size', 16)
all_outputs = []
with torch.inference_mode(), _amp_context(cfg.use_amp, device):
    for chunk_start in range(0, total_seqs, gen_bs):
        chunk_end = min(chunk_start + gen_bs, total_seqs)
        chunk_out = gen_model.generate(
            encoder_outputs=...[chunk_start:chunk_end],
            attention_mask=...[chunk_start:chunk_end],
            **base_gen_kwargs,
        )
        all_outputs.append(chunk_out)
# Pad and concatenate sub-batch outputs
```

### Batch loop fix (rl_train.py:651)

```python
# FIXED: iterate over effective_train, not num_train
for batch_start in range(0, effective_train, cfg.batch_size):
```

### Config field (rl_config.py)

Added `gen_batch_size: int = 16` to `T5GRPOConfig` with CLI override support.

## Result

- Training runs at ~3.6s/batch, ~7.5 min/epoch with batch_size=4, group_size=4
- VRAM: 5.8 GB / 32 GB (can safely increase batch_size since generation is chunked)
- 125 batches/epoch with 500-query subsample, ~25 epochs in 3h budget

## Files Modified

- `part1/rl_train.py` — sub-batch generation, batch loop fix, CLI arg
- `part1/rl_config.py` — `gen_batch_size` field added to `T5GRPOConfig`
