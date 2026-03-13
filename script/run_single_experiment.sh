#!/usr/bin/env bash
# Run a single LLM prompting experiment with timeout on cleanup.
# Usage: script/run_single_experiment.sh <name> <args...>
# Example: script/run_single_experiment.sh "k=3" --shot 3 --model gemma --experiment_name k3 --eval_splits dev

set -uo pipefail
cd /home/coder/nlp_Assignment3
export HF_HOME=/home/coder/.cache/huggingface

NAME="$1"
shift

LOG="output/llm_experiments.log"
mkdir -p output results records

echo "" | tee -a "$LOG"
echo "--- Experiment: $NAME ---" | tee -a "$LOG"
echo "Command: python3 prompting.py $@" | tee -a "$LOG"
echo "Start: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" | tee -a "$LOG"

T0=$(date +%s)

# Run with a 30-minute timeout
timeout 1800 python3 prompting.py "$@" 2>&1 | tee -a "$LOG"
EXIT_CODE=$?

T1=$(date +%s)
DURATION=$(( T1 - T0 ))
echo "End: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" | tee -a "$LOG"
echo "Duration: ${DURATION}s" | tee -a "$LOG"

if [ $EXIT_CODE -eq 124 ]; then
    echo "WARNING: Experiment timed out (but results may have been saved)" | tee -a "$LOG"
elif [ $EXIT_CODE -ne 0 ]; then
    echo "WARNING: Experiment exited with code $EXIT_CODE" | tee -a "$LOG"
fi

echo "--- Done: $NAME ---" | tee -a "$LOG"
exit 0  # Always exit 0 so caller continues
