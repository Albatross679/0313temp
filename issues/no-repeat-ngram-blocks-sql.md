---
name: no-repeat-ngram-blocks-sql
description: no_repeat_ngram_size=3 structurally prevents generation of valid multi-join SQL
type: issue
status: resolved
severity: critical
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

# no_repeat_ngram_size=3 Blocks Valid SQL

## Context

Run: `output/t5_scr_v2_fixed_20260303_184330` (T5ScratchConfig_v2)

## Symptom

100% SQL execution error rate despite steadily decreasing loss (5.69 -> 1.52 train).
F1 flat at ~0.118 (baseline for empty/failed results).

## Root Cause

**100% of ground truth SQL queries contain repeated 3-grams.** SQL inherently
repeats structural patterns across join conditions:

```sql
-- Repeated 3-grams shown with markers:
airport_service_1.airport_code AND  -- pattern A
airport_service_2.airport_code AND  -- pattern A again (blocked!)
city_1.city_code AND               -- pattern B
city_2.city_code AND               -- pattern B again (blocked!)
```

With `no_repeat_ngram_size=3`, the model is **structurally prevented** from
generating valid multi-join SQL. Every query that needs two or more similar
join conditions (virtually all of them) will be corrupted.

## Fix

Set `no_repeat_ngram_size=0` (disable):

```python
@dataclass
class T5ScratchConfig_v2(T5ScratchConfig):
    no_repeat_ngram_size: int = 0  # was 3
```
