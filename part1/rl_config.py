"""Part 1: RL fine-tune configs (GRPO / CISPO). Inherits T5FineTuneConfig."""

from dataclasses import dataclass, field
from typing import Optional

from part1.config import T5FineTuneConfig


# ======================================================================
#  Base GRPO config (shared by GRPO and CISPO variants)
# ======================================================================

@dataclass
class T5GRPOConfig(T5FineTuneConfig):
    """GRPO/CISPO RL fine-tuning on T5 with execution-based reward.

    Builds on the best supervised fine-tune checkpoint. Uses group-relative
    advantage estimation (no critic network) and online generation.

    RL algorithm selection:
      - "grpo": PPO-style clipped surrogate (DeepSeekMath formulation)
      - "cispo": Clipped IS weights with detached ratio (MiniMax-M1 formulation)
    """

    # ---- Overrides from T5FineTuneConfig with RL-appropriate defaults ----
    name: str = "t5_ft_grpo"
    model_checkpoint: str = "google-t5/t5-base"
    use_restricted_vocab: bool = True
    include_schema: bool = True
    schema_mode: str = "tables"
    learning_rate: float = 5e-6
    num_epochs: int = 9999                          # early stopping is binding
    batch_size: int = 8                              # queries per batch (generates G*B completions)
    patience_epochs: int = 5
    eval_every_n_epochs: int = 1
    eval_subset_size: int = 0                        # full dev set every epoch
    num_beams: int = 4
    grad_clip_norm: float = 1.0
    max_wall_clock_hours: Optional[float] = 1.0      # 1hr per config within 1-2hr total budget

    # ---- LoRA (wider adapter per user decision) ----
    use_lora: bool = True
    lora_r: int = 32
    lora_alpha: int = 64
    lora_target_modules: list = field(default_factory=lambda: ["q", "k", "v", "o"])

    # ---- Base checkpoint to warm-start from ----
    base_checkpoint_path: str = (
        "output/t5_ft_base_sweep_1i8vr3_20260314_012024/checkpoints/model_best.pt"
    )

    # ---- RL algorithm selection ----
    rl_algorithm: str = "grpo"                       # "grpo" or "cispo"
    group_size: int = 8                              # G completions per query
    sampling_temperature: float = 1.0                # temperature for group generation
    sampling_top_k: int = 50                         # top-k for group generation

    # ---- Loss hyperparameters ----
    epsilon: float = 0.2                             # symmetric clipping (GRPO)
    epsilon_high: float = 0.3                        # upper IS weight clip (CISPO)
    kl_beta: float = 0.01                            # KL penalty against reference (0 = no KL)
    use_std_normalization: bool = True               # True=GRPO, False=Dr.GRPO advantage

    # ---- Reward ----
    reward_type: str = "graded"                      # "graded" per user decision (+1, +0.5, -0.5, -1)
    skip_dead_groups: bool = True                    # DAPO-style: skip groups with all-same reward

    # ---- Stability ----
    max_grad_norm_spike_factor: float = 10.0         # skip update if grad_norm > factor * ema
    grad_norm_ema_decay: float = 0.99                # EMA decay for gradient norm tracking


# ======================================================================
#  Concrete variant configs
# ======================================================================

@dataclass
class T5GRPOConfig_grpo(T5GRPOConfig):
    """GRPO variant with optional small KL penalty."""
    name: str = "t5_ft_grpo_v1"
    rl_algorithm: str = "grpo"
    kl_beta: float = 0.02


@dataclass
class T5GRPOConfig_cispo(T5GRPOConfig):
    """CISPO variant -- clipped IS weights, no KL."""
    name: str = "t5_ft_cispo_v1"
    rl_algorithm: str = "cispo"
    kl_beta: float = 0.0
    epsilon_high: float = 0.3
