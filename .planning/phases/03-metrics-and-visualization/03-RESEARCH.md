# Phase 3: Metrics and Visualization - Research

**Researched:** 2026-03-13
**Domain:** Evaluation metrics computation, matplotlib plotting, LaTeX report editing
**Confidence:** HIGH

## Summary

Phase 3 involves two distinct tasks: (1) computing and inserting all metrics into the report LaTeX tables, and (2) creating an ICL sensitivity plot. The critical constraint is that **test set ground truth does not exist locally** -- there is no `data/test.sql` or `records/ground_truth_test.pkl`. Test metrics are computed exclusively on Gradescope upon submission. Therefore, "compute test metrics" means using `evaluate.py` or `compute_metrics()` to evaluate predictions against ground truth for **dev set** results that still need filling, plus noting that test metrics can only be obtained by submitting to Gradescope.

All prediction files already exist (`results/t5_ft_test.sql`, `results/t5_scr_test.sql`, `results/llm_test.sql` with corresponding `.pkl` records). Dev set predictions also exist with metrics already computed for most variants (cached in log files). The ICL sensitivity data points for k=0, k=1, k=3 on dev set are available from existing experiment logs.

**Primary recommendation:** Focus on LaTeX editing to fill placeholders with existing metrics, restructure the LLM results table with actual experiment names, and create a simple matplotlib bar/line plot for ICL sensitivity. Test metric placeholders should be filled after Gradescope submission or left as "TBD (Gradescope)" if not yet submitted.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RPT-01 | Compute test set Query EM and Record F1 for Part 1 (T5 fine-tune) | Test ground truth unavailable locally; must submit to Gradescope. Test prediction files exist. Dev metrics already in report table. |
| RPT-02 | Compute test set Query EM and Record F1 for Part 2 (T5 from scratch) | Same as RPT-01. Test prediction files exist at `results/t5_scr_test.sql`. |
| RPT-03 | Compute test set Query EM and Record F1 for Part 3 (LLM prompting) | Same constraint. Test predictions at `results/llm_test.sql`. |
| RPT-04 | Fill all XX.XX placeholders in report tables with actual scores | 9 placeholder locations identified in `report.tex` (lines 482-483, 500-505, 509). Dev metrics available from experiment logs. Test metrics from Gradescope. |
| VIZ-01 | Create ICL sensitivity plot (Record F1 vs k=0,1,3) | Data points available: k=0 F1=0.1260, k=1 F1=0.1260, k=3 F1=0.1196 (random) and BM25 k=3 F1=0.1735. Use matplotlib. |
| VIZ-02 | Insert plot into report LaTeX | Replace placeholder text at line 519 of `report.tex` with `\includegraphics` referencing `media/icl_sensitivity.pdf`. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| matplotlib | 3.8.0 | Plot generation (ICL sensitivity) | In project requirements.txt, standard Python plotting |
| numpy | 1.26.0 | Metric computation support | Already used by `utils.py` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| seaborn | 0.13.2 | Optional plot styling | If cleaner academic-style plots desired |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| matplotlib | plotly | plotly in requirements.txt but generates interactive HTML, not PDF for LaTeX |
| seaborn | raw matplotlib | seaborn adds styling polish but adds dependency complexity |

**Installation:**
Already in `requirements.txt`. On the actual compute environment:
```bash
pip install matplotlib==3.8.0 seaborn==0.13.2
```

## Architecture Patterns

### Task Structure
```
Phase 3 execution flow:
1. Collect all existing dev metrics from experiment logs
2. Run evaluate.py for any missing dev metrics
3. Restructure LLM results table with actual experiment names/metrics
4. Fill T5 test result placeholders (after Gradescope submission)
5. Generate ICL sensitivity plot to media/icl_sensitivity.pdf
6. Insert plot into report.tex via \includegraphics
```

### Pattern 1: Metric Collection from Existing Logs
**What:** All dev metrics already exist in log files and experiment docs. No re-running of inference needed.
**When to use:** Always -- avoid re-running GPU inference unnecessarily.
**Available metrics from experiment logs:**

T5 Fine-tune dev (from report.tex line 463): Query EM = 2.67%, Record F1 = 79.60%
T5 From-scratch dev (from report.tex line 478): Query EM = 3.22%, Record F1 = 66.12%

