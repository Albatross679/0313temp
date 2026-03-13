---
name: eval-speedup
description: Optimizations to reduce T5 training eval time from 370s to 25-40s per epoch
type: experiment
status: complete
created: 2026-03-11
updated: 2026-03-11
tags:
  - performance
  - evaluation
  - beam-search
  - training
aliases: []
---

# Eval Speedup Optimizations

## Problem

Evaluation epochs during T5 training took ~370s vs ~40s for training epochs.
The bottleneck was autoregressive beam search generation (`num_beams=4`,
`max_new_tokens=512`) on 466 dev examples, plus a redundant teacher-forced loss
pass over the full dev set.

## Root Cause Analysis

| Component | Time | Why |
|-----------|------|-----|
| Teacher-forced loss (dev) | ~30s | Full forward pass over 466 examples (redundant) |
| Beam search generation | ~340s | 512 steps × 4 beams × 30 batches, autoregressive |
| **Total eval** | **~370s** | |
| Training epoch | ~40s | Single parallel forward + backward (teacher-forced) |

Training is fast because teacher forcing processes the entire target sequence in
one parallel forward pass. Beam search generates tokens one at a time — up to
`max_new_tokens × num_beams = 2048` sequential decoder forward passes per batch.

## Optimizations Applied

### 1. Greedy decoding during training eval (HIGH IMPACT)

**Config:** `eval_num_beams` (default: `1` in part2 v2, `None` → inherit in part1)

During training, eval only needs a directional signal for early stopping and
checkpoint selection. Greedy decoding (`num_beams=1`) has very high rank
correlation with beam search for model selection — if checkpoint A beats B under
greedy, it almost always beats it under beam search too.

Full beam search (`num_beams=4`) is used only for the final eval on the best
checkpoint (`is_final=True`).

**Expected speedup:** ~4× on generation time.

### 2. Dev subset during training eval (HIGH IMPACT)

**Config:** `eval_subset_size` (default: `150` in part2 v2, `None` → full in part1)

Instead of generating on all 466 dev examples during training, use the first 150.
This provides a reliable enough Record F1 estimate for early stopping (150
examples is well above the threshold for stable metrics), while reducing
generation time proportionally.

Full dev set is used for final eval (`is_final=True`).

**Expected speedup:** ~3× on generation time (466 → 150 examples).

### 3. `early_stopping=True` in beam search (MEDIUM IMPACT)

When `num_beams > 1`, HuggingFace `generate()` now stops beam search as soon as
`num_beams` complete candidates are found, rather than continuing until all beams
reach `max_new_tokens`. Since most SQL queries are well under 512 tokens (median:
186), this avoids wasting decode steps on beams that are still going after the
best answer is already complete.

**Expected speedup:** 10–30% on beam search.

### 4. `torch.inference_mode()` instead of `torch.no_grad()` (LOW IMPACT)

`inference_mode()` disables both gradient computation AND view tracking / version
counter bumps, providing a small additional speedup over `no_grad()`.

**Expected speedup:** 0–5%.

### 5. Dropped redundant loss pass (LOW IMPACT)

`eval_epoch_gpu` previously iterated over the dev set twice:
1. Teacher-forced forward pass to compute dev loss (~30s)
2. Beam search generation (~340s)

The dev loss is not used for checkpoint selection (Record F1 is), so the first
pass was removed. `eval_epoch_gpu` now returns only predictions, not loss.

**Expected speedup:** ~30s saved per eval epoch.

## Combined Impact

| Scenario | Config | Estimated eval time |
|----------|--------|---------------------|
| **Before** (beam=4, all 466, + loss pass) | — | ~370s |
| **After** (greedy, 150 examples, no loss) | `eval_num_beams=1, eval_subset_size=150` | ~25–40s |
| **Final eval** (beam=4, all 466, no loss) | `is_final=True` | ~310s |

Training-time eval drops from ~370s to ~25–40s — nearly matching a training
epoch. The full-quality beam search eval runs once at the end on the best
checkpoint.

## Files Changed

- `src/config.py` — Added `eval_num_beams`, `eval_subset_size` to `SLNeuralConfig`
- `part1/train.py` — All 5 optimizations applied
- `part2/train.py` — All 5 optimizations applied
- `part2/config.py` — Set `eval_num_beams=1`, `eval_subset_size=150` in v2 config

## API Changes

`eval_epoch_gpu()` signature changed:
```python
# Before
def eval_epoch_gpu(cfg, model, dev_loader, device):
    return eval_loss, all_preds

# After
def eval_epoch_gpu(cfg, model, dev_loader, device, *, is_final=False):
    return all_preds
```

`eval_epoch()` return value changed:
```python
# Before
return eval_loss, record_f1, record_em, sql_em, error_rate

# After
return record_f1, record_em, sql_em, error_rate
```

`_collect_async_sql()` pending tuple changed (removed `p_eval_loss`):
```python
# Before: (future, epoch, eval_loss, tr_loss, grad_norm, lr, ...)
# After:  (future, epoch, tr_loss, grad_norm, lr, ...)
```

## Token Length Distribution (dev.sql)

Justification for keeping `max_new_tokens=512`:

| Metric | Value |
|--------|-------|
| Mean | 211 tokens |
| Median | 186 tokens |
| p90 | 351 tokens |
| p95 | 447 tokens |
| Max | 503 tokens |
| > 256 | 120 / 466 (26%) would truncate |
| > 512 | 0 / 466 |
