"""W&B Bayesian sweep for T5-base hyperparameter search.

Usage (in tmux):
    tmux new -s sweep
    python part1/sweep.py [--budget 1.5] [--max-hours 12] [--count 100]
    # Ctrl+B, D to detach

The sweep agent runs trials sequentially in one process (no GPU lock needed).
Each trial gets its own W&B run with swept hyperparameters.
"""

import argparse
import os
import sys
import time

# Ensure project root is on PYTHONPATH
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/huggingface"))

import wandb
from part1.config import T5FineTuneConfig_base_v1
from part1.train import main_with_config, cleanup_vram


# ── Sweep search space ──────────────────────────────────────────────────

def build_sweep_config(budget_hours: float) -> dict:
    return {
        "method": "bayes",
        "metric": {"name": "record_f1", "goal": "maximize"},
        "early_terminate": {"type": "hyperband", "min_iter": 8, "eta": 3},
        "parameters": {
            "learning_rate": {
                "distribution": "log_uniform_values",
                "min": 1e-5,
                "max": 1e-3,
            },
            "label_smoothing": {"values": [0, 0.05, 0.1, 0.15]},
            "dropout": {"values": [0, 0.05, 0.1, 0.15, 0.2]},
            "weight_decay": {
                "distribution": "log_uniform_values",
                "min": 1e-3,
                "max": 0.1,
            },
            "include_schema": {"values": [True, False]},
            "num_beams": {"values": [1, 2, 3, 4]},
            # Architecture preset — LoRA and MLP are mutually exclusive
            "architecture": {
                "values": [
                    "full_ft",        # vanilla full fine-tune
                    "lora_qv_r16",    # LoRA r=16 on q,v
                    "lora_qv_r32",    # LoRA r=32 on q,v
                    "lora_qkvo_r16",  # LoRA r=16 on q,k,v,o
                    "lora_qkvo_r32",  # LoRA r=32 on q,k,v,o
                    "mlp_512",        # MLP projection head (512)
                    "mlp_1024",       # MLP projection head (1024)
                ],
            },
        },
    }


# ── Fixed parameters (not swept) ────────────────────────────────────────
# model_checkpoint = google-t5/t5-base
# use_restricted_vocab = True
# use_amp = True (bf16)
# auto_batch_size = True


# ── Architecture presets (LoRA and MLP are mutually exclusive) ────────────

_ARCHITECTURE_PRESETS = {
    "full_ft":       {},
    "lora_qv_r16":   {"use_lora": True, "lora_r": 16, "lora_alpha": 32,  "lora_target_modules": ["q", "v"]},
    "lora_qv_r32":   {"use_lora": True, "lora_r": 32, "lora_alpha": 64,  "lora_target_modules": ["q", "v"]},
    "lora_qkvo_r16": {"use_lora": True, "lora_r": 16, "lora_alpha": 32,  "lora_target_modules": ["q", "k", "v", "o"]},
    "lora_qkvo_r32": {"use_lora": True, "lora_r": 32, "lora_alpha": 64,  "lora_target_modules": ["q", "k", "v", "o"]},
    "mlp_512":       {"use_mlp_head": True, "mlp_dim": 512,  "mlp_dropout": 0.1},
    "mlp_1024":      {"use_mlp_head": True, "mlp_dim": 1024, "mlp_dropout": 0.1},
}


def sweep_train():
    """Single sweep trial. Called by wandb.agent for each parameter combo."""
    # Check total sweep time budget before starting a new trial
    if _MAX_HOURS and _SWEEP_START:
        elapsed = (time.time() - _SWEEP_START) / 3600
        if elapsed >= _MAX_HOURS:
            print(f"Sweep time budget exhausted ({elapsed:.1f}h / {_MAX_HOURS}h). Stopping.")
            raise SystemExit(0)

    run = wandb.init()

    # Build config from base, override with swept params
    cfg = T5FineTuneConfig_base_v1()
    swept = dict(wandb.config)

    # Apply architecture preset (LoRA / MLP / vanilla — mutually exclusive)
    arch = swept.pop("architecture", "full_ft")
    for k, v in _ARCHITECTURE_PRESETS[arch].items():
        setattr(cfg, k, v)

    # Apply remaining scalar hyperparameters
    for key, val in swept.items():
        if hasattr(cfg, key):
            setattr(cfg, key, val)

    # Per-trial time budget and naming
    cfg.max_wall_clock_hours = _BUDGET_HOURS
    cfg.name = f"t5_ft_base_sweep_{run.id[:6]}"

    try:
        main_with_config(cfg)
    finally:
        cleanup_vram()


# ── Entry point ──────────────────────────────────────────────────────────

_BUDGET_HOURS = 1.5   # per-trial budget (module-level so sweep_train can read it)
_SWEEP_START = None   # set in main(), checked in sweep_train()
_MAX_HOURS = None     # total sweep wall clock limit


def main():
    parser = argparse.ArgumentParser(description="W&B sweep for T5-base fine-tuning")
    parser.add_argument("--count", type=int, default=100,
                        help="Max number of sweep trials (default: 100)")
    parser.add_argument("--budget", type=float, default=1.5,
                        help="Wall-clock hours per trial (default: 1.5)")
    parser.add_argument("--max-hours", type=float, default=None,
                        help="Total sweep wall-clock limit in hours (runs until stopped if omitted)")
    parser.add_argument("--sweep-id", type=str, default=None,
                        help="Resume an existing sweep by ID")
    args = parser.parse_args()

    global _BUDGET_HOURS, _SWEEP_START, _MAX_HOURS
    _BUDGET_HOURS = args.budget
    _SWEEP_START = time.time()
    _MAX_HOURS = args.max_hours

    sweep_config = build_sweep_config(args.budget)

    if args.sweep_id:
        sweep_id = args.sweep_id
        print(f"Resuming sweep: {sweep_id}")
    else:
        sweep_id = wandb.sweep(sweep_config, project="nlp_as3")
        print(f"Created sweep: {sweep_id}")

    print(f"Running up to {args.count} trials, {args.budget}h budget each")
    if args.max_hours:
        print(f"Total sweep budget: {args.max_hours}h")
    else:
        print("No total time limit — stop manually with Ctrl+C or `touch STOP`")

    wandb.agent(sweep_id, function=sweep_train, count=args.count)


if __name__ == "__main__":
    from src.utils.gpu_lock import GpuLock
    with GpuLock():
        main()
