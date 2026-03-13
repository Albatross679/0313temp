#!/usr/bin/env bash
# Run all LLM prompting experiments sequentially.
# Each experiment uses prompting.py (root entry point) which auto-acquires GPU lock.
# Results are logged to output/llm_experiments.log

set -euo pipefail
cd /home/coder/nlp_Assignment3

# Ensure correct HuggingFace cache directory
export HF_HOME=/home/coder/.cache/huggingface

LOG="output/llm_experiments.log"
mkdir -p output results records

echo "========================================" | tee -a "$LOG"
echo "LLM Prompting Experiments" | tee -a "$LOG"
echo "Started: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" | tee -a "$LOG"
echo "========================================" | tee -a "$LOG"

# Helper: run experiment and log timing
run_exp() {
    local name="$1"
    shift
    echo "" | tee -a "$LOG"
    echo "--- Experiment: $name ---" | tee -a "$LOG"
    echo "Command: python3 $@" | tee -a "$LOG"
    echo "Start: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" | tee -a "$LOG"
    local t0=$(date +%s)
    python3 "$@" 2>&1 | tee -a "$LOG"
    local t1=$(date +%s)
    echo "End: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" | tee -a "$LOG"
    echo "Duration: $(( t1 - t0 ))s" | tee -a "$LOG"
    echo "--- Done: $name ---" | tee -a "$LOG"
}

# ── Step 1: k-shot experiments (dev only) ──────────────────────────────
# k=0 already run -- skip if results exist
if [ -f results/llm_k0_dev.sql ]; then
    echo "SKIP k=0: results/llm_k0_dev.sql already exists" | tee -a "$LOG"
else
    run_exp "k=0 (dev)" prompting.py --shot 0 --model gemma --experiment_name k0 --eval_splits dev
fi

run_exp "k=1 (dev)" prompting.py --shot 1 --model gemma --experiment_name k1 --eval_splits dev
run_exp "k=3 (dev)" prompting.py --shot 3 --model gemma --experiment_name k3 --eval_splits dev

# ── Step 2: BM25 comparison at k=3 ────────────────────────────────────
run_exp "BM25 k=3 (dev)" prompting.py --shot 3 --model gemma --example_selection bm25 --experiment_name bm25_k3 --eval_splits dev

# ── Step 3: Ablation conditions (dev only) ─────────────────────────────
# Ablation 1: Full prompt = k3 (already run above)
# Ablation 2: No schema
run_exp "Ablation: no schema (dev)" prompting.py --shot 3 --model gemma --include_schema false --experiment_name abl_no_schema --eval_splits dev
# Ablation 3: No instructions
run_exp "Ablation: no instructions (dev)" prompting.py --shot 3 --model gemma --include_instructions false --experiment_name abl_no_instr --eval_splits dev
# Ablation 4: No examples (0-shot) = k0 (already run above)
# Ablation 5: Schema only (no instructions, no examples)
run_exp "Ablation: schema only (dev)" prompting.py --shot 0 --model gemma --include_instructions false --experiment_name abl_schema_only --eval_splits dev

echo "" | tee -a "$LOG"
echo "========================================" | tee -a "$LOG"
echo "All dev experiments complete." | tee -a "$LOG"
echo "Finished: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" | tee -a "$LOG"
echo "========================================" | tee -a "$LOG"

# ── Step 4: Evaluate all results ───────────────────────────────────────
echo "" | tee -a "$LOG"
echo "=== RESULTS SUMMARY ===" | tee -a "$LOG"

evaluate() {
    local name="$1"
    local sql_path="$2"
    local pkl_path="$3"
    echo "" | tee -a "$LOG"
    echo "$name:" | tee -a "$LOG"
    python3 evaluate.py \
        --predicted_sql "$sql_path" \
        --predicted_records "$pkl_path" \
        --development_sql data/dev.sql \
        --development_records records/ground_truth_dev.pkl 2>&1 | tee -a "$LOG"
}

evaluate "k=0 (random)" results/llm_k0_dev.sql records/llm_k0_dev.pkl
evaluate "k=1 (random)" results/llm_k1_dev.sql records/llm_k1_dev.pkl
evaluate "k=3 (random)" results/llm_k3_dev.sql records/llm_k3_dev.pkl
evaluate "BM25 k=3" results/llm_bm25_k3_dev.sql records/llm_bm25_k3_dev.pkl
evaluate "Ablation: no schema" results/llm_abl_no_schema_dev.sql records/llm_abl_no_schema_dev.pkl
evaluate "Ablation: no instructions" results/llm_abl_no_instr_dev.sql records/llm_abl_no_instr_dev.pkl
evaluate "Ablation: schema only" results/llm_abl_schema_only_dev.sql records/llm_abl_schema_only_dev.pkl

echo "" | tee -a "$LOG"
echo "Review results above to determine best config for final test run." | tee -a "$LOG"
echo "Then run the final config with part3/train.py to produce llm_test.sql" | tee -a "$LOG"
