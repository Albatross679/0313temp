# CLAUDE.md

## Project Overview

CSE 5525 Assignment 3: Natural Language to SQL. Three approaches to translate NL flight-database queries into SQL:
1. **Part 1** — Fine-tune pretrained T5-small
2. **Part 2** — Train T5-small from scratch (random init)
3. **Part 3** — Prompt-based ICL with Gemma 2B / CodeGemma 7B

Database: `data/flight_database.db` (25 tables). Evaluation: Record F1 (primary), Record EM, SQL EM via `evaluate.py`.

**Repository:** `git@github.com:Albatross679/nlp_Assignment3.git` | https://github.com/Albatross679/nlp_Assignment3

## Project Structure

```
nlp_Assignment3/
├── .claude/              # Claude Code settings, skills, memory
├── data/                 # datasets (DO NOT MODIFY)
├── src/                  # shared infrastructure (config hierarchy, tracking, utils)
│   ├── config.py         # BaseConfig → SLNeuralConfig → SLNeuralClsConfig
│   ├── infrastructure.py # setup_run, save_config, console logging
│   └── utils/
├── part1/                # T5 fine-tune configs, data, model, train
├── part2/                # T5 from-scratch configs
├── part3/                # LLM prompting configs
├── train_t5.py           # T5 training loop (Parts 1 & 2)
├── t5_utils.py           # T5 model init, save/load, optimizer setup
├── load_data.py          # T5Dataset, collate, prompting data
├── prompting.py          # LLM prompting pipeline (Part 3)
├── prompting_utils.py    # schema reader, SQL extraction
├── utils.py              # metrics, record computation, seed
├── evaluate.py           # CLI evaluation script
├── records/              # pickled database records
├── results/              # predicted SQL output files
├── model/                # saved model weights (not committed)
├── output/               # run outputs and checkpoints (not committed)
├── report/               # LaTeX report
├── media/                # images, plots
├── script/               # standalone utility scripts
├── logs/ experiments/ issues/ knowledge/ references/ tasks/  # documentation
└── .planning/            # GSD roadmap and phase plans
```

## File Protection

**Do not rename or move** (graded by file name/location):
`evaluate.py`, `load_data.py`, `prompting.py`, `prompting_utils.py`, `t5_utils.py`, `train_t5.py`, `utils.py`, `requirements.txt`, `data/`, `records/ground_truth_dev.pkl`, `results/`

**Do not modify contents:** `data/` (all dataset files), `records/ground_truth_dev.pkl`

**Required submission outputs** (exact names): `results/{t5_ft,t5_scr,llm}_test.sql`, `records/{t5_ft,t5_scr,llm}_test.pkl`

## Architecture

| Part | Entry Point | Description |
|------|-------------|-------------|
| 1 | `train_t5.py --finetune` | Fine-tune pretrained T5-small on NL→SQL pairs |
| 2 | `train_t5.py` (no flag) | Train T5-small from scratch (random init, same arch) |
| 3 | `prompting.py` | Prompt Gemma 2B / CodeGemma 7B with k-shot examples |
| Shared | `src/` | Config hierarchy, run infrastructure, utilities |

Each part has its own `partN/` directory with `config.py`, `data.py`, `model.py`, `train.py`, and optionally `model_domain.py` and `eval_checkpoint.py`.

## Credentials & Models

- **GitHub:** `Albatross679`, email `qifan_wen@outlook.com`
- **HuggingFace:** `<REDACTED>`
- **W&B:** `<REDACTED>`
- **HF_HOME:** `/home/coder/.cache/huggingface` (all models cached locally)

| Model | HuggingFace ID | Used in |
|-------|---------------|---------|
| T5-small | `google-t5/t5-small` | Part 1 (fine-tune), Part 2 (config only) |
| T5-base | `google-t5/t5-base` | Optional larger baseline |
| Gemma 2B | `google/gemma-1.1-2b-it` | Part 3 (default) |
| CodeGemma 7B | `google/codegemma-7b-it` | Part 3 (optional) |

## Key Commands

