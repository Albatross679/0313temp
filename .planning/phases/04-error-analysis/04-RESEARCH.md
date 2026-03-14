# Phase 4: Error Analysis - Research

**Researched:** 2026-03-14
**Domain:** NL-to-SQL error analysis, qualitative evaluation, LaTeX report writing
**Confidence:** HIGH

## Summary

Phase 4 requires identifying common SQL error patterns across all three model approaches (T5 fine-tune, T5 from-scratch, LLM prompting) and filling a qualitative error analysis table in the LaTeX report with concrete examples and statistics. This is a pure analysis and writing task -- no model training or code changes required.

The research reveals five distinct error categories that span the three models, with clear per-model statistics. The dev set (466 queries) provides sufficient material for the analysis. All prediction files (`results/t5_ft_dev.sql`, `results/t5_scr_dev.sql`, `results/llm_dev.sql`) and their corresponding record files exist and have been verified. The key insight is that each model approach has a characteristic failure mode: T5 models drop comparison operators during decoding (a SentencePiece artifact), the LLM truncates queries due to max_new_tokens limits, and all models struggle with complex multi-table queries involving subqueries and fares.

**Primary recommendation:** Write a Python analysis script that computes exact error counts per category per model, then fill the LaTeX `tab:qualitative` table with 5 error rows including concrete NL/SQL examples and COUNT/TOTAL statistics.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ANL-01 | Identify common SQL error patterns across all 3 parts | Five error categories identified with cross-model statistics: (1) missing comparison operators, (2) query truncation, (3) wrong table/column references, (4) wrong JOIN structure, (5) wrong predicate values. Data verified from all three model outputs. |
| ANL-02 | Fill qualitative error analysis table with concrete examples and statistics | Report template examined -- `tab:qualitative` table in landscape format needs Error Type, Relevant Models, Example Of Error, Error Description, and Statistics columns. At least 3 rows required; 5 recommended. Concrete examples identified from dev set analysis. |
</phase_requirements>

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Python 3 | 3.10+ | Analysis script | Already in project |
| pickle | stdlib | Load .pkl record files | Used by existing evaluate.py |
| re | stdlib | SQL pattern matching | Lightweight, no deps |
| sqlite3 | stdlib | Optionally re-execute queries for validation | Already used by utils.py |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| LaTeX (report/report.tex) | Error analysis table | Fill tab:qualitative |
| collections.Counter | Aggregate error counts | Categorization |

### No Additional Libraries Needed
This phase requires zero new dependencies. All analysis uses stdlib Python and existing project infrastructure (`utils.py`, `evaluate.py`).

## Architecture Patterns

### Analysis Script Structure
```
script/
  error_analysis.py    # Standalone script that reads all prediction files
                       # and outputs categorized error statistics
```

The analysis script should:
1. Load ground truth SQL (`data/dev.sql`), NL (`data/dev.nl`), and records (`records/ground_truth_dev.pkl`)
2. Load predictions for all 3 models from `results/` and `records/`
3. Classify each prediction into error categories
4. Output per-model statistics and concrete examples for the report

### Report Table Structure (from template)

The `tab:qualitative` table uses landscape orientation with 5 columns:
- **Error Type** (2cm) -- Short name
- **Relevant Models** (2cm) -- Which of: ICL, T5 fine-tuned, T5 from scratch
- **Example Of Error** (6cm) -- Concrete NL + SQL snippet
- **Error Description** (6cm) -- Natural language explanation
- **Statistics** (6cm) -- COUNT/TOTAL format, per-model if shared

The assignment requires at least 3 error types. Based on analysis, 5 categories provide thorough coverage without redundancy.

### Pattern: Error Classification Logic

```python
def classify_error(gt_sql, pred_sql, error_msg, gt_records, pred_records):
    """Classify a single prediction into an error category."""
    if gt_sql == pred_sql:
        return "correct"

    # Category 1: Missing comparison operator (syntax error near number)
    if error_msg and "near" in error_msg:
        if re.search(r'\w+\.\w+\s+\d+\b', pred_sql):
            return "missing_operator"

    # Category 2: Truncated/incomplete query
    if len(pred_sql) < 50:  # LLM truncation
        return "truncated"
    if error_msg and "incomplete" in error_msg:
        return "truncated"

    # Category 3: Wrong table/column reference
    if error_msg and ("no such column" in error_msg or "no such table" in error_msg):
        return "wrong_reference"

    # Category 4: Other execution error
    if error_msg:
        return "other_execution_error"

    # Query executes -- check records
    if set(gt_records) == set(pred_records):
        return "correct_records"  # Different SQL but same result

    # Category 5: Semantic error (wrong records)
    return "semantic_error"
```

