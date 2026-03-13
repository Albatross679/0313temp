---
name: repetition-penalty-too-aggressive
description: repetition_penalty=2.5 distorts token probabilities away from valid SQL
type: issue
status: resolved
severity: high
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

# repetition_penalty=2.5 Too Aggressive for SQL

## Context

Run: `output/t5_scr_v2_fixed_20260303_184330` (T5ScratchConfig_v2)

## Symptom

Generated SQL contained structural anomalies despite the model learning meaningful
patterns (loss decreasing). SQL tokens like `AND`, `.`, `=`, `airport_code`,
`city_code` were underrepresented in predictions.

## Root Cause

A penalty of 2.5 means each token's logit is divided by 2.5 after first use.
SQL reuses tokens like `AND`, `.`, `=`, `airport_code`, `city_code` extensively.
Heavy penalization distorts the probability distribution away from valid SQL.

## Fix

Set `repetition_penalty=1.0` (disable) or at most 1.2:

```python
@dataclass
class T5ScratchConfig_v2(T5ScratchConfig):
    repetition_penalty: float = 1.0  # was 2.5
```
