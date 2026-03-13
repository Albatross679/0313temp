# Technology Stack

**Analysis Date:** 2026-03-13

## Languages

**Primary:**
- Python 3.12.3 - All source code (training, evaluation, data processing, utilities)

## Runtime

**Environment:**
- CPython 3.12.3 (Linux 6.8.0-94-generic)

**Package Manager:**
- pip / setuptools (build backend via `pyproject.toml`)
- Lockfile: Not present; pinned versions in `requirements.txt`

## Frameworks

**Core ML:**
- PyTorch 2.1.2 - Tensor operations, model training, CUDA device management
- Transformers 4.40.0 - T5 (`T5ForConditionalGeneration`, `T5Config`, `T5TokenizerFast`), Gemma (`GemmaForCausalLM`, `GemmaTokenizerFast`), `AutoModelForCausalLM`, scheduler utilities
- Accelerate 0.29.3 - CUDA acceleration utilities
- bitsandbytes 0.43.1 - 4-bit NF4 quantization for CodeGemma 7B (`BitsAndBytesConfig`)
- sentencepiece 0.2.0 - Tokenization backend for Gemma models

**Data / Retrieval:**
- NumPy 1.26.0 - Metric computation (`compute_record_F1`) and numerical operations
- rank_bm25 (imported dynamically) - BM25 retrieval index for k-shot example selection (`part3/data.py`)
- NLTK 3.8.1 - Listed as dependency; not heavily used in current codebase surface

**Database:**
- sqlite3 (stdlib) - SQL execution against `data/flight_database.db` in `utils.py`

**Testing:**
- pytest 7.4.4 - Test runner
- hypothesis 6.96.1 - Property-based testing

**Build/Dev:**
- setuptools >= 61.0 - Build backend
- tensorboard (optional dev dependency)
- tqdm 4.66.1 - Training loop and inference progress bars

**Visualization:**
- matplotlib 3.8.0 - Plotting
- plotly 5.18.0 - Interactive plots
- seaborn 0.13.2 - Statistical visualizations

## Key Dependencies

**Critical:**
- `torch==2.1.2` - Core deep learning; CUDA availability gates GPU use (`resolve_device` in `src/config.py`)
- `transformers==4.40.0` - All model loading/inference for T5 and Gemma families
- `bitsandbytes==0.43.1` - Required for CodeGemma 7B 4-bit quantization path in `part3/model.py`
- `wandb==0.15.10` - Experiment tracking; imported with try/except graceful fallback in `src/wandb_utils.py`
- `sentencepiece==0.2.0` - Tokenizer backend required by Gemma tokenizers

**Infrastructure:**
- `psutil>=5.9.0` - RAM and CPU metrics in `src/utils/system_metrics.py`
- `nvidia-ml-py>=12.0.0` - GPU utilization, temperature, power via `pynvml` in `src/utils/system_metrics.py`
- `fcntl` (stdlib) - GPU task serialization lock (`src/utils/gpu_lock.py`)
- `pickle` (stdlib) - Record persistence in `utils.py` and `records/` directory
- `concurrent.futures.ThreadPoolExecutor` (stdlib) - Parallel SQL execution in `utils.py`

## Configuration

**Environment:**
- `HF_HOME` environment variable: controls HuggingFace model cache location; defaults to `~/.cache/huggingface`, set explicitly in `train_t5.py` and implicitly assumed at `/home/coder/.cache/huggingface` on the training server
- No `.env` file; all configuration via dataclass hierarchy in `src/config.py`
- Config serialized to `output/<run_name>/config.json` at run start

**Build:**
- `pyproject.toml` - Project metadata, dependency specs, build system
- `requirements.txt` - Pinned dependency versions for reproducibility

**Model Config Files:**
- `src/config.py` - `BaseConfig` → `SLNeuralConfig` → `SLNeuralClsConfig` dataclass hierarchy
- `part1/config.py` - T5 fine-tune configs (11 named variants + DPO config)
- `part2/config.py` - T5 from-scratch configs (4 named variants)
- `part3/config.py` - LLM prompting configs (8 named variants)

## Platform Requirements

**Development:**
- Python >= 3.10 (as specified in `pyproject.toml`)
- NVIDIA GPU with CUDA support (strongly assumed; device auto-detection falls back to MPS then CPU)
- GPU task lock via `flock` syscall on `/tmp/gpu-task.lock`; Linux-specific (uses `fcntl`)

**Production:**
- Single-GPU training server (Linux)
- All models loaded from local HuggingFace cache (`HF_HOME`)
- `nohup` + background process pattern for all runs > 5 minutes

---

*Stack analysis: 2026-03-13*
