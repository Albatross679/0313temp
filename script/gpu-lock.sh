#!/usr/bin/env bash
# GPU task serialization via flock.
#
# Ensures only one GPU-intensive task runs at a time across all sessions.
# Uses flock on a shared lockfile -- automatic cleanup on crash/kill.
#
# Usage:
#   gpu-lock.sh run <command...>   # Acquire lock, run command, release
#   gpu-lock.sh status             # Check if GPU is locked and by whom
#   gpu-lock.sh wait               # Block until GPU is free (no command)
#   gpu-lock.sh --help             # Show usage
set -euo pipefail

LOCKFILE="/tmp/gpu-task.lock"

usage() {
    cat <<'USAGE'
gpu-lock.sh -- GPU task serialization via flock

Subcommands:
  run <command...>   Acquire exclusive GPU lock, then run command.
                     Lock is held for the entire duration of the command.
                     Auto-released on exit, crash, or kill.
                     Example: gpu-lock.sh run python train_t5.py --finetune

  status             Check if the GPU lock is currently held.
                     Shows holding PID and process details if locked.
                     Example: gpu-lock.sh status

  wait               Block until the GPU lock is free, then exit.
                     Does not run any command -- just waits.
                     Example: gpu-lock.sh wait && echo "GPU is free"

  --help, -h         Show this usage message.

Lockfile: /tmp/gpu-task.lock
USAGE
}

cmd_run() {
    if [[ $# -eq 0 ]]; then
        echo "[gpu-lock] Error: 'run' requires a command." >&2
        echo "[gpu-lock] Usage: gpu-lock.sh run <command...>" >&2
        exit 1
    fi

    # Open lockfile on fd 200
    exec 200>"$LOCKFILE"

    echo "[gpu-lock] Waiting for GPU lock..." >&2
    flock -x 200
    echo "[gpu-lock] Acquired GPU lock (PID $$)" >&2

    # Release message on exit (normal, error, signal)
    trap 'echo "[gpu-lock] Released GPU lock (PID $$)" >&2' EXIT

    # Run the command (not exec, so trap fires)
    "$@"
}

cmd_status() {
    # Try non-blocking lock acquisition
    exec 200>"$LOCKFILE"
    if flock -n -x 200; then
        # Lock acquired -- it was free. Release immediately.
        flock -u 200
        exec 200>&-
        echo "GPU lock: free"
    else
        exec 200>&-
        echo "GPU lock: held"
        # Try to find the holding process via fuser
        local pids
        pids=$(fuser "$LOCKFILE" 2>/dev/null || true)
        if [[ -n "$pids" ]]; then
            echo "Holding PID(s): $pids"
            for pid in $pids; do
                # Show process details
                ps -p "$pid" -o pid,user,start,cmd --no-headers 2>/dev/null || true
            done
        else
            echo "(Could not determine holding PID -- process may have just released)"
        fi
    fi
}

cmd_wait() {
    echo "[gpu-lock] Waiting for GPU lock to become free..." >&2
    flock -x "$LOCKFILE" true
    echo "[gpu-lock] GPU lock is free." >&2
}

# ── Main dispatch ──────────────────────────────────────────────────────────
case "${1:-}" in
    run)
        shift
        cmd_run "$@"
        ;;
    status)
        cmd_status
        ;;
    wait)
        cmd_wait
        ;;
    --help|-h)
        usage
        ;;
    "")
        usage
        ;;
    *)
        echo "[gpu-lock] Unknown subcommand: $1" >&2
        echo "[gpu-lock] Run 'gpu-lock.sh --help' for usage." >&2
        exit 1
        ;;
esac
