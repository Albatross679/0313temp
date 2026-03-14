"""W&B random sweep for DPO hyperparameter search.

Usage (in tmux):
    tmux new -s dpo-sweep
    python part1/dpo_sweep.py [--max-hours 6] [--count 20]
    # Ctrl+B, D to detach

The sweep agent runs trials sequentially in one process.
Each trial gets its own W&B run with swept hyperparameters.
"""

import argparse
import gc
import os
import sys
import time

# Ensure project root is on PYTHONPATH
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
os.environ.setdefault("PYTORCH_ALLOC_CONF", "expandable_segments:True")

import wandb
from part1.config import T5DPOConfig
from part1.dpo_train import main_with_config
from part1.train import cleanup_vram


# ── Sweep search space ──────────────────────────────────────────────────

def build_sweep_config() -> dict:
    return {
        "method": "random",
        "metric": {"name": "record_f1", "goal": "maximize"},
        "parameters": {
            "dpo_beta": {
                "values": [0.05, 0.1, 0.2, 0.3, 0.5],
            },
            "learning_rate": {
                "distribution": "log_uniform_values",
                "min": 1e-7,
                "max": 5e-5,
            },
            "weight_decay": {
                "distribution": "log_uniform_values",
                "min": 1e-4,
                "max": 0.1,
            },
            "grad_clip_norm": {
                "values": [0.5, 1.0, 2.0],
            },
            # Architecture: full-FT DPO vs LoRA DPO
            "architecture": {
                "values": [
                    "full_ft",
                    "lora_qv_r16",
                    "lora_qkvo_r16",
                ],
            },
        },
    }


# ── Architecture presets ─────────────────────────────────────────────────

_ARCHITECTURE_PRESETS = {
    "full_ft":       {},
    "lora_qv_r16":   {"use_lora": True, "lora_r": 16, "lora_alpha": 32,
                      "lora_target_modules": ["q", "v"], "learning_rate": 1e-5},
    "lora_qkvo_r16": {"use_lora": True, "lora_r": 16, "lora_alpha": 32,
                      "lora_target_modules": ["q", "k", "v", "o"], "learning_rate": 1e-5},
}


# ── Sweep trial function ────────────────────────────────────────────────

_SWEEP_START = None
_MAX_HOURS = None


def sweep_train():
    """Single sweep trial. Called by wandb.agent for each parameter combo."""
    if _MAX_HOURS and _SWEEP_START:
        elapsed = (time.time() - _SWEEP_START) / 3600
        if elapsed >= _MAX_HOURS:
            print(f"Sweep time budget exhausted ({elapsed:.1f}h / {_MAX_HOURS}h). Stopping.")
            raise SystemExit(0)

    run = wandb.init()

    # Build config from base, override with swept params
    cfg = T5DPOConfig()
    swept = dict(wandb.config)

    # Apply architecture preset
    arch = swept.pop("architecture", "full_ft")
    for k, v in _ARCHITECTURE_PRESETS[arch].items():
        setattr(cfg, k, v)

    # Apply remaining scalar hyperparameters (swept LR overrides preset LR)
    for key, val in swept.items():
        if hasattr(cfg, key):
            setattr(cfg, key, val)

    # No per-trial time cap — early stopping decides
    cfg.max_wall_clock_hours = None
    cfg.num_epochs = 9999
    cfg.name = f"t5_dpo_sweep_{run.id[:6]}"

    try:
        main_with_config(cfg)
    except Exception as e:
        print(f"Trial failed: {e}")
    finally:
        del cfg
        gc.collect()
        gc.collect()
        cleanup_vram()


# ── Entry point ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="W&B sweep for DPO training")
    parser.add_argument("--count", type=int, default=20,
                        help="Max number of sweep trials (default: 20)")
    parser.add_argument("--max-hours", type=float, default=None,
                        help="Total sweep wall-clock limit in hours")
    parser.add_argument("--sweep-id", type=str, default=None,
                        help="Resume an existing sweep by ID")
    args = parser.parse_args()

    global _SWEEP_START, _MAX_HOURS
    _SWEEP_START = time.time()
    _MAX_HOURS = args.max_hours

    sweep_config = build_sweep_config()

    if args.sweep_id:
        sweep_id = args.sweep_id
        print(f"Resuming sweep: {sweep_id}")
    else:
        sweep_id = wandb.sweep(sweep_config, project="nlp_as3")
        print(f"Created sweep: {sweep_id}")

    print(f"Running up to {args.count} trials")
    if args.max_hours:
        print(f"Total sweep budget: {args.max_hours}h")
    else:
        print("No total time limit — stop manually with Ctrl+C or `touch STOP`")

    wandb.agent(sweep_id, function=sweep_train, count=args.count)


if __name__ == "__main__":
    from src.utils.gpu_lock import GpuLock
    with GpuLock():
        main()
