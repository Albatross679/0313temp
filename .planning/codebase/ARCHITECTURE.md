# Architecture

**Analysis Date:** 2026-03-13

## Pattern Overview

**Overall:** Part-based ML pipeline — three parallel approaches to NL-to-SQL sharing a common infrastructure layer.

**Key Characteristics:**
- Root-level graded stubs (required by assignment) delegate entirely to `partN/` implementations
- Shared infrastructure in `src/` (config hierarchy, W&B tracking, GPU locking, system metrics) — never duplicated per-part
- Two-phase async evaluation: GPU inference overlaps CPU-bound SQL execution via `ThreadPoolExecutor`
- Config-driven training: dataclass configs select variants; CLI overrides apply on top

## Layers

**Shared Infrastructure (`src/`):**
- Purpose: Cross-cutting concerns shared by all three parts
- Location: `src/`
- Contains: Config hierarchy (`src/config.py`), W&B integration (`src/wandb_utils.py`), GPU lock (`src/utils/gpu_lock.py`), system metrics (`src/utils/system_metrics.py`)
- Depends on: wandb, torch, psutil (optional), pynvml (optional)
- Used by: All `partN/train.py` modules, all root entry points

**Root Graded Stubs:**
- Purpose: Assignment-required file names; pure delegation, no logic
- Location: `train_t5.py`, `load_data.py`, `t5_utils.py`, `prompting.py`, `prompting_utils.py`, `utils.py`, `evaluate.py`
- Contains: Re-exports and thin wrappers that call into `partN/` modules
- Depends on: `part1/`, `part3/`, `utils.py`
- Used by: External graders, `part3/train.py` (imports `create_prompt`, `exp_kshot` from `prompting.py`)

**Part Modules (`part1/`, `part2/`, `part3/`):**
- Purpose: Self-contained approach implementations (fine-tune, from-scratch, prompting)
- Location: `part1/`, `part2/`, `part3/`
- Contains: `config.py` (experiment variants), `data.py` (loading/tokenization), `model.py` (init/save/load), `model_flightdb.py` (restricted vocab wrapper — Parts 1 & 2), `train.py` (full training loop)
- Depends on: `src/`, root utils (`utils.py`, `t5_utils.py`)
- Used by: Root entry points

**Data Layer:**
- Purpose: Raw dataset files and pre-executed SQL records for evaluation
- Location: `data/` (read-only), `records/` (ground truth + generated)
- Contains: `.nl` (natural language queries), `.sql` (ground truth SQL), `.db` (SQLite), `.schema` (JSON DDL), `.pkl` (cached DB records)
- Depends on: Nothing (static)
- Used by: All parts during training and evaluation

**Output Layer:**
- Purpose: Experiment artifacts
- Location: `output/{name}_{timestamp}/` (run dirs), `results/` (submission SQL), `records/` (submission pkl)
- Contains: Checkpoints (`model_best.pt`, `model_last.pt`), `config.json`, `metrics.jsonl`, per-epoch prediction files

## Data Flow

**T5 Fine-tune / From-scratch Training (Parts 1 & 2):**

