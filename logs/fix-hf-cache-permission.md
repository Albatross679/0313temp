---
name: fix-hf-cache-permission
description: Resolved HuggingFace cache permission denied by overriding HF_HOME
type: log
status: complete
subtype: fix
created: 2026-03-11
updated: 2026-03-11
tags:
  - debugging
  - environment
  - training
  - huggingface
aliases: []
---

# Fix: HuggingFace Cache Permission Denied

## Symptom

```
PermissionError: [Errno 13] Permission denied: '/workspace/.hf_home/hub'
OSError: PermissionError at /workspace/.hf_home/hub when downloading google-t5/t5-small.
```

Raised at import time inside `part1/data.py` when `T5TokenizerFast.from_pretrained()`
tried to write to the default HF cache.

## Root Cause

The environment variable `HF_HOME` was pointing to `/workspace/.hf_home`, a directory
owned by `root` that the `coder` user cannot write into.

## Fix

Override `HF_HOME` at launch to a user-writable directory (`~/.cache/huggingface`
already existed and had correct permissions):

```bash
HF_HOME=~/.cache/huggingface python3 -m part1.train --config T5FineTuneConfig
```

### Permanent Fix

Add to `~/.bashrc` or the project's `.env`:

```bash
export HF_HOME=~/.cache/huggingface
```
