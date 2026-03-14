---
name: peft-not-installed-sweep-crash
description: W&B sweep LoRA trials crash with ModuleNotFoundError for peft package
type: issue
status: resolved
severity: medium
subtype: compatibility
created: 2026-03-14
updated: 2026-03-14
tags: [sweep, lora, peft, dependency]
aliases: [peft-missing]
---

# peft Not Installed — LoRA Sweep Trials Crash

## Symptom

Sweep trial 2 (architecture: `lora_qkvo_r32`) crashed immediately after loading model weights:

```
File "/home/turncloak/0313temp/part1/train.py", line 826, in main_with_config
    from peft import LoraConfig, get_peft_model, TaskType
ModuleNotFoundError: No module named 'peft'
```

## Impact

All LoRA architecture variants in the sweep (`lora_qv_r16`, `lora_qv_r32`, `lora_qkvo_r16`, `lora_qkvo_r32`) would crash on selection. The sweep agent recovers and moves to the next trial, but LoRA configs are never explored.

## Root Cause

The `peft` library was not listed in `requirements.txt` or installed in the environment, but `part1/train.py` conditionally imports it when `cfg.use_lora=True`. Since the T5-small runs used `full_ft` only, the missing dependency was never triggered until the sweep selected a LoRA architecture.

## Fix

```bash
pip3 install peft
```

Installed during sweep runtime. Subsequent LoRA trials should work.

## Prevention

Add `peft` to `requirements.txt` so it's installed with the project dependencies.
