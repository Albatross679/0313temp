# Coding Conventions

**Analysis Date:** 2026-03-13

## Naming Patterns

**Files:**
- Module files use `snake_case`: `train_t5.py`, `load_data.py`, `prompting_utils.py`
- Root entry points are short and descriptive: `train_t5.py`, `prompting.py`, `evaluate.py`
- Part-scoped modules mirror each other: `config.py`, `data.py`, `model.py`, `train.py` inside each `partN/`
- Domain-specific model files use `_domain` suffix: `part1/model_flightdb.py`
- Evaluation helpers named `eval_checkpoint.py` within each part directory
- Script utilities in `script/` are either `.py` or `.sh` and are named by function

**Functions:**
- Public functions use `snake_case`: `compute_metrics`, `load_t5_data`, `initialize_model`
- Private/internal helpers prefixed with `_`: `_forward_and_loss`, `_generate_predictions`, `_load_schema_string`, `_pad_encoder`, `_make_criterion`
- Async/background helpers named with context: `_collect_async_sql`, `_pending_list`
- Boolean state setters named as questions: `stop_requested()`, `_is_peft_model()`
- Factory functions named `initialize_*`: `initialize_model`, `initialize_optimizer`, `initialize_optimizer_and_scheduler`
- Setup helpers named `setup_*`: `setup_run`, `setup_wandb`
- Cleanup helpers named `cleanup_*`: `cleanup_vram`

**Variables:**
- Configuration objects: `cfg` (short) throughout training loops
- Loader variables: `train_loader`, `dev_loader`, `test_loader`
- Loss tensor: `loss`, accumulated: `total_loss`, average: `avg_loss`
- Token counts: `num_tokens`, `total_tokens`
- Counters: `num_batches`, `global_step`, `epochs_since_improvement`
- Per-sample cache: `_pred_cache`, `_SCHEMA_CACHE` (module-level cache with `_` prefix + `UPPER`)
- Module-level singletons in `UPPER_CASE`: `DB_PATH`, `PAD_IDX`, `DEVICE`, `GPU_LOCKFILE`
- Module-level private singletons: `_TOKENIZER`, `_BOS_ID`, `_WANDB_AVAILABLE`
- Ground-truth paths: `gt_sql_path`, `gt_record_path`
- Model prediction paths: `model_sql_path`, `model_record_path`

**Types and Classes:**
- Config dataclasses: `PascalCase` with descriptive suffix `Config`: `T5FineTuneConfig`, `SLNeuralConfig`, `CheckpointingConfig`
- Config variants: base name + `_variant`: `T5FineTuneConfig_lora_v1`, `T5FineTuneConfig_restricted`
- Model wrapper classes: `PascalCase` describing purpose: `T5ForFlightSQL`, `T5ForFlightSQLWithMLP`, `FlightSQLVocab`
- Dataset classes: `PascalCase` with `Dataset` suffix: `T5Dataset`
- Context manager classes: `PascalCase`: `GpuLock`

## Code Style

**Formatting:**
- No formatter config file detected (no `.prettierrc`, `.black`, `pyproject.toml` formatter section)
- Indentation: 4 spaces throughout all Python files
- Maximum line length: approximately 100-120 characters (long log format strings go to ~140)
- String quotes: double quotes preferred in docstrings/comments, single quotes used in f-strings and short literals

**Linting:**
- No `.flintrc`, `setup.cfg [flake8]`, or `ruff.toml` detected
- No type annotations enforced (used selectively in new infrastructure code: `src/`)
- `from __future__ import annotations` used in newer `src/` modules (`config.py`, `wandb_utils.py`, `gpu_lock.py`) for forward reference resolution

## Import Organization

**Order (observed pattern):**
1. Standard library (`os`, `sys`, `json`, `re`, `gc`, `signal`, `time`, `argparse`, `pathlib`)
2. Third-party packages (`torch`, `transformers`, `tqdm`, `wandb`, `numpy`)
3. Local project imports (`from part1.data import ...`, `from src.config import ...`, `from utils import ...`)

**Module-level vs. local imports:**
- Expensive or circular imports deferred inside functions: `from part1.data import ...` inside `initialize_model` in `t5_utils.py`, `from peft import ...` inside `main()` in `part1/train.py`
- `from rank_bm25 import BM25Okapi` imported inside `build_bm25_index()` in `part3/data.py`

**Path setup pattern** (used in script and eval files):
```python
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
```

**Root stub pattern** (graded entry points delegate to part implementations):
```python
# load_data.py
from part1.data import T5Dataset, normal_collate_fn, ...
__all__ = ["T5Dataset", ...]
```

## Error Handling

**Patterns observed:**

- `try/except Exception as e` for SQL execution, using `{type(e).__name__}: {e}` for error messages:
```python
# utils.py
try:
    cursor.execute(query)
    rec = cursor.fetchall()
    error_msg = ""
except Exception as e:
    rec = []
    error_msg = f"{type(e).__name__}: {e}"
```

- Silent degradation with bare `except Exception: pass` for optional metrics (GPU monitoring):
```python
# src/utils/system_metrics.py
try:
    import pynvml
    ...
except Exception:
    pass
```

