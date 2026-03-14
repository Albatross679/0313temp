---
name: sweep-inter-trial-oom-fragmentation
description: OOM between sweep trials due to CUDA memory fragmentation even after successful cleanup
type: issue
status: resolved
severity: medium
subtype: training
created: 2026-03-14
updated: 2026-03-14
tags: [sweep, oom, vram, fragmentation, cuda]
aliases: []
---

# OOM Between Sweep Trials Due to CUDA Memory Fragmentation

## Symptom

After trial 1 completed successfully (including cleanup), trial 2 OOMed at `model.to(device)`:

```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 170.00 MiB.
GPU 0 has a total capacity of 31.36 GiB of which 74.25 MiB is free.
435.57 MiB is reserved by PyTorch but unallocated.
```

74 MiB free + 435 MiB reserved-but-unallocated = ~509 MiB technically available, but PyTorch couldn't satisfy a 170 MiB allocation because the free blocks were fragmented into non-contiguous pieces.

## Root Cause

PyTorch's default CUDA memory allocator reserves memory in fixed-size blocks. After a full training run (forward/backward passes with varying tensor sizes), these blocks become fragmented. Even after `del model` and `torch.cuda.empty_cache()`, the freed blocks may not be contiguous enough for the next trial's model allocation.

This is distinct from the crash-loop OOM issue (see `sweep-oom-crash-loop.md`) — that was caused by unreleased references. This happens even when cleanup succeeds.

## Fix

Set `PYTORCH_ALLOC_CONF=expandable_segments:True` before any CUDA allocation. This tells PyTorch to use expandable memory segments instead of fixed blocks, which avoids fragmentation.

Added to `part1/sweep.py`:
```python
os.environ.setdefault("PYTORCH_ALLOC_CONF", "expandable_segments:True")
```

## References

- PyTorch docs: https://pytorch.org/docs/stable/notes/cuda.html#environment-variables