## Identified Error Categories

### Category 1: Missing Comparison Operator
**What:** T5 models output `column_name NUMBER` instead of `column_name < NUMBER`, dropping `<`, `>`, `<=`, `>=` operators.
**Root cause:** SentencePiece tokenizer artifact. The `<` and `>` characters are special in the T5 vocabulary and get dropped or mangled during beam search decoding.
**Statistics:**
- T5-FT: 26/466 (5.6%)
- T5-Scr: 27/466 (5.8%)
- LLM: 0/466 (0%)

**Concrete example:**
- NL: "give me the flights from salt lake city to new york city arriving before 6pm"
- GT: `...flight_1.arrival_time < 1800...`
- Pred: `...flight_1.arrival_time  1800...`
- Error: `OperationalError: near "1800": syntax error`

### Category 2: Query Truncation / Incomplete Generation
**What:** The model generates only a fragment of the SQL query, missing FROM/WHERE/JOIN clauses entirely.
**Root cause (LLM):** Gemma 2B's `max_new_tokens` limit causes premature cutoff. The model outputs only `SELECT DISTINCT flight_1.flight_id` without any FROM clause.
**Root cause (T5):** Rare cases where the decoder hits EOS too early or max_length is insufficient for complex queries.
**Statistics:**
- T5-FT: 1/466 (0.2%)
- T5-Scr: 3/466 (0.6%)
- LLM: 377/466 (80.9%)

**Concrete example (LLM):**
- NL: "what flights are available tomorrow from denver to philadelphia"
- Pred: `SELECT DISTINCT flight_1.flight_id`
- Error: `OperationalError: no such column: flight_1.flight_id` (no FROM clause)

