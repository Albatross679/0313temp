"""Run all LLM prompting experiments efficiently (load model once).

Loads Gemma 2B once, then runs k-shot variants, BM25 comparison, and ablation
experiments on the dev set. Finally, runs the best config on test to produce
the submission files.

Usage:
    HF_HOME=/home/coder/.cache/huggingface python run_llm_experiments.py
"""

import os
import sys
import json
import time
import random
import shutil

import torch
from utils import set_random_seeds, save_queries_and_records, compute_metrics
from prompting import create_prompt, exp_kshot, eval_outputs
from prompting_utils import read_schema
from load_data import load_prompting_data
from part3.model import initialize_model_and_tokenizer
from part3.data import build_bm25_index


def run_experiment(name, tokenizer, model, eval_x, eval_y, shot, schema_text,
                   examples=None, include_instructions=True, include_schema=True,
                   bm25_index=None, example_selection="random",
                   train_x=None, train_y=None, eval_split="dev",
                   max_new_tokens=128):
    """Run a single experiment and return metrics."""
    print(f"\n{'='*70}")
    print(f"  Experiment: {name} [{eval_split}] (k={shot}, sel={example_selection})")
    print(f"  schema={include_schema}, instructions={include_instructions}")
    print(f"{'='*70}")
    sys.stdout.flush()

    t0 = time.time()
    raw_outputs, extracted_queries = exp_kshot(
        tokenizer, model, eval_x, shot,
        schema_text=schema_text,
        examples=examples,
        include_instructions=include_instructions,
        include_schema=include_schema,
        bm25_index=bm25_index,
        example_selection=example_selection,
        train_x=train_x,
        train_y=train_y,
        max_new_tokens=max_new_tokens,
    )
    elapsed = time.time() - t0
    print(f"\nInference time: {elapsed:.1f}s ({elapsed/len(eval_x):.2f}s/example)")
    sys.stdout.flush()

    gt_sql_path = f"data/{eval_split}.sql"
    gt_record_path = f"records/ground_truth_{eval_split}.pkl"
    model_sql_path = f"results/llm_{name}_{eval_split}.sql"
    model_record_path = f"records/llm_{name}_{eval_split}.pkl"

    metrics = {}
    if eval_y is not None:
        sql_em, record_em, record_f1, model_error_msgs, error_rate = eval_outputs(
            extracted_queries,
            gt_sql_path, model_sql_path,
            gt_record_path, model_record_path,
        )
        metrics = {
            "name": name,
            "split": eval_split,
            "shot": shot,
            "example_selection": example_selection,
            "include_schema": include_schema,
            "include_instructions": include_instructions,
            "record_f1": record_f1,
            "record_em": record_em,
            "sql_em": sql_em,
            "error_rate": error_rate,
            "inference_time_s": elapsed,
        }
        print(f"Record F1: {record_f1:.4f}, Record EM: {record_em:.4f}, SQL EM: {sql_em:.4f}")
        print(f"Error rate: {error_rate*100:.1f}%")
    else:
        # Test split -- save predictions only
        save_queries_and_records(extracted_queries, model_sql_path, model_record_path)
        metrics = {
            "name": name,
            "split": eval_split,
            "shot": shot,
            "example_selection": example_selection,
            "include_schema": include_schema,
            "include_instructions": include_instructions,
            "inference_time_s": elapsed,
        }
        print(f"Test predictions saved to {model_sql_path}")

    sys.stdout.flush()
    return metrics


