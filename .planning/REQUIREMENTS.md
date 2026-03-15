# Requirements: CSE 5525 Assignment 3 Completion

**Defined:** 2026-03-13
**Core Value:** Get the assignment fully submission-ready -- complete report with real metrics, DPO-improved Part 1 model, and all required output files.

## v1 Requirements

### T5-Base Fine-Tuning

- [ ] **FT-01**: Fine-tune T5-base (google-t5/t5-base) on NL→SQL training data using existing Part 1 pipeline
- [ ] **FT-02**: Evaluate T5-base fine-tuned model on dev set (Record F1, Query EM) and compare against T5-small baseline
- [ ] **FT-03**: If T5-base outperforms T5-small, generate test SQL and records for submission

### DPO Training

- [ ] **DPO-01**: Generate preference pairs by sampling multiple SQL outputs from best fine-tuned T5 per query
- [ ] **DPO-02**: Rank preference pairs by SQL execution correctness against ground truth
- [ ] **DPO-03**: Implement DPO training loop for T5 (full fine-tune)
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

- [x] **ANL-01**: Identify common SQL error patterns across all 3 parts
- [x] **ANL-02**: Fill qualitative error analysis table with concrete examples and statistics

### RL Fine-Tuning (Phase 5)

- [x] **RL-01**: Create T5GRPOConfig dataclass with RL-specific fields (algorithm, group_size, epsilon, reward_type, stability params)
- [x] **RL-02**: Implement GRPO loss function with PPO-style clipping and diagnostics
- [x] **RL-03**: Implement CISPO loss function with detached IS weight clipping (per-token and sequence-level)
- [x] **RL-04**: Implement group sampling with constrained decoding (G=8 completions per query)
- [x] **RL-05**: Implement graded execution reward (+1.0/+0.5/-0.5/-1.0) via in-memory SQLite
- [x] **RL-06**: Build complete RL training loop with W&B logging, early stopping, gradient spike detection, and LoRA
- [x] **RL-07**: Run GRPO and CISPO experiments within 1-2 hour compute budget
- [x] **RL-08**: Add RL Fine-Tuning subsection to report with methodology, results, and analysis

## v2 Requirements

None -- this is a one-shot assignment submission.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Retraining Part 2 (T5 from scratch) | Already has satisfactory test outputs |
| Retraining Part 3 (LLM prompting) | Already has satisfactory test outputs |
| Hyperparameter sweep for DPO | Time constraint -- run best-guess config |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FT-01 | Phase 1 | Pending |
| FT-02 | Phase 1 | Pending |
| FT-03 | Phase 1 | Pending |
| DPO-01 | Phase 2 | Pending |
| DPO-02 | Phase 2 | Pending |
| DPO-03 | Phase 2 | Pending |
| DPO-04 | Phase 2 | Pending |
| DPO-05 | Phase 2 | Pending |
| DPO-06 | Phase 2 | Pending |
| DPO-07 | Phase 2 | Pending |
| RPT-01 | Phase 3 | Pending |
| RPT-02 | Phase 3 | Pending |
| RPT-03 | Phase 3 | Pending |
| RPT-04 | Phase 3 | Pending |
| VIZ-01 | Phase 3 | Pending |
| VIZ-02 | Phase 3 | Pending |
| ANL-01 | Phase 4 | Complete |
| ANL-02 | Phase 4 | Complete |
| RL-01 | Phase 5 | Complete |
| RL-02 | Phase 5 | Complete |
| RL-03 | Phase 5 | Complete |
| RL-04 | Phase 5 | Complete |
| RL-05 | Phase 5 | Complete |
| RL-06 | Phase 5 | Complete |
| RL-07 | Phase 5 | Complete |
| RL-08 | Phase 5 | Complete |

**Coverage:**
- v1 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-14 after Phase 5 RL Fine-Tuning requirements added*
