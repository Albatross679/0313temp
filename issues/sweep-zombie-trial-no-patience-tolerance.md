---
name: sweep-zombie-trial-no-patience-tolerance
description: LoRA sweep trial ran 335 epochs (~10h) due to marginal F1 gains resetting early stopping patience without a minimum improvement threshold
type: issue
status: resolved
severity: medium
subtype: training
created: 2026-03-14
updated: 2026-03-14
tags: [sweep, early-stopping, patience, lora, efficiency]
aliases: [zombie-trial]
---

# Sweep Zombie Trial: No Patience Tolerance

## Symptom

Sweep v4 trial 8 (lora_qkvo_r32) ran for **335 epochs across ~10 hours**, consuming most of the 12-hour sweep budget on a single trial that peaked at F1=0.772 — well below the full_ft best of 0.865.

The trial kept finding tiny marginal F1 improvements (~0.005-0.01) that reset the 7-cycle early stopping patience window:

```
Epoch 135: F1 = 0.672  → patience reset
Epoch 163: F1 = 0.680  → patience reset (+0.008)
Epoch 187: F1 = 0.689  → patience reset (+0.009)
Epoch 199: F1 = 0.695  → patience reset (+0.006)
Epoch 211: F1 = 0.713  → patience reset (+0.018)
Epoch 227: F1 = 0.719  → patience reset (+0.006)
Epoch 243: F1 = 0.736  → patience reset (+0.017)
Epoch 271: F1 = 0.747  → patience reset (+0.011)
Epoch 283: F1 = 0.754  → patience reset (+0.007)
Epoch 299: F1 = 0.769  → patience reset (+0.015)
Epoch 307: F1 = 0.772  → patience reset (+0.003)
Epoch 335: early stopped (patience=7)
```

Each reset extended the trial by another 28 epochs (7 patience cycles × 4 epochs between evals). The pattern repeated ~11 times, adding ~300 extra epochs.

## Root Cause

`patience_tolerance` was set to `0.0` (default), meaning **any improvement in F1, no matter how small, counts as a real improvement** and resets the patience counter. This is fine for trials that converge quickly (like full_ft at 71 epochs), but pathological for slowly-converging architectures like LoRA that grind upward in tiny increments.

## Impact

- Trial 8 consumed ~10h of the 12h sweep budget
- Only 4 trials completed out of 8 attempts (the other 4 were instant failures from separate bugs)
- No time remained for additional full_ft or other architecture trials

## Fix

Set `patience_tolerance: float = 0.005` in `T5FineTuneConfig_base_v1` (and inherited configs). This requires at least a 0.5% F1 improvement to count as a real improvement and reset patience.

With this tolerance, trial 8 would have early-stopped much earlier:
- Epoch 163 (F1=0.680): +0.008 from 0.672 → resets (above 0.005)
- Epoch 187 (F1=0.689): +0.009 → resets
- Epoch 199 (F1=0.695): +0.006 → resets
- Epoch 211 (F1=0.713): +0.018 → resets
- Epoch 227 (F1=0.719): +0.006 → resets
- Epoch 243 (F1=0.736): +0.017 → resets
- Epoch 271 (F1=0.747): +0.011 → resets
- Epoch 283 (F1=0.754): +0.007 → resets
- Epoch 299 (F1=0.769): +0.015 → resets
- Epoch 307 (F1=0.772): +0.003 → **DOES NOT reset** (below 0.005)
- Would early-stop at ~epoch 307 + 28 = 335

In this specific case 0.005 wouldn't have helped much. A tolerance of 0.01 would have stopped the trial around epoch ~271 (saving ~2.5h). The right value depends on the task — 0.005 is a conservative starting point that prevents the most egregious cases.

## Files Modified

- `part1/config.py`: Added `patience_tolerance: float = 0.005` to `T5FineTuneConfig_base_v1`
