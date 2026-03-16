---
name: vm-setup
description: Set up a new Vast.ai (or any cloud GPU) VM instance after pulling the ml-base Docker image. Handles environment variables from .env file, project cloning, pip install from pyproject.toml, Backblaze B2 file downloads, and service authentication (W&B, HF, GitHub). Use when the user asks to (1) set up a new VM or cloud instance, (2) configure a fresh Vast.ai machine, (3) run the setup script on a new instance, (4) bootstrap a project on a new GPU machine, (5) "I just spun up a new VM", (6) initialize environment on remote machine.
---

# VM Setup

Run the setup script after SSH into a new Vast.ai instance running the `ml-base` Docker image.

## Prerequisites

1. A running Vast.ai instance using the `ml-base` Docker image
2. A `.env` file with credentials (create locally, scp to VM)

### Required .env format

```
ANTHROPIC_API_KEY=sk-ant-...
B2_APPLICATION_KEY_ID=...
B2_APPLICATION_KEY=...
WANDB_API_KEY=...
HF_TOKEN=hf_...
GH_TOKEN=ghp_...
```

## Usage

```bash
# 1. SCP the .env file to the VM
scp .env root@<vast-ip>:/workspace/.env

# 2. SSH into the VM
ssh root@<vast-ip> -p <port>

# 3. Run the setup script (after first git clone)
# First time: clone manually, then use the script for future VMs
git clone <repo-url> /workspace/project
cd /workspace/project
./script/setup.sh <repo-url> /workspace/.env

# Or if the script is already available:
curl -sL <raw-script-url> | bash -s -- <repo-url> /workspace/.env
```

## What the script does

1. Loads env vars from `.env` and persists to `~/.bashrc`
2. Clones the project repo (or pulls if already cloned)
3. Installs project deps via `pip install -e .` (pyproject.toml)
4. Runs `script/b2-pull.sh` to download model weights from Backblaze B2
5. Authenticates W&B, HuggingFace, and GitHub CLI
6. Verifies Python, PyTorch, CUDA, and GPU availability

## Post-setup

```bash
# Start a tmux session (persists if SSH drops)
tmux new -s work

# Verify Claude Code works
claude

# Start training
python train_t5.py --finetune ...
```

## Adding files to B2 download

Edit `script/b2-pull.sh` to add more files. Each file is a `b2 file download` line:

```bash
b2 file download "b2://mlworkflow/path/to/file" local/path/to/file
```
