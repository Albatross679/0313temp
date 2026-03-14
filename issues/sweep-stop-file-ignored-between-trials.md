---
name: STOP file not checked between W&B sweep trials
description: touch STOP only works inside the training epoch loop, not between wandb.agent() trial dispatches
type: issue
status: open
severity: low
subtype: training
created: 2026-03-14
updated: 2026-03-14
tags: [sweep, graceful-stop, wandb]
aliases: [sweep-stop-ignored]
---

## Summary

Creating a `STOP` file to gracefully terminate a DPO sweep did not prevent trial 3 from starting. The sweep had to be killed with `kill -9`.

## Root Cause

`stop_requested()` is checked inside the `dpo_train()` epoch loop (between epochs). But W&B's `wandb.agent()` controls trial dispatch — it calls `sweep_train()` for each new trial without checking any external stop signal. The STOP file is only effective within an active trial's training loop, not between trials.

## Workaround

Kill the sweep process directly: `kill <PID>` (SIGTERM) or `kill -9 <PID>` (SIGKILL).

## Potential Fix

Check `stop_requested()` at the top of `sweep_train()` in `dpo_sweep.py`:
```python
def sweep_train():
    if stop_requested():
        print("STOP file detected, skipping trial")
        raise SystemExit(0)
    ...
```

This would cause `wandb.agent()` to receive an exit signal and stop dispatching new trials.
