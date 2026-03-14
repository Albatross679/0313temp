---
phase: quick-2
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [report/report.tex]
autonomous: true
requirements: [QUICK-2]

must_haves:
  truths:
    - "Table 9a shows all T5-small fine-tune + from-scratch + test results with a Params (M) column"
    - "Table 9b shows T5-base sweep results with a Params (M) column, sorted by F1 descending"
    - "Freeze Enc column is removed; freeze-encoder variants are indicated in the System name"
    - "Both tables compile without LaTeX errors"
  artifacts:
    - path: "report/report.tex"
      provides: "Split T5 results tables (9a and 9b)"
      contains: "tab:results_t5_small"
    - path: "report/report.tex"
      provides: "T5-base results table"
      contains: "tab:results_t5_base"
  key_links:
    - from: "report/report.tex"
      to: "autoref references"
      via: "label names"
      pattern: "tab:results_t5"
---

<objective>
Split the existing T5 results table (Table 9) into two sub-tables: Table 9a for T5-small results and Table 9b for T5-base sweep results. Add a "Params (M)" column to both. Remove the "Freeze Enc" and "Time" columns, folding freeze-encoder info into System names.

Purpose: Present T5-base fine-tuning sweep results alongside existing T5-small results, showing model size and tunable parameter counts for clearer comparison.
Output: Updated report/report.tex with two properly formatted tables.
</objective>

<context>
@report/report.tex (lines 474-513 — the current Table 9)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Replace Table 9 with Table 9a (T5-small) and Table 9b (T5-base)</name>
  <files>report/report.tex</files>
  <action>
Replace lines 474-513 of report/report.tex (the existing `\begin{table}[h!]` through `\end{table}` block for tab:results_t5) with TWO new tables.

**Table 9a — T5-small (tab:results_t5_small):**

Column structure (10 columns, down from 11): System, Method, Params (M), LR, Batch, Schema, Dropout, Epochs, Query EM (%), F1 (%)

Removed columns: "Freeze Enc" (fold into System name) and "Time" (not needed).

Row data — carry over all existing rows with these changes:
- "Restricted v5" row: rename System to "Restricted v5 + freeze enc" (it had Freeze Enc = checkmark). Remove the Freeze Enc column value.
- "LoRA + freeze encoder" row: already has freeze in name, just remove the Freeze Enc column value.
- Add Params (M) column with these values:
  - Restricted v1, v2, v3 (best), v7: 60.5
  - Restricted v5 + freeze enc: 41.6
  - LoRA v1 (r=16, q/v): 0.6
  - LoRA v2 (r=16, q/v): 0.6
  - LoRA v3 (r=32, q/k/v/o): 2.4
  - LoRA + freeze encoder: 0.6
  - LoRA + warmstart: 0.6
  - MLP v1 (dim=1024): 61.6
  - MLP v2 (dim=1024): 61.6
  - From-scratch: 60.5
  - T5 fine-tuning (test): 60.5
  - T5 from scratch (test): 60.5

Use `\multicolumn{10}` (not 11) for section header rows.
Use `p{4.2cm}crccccccc` for column spec (r for Params so numbers align right).
Keep `\makebox[\textwidth][c]` wrapping and `\small`.
Keep bold on Restricted v3 (best) row and its Query EM / F1 values.

Caption: "T5-small development and test results (Parts 1 \& 2). Params (M) = tunable parameters in millions. Constant hyperparameters in \autoref{tab:constant_params}. Method: Full = all parameters, LoRA = low-rank adapters, MLP = projection head. Best dev result in bold."
Label: `tab:results_t5_small`

**Table 9b — T5-base (tab:results_t5_base):**

Immediately after Table 9a. Same column structure but WITHOUT Schema column (all base runs had varying schema settings already captured). Use 9 columns: System, Method, Params (M), LR, Batch, Schema, Dropout, Epochs, Query EM (%), F1 (%)

Actually, keep Schema column for consistency (10 columns, same as 9a).

Row data (sorted by F1 descending, all dev results):
```
\multicolumn{10}{l}{\textbf{Dev Results --- T5-base Fine-tuned}} \\
\midrule
\multicolumn{10}{l}{\emph{Full fine-tune}} \\
\textbf{Base sweep best}    & Full & 222.9 & 6.19e-5 & 32 & \checkmark & 0.05 & 79  & -- & \textbf{85.96} \\
Base sweep v2               & Full & 222.9 & 5.52e-5 & 32 & \checkmark & 0    & 79  & -- & 84.31 \\
Base sweep v3               & Full & 222.9 & 2.59e-4 & 32 & --         & 0.2  & 71  & -- & 83.05 \\
Base sweep v4               & Full & 222.9 & 5.50e-5 & 32 & --         & 0    & 31  & -- & 75.77 \\[4pt]
\multicolumn{10}{l}{\emph{MLP projection head}} \\
Base MLP-512 v1             & MLP  & 223.7 & 2.35e-4 & 32 & --         & 0.15 & 123 & -- & 80.76 \\
Base MLP-512 v2             & MLP  & 223.7 & 7.83e-4 & 32 & --         & 0.15 & 43  & -- & 79.56 \\
Base MLP-1024               & MLP  & 224.5 & 1.28e-4 & 32 & --         & 0.1  & 147 & -- & 78.86 \\[4pt]
\multicolumn{10}{l}{\emph{LoRA adapters}} \\
Base LoRA $r$=32 (q/k/v/o)  & LoRA & 7.1   & 1.29e-5 & 32 & \checkmark & 0.05 & 335 & -- & 76.48 \\
```

Bold the best row (Base sweep best) System name and F1 value.

Caption: "T5-base fine-tuning development results. Same constant hyperparameters as \autoref{tab:constant_params} except model = T5-base (222M params). Best result in bold."
Label: `tab:results_t5_base`

**Update any `\autoref{tab:results_t5}` references elsewhere in the file** to reference both tables or the appropriate one. Search the file for `tab:results_t5` references (likely in the paragraph on line 442 and the Query EM correction paragraph on line 515). Update:
- Line 442 area: change `\autoref{tab:results_t5}` to `\autoref{tab:results_t5_small} and \autoref{tab:results_t5_base}`
- Line 515 area (Query EM correction): keep reference to T5-small table only since correction applies to T5-small runs → `\autoref{tab:results_t5_small}`
  </action>
  <verify>
    <automated>cd /home/turncloak/0313temp/report && latexmk -pdf -interaction=nonstopmode report.tex 2>&1 | tail -5</automated>
  </verify>
  <done>
    - Table 9a (tab:results_t5_small) shows all T5-small rows with Params (M) column, no Freeze Enc or Time columns
    - Table 9b (tab:results_t5_base) shows 8 T5-base sweep rows sorted by F1, with Params (M) column
    - Both tables compile cleanly with latexmk
    - All autoref references updated
    - report.pdf renders both tables correctly
  </done>
</task>

</tasks>

<verification>
cd /home/turncloak/0313temp/report && latexmk -pdf -interaction=nonstopmode report.tex 2>&1 | grep -E "Error|Warning.*ref|Output written"
</verification>

<success_criteria>
- report.tex compiles without errors
- Table 9a contains T5-small results with Params (M) column (no Freeze Enc, no Time)
- Table 9b contains 8 T5-base sweep rows sorted by F1 descending
- Both tables have consistent column structure
- All cross-references resolve (no undefined ref warnings for tab:results_t5*)
</success_criteria>

<output>
After completion, create `.planning/quick/2-look-into-part-1-fine-tune-t5-base-model/2-SUMMARY.md`
</output>
