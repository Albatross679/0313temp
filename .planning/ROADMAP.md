# Roadmap: CSE 5525 Assignment 3 Completion

## Overview

Three phases to get the assignment submission-ready. First, run DPO training on the Part 1 fine-tuned T5 model and finalize test outputs. Then compute all test metrics across all three parts and create the ICL sensitivity plot. Finally, complete the qualitative error analysis to finish the report.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: DPO Training** - Train DPO on Part 1 fine-tuned T5 to improve Record F1, finalize test outputs
- [ ] **Phase 2: Metrics and Visualization** - Compute all test set metrics and create ICL sensitivity plot for report
- [ ] **Phase 3: Error Analysis** - Complete qualitative error analysis table in report

## Phase Details

### Phase 1: DPO Training
**Goal**: Part 1 model is finalized (DPO-improved or baseline retained) with test SQL and records ready for submission
**Depends on**: Nothing (first phase)
**Requirements**: DPO-01, DPO-02, DPO-03, DPO-04, DPO-05, DPO-06, DPO-07
**Success Criteria** (what must be TRUE):
  1. Preference dataset exists with chosen/rejected SQL pairs generated from the fine-tuned T5 model
  2. DPO training completes for both full fine-tune and LoRA variants with dev set evaluation logged
  3. Best DPO variant is identified by comparing dev Record F1 against baseline fine-tune
  4. If DPO improves dev F1, test SQL (`results/t5_ft_test.sql`) and records (`records/t5_ft_test.pkl`) are regenerated from the DPO model; otherwise baseline outputs are retained
**Plans**: TBD

Plans:
- [ ] 01-01: Generate preference data and implement DPO training
- [ ] 01-02: Evaluate DPO variants and finalize Part 1 outputs

### Phase 2: Metrics and Visualization
**Goal**: All test set metrics are computed and the ICL sensitivity plot is created, with both inserted into the report
**Depends on**: Phase 1
**Requirements**: RPT-01, RPT-02, RPT-03, RPT-04, VIZ-01, VIZ-02
**Success Criteria** (what must be TRUE):
  1. Test set Query EM and Record F1 are computed for all three parts (Part 1, Part 2, Part 3)
  2. All `XX.XX` placeholder values in the report LaTeX tables are replaced with actual scores
  3. ICL sensitivity plot showing Record F1 vs k=0,1,3 exists as a figure in `media/` and is included in the report
**Plans**: TBD

Plans:
- [ ] 02-01: Compute test metrics for all parts and fill report tables
- [ ] 02-02: Create ICL sensitivity plot and insert into report

### Phase 3: Error Analysis
**Goal**: The report contains a complete qualitative error analysis with concrete examples and error pattern statistics
**Depends on**: Phase 2
**Requirements**: ANL-01, ANL-02
**Success Criteria** (what must be TRUE):
  1. Common SQL error patterns are identified across all three parts with concrete query examples
  2. The qualitative error analysis table in the report is filled with specific examples, error categories, and statistics
**Plans**: TBD

Plans:
- [ ] 03-01: Analyze errors across all parts and complete error analysis table

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. DPO Training | 0/2 | Not started | - |
| 2. Metrics and Visualization | 0/2 | Not started | - |
| 3. Error Analysis | 0/1 | Not started | - |
