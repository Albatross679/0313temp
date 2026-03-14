---
name: sweep-mlp-checkpoint-state-dict-mismatch
description: MLP head trials save wrapper state_dict with extra keys, causing load failures in subsequent trials and final eval
type: issue
status: resolved
severity: high
subtype: model
created: 2026-03-14
updated: 2026-03-14
tags: [sweep, checkpoint, state_dict, mlp, save, load]
aliases: []
---

# MLP Checkpoint State Dict Mismatch

## Symptom

In sweep v4, trials following MLP head trials (trials 2, 5) crashed immediately with:

```
Error(s) in loading state_dict for T5ForConditionalGeneration:
    Unexpected key(s) in state_dict: "mlp_norm.weight", "mlp_norm.bias",
    "mlp.0.weight", "mlp.0.bias", "mlp.3.weight", "mlp.3.bias".
```

This also affected the MLP trials' own final evaluation — after early stopping, the best checkpoint couldn't be reloaded because it was saved with MLP keys but loaded into a vanilla T5.

## Root Cause

`save_model()` in `part1/model.py` had a bug in the non-peft branch:

```python
inner = _get_inner_model(model)  # correctly unwraps T5ForFlightSQL → model.model
if _is_peft_model(inner):
    # ... merge and save inner T5 state_dict (correct)
else:
    torch.save(model.state_dict(), path)  # BUG: saves wrapper, not inner
```

`_get_inner_model()` correctly unwraps `T5ForFlightSQLWithMLP` → inner T5 model, but the else branch saved `model.state_dict()` (the full wrapper including MLP layers) instead of `inner.state_dict()` (just the T5 weights).

Then `load_model_from_checkpoint()` creates a vanilla `T5ForConditionalGeneration` and calls `model.load_state_dict(...)` with `strict=True` (default), which fails on the unexpected MLP keys.

The LoRA path was correct because it explicitly saves `merged.state_dict()` (the inner model after merge_and_unload).

## Impact

- 4 out of 8 sweep v4 trials were wasted:
  - Trials 2, 5: state_dict error loading checkpoint
  - Trials 3, 7: OOM from unreleased VRAM after state_dict crash
- MLP trials (1, 4) couldn't run final dev evaluation on best checkpoint, so the "Final dev" metrics were never reported for them

## Fix

Changed `save_model()` to always save `inner.state_dict()` instead of `model.state_dict()`:

```python
else:
    # Always save the inner T5 state_dict, not the wrapper
    torch.save(inner.state_dict(), path)
```

This ensures checkpoints always contain vanilla T5 weights, consistent with the LoRA path which already did this via `merge_and_unload()`.

## Files Modified

- `part1/model.py`: `save_model()` — save `inner.state_dict()` instead of `model.state_dict()`
