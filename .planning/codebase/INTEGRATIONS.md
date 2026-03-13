# External Integrations

**Analysis Date:** 2026-03-13

## APIs & External Services

**Experiment Tracking:**
- Weights & Biases (W&B) - Run tracking, metric logging, model artifact storage
  - SDK/Client: `wandb==0.15.10`
  - Auth: W&B API key (not committed; configured via environment)
  - Integration: `src/wandb_utils.py` wraps all W&B calls; never call `wandb.*` directly from training code
  - Project name: `"nlp_as3"` (hardcoded in `src/wandb_utils.py:setup_run`)
  - Metric namespaces: epoch-level (no prefix), `batch/` (per-batch), `timing/`, `tracking/`, `system/`
  - Graceful degradation: `_WANDB_AVAILABLE` flag; all W&B calls no-op if not installed/authenticated

**HuggingFace Hub:**
- Model weights download - T5-small, T5-base, Gemma 2B, CodeGemma 7B
  - SDK/Client: `transformers==4.40.0` (`from_pretrained`)
  - Auth: HuggingFace token (required for gated Gemma models); configured via `HF_HOME` env var
  - All models cached locally at `/home/coder/.cache/huggingface` on training server
  - No runtime network calls expected after initial download

## Data Storage

**Databases:**
- SQLite (flight domain database)
  - Location: `data/flight_database.db` (25 tables, read-only for evaluation)
  - Connection: `sqlite3.connect('data/flight_database.db')` in `utils.py:compute_record`
  - Client: Python stdlib `sqlite3`; no ORM
  - Access pattern: parallel query execution via `ThreadPoolExecutor` with 120-second timeout
  - Schema reference: `data/flight_database.schema` (JSON format with table/column definitions)

**File Storage:**
- Local filesystem only
  - Model checkpoints: `output/<run_name>/checkpoints/model_best.pt`, `model_last.pt`
  - SQL predictions: `results/*.sql` (one query per line)
  - Record pickles: `records/*.pkl` (pickled `(List[records], List[error_msgs])` tuples)
  - Training state: `output/<run_name>/checkpoints/training_state.pt` (for resumable runs)
  - Metrics log: `output/<run_name>/metrics.jsonl` (one JSON object per epoch)
  - Config snapshot: `output/<run_name>/config.json`
  - Run console log: `output/<run_name>/console.log`

**Caching:**
- HuggingFace model cache: `$HF_HOME` (defaults to `~/.cache/huggingface`)
- In-memory schema string cache: `_SCHEMA_CACHE` dict in `part1/data.py` (keyed by schema mode)

## Authentication & Identity

**Auth Provider:**
- HuggingFace token - Required for gated model downloads (Gemma family)
  - Implementation: standard `transformers` `from_pretrained` credential flow; token stored in HF cache
- W&B API key - Required for experiment tracking
  - Implementation: standard `wandb.init` credential flow

## Monitoring & Observability

**Experiment Tracking:**
- W&B (`src/wandb_utils.py`) - primary metrics dashboard
  - Per-epoch metrics logged via `log_epoch_metrics()`
  - Hardware info logged once at run start (GPU name, CUDA version, driver, RAM)
  - Model artifacts uploaded via `log_model_artifact()` at end of training

**System Metrics:**
- `src/utils/system_metrics.py` - collects and logs per-epoch:
  - GPU: memory allocated/reserved/peak (torch.cuda), utilization %, temperature C, power W (pynvml)
  - CPU: utilization % (psutil), process RSS MB
  - RAM: used GB, used % (psutil)

**Error Tracking:**
- None (no Sentry or equivalent)

**Logs:**
- Console output written to `output/<run_name>/console.log` via `ConsoleConfig` (tee to stdout)
- Per-experiment logs for LLM runs saved to `results/llm_<experiment>_<split>_log.txt` via `prompting_utils.save_logs`
- Documentation logs written to `logs/` directory as Markdown files

## CI/CD & Deployment

**Hosting:**
- Single Linux training server (GPU machine)
- No cloud hosting, containerization, or CI pipeline detected

**CI Pipeline:**
- None detected

**Process Management:**
- `nohup` + background process for all long-running jobs
- GPU task serialization via `src/utils/gpu_lock.py` (flock on `/tmp/gpu-task.lock`)
- Shell wrapper at `script/gpu-lock.sh` for non-Python GPU commands
- STOP-file graceful shutdown: `touch STOP` halts training between epochs

## Environment Configuration

**Required env vars:**
- `HF_HOME` - HuggingFace cache directory (set to `/home/coder/.cache/huggingface` on server; defaults to `~/.cache/huggingface`)
- W&B API key - must be set for experiment tracking (standard wandb env var `WANDB_API_KEY`)
- HuggingFace token - must be set for gated model downloads

**Secrets location:**
- Not committed; credentials live in shell environment or `~/.cache/huggingface/token`

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- W&B run data sent to `wandb.ai` on each `wandb.log()` call during training

## Model Registry

**HuggingFace Model IDs used:**
- `google-t5/t5-small` - Part 1 (fine-tune) and Part 2 (config architecture reference for from-scratch init)
- `google-t5/t5-base` - Part 1 optional larger baseline (`T5FineTuneConfig_base_restricted`)
- `google/gemma-1.1-2b-it` - Part 3 default prompting model (2B params, bfloat16)
- `google/codegemma-7b-it` - Part 3 optional larger prompting model (7B params, 4-bit quantized)

**W&B Artifact Storage:**
- Model checkpoints uploaded as versioned artifacts at end of each training run
- Artifact type: `"model"`; named by config name (e.g., `"t5-ft-restricted-v7"`)

---

*Integration audit: 2026-03-13*
