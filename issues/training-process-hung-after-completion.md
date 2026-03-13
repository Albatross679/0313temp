---
name: training-process-hung-after-completion
description: Python training process blocks on futex after W&B marks run FINISHED
type: issue
status: resolved
severity: high
subtype: performance
created: 2026-03-11
updated: 2026-03-11
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

Likely PyTorch/CUDA threading deadlock during GPU memory cleanup. The
`ThreadPoolExecutor(max_workers=1)` for async SQL eval, combined with the
background task output pipe being deleted, likely prevented clean exit.

## Fix

Added watchdog co-process to `run_base_configs.sh` that polls W&B status
every 60s and kills the training process if it's still alive 5 min after the
run is marked FINISHED. Also treats exit codes 137 (SIGKILL) and 143 (SIGTERM)
as success when coming from the watchdog.

For ad-hoc runs, manually killed with `kill` after confirming output files
were complete.
