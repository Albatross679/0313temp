---
name: GPU OOM from concurrent Claude Code sessions
description: Multiple Claude Code sessions submitting GPU tasks causes CUDA OOM because AutoBatch maximizes VRAM for the first task, leaving nothing for the second.
type: issue
status: resolved
severity: high
subtype: performance
created: 2026-03-12
updated: 2026-03-12
tags: [gpu, oom, vram, concurrency, autobatch]
aliases: [gpu-lock, vram-contention, concurrent-training-oom]
---

# GPU OOM from Concurrent Claude Code Sessions

## Problem

When running training with AutoBatch enabled, the batch size is tuned to maximize VRAM usage. If another Claude Code session then submits a GPU task (e.g., another training run, evaluation, or inference), CUDA runs out of memory because the first process has already allocated nearly all available VRAM.

This is a recurring issue when working across multiple Claude Code sessions on the same machine with a single GPU.

## Root Cause

AutoBatch probes for the largest batch size that fits VRAM. Once training starts, VRAM is fully committed. Any second GPU process that tries to allocate CUDA memory triggers an OOM error.

There was no mechanism to prevent concurrent GPU access across separate sessions.

## Solution

Implemented a file-based GPU lock using Linux `flock`:

1. **Python lock** (`src/utils/gpu_lock.py`): `GpuLock` context manager using `fcntl.flock` on `/tmp/gpu-task.lock`.
2. **Shell wrapper** (`script/gpu-lock.sh`): `run`, `status`, `wait` subcommands using the same lockfile.
3. **Automatic integration**: All training entry points (`train_t5.py`, `part1/train.py`, `part2/train.py`, `part3/train.py`, `prompting.py`) wrap `main()` with `GpuLock()` in their `if __name__ == "__main__"` block.

When a GPU task is running, any other GPU task blocks and waits until the first completes. The lock auto-releases on process exit, crash, or kill (flock guarantee).

## Key Properties

- **Automatic**: No manual wrapping needed for standard training commands.
- **Cross-language**: Shell and Python locks are mutually exclusive (same lockfile).
- **Crash-safe**: `flock` releases automatically when the file descriptor closes.
- **Queue behavior**: Second task waits, doesn't error.

## Files Changed

- `src/utils/gpu_lock.py` — New: Python GpuLock context manager
- `script/gpu-lock.sh` — New: Shell wrapper with run/status/wait
- `train_t5.py` — Added GpuLock wrapping
- `part1/train.py` — Added GpuLock wrapping
- `part2/train.py` — Added GpuLock wrapping
- `part3/train.py` — Added GpuLock wrapping
- `prompting.py` — Added GpuLock wrapping
- `CLAUDE.md` — Documented as hard preference
- `.claude/skills/ml-workflow/SKILL.md` — Added GPU Task Serialization section
