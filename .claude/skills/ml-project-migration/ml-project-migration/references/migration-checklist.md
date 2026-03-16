# ML Project Migration Checklist

## Pre-Migration: Audit Source VM

### 1. Inventory Large Files

```bash
# Find files > 100MB (candidates for cloud storage, not Git)
find . -type f -size +100M -exec ls -lh {} \; 2>/dev/null | awk '{print $5, $9}'

# Check total size of key directories
du -sh model/ output/ data/ .cache/ ~/.cache/huggingface/ 2>/dev/null

# Check Git repo size
git count-objects -vH
```

### 2. Catalog What Exists

| Category | Typical Contents | Transfer Via |
|----------|-----------------|-------------|
| Code & configs | `*.py`, `*.yaml`, `*.json`, `*.toml`, `requirements.txt`, `Makefile` | Git |
| Documentation | `*.md`, `*.tex`, `report/`, `README` | Git |
| Small data | `data/*.sql`, `data/*.csv` (<50 MB) | Git (or Git LFS) |
| Large data | datasets >100 MB, `.db` files | Cloud storage |
| Model weights | `model/`, `*.pt`, `*.bin`, `*.safetensors` | Cloud storage |
| Checkpoints | `output/`, `checkpoint-*/` | Cloud storage (or re-train) |
| HF cache | `~/.cache/huggingface/` | Cloud storage (or re-download) |
| Experiment logs | W&B runs, TensorBoard | Already in cloud (W&B/TB.dev) |
| Secrets | `.env`, API keys, tokens | Manual (never Git) |
| Dot-configs | `.claude/`, `.vscode/`, `.devcontainer/` | Selective (see below) |
| Build artifacts | `__pycache__/`, `*.pyc`, `.mypy_cache/` | Never transfer |

## Phase 1: Git (Code & Configuration)

### What Goes on GitHub

- All source code (`*.py`, `*.sh`)
- Config files (`*.yaml`, `*.json`, `*.toml`, `pyproject.toml`, `setup.py`)
- `requirements.txt` / `environment.yml` / `Pipfile`
- Documentation (`*.md`, `*.tex`, `report/`)
- Small data files (<50 MB) used in evaluation/testing
- `Dockerfile` and `docker-compose.yml`
- `.gitignore`, `.dockerignore`
- `Makefile` or task runners
- CI/CD configs (`.github/workflows/`)
- DVC tracking files (`*.dvc`, `.dvc/config`) if using DVC
- Project-level Claude config (`CLAUDE.md`, shared `.claude/skills/`)

### .gitignore Essentials for ML

```gitignore
# Model artifacts
model/
output/
checkpoint-*/
*.pt
*.bin
*.safetensors
*.onnx

# Data (large)
*.db
*.pkl
data/large/

# Caches
__pycache__/
.mypy_cache/
.pytest_cache/
.ipynb_checkpoints/
*.pyc

# HF/torch cache
.cache/

# Environment
.env
.env.local

# IDE/personal
.vscode/settings.json
.idea/
.claude/settings.local.json
.claude/memory/

# OS
.DS_Store
Thumbs.db

# W&B local
wandb/
```

### Push to GitHub

```bash
# On source VM
git add -A && git commit -m "pre-migration snapshot"
git push origin main

# On target VM
git clone <repo-url>
cd <project>
```

## Phase 2: Cloud Storage (Large Files)

### Option A: Backblaze B2 + rclone

```bash
# Install rclone (if not present)
curl https://rclone.org/install.sh | sudo bash

# Configure Backblaze B2 remote (interactive)
rclone config
# Name: b2
# Type: b2
# Account: <applicationKeyId>
# Key: <applicationKey>

# Upload from source VM
rclone sync model/ b2:my-ml-bucket/project-name/model/ --progress
rclone sync output/ b2:my-ml-bucket/project-name/output/ --progress
rclone sync data/flight_database.db b2:my-ml-bucket/project-name/data/ --progress

# Download on target VM
rclone sync b2:my-ml-bucket/project-name/model/ model/ --progress
rclone sync b2:my-ml-bucket/project-name/output/ output/ --progress
rclone sync b2:my-ml-bucket/project-name/data/flight_database.db data/ --progress
```

### Option B: DVC (Data Version Control)

```bash
# Configure DVC remote (works with S3, GCS, Azure, B2, SSH)
dvc remote add -d myremote s3://my-bucket/dvc-store

# Track large files
dvc add data/flight_database.db
dvc add model/
git add data/flight_database.db.dvc model/.dvc .gitignore
git commit -m "track large files with DVC"
git push

# Push data to remote
dvc push

# On target VM (after git clone)
dvc pull
```

### Option C: Direct Transfer (rsync/scp)

```bash
# Direct VM-to-VM (if network accessible)
rsync -avz --progress model/ user@target-vm:/path/to/project/model/
rsync -avz --progress output/ user@target-vm:/path/to/project/output/

# Or tar + scp for many small files
tar czf model-weights.tar.gz model/
scp model-weights.tar.gz user@target-vm:/path/to/project/
```

