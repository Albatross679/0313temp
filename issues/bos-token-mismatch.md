---
name: bos-token-mismatch
description: T5 decoder received wrong start token during inference, dropping SELECT keyword
type: issue
status: resolved
severity: critical
subtype: model
created: 2026-03-11
updated: 2026-03-11
tags:
  - part1
  - part2
  - t5
  - bug
  - inference
aliases: []
---

# BOS Token Mismatch: Training vs Inference

## Summary

The T5 decoder received a different start-of-sequence token during inference than
during training, causing predictions to consistently **miss the `SELECT` keyword**
— the first token of every SQL query.

## Affected Code

| File | Role |
|---|---|
| `part1/data.py:16,83` | Defines `_BOS_ID` and prepends it during training |
| `part1/train.py:45` | `model.generate()` call (Part 1 fine-tune) |
| `part2/train.py:57` | `model.generate()` call (Part 2 from-scratch) |

## Root Cause

### Training (teacher forcing)

The collate function in `part1/data.py` constructs decoder inputs by prepending
`<extra_id_0>` (token ID **32099**) as the BOS token:

```python
_BOS_ID = _TOKENIZER.convert_tokens_to_ids("<extra_id_0>")  # 32099

bos_column = torch.full((encoder_ids.size(0), 1), _BOS_ID, dtype=torch.long)
decoder_inputs = torch.cat([bos_column, decoder_targets[:, :-1]], dim=1)
```

The model learns: *"when the first token is 32099, predict `SELECT` next."*

### Inference (autoregressive generation)

`model.generate()` was called **without** specifying `decoder_start_token_id`.
HuggingFace T5 defaults to `config.decoder_start_token_id = 0` (the **pad token**).

The model had never seen token 0 as a start token during training, so the learned
conditional distribution `P(token | start=0)` was essentially random for the first
position. Since `SELECT` is always the first real token in every SQL query, it was
consistently dropped.

## Symptom

Predictions contained recognizable SQL fragments (table names, `WHERE`, `JOIN`) but
started mid-query, e.g.:

```
_1, airport_2 WHERE flight.from_airport = airport_1.airport_code ...
```

instead of:

```
SELECT ... FROM flight, airport AS airport_1, airport AS airport_2 WHERE ...
```

This caused 100% SQL execution error rate despite the model learning meaningful
structure.

## Impact by Model

| Model | Severity | Explanation |
|---|---|---|
| Part 2 (from-scratch) | **High** | All token distributions learned from data; entirely dependent on correct BOS |
| Part 1 (fine-tune) | **Low** | Pretrained weights provide robust priors; less sensitive to start token |

## Fix

Added `decoder_start_token_id=32099` to `model.generate()` calls so inference
starts from the same `<extra_id_0>` token used during training.

**part1/train.py** — `_generate_predictions()`:

```python
outputs = model.generate(
    input_ids=encoder_input,
    attention_mask=encoder_mask,
    max_new_tokens=max_new_tokens,
    num_beams=num_beams,
    decoder_start_token_id=32099,  # <extra_id_0>, matches training BOS
)
```

**part2/train.py** — `_generate_predictions()`:

```python
gen_kwargs = dict(
    max_new_tokens=max_new_tokens,
    num_beams=num_beams,
    decoder_start_token_id=32099,  # <extra_id_0>, matches training BOS
)
```

### Alternative Fix (not chosen)

Change training to use pad token (ID 0) as BOS in the collate function, aligning
with T5's default `decoder_start_token_id`. This would require retraining all
models, so the inference-side fix was preferred.
