#!/usr/bin/env python3
"""
Analyze prediction errors across T5 fine-tuned, T5 from-scratch, and LLM (Gemma 2B).

Classifies every dev-set query (466 total) into exactly ONE of 6 mutually exclusive
categories per model, using priority-based assignment:

  1. Correct (exact SQL match)
  2. Correct records (different SQL, same execution result)
  3. Missing comparison operator (T5 SentencePiece artifact)
  4. Query truncation / incomplete generation
  5. Wrong table/column reference
  6. Semantic error: wrong JOIN structure or wrong predicate values

Usage:
    python3 script/error_analysis.py
"""

import pickle
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

GT_SQL_PATH = PROJECT_ROOT / "data" / "dev.sql"
GT_NL_PATH = PROJECT_ROOT / "data" / "dev.nl"
GT_PKL_PATH = PROJECT_ROOT / "records" / "ground_truth_dev.pkl"

MODELS = {
    "T5 Fine-tuned": {
        "sql": PROJECT_ROOT / "results" / "t5_ft_dev.sql",
        "pkl": PROJECT_ROOT / "records" / "t5_ft_dev.pkl",
        "short": "T5-FT",
    },
    "T5 From Scratch": {
        "sql": PROJECT_ROOT / "results" / "t5_scr_dev.sql",
        "pkl": PROJECT_ROOT / "records" / "t5_scr_dev.pkl",
        "short": "T5-Scr",
    },
    "ICL (Gemma 2B)": {
        "sql": PROJECT_ROOT / "results" / "llm_dev.sql",
        "pkl": PROJECT_ROOT / "records" / "llm_dev.pkl",
        "short": "ICL",
    },
}

# Number of dev queries
TOTAL = 466

# Category labels
CAT_CORRECT_SQL = "Correct (exact SQL match)"
CAT_CORRECT_RECORDS = "Correct (different SQL, same records)"
CAT_MISSING_OPERATOR = "Missing comparison operator"
CAT_TRUNCATION = "Query truncation / incomplete"
CAT_WRONG_REFERENCE = "Wrong table/column reference"
CAT_SEMANTIC = "Semantic error (wrong JOIN/predicate)"
CAT_OTHER_EXEC = "Other execution error"

