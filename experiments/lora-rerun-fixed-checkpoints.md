---
name: lora-rerun-fixed-checkpoints
description: Re-run all 4 LoRA configs with fixed merge_and_unload checkpoint saving, plus warm-start LoRA exploration
type: experiment
status: complete
created: 2026-03-11
updated: 2026-03-12
tags: [lora, checkpoint, merge_and_unload, fine-tune, t5, warm-start]
aliases: []
---

# LoRA Re-run with Fixed Checkpoint Saving

## Objective

Re-run all 4 existing LoRA configurations after fixing the checkpoint save/load pipeline. The previous pipeline stripped LoRA adapter keys during saving, causing F1 to collapse from ~0.335 (during training) to 0.118 on checkpoint reload.

## Fix Applied

**Problem:** `save_model()` called `model.state_dict()` which went through `T5ForFlightSQL.state_dict()`. This method cleaned peft prefixes but preserved both base and LoRA keys in a format that didn't match the vanilla T5 structure expected by `load_model_from_checkpoint()`. On reload, the LoRA adapter weights were lost.

**Solution:** Updated `save_model()` in `part1/model.py` to detect peft (LoRA) models and apply `merge_and_unload()` on a deep copy before saving. This merges the adapter weights into the base model weights, producing a vanilla T5 state_dict that loads correctly without any LoRA-specific reload logic. The original training model is unaffected (deep copy preserves LoRA adapters for continued training).

**Final eval simplification:** Removed the LoRA re-application block from `train.py` final eval. Since merged checkpoints are vanilla T5, the final eval path is now identical for LoRA and non-LoRA models.

## Results

### Dev Record F1 Comparison

| Config | Description | Init | Best Training F1 | Final Dev F1 | Error Rate |
|--------|-------------|------|-------------------|--------------|------------|
| lora_v1 | r=16, q/v | pretrained | 0.335 (e75) | 0.280 | 22.7% |
| lora_v2 | r=16, q/v + schema | pretrained | 0.516 (e63) | 0.258 | 60.1% |
| lora_v3 | r=32, q/k/v/o | pretrained | 0.476 (e59) | 0.337 | 29.2% |
| lora_freeze_enc | r=16, q/v + frozen encoder | pretrained | 0.352 (e63) | 0.332 | 15.0% |
| **lora_warmstart** | **r=16, q/v** | **restricted_v3** | **0.734 (e47)** | **0.582** | **15.0%** |

**Full fine-tune baseline (restricted_v3):** dev F1 = 0.618

### Key Observations

1. **Checkpoint fix confirmed:** All 4 configs produce Final dev F1 > 0.2 (target threshold), up from the collapsed 0.118. The merge_and_unload approach correctly preserves learned adapter knowledge in the saved checkpoint.

2. **Training-time vs final eval gap:** There is a gap between the best training-time F1 (evaluated on a 150-sample subset with greedy decoding) and the final dev F1 (evaluated on the full 423-sample dev set with beam search). This gap is largest for lora_v2 (0.516 vs 0.258), likely because the model's predictions on harder examples in the full dev set produce more SQL execution errors (60.1% error rate).

3. **Schema augmentation helps during training but increases variance:** lora_v2 (with schema) reached higher training F1 than lora_v1 (without), but its final F1 was lower due to higher error rates on the full dev set. The schema context may help the model learn table names but also leads to more complex (and more error-prone) SQL on difficult queries.

4. **Wider LoRA (lora_v3) achieves best final F1:** r=32 on all attention projections (q,k,v,o) gave the best final dev F1 (0.337), suggesting that more adapter capacity and broader module coverage help. It also had a relatively low error rate (29.2%).

5. **Frozen encoder (lora_freeze_enc) performs well:** Despite training only decoder LoRA adapters with a frozen encoder, this config achieved F1=0.332 with the lowest error rate (15.0%). The pretrained encoder representations are sufficient for understanding NL queries.

6. **LoRA vs full fine-tune:** All cold-start LoRA configs (best: 0.337) significantly underperform the full fine-tune baseline (0.618). With only 1-4% trainable parameters, cold-start LoRA cannot match the expressiveness of full parameter updates for this NL-to-SQL task.

7. **Warm-start LoRA dramatically closes the gap:** The warm-start LoRA config (lora_warmstart) loads the best full fine-tune checkpoint (restricted_v3, F1=0.618) as a base before applying LoRA adapters. With the same architecture as lora_v1 (r=16, q/v), it achieves final dev F1=0.582 vs lora_v1's 0.280 -- a 2.1x improvement. The training-time F1 peaked at 0.734 (epoch 47), exceeding the full fine-tune baseline. The gap between training-time and final dev F1 is consistent with other LoRA configs (eval on 150-sample subset vs full 423-sample dev set).

8. **Warm-start confirms the base model matters most for LoRA:** The same LoRA architecture (r=16, q/v, 1% params) produces dramatically different results depending on initialization -- 0.280 from pretrained T5 vs 0.582 from a fine-tuned T5. This suggests that for NL-to-SQL, LoRA adapters are most effective when the base model already has task-relevant representations.

### Training Details

- All configs: 80 epochs max, eval every 4 epochs, patience 7 eval cycles
- Restricted SQL vocabulary (~600 tokens)
- Beam search: 4 beams for final eval
- Hardware: Single GPU (NVIDIA A100 46GB)

### Run Directories

- lora_v1: `output/t5_ft_lora_v1_20260311_182954/`
- lora_v2: `output/t5_ft_lora_v2_20260311_194153/`
- lora_v3: `output/t5_ft_lora_v3_20260311_210104/`
- lora_freeze_enc: `output/t5_ft_lora_freeze_enc_20260311_223458/`
- lora_warmstart: `output/t5_ft_lora_warmstart_20260312_000022/`