1. CLI parses args → `load_config(class_name)` instantiates dataclass config from `part1/config.py` or `part2/config.py`
2. `apply_cli_overrides(cfg, cli)` applies non-None CLI flags on top of config defaults
3. `load_t5_data()` → `T5Dataset` tokenizes `.nl` and `.sql` files with T5-small tokenizer → `DataLoader` with dynamic padding collate
4. `initialize_model()` loads pretrained weights (fine-tune) or random-init from config (scratch); optionally wraps in `T5ForFlightSQL` (restricted vocab) or applies LoRA adapters
5. Auto-batch tuning probes VRAM to find optimal batch size
6. Training loop: `train_epoch()` → cross-entropy loss → AdamW + cosine/linear scheduler
7. Every `eval_every_n_epochs`: `eval_epoch_gpu()` (Phase A, GPU) generates predictions, then `eval_epoch_sql()` (Phase B, CPU) executes SQL against `data/flight_database.db` via `ThreadPoolExecutor`
8. Phase B runs in background `ThreadPoolExecutor` (1 worker) while next epoch trains on GPU — phases overlap
9. On improvement: `save_model()` to `output/.../checkpoints/model_best.pt`; if LoRA, deep-copies and calls `merge_and_unload()` before saving (preserving vanilla T5 checkpoint format)
10. After training: loads best checkpoint, runs final eval, writes `results/t5_{ft|scr}_dev.sql` + `records/t5_{ft|scr}_dev.pkl`, then test inference → `results/t5_{ft|scr}_test.sql`
11. Uploads best checkpoint to W&B as versioned artifact; calls `end_run()`

**LLM Prompting (Part 3):**

1. `prompting.py` (or `part3/train.py`) parses args → loads `PromptingConfig`
2. `load_prompting_data()` loads raw text lists (no tokenization)
3. `read_schema()` reads `data/flight_database.schema` → formats CREATE TABLE DDL
4. Optional: `build_bm25_index(train_x)` for per-query BM25 example retrieval
5. `initialize_model_and_tokenizer()` loads Gemma 2B or CodeGemma 7B (optionally 4-bit NF4)
6. `exp_kshot()` iterates queries: `create_prompt()` assembles `<start_of_turn>user/model` format → `model.generate()` → `extract_sql_query()` extracts SQL with multi-pattern regex
7. `save_queries_and_records()` writes predictions; `compute_metrics()` evaluates
8. Outputs: `results/llm_{experiment}_{split}.sql`, `records/llm_{experiment}_{split}.pkl`

**Evaluation Flow:**
1. `utils.compute_metrics(gt_sql, pred_sql, gt_records, pred_records)`
2. `compute_records()` executes each SQL against `data/flight_database.db` via `ThreadPoolExecutor(32 threads)` with 120s timeout
3. Returns SQL EM, Record EM, Record F1 (primary metric)

**State Management:**
- No global mutable state except `_TOKENIZER` (module-level singleton in `part1/data.py`) and `_SCHEMA_CACHE` (dict, keyed by schema mode)
- Training state (optimizer, scheduler, epoch, best_val) saved to `checkpoints/training_state.pt` for resume support
- W&B run state managed via `src/wandb_utils.py` — `wandb.run` global, always finish before starting new run

## Key Abstractions

**Config Hierarchy:**
- Purpose: Type-safe, JSON-serializable experiment configuration with variant classes
- Examples: `src/config.py` (BaseConfig, SLNeuralConfig, SLNeuralClsConfig), `part1/config.py` (T5FineTuneConfig and 11+ variants), `part2/config.py` (T5ScratchConfig variants), `part3/config.py` (PromptingConfig variants)
- Pattern: `@dataclass` inheritance — subclasses only override differing fields. `to_dict()`/`from_dict()` for JSON round-trip. CLI arg names map to config field names via `_CLI_TO_CFG` dict.

**T5ForFlightSQL (Restricted Vocab Wrapper):**
- Purpose: Projects decoder output against only the ~600 SQL-relevant T5 token embeddings instead of full 32,128 vocab; 54x smaller softmax
- Examples: `part1/model_flightdb.py`, `part2/model_flightdb.py` (both implement same interface)
- Pattern: `nn.Module` wrapper around `T5ForConditionalGeneration`; `restricted_forward()` for training, inner `model.generate()` with `prefix_allowed_tokens_fn` for constrained beam search; `state_dict`/`load_state_dict` delegate to inner model for checkpoint compatibility

**FlightSQLVocab:**
- Purpose: Builds and manages the restricted SQL token set by scanning training SQL files + extra keywords
- Examples: `part1/model_flightdb.py:FlightSQLVocab`, `part2/model_flightdb.py:FlightSQLVocab`
- Pattern: Scans `data/train.sql` and `data/dev.sql` at init; maintains `sql_token_ids` tensor and reverse mapping `_orig_to_restricted` for target remapping