LLM Prompting dev (from experiment log files):
- k=0 (zero-shot, random): SQL EM=0.0, Record F1=0.1260 (12.60%)
- k=1 (random): SQL EM=0.0, Record F1=0.1260 (12.60%)
- k=3 (random): SQL EM=0.0, Record F1=0.1196 (11.96%)
- k=3 (BM25, best): SQL EM=0.0, Record F1=0.1735 (17.35%)
- Ablation no-instructions: SQL EM=0.0, Record F1=0.1180 (11.80%)
- Ablation no-schema: SQL EM=0.0, Record F1=0.1180 (11.80%)
- Ablation schema-only: SQL EM=0.0, Record F1=0.1137 (11.37%)

### Pattern 2: Test Metrics via Gradescope
**What:** Test ground truth is NOT available locally. No `data/test.sql` or `records/ground_truth_test.pkl` exists.
**When to use:** Test metrics can only be obtained by submitting prediction files to Gradescope.
**Implication:** The planner must account for this -- either (a) submit to Gradescope first, get scores, then fill report, or (b) fill dev metrics now and leave test metrics as a final step after Gradescope submission.

### Pattern 3: ICL Sensitivity Plot
**What:** Simple line/bar plot with x=k (0,1,3), y=Record F1 (dev set).
**When to use:** Required by assignment (see report.tex line 517).
**Data points:** k=0 (0.1260), k=1 (0.1260), k=3 (0.1196) for random selection. Could optionally show BM25 k=3 (0.1735) as separate series.

### Anti-Patterns to Avoid
- **Re-running inference:** All predictions already exist. Do NOT re-run prompting.py or train_t5.py just to get metrics.
- **Using plotly for LaTeX:** Plotly generates HTML/interactive plots. Use matplotlib to generate PDF/PNG for LaTeX \includegraphics.
- **Hardcoding test metrics as 0.00:** Test metrics are unknown until Gradescope submission. Use actual Gradescope scores.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Metric computation | Custom metric code | `evaluate.py` / `utils.compute_metrics()` | Already implemented, handles edge cases |
| Plot styling | Manual matplotlib style tuning | seaborn with `set_theme(style='whitegrid')` | Academic-quality defaults |
| PDF figure generation | Manual figure export | `plt.savefig('media/icl_sensitivity.pdf', bbox_inches='tight')` | Proper LaTeX-compatible output |

**Key insight:** All metrics are already computed and cached in log files. This phase is primarily about data collection and LaTeX editing, not computation.

## Common Pitfalls

### Pitfall 1: Assuming Test Ground Truth Exists
**What goes wrong:** Trying to call `evaluate.py` with `--development_sql data/test.sql` which does not exist.
**Why it happens:** The phase description says "compute test set metrics" but ground truth is only on Gradescope.
**How to avoid:** Submit to Gradescope to get test metrics. Or if already submitted, use the Gradescope scores.
**Warning signs:** FileNotFoundError on `data/test.sql`.

### Pitfall 2: LLM Results Table Still Has Template Placeholders
**What goes wrong:** The LLM results table (lines 500-509) still has generic "Variant1", "Variant2" etc. with gray placeholder text.
**Why it happens:** The template was never customized with actual experiment names.
**How to avoid:** Restructure the entire LLM results table with actual experiment descriptions: "BM25 k=3 (best)", "Random k=0 (zero-shot)", "Random k=1", "Random k=3", ablation variants.

### Pitfall 3: Inconsistent Metric Formats
**What goes wrong:** Mixing raw decimal (0.1735) with percentage (17.35) formats across tables.
**Why it happens:** T5 table uses percentages (79.60), LLM table uses "XX.XX" ambiguously.
**How to avoid:** Follow existing convention: T5 table uses percentages with % symbol. LLM table caption says "F1 score" -- check the T5 table convention and be consistent. The T5 table uses Query EM (%) and F1 (%) headers so LLM should match (use percentages).

### Pitfall 4: ICL Plot Uses Wrong Data Points
**What goes wrong:** Plotting BM25 results alongside random results without labeling the difference.
**Why it happens:** The "best" config (BM25 k=3) uses a different example selection strategy than k=0, k=1, k=3 random.
**How to avoid:** The assignment says "the prompts and examples used for this plot should correspond to the ones you described in Subsection ICL." Plot the random selection k=0,1,3 as the primary series. Optionally add BM25 as a separate marked point.

