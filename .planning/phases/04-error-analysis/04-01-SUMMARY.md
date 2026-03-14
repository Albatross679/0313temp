---
phase: 04-error-analysis
plan: 01
subsystem: analysis
tags: [error-analysis, sql, qualitative, latex, t5, gemma, sentencepiece]

# Dependency graph
requires:
  - phase: prior-training
    provides: prediction files (results/*.sql, records/*.pkl) for all 3 models
provides:
  - 5-category error classification script with per-model statistics
  - Filled qualitative error analysis table in LaTeX report
affects: [report-finalization]

# Tech tracking
tech-stack:
  added: []
  patterns: [priority-based mutually-exclusive error classification]

key-files:
  created: []
  modified:
    - script/error_analysis.py
    - report/report.tex

key-decisions:
  - "Used 7 mutually exclusive categories (5 error + 2 correct) with priority-based classification to prevent double-counting"
  - "Classified LLM truncation separately from wrong-reference errors since 82% of LLM errors are actually truncation"
  - "Used pre-computed .pkl records instead of re-executing SQL queries for efficiency"

patterns-established:
  - "Priority-based error classification: truncation > missing operator > wrong reference > other exec > semantic"

requirements-completed: [ANL-01, ANL-02]

# Metrics
duration: 3min
completed: 2026-03-14
---

# Phase 4 Plan 1: Error Analysis Summary

**5-category SQL error classification across T5-FT, T5-Scr, and Gemma 2B with filled qualitative report table using COUNT/TOTAL statistics**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-14T13:25:27Z
- **Completed:** 2026-03-14T13:29:25Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Rewrote error_analysis.py with 7 mutually exclusive categories classifying all 466 dev queries per model
- Filled the tab:qualitative LaTeX table with 5 error rows containing concrete NL/SQL examples and per-model statistics
- Removed all gray placeholder text from the qualitative analysis section
- Report compiles without LaTeX errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Update error analysis script with 5-category classification** - `3d5cf96` (feat)
2. **Task 2: Fill qualitative error analysis table in report** - `aca05d8` (feat)

## Files Created/Modified
- `script/error_analysis.py` - Standalone error classification script: loads all 3 models' predictions, classifies each query into one of 7 categories, outputs per-model stats and cross-model summary
- `report/report.tex` - Filled tab:qualitative table with 5 error rows (missing operator, truncation, wrong reference, wrong JOIN, wrong predicate), replaced instruction text with brief intro

## Key Statistics Produced

| Category | T5-FT | T5-Scr | ICL |
|----------|-------|--------|-----|
| Correct (exact SQL) | 274/466 | 15/466 | 0/466 |
| Correct (same records) | 58/466 | 273/466 | 28/466 |
| Missing comparison operator | 26/466 | 27/466 | 0/466 |
| Query truncation | 0/466 | 0/466 | 383/466 |
| Wrong table/column reference | 16/466 | 0/466 | 5/466 |
| Other execution error | 9/466 | 7/466 | 15/466 |
| Semantic error (wrong JOIN/pred) | 83/466 | 144/466 | 35/466 |

## Decisions Made
- Used 7 mutually exclusive categories (5 error + 2 correct) with priority-based classification to prevent double-counting. Each query assigned to exactly one category per model.
- Separated LLM truncation (383/466) from wrong column reference (5/466) since the "no such column" errors for truncated queries are caused by missing FROM clauses, not incorrect column names.
- Kept "Wrong predicate values" as a separate report row (Row 5) even though it is a subset of semantic errors, because it represents a distinct failure mode (correct structure, wrong literal values).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Error analysis complete for all 3 models
- Report qualitative table filled with concrete examples and statistics
- Pre-existing undefined reference `tab:results` (line 380) is a separate issue unrelated to this plan

---
*Phase: 04-error-analysis*
*Completed: 2026-03-14*
