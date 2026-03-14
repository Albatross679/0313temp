---
name: ml-workflow
description: |
  User's preferred workflow, conventions, and style for machine learning experiments.
  Covers: config system (hierarchical dataclass configs for neural, tree, and RL pipelines),
  experiment tracking (W&B), training execution (sequential auto-batch, VRAM management, bf16),
  monitoring (/loop), hyperparameter strategy (W&B random sweeps, early-stopping-only, config combinations),
  RL/alignment algorithms (PPO, SAC, DQN, DPO, GRPO, CISPO), reward design, training stability,
  codebase structure, and documentation expectations.
  Use when: (1) Setting up experiment configurations for any ML framework,
  (2) Creating configs for SL Neural, SL Tree, RL, or PPO training pipelines,
  (3) Setting up or running ML training experiments,
  (4) Creating new config variants or experiment combinations,
  (5) Launching training runs or scheduling batches,
  (6) Monitoring active training,
  (7) Planning hyperparameter searches or ablation studies,
  (8) Scaffolding a new ML project or adding a new model/task,
  (9) Setting up RL alignment training (DPO, GRPO, CISPO) or classic RL (PPO, SAC, DQN),
  (10) Designing reward functions or diagnosing RL training instability.
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
- [references/rl_fields.md](references/rl_fields.md) — RL: Classic Control (PPO, SAC, DQN) + LLM Alignment (DPO, GRPO, CISPO), metrics, reward design, stability

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

### Mixed Precision (bf16)

All neural training uses **bf16 autocast by default** (`use_amp=True` in SLNeuralConfig). bf16 over fp16 because:
- Same exponent range as fp32 (8 bits) — no gradient underflow, no `GradScaler` needed
- T5 was pretrained in bf16 by Google — no precision mismatch when fine-tuning
- fp16 has known stability issues with T5 (narrow dynamic range + layer norm)
- Ampere+ GPUs have native bf16 Tensor Cores — same throughput as fp16

**Implementation pattern:**
```python
from contextlib import nullcontext

def _amp_context(use_amp, device):
    if use_amp and 'cuda' in str(device):
        return torch.amp.autocast('cuda', dtype=torch.bfloat16)
    return nullcontext()

# Training: wrap forward+loss, keep backward outside
with _amp_context(cfg.use_amp, device):
    loss = model(inputs)
loss.backward()

# Inference: wrap generation
with torch.inference_mode(), _amp_context(cfg.use_amp, device):
    outputs = model.generate(...)
```

**No GradScaler** — bf16's wide dynamic range eliminates the need for loss scaling. This keeps the training loop simpler than fp16.

**GPU requirement:** Ampere+ (A100, 3090, 4090, 5090). On older GPUs, set `use_amp=False`.

### VRAM Maximization

- Enable auto batch size tuning when available — find the largest batch size that fits VRAM.
- Clean VRAM between sequential configs (model deletion + cache clear).
- bf16 autocast roughly halves VRAM per sample, allowing auto_batch_size to find larger batches.

### Long-Running Process Resilience

Any script expected to run >5 minutes (training, inference, experiment batches) MUST be launched with `nohup` so it survives terminal/session restarts (e.g., tmux window reloads, Claude Code session reconnects):

```bash
PYTHONUNBUFFERED=1 nohup <command> > output/<descriptive_log>.txt 2>&1 &
```

**Always set `PYTHONUNBUFFERED=1`** — Python buffers stdout when not connected to a TTY (i.e., piped or redirected by `nohup`), so without this, log files show no output for long periods and monitoring is ineffective.

Then monitor with `tail -f output/<log>.txt` or `/loop`.

This applies to all execution contexts — manual runs, GSD execute-phase tasks, and any agent-spawned training jobs. Without `nohup`, child processes receive SIGHUP when the parent session dies and are killed mid-run.

### Hung Process Watchdog

PyTorch/CUDA can deadlock during post-training cleanup (`gc.collect()` / `torch.cuda.empty_cache()`), especially when `ThreadPoolExecutor` threads are still active. The process blocks on `futex_wait_queue_me` indefinitely even though W&B has marked the run FINISHED and all outputs are saved.

**Prevention:** For sequential training scripts (multiple configs in one process), add a watchdog that polls W&B run status and kills the training process if it's still alive N minutes after the run is marked FINISHED. Treat exit codes 137 (SIGKILL) and 143 (SIGTERM) from the watchdog as success.

**Ad-hoc detection:** If monitoring (`/loop`) shows a process alive but no log activity and W&B shows FINISHED, confirm outputs are saved, then `kill` the process manually.

### Graceful Stop

