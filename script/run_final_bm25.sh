#!/usr/bin/env bash
# Run the final BM25 k=3 experiment on both dev and test splits.
set -euo pipefail
cd /home/coder/nlp_Assignment3
export HF_HOME=/home/coder/.cache/huggingface
echo "Starting final BM25 k=3 run at $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "Working directory: $(pwd)"
PYTHONDONTWRITEBYTECODE=1 python3 -m part3.train --config PromptingConfig_bm25
echo "Final run completed at $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
