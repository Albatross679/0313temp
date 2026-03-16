#!/usr/bin/env bash
# Pull model weights and checkpoints from Backblaze B2
# Usage: ./script/b2-pull.sh
#
# Requires: B2_APPLICATION_KEY_ID and B2_APPLICATION_KEY env vars

set -euo pipefail

BUCKET="mlworkflow"

# Verify B2 credentials
if [[ -z "${B2_APPLICATION_KEY_ID:-}" || -z "${B2_APPLICATION_KEY:-}" ]]; then
    echo "ERROR: Set B2_APPLICATION_KEY_ID and B2_APPLICATION_KEY env vars"
    exit 1
fi

echo "=== Pulling from B2 bucket: $BUCKET ==="

# Model checkpoints
echo ">> Downloading model checkpoints..."
b2 file download "b2://$BUCKET/output/t5_ft_base_sweep_1i8vr3_20260314_012024/checkpoints/model_best.pt" \
    output/t5_ft_base_sweep_1i8vr3_20260314_012024/checkpoints/model_best.pt

# Add more files here as needed:
# b2 file download "b2://$BUCKET/path/to/file" local/path/to/file

echo "=== Done ==="
