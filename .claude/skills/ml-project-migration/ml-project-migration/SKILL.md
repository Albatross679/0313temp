---
name: ml-project-migration
description: Guide for migrating ML projects between virtual machines. Covers the full workflow — what to transfer via Git (code, configs, docs), what to transfer via cloud storage like Backblaze B2 or DVC (model weights, datasets, caches), environment reproduction with Docker or venv, and handling dot-folders (.claude/, .env, .vscode/). Use when the user asks to (1) migrate, move, or transfer an ML project to a new VM or machine, (2) set up a new VM for an existing ML project, (3) decide what goes on GitHub vs cloud storage for ML artifacts, (4) create a Dockerfile or Docker image for ML project portability, (5) handle dot-folders and personal configs during migration, (6) back up or archive an ML project for later restoration.
---

# ML Project Migration

Migrate ML projects between VMs in 5 phases: Git push code, cloud-upload large files, clone on target, reproduce environment, verify.

## Workflow

### 1. Audit & Categorize

Before migrating, categorize every file:

- **Git**: code, configs, requirements, docs, small data (<50 MB), Dockerfile, shared `.claude/skills/`, `CLAUDE.md`
- **Cloud storage**: model weights, checkpoints, large datasets, HF cache (if slow internet)
- **Manual**: `.env` secrets, personal `.claude/memory/`, `.claude/settings.local.json`
- **Skip**: `__pycache__/`, `.mypy_cache/`, `.wandb/`, `.ipynb_checkpoints/` (all regenerated)

### 2. Transfer Code via Git

Push all code and configs. Ensure `.gitignore` excludes model weights, large data, caches, secrets, and personal dot-configs.

### 3. Transfer Large Files via Cloud Storage

Use **rclone + Backblaze B2** (simplest) or **DVC** (version-controlled). Transfer: `model/`, `output/`, large `data/` files, optionally HF cache.

For direct VM-to-VM access, `rsync` also works.

### 4. Reproduce Environment

**Dockerfile** (recommended) — commit to Git, rebuild on target. Use `nvidia/cuda` base for GPU projects.

**Docker image** — push pre-built image to registry when builds are slow or exact binary match is needed.

**venv + requirements.txt** — simplest for small projects.

### 5. Verify

Clone, install deps, download large files, copy secrets, run smoke test.

## Detailed Reference

Read [references/migration-checklist.md](references/migration-checklist.md) for:
- Exact commands for each phase (rclone, DVC, rsync, Docker)
- Complete `.gitignore` template for ML projects
- Dot-folder decision matrix (what to commit, transfer, or skip)
- `.claude/` specific guidance
- HF cache transfer decision table
- Post-migration verification checklist
