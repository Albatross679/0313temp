#!/bin/bash
# Run all 4 LoRA configs sequentially with fixed merge_and_unload checkpoints.
# Phase 01.2 Plan 01 Task 2.

set -e
cd /home/coder/nlp_Assignment3
export PYTHONPATH=/home/coder/nlp_Assignment3
export HF_HOME=/home/coder/.cache/huggingface
export WANDB_API_KEY=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

CONFIGS=(
    "T5FineTuneConfig_lora_v1"
    "T5FineTuneConfig_lora_v2"
    "T5FineTuneConfig_lora_v3"
    "T5FineTuneConfig_lora_freeze_enc"
)

rm -f STOP

for cfg in "${CONFIGS[@]}"; do
    if [ -f STOP ]; then
        echo "STOP file detected -- halting before $cfg"
        break
    fi
    echo ""
    echo "========================================"
    echo "  Starting: $cfg"
    echo "  $(date)"
    echo "========================================"
    python3 part1/train.py --config "$cfg" || {
        echo "  ERROR: $cfg exited with code $? at $(date)"
    }
    echo "  Finished: $cfg at $(date)"
    # Cleanup VRAM between runs
    python3 -c "import torch; torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats()" 2>/dev/null || true
done

echo ""
echo "All 4 LoRA configs completed at $(date)"
