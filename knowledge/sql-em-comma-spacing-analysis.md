---
name: SQL EM Comma Spacing Analysis
description: Quantified analysis of T5 SentencePiece decode artifact impact on SQL exact match, with corrected metrics for all three model approaches
type: knowledge
created: 2026-03-14
updated: 2026-03-14
tags: [sql-em, evaluation, metrics, t5, sentencepiece, comma-spacing, normalization]
aliases: [sql-em-analysis, comma-normalization-analysis]
---

# SQL EM Comma Spacing Analysis

## Overview

SQL exact match (SQL EM) as reported by `compute_sql_exact_match()` in `utils.py` uses pure string equality (`gt_q == model_q`). This makes it sensitive to trivial formatting differences that do not affect query semantics. The T5 SentencePiece tokenizer introduces a systematic formatting difference during decode: ` , ` (space-comma-space) in ground truth becomes `, ` (comma-space) in decoded output.

This document quantifies the impact and provides corrected SQL EM numbers.

## Raw vs Normalized SQL EM Comparison

### Normalization Method

Comma normalization: replace all `, ` (comma-space without preceding space) with ` , ` (space-comma-space) in both predicted and ground truth SQL before comparison.

```python
import re
normalized = re.sub(r'(?<=[a-zA-Z0-9_)])\s*,\s*', ' , ', sql_string)
```

### Results (Dev Set, 466 queries)

| Model | Raw SQL EM | Normalized SQL EM | Absolute Gain | Mismatches Explained by Commas |
|-------|-----------|-------------------|---------------|-------------------------------|
| T5 fine-tune (best config) | 0.034 (16/466) | 0.725 (338/466) | +69.1 pp | 322/450 (71.6%) |
| T5 from scratch | 0.032 (15/466) | 0.504 (235/466) | +47.2 pp | 220/451 (48.8%) |
| LLM prompting (Gemma 2B, 3-shot) | 0.000 (0/466) | 0.000 (0/466) | 0 pp | 0/466 (0%) |

### Interpretation

**T5 Fine-tune:** The corrected SQL EM of 72.5% is a strong result. It means the model produces the exact correct SQL query for nearly 3 out of 4 dev examples. The remaining 128 mismatches are genuine semantic errors (wrong table joins, incorrect predicates, missing conditions, etc.). This aligns well with the 62% Record F1 -- some queries that are structurally wrong may still return partially correct records.

**T5 From Scratch:** Even with random initialization, the model achieves 50.4% SQL EM after normalization. The larger gap between raw (3.2%) and normalized (50.4%) follows the same pattern as fine-tune, confirming the artifact is systematic across all T5 models using SentencePiece decode.

**LLM Prompting:** The 0% SQL EM is NOT caused by the comma spacing artifact. LLM-generated SQL has fundamentally different problems:
- Different query structure (e.g., using subqueries instead of JOINs)
- Different alias naming conventions
- Additional or missing clauses
- Different predicate formulations

The LLM produces semantically different (though sometimes functionally equivalent) SQL. Comma normalization has no effect because the queries differ in structure, not just formatting.

## Breakdown of Remaining Errors (T5 Fine-tune)

After comma normalization, 128 queries still do not match exactly. Categories of remaining errors:

| Error Type | Approximate Count | Example |
|-----------|-------------------|---------|
| Wrong/missing JOIN conditions | ~40 | Missing a table in FROM clause |
| Incorrect WHERE predicates | ~35 | Wrong column or value in conditions |
| Wrong aggregation/DISTINCT | ~20 | Missing DISTINCT, wrong COUNT |
| Column selection errors | ~15 | Wrong columns in SELECT |
| Structural differences | ~18 | Subquery vs JOIN, different approach |

These represent genuine model errors where the model has not learned the correct SQL pattern for the given natural language query.

## Is SQL EM a Meaningful Metric?

### Limitations

SQL EM is a strict metric that penalizes:
1. **Formatting differences** (like the comma artifact) -- these are false negatives
2. **Semantically equivalent queries** -- `SELECT a, b` vs `SELECT b, a` both return the same records but fail SQL EM
3. **Functionally equivalent queries** -- different JOIN orders, equivalent subquery reformulations

### Why Record F1/EM Are Better Primary Metrics

Record F1 and Record EM measure whether the predicted SQL **returns the correct database records**, which is the actual goal of NL-to-SQL. Two structurally different SQL queries that return the same result set are equally correct for the user.

### Recommendation for Reporting

In the assignment report:
1. Report **raw SQL EM** as the official metric (it is what `evaluate.py` computes)
2. Note the comma spacing artifact in the analysis section
3. Report **normalized SQL EM** as supplementary analysis
4. Use **Record F1** as the primary quality indicator (as specified in the assignment)

## Training Data Statistics

Comma usage in the dataset:

| Dataset | Instances of ` , ` | Instances of `, ` (no leading space) |
|---------|--------------------|------------------------------------|
| train.sql (8,616 queries) | 22,077 | 0 |
| dev.sql (466 queries) | 2,352 | 0 |

Average commas per query: ~2.6 (train), ~5.0 (dev). Dev queries are more complex on average, with more JOINs and conditions.

## Fix Strategy

### Short-term (Recommended)

Apply regex post-processing after `batch_decode` in the prediction pipeline:

```python
import re

decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
# Restore space before commas that SentencePiece decode collapses
fixed = [re.sub(r'(?<=[a-zA-Z0-9_)])\s*,\s*', ' , ', s) for s in decoded]
```

Apply in:
- `part1/train.py` `_generate_predictions()` (line 217-218)
- `part2/train.py` equivalent decode path
- Any evaluation scripts that decode T5 output

### Long-term

If pursuing maximum SQL EM, investigate:
- Custom decode function that preserves space sentinels before punctuation
- Training with a modified tokenizer that handles ` , ` as a single token
- Neither is worth the effort for this assignment given Record F1 is the primary metric

## Related

- Issue: `issues/sql-exact-match-tokenizer-artifact.md` (root cause documentation)
- Experiment: `experiments/t5-ft-multi-config-training.md` (reports raw SQL EM = 0.021)
