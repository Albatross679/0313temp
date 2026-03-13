---
name: ml-workflow
description: |
  User's preferred workflow, conventions, and style for machine learning experiments.
  Covers: config system (hierarchical dataclass configs for neural, tree, and RL pipelines),
  experiment tracking (W&B), training execution (sequential auto-batch, VRAM management),
  monitoring (/loop), hyperparameter strategy (wall-clock budgets, config combinations),
  codebase structure, and documentation expectations.
  Use when: (1) Setting up experiment configurations for any ML framework,
  (2) Creating configs for SL Neural, SL Tree, RL, or PPO training pipelines,
  (3) Setting up or running ML training experiments,
  (4) Creating new config variants or experiment combinations,
  (5) Launching training runs or scheduling batches,
  (6) Monitoring active training,
  (7) Planning hyperparameter searches or ablation studies,
  (8) Scaffolding a new ML project or adding a new model/task.
  Works with: PyTorch, Hugging Face, TensorFlow/Keras, XGBoost, LightGBM, CatBoost, JAX.
  Always apply these preferences unless the user explicitly overrides them.
---

# ML Workflow Preferences

These are the user's established conventions for ML experiment work. Follow them whenever working on training, evaluation, experiment design, or ML code organization.

## Configuration System

Hierarchical `@dataclass` configs for all ML experiments. See [references/config-system.md](references/config-system.md) for the full spec (Base fields, built-in infrastructure, output conventions, framework adaptation).

**Field references** (read on demand for detailed field tables):
- [references/sl_neural_fields.md](references/sl_neural_fields.md) — SL Neural + Regression + Classification + task configs (LSTM, Transformer, CNN, T5)
- [references/sl_tree_fields.md](references/sl_tree_fields.md) — SL Tree + Regression + task configs (XGBoost, LightGBM, CatBoost)
- [references/rl_fields.md](references/rl_fields.md) — RL + PPO fields

## Experiment Tracking: Weights & Biases

Use W&B as the primary experiment tracker. Every training run must log to W&B.

**What gets logged** (metric key namespacing):

| Prefix | Granularity | Contents |
|--------|-------------|----------|
| *(no prefix)* | per epoch | `train_loss`, `dev_loss`, eval metrics, `gradient_norm`, `lr` |
| `batch/` | per batch | `loss`, `gradient_norm`, `lr` (step = global batch counter) |
| `timing/` | per epoch | `epoch_seconds`, `wall_clock_seconds`, `train_epoch_seconds`, `train_tokens_per_sec` |
| `tracking/` | per epoch | `best_{metric}`, `epochs_since_improvement` |
| `system/` | per epoch | GPU/CPU/RAM metrics (when `log_system_metrics=True`) |

**One-time params**: `total_params`, `trainable_params`, `num_train_samples`, `num_dev_samples`, `gpu_name`.

**W&B setup pattern:**
- Define custom metric axes with `wandb.define_metric` so batch and epoch metrics have independent x-axes.
- Finish any previous run (`wandb.finish()`) before starting a new one (critical for auto-batch mode).
- Support resume via `wandb.init(resume="allow", id=run_id)`.

**Integration lives in a shared utils module** (`src/wandb_utils.py`). Training loops call helper functions (`setup_run`, `log_epoch_metrics`, `log_extra_params`, `log_model_artifact`, `end_run`). Never call `wandb.*` directly from training code.

**Model weight artifacts**: Always upload the final best model checkpoint to W&B as a versioned artifact using `log_model_artifact(checkpoint_path, artifact_name, metadata)` at end of training. Upload once per run (not per improvement) to conserve W&B storage.

## Training Execution

### Sequential Auto-Batch

All experiment configs run **sequentially in a single process**. Never launch parallel training jobs on the same GPU.

- Define a list of config classes in `main()`, ordered by priority.
- The training loop iterates through them one by one.
- Between configs: call `cleanup_vram()` — delete model, optimizer, scheduler, clear CUDA cache, run `gc.collect()`. The next config starts with a clean GPU.
- Each config gets its own W&B run (finish previous, init new).

### GPU Task Serialization (Hard Preference)

All training entry points automatically acquire an exclusive GPU lock (`src/utils/gpu_lock.py`) at startup. This is a **hard preference** — GPU tasks must always be serialized to prevent VRAM interruption from concurrent sessions, especially since AutoBatch maximizes VRAM usage.