### HuggingFace Cache Decision

| Scenario | Recommendation |
|----------|---------------|
| Fast internet on target VM | Re-download (simpler) |
| Slow/metered internet | Transfer via cloud storage |
| Custom/fine-tuned models | Always transfer (not re-downloadable) |
| Base models only | Re-download |

```bash
# Transfer HF cache if needed
rclone sync ~/.cache/huggingface/ b2:my-ml-bucket/hf-cache/ --progress

# On target VM
rclone sync b2:my-ml-bucket/hf-cache/ ~/.cache/huggingface/ --progress
```

## Phase 3: Environment Reproduction

### Option A: Dockerfile (Recommended)

```dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# System deps
RUN apt-get update && apt-get install -y python3 python3-pip git && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Project code
WORKDIR /app
COPY . .

# Default command
CMD ["bash"]
```

```bash
# Build and run
docker build -t ml-project .
docker run --gpus all -it -v $(pwd)/model:/app/model ml-project
```

### Option B: Docker Image (Pre-built)

```bash
# On source VM: build and push
docker build -t myregistry/ml-project:v1 .
docker push myregistry/ml-project:v1

# On target VM: pull and run
docker pull myregistry/ml-project:v1
docker run --gpus all -it myregistry/ml-project:v1
```

### Option C: requirements.txt + venv (Simplest)

```bash
# On target VM
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dockerfile vs Docker Image

| Aspect | Dockerfile | Docker Image |
|--------|-----------|-------------|
| What it is | Build recipe (text file) | Built binary (~GB) |
| Transfer via | Git (tiny) | Registry or cloud storage (large) |
| Reproducible | Yes (rebuild anytime) | Exact snapshot |
| When to use | Default choice | When build is slow/complex or exact binary match needed |
| GPU support | Need nvidia-docker runtime | Same |

## Phase 4: Dot-Folder Handling

### Decision Matrix

| Dot-folder/file | Commit to Git? | Transfer manually? | Regenerated? |
|----------------|---------------|-------------------|-------------|
| `.gitignore` | Yes | N/A (in Git) | No |
| `.dockerignore` | Yes | N/A (in Git) | No |
| `.github/` | Yes | N/A (in Git) | No |
| `.devcontainer/` | Yes | N/A (in Git) | No |
| `.dvc/`, `.dvcignore` | Yes | N/A (in Git) | No |
| `.flake8`, `.pylintrc` | Yes | N/A (in Git) | No |
| `.pre-commit-config.yaml` | Yes | N/A (in Git) | No |
| `.env.example` | Yes | N/A (in Git) | No |
| `CLAUDE.md` | Yes | N/A (in Git) | No |
| `.claude/skills/` (shared) | Yes | N/A (in Git) | No |
| `.claude/settings.local.json` | No | Optional (has local paths) | Recreate |
| `.claude/memory/` | No | Optional (personal) | Personal |
| `.env` | No | Manual copy | Secrets |
| `.vscode/settings.json` | No | Optional | Recreate |
| `.idea/` | No | No | Recreate |
| `.cache/`, `.huggingface/` | No | Via cloud storage | Re-download |
| `.wandb/` | No | No | Regenerated |
| `.ipynb_checkpoints/` | No | No | Regenerated |
| `.mypy_cache/`, `.pytest_cache/` | No | No | Regenerated |
| `__pycache__/` | No | No | Regenerated |

### .claude/ Specific Guidance

```bash
# In .gitignore — exclude personal/machine-specific parts
.claude/settings.local.json
.claude/memory/

# In Git — include project-shared parts
# CLAUDE.md (at repo root)
# .claude/skills/ (shared skills useful to any contributor)
```

To transfer personal `.claude/` config to new VM:
```bash
rsync -avz .claude/memory/ user@new-vm:~/project/.claude/memory/
rsync -avz .claude/settings.local.json user@new-vm:~/project/.claude/settings.local.json
# Then edit settings.local.json to fix any machine-specific paths
```

## Phase 5: Post-Migration Verification

```bash
# 1. Verify code
git log --oneline -5          # confirm history
git status                     # confirm clean

# 2. Verify environment
python3 -c "import torch; print(torch.cuda.is_available())"
pip list | head -20

# 3. Verify data/models
ls -lh model/                  # confirm weights present
ls -lh data/                   # confirm data present

# 4. Verify training can start
python3 train_t5.py --finetune --max_n_epochs 1 --dry_run  # smoke test

# 5. Verify experiment tracking
python3 -c "import wandb; wandb.login()"
```

## Quick Reference: Migration Order

1. `git push` all code and configs from source
2. Upload large files to cloud storage (rclone/DVC)
3. `git clone` on target VM
4. Install environment (Docker or venv + requirements.txt)
5. Download large files from cloud storage
6. Copy secrets (`.env`) and personal configs (`.claude/memory/`) manually
7. Verify everything works with a smoke test