# Priority order for classification (higher priority = checked first)
CATEGORY_ORDER = [
    CAT_CORRECT_SQL,
    CAT_CORRECT_RECORDS,
    CAT_TRUNCATION,
    CAT_MISSING_OPERATOR,
    CAT_WRONG_REFERENCE,
    CAT_OTHER_EXEC,
    CAT_SEMANTIC,
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_lines(path: Path) -> list[str]:
    """Load a text file as a list of stripped lines."""
    with open(path) as f:
        return [line.strip() for line in f]


def load_pkl(path: Path) -> tuple[list, list]:
    """Load a pickle file returning (records_list, errors_list)."""
    with open(path, "rb") as f:
        return pickle.load(f)


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------
def has_missing_operator(pred_sql: str) -> bool:
    """Detect T5 SentencePiece artifact: column name followed by 2+ spaces then a number.

    Pattern: `column_name  1800` where `< 1800` should be.
    Also catches `column_name  = 1800` (double space before equals).
    """
    # Match: word.word or word followed by 2+ spaces then a digit
    return bool(re.search(r"\w+(?:\.\w+)?\s{2,}\d+", pred_sql))


def is_truncated(pred_sql: str) -> bool:
    """Detect truncated / incomplete query generation.

    Indicators:
    - Very short SQL (< 60 chars) -- likely just SELECT fragment
    - Missing FROM clause entirely
    - Only SELECT keyword present with no other SQL keywords
    """
    sql_upper = pred_sql.upper().strip()

    # Very short query (just a SELECT fragment)
    if len(pred_sql.strip()) < 60:
        return True

    # Has SELECT but no FROM
    if "SELECT" in sql_upper and "FROM" not in sql_upper:
        return True

    return False


def is_wrong_reference(error_msg: str) -> bool:
    """Detect wrong table/column reference from error message."""
    e = error_msg.lower()
    return "no such column" in e or "no such table" in e


def extract_from_tables(sql: str) -> set[str]:
    """Extract table names from the FROM clause of a SQL query."""
    # Get text between FROM and WHERE (or end of string)
    from_match = re.search(r"\bFROM\s+(.*?)(?:\bWHERE\b|$)", sql, re.IGNORECASE | re.DOTALL)
    if not from_match:
        return set()
    from_clause = from_match.group(1)
    # Extract table names (words before aliases)
    tables = set()
    # Match patterns like: table_name alias_name or table_name AS alias_name
    for match in re.finditer(r"\b([a-z_]+)\s+(?:AS\s+)?([a-z_]+_\d+|\b[a-z_]+\b)", from_clause, re.IGNORECASE):
        tables.add(match.group(1).lower())
    return tables


# ---------------------------------------------------------------------------
# Main classification function
# ---------------------------------------------------------------------------
def classify_query(
    idx: int,
    gt_sql: str,
    pred_sql: str,
    gt_records: list,
    pred_records: list,
    error_msg: str,
) -> str:
    """Classify a single prediction into exactly one category.

    Priority order:
    1. Correct SQL match
    2. Correct records (different SQL, same result)
    3. Truncation (checked before missing operator -- LLM truncation dominates)
    4. Missing comparison operator (T5 SentencePiece artifact)
    5. Wrong table/column reference (execution error)
    6. Other execution error
    7. Semantic error (executes but wrong results)
    """
    # 1. Exact SQL match
    if pred_sql.strip() == gt_sql.strip():
        return CAT_CORRECT_SQL

    # 2. Check if records match (for queries that executed successfully)
    if not error_msg:
        gt_set = set(map(tuple, gt_records)) if gt_records else set()
        pred_set = set(map(tuple, pred_records)) if pred_records else set()
        if gt_set == pred_set:
            return CAT_CORRECT_RECORDS

    # 3. Truncation (must check before wrong reference -- LLM truncation causes
    #    "no such column" errors that should be classified as truncation)
    if is_truncated(pred_sql):
        return CAT_TRUNCATION

    # 4. Missing comparison operator (T5 SentencePiece artifact)
    if has_missing_operator(pred_sql):
        return CAT_MISSING_OPERATOR

    # 5. Wrong table/column reference (execution error, not from truncation)
    if error_msg and is_wrong_reference(error_msg):
        return CAT_WRONG_REFERENCE

    # 6. Other execution error (syntax, ambiguous, aggregate misuse, etc.)
    if error_msg:
        return CAT_OTHER_EXEC

    # 7. Semantic error -- query executes but returns wrong records
    return CAT_SEMANTIC


# ---------------------------------------------------------------------------
# Example selection
# ---------------------------------------------------------------------------
def select_best_example(examples: list[dict], category: str) -> dict | None:
    """Select the most illustrative example for a category.

    Prefers shorter NL inputs that clearly show the error pattern.
    """
    if not examples:
        return None

    # Sort by NL length (shorter = clearer illustration)
    sorted_ex = sorted(examples, key=lambda x: len(x["nl"]))

    # For missing operator, prefer examples that clearly show the double-space
    if category == CAT_MISSING_OPERATOR:
        for ex in sorted_ex:
            if re.search(r"time\s{2,}\d+", ex["pred_sql"]):
                return ex

    # For truncation, prefer examples with very short pred
    if category == CAT_TRUNCATION:
        sorted_ex = sorted(examples, key=lambda x: len(x["pred_sql"]))

    return sorted_ex[0]


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------
def main():
    # Load ground truth
    gt_sqls = load_lines(GT_SQL_PATH)
    nl_inputs = load_lines(GT_NL_PATH)
    gt_records_list, gt_errors_list = load_pkl(GT_PKL_PATH)

    assert len(gt_sqls) == TOTAL, f"Expected {TOTAL} GT SQL queries, got {len(gt_sqls)}"
    assert len(nl_inputs) == TOTAL, f"Expected {TOTAL} NL inputs, got {len(nl_inputs)}"

    print(f"Dev set size: {TOTAL} queries")
    print(f"{'=' * 80}\n")

    # Store all results for cross-model summary
    all_results = {}

    for model_name, model_info in MODELS.items():
        short = model_info["short"]

        # Load predictions
        pred_sqls = load_lines(model_info["sql"])
        pred_records_list, pred_errors_list = load_pkl(model_info["pkl"])

        assert len(pred_sqls) == TOTAL, f"{model_name}: Expected {TOTAL} predictions, got {len(pred_sqls)}"

        # Classify each query
        categories = []
        examples_by_cat: dict[str, list[dict]] = defaultdict(list)

        for i in range(TOTAL):
            # Handle records: gt_records may be empty list if GT query also errors
            gt_recs = gt_records_list[i] if gt_records_list[i] else []
            pred_recs = pred_records_list[i] if pred_records_list[i] else []
            error = pred_errors_list[i] if pred_errors_list[i] else ""

            cat = classify_query(i, gt_sqls[i], pred_sqls[i], gt_recs, pred_recs, error)
            categories.append(cat)

            # Collect examples (limit to 5 per category to save memory)
            if len(examples_by_cat[cat]) < 5:
                examples_by_cat[cat].append({
                    "idx": i,
                    "nl": nl_inputs[i],
                    "gt_sql": gt_sqls[i],
                    "pred_sql": pred_sqls[i],
                    "error": error,
                })

        # Count
        counts = Counter(categories)
        total_classified = sum(counts.values())

        print(f"{'=' * 80}")
        print(f"=== {model_name} ({short}) ===")
        print(f"{'=' * 80}")

        for cat in CATEGORY_ORDER:
            c = counts.get(cat, 0)
            pct = 100 * c / TOTAL
            print(f"  {cat}: {c}/{TOTAL} ({pct:.1f}%)")

        # Verify total
        print(f"\n  Total classified: {total_classified}/{TOTAL}", end="")
        if total_classified == TOTAL:
            print(" [OK]")
        else:
            print(" [MISMATCH!]")

        # Print best examples per category
        print(f"\n  --- Concrete Examples ---")
        for cat in CATEGORY_ORDER:
            if cat in (CAT_CORRECT_SQL, CAT_CORRECT_RECORDS):
                continue  # Skip correct categories for examples
            ex = select_best_example(examples_by_cat.get(cat, []), cat)
            if ex:
                print(f"\n  [{cat}]")
                print(f"    NL: {ex['nl'][:100]}")
                print(f"    GT: {ex['gt_sql'][:120]}...")
                print(f"    Pred: {ex['pred_sql'][:120]}...")
                if ex["error"]:
                    print(f"    Error: {ex['error'][:100]}")

        print()
        all_results[model_name] = {"counts": counts, "short": short, "examples": examples_by_cat}

    # ---------------------------------------------------------------------------
    # Cross-model summary table
    # ---------------------------------------------------------------------------
    print(f"{'=' * 80}")
    print("CROSS-MODEL SUMMARY")
    print(f"{'=' * 80}")

    # Header
    model_shorts = [m["short"] for m in MODELS.values()]
    header = f"{'Category':<45s}" + "".join(f"{s:>12s}" for s in model_shorts)
    print(header)
    print("-" * len(header))

    for cat in CATEGORY_ORDER:
        row = f"{cat:<45s}"
        for model_name in MODELS:
            c = all_results[model_name]["counts"].get(cat, 0)
            row += f"{c:>5d}/{TOTAL:<5d}"
        print(row)

    # Print totals row
    print("-" * len(header))
    row = f"{'TOTAL':<45s}"
    for model_name in MODELS:
        t = sum(all_results[model_name]["counts"].values())
        row += f"{t:>5d}/{TOTAL:<5d}"
    print(row)

    # ---------------------------------------------------------------------------
    # Report-ready statistics (for LaTeX table)
    # ---------------------------------------------------------------------------
    print(f"\n{'=' * 80}")
    print("REPORT-READY STATISTICS (for LaTeX tab:qualitative)")
    print(f"{'=' * 80}")

    report_cats = [
        (CAT_MISSING_OPERATOR, "Missing comparison operator"),
        (CAT_TRUNCATION, "Query truncation / incomplete generation"),
        (CAT_WRONG_REFERENCE, "Wrong table/column reference"),
        (CAT_SEMANTIC, "Wrong JOIN structure / wrong predicate values"),
        (CAT_OTHER_EXEC, "Other execution error"),
    ]

    for cat, label in report_cats:
        print(f"\n  {label}:")
        for model_name, result in all_results.items():
            c = result["counts"].get(cat, 0)
            short = result["short"]
            if c > 0:
                print(f"    {short}: {c}/{TOTAL} ({100*c/TOTAL:.1f}%)")

    # ---------------------------------------------------------------------------
    # Best examples for report (one per category, cross-model)
    # ---------------------------------------------------------------------------
    print(f"\n{'=' * 80}")
    print("BEST EXAMPLES FOR REPORT")
    print(f"{'=' * 80}")

    for cat, label in report_cats:
        print(f"\n--- {label} ---")
        # Find model with most examples in this category
        best_model = None
        best_count = 0
        for model_name, result in all_results.items():
            c = result["counts"].get(cat, 0)
            if c > best_count:
                best_count = c
                best_model = model_name
        if best_model and best_count > 0:
            ex = select_best_example(all_results[best_model]["examples"].get(cat, []), cat)
            if ex:
                print(f"  Model: {best_model}")
                print(f"  NL: {ex['nl']}")
                print(f"  GT SQL: {ex['gt_sql'][:200]}")
                print(f"  Pred SQL: {ex['pred_sql'][:200]}")
                if ex["error"]:
                    print(f"  Error: {ex['error'][:150]}")


if __name__ == "__main__":
    main()