```bash
python train_t5.py --finetune --max_n_epochs 20 --learning_rate 1e-4 --patience_epochs 5  # Part 1
python train_t5.py --max_n_epochs 50 --learning_rate 1e-3                                 # Part 2
python prompting.py --shot 3 --model gemma                                                 # Part 3
python evaluate.py --predicted_sql results/t5_ft_dev.sql --predicted_records records/t5_ft_dev.pkl --development_sql data/dev.sql --development_records records/ground_truth_dev.pkl
```

## Todoist Tracking

Project **nlp_as3** (ID: `6g5H7Vvvwhx95Pvv`). Tasks: `part1` (T5 fine-tune), `part2` (T5 from scratch), `part3` (LLM prompting).

---

## ML Workflow Preferences

### Config System

- **Hierarchical `@dataclass` configs:** `BaseConfig` → `SLNeuralConfig` → task-specific config. Each variant is its own class overriding only differing fields.
- **Config-driven CLI:** `--config` flag selects dataclass class; per-field CLI overrides apply on top. Priority: dataclass defaults < config class < CLI flags.
- **Batteries included:** every config gets output dir, console logging, checkpointing, metrics log, and experiment tracking by default (individually disableable).
- **Serializable:** every config supports `to_dict()` / `from_dict()` for JSON round-trip.
- **Human-friendly time units:** hours for time-budget fields (`max_wall_clock_hours`).

### Experiment Tracking (W&B)

W&B is the primary tracker. Every training run must log to it.

- **Metric namespacing:** no prefix (epoch), `batch/` (per-batch), `timing/` (wall clock), `tracking/` (best metrics), `system/` (GPU/CPU)
- **Integration in shared utils** (`src/wandb_utils.py`): `setup_run`, `log_epoch_metrics`, `log_extra_params`, `log_model_artifact`, `end_run`. Never call `wandb.*` directly from training loops.
- **Model weight artifacts**: Always upload the final best model checkpoint to W&B as a versioned artifact via `log_model_artifact()` at end of training (once per run, not per improvement, to conserve storage).
- **Define custom metric axes** with `wandb.define_metric`; finish previous run before starting new one.

### Training Execution

- **Sequential auto-batch:** all configs run one-by-one in a single process. Never parallel on same GPU.
- **VRAM cleanup between configs:** delete model/optimizer/scheduler, `torch.cuda.empty_cache()`, `gc.collect()`.
- **Pre-flight check:** `ps aux | grep -E "python.*train" | grep -v grep` before launching.
- **Graceful stop:** `touch STOP` file or SIGTERM — both drain async work, save checkpoints, finish W&B run.
- **VRAM maximization:** auto batch size tuning when available.
- **bf16 mixed precision:** `use_amp=True` in SLNeuralConfig enables `torch.amp.autocast('cuda', dtype=torch.bfloat16)` for training and inference. No GradScaler needed. Requires Ampere+ GPU.
- **`nohup` for long-running jobs:** Any script expected to run >5 minutes (training, inference, experiments) MUST be launched with `nohup` so it survives terminal/session restarts: `nohup <command> > output/<log>.txt 2>&1 &`. Monitor with `tail -f`. This applies to GSD execute-phase tasks too.
- **GPU task serialization (ALWAYS ON):** All training entry points (`train_t5.py`, `part1/train.py`, `part2/train.py`, `part3/train.py`, `prompting.py`) automatically acquire the GPU lock on startup. This is a hard preference — GPU tasks must always be serialized to prevent VRAM interruption from concurrent sessions. The lock uses `flock` on `/tmp/gpu-task.lock` and auto-releases on process exit/crash/kill.

### GPU Task Queue

All training entry points automatically acquire the GPU lock (`src/utils/gpu_lock.py`) at startup. When a training job is running, any other training job launched from another session will **block and wait** until the first finishes. This prevents OOM from concurrent GPU usage and allows AutoBatch to safely maximize VRAM.

**How it works:** Each entry point wraps `main()` with `GpuLock()` in its `if __name__ == "__main__"` block. No manual wrapping needed for standard training commands.

**For non-standard GPU commands**, use the shell wrapper:
```bash
script/gpu-lock.sh run <any-gpu-command>   # blocks until GPU is free, then runs
script/gpu-lock.sh status                   # check if GPU is locked and by whom
script/gpu-lock.sh wait                     # block until GPU is free (no command)
```

