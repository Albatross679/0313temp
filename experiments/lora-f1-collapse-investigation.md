---
name: lora-f1-collapse-investigation
description: Root cause analysis of LoRA F1 collapse during final full-dev evaluation
type: experiment
status: complete
created: 2026-03-11
updated: 2026-03-11
tags: [lora, debugging, checkpoint, part1]
aliases: []
---

# LoRA F1 Collapse Investigation

## Symptom

LoRA configurations (lora_v1, lora_v2) showed training-time subset F1 of 0.335+ but final full-dev evaluation collapsed to F1=0.118. This large gap suggested a systemic issue rather than overfitting or subset bias.

## Root Cause

The final evaluation in `main()` (part1/train.py) followed a delete-reload-rewrap pattern that destroyed trained LoRA adapter weights:

1. **`del model`** -- destroys the trained model with LoRA adapters in memory
2. **`load_model_from_checkpoint()`** -- loads from checkpoint file, which contains only base T5 weights
3. **Re-wraps with `T5ForFlightSQL`** -- creates the restricted vocab wrapper
4. **`get_peft_model(model, lora_config)`** -- applies LoRA with **fresh randomly-initialized** adapters

Step 4 is the bug: the LoRA adapters applied after checkpoint reload are untrained (random init), so the final evaluation runs on a model that has never been fine-tuned with LoRA.

### Why checkpoints lack LoRA weights

`T5ForFlightSQL.state_dict()` in `part1/model_flightdb.py` (lines 226-227) intentionally strips LoRA adapter keys:

```python
# Skip LoRA adapter weights (lora_A, lora_B) -- only save base weights
if ".lora_A." in new_key or ".lora_B." in new_key:
    continue
```

This was designed to produce checkpoints compatible with vanilla `T5ForConditionalGeneration`, but it means the checkpoint file has zero LoRA information.

### Why training-time evals were correct

During training, `eval_epoch_gpu()` is called with the in-memory model that has trained LoRA adapters. The subset F1=0.335 was the real LoRA performance. The collapse only happened in the post-training final eval flow.

## Evidence

- `part1/model_flightdb.py` lines 226-227: explicit `lora_A`/`lora_B` key filtering in `state_dict()`
- `part1/train.py` lines 875-887 (before fix): `get_peft_model()` re-applied with fresh `LoraConfig` after checkpoint reload
- F1=0.118 is consistent with a pretrained T5-small generating SQL without any task-specific fine-tuning (base model baseline)

## Fix Applied

For LoRA models, skip the checkpoint reload entirely and use the in-memory trained model for final evaluation and test inference:

```python
if use_lora:
    # LoRA checkpoints strip adapter weights for vanilla T5 compatibility,
    # so reloading would lose trained adapters. Use in-memory model directly.
    del optimizer, scheduler
    cleanup_vram()
    model.eval()
else:
    # Non-LoRA: free training objects and reload best checkpoint
    del model, optimizer, scheduler
    cleanup_vram()
    # ... existing checkpoint reload logic ...
```

The `get_peft_model` re-application block was removed entirely since it is no longer needed.

## Impact Assessment

- **This was a code bug, not a fundamental LoRA limitation.** The reported F1=0.118 for LoRA was invalid.
- **Actual LoRA performance:** subset F1=0.335 with ~1% trainable parameters. This is significantly worse than full fine-tune F1=0.618, but not catastrophically bad as the reported 0.118 suggested.
- **Non-LoRA models unaffected:** the checkpoint reload path for full fine-tune and from-scratch models remains unchanged.
- **Checkpoint format unchanged:** LoRA checkpoints still save vanilla-compatible base weights (useful for deployment without peft dependency).

## Limitation

The fix uses the in-memory model for final eval, which means the final eval uses the model state from the last training epoch rather than the "best" checkpoint. For LoRA, since checkpoints cannot capture adapter state, this is the only correct approach without changing the checkpoint format. In practice, the last-epoch model is often close to the best-epoch model when early stopping has not triggered.

A future improvement could merge LoRA weights into the base model before saving (`model.merge_and_unload()`), which would produce a vanilla-compatible checkpoint with LoRA enhancements baked in.
