---
name: training-process-hung-after-completion
description: Python training process blocks on futex after W&B marks run FINISHED
type: issue
status: resolved
severity: high
subtype: performance
created: 2026-03-11
updated: 2026-03-14
tags:
  - training
  - environment
  - pytorch
  - cuda
aliases: []
---

# Training Process Hung After Completion

## Symptom

Training PID (e.g., 110973 for `t5_ft_base_v1`, 792907 for part1 restricted,
876875 for part2 restricted) completed all work — W&B showed FINISHED, test
outputs were saved — but blocked indefinitely on `futex_wait_queue_me` during
`gc.collect()` / `torch.cuda.empty_cache()`.

Sequential training scripts could not proceed to the next config.

## Root Cause

Race condition between background threads and GPU memory cleanup. Three factors:

1. **Orphaned async SQL futures.** The training loop submits `eval_epoch_sql`
   to a `ThreadPoolExecutor(max_workers=1)` for background evaluation. When
   training ends (normal loop exit or early stopping), the `finally` block
   called `_sql_pool.shutdown(wait=False)` — which returns immediately without
   waiting for the in-flight background thread to finish.

2. **Nested thread pools.** The background `eval_epoch_sql` calls
   `compute_records()` which spawns *another* `ThreadPoolExecutor(32 threads)`
   for parallel SQLite execution. These nested threads hold open database
   connections and Python object references.

3. **Cleanup races against live threads.** With background threads still
   running, `gc.collect()` contended for object ownership and
   `torch.cuda.synchronize()` blocked on CUDA stream completion, causing a
   deadlock on Linux futex primitives.

The GpuLock (flock-based) never released because `main()` never returned,
blocking all subsequent training configs.

## Previous Workaround (2026-03-11)

Added exit code handling to `run_base_configs.sh` treating SIGKILL (137) and
SIGTERM (143) as success. Required manual or external watchdog to kill the
hung process.

## Fix (2026-03-14)

Three changes applied to both `part1/train.py` and `part2/train.py`:

1. **Drain pending futures in `finally` block.** Before shutting down the pool,
   all remaining async SQL futures are collected via `_collect_async_sql()`,
   ensuring background threads complete before cleanup begins.

2. **`_sql_pool.shutdown(wait=True)`** instead of `wait=False`, so the pool
   waits for any in-flight work to finish.

3. **Removed `torch.cuda.synchronize()` from `cleanup_vram()`.** This call is
   unnecessary after `empty_cache()` (which synchronizes internally) and was
   the primary futex contention point.