def main():
    overall_t0 = time.time()
    set_random_seeds(42)

    # Load data
    print("Loading data...")
    train_x, train_y, dev_x, dev_y, test_x = load_prompting_data("data")
    schema_text = read_schema("data/flight_database.schema")
    print(f"Data: {len(train_x)} train, {len(dev_x)} dev, {len(test_x)} test")

    # Build BM25 index
    print("Building BM25 index...")
    bm25_index = build_bm25_index(train_x)

    # Load model once
    print("Loading Gemma 2B...")
    sys.stdout.flush()
    tokenizer, model = initialize_model_and_tokenizer("gemma", quantize=False)
    print("Model loaded.")
    sys.stdout.flush()

    all_results = []

    # ── Step 1: k=0 zero-shot (fast ~10min) ──────────────────────────────
    # Also serves as ablation "no examples" condition
    set_random_seeds(42)
    metrics = run_experiment(
        "k0", tokenizer, model, dev_x, dev_y,
        shot=0, schema_text=schema_text,
        include_instructions=True, include_schema=True,
        eval_split="dev",
    )
    all_results.append(metrics)

    # ── Step 2: Ablation - schema only (k=0, no instructions) (~10min) ───
    set_random_seeds(42)
    metrics = run_experiment(
        "abl_schema_only", tokenizer, model, dev_x, dev_y,
        shot=0, schema_text=schema_text,
        include_instructions=False, include_schema=True,
        eval_split="dev",
    )
    all_results.append(metrics)

    # ── Step 3: k=3 random (full prompt - ablation baseline) (~90min) ────
    set_random_seeds(42)
    examples_3 = random.sample(list(zip(train_x, train_y)), 3)
    metrics = run_experiment(
        "k3", tokenizer, model, dev_x, dev_y,
        shot=3, schema_text=schema_text,
        examples=examples_3,
        include_instructions=True, include_schema=True,
        eval_split="dev",
    )
    all_results.append(metrics)

    # ── Step 4: k=3 BM25 (~90min) ────────────────────────────────────────
    set_random_seeds(42)
    metrics = run_experiment(
        "bm25_k3", tokenizer, model, dev_x, dev_y,
        shot=3, schema_text=schema_text,
        bm25_index=bm25_index,
        example_selection="bm25",
        train_x=train_x, train_y=train_y,
        include_instructions=True, include_schema=True,
        eval_split="dev",
    )
    all_results.append(metrics)

    # ── Step 5: Ablation - no schema (k=3 random, no schema) ─────────────
    # Should be FASTER since no schema in prompt = shorter prompt
    set_random_seeds(42)
    examples_3_ns = random.sample(list(zip(train_x, train_y)), 3)
    metrics = run_experiment(
        "abl_no_schema", tokenizer, model, dev_x, dev_y,
        shot=3, schema_text=schema_text,
        examples=examples_3_ns,
        include_instructions=True, include_schema=False,
        eval_split="dev",
    )
    all_results.append(metrics)

    # ── Step 6: Ablation - no instructions (k=3 random, no instr) ────────
    set_random_seeds(42)
    examples_3_ni = random.sample(list(zip(train_x, train_y)), 3)
    metrics = run_experiment(
        "abl_no_instr", tokenizer, model, dev_x, dev_y,
        shot=3, schema_text=schema_text,
        examples=examples_3_ni,
        include_instructions=False, include_schema=True,
        eval_split="dev",
    )
    all_results.append(metrics)

    # ── Step 7: k=1 random (for k-shot comparison) ───────────────────────
    set_random_seeds(42)
    examples_1 = random.sample(list(zip(train_x, train_y)), 1)
    metrics = run_experiment(
        "k1", tokenizer, model, dev_x, dev_y,
        shot=1, schema_text=schema_text,
        examples=examples_1,
        include_instructions=True, include_schema=True,
        eval_split="dev",
    )
    all_results.append(metrics)

    # ── Summary table ────────────────────────────────────────────────────
    print(f"\n{'='*90}")
    print(f"  RESULTS SUMMARY (DEV SET)")
    print(f"{'='*90}")
    print(f"{'Name':<25} {'k':>3} {'Selection':<8} {'Schema':>6} {'Instr':>6} {'F1':>8} {'EM':>8} {'SQL_EM':>8} {'Err%':>6}")
    print("-"*90)
    for r in all_results:
        if "record_f1" in r:
            print(f"{r['name']:<25} {r['shot']:>3} {r['example_selection']:<8} "
                  f"{'Y' if r['include_schema'] else 'N':>6} "
                  f"{'Y' if r['include_instructions'] else 'N':>6} "
                  f"{r['record_f1']:.4f}  {r['record_em']:.4f}  {r['sql_em']:.4f}  {r['error_rate']*100:>5.1f}")
    sys.stdout.flush()

    # ── Step 8: Determine best config ────────────────────────────────────
    k3_random = next((r for r in all_results if r["name"] == "k3"), None)
    k3_bm25 = next((r for r in all_results if r["name"] == "bm25_k3"), None)

    if k3_random and k3_bm25:
        print(f"\n  k=3 Random F1: {k3_random['record_f1']:.4f}")
        print(f"  k=3 BM25   F1: {k3_bm25['record_f1']:.4f}")
        use_bm25 = k3_bm25["record_f1"] > k3_random["record_f1"]
        best_strategy = "bm25" if use_bm25 else "random"
        best_name = "bm25_k3" if use_bm25 else "k3"
        print(f"  Best strategy: {best_strategy}")
    else:
        use_bm25 = False
        best_strategy = "random"
        best_name = "k3"
        print("  Defaulting to random strategy")
    sys.stdout.flush()

    # ── Step 9: Copy best dev results to canonical names ─────────────────
    # Reuse the dev results from the best experiment (no need to re-run)
    best_dev_sql = f"results/llm_{best_name}_dev.sql"
    best_dev_pkl = f"records/llm_{best_name}_dev.pkl"
    if os.path.exists(best_dev_sql):
        shutil.copy2(best_dev_sql, "results/llm_dev.sql")
        print(f"Copied {best_dev_sql} -> results/llm_dev.sql")
    if os.path.exists(best_dev_pkl):
        shutil.copy2(best_dev_pkl, "records/llm_dev.pkl")
        print(f"Copied {best_dev_pkl} -> records/llm_dev.pkl")

    # ── Step 10: Run best config on test set ─────────────────────────────
    print(f"\n{'='*70}")
    print(f"  FINAL RUN: k=3 with {best_strategy} on test set")
    print(f"{'='*70}")
    sys.stdout.flush()

    set_random_seeds(42)
    if use_bm25:
        final_examples = None
        final_bm25 = bm25_index
        final_sel = "bm25"
    else:
        final_examples = random.sample(list(zip(train_x, train_y)), 3)
        final_bm25 = None
        final_sel = "random"

    metrics_test = run_experiment(
        "final", tokenizer, model, test_x, None,
        shot=3, schema_text=schema_text,
        examples=final_examples,
        bm25_index=final_bm25,
        example_selection=final_sel,
        train_x=train_x, train_y=train_y,
        include_instructions=True, include_schema=True,
        eval_split="test",
    )
    all_results.append(metrics_test)

    # Copy test results to canonical names
    if os.path.exists("results/llm_final_test.sql"):
        shutil.copy2("results/llm_final_test.sql", "results/llm_test.sql")
        print(f"Copied results/llm_final_test.sql -> results/llm_test.sql")
    if os.path.exists("records/llm_final_test.pkl"):
        shutil.copy2("records/llm_final_test.pkl", "records/llm_test.pkl")
        print(f"Copied records/llm_final_test.pkl -> records/llm_test.pkl")

    # ── Save all results to JSON ─────────────────────────────────────────
    results_path = "results/llm_experiment_results.json"
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nAll results saved to {results_path}")

    # ── Final validation ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  VALIDATION")
    print(f"{'='*70}")
    for path in ["results/llm_test.sql", "records/llm_test.pkl",
                  "results/llm_dev.sql", "records/llm_dev.pkl"]:
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  OK: {path} ({size} bytes)")
        else:
            print(f"  MISSING: {path}")

    if os.path.exists("results/llm_test.sql"):
        with open("results/llm_test.sql") as f:
            n_lines = len(f.readlines())
        print(f"  llm_test.sql line count: {n_lines} (expected 432)")

    if os.path.exists("results/llm_dev.sql"):
        with open("results/llm_dev.sql") as f:
            n_lines = len(f.readlines())
        print(f"  llm_dev.sql line count: {n_lines} (expected 466)")

    overall_elapsed = time.time() - overall_t0
    print(f"\nTotal time: {overall_elapsed/60:.1f} minutes ({overall_elapsed/3600:.1f} hours)")
    print("Done!")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
