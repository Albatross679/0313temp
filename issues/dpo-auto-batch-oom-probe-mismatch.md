---
name: DPO auto batch size probe overestimates safe batch size
description: Auto batch probe found batch_size=32 but training OOM'd due to probe measuring current allocation instead of peak, and not accounting for full pipeline overhead
type: issue
status: resolved
severity: high
subtype: performance
created: 2026-03-14
updated: 2026-03-14
tags: [dpo, auto-batch, oom, vram]
aliases: [auto-batch-oom]
---

## Summary

The `dpo_auto_batch_size()` probe found batch_size=32 fit within 85% VRAM, but actual DPO training OOM'd on the first epoch. Cascading CUDA context poisoning caused all subsequent sweep trials to fail immediately.

## Root Cause (two issues)

### 1. Current vs peak memory measurement
The probe used `torch.cuda.memory_allocated()` which measures current allocation AFTER intermediates are freed. DPO's 4 forward passes create large activation tensors that are freed before measurement. Fix: use `torch.cuda.max_memory_allocated()` with `reset_peak_memory_stats()`.

### 2. VRAM target too aggressive
Even with peak measurement, 70-85% targets left insufficient headroom for:
- Real optimizer state (AdamW momentum + variance for ~222M params = ~1.7 GB)
- Dev/test data loaders loaded after the probe
- Variable-length batch padding (probe uses first batch; training sees longer sequences)
- W&B overhead, scheduler state

## Fix

1. Changed probe to use `torch.cuda.max_memory_allocated()` for peak measurement
2. Lowered `target_vram_pct` from 0.85 → 0.55 for DPO (conservative due to 4 forward passes + dual model overhead)
3. Result: batch_size=16 (2x original) — stable, no OOM

## Root Cause (revised after deeper investigation)

The primary cause was **not** the VRAM target percentage — it was the probe testing with **unrepresentative data**. The probe used the first batch (max seq len 255) while training encountered batches with seq len up to 511 (2x longer). Since attention memory scales with sequence length, worst-case batches needed far more VRAM than the probe measured.

Lowering target_vram_pct from 85% to 55% was a band-aid that happened to reject batch_size=32, but it also prevented finding intermediate sizes (24, 28) that might have worked.

## Final Fix (v3)

1. **Worst-case probing**: Sort dataset by sequence length, build probe batches from the longest samples
2. **Peak memory measurement**: `torch.cuda.max_memory_allocated()` with `reset_peak_memory_stats()`
3. **Two-phase search**: Coarse (powers of 2) then fine-grained (intermediate values)
4. **Target back to 85%**: Correct measurement eliminates need for excessive safety margin

## Lesson

Auto batch probes must test with **worst-case data**, not first-available data. Variable-length sequences (common in NLP) create up to 2x memory variance between batches. Always sort by length and probe with the longest samples. Updated ml-workflow skill with this pattern.
