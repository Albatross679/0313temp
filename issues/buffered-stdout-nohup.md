---
name: buffered-stdout-nohup
description: Python stdout buffered when piped through tee or redirected by nohup
type: issue
status: resolved
severity: low
subtype: performance
created: 2026-03-11
updated: 2026-03-11
tags:
  - training
  - environment
  - monitoring
aliases: []
---

# Buffered stdout with nohup/pipe

## Symptom

Log file showed no output for long periods when training via `nohup ... | tee`.
`tee` did not receive lines until Python's stdout buffer flushed.

## Root Cause

Python buffers stdout when not connected to a TTY (e.g., piped through `tee`
or redirected by `nohup`).

## Fix

Added `export PYTHONUNBUFFERED=1` to the training script before launching Python.
