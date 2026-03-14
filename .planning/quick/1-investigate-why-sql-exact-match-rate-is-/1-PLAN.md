---
phase: quick-1
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - issues/sql-exact-match-tokenizer-artifact.md
  - knowledge/sql-em-comma-spacing-analysis.md
autonomous: true
requirements: []

must_haves:
  truths:
    - "Root cause of low SQL EM is documented with evidence"
    - "Quantified impact of the tokenizer comma-spacing artifact on all 3 parts"
    - "Actionable fix strategy is documented (post-processing decode output)"
  artifacts:
    - path: "issues/sql-exact-match-tokenizer-artifact.md"
      provides: "Root cause analysis of low SQL EM"
    - path: "knowledge/sql-em-comma-spacing-analysis.md"
      provides: "Quantified analysis with corrected SQL EM numbers"
  key_links: []
---

<objective>
Investigate why SQL exact match (SQL EM) is extremely low (~2-3%) for T5 models despite decent Record F1 (~62%) and Record EM (~59%), and document findings with quantified evidence.

Purpose: SQL EM is a reported metric in the assignment. Understanding whether the low rate is a genuine model deficiency or a measurement artifact is critical for (a) knowing whether to invest effort fixing it, and (b) accurately reporting results in the paper.

Output: Issue doc explaining root cause, knowledge doc with quantified analysis and fix strategy.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@./utils.py (compute_sql_exact_match — line 143-153: pure string equality)
@./results/t5_ft_dev.sql (model predictions)
@./data/dev.sql (ground truth SQL)
@./part1/data.py (T5Dataset — tokenizer decode path)
@./part1/train.py (_generate_predictions — line 217: batch_decode with skip_special_tokens=True)
@./experiments/t5-ft-multi-config-training.md (best config: SQL EM = 0.021)

<investigation_findings>
## Pre-investigation Analysis (already performed during planning)

### Root Cause: T5 SentencePiece Tokenizer Decode Artifact

The ground truth SQL uses ` , ` (space-comma-space) for all comma separators:
```
FROM flight flight_1 , airport airport_1 , city city_1
```

The T5 tokenizer (SentencePiece) tokenizes ` , ` as two tokens: `'▁'` (space) + `','` (comma).
During `batch_decode(outputs, skip_special_tokens=True)`, the `'▁'` before `,` gets collapsed,
producing `', '` (comma-space, no preceding space):
```
FROM flight flight_1, airport airport_1, city city_1
```

`compute_sql_exact_match()` in utils.py does pure string equality (`gt_q == model_q`), so
every query with commas fails — which is virtually all of them.

### Quantified Impact

| Model | Raw SQL EM | After Comma Normalization | Gain |
|-------|-----------|--------------------------|------|
| T5 fine-tune (best) | 0.034 (16/466) | 0.725 (338/466) | +69.1% |
| T5 from scratch | 0.032 (15/466) | 0.504 (235/466) | +47.2% |
| LLM prompting | 0.000 (0/466) | 0.000 (0/466) | 0% (different issue) |

The comma normalization alone accounts for 322 of 450 mismatches for the fine-tuned model.
The remaining 128 are genuine semantic differences (wrong query structure, wrong predicates, etc.).

### Training Data Confirmation
- Training SQL (`data/train.sql`): 22,077 instances of ` , ` (space-comma-space), 0 without-space commas
- Dev SQL (`data/dev.sql`): 2,352 instances of ` , `, 0 without-space commas
- The model correctly LEARNS the ` , ` pattern (tokens include the `'▁'` before `','`)
- The issue is purely in decode — the SentencePiece decode collapses the leading space before punctuation

### Fix: Post-Processing Regex
```python
import re
decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
# Restore space before commas (SentencePiece collapses it)
fixed = [re.sub(r'(?<=[a-zA-Z0-9_)])\s*,\s*', ' , ', s) for s in decoded]
```

This is safe because SQL never uses `, ` without a preceding space in this dataset.
</investigation_findings>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Document root cause and quantified analysis</name>
  <files>issues/sql-exact-match-tokenizer-artifact.md, knowledge/sql-em-comma-spacing-analysis.md</files>
  <action>
    Create two documentation files based on the investigation findings provided in the context above:

    1. **issues/sql-exact-match-tokenizer-artifact.md** — Issue document with:
       - Frontmatter: type=issue, status=investigating, severity=high, subtype=evaluation
       - Root cause: T5 SentencePiece tokenizer `decode()` collapses leading space before punctuation, converting ` , ` to `, `
       - Evidence: tokenizer roundtrip test showing `'▁'` + `','` tokens decode to `', '`
       - Impact: 322/450 "mismatches" in T5 fine-tune are purely cosmetic comma spacing
       - The model IS learning the correct pattern — the decode step destroys it
       - Fix options: (a) post-process decode output with regex, (b) use raw token-to-string conversion
       - Recommendation: Apply regex post-processing in `_generate_predictions()` in `part1/train.py` line 217-218

    2. **knowledge/sql-em-comma-spacing-analysis.md** — Knowledge document with:
       - Full quantified breakdown table for all 3 parts (T5-ft, T5-scratch, LLM)
       - Raw vs normalized SQL EM comparison
       - Note that LLM has 0% even after normalization (different problems — wrong query structure entirely)
       - Discussion: whether SQL EM is a meaningful metric for this task (it penalizes semantically equivalent queries)
       - The 128 remaining semantic mismatches for T5-ft (after comma fix) represent genuine model errors
       - Corrected "true" SQL EM of 72.5% for fine-tuned T5 would be a strong result

    Use proper frontmatter per CLAUDE.md documentation requirements. Include all quantified data from the investigation findings.
  </action>
  <verify>
    <automated>test -f issues/sql-exact-match-tokenizer-artifact.md && test -f knowledge/sql-em-comma-spacing-analysis.md && grep -q "comma" issues/sql-exact-match-tokenizer-artifact.md && grep -q "0.725" knowledge/sql-em-comma-spacing-analysis.md && echo "PASS" || echo "FAIL"</automated>
  </verify>
  <done>Both files exist with complete root cause analysis, quantified impact tables, and actionable fix strategy. The issue correctly identifies T5 SentencePiece decode as the root cause and the knowledge doc provides the corrected SQL EM numbers for all three model approaches.</done>
</task>

</tasks>

<verification>
- Issue document exists with correct frontmatter and root cause explanation
- Knowledge document exists with quantified SQL EM comparison table
- Both files reference the tokenizer decode behavior with specific evidence
- Fix strategy is documented with code example
</verification>

<success_criteria>
- Root cause (SentencePiece decode collapsing space before comma) is clearly documented
- Quantified impact shows T5-ft SQL EM jumps from 3.4% to 72.5% after comma normalization
- Fix strategy (regex post-processing) is documented with code
- LLM's 0% SQL EM is separately explained (not the same issue)
</success_criteria>

<output>
After completion, create `.planning/quick/1-investigate-why-sql-exact-match-rate-is-/1-SUMMARY.md`
</output>