**Python API** (for custom scripts):
```python
from src.utils.gpu_lock import GpuLock
with GpuLock():
    # GPU-intensive work here
    run_inference(model)
```

**When to use manually:** Only for GPU commands not covered by the standard entry points. All `train_t5.py`, `part*/train.py`, and `prompting.py` runs are already protected automatically.

### Monitoring

After launching background training, always start `/loop 20m` to check: process alive, loss decreasing, eval metric improving, GPU utilization. If issue found: diagnose, fix, restart, write issue doc.

### Experiment Strategy

- **Config variants:** baseline + single-dimension variants + one aggressive variant pushing multiple dimensions.
- **Wall-clock time budget:** `max_wall_clock_hours` per config. Early stopping and time budgets work together.
- **Checkpointing:** always save best (by primary eval metric) and last model.
- **Early stopping by patience** (eval cycles, not raw epochs). Effective patience = `patience_epochs * eval_every_n_epochs`.

### Codebase Structure

- **Part-based segmentation:** `partN/` per approach with `config.py`, `data.py`, `model.py`, `train.py`.
- **Shared infra in `src/`:** config hierarchy, W&B integration, system metrics. Never duplicated per-part.
- **Root entry points:** thin wrappers delegating to part-specific `main()`.
- **Two-phase async evaluation:** GPU inference (generate predictions) overlaps with CPU-bound metric computation (SQL execution, F1/EM) via `ThreadPoolExecutor`.
- **Dynamic padding collate:** pad per-batch to longest sequence, no fixed-length padding.

---

## LaTeX Report

Report lives in `report/`. Compiled with **LaTeX Workshop** (VSCode extension).

```
report/
├── report.tex                # main file (self-contained)
├── a4-report.tex             # original template (reference only)
├── header.tex                # shared imports and macros
├── colm2024_conference.sty   # COLM 2024 style (DO NOT MODIFY)
└── report.pdf                # compiled output
```

- LaTeX Workshop compiles on save — do NOT run `pdflatex`/`latexmk` from terminal.
- Images in `media/`, include with `\includegraphics`.

---

## Documentation (IMPORTANT)

Claude Code MUST document **as it goes** — immediately after each change, not batched at the end. Each entry is a **separate file** covering **exactly one topic**.

| What | Where | Naming | When | Type |
|---|---|---|---|---|
| Logs | `logs/` | `<topic>.md` | After any code change that adds, fixes, or modifies functionality | `log` |
| Experiments | `experiments/` | `<topic>.md` | After running a simulation, test, or investigation | `experiment` |
| Issues | `issues/` | `<topic>.md` | When encountering a bug or error (before or alongside the fix) | `issue` |
| Knowledge | `knowledge/` | `<topic>.md` | When capturing domain knowledge or reference material | `knowledge` |
| References | `references/` | `<topic>.md` | When capturing external references or citations | `reference` |
| Tasks | `tasks/` | `prd-<feature>.md` | When planning a feature or task (PRDs) | `task` |

### Required Frontmatter

All types: `name`, `description`, `type`, `created`, `updated`, `tags`, `aliases`. Additional per type:

- **`log`**: `status` (draft | complete), `subtype` (fix | feature | refactor | setup | training | tuning | prompting)
- **`experiment`**: `status` (planned | running | complete | failed)
- **`issue`**: `status` (open | investigating | resolved | wontfix), `severity` (low | medium | high | critical), `subtype` (training | data | model | evaluation | compatibility | performance)
- **`knowledge`**: common properties only
- **`reference`**: `source`, `url`, `authors`
- **`task`**: `status` (planned | in-progress | complete | cancelled)

**Threshold:** Log if it modifies behavior, fixes a bug, or changes config. Skip trivial edits.

---

## Active Mode ("Stay Active")

When asked to **stay active**, Claude Code MUST:
1. **Scope** — only address in-scope issues. Don't "fix" unrelated working code.
2. **Prioritize** — errors/blockers first, then warnings, then improvements.
3. **Autonomously iterate** — keep going without waiting for prompts.
4. **Document each resolution** — write a log immediately, before moving to next.
5. **Check in every ~5 fixes** — brief summary of progress and remaining issues.
6. **Stop** when no remaining in-scope issues or user says stop.
