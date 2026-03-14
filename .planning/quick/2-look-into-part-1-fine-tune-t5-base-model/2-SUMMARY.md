---
phase: quick-2
plan: 01
subsystem: report
tags: [latex, tables, t5-base, t5-small, parameter-counts]

requires:
  - phase: none
    provides: n/a
provides:
  - Split T5 results tables (Table 9a for T5-small, Table 9b for T5-base)
  - Params (M) column showing tunable parameter counts
affects: [report]

tech-stack:
  added: []
  patterns: [split-table-by-model-size]

key-files:
  created: []
  modified: [report/report.tex]

decisions:
  - Removed Freeze Enc and Time columns to make room for Params (M) column
  - Folded freeze-encoder info into System names instead of separate column
  - T5-base table sorted by F1 descending with method-based subsections

metrics:
  duration: 2min
  completed: "2026-03-14T13:52:34Z"
  tasks_completed: 1
  tasks_total: 1
---

# Quick Task 2: Split T5 Results Table Summary

Split Table 9 into T5-small (9a) and T5-base (9b) tables with tunable parameter counts.

## Task Completion

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Replace Table 9 with Table 9a (T5-small) and Table 9b (T5-base) | fd4c0b7 | report/report.tex |

## What Was Done

1. **Table 9a (tab:results_t5_small):** Preserved all 17 existing T5-small rows (5 full fine-tune, 5 LoRA, 2 MLP, 1 from-scratch, 2 test). Added Params (M) column with values ranging from 0.6M (LoRA r=16) to 61.6M (MLP dim=1024). Removed Freeze Enc and Time columns. "Restricted v5" renamed to "Restricted v5 + freeze enc".

2. **Table 9b (tab:results_t5_base):** Added 8 new T5-base sweep results sorted by F1 descending. Grouped into full fine-tune (4 rows), MLP projection head (3 rows), and LoRA adapters (1 row). Best result (Base sweep best, F1=85.96) bolded. All Query EM values marked "--".

3. **Reference updates:** `\autoref{tab:results_t5}` on line 442 updated to reference both `tab:results_t5_small` and `tab:results_t5_base`.

4. **Compilation:** LaTeX compiles cleanly with no new warnings. Only pre-existing `tab:results` undefined ref remains (unrelated to this change).

## Deviations from Plan

None -- plan executed exactly as written.

## Self-Check: PASSED

- report/report.tex: FOUND
- Commit fd4c0b7: FOUND
- tab:results_t5_small: 2 references (autoref + label)
- tab:results_t5_base: 2 references (autoref + label)
- LaTeX compilation: clean (no new warnings)
