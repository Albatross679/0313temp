---
name: rl-reward-all-negative-one
description: RL training produces reward=-1.0 for all samples due to truncated SQL and excessive sampling temperature
type: issue
status: resolved
severity: high
subtype: training
created: 2026-03-14
updated: 2026-03-14
tags: [rl, reward, temperature, truncation, sql]
aliases: []
---

## Symptom

PPO training shows `reward_mean ≈ -1.0` for every batch. The reward function
returns -1.0 for SQL execution errors, meaning all generated SQL fails to execute.

## Root Cause (Two Factors)

### 1. max_completion_length=128 truncates 85% of SQL

Gold SQL token length distribution: min=26, median=199, p90=362, p99=492, max=511.
With max_completion_length=128, 85% of queries produce "incomplete input" errors —
the SQL is syntactically valid but gets cut off mid-query.

### 2. sampling_temperature=1.0 corrupts SQL tokens

With temp=1.0 and the restricted 598-token SQL vocabulary:
- Greedy (max=512): 7/8 execute OK
- temp=1.0 (max=512): 1/8 execute OK — tokens like "SELment", "flightTER_1"
- temp=0.7 (max=512): 6/8 execute OK — good exploration/quality balance
- temp=0.5 (max=512): 7/8 execute OK — near-greedy quality

## Fix

Updated `part1/rl_config.py`:
- `sampling_temperature: 1.0 → 0.7`
- `max_completion_length: 128 → 512`

After fix: reward_mean improved from -1.0 to +0.28/+0.69 range.

## Files Modified

- `part1/rl_config.py` — temperature and max_completion_length
