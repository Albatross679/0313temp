---
name: sweep-oom-crash-loop
description: Sweep enters OOM crash loop after a trial fails — cleanup_vram cannot free model tensors held by main_with_config locals
type: issue
status: resolved
severity: high
subtype: training
created: 2026-03-14
updated: 2026-03-14
tags: [sweep, oom, vram, cleanup, crash-loop]
aliases: []
---

# Sweep OOM Crash Loop After Trial Failure

## Symptom

After trial 5 crashed mid-training, 6+ consecutive trials immediately OOMed at `model.to(device)`:

```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 20.00 MiB.
GPU 0 has a total capacity of 31.36 GiB of which 10.25 MiB is free.
```

The sweep burned through its trial count with every trial crashing instantly.

## Root Cause

`cleanup_vram()` only called `gc.collect()` and `torch.cuda.empty_cache()`, but the model/optimizer tensors were still referenced by `main_with_config()`'s local variables in the stack frame. After an exception:

1. `main_with_config` raises an exception mid-execution
2. Python keeps the stack frame alive (traceback holds refs to locals)
3. `sweep_train`'s `finally` block calls `cleanup_vram()`
4. But `gc.collect()` can't free the tensors because the traceback still references them
5. `torch.cuda.empty_cache()` only frees cached (unreferenced) memory — not allocated tensors
6. Next trial tries `model.to(device)` → OOM because previous model is still on GPU

## Fix

1. **`sweep_train` now catches exceptions explicitly** — `except Exception as e` handles the error and allows the stack frame to unwind, releasing local variable references before cleanup.

2. **Double `gc.collect()` pass** — catches reference cycles that a single pass might miss.

3. **`cleanup_vram()` enhanced** — added `torch.cuda.synchronize()` and `torch.cuda.reset_accumulated_memory_stats()` for more thorough cleanup.

## Files Modified

- `part1/sweep.py`: Added exception handling in `sweep_train`, double gc.collect
- `part1/train.py`: Enhanced `cleanup_vram()` with synchronize and reset_accumulated_memory_stats

## Also Changed

Switched sweep from Bayesian (`"method": "bayes"`) to random search (`"method": "random"`) to get broader architecture coverage instead of Bayesian converging on full_ft only.
