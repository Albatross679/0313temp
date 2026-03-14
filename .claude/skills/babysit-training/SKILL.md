---
name: babysit-training
description: |
  Monitor and babysit running ML training jobs for the NL-to-SQL T5 project.
  Perform comprehensive health checks: process alive, loss/metric trending,
  GPU utilization, disk space, checkpoint integrity, W&B connectivity, and
  hung process detection. Auto-restart from last checkpoint on crash.
  Document any issues found in issues/ with proper frontmatter.
  Use when: (1) User asks to babysit, monitor, or watch training,
  (2) User says "check on training", "is training healthy", "monitor the run",
  (3) Used with /loop for periodic automated monitoring,
  (4) User asks to check if training crashed or needs restart.
  Typical invocation: `/loop 10m /babysit-training`
---

# Babysit Training

Autonomous training monitor for the NL-to-SQL T5 project. Run through every check below in order, report a status line, and take action on any issues found.

## Check Sequence

Execute these checks in order. Stop and act on the first critical issue before continuing.

### 1. Process Health

```bash
ps aux | grep -E "python.*(train|sweep|prompting)" | grep -v grep
```

**If no process found:**
- Check `output/` for the most recent log file: `ls -lt output/*.txt | head -5`
- Read the tail of the log to determine if it exited cleanly or crashed
- If crashed: **auto-restart** (see Restart Procedure below)
- If completed normally: report completion and skip remaining checks

**If process found but no log output for >10 minutes:**
- Check if W&B shows FINISHED: `tail -20 <log_file>` and look for "wandb: Synced" or "Run history"
- If W&B finished but process alive: this is the known hung-process bug (futex deadlock during cleanup). Outputs are saved. Kill with `kill <PID>` and report. See [references/known-issues.md](references/known-issues.md).
- If W&B not finished and no output: genuine hang. Kill and restart.

### 2. Log Output Analysis

Read the latest training log:

```bash
# Find active log
ls -lt output/*.txt | head -3
# Read last 50 lines
tail -50 <latest_log>
```

**Extract and report:**
- Current epoch N / max_epochs
- Latest train_loss value
- Latest eval metrics (Record F1, Record EM, SQL EM) if available
- Any error messages or tracebacks

**Red flags (act immediately):**
- `NaN` or `inf` in loss: training diverged. Kill and restart with lower LR.
- `CUDA out of memory` / `OutOfMemoryError`: OOM. Kill, reduce batch size or disable auto_batch_size, restart.
- `RuntimeError` tracebacks: read full traceback, diagnose, fix code, restart.
- Loss increasing for >5 consecutive epochs: possible LR too high or data issue. Flag to user.

### 3. Metric Trending

Compare current metrics against earlier epochs in the same log:

```bash
grep -E "F1 =|train loss =" <log_file> | tail -20
```

**Flag if:**
- Record F1 has not improved in the last `patience_epochs` eval cycles (early stopping should handle this, but verify)
- Train loss plateaued (< 0.1% change over 5+ epochs)
- Dev loss diverging from train loss (overfitting signal)

### 4. GPU & System Health

```bash
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits
df -h / | tail -1
```

**Flag if:**
- GPU utilization < 30% for a running training process (possible data loading bottleneck)
- GPU memory usage near 100% of total (OOM risk on next batch size increase)
- GPU temperature > 85C (thermal throttling risk)
- Disk usage > 90% (checkpoint saves will fail silently)

### 5. Checkpoint & W&B Integrity

```bash
# Find the active run directory
ls -lt output/ | head -5
# Check checkpoints exist and are recent
ls -la output/<run_dir>/checkpoints/
# Check W&B is syncing (not offline/crashed)
ls -lt output/<run_dir>/wandb/latest-run/
```

**Flag if:**
- No checkpoint files in run directory after >1 epoch
- Checkpoint files are 0 bytes (write failure)
- W&B `latest-run/` directory missing or no recent sync files
- `wandb-offline-run-*` directories exist (W&B fell back to offline mode)

### 6. STOP File Check

```bash
ls -la STOP 2>/dev/null
```

If STOP file exists, verify training acknowledged it (log should show "Stop file detected"). If training is still running without acknowledgment after 2+ epochs, the stop check may be broken.

## Restart Procedure

When a crash is detected and restart is needed:

1. **Identify the crash cause** from the log tail
2. **Find the latest run directory** with saved training state:
   ```bash
   ls -lt output/ | grep -E "t5_ft|t5_scr" | head -5
   ```
3. **Check for saved training state:**
   ```bash
   ls output/<run_dir>/checkpoints/training_state.pt
   ```
4. **Restart with resume:**
   ```bash
   PYTHONUNBUFFERED=1 nohup python3 train_t5.py --resume output/<run_dir> > output/<descriptive_log>.txt 2>&1 &
   ```
5. **Verify restart** by checking the new log after ~30 seconds:
   ```bash
   sleep 30 && tail -20 output/<descriptive_log>.txt
   ```
6. **Document the crash** as an issue (see Issue Documentation below)

For sweep restarts, the sweep agent handles trial-level recovery automatically. Only restart the sweep process itself if it crashed:
```bash
PYTHONUNBUFFERED=1 nohup python3 part1/sweep.py --budget 1.5 --max-hours 12 > output/sweep_restart.txt 2>&1 &
```

## Issue Documentation

When an issue is found, create `issues/<descriptive-name>.md`:

```yaml
---
name: <descriptive-name>
description: <one-line summary>
type: issue
status: open  # or "resolved" if fixed during this check
severity: <low|medium|high|critical>
subtype: <training|data|model|evaluation|performance>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: [relevant, tags]
aliases: []
---
```

Include sections: Symptom, Root Cause (if known), Fix (if applied), Files Modified.

## Status Report Format

After all checks, output a single status line:

```
HEALTHY | Epoch 15/50 | loss=0.342 | F1=0.812 | GPU 78% 62C | disk 45%
```

or

```
ACTION TAKEN | <what happened> | <what was done> | training resumed at epoch N
```

or

```
NEEDS ATTENTION | <issue description> | <recommended action>
```

## Known Issues Reference

See [references/known-issues.md](references/known-issues.md) for a quick-reference table of previously encountered issues with immediate actions. For full root cause analysis and code fixes, see the canonical source in `ml-workflow/references/known-issues.md`. Check these patterns first before deep-diving into new diagnostics.
