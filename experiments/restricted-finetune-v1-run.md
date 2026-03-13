---
name: restricted-finetune-v1-run
description: T5FineTuneConfig_restricted run — best F1=0.4723 with date hallucination issues
type: experiment
status: complete
created: 2026-03-11
updated: 2026-03-11
tags:
  - training
  - restricted-vocab
  - part1
aliases: []
---

# Restricted Vocab Fine-Tune v1: T5FineTuneConfig_restricted

| Field | Value |
|---|---|
| **Config** | `T5FineTuneConfig_restricted` (part1) |
| **Best F1** | 0.4723 (epoch 27) |
| **Record EM** | 0.3820 |
| **SQL EM** | 0.0021 |
| **Error Rate** | 22.1% |
| **Status** | FINISHED |

## Hyperparameters

LR: 3e-5, 30 epochs, patience 7, cosine scheduler, beam=4, max_new_tokens=512.
Fine-tune pretrained T5-small with restricted SQL output vocabulary (~600 tokens).

## Training Curve

Loss decreased smoothly (4.82 -> 0.14). F1 grew steadily from 0.12 (ep 0)
to 0.47 (ep 27) but plateaued in the low-to-mid 0.47s for the last 5 epochs.

**F1 trajectory:** ep 20: 0.4547 -> ep 23: 0.4666 -> ep 25: 0.4707 -> ep 27: 0.4723 -> ep 29: 0.4702

## Root Cause Analysis: Why F1 = 0.47 is Lower Than Expected

Three systematic issues account for the majority of errors:

### 1. Date Value Hallucination (93% of date queries wrong)

The model memorizes a small set of common training dates (especially month=4, day=23)
and outputs them regardless of the actual query context. Of 100 dev queries requiring
date predicates, **93 have wrong dates**.

The NL input says things like "tomorrow" or "thursday" but the model must learn to map
these to specific `(year, month_number, day_number)` triples that appear in the training
data. With fine-tuning at LR=3e-5, the pretrained T5 language priors make it harder to
learn this arbitrary mapping — the model defaults to the most common training dates.

**Most predicted dates:** (4,23) 28x, (4,26) 11x, (3,23) 7x
**Gold distribution:** (3,22) 16x, (4,23) 15x, (5,24) 14x — much more spread out.

### 2. Incomplete SQL Generation (46 queries / 9.9%)

46 predictions are truncated mid-query, producing "incomplete input" SQLite errors.
These have mean token length ~243 (well under the 512 max_new_tokens), suggesting
the model generates EOS too early or the constrained beam search gets stuck.

Possible cause: the `prefix_allowed_tokens_fn` constrains decoding to only SQL
vocabulary tokens. With a fine-tuned model whose logit distribution is shaped by
pretrained English priors, the constrained decoding may conflict more severely with
the model's preferred continuations, causing premature EOS.

### 3. Missing WHERE Conditions (79 queries return >3x gold records)

The model drops important filtering conditions like time constraints, stop conditions,
airline filters, and fare subqueries. This returns too many records, tanking precision
and F1. **325 predictions are missing at least one gold condition.**
