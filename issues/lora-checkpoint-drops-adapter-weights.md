---
name: lora-checkpoint-drops-adapter-weights
description: LoRA final eval collapses to F1=0.118 because checkpoint reload discards trained adapter weights and re-initializes them randomly
type: issue
status: resolved
severity: high
subtype: model
created: 2026-03-11
updated: 2026-03-11
tags: [lora, checkpoint, part1, evaluation, peft]
aliases: [lora-f1-collapse]
---

# LoRA checkpoint drops adapter weights — final eval collapses to F1=0.118

## Symptom

Both LoRA configs (`lora_v1`, `lora_v2`) report training-time subset F1 around 0.335–0.516, but final full-dev evaluation collapses to F1=0.118. The 0.118 figure is consistent across both configs, suggesting a systematic bug rather than overfitting or subset bias.

## Root cause

The post-training final eval flow in `part1/train.py` `main()` followed a **delete → reload → re-wrap** pattern that destroyed trained LoRA adapter weights:

1. **`del model`** — destroys the in-memory model (which has trained LoRA adapters)
2. **`load_model_from_checkpoint()`** — loads from checkpoint file, which only contains base T5 weights
3. **Re-wrap with `T5ForFlightSQL`** — creates the restricted vocab wrapper
4. **`get_peft_model(model, lora_config)`** — applies LoRA with **fresh randomly-initialized** adapters

Step 4 is the bug: the LoRA adapters after checkpoint reload are untrained (random init), so final evaluation runs on a model that was never LoRA-fine-tuned.

### Why checkpoints lack LoRA weights

`T5ForFlightSQL.state_dict()` in [model_flightdb.py:226-228](part1/model_flightdb.py#L226-L228) intentionally strips LoRA adapter keys:

```python
# Skip LoRA adapter weights (lora_A, lora_B) -- only save base weights
if ".lora_A." in new_key or ".lora_B." in new_key:
    continue
```

This was designed to produce checkpoints compatible with vanilla `T5ForConditionalGeneration`, but it means the checkpoint file has zero LoRA information.

### Why training-time evals were correct

During training, `eval_epoch_gpu()` is called with the **in-memory model** that has trained LoRA adapters. The subset F1 of 0.335–0.516 was the real LoRA performance. The collapse only happened in the post-training final eval flow that reloaded from checkpoint.

## Impact

- **Reported LoRA F1=0.118 was invalid.** Actual LoRA performance is ~0.335 (subset) — worse than full fine-tune (0.618) but not catastrophically bad.
- **Non-LoRA models unaffected.** The checkpoint reload path for full fine-tune and from-scratch models works correctly since their checkpoints contain all weights.
- **Did not affect submission.** Best config was `restricted_v3` (full fine-tune, F1=0.618).

## Files involved

- [part1/train.py:857-881](part1/train.py#L857-L881) — post-training eval flow (where the bug manifested)
- [part1/model_flightdb.py:226-228](part1/model_flightdb.py#L226-L228) — `state_dict()` LoRA key stripping

## Fix (two parts)

### 1. Save LoRA weights in checkpoints ([model_flightdb.py:226-228](part1/model_flightdb.py#L226-L228))

Removed the `lora_A`/`lora_B` key stripping from `state_dict()`. Checkpoints now preserve adapter weights alongside cleaned base weights. Updated `load_state_dict()` to remap cleaned keys back to peft's `base_model.model.` prefix format when loading into a peft-wrapped model.

### 2. Reload best checkpoint with LoRA for final eval ([train.py:857-890](part1/train.py#L857-L890))

Unified the post-training flow: always reload from best checkpoint. For LoRA models, re-apply `get_peft_model()` then load the checkpoint (which now includes adapter weights). This means final eval uses the **best** model, not just the last-epoch model.
