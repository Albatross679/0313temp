---
name: pythonpath-module-not-found
description: ModuleNotFoundError for part1/part2 packages without PYTHONPATH set
type: issue
status: resolved
severity: low
subtype: compatibility
created: 2026-03-11
updated: 2026-03-11
tags:
  - environment
  - training
aliases: []
---

# PYTHONPATH Required for Module Imports

## Symptom

```
ModuleNotFoundError: No module named 'part1'
```

## Root Cause

Python does not include the project root in `sys.path` by default when
running with `python3 -m`.

## Fix

Set `PYTHONPATH=/home/coder/nlp_Assignment3` before launching training.