Support two stop mechanisms:
- `touch STOP` file — checked between epochs, allows current epoch to finish.
- SIGTERM signal — handler sets a flag, same graceful drain behavior.

Both drain pending async work, save checkpoints, and finish W&B run before exiting.

## Known Issues

Common training pitfalls and their fixes. See [references/known-issues.md](references/known-issues.md) for the full catalog (process/lifecycle, memory/OOM, model/checkpoint, evaluation, decoding). Check these patterns first when diagnosing training problems — most are recurring.

## Monitoring

After launching a background training run, always start the babysit-training skill:

```
/loop 10m /babysit-training
```

The `babysit-training` skill handles all monitoring: process health, metric trending, GPU/system checks, checkpoint integrity, hung process detection, auto-restart from checkpoint on crash, and issue documentation. See that skill for the full check sequence.

## Experiment Strategy

### Config Combinations

Always create **enough config variants** to explore the design space meaningfully. A typical experiment set includes:
- A baseline config
- Variants that change one dimension at a time (learning rate, model size, regularization, data augmentation)
- At least one "aggressive" variant pushing multiple dimensions
- Each variant is its own dataclass config inheriting from a base, with only the differing fields overridden

### Stopping Strategy

**Early stopping is the primary mechanism** for deciding when training should stop. Do not set hard epoch caps (`num_epochs`) or wall-clock time limits (`max_wall_clock_hours`) per trial/config — let early stopping handle convergence detection.

- `max_wall_clock_hours` is only used at the **sweep level** (`--max-hours`) to bound total compute, not per trial.
- `num_epochs` should be set high (effectively unlimited) so early stopping is the binding constraint.
- A config that converges early frees time for the next one in a sequential batch.

### W&B Hyperparameter Sweeps

For systematic hyperparameter search, use **W&B random sweeps**. Preferred over grid search or manual config variants when the search space is large. Random search gives broader coverage across architecture types than Bayesian search, which tends to over-exploit early winners.

**Architecture pattern:**
1. **Sweep script** (`partN/sweep.py`) — defines search space, creates sweep, runs agent. Lives alongside its part's config/train modules.
2. **`main_with_config(cfg)`** — extracted from `main()` so sweeps can call the training pipeline programmatically
3. **Sweep-aware `setup_run()`** — detects active sweep via `wandb.run.sweep_id`, skips `wandb.init()`, updates config instead

**Search space types:**
- **Continuous**: `"distribution": "log_uniform_values", "min": 1e-5, "max": 1e-3` — for LR, weight_decay
- **Discrete**: `"values": [0, 0.05, 0.1, 0.15]` — for dropout, label_smoothing, num_beams
- **Binary**: `"values": [True, False]` — for feature flags like include_schema
- **Weighted discrete**: `"values": [...], "probabilities": [0.7, 0.3]` — bias initial sampling toward promising values

**Mutually exclusive structural choices** (e.g., LoRA vs MLP vs vanilla): Encode as a single `architecture` preset parameter to guarantee exclusivity. Decode the preset string into config fields in `sweep_train()`:
```python
_ARCHITECTURE_PRESETS = {
    "full_ft":       {},
    "lora_qv_r16":   {"use_lora": True, "lora_r": 16, ...},
    "mlp_1024":      {"use_mlp_head": True, "mlp_dim": 1024, ...},
}

def sweep_train():
    run = wandb.init()
    cfg = MyBaseConfig()
    swept = dict(wandb.config)
    arch = swept.pop("architecture", "full_ft")
    for k, v in _ARCHITECTURE_PRESETS[arch].items():
        setattr(cfg, k, v)
    for key, val in swept.items():
        if hasattr(cfg, key):
            setattr(cfg, key, val)
    ...
```

**Sweep-level controls:**
- `--max-hours` — total sweep wall clock limit; auto-stops when exhausted
- `--count` — max trials (default 100, effectively unlimited)
- Manual stop: Ctrl+C in tmux, or `touch STOP` from another terminal
- Per-trial stopping is handled by **early stopping only** — no per-trial epoch cap or time budget

**Execution:** Run sweeps in a **tmux session** (not `nohup`) — single process runs trials sequentially, compatible with GPU lock:
```bash
tmux new -s sweep
python partN/sweep.py --budget 1.5 --max-hours 12
# Ctrl+B, D to detach; tmux attach -t sweep to reattach
```

**When to use sweeps vs config variants:**
- **Sweeps**: mixed continuous + discrete search, exploration-heavy, architecture search (LoRA/MLP/full-FT)
- **Config variants**: when you need exact reproducibility of each variant, or only 2-3 configs to compare

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
