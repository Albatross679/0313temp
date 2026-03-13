#!/usr/bin/env python3
"""Analyze prediction errors for T5 fine-tuned, T5 from-scratch, and LLM models."""

import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

DB_PATH = Path("data/flight_database.db")
GT_SQL = Path("data/dev.sql")
NL_INPUT = Path("data/dev.nl")
PRED_FILES = {
    "t5_ft": Path("results/t5_ft_dev.sql"),
    "t5_scr": Path("results/t5_scr_dev.sql"),
    "llm_k0": Path("results/llm_k0_dev.sql"),
    "llm_k1": Path("results/llm_k1_dev.sql"),
}


def load_lines(path):
    return [line.strip() for line in open(path)]


def try_execute(conn, sql):
    """Try to execute SQL, return (success, result_or_error)."""
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        return True, rows
    except Exception as e:
        return False, str(e)


def classify_exec_error(error_msg):
    """Classify a SQL execution error."""
    e = error_msg.lower()
    if "no such table" in e:
        return "no_such_table"
    if "no such column" in e:
        return "no_such_column"
    if "syntax error" in e or "near" in e:
        return "syntax_error"
    if "ambiguous" in e:
        return "ambiguous_column"
    if "misuse of aggregate" in e:
        return "aggregate_misuse"
    return "other_exec_error"


def analyze_structural(pred, gt):
    """Analyze structural differences between prediction and ground truth."""
    issues = []

    # Check SQL dialect: JOIN vs comma-separated FROM
    pred_has_join = bool(re.search(r'\bJOIN\b', pred, re.IGNORECASE))
    gt_has_join = bool(re.search(r'\bJOIN\b', gt, re.IGNORECASE))
    if pred_has_join and not gt_has_join:
        issues.append("wrong_sql_dialect")

    # Check for SELECT * vs specific columns
    if re.search(r'SELECT\s+\w+\.\*', pred, re.IGNORECASE) and not re.search(r'SELECT\s+\w+\.\*', gt, re.IGNORECASE):
        issues.append("select_star_instead_of_specific")

    # Check for subquery presence
    gt_has_subquery = gt.upper().count("SELECT") > 1
    pred_has_subquery = pred.upper().count("SELECT") > 1
    if gt_has_subquery and not pred_has_subquery:
        issues.append("missing_subquery")
    if not gt_has_subquery and pred_has_subquery:
        issues.append("spurious_subquery")

    # Check for missing operator (e.g., "arrival_time  900" instead of "arrival_time < 900")
    if re.search(r'\w+\s{2,}\d+', pred):
        issues.append("missing_operator")

    # Check for undeclared aliases (aliases used in WHERE but not in FROM)
    from_match = re.search(r'FROM\s+(.*?)(?:WHERE|$)', pred, re.IGNORECASE)
    if from_match:
        from_clause = from_match.group(1)
        # Extract declared aliases
        declared = set(re.findall(r'\b(\w+_\d+)\b', from_clause))
        # Extract aliases used in conditions
        where_match = re.search(r'WHERE\s+(.*)', pred, re.IGNORECASE)
        if where_match:
            where_clause = where_match.group(1)
            used = set(re.findall(r'\b(\w+_\d+)\b', where_clause))
            undeclared = used - declared
            if undeclared:
                issues.append("undeclared_alias")

    # Check for city names vs airport codes
    # Ground truth uses city_name = 'DENVER', LLM might use airport codes like 'DENV'
    gt_cities = set(re.findall(r"city_name\s*=\s*'([^']+)'", gt, re.IGNORECASE))
    pred_cities = set(re.findall(r"city_name\s*=\s*'([^']+)'", pred, re.IGNORECASE))
    if gt_cities and not pred_cities:
        # Pred doesn't use city_name at all — might use airport codes directly
        if re.search(r"(?:from_airport|to_airport|airport)\s*=\s*'[A-Z]{3,4}'", pred, re.IGNORECASE):
            issues.append("airport_code_instead_of_city_name")

    # Check for wrong city name
    if gt_cities and pred_cities and gt_cities != pred_cities:
        issues.append("wrong_city_name")

    # Check for missing FROM tables
    gt_tables = set(re.findall(r'\b(flight|fare|airport_service|city|airport|days|date_day|flight_stop|flight_fare|airline|food_service|ground_service|restriction|equipment_sequence|flight_leg)\b', gt.split('WHERE')[0] if 'WHERE' in gt else gt, re.IGNORECASE))
    pred_tables = set(re.findall(r'\b(flight|fare|airport_service|city|airport|days|date_day|flight_stop|flight_fare|airline|food_service|ground_service|restriction|equipment_sequence|flight_leg)\b', pred.split('WHERE')[0] if 'WHERE' in pred else pred, re.IGNORECASE))
    gt_tables_lower = {t.lower() for t in gt_tables}
    pred_tables_lower = {t.lower() for t in pred_tables}
    missing_tables = gt_tables_lower - pred_tables_lower
    extra_tables = pred_tables_lower - gt_tables_lower
    if missing_tables:
        issues.append("missing_tables")
    if extra_tables:
        issues.append("extra_tables")

    # Check for completely wrong query structure (different SELECT target)
    gt_select = re.search(r'SELECT\s+(.*?)\s+FROM', gt, re.IGNORECASE)
    pred_select = re.search(r'SELECT\s+(.*?)\s+FROM', pred, re.IGNORECASE)
    if gt_select and pred_select:
        gt_sel = gt_select.group(1).strip().lower()
        pred_sel = pred_select.group(1).strip().lower()
        if gt_sel != pred_sel:
            issues.append("wrong_select_target")

    # Check for non-existent columns referenced in pred
    nonexistent_cols = re.findall(r'\b(?:departure_date|day_name|meal_code|connections|arrival_airport|airline_flight)\b', pred, re.IGNORECASE)
    if nonexistent_cols:
        issues.append("hallucinated_columns")

    # Check for wrong date formats or modern SQL features
    if re.search(r"DATE_ADD|NOW\(\)|INTERVAL|LIMIT\s+\d+|ORDER\s+BY.*ASC|ORDER\s+BY.*DESC", pred, re.IGNORECASE):
        issues.append("modern_sql_features")

    # Check query length ratio (truncation indicator)
    if len(pred) < len(gt) * 0.5 and len(gt) > 200:
        issues.append("possible_truncation")

    return issues