- `assert` for preconditions in training setup:
```python
assert os.path.exists(base_ckpt_path), f"Base checkpoint not found: {base_ckpt_path}"
```

- `raise ValueError` for unknown config/argument values:
```python
raise ValueError(f"Unknown loss_fn: {cfg.loss_fn}")
raise ValueError(f"Unknown schema mode: {mode!r}. Choose from: ...")
raise NotImplementedError  # in t5_utils.py for unknown scheduler_type
```

- `sys.exit(1)` in evaluation scripts when a required resource is missing:
```python
if run_dir is None or not os.path.isdir(run_dir):
    print("ERROR: No run directory found. Use --run_dir to specify one.")
    sys.exit(1)
```

- `KeyboardInterrupt` caught in the main training loop to drain background work and save state before exit.

## Logging

**Framework:** `print()` for all user-facing output. No structured logging library (`logging` module not used).

**W&B logging via abstraction layer (`src/wandb_utils.py`):**
- Never call `wandb.*` directly from training loops — always use `log_epoch_metrics`, `log_extra_params`, `log_model_artifact`, `end_run`
- Metric namespacing: no prefix for epoch metrics, `batch/` for per-batch, `timing/` for wall clock, `tracking/` for best-value bookkeeping, `system/` for GPU/CPU

**Print conventions:**
- Training progress: `f"Epoch {epoch}: train loss = {tr_loss:.4f}, dev loss = {dev_loss:.4f}"`
- Metric reporting: `f"Epoch {epoch}: F1 = {record_f1:.4f}, EM = {record_em:.4f}, SQL_EM = {sql_em:.4f}, err = {error_rate*100:.1f}%"`
- Section headers in scripts: `f"{'='*70}"` separators
- GPU lock messages go to `sys.stderr`: `print("[gpu-lock] ...", file=sys.stderr)`
- Graceful stop messages print to `stdout` with `\n` prefix for visual separation

## Comments

**When to Comment:**
- Module-level docstrings on every file (triple-quoted): describe purpose and hierarchy
- Section dividers with `# ── Section name ────` pattern (ASCII box-drawing dashes) to organize long files
- Inline comments for non-obvious logic, tensor shape annotations: `# (B, T, d_model)`
- `# NOTE:` prefix for important implementation decisions to preserve
- Config variant comments describe the experiment rationale: `"""LoRA r=16, alpha=32 on q,v projections. Fastest variant."""`

**Docstring style:**
- Triple single-quote docstrings (`'''`) in original/graded files (`utils.py`, `prompting.py`, `t5_utils.py`)
- Triple double-quote docstrings (`"""`) in newer infrastructure files (`src/`, `part1/model.py`)
- Inputs section lists parameters with `* param (type): description` format in original files
- Google-style `Args:` / `Returns:` in newer files (`src/utils/gpu_lock.py`, `part3/data.py`)

## Function Design

**Size:** Functions generally kept to 30-60 lines. Longer functions (>100 lines) exist in training loops and are subdivided with `# ──` section comment banners.

**Parameters:**
- Config objects (`cfg`) passed as single argument rather than individual hyperparameters
- Loaders, models, and paths passed explicitly — no global state in training functions
- Optional parameters use `Optional[T]` type hint and default to `None`
- `getattr(cfg, 'field', default)` used defensively when accessing fields that may not exist on older configs

**Return Values:**
- Tuples for multiple return values: `return record_f1, record_em, sql_em, error_rate`
- Named tuple-like returns at function call sites use unpacking: `f1, em, sql_em, err = eval_epoch(...)`
- Functions that both save and return: save side-effect is primary, return value is metric

## Module Design

**Exports:**
- Root stub files use `__all__` to declare public API: `load_data.py`, `src/utils/__init__.py`
- Part modules expose public functions/classes at module level, prefixing private helpers with `_`

**Barrel Files:**
- `src/utils/__init__.py` re-exports from submodules
- `load_data.py` and `t5_utils.py` are graded stubs that delegate to `part1/` implementations

**Config inheritance chain:**
```
BaseConfig
└── SLNeuralConfig
    └── SLNeuralClsConfig
        ├── T5FineTuneConfig          (part1/config.py)
        │   ├── T5FineTuneConfig_lora_v1
        │   ├── T5FineTuneConfig_restricted_v3
        │   └── ... (10+ variants)
        └── T5ScratchConfig           (part2/config.py)
            └── T5ScratchConfig_v2
BaseConfig
└── PromptingConfig                   (part3/config.py)
    ├── PromptingConfig_k1
    └── ...
```

**Two-phase evaluation pattern** (GPU inference decoupled from CPU SQL execution):
```python
# Phase A (GPU): generate predictions
dev_loss, all_preds = eval_epoch_gpu(cfg, model, dev_loader, device)

# Phase B (CPU): run SQL queries and compute metrics (can run async)
future = _sql_pool.submit(eval_epoch_sql, all_preds, ...)
```

---

*Convention analysis: 2026-03-13*
