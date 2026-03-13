---
name: fix-python-command-not-found
description: Resolved python command not found error by using python3 explicitly
type: log
status: complete
subtype: fix
created: 2026-03-11
updated: 2026-03-11
tags:
  - debugging
  - environment
  - training
aliases: []
---

# Fix: `python` Command Not Found

## Symptom

```
/bin/bash: line 1: python: command not found
```

Exit code `127` when invoking `python -m part1.train`.

## Root Cause

The system only has `python3` on `PATH`; no `python` symlink exists.

## Fix

Use `python3` explicitly for all invocations:

```bash
python3 -m part1.train --config T5FineTuneConfig
```
