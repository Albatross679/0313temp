# CSE 5525 Assignment 3: Finish & Submit

## What This Is

Completing the remaining deliverables for CSE 5525 Assignment 3 (NL-to-SQL). All three parts (T5 fine-tune, T5 from scratch, LLM prompting) have trained models and generated test outputs. What remains is DPO training on the Part 1 model to improve F1, filling in report metrics, creating the ICL sensitivity plot, and writing the qualitative error analysis.

## Core Value

Get the assignment fully submission-ready — complete report with real metrics, DPO-improved Part 1 model, and all required output files.

## Requirements

### Validated

- ✓ Part 1: T5 fine-tune training pipeline — existing
- ✓ Part 1: Test SQL and records generated (`results/t5_ft_test.sql`, `records/t5_ft_test.pkl`) — existing
- ✓ Part 2: T5 from-scratch training pipeline — existing
- ✓ Part 2: Test SQL and records generated (`results/t5_scr_test.sql`, `records/t5_scr_test.pkl`) — existing
- ✓ Part 3: LLM prompting pipeline with k-shot variants — existing
- ✓ Part 3: Test SQL and records generated (`results/llm_test.sql`, `records/llm_test.pkl`) — existing
- ✓ Shared infrastructure (config system, W&B tracking, GPU lock) — existing
- ✓ Report LaTeX structure with tables and sections — existing

### Active

- [ ] DPO training on Part 1 fine-tuned T5 to improve Record F1
- [ ] Compute and fill test set metrics in report (Query EM, Record F1 for all parts)
- [ ] Create ICL sensitivity plot (F1 vs k values for Part 3)
- [ ] Complete qualitative error analysis table in report
- [ ] Regenerate Part 1 test outputs if DPO improves the model

### Out of Scope

- Retraining Part 2 (from-scratch) — already has test outputs
- Retraining Part 3 (LLM prompting) — already has test outputs
- New model architectures beyond DPO on existing Part 1 checkpoint

## Context

- All three parts fully implemented with extensive experiment history
- Part 1 best model: `output/t5_ft_restricted_v3/`
- Part 2 best model: `output/t5_scr_restricted/`
- Part 3 has multiple k-shot variants (k=0,1,3) and BM25 retrieval experiments
- Report is ~85% complete — tables exist but test metrics are placeholder `XX.XX`
- DPO preference data strategy TBD — likely sample multiple SQL outputs from fine-tuned model and rank by execution correctness
- Due this week (by ~2026-03-14/15)

## Constraints

- **Hardware**: Single GPU, GPU lock serialization required
- **Model**: T5-small architecture (fixed by assignment)
- **Files**: Cannot rename/move graded files (`evaluate.py`, `train_t5.py`, etc.)
- **Data**: `data/` directory is read-only
- **Timeline**: Due this week

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| DPO on Part 1 fine-tuned model | Improve Record F1 beyond standard fine-tuning | — Pending |
| Preference data from model sampling | Generate chosen/rejected pairs by sampling and checking SQL correctness | — Pending |

---
*Last updated: 2026-03-13 after initialization*
