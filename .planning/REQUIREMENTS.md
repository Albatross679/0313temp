# Requirements: CSE 5525 Assignment 3 Completion

**Defined:** 2026-03-13
**Core Value:** Get the assignment fully submission-ready — complete report with real metrics, DPO-improved Part 1 model, and all required output files.

## v1 Requirements

### DPO Training

- [ ] **DPO-01**: Generate preference pairs by sampling multiple SQL outputs from fine-tuned T5 per query
- [ ] **DPO-02**: Rank preference pairs by SQL execution correctness against ground truth
- [ ] **DPO-03**: Implement DPO training loop for T5-small (full fine-tune)
- [ ] **DPO-04**: Implement DPO training with LoRA
- [ ] **DPO-05**: Compare DPO with and without LoRA on dev set metrics
- [ ] **DPO-06**: Evaluate best DPO model on dev set (Record F1, Query EM)
- [ ] **DPO-07**: If DPO improves dev F1, regenerate test SQL and records

### Report Metrics

- [ ] **RPT-01**: Compute test set Query EM and Record F1 for Part 1 (T5 fine-tune)
- [ ] **RPT-02**: Compute test set Query EM and Record F1 for Part 2 (T5 from scratch)
- [ ] **RPT-03**: Compute test set Query EM and Record F1 for Part 3 (LLM prompting)
- [ ] **RPT-04**: Fill all XX.XX placeholders in report tables with actual scores

### Report Visualization

- [ ] **VIZ-01**: Create ICL sensitivity plot (Record F1 vs k=0,1,3)
- [ ] **VIZ-02**: Insert plot into report LaTeX

### Report Analysis

- [ ] **ANL-01**: Identify common SQL error patterns across all 3 parts
- [ ] **ANL-02**: Fill qualitative error analysis table with concrete examples and statistics

## v2 Requirements

None — this is a one-shot assignment submission.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Retraining Part 2 (T5 from scratch) | Already has satisfactory test outputs |
| Retraining Part 3 (LLM prompting) | Already has satisfactory test outputs |
| New model architectures beyond DPO | Assignment scope is fixed |
| Hyperparameter sweep for DPO | Time constraint — run best-guess config |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DPO-01 | — | Pending |
| DPO-02 | — | Pending |
| DPO-03 | — | Pending |
| DPO-04 | — | Pending |
| DPO-05 | — | Pending |
| DPO-06 | — | Pending |
| DPO-07 | — | Pending |
| RPT-01 | — | Pending |
| RPT-02 | — | Pending |
| RPT-03 | — | Pending |
| RPT-04 | — | Pending |
| VIZ-01 | — | Pending |
| VIZ-02 | — | Pending |
| ANL-01 | — | Pending |
| ANL-02 | — | Pending |

**Coverage:**
- v1 requirements: 15 total
- Mapped to phases: 0
- Unmapped: 15 ⚠️

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 after initial definition*