### Pitfall 5: LaTeX Compile Errors from Bad Escaping
**What goes wrong:** Inserting values with underscores or special chars breaks LaTeX.
**Why it happens:** Metric values are plain numbers but surrounding text edits might introduce errors.
**How to avoid:** Only modify numeric values in existing cells. Test compilation after edits.

## Code Examples

### Metric Collection Script (No GPU Needed)
```python
# script/collect_metrics.py
# Reads existing log files and prints all metrics for report

import re
from pathlib import Path

LOG_FILES = {
    "llm_k1_dev": "results/llm_k1_dev_log.txt",
    "llm_k3_dev": "results/llm_k3_dev_log.txt",
    "llm_bm25_k3_dev": "results/llm_bm25_k3_dev_log.txt",
    "llm_abl_no_instr_dev": "results/llm_abl_no_instr_dev_log.txt",
    "llm_abl_no_schema_dev": "results/llm_abl_no_schema_dev_log.txt",
    "llm_abl_schema_only_dev": "results/llm_abl_schema_only_dev_log.txt",
}

for name, path in LOG_FILES.items():
    p = Path(path)
    if p.exists():
        text = p.read_text()
        sql_em = re.search(r"SQL EM: ([\d.]+)", text)
        rec_em = re.search(r"Record EM: ([\d.]+)", text)
        rec_f1 = re.search(r"Record F1: ([\d.]+)", text)
        if sql_em and rec_em and rec_f1:
            print(f"{name}: Query EM={float(sql_em.group(1))*100:.2f}%, "
                  f"Record F1={float(rec_f1.group(1))*100:.2f}%")
```

### ICL Sensitivity Plot
```python
# script/plot_icl_sensitivity.py
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# Data from experiment logs
k_values = [0, 1, 3]
random_f1 = [0.1260, 0.1260, 0.1196]  # Random selection
bm25_f1 = [None, None, 0.1735]  # BM25 only at k=3

fig, ax = plt.subplots(figsize=(5, 3.5))

# Plot random selection line
ax.plot(k_values, [f * 100 for f in random_f1], 'o-', color='#2196F3',
        label='Random selection', linewidth=2, markersize=8)

# Plot BM25 point at k=3
ax.plot(3, 0.1735 * 100, 's', color='#FF5722', markersize=10,
        label='BM25 selection', zorder=5)

ax.set_xlabel('Number of examples ($k$)', fontsize=12)
ax.set_ylabel('Record F1 (%)', fontsize=12)
ax.set_xticks(k_values)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_ylim(0, max(max(random_f1), 0.1735) * 100 * 1.15)

plt.tight_layout()
plt.savefig('media/icl_sensitivity.pdf', bbox_inches='tight', dpi=300)
plt.savefig('media/icl_sensitivity.png', bbox_inches='tight', dpi=300)
print("Saved to media/icl_sensitivity.pdf and media/icl_sensitivity.png")
```

### LaTeX Figure Insertion
```latex
% Replace the placeholder text at line 519 of report.tex with:
\begin{figure}[h!]
\centering
\includegraphics[width=0.7\textwidth]{media/icl_sensitivity.pdf}
\caption{ICL sensitivity to number of examples $k$ on the development set. Record F1 is shown for random example selection ($k = 0, 1, 3$) and BM25 per-query selection ($k = 3$).}
\label{fig:icl_sensitivity}
\end{figure}
```

### LaTeX Report XX.XX Replacement Map

**T5 Results Table (tab:results_t5), lines 482-483:**
```
Line 482: T5 fine-tuning test -- XX.XX & XX.XX -> [Gradescope Query EM] & [Gradescope F1]
Line 483: T5 from scratch test -- XX.XX & XX.XX -> [Gradescope Query EM] & [Gradescope F1]
```

