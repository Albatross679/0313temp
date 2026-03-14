---
name: DPO final eval F1 significantly lower than in-training best
description: Checkpoint reload for final evaluation produces lower F1 than in-training eval due to beam search mismatch and potential LoRA merge issues
type: issue
status: investigating
severity: high
subtype: evaluation
created: 2026-03-14
updated: 2026-03-14
tags: [dpo, evaluation, beam-search, lora, checkpoint]
aliases: [dpo-eval-mismatch, dpo-checkpoint-f1-drop]
---

## Summary

Both DPO sweep trials showed significant F1 drops when reloading the "best" checkpoint for final evaluation:

| Trial | Architecture | In-Training Best F1 | Final Eval F1 | Drop |
|-------|-------------|---------------------|---------------|------|
| 1 | full-FT | 0.8482 | 0.8242 | -3.0% |
| 2 | LoRA qkvo | 0.8596 | 0.7575 | -12.1% |

## Root Cause 1: Beam Search Mismatch (both trials)

In-training eval uses `eval_num_beams=1` (greedy search) via `eval_epoch_gpu(is_final=False)`.
Final eval uses `num_beams=4` (full beam search) via `eval_epoch(is_final=True)`.

In `part1/train.py:eval_epoch_gpu()`:
```python
if is_final:
    num_beams = cfg.num_beams          # 4 for DPO config
else:
    num_beams = cfg.eval_num_beams     # 1 (greedy, inherited from T5FineTuneConfig)
```

The model was checkpointed based on greedy-search F1 scores, but final eval uses beam search which produces different (often more conservative) predictions. This explains the consistent drop across both trials.

## Root Cause 2: LoRA Merge on Save (trial 2 only)

Trial 2's 12.1% drop is much larger than trial 1's 3.0%, suggesting an additional LoRA-specific issue.

`part1/model.py:save_model()` calls `merge_and_unload()` on a deep copy of the peft model:
```python
inner_copy = copy.deepcopy(inner)
merged = inner_copy.merge_and_unload()
torch.save(merged.state_dict(), path)
```

Then `main_with_config()` reloads into a plain T5 (no LoRA wrapper):
```python
final_base = load_model_from_checkpoint(ckpt_dir, ...)
final_model = T5ForFlightSQL(final_base, sql_vocab)
```

While the merge-and-save logic looks correct in principle, the 12% drop for a LoRA model that barely learned anything (reward accuracy only reached 53.9%) is suspicious. The merged weights should be nearly identical to the base model, yet F1 dropped from 0.8596 to 0.7575.

## Impact

- Saved "best" checkpoints produce significantly worse results than reported during training
- W&B sweep comparison is unreliable — in-training F1 and final F1 measure different things
- LoRA checkpoints may be corrupted by the merge-and-save path

## Recommended Fixes

1. **Align beam search:** Set `eval_num_beams = num_beams` in DPO config so in-training eval matches final eval
2. **Investigate LoRA merge:** Compare parameter values before/after merge_and_unload() to verify correctness
3. **Consider saving without merge for LoRA:** Keep peft format checkpoints and reload with LoRA wrapper