def main():
    gt_sqls = load_lines(GT_SQL)
    nl_inputs = load_lines(NL_INPUT)

    conn = sqlite3.connect(str(DB_PATH))

    # First, check ground truth execution
    gt_exec_ok = 0
    for sql in gt_sqls:
        ok, _ = try_execute(conn, sql)
        if ok:
            gt_exec_ok += 1
    print(f"Ground truth: {gt_exec_ok}/{len(gt_sqls)} execute successfully\n")

    for model_name, pred_path in PRED_FILES.items():
        if not pred_path.exists():
            print(f"--- {model_name}: file not found ---\n")
            continue

        pred_sqls = load_lines(pred_path)
        assert len(pred_sqls) == len(gt_sqls), f"{model_name}: {len(pred_sqls)} preds vs {len(gt_sqls)} gt"

        print(f"{'='*80}")
        print(f"MODEL: {model_name}")
        print(f"{'='*80}")

        # Exact match
        exact_matches = sum(1 for p, g in zip(pred_sqls, gt_sqls) if p.strip() == g.strip())
        print(f"Exact match: {exact_matches}/{len(gt_sqls)} ({100*exact_matches/len(gt_sqls):.1f}%)")

        # Execution success
        exec_ok = 0
        exec_errors = Counter()
        exec_error_examples = defaultdict(list)
        for i, (pred, gt, nl) in enumerate(zip(pred_sqls, gt_sqls, nl_inputs)):
            ok, result = try_execute(conn, pred)
            if ok:
                exec_ok += 1
            else:
                err_type = classify_exec_error(result)
                exec_errors[err_type] += 1
                if len(exec_error_examples[err_type]) < 3:
                    exec_error_examples[err_type].append((i, nl, pred[:200], result[:150]))

        print(f"Execution success: {exec_ok}/{len(gt_sqls)} ({100*exec_ok/len(gt_sqls):.1f}%)")
        print(f"Execution errors: {len(gt_sqls) - exec_ok}/{len(gt_sqls)} ({100*(len(gt_sqls)-exec_ok)/len(gt_sqls):.1f}%)")
        if exec_errors:
            print("\n  Execution error breakdown:")
            for err, count in exec_errors.most_common():
                print(f"    {err}: {count}")
                for idx, nl, pred_snip, err_msg in exec_error_examples[err][:2]:
                    print(f"      Example (line {idx+1}): NL: {nl[:80]}")
                    print(f"        Pred: {pred_snip}...")
                    print(f"        Error: {err_msg}")

        # Structural analysis (for all predictions, not just exec errors)
        all_issues = Counter()
        issue_examples = defaultdict(list)
        for i, (pred, gt, nl) in enumerate(zip(pred_sqls, gt_sqls, nl_inputs)):
            issues = analyze_structural(pred, gt)
            for issue in issues:
                all_issues[issue] += 1
                if len(issue_examples[issue]) < 3:
                    issue_examples[issue].append((i, nl, pred[:300], gt[:300]))

        print(f"\n  Structural issues:")
        for issue, count in all_issues.most_common():
            print(f"    {issue}: {count}/{len(gt_sqls)} ({100*count/len(gt_sqls):.1f}%)")
            for idx, nl, pred_snip, gt_snip in issue_examples[issue][:1]:
                print(f"      Example (line {idx+1}): NL: {nl[:80]}")
                print(f"        Pred: {pred_snip[:150]}...")
                print(f"        GT:   {gt_snip[:150]}...")

        # Record-level comparison (execute both and compare results)
        record_match = 0
        record_mismatch = 0
        record_both_fail = 0
        record_pred_fail = 0
        empty_result_when_gt_nonempty = 0
        extra_results = 0
        missing_results = 0

        for pred, gt in zip(pred_sqls, gt_sqls):
            gt_ok, gt_res = try_execute(conn, gt)
            pred_ok, pred_res = try_execute(conn, pred)

            if not gt_ok and not pred_ok:
                record_both_fail += 1
            elif not pred_ok:
                record_pred_fail += 1
            elif not gt_ok:
                pass  # GT fails, can't compare
            else:
                gt_set = set(gt_res)
                pred_set = set(pred_res)
                if gt_set == pred_set:
                    record_match += 1
                else:
                    record_mismatch += 1
                    if len(pred_set) == 0 and len(gt_set) > 0:
                        empty_result_when_gt_nonempty += 1
                    if len(pred_set) > len(gt_set):
                        extra_results += 1
                    if len(pred_set) < len(gt_set) and len(pred_set) > 0:
                        missing_results += 1

        print(f"\n  Record comparison:")
        print(f"    Exact record match: {record_match}/{len(gt_sqls)}")
        print(f"    Record mismatch: {record_mismatch}/{len(gt_sqls)}")
        print(f"    Pred execution failed: {record_pred_fail}/{len(gt_sqls)}")
        print(f"    Both failed: {record_both_fail}/{len(gt_sqls)}")
        print(f"    Empty result (GT non-empty): {empty_result_when_gt_nonempty}")
        print(f"    Extra results: {extra_results}")
        print(f"    Missing results: {missing_results}")

        print()

    conn.close()


if __name__ == "__main__":
    main()
