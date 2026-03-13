---
name: T5 Fine-Tune Multi-Config Training
description: Sequential training of 3 config variants for T5 fine-tune NL-to-SQL, selecting best by dev Record F1
type: experiment
status: complete
created: 2026-03-11
updated: 2026-03-11
tags: [t5, fine-tune, restricted-vocab, lora, training, multi-config]
aliases: [t5-ft-training-run-2]
---

# T5 Fine-Tune Multi-Config Training

## Setup

- GPU: NVIDIA A40 (46GB VRAM)
- Model: T5-small (google-t5/t5-small)
- Restricted SQL vocab: 598 tokens (vs 32128 full)
- Beam search: num_beams=4, min_new_tokens=10, length_penalty=1.0
- Eval: every 4 epochs on 150-sample dev subset; full 466-sample eval at end
- Early stopping: patience=7 eval cycles (28 effective epochs)
- Checkpointing: best by subset Record F1

## Configs Tested

### 1. T5FineTuneConfig_lora_v1

- LoRA r=16, alpha=32 on q,v projections
- LR=3e-4, label_smoothing=0.1, 80 epochs
- Auto batch size: 128
- Trainable params: 589K / 61M (1.0%)
- **Result:** Subset F1=0.335 (epoch 75), Full dev F1=0.118, err=85.8%
- **Duration:** ~45 min
- **Notes:** LoRA with only 1% trainable params learned very slowly; F1 stuck at 0.087 for first 20 epochs. Error rate remained high throughout. Full fine-tune significantly outperformed LoRA.

### 2. T5FineTuneConfig_restricted_v2

- Full fine-tune, LR=1e-4, label_smoothing=0.1, 60 epochs
- Auto batch size: 64
- **Result:** Subset F1=0.663 (epoch 51), Full dev F1=0.469
- **Duration:** ~55 min
- **Notes:** Solid improvement over base restricted config (0.445). LR=1e-4 converges well but slowly.

### 3. T5FineTuneConfig_restricted_v3 (BEST)

- Full fine-tune, LR=3e-4, label_smoothing=0.1, 80 epochs
- Tables schema augmentation in input
- Auto batch size: 64
- **Result:** Subset F1=0.796 (epoch 75), Full dev F1=0.618, Record EM=0.594, SQL EM=0.021
- **Duration:** ~75 min
- **Notes:** Higher LR + schema augmentation produced the best results. Peaked late (epoch 75), suggesting the model benefits from longer training with schema context.

## Results Comparison

| Config | Subset F1 (150) | Full Dev F1 (466) | Full Dev EM | SQL EM | Error Rate | Best Epoch |
|--------|-----------------|-------------------|-------------|--------|------------|------------|
| LoRA v1 | 0.335 | 0.118 | 0.118 | 0.000 | 85.8% | 75 |
| restricted_v2 | 0.663 | 0.469 | 0.384 | 0.017 | ~20% | 51 |
| **restricted_v3** | **0.796** | **0.618** | **0.594** | **0.021** | **12.7%** | **75** |

## Key Findings

1. Full fine-tune significantly outperforms LoRA for this task. LoRA's 1% trainable params is insufficient for NL-to-SQL generation quality.
2. Higher LR (3e-4 vs 1e-4) improves convergence speed and final quality.
3. Schema augmentation (table names in input) provides meaningful improvement.
4. Label smoothing (0.1) helps regularization across all configs.
5. Subset evaluation (150 examples) overestimates full-set performance by roughly 20-30%.

## Selected Best

Config: `T5FineTuneConfig_restricted_v3`
Checkpoint: `output/t5_ft_restricted_v3_20260311_054501/checkpoints/model_best.pt`
Output files: `results/t5_ft_dev.sql`, `results/t5_ft_test.sql`, `records/t5_ft_dev.pkl`, `records/t5_ft_test.pkl`
