#!/bin/bash
# Wait for DPO preference data generation to finish, then launch DPO sweep.
# Usage: nohup bash script/launch_dpo_sweep.sh > output/dpo_sweep.txt 2>&1 &

set -e
cd "$(dirname "$0")/.."

DATA_PID=$1
DATA_FILE="output/dpo_preference_data.json"

if [ -n "$DATA_PID" ]; then
    echo "[$(date)] Waiting for preference data generation (PID $DATA_PID)..."
    while kill -0 "$DATA_PID" 2>/dev/null; do
        sleep 30
    done
    echo "[$(date)] Data generation process finished."
fi

# Verify data exists
if [ ! -f "$DATA_FILE" ]; then
    echo "ERROR: $DATA_FILE not found. Data generation may have failed."
    echo "Check output/dpo_pref_gen.txt for errors."
    exit 1
fi

COUNT=$(python3 -c "import json; print(len(json.load(open('$DATA_FILE'))))")
echo "[$(date)] Preference data ready: $COUNT triplets"

# Launch DPO sweep
echo "[$(date)] Starting DPO sweep..."
export PYTHONUNBUFFERED=1
export PYTHONPATH=/home/turncloak/0313temp
exec python3 part1/dpo_sweep.py --max-hours 6 --count 20
