"""Weights & Biases tracking: metrics/params in one setup call."""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

try:
    import wandb
    _WANDB_AVAILABLE = True
except ImportError:
    _WANDB_AVAILABLE = False


def setup_run(cfg, experiment_name: str, **_kw) -> tuple[Path, str]:
    """Create output directory and start W&B run.

    Fresh run: creates output/{name}_{timestamp}/, saves config.json, logs params.
    Resume:    reuses cfg.resume_run_dir.
    Returns (run_dir, wandb_run_id).
    """
    if getattr(cfg, "resume_run_dir", None):
        run_dir = Path(cfg.resume_run_dir)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(cfg.output.base_dir) / f"{cfg.name}_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "checkpoints").mkdir(exist_ok=True)
        with open(run_dir / "config.json", "w") as f:
            json.dump(cfg.to_dict(), f, indent=2)

    wandb_run_id = ""
    if _WANDB_AVAILABLE:
        # Detect active sweep run — don't reinitialize, just define metrics
        in_sweep = (wandb.run is not None
                    and getattr(wandb.run, 'sweep_id', None))
        if not in_sweep:
            resume_run_id = _kw.get("resume_run_id")
            # Finish any previous run before starting a new one
            if wandb.run is not None:
                wandb.finish()
            wandb_kwargs = dict(
                project="nlp_as3",
                name=cfg.name,
                config=cfg.to_dict(),
            )
            if resume_run_id:
                wandb_kwargs["resume"] = "allow"
            wandb.init(**wandb_kwargs)
        else:
            # Sweep run: update config with actual training params
            wandb.config.update(cfg.to_dict(), allow_val_change=True)
        # Custom x-axes: batch/* uses global_step, everything else uses epoch
        wandb.define_metric("global_step")
        wandb.define_metric("epoch")
        wandb.define_metric("batch/*", step_metric="global_step")
        wandb.define_metric("*", step_metric="epoch")
        wandb_run_id = wandb.run.id if wandb.run else ""

    return run_dir, wandb_run_id


def log_epoch_metrics(metrics_dict: dict, step: int):
    """Log numeric metrics for one epoch (or any step-indexed point).

    Batch-level metrics (keys starting with 'batch/') use global_step as x-axis.
    All other metrics use epoch as x-axis.  W&B define_metric handles the routing.
    """
    if not _WANDB_AVAILABLE or wandb.run is None:
        return
    wandb_payload = {k: v for k, v in metrics_dict.items() if isinstance(v, (int, float))}
    if not wandb_payload:
        return
    is_batch = any(k.startswith("batch/") for k in wandb_payload)
    if is_batch:
        wandb_payload["global_step"] = step
    else:
        wandb_payload["epoch"] = step
    wandb.log(wandb_payload, commit=True)


def log_extra_params(params: dict):
    """Log additional params after initial setup (e.g. model size, data counts)."""
    if _WANDB_AVAILABLE and wandb.run is not None:
        wandb.config.update(params, allow_val_change=True)


def log_model_artifact(checkpoint_path: str, artifact_name: str,
                       metadata: dict | None = None):
    """Upload a model checkpoint to W&B as a versioned artifact.

    Args:
        checkpoint_path: Local path to the .pt checkpoint file.
        artifact_name: Name for the artifact (e.g. 't5-ft-restricted-v7').
        metadata: Optional dict of extra metadata (e.g. metrics at save time).
    """
    if not _WANDB_AVAILABLE or wandb.run is None:
        return
    artifact = wandb.Artifact(artifact_name, type="model", metadata=metadata or {})
    artifact.add_file(checkpoint_path)
    wandb.log_artifact(artifact)


def end_run():
    """Finish the W&B run."""
    if _WANDB_AVAILABLE and wandb.run is not None:
        wandb.finish()
