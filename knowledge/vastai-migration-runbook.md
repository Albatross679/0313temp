---
name: vastai-migration-runbook
description: Step-by-step runbook for migrating this ML project to a new Vast.ai instance
type: knowledge
created: 2026-03-16
updated: 2026-03-16
tags: [migration, vastai, docker, deployment]
aliases: [migration-guide, vm-setup]
---

# Vast.ai Migration Runbook

## Prerequisites

- Docker Hub image: `albatross679/nlp-as3:latest` (built via GitHub Actions)
- Checkpoint on B2: `b2:mlworkflow/nlp-assignment3/checkpoints/model_best.pt` (851 MB)
- Code on GitHub: `git@github.com:Albatross679/nlp_Assignment3.git`

## Step 1: Set GitHub Secrets (one-time)

Go to `https://github.com/Albatross679/0313temp/settings/secrets/actions` and add:

| Secret | Value |
|--------|-------|
| `DOCKERHUB_USERNAME` | `albatross679` |
| `DOCKERHUB_TOKEN` | (your Docker Hub PAT) |

Then trigger the workflow: Actions tab > "Build and Push Docker Image" > "Run workflow".

## Step 2: Create Vast.ai Template

1. Go to `https://cloud.vast.ai/templates/`
2. Create new template:
   - **Image path**: `albatross679/nlp-as3:latest`
   - **Docker options**: `-e B2_APPLICATION_KEY_ID=<your-key-id> -e B2_APPLICATION_KEY=<your-key> -e WANDB_API_KEY=<your-key> -e HF_TOKEN=<your-token>`
   - **Launch mode**: Jupyter + SSH
   - **Disk space**: >= 20 GB (for code + data + checkpoint)
   - **On-start script**: (see below)

### On-start script

```bash
#!/bin/bash
# Clone repo and download checkpoint
cd /workspace
git clone git@github.com:Albatross679/nlp_Assignment3.git project
cd project

# Install rclone and download checkpoint from B2
curl https://rclone.org/install.sh | bash
rclone config create b2 b2 account=$B2_APPLICATION_KEY_ID key=$B2_APPLICATION_KEY
mkdir -p output/t5_ft_base_sweep_1i8vr3_20260314_012024/checkpoints/
rclone copy b2:mlworkflow/nlp-assignment3/checkpoints/model_best.pt \
  output/t5_ft_base_sweep_1i8vr3_20260314_012024/checkpoints/ --progress

# Login to W&B
wandb login $WANDB_API_KEY

echo "Setup complete. Project ready at /workspace/project"
```

## Step 3: Launch Instance

1. Go to `https://cloud.vast.ai/` > Search
2. Filter: GPU >= 16 GB VRAM, CUDA >= 12.1
3. Select machine, use your template
4. Wait for instance to start and on-start script to finish

## Step 4: Verify on the New Instance

```bash
cd /workspace/project

# Check code
git log --oneline -3

# Check environment
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0)}')"

# Check checkpoint
ls -lh output/t5_ft_base_sweep_1i8vr3_20260314_012024/checkpoints/model_best.pt

# Check data
ls -lh data/

# Smoke test
python3 train_t5.py --finetune --max_n_epochs 1

# Check W&B
python3 -c "import wandb; wandb.login()"
```

## Step 5: Transfer Personal Configs (Optional)

From the old VM (or local machine):

```bash
# Transfer .claude/memory/ if you want Claude Code continuity
rsync -avz .claude/memory/ <vast-ssh>:/workspace/project/.claude/memory/

# Or just start fresh — Claude will rebuild context from CLAUDE.md and skills
```

## What Lives Where

| Asset | Location | How to get it |
|-------|----------|---------------|
| Code, configs, docs | GitHub | `git clone` |
| Python environment | Docker Hub | `albatross679/nlp-as3:latest` |
| Model checkpoint (851 MB) | Backblaze B2 | `rclone copy b2:mlworkflow/nlp-assignment3/checkpoints/` |
| Experiment history | W&B cloud | Already synced, just `wandb login` |
| Secrets (API keys) | Vast.ai template env vars | Set in template, never in Git |
| `.claude/` personal config | Manual transfer or recreate | Optional rsync |

## Destroying Old Instance

Before destroying the old VM, verify:
- [ ] Code pushed to GitHub (`git status` shows clean, `git push` done)
- [ ] Checkpoint on B2 (verified with `rclone ls b2:mlworkflow/nlp-assignment3/checkpoints/`)
- [ ] Docker image on Docker Hub (check Actions workflow succeeded)
- [ ] W&B runs synced (check wandb.ai dashboard)
- [ ] Any personal files backed up (`.claude/memory/`, notes, etc.)
