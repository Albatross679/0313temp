---
phase: quick-1
plan: 1
subsystem: evaluation
tags: [sql-em, t5, sentencepiece, tokenizer, decode-artifact, metrics]

# Dependency graph
requires: []
provides:
  - Root cause analysis of low SQL EM for T5 models
  - Quantified corrected SQL EM numbers for all 3 approaches
  - Actionable regex post-processing fix strategy
affects: [part1-training, part2-training, report-writing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Post-decode regex normalization for SentencePiece comma spacing artifact"

key-files:
  created:
    - issues/sql-exact-match-tokenizer-artifact.md
    - knowledge/sql-em-comma-spacing-analysis.md
  modified: []

key-decisions:
  - "SQL EM artifact is in decode, not model -- no retraining needed"
  - "Regex post-processing recommended over custom decode function"
  - "Report should show both raw and normalized SQL EM"

patterns-established:
  - "Document measurement artifacts separately from model deficiencies"

requirements-completed: []

# Metrics
duration: 2min
completed: 2026-03-14
---

# Quick Task 1: Investigate SQL Exact Match Rate Summary

**T5 SentencePiece decode collapses ` , ` to `, `, causing SQL EM to report 3.4% instead of actual 72.5% for fine-tuned model**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-14T00:26:55Z
- **Completed:** 2026-03-14T00:28:38Z
- **Tasks:** 1
- **Files created:** 2

## Accomplishments
- Documented root cause: T5 SentencePiece tokenizer `batch_decode` collapses leading space before commas, converting ground truth ` , ` to `, ` in model output
- Quantified impact: 322 out of 450 SQL EM failures for T5-ft are purely cosmetic comma spacing differences (71.6%)
- Corrected SQL EM: T5-ft jumps from 3.4% to 72.5%, T5-scratch from 3.2% to 50.4%, LLM stays at 0% (different root cause)
- Documented actionable fix: regex post-processing in `_generate_predictions()` after `batch_decode`

## Task Commits

Each task was committed atomically:

1. **Task 1: Document root cause and quantified analysis** - `a152741` (docs)

## Files Created/Modified
- `issues/sql-exact-match-tokenizer-artifact.md` - Root cause analysis: SentencePiece decode artifact causing false SQL EM failures
- `knowledge/sql-em-comma-spacing-analysis.md` - Quantified comparison of raw vs normalized SQL EM for all 3 model approaches

## Decisions Made
- SQL EM artifact is in the decode step, not the model -- no retraining is needed, only post-processing
- Regex post-processing (`re.sub`) is recommended over custom decode function (simpler, safer, reversible)
- Assignment report should show both raw SQL EM (official metric) and normalized SQL EM (supplementary analysis)
- LLM 0% SQL EM is a separate issue (structural query differences) and should not be conflated with the tokenizer artifact

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Steps
- Apply the regex post-processing fix in `part1/train.py` and `part2/train.py` decode paths
- Re-evaluate best model checkpoints with comma normalization to get accurate SQL EM
- Include both raw and normalized SQL EM in the assignment report with explanation

## Self-Check: PASSED

All artifacts verified:
- [x] `issues/sql-exact-match-tokenizer-artifact.md` exists
- [x] `knowledge/sql-em-comma-spacing-analysis.md` exists
- [x] Commit `a152741` exists in git log

---
*Quick Task: 1*
*Completed: 2026-03-14*
