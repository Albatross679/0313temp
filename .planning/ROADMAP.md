# Roadmap: CSE 5525 Assignment 3 Completion

## Overview

Four phases to get the assignment submission-ready. First, fine-tune T5-base (larger model) on NL-to-SQL to establish a stronger Part 1 baseline. Then run DPO training on the best fine-tuned model to further improve Record F1. Next compute all test metrics and create the ICL sensitivity plot. Finally, complete the qualitative error analysis to finish the report.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: T5-Base Fine-Tuning** - Fine-tune T5-base on NL-to-SQL to establish stronger Part 1 baseline
- [ ] **Phase 2: DPO Training** - Train DPO on best fine-tuned T5 to improve Record F1, finalize test outputs
- [ ] **Phase 3: Metrics and Visualization** - Compute all test set metrics and create ICL sensitivity plot for report
- [ ] **Phase 4: Error Analysis** - Complete qualitative error analysis table in report

## Phase Details

### Phase 1: T5-Base Fine-Tuning
**Goal**: Fine-tuned T5-base model evaluated on dev set, with test outputs generated if it outperforms T5-small
**Depends on**: Nothing (first phase)
**Requirements**: FT-01, FT-02, FT-03
**Success Criteria** (what must be TRUE):
  1. T5-base model is fine-tuned on NL-to-SQL training data using existing Part 1 pipeline
  2. Dev set Record F1 and Query EM are computed and compared against T5-small baseline
  3. If T5-base outperforms T5-small, test SQL and records are generated; best model selected for DPO phase
**Plans:** 1 plan

Plans:
- [ ] 01-01-PLAN.md — Fine-tune T5-base, add batch rank tracking, evaluate vs T5-small, finalize test outputs

### Phase 2: DPO Training
**Goal**: Best Part 1 model is finalized (DPO-improved or baseline retained) with test SQL and records ready for submission
**Depends on**: Phase 1
**Requirements**: DPO-01, DPO-02, DPO-03, DPO-04, DPO-05, DPO-06, DPO-07
**Success Criteria** (what must be TRUE):
  1. Preference dataset exists with chosen/rejected SQL pairs generated from the best fine-tuned T5 model
  2. DPO training completes for both full fine-tune and LoRA variants with dev set evaluation logged
  3. Best DPO variant is identified by comparing dev Record F1 against baseline fine-tune
  4. If DPO improves dev F1, test SQL (`results/t5_ft_test.sql`) and records (`records/t5_ft_test.pkl`) are regenerated from the DPO model; otherwise baseline outputs are retained
**Plans:** 2 plans

Plans:
- [ ] 02-01-PLAN.md — Fix DPO bugs, add LoRA config, generate preference data, run both DPO variants
- [ ] 02-02-PLAN.md — Compare DPO variants against baseline, finalize test outputs for submission

### Phase 3: Metrics and Visualization
**Goal**: All test set metrics are computed and the ICL sensitivity plot is created, with both inserted into the report
**Depends on**: Phase 2
**Requirements**: RPT-01, RPT-02, RPT-03, RPT-04, VIZ-01, VIZ-02
**Success Criteria** (what must be TRUE):
  1. Test set Query EM and Record F1 are computed for all three parts (Part 1, Part 2, Part 3)
  2. All `XX.XX` placeholder values in the report LaTeX tables are replaced with actual scores
  3. ICL sensitivity plot showing Record F1 vs k=0,1,3 exists as a figure in `media/` and is included in the report
**Plans:** 2 plans

Plans:
- [ ] 03-01-PLAN.md — Fill dev metrics in report tables, restructure LLM table with actual experiments, get test scores from Gradescope
- [ ] 03-02-PLAN.md — Create ICL sensitivity plot and insert into report

### Phase 4: Error Analysis
**Goal**: The report contains a complete qualitative error analysis with concrete examples and error pattern statistics
**Depends on**: Phase 3
**Requirements**: ANL-01, ANL-02
**Success Criteria** (what must be TRUE):
  1. Common SQL error patterns are identified across all three parts with concrete query examples
  2. The qualitative error analysis table in the report is filled with specific examples, error categories, and statistics
**Plans:** 1 plan

Plans:
- [ ] 04-01-PLAN.md — Analyze errors across all 3 models, fill qualitative error analysis table in report

### Phase 5: Explore RL algorithm from Minimax model for Part 1 fine-tuning
**Goal:** GRPO and CISPO RL training runs completed on best T5-base checkpoint, with results documented in the report's RL Fine-Tuning subsection regardless of outcome
**Depends on:** Phase 4
**Requirements**: RL-01, RL-02, RL-03, RL-04, RL-05, RL-06, RL-07, RL-08
**Success Criteria** (what must be TRUE):
  1. T5GRPOConfig, GRPO loss, and CISPO loss are implemented following MiniMax-M1 and DeepSeekMath formulations
  2. Complete RL training pipeline runs with group sampling, execution-based reward, and W&B logging
  3. Both GRPO and CISPO experiments complete within 1-2 hour compute budget
  4. Report contains RL Fine-Tuning subsection with methodology, results table, and analysis
**Plans:** 3 plans

Plans:
- [ ] 05-01-PLAN.md — Create RL config dataclass and GRPO/CISPO loss functions
- [ ] 05-02-PLAN.md — Build complete RL training loop with group sampling, execution reward, and evaluation
- [ ] 05-03-PLAN.md — Run GRPO/CISPO experiments and add RL Fine-Tuning subsection to report

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. T5-Base Fine-Tuning | 0/1 | Not started | - |
| 2. DPO Training | 0/2 | Not started | - |
| 3. Metrics and Visualization | 0/2 | Not started | - |
| 4. Error Analysis | 0/1 | Not started | - |
| 5. RL Fine-Tuning | 0/3 | Not started | - |