### Category 3: Wrong Table/Column Reference
**What:** The predicted SQL references a column or table alias that was never defined in the FROM clause, or uses the wrong alias.
**Root cause (T5-FT):** Model generates alias names (e.g., `city_1`) but forgets to include the corresponding table in FROM, or uses different aliases than defined.
**Root cause (LLM):** When queries are not truncated, the LLM uses incorrect column names (e.g., `fare.flight_id` which doesn't exist) or references undeclared aliases.
**Statistics:**
- T5-FT: 16/466 (3.4%)
- T5-Scr: 0/466 (0%)
- LLM: 387/466 (83.0%) -- mostly from truncation causing "no such column"

Note: For the LLM, the 387 "no such column" errors are overwhelmingly caused by truncation (Category 2). Among the 89 non-truncated LLM queries, only 10 have wrong column reference errors. For the report, it is cleaner to count truncation and wrong reference separately: LLM truncation causes 377 errors, and the remaining 10 non-truncated wrong-reference errors can be noted.

### Category 4: Wrong JOIN Structure / Missing Conditions
**What:** The query executes successfully but returns wrong records because it has incorrect JOIN conditions, missing table joins, or extra unnecessary joins.
**Sub-patterns:**
- Missing a table in FROM (e.g., omitting `airport_service` when translating airport codes to city names)
- Extra unnecessary joins (e.g., joining `airport_service` twice when once suffices)
- Wrong subquery structure (using different aggregation approach)
**Statistics (executes but wrong records):**
- T5-FT: 83/466 (17.8%)
- T5-Scr: 144/466 (30.9%)
- LLM: 36/466 (7.7%)

### Category 5: Wrong Predicate Values
**What:** The SQL structure is correct but specific values in WHERE clauses are wrong -- wrong city name, wrong date, wrong time value, wrong airline code.
**Sub-patterns:**
- Wrong date values (e.g., `month_number = 2` instead of `month_number = 1`)
- Wrong city names (e.g., extra city or missing city in self-join patterns)
- Wrong time boundaries (e.g., `BETWEEN 0 AND 800` instead of `< 800`)
**This is a subset of Category 4 that is analytically distinct:** the model understands the query structure but misinterprets the specific values from the NL input.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SQL parsing | Custom SQL parser | Regex pattern matching on predicted SQL strings | Full SQL parsing is overkill for error categorization; regex suffices for pattern detection |
| Record comparison | Custom record diff | Existing `compute_record_F1` / `compute_record_exact_match` in `utils.py` | Already handles set comparison correctly |
| Query execution | Custom DB executor | Existing `compute_records()` in `utils.py` with ThreadPoolExecutor | Already handles timeouts, errors, parallel execution |

**Key insight:** The error analysis is fundamentally a text comparison and categorization task. The heavy lifting (SQL execution, record comparison) is already done and stored in the `.pkl` files. The analysis script just needs to read those results and categorize them.

## Common Pitfalls

### Pitfall 1: Confusing LLM Truncation with Column Errors
**What goes wrong:** The LLM's 387 "no such column" errors might be reported as a column-naming issue, when the real root cause is query truncation. `SELECT DISTINCT flight_1.flight_id` without a FROM clause triggers "no such column" because there's no `flight` table alias defined.
**How to avoid:** Check query length first. If `len(sql) < 50`, classify as truncation regardless of the error message.

### Pitfall 2: Double-Counting Error Categories
**What goes wrong:** A single query might exhibit multiple error patterns (e.g., missing operator AND wrong city name). If counted in both categories, statistics sum to more than total errors.
**How to avoid:** Use a priority-based classification: assign each query to exactly one category using the priority order: execution error > truncation > wrong reference > semantic error. Alternatively, clearly state in the report that categories are not mutually exclusive.

### Pitfall 3: LaTeX Table Overflow
**What goes wrong:** The qualitative table uses landscape format with fixed column widths (p{2cm}, p{6cm}). Long SQL examples overflow cells or cause bad line breaks.
**How to avoid:** Use `\texttt{...}` for SQL snippets, truncate long queries with `...`, and use `\\` for line breaks within cells. Keep examples to the most diagnostic fragment, not the full query.

### Pitfall 4: Reporting Statistics Inconsistently
**What goes wrong:** The assignment says "COUNT/TOTAL" format. Using percentages alone or mixing formats confuses graders.
**How to avoid:** Always use "COUNT/TOTAL" (e.g., "26/466") and optionally add percentage in parentheses. When an error type applies to multiple models, prefix with model name: "T5-FT: 26/466, T5-Scr: 27/466".

### Pitfall 5: Not Showing Both Predicted and Ground Truth SQL
**What goes wrong:** Only showing the predicted SQL without the ground truth makes it impossible for the reader to see what went wrong.
**How to avoid:** For each example, show: (1) NL input, (2) ground truth SQL (or key fragment), (3) predicted SQL (or key fragment), (4) what specifically is wrong.

## Code Examples

### Loading All Model Predictions

```python
import pickle
import re

# Load ground truth
with open('data/dev.sql') as f:
    gt_sql = [l.strip() for l in f.readlines()]
with open('data/dev.nl') as f:
    nl = [l.strip() for l in f.readlines()]
with open('records/ground_truth_dev.pkl', 'rb') as f:
    gt_records, _ = pickle.load(f)

# Load predictions
models = {}
for name, sql_path, pkl_path in [
    ('t5_ft', 'results/t5_ft_dev.sql', 'records/t5_ft_dev.pkl'),
    ('t5_scr', 'results/t5_scr_dev.sql', 'records/t5_scr_dev.pkl'),
    ('llm', 'results/llm_dev.sql', 'records/llm_dev.pkl'),
]:
    with open(sql_path) as f:
        pred_sql = [l.strip() for l in f.readlines()]
    with open(pkl_path, 'rb') as f:
        records, errors = pickle.load(f)
    models[name] = {'sql': pred_sql, 'records': records, 'errors': errors}
```

### LaTeX Table Row Example

```latex
Missing comparison operator
& T5 fine-tuned, T5 from scratch
& NL: ``arriving before 6pm'' \newline
  GT: \texttt{arrival\_time < 1800} \newline
  Pred: \texttt{arrival\_time \space\space 1800}
& The model drops the comparison operator (\texttt{<}, \texttt{>})
  from inequality predicates, producing invalid SQL.
  Root cause: T5 SentencePiece tokenizer treats angle brackets
  as special characters during beam search decode.
& T5-FT: 26/466 (5.6\%) \newline
  T5-Scr: 27/466 (5.8\%) \\
```

## Verified Error Statistics (Dev Set, 466 queries)

### Overall Model Performance

| Metric | T5 Fine-tune | T5 From Scratch | LLM (Gemma 2B) |
|--------|-------------|-----------------|-----------------|
| Record F1 | 0.7707 | 0.6612 | 0.1735 |
| Record EM | 0.7318 | 0.6352 | 0.1652 |
| SQL EM (raw) | 0.5880 | 0.0322 | 0.0000 |
| Execution errors | 51/466 | 34/466 | 402/466 |
| Correct SQL | 274/466 | 15/466 | 0/466 |
| Wrong SQL, correct records | 58/466 | 53/466 | 28/466 |
| Wrong SQL, wrong records | 83/466 | 144/466 | 36/466 |

### Error Pattern Cross-Model Summary

| Error Pattern | T5-FT | T5-Scr | LLM | Shared? |
|---------------|-------|--------|-----|---------|
| Missing comparison operator | 26/466 | 27/466 | 0/466 | T5 only |
| Query truncation/incomplete | 1/466 | 3/466 | 377/466 | LLM dominant |
| Wrong table/column reference | 16/466 | 0/466 | 10/89* | T5-FT, LLM |
| Other syntax error | 8/466 | 4/466 | 15/466 | All |
| Semantic error (wrong records) | 83/466 | 144/466 | 36/466 | All |

*LLM: 10 out of 89 non-truncated queries have wrong column references.

### Query Complexity vs. Accuracy (Record EM)

| Query Type | N | T5-FT | T5-Scr | LLM |
|-----------|---|-------|--------|-----|
| Simple (no complex features) | 240 | 72% | 62% | 21% |
| Date conditions | 60 | 67% | 62% | 5% |
| Fare queries | 56 | 70% | 61% | 14% |
| Date + range conditions | 21 | 95% | 67% | 5% |
| Flight stops | 20 | 90% | 100% | 55% |
| Aggregation + subquery | 18 | 89% | 61% | 6% |
| Range conditions only | 17 | 71% | 76% | 18% |
| Aggregation + fare + subquery | 14 | 71% | 43% | 0% |

## Data File Locations (Verified)

| File | Path | Lines | Exists |
|------|------|-------|--------|
| Ground truth SQL | `data/dev.sql` | 466 | Yes |
| Ground truth NL | `data/dev.nl` | 466 | Yes |
| Ground truth records | `records/ground_truth_dev.pkl` | 466 entries | Yes |
| T5-FT predictions | `results/t5_ft_dev.sql` | 466 | Yes |
| T5-FT records | `records/t5_ft_dev.pkl` | 466 entries | Yes |
| T5-Scr predictions | `results/t5_scr_dev.sql` | 466 | Yes |
| T5-Scr records | `records/t5_scr_dev.pkl` | 466 entries | Yes |
| LLM predictions | `results/llm_dev.sql` | 466 | Yes |
| LLM records | `records/llm_dev.pkl` | 466 entries | Yes |

## Recommended Error Categories for Report

Based on the analysis, use these 5 error categories in the qualitative table:

1. **Missing comparison operator** -- T5-FT (26/466), T5-Scr (27/466). Model drops `<`/`>` operators.
2. **Query truncation** -- LLM (377/466), T5-Scr (3/466). Model generates incomplete SQL.
3. **Wrong table/column reference** -- T5-FT (16/466), LLM (10/89 non-truncated). References undefined aliases.
4. **Wrong JOIN structure** -- T5-FT (subset of 83 semantic errors), T5-Scr (subset of 144). Missing or extra table joins.
5. **Wrong predicate values** -- T5-FT (subset of 83), T5-Scr (subset of 144), LLM (subset of 36). Wrong city names, dates, time values.

Categories 4 and 5 are sub-classifications of the "semantic error" bucket. The planner should decide whether to keep them separate or merge them, depending on report space. The assignment requires at least 3 categories; 5 provides thorough coverage.

## Concrete Examples for Each Category

### Example 1: Missing Comparison Operator
- **NL:** "give me the flights from salt lake city to new york city arriving before 6pm"
- **GT fragment:** `flight_1.arrival_time < 1800`
- **T5-FT prediction:** `flight_1.arrival_time  1800` (operator dropped)
- **Result:** `OperationalError: near "1800": syntax error`

### Example 2: Query Truncation (LLM)
- **NL:** "what flights are available tomorrow from denver to philadelphia"
- **GT:** Full query with FROM flight, airport_service, city, days, date_day + WHERE clause
- **LLM prediction:** `SELECT DISTINCT flight_1.flight_id` (entire query after SELECT is missing)
- **Result:** `OperationalError: no such column: flight_1.flight_id`

### Example 3: Wrong Table/Column Reference
- **NL:** "ground transportation oakland"
- **T5-FT prediction:** References `airport_service_1.airport_code` but `airport_service` table not in FROM clause
- **Result:** `OperationalError: no such column: airport_service_1.airport_code`

### Example 4: Wrong JOIN Structure
- **NL:** "list all flights from boston to san francisco with the maximum number of stops"
- **GT:** Uses subquery with `MAX(flight_1.stops)` to find maximum stops
- **T5-FT prediction:** Uses `flight_1.stops = 0` (nonstop flights -- opposite of intent)
- **Result:** Returns 4 records instead of 2, completely wrong semantics

### Example 5: Wrong Predicate Values
- **NL:** "what flights are available tomorrow from denver to philadelphia"
- **GT:** `date_day_1.month_number = 1 AND date_day_1.day_number = 20`
- **T5-FT prediction:** `date_day_1.month_number = 2 AND date_day_1.day_number = 20`
- **Result:** Returns 24 records instead of 23 (wrong month)

## State of the Art

| Aspect | Finding |
|--------|---------|
| SQL EM metric | Overly strict -- penalizes formatting and semantically equivalent queries. Record F1/EM are more meaningful |
| SentencePiece comma artifact | Documented in quick-task-1. Comma spacing difference (`, ` vs ` , `) inflates SQL EM errors. Already fixed in current results |
| LLM truncation issue | 80.9% of LLM queries truncated. Known `max_new_tokens` limitation of Gemma 2B |
| Error analysis in NL-to-SQL literature | Standard categories: syntax errors, schema linking errors, nested query errors, value prediction errors |

## Open Questions

1. **Best model checkpoint for T5-FT analysis**
   - What we know: The user mentioned best model at `output/t5_ft_base_sweep_1i8vr3_20260314_012024/` (T5-base, F1=0.8596). However, `results/t5_ft_dev.sql` currently contains T5-base predictions with F1=0.7707.
   - What's unclear: Whether the results/ files need to be regenerated from the best checkpoint before analysis, or whether to use what's currently there.
   - Recommendation: Use the current `results/t5_ft_dev.sql` for error analysis since it is the most recent. If Phase 3 (report metrics) updates these files, the error analysis numbers may need to be refreshed. The planner should sequence accordingly.

2. **Number of error categories**
   - What we know: Assignment requires minimum 3. Analysis identified 5 meaningful categories.
   - Recommendation: Use 5 categories. They are distinct enough to be analytically useful and provide thorough coverage that demonstrates understanding.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual validation (no automated tests needed) |
| Config file | none |
| Quick run command | `python3 script/error_analysis.py` |
| Full suite command | Visual inspection of LaTeX table output |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ANL-01 | Error patterns identified across all 3 parts | manual | `python3 script/error_analysis.py` | Wave 0 |
| ANL-02 | Qualitative table filled with examples/stats | manual | Compile report, visually inspect table | N/A |

### Sampling Rate
- **Per task commit:** Visual inspection of generated statistics
- **Per wave merge:** Compile LaTeX report and verify table renders correctly
- **Phase gate:** Table has minimum 3 error rows with concrete examples and COUNT/TOTAL statistics

### Wave 0 Gaps
- [ ] `script/error_analysis.py` -- analysis script that outputs categorized statistics
- [ ] Report table filled in `report/report.tex` -- the `tab:qualitative` table

## Sources

### Primary (HIGH confidence)
- Direct analysis of prediction files (`results/*.sql`, `records/*.pkl`) -- all statistics computed from actual data
- `utils.py` -- verified evaluation logic (compute_metrics, compute_records, compute_record_F1)
- `report/report.tex` -- verified report template structure and requirements
- `knowledge/sql-em-comma-spacing-analysis.md` -- prior research on SQL EM artifact

### Secondary (MEDIUM confidence)
- `.planning/quick/1-investigate-why-sql-exact-match-rate-is-/1-SUMMARY.md` -- SQL EM investigation results

## Metadata

**Confidence breakdown:**
- Error categories: HIGH -- computed directly from all 1,398 predictions (466 x 3 models)
- Statistics: HIGH -- exact counts verified with Python analysis
- LaTeX template: HIGH -- read directly from report.tex
- Recommended examples: HIGH -- selected from actual data

**Research date:** 2026-03-14
**Valid until:** Indefinite (analysis of fixed prediction files; only changes if prediction files are regenerated)
