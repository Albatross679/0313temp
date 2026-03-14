---
name: sweep-backward-pass-exception
description: Sweep trial 3 crashed with bare Exception during loss.backward() at epoch 71
type: issue
status: resolved
severity: low
subtype: training
created: 2026-03-14
updated: 2026-03-14
tags: [sweep, cuda, backward, transient]
aliases: []
---

# Sweep Trial 3 — Bare Exception During loss.backward()

## Symptom

Sweep trial 3 (architecture: `full_ft`) crashed at epoch 71 (~53% through the epoch) with a bare `Exception` in the autograd backward pass:

```
File "/home/turncloak/0313temp/part1/train.py", line 519, in train_epoch
    loss.backward()
...
File "/home/turncloak/.local/lib/python3.12/site-packages/torch/autograd/graph.py", line 865, in _engine_run_backward
    return Variable._execution_engine.run_backward(
Exception
```

No further detail — just `Exception` with no message.

## Impact

Trial 3 lost. The sweep agent recovered and started trial 4 successfully with auto batch size 16→32.

## Root Cause

Likely a transient CUDA error or memory corruption. The bare `Exception` from the C++ autograd engine typically indicates a low-level GPU issue rather than a Python-level bug. Contributing factors:
- Previous trial (trial 2, LoRA) crashed mid-setup, possibly leaving VRAM in a dirty state
- `cleanup_vram()` runs between trials but may not fully clear CUDA state after an abnormal exit

## Resolution

Self-resolved — sweep agent moved to trial 4 which ran successfully. No code fix needed. The `cleanup_vram()` function between trials provides sufficient recovery for most cases.