**Two-Phase Async Eval:**
- Purpose: Overlap GPU inference (Phase A) with CPU SQL execution (Phase B) to eliminate evaluation dead time
- Examples: `part1/train.py:eval_epoch_gpu()` / `eval_epoch_sql()`, same pattern in `part2/train.py`
- Pattern: `ThreadPoolExecutor(max_workers=1)` runs Phase B in background; `_pending_list` queue; results collected at start of next epoch or synchronously on final epoch

**GpuLock:**
- Purpose: Serialize GPU tasks across concurrent terminal sessions using `flock` on `/tmp/gpu-task.lock`
- Examples: `src/utils/gpu_lock.py`, used as `with GpuLock(): main()` in all training entry points
- Pattern: Context manager + decorator; compatible with shell `script/gpu-lock.sh`

## Entry Points

**`train_t5.py`:**
- Location: `train_t5.py`
- Triggers: `python train_t5.py [--config T5FineTuneConfig*] [--finetune] [hyperparams...]`
- Responsibilities: Sets PYTHONPATH, acquires GPU lock, delegates entirely to `part1.train.main()`

**`part2/train.py` (standalone):**
- Location: `part2/train.py`
- Triggers: `python part2/train.py [--config T5ScratchConfig*] [--configs c1,c2,...]`
- Responsibilities: From-scratch training; `--configs` accepts comma-separated list for sequential multi-config runs; selects winner by Record F1 and copies outputs to submission paths

**`prompting.py`:**
- Location: `prompting.py`
- Triggers: `python prompting.py --shot k --model gemma|codegemma [--example_selection random|bm25]`
- Responsibilities: Acquires GPU lock, loads LLM, runs k-shot prompting on dev/test splits

**`evaluate.py`:**
- Location: `evaluate.py`
- Triggers: `python evaluate.py --predicted_sql ... --predicted_records ... --development_sql ... --development_records ...`
- Responsibilities: Standalone CLI for computing SQL EM, Record EM, Record F1 against ground truth

**`part1/eval_checkpoint.py`:**
- Location: `part1/eval_checkpoint.py`
- Triggers: `python part1/eval_checkpoint.py [--run_dir output/...] [--use_last]`
- Responsibilities: Load checkpoint from output dir, run dev eval, print per-example analysis

## Error Handling

**Strategy:** Fail-fast on configuration errors; graceful degradation for infrastructure (W&B, pynvml, psutil missing → log warning, continue without).

**Patterns:**
- Training interruption: `KeyboardInterrupt` caught in training loop → drains pending async SQL → saves training state → exits cleanly
- SIGTERM: signal handler sets `_STOP_REQUESTED = True`; checked between epochs
- Stop file: `touch STOP` detected between epochs via `Path("STOP").exists()`
- SQL execution errors: caught per-query, stored as error messages; query returns empty records `[]`
- OOM in auto-batch: caught via `RuntimeError` containing "out of memory" → use last working batch size
- W&B unavailable: `try/except ImportError` at module load; all `src/wandb_utils.py` functions no-op gracefully

## Cross-Cutting Concerns

**Logging:** W&B via `src/wandb_utils.py`; all training code calls `log_epoch_metrics()` / `log_extra_params()` — never `wandb.*` directly. Metric namespaces: no prefix (epoch-level), `batch/` (step-level), `timing/`, `tracking/`, `system/`.

**Validation:** Config-level via `@dataclass` field defaults and `__post_init__` (e.g., `resolve_device()`). CLI validation via `argparse` choices.

**Authentication:** HuggingFace token for model downloads (cached in `HF_HOME`); W&B API key from environment. Both set externally; not handled in code.

---

*Architecture analysis: 2026-03-13*
