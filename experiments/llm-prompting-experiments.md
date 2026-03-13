---
name: LLM Prompting Experiments
description: Systematic evaluation of Gemma 2B on NL-to-SQL via k-shot prompting with random and BM25 example selection, plus ablation study
type: experiment
status: complete
created: 2026-03-12
updated: 2026-03-12
tags: [gemma, prompting, bm25, ablation, k-shot, sql]
aliases: [llm-experiments, part3-experiments]
---

# LLM Prompting Experiments

## Overview

Evaluated Gemma 2B (`google/gemma-1.1-2b-it`) on the NL-to-SQL flight database task using zero-shot, 1-shot, and 3-shot prompting with random and BM25 example selection strategies, plus a 5-condition ablation study.

## K-Shot Results (Dev Set)

| Config | Record F1 | Record EM | SQL EM | Error Rate | Duration |
|--------|-----------|-----------|--------|------------|----------|
| k=0 (random) | 0.1260 | 0.1223 | 0.0 | ~93% | ~18min |
| k=1 (random) | 0.1260 | 0.1202 | 0.0 | 92.70% | 1010s |
| k=3 (random) | 0.1196 | 0.1180 | 0.0 | 98.50% | 1010s |

**Finding:** k-shot with random examples provides no improvement over zero-shot. In fact, k=3 random is slightly worse due to longer prompts confusing the model and nearly all outputs being SQL errors.

## BM25 vs Random at k=3 (Dev Set)

| Strategy | Record F1 | Record EM | SQL EM | Error Rate | Duration |
|----------|-----------|-----------|--------|------------|----------|
| Random k=3 | 0.1196 | 0.1180 | 0.0 | 98.50% | 1010s |
| **BM25 k=3** | **0.1735** | **0.1652** | 0.0 | 86.27% | 1044s |

**Finding:** BM25 per-query example selection significantly outperforms random selection (F1 0.174 vs 0.120, +45% relative improvement). BM25 selects training examples most similar to each query, giving the model more relevant patterns. Error rate also drops from 98.5% to 86.3%.

**Decision: BM25 k=3 is the best config for final test predictions.**

## Ablation Study (Dev Set)

5 conditions evaluated to understand the contribution of each prompt component:

| # | Condition | Schema | Instructions | Examples (k) | Record F1 | Error Rate |
|---|-----------|--------|-------------|-------------|-----------|------------|
| 1 | Full prompt (BM25 k=3) | Yes | Yes | 3 | **0.1735** | 86.27% |
| 2 | No schema | No | Yes | 3 | 0.1180 | 99.14% |
| 3 | No instructions | Yes | No | 3 | 0.1180 | 100.00% |
| 4 | No examples (0-shot) | Yes | Yes | 0 | 0.1260 | ~93% |
| 5 | Schema only | Yes | No | 0 | 0.1137 | 69.96% |

### Key Findings

1. **Schema is critical for reducing errors**: Without schema, 99.14% of outputs are SQL errors (vs 86.27% with schema). The model needs table/column names.

2. **Instructions are essential for SQL generation**: Without explicit SQL task instructions, 100% of outputs are invalid SQL. The model needs to be told to generate SQL.

3. **Schema-only has lowest error rate but lowest F1**: With just schema and no instructions, only 69.96% errors, but F1 is worst (0.114). The model generates more syntactically valid SQL but without task context produces wrong queries.

4. **BM25 examples provide the biggest marginal improvement**: Going from no examples (F1=0.126) to BM25 k=3 (F1=0.174) is the largest single improvement (+38% relative).

5. **All components together yield best performance**: Full prompt with schema + instructions + BM25 examples achieves the highest F1 (0.174).

## Final Submission

Best config (BM25 k=3 with full prompt) used for final test predictions:
- `results/llm_test.sql` - 432 SQL predictions
- `records/llm_test.pkl` - 432 record sets
- `results/llm_dev.sql` - 466 SQL predictions (dev)
- `records/llm_dev.pkl` - 466 record sets (dev)
- Dev Record F1: 0.1735

## Model Observations

- Gemma 2B generates significant amounts of non-SQL text (explanations, markdown, etc.) even with explicit SQL-only instructions
- SQL extraction regex handles most cases but 86-99% of outputs still produce SQL execution errors
- The 2B model struggles with the flight database schema complexity (25 tables)
- BM25 example selection helps by providing relevant schema usage patterns

## Config Details

- Model: `google/gemma-1.1-2b-it` (2B parameters, bf16)
- Generation: `do_sample=False`, `max_new_tokens=256`
- BM25: whitespace tokenization, per-query top-k selection from 4225 training examples
- Prompt template: Gemma chat format with `<start_of_turn>user` / `<start_of_turn>model` markers
- SQL extraction: 5-priority regex (sql code block > generic block > SELECT...;  > SELECT line > fallback)
- Seed: 42