**How it works:**
- Each entry point (`train_t5.py`, `part*/train.py`, `prompting.py`) wraps `main()` with `GpuLock()` in its `if __name__ == "__main__"` block.
- Uses `flock` on `/tmp/gpu-task.lock` — auto-releases on process exit, crash, or kill.
- When a GPU task is running, other GPU tasks block and wait (queue behavior, not error).
- Shell wrapper for non-standard commands: `script/gpu-lock.sh run <command>`.

**When creating new training entry points:** Always wrap `main()` with `GpuLock()` in the `if __name__` block:
```python
if __name__ == "__main__":
    from src.utils.gpu_lock import GpuLock
    with GpuLock():
        main()
```

### Pre-Flight Check

Before launching any training, verify no other training process is running:

```bash
ps aux | grep -E "python.*train" | grep -v grep
```

Only proceed when the GPU is free. This prevents OOM from competing processes.

### VRAM Maximization

- Enable auto batch size tuning when available — find the largest batch size that fits VRAM.
- Clean VRAM between sequential configs (model deletion + cache clear).

### Long-Running Process Resilience

Any script expected to run >5 minutes (training, inference, experiment batches) MUST be launched with `nohup` so it survives terminal/session restarts (e.g., tmux window reloads, Claude Code session reconnects):

```bash
nohup <command> > output/<descriptive_log>.txt 2>&1 &
```

Then monitor with `tail -f output/<log>.txt` or `/loop`.

This applies to all execution contexts — manual runs, GSD execute-phase tasks, and any agent-spawned training jobs. Without `nohup`, child processes receive SIGHUP when the parent session dies and are killed mid-run.

### Graceful Stop

Support two stop mechanisms:
- `touch STOP` file — checked between epochs, allows current epoch to finish.
- SIGTERM signal — handler sets a flag, same graceful drain behavior.

Both drain pending async work, save checkpoints, and finish W&B run before exiting.

## Monitoring with /loop

After launching a background training run, always start a monitoring loop:

```
/loop 20m Check on training status. Read the latest training log output, verify the process is still running, check GPU utilization, and confirm loss is decreasing / metrics are improving. If any issues are found (OOM, NaN loss, stuck training, process died), diagnose the root cause, fix it, restart training, and document the issue in issues/<topic>.md with proper frontmatter. If training is healthy, briefly report current epoch, loss, and primary eval metric for the active config.
```

The monitoring agent should:
1. Check process is alive (`ps aux | grep python.*train`)
2. Read latest log output or `metrics.jsonl` for the active run
3. Verify loss is decreasing and eval metric is improving
4. Check GPU utilization and temperature
5. If an issue is found: diagnose, fix, restart, and write an issue doc
6. If healthy: report a brief status line

## Experiment Strategy

### Config Combinations

Always create **enough config variants** to explore the design space meaningfully. A typical experiment set includes:
- A baseline config
- Variants that change one dimension at a time (learning rate, model size, regularization, data augmentation)
- At least one "aggressive" variant pushing multiple dimensions
- Each variant is its own dataclass config inheriting from a base, with only the differing fields overridden

### Wall-Clock Time Budget

Experiment batches are scheduled by **wall-clock time budget**, not by number of epochs. Set `max_wall_clock_hours` on each config so the entire batch fits within the available compute window. Early stopping and time budgets work together — a config that converges early frees time for the next one.

### Checkpointing and Early Stopping

- Always save best model (by primary eval metric) and last model.
- **Always upload the final best model weights to W&B as a versioned artifact** via `log_model_artifact()` at end of training (once per run, not per improvement, to conserve storage). This ensures weights are backed up and retrievable from any machine.
- Early stopping by patience (measured in eval cycles, not raw epochs).
- `eval_every_n_epochs` controls eval frequency — effective patience = `patience_epochs * eval_every_n_epochs`.
- Optional `patience_tolerance` for minimum improvement threshold.

## Codebase Structure

The preferred code organization for ML projects. See [references/codebase-structure.md](references/codebase-structure.md) for the full reference with module-level detail.

**Key principles:**
- **Part-based segmentation** — each experimental approach (fine-tune, from-scratch, prompting) gets its own `partN/` directory with config, data, model, and train modules.
- **Shared infrastructure in `src/`** — config hierarchy, W&B integration, system metrics. Never duplicated per-part.
- **Root entry points** — thin wrappers that delegate to part-specific `main()`.
- **Config-driven experiments** — every variant is a `@dataclass` config. CLI `--config` flag selects the class. Per-field CLI overrides apply on top.
- **Two-phase async evaluation** — GPU inference and CPU-bound metric computation overlap with the next training epoch.
- **Documentation directories** — `logs/`, `experiments/`, `issues/`, `knowledge/`, `references/`, `tasks/` for structured project documentation (see project-preference skill).
