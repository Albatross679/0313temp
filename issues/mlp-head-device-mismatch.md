---
name: MLP head device mismatch
description: T5ForFlightSQLWithMLP layers created on CPU after base model moved to GPU
type: issue
status: resolved
severity: high
subtype: model
created: 2026-03-11
updated: 2026-03-11
tags: [mlp, device, cuda, training]
aliases: []
---

## Error

```
RuntimeError: Expected all tensors to be on the same device, but got weight is on cpu,
different from other tensors on cuda:0
(when checking argument in method wrapper_CUDA__native_layer_norm)
```

At line: `hidden = hidden + self.mlp(self.mlp_norm(hidden))`

## Root Cause

`T5ForFlightSQLWithMLP.__init__()` creates `mlp_norm` (LayerNorm) and `mlp` (Sequential)
as new nn.Module layers. These default to CPU. The base T5 model was already moved to GPU
via `initialize_model(..., device=device)` before wrapping, so the MLP layers remained on
CPU while decoder hidden states were on CUDA.

## Affected Configs

- `T5FineTuneConfig_mlp_v1` — crashed immediately at first forward pass
- `T5FineTuneConfig_mlp_v2` — same crash

## Fix

Added `model = model.to(device)` after creating `T5ForFlightSQLWithMLP` in both:
1. Initial model creation (line ~761 in `part1/train.py`)
2. Checkpoint loading path (line ~872 in `part1/train.py`)

## Verification

MLP configs will be re-run after current training batch completes.
