---
name: max-new-tokens-truncation
description: max_new_tokens=256 truncates 26% of dev targets during inference
type: issue
status: resolved
severity: medium
subtype: model
created: 2026-03-11
updated: 2026-03-11
tags:
  - part2
  - t5-scratch
  - inference
  - generation
aliases: []
---

# max_new_tokens=256 Truncates 26% of Targets

## Context

Run: `output/t5_scr_v2_fixed_20260303_184330` (T5ScratchConfig_v2)

## Symptom

Complex queries with multiple joins were truncated during inference, producing
incomplete SQL that fails to execute.

## Root Cause

- Dev set: 120/466 queries (25.8%) have targets > 256 tokens.
- Train set: 1147 samples have targets > 256 tokens.
- Max target length: 511 tokens.

During training the model sees full targets, but during inference it is cut
off at 256 tokens.

## Fix

Set `max_new_tokens=512`:

```python
@dataclass
class T5ScratchConfig_v2(T5ScratchConfig):
    max_new_tokens: int = 512  # was 256
```
