---
name: Root stubs and LoRA integration
description: Created root graded stubs delegating to part1/, data validation script, and fixed LoRA checkpoint compatibility
type: log
status: complete
subtype: feature
created: 2026-03-11
updated: 2026-03-11
tags: [t5, lora, peft, data-validation, root-stubs]
aliases: [01-01-stubs]
---

# Root Stubs and LoRA Integration

## Changes

### Root Graded Stubs
- `load_data.py`: Re-exports T5Dataset, collate functions, get_dataloader, load_t5_data, PAD_IDX from part1.data
- `train_t5.py`: Minimal entry point delegating to part1.train.main()
- `t5_utils.py`: Filled initialize_model, save_model, load_model_from_checkpoint stubs to delegate to part1.model

### Data Validation Script
- `script/validate_data.py`: Standalone validation checking dataset sizes (4225/466/432), tokenization, BOS token (32099), restricted vocab coverage (0 missing)

### LoRA Checkpoint Fix
- `part1/model_flightdb.py`: T5ForFlightSQL.state_dict() now strips `base_model.model.` prefix and drops LoRA adapter weights when saving, ensuring checkpoints are loadable by vanilla T5ForConditionalGeneration

## Verification
- All imports pass
- Data validation passes all 4 checks
- LoRA save/load cycle works
- MLP state_dict includes 6 MLP keys
- Non-LoRA path unbroken