**LLM Results Table (tab:results_llm), lines 500-509:**
The entire table needs restructuring. Replace template rows with actual experiments:
```
Dev Results:
  BM25 k=3 (best)           -> 0.00 & 17.35
  Random k=0 (zero-shot)    -> 0.00 & 12.60
  Random k=1                -> 0.00 & 12.60
  Random k=3                -> 0.00 & 11.96
  No instructions (ablation) -> 0.00 & 11.80
  No schema (ablation)      -> 0.00 & 11.80
  Schema only (ablation)    -> 0.00 & 11.37

Test Results:
  ICL                       -> [Gradescope Query EM] & [Gradescope F1]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Compute metrics locally for test | Submit to Gradescope | N/A (assignment design) | Cannot compute test metrics locally |
| Generic template LLM table | Customized with actual experiments | This phase | Report becomes submission-ready |

**Key constraint:** Test metrics require Gradescope submission. The report says "Your test results should match with the results on gradescope."

## Open Questions

1. **Test metrics from Gradescope**
   - What we know: All test prediction files exist and are properly formatted (432 lines each)
   - What's unclear: Whether the student has already submitted to Gradescope and received scores
   - Recommendation: Plan should include a step to submit to Gradescope (or request scores from user), then fill test XX.XX values. If Phase 1/2 changed the best model, test predictions may need regeneration first.

2. **Phase 1/2 dependency -- will T5 outputs change?**
   - What we know: Phase 3 depends on Phase 2. If DPO improves Part 1, test outputs get regenerated.
   - What's unclear: Whether existing `t5_ft_test.sql` is from the final best model or might be replaced.
   - Recommendation: Plan should accommodate using whatever test files exist after Phase 2 completes.

3. **ICL plot scope -- random only or include BM25?**
   - What we know: Assignment says "prompts and examples should correspond to ones described in ICL subsection." The ICL subsection describes k-shot prompting generally.
   - What's unclear: Whether BM25 should be on the same plot since it's a different example selection strategy.
   - Recommendation: Plot both random and BM25 as separate series. This is more informative and the assignment doesn't restrict it.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4.4 (in requirements.txt) |
| Config file | None detected in project root |
| Quick run command | `python3 evaluate.py -ps results/t5_ft_dev.sql -pr records/t5_ft_dev.pkl -ds data/dev.sql -dr records/ground_truth_dev.pkl` |
| Full suite command | Run evaluate.py for all 3 parts (dev) |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RPT-01 | T5 FT test metrics computed | manual-only | Submit to Gradescope | N/A |
| RPT-02 | T5 SCR test metrics computed | manual-only | Submit to Gradescope | N/A |
| RPT-03 | LLM test metrics computed | manual-only | Submit to Gradescope | N/A |
| RPT-04 | All XX.XX replaced | smoke | `grep -c 'XX.XX' report/report.tex` returns 0 | N/A |
| VIZ-01 | ICL plot exists | smoke | `test -f media/icl_sensitivity.pdf` | Not yet |
| VIZ-02 | Plot in report | smoke | `grep 'icl_sensitivity' report/report.tex` returns match | Not yet |

### Sampling Rate
- **Per task commit:** Verify `grep 'XX.XX' report/report.tex` count decreases
- **Per wave merge:** All placeholder checks pass
- **Phase gate:** Zero XX.XX in report, ICL plot file exists, `\includegraphics{media/icl_sensitivity}` in report.tex

### Wave 0 Gaps
None -- no test infrastructure needed. This phase is about data collection, plotting, and LaTeX editing. Verification is via simple file existence and grep checks.

## Sources

### Primary (HIGH confidence)
- `report/report.tex` - Direct inspection of all XX.XX placeholders (9 locations)
- `results/*_log.txt` - Cached dev metrics from all LLM experiments
- `experiments/llm-prompting-experiments.md` - Complete ICL experiment results
- `evaluate.py` + `utils.py` - Metric computation pipeline code
- `data/` directory listing - Confirmed NO test.sql or ground_truth_test.pkl

### Secondary (MEDIUM confidence)
- `requirements.txt` - matplotlib 3.8.0, seaborn 0.13.2 listed as project dependencies
- Report template instructions (lines 417-425, 517) - Assignment requirements for tables and plots

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - matplotlib/seaborn in requirements.txt, standard Python plotting
- Architecture: HIGH - All data sources verified, file existence confirmed, metrics extracted from logs
- Pitfalls: HIGH - Test ground truth absence verified by direct file listing, placeholder locations confirmed

**Research date:** 2026-03-13
**Valid until:** 2026-03-20 (stable -- this is a one-shot assignment submission)
