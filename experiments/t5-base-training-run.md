---
name: t5-base-training-run
description: Sequential training run of four T5-base fine-tune configs with watchdog
type: experiment
status: complete
created: 2026-03-11
updated: 2026-03-11
tags:
  - training
  - t5-base
  - part1
  - monitoring
aliases: []
---

# T5-Base Sequential Training Run

Sequential run of four T5-base fine-tune configs via `script/run_base_configs.sh`.
Configs: `T5FineTuneConfig_base`, `T5FineTuneConfig_base2`, `T5FineTuneConfig_base3`, `T5FineTuneConfig_base4`.

---

## Config Summary

| Config | Name | Changes vs base |
|---|---|---|
| `T5FineTuneConfig_base` | `t5_ft_base_v1` | Baseline T5-base, batch=16, beams=2 |
| `T5FineTuneConfig_base2` | `t5_ft_base_v2` | + `freeze_encoder=True` |
| `T5FineTuneConfig_base3` | `t5_ft_base_v3` | + `freeze_embeddings=True` |
| `T5FineTuneConfig_base4` | `t5_ft_base_v4` | `lr=1e-5`, `num_epochs=40` |

---

## Run Log

### Run 1 (configs 1–4, initial attempt)
- **Date**: 2026-03-03 04:22 UTC
- **Script**: `script/run_base_configs.sh`
- **Log file**: `/tmp/t5_base_train.log`
- **Result**: Config 1 completed. Process hung after cleanup (`gc.collect()` / `torch.cuda.empty_cache()` deadlock on futex). Manual kill caused script to abort (exit 143 treated as non-OOM failure).

### Run 2 (configs 2–4, resumed)
- **Date**: 2026-03-03 13:22 UTC
- **Script**: `nohup bash script/run_base_configs.sh --skip T5FineTuneConfig_base`
- **Log file**: `/tmp/t5_base_train_r2.log`
- **Improvements**: Added `--skip` flag, `PYTHONUNBUFFERED=1`, watchdog to kill hung processes after W&B marks run FINISHED + 5 min grace.

---

## Related Issues

- [python command not found](../logs/fix-python-command-not-found.md)
- [HF cache permission denied](../logs/fix-hf-cache-permission.md)
- [Training process hung after completion](../issues/training-process-hung-after-completion.md)
- [Buffered stdout with nohup](../issues/buffered-stdout-nohup.md)

---

## Results

| Config | Best record_f1 | Best record_em | Best sql_em | Epochs | Wall clock |
|---|---|---|---|---|---|
| `t5_ft_base_v1` | **0.5885** | 0.5601 | 0.0150 | 21 (best@17) | 5.1h |
| `t5_ft_base_v2` | _running_ | | | | |
| `t5_ft_base_v3` | _pending_ | | | | |
| `t5_ft_base_v4` | _pending_ | | | | |

### Config 1 epoch-by-epoch (selected)

| Epoch | record_f1 | error_rate | Notes |
|---|---|---|---|
| 0 | 0.1180 | 1.00 | Warmup, all SQL broken |
| 5 | 0.4931 | 0.32 | |
| 8 | 0.5507 | 0.36 | |
| 11 | 0.5702 | 0.37 | |
| 14 | 0.5804 | 0.36 | New best after 2-epoch dip |
| 17 | **0.5885** | 0.38 | Final best |
| 21 | 0.5748 | 0.37 | Early stop (patience=7) |
