"""Part 1: RL fine-tune configs (GRPO / CISPO / PPO). Inherits T5FineTuneConfig."""

from dataclasses import dataclass, field
from typing import Optional

from part1.config import T5FineTuneConfig


# ======================================================================
#  Base GRPO config (shared by GRPO, CISPO, and PPO variants)
# ======================================================================

@dataclass
class T5GRPOConfig(T5FineTuneConfig):
    """GRPO/CISPO/PPO RL fine-tuning on T5 with execution-based reward.

    Builds on the best supervised fine-tune checkpoint. Uses group-relative
    advantage estimation (no critic network for GRPO/CISPO) and online generation.

    RL algorithm selection:
      - "grpo": PPO-style clipped surrogate (DeepSeekMath formulation)
      - "cispo": Clipped IS weights with detached ratio (MiniMax-M1 formulation)
      - "ppo": PPO with learned value head baseline
    """

    # ---- Overrides from T5FineTuneConfig with RL-appropriate defaults ----
    name: str = "t5_ft_grpo"
    model_checkpoint: str = "google-t5/t5-base"
    use_restricted_vocab: bool = True
    include_schema: bool = True
    schema_mode: str = "tables"
    learning_rate: float = 5e-6
    num_epochs: int = 9999                          # early stopping is binding
    batch_size: int = 4                              # queries per batch (generates G*B completions)
    patience_epochs: int = 3                         # fewer patience for RL (each epoch is expensive)
    eval_every_n_epochs: int = 1
    eval_subset_size: int = 0                        # full dev set every epoch
    num_beams: int = 4
    grad_clip_norm: float = 1.0
    max_wall_clock_hours: Optional[float] = None     # no per-config cap; --max_hours at sweep level

    # ---- Training data subsampling ----
    train_subset_size: int = 200                     # subsample training queries per epoch for RL speed; 0 = use all

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
    rl_algorithm: str = "grpo"                       # "grpo", "cispo", or "ppo"
    group_size: int = 4                              # G completions per query (reduced from 8 for speed)
    sampling_temperature: float = 0.7                # temperature for group generation (1.0 makes >85% SQL fail)
    sampling_top_k: int = 50                         # top-k for group generation

    # ---- Generation ----
    top_p: Optional[float] = None                    # nucleus sampling (None = disabled)
    max_completion_length: int = 512                 # max tokens per completion (median gold SQL is 199 tokens, p99=492)
    gen_batch_size: int = 16                         # max sequences per generate() call (bounds peak VRAM)

    # ---- Loss hyperparameters ----
    epsilon: float = 0.2                             # symmetric clipping (GRPO)
    epsilon_high: float = 0.3                        # upper IS weight clip (CISPO)
    kl_beta: float = 0.01                            # KL penalty against reference (0 = no KL)
    use_std_normalization: bool = True               # True=GRPO, False=Dr.GRPO advantage

    # ---- Reward ----
    reward_type: str = "graded"                      # "graded" per user decision (+1, +0.5, -0.5, -1)
    skip_dead_groups: bool = True                    # DAPO-style: skip groups with all-same reward
    reward_scale: float = 1.0                        # multiplicative reward scaling
    reward_clip: Optional[float] = None              # clamp rewards to [-clip, clip]

    # ---- Reference model ----
    reference_model_update: str = "none"             # "none" (frozen), "periodic", "ema"
    reference_update_interval: int = 100             # steps between reference syncs
    ema_decay: float = 0.999                         # EMA decay for reference model

    # ---- CISPO-specific ----
    normalize_by_total_tokens: bool = True           # normalize loss by total tokens (not per-sample)

    # ---- Stability ----
    max_grad_norm_spike_factor: float = 10.0         # skip update if grad_norm > factor * ema
    grad_norm_ema_decay: float = 0.99                # EMA decay for gradient norm tracking


# ======================================================================
#  PPO config (learned value head baseline)
# ======================================================================

@dataclass
class T5PPOConfig(T5GRPOConfig):
    """PPO variant with learned value head baseline.

    Uses a learned value function V(s) instead of GRPO's group-mean baseline.
    The value head is a small MLP on mean-pooled encoder hidden states.
    Supports both pure learned advantage (A = R - V) and hybrid
    (group-relative normalization on top of learned baseline).
    """
    rl_algorithm: str = "ppo"

    # PPO-specific
    value_coef: float = 0.5                          # value loss coefficient in total loss
    entropy_coef: float = 0.01                       # entropy bonus coefficient
    value_clip_range: float = 0.2                    # value function clipping range (0 = disabled)
    advantage_type: str = "learned"                  # "learned" (V head), "group" (GRPO-style), "hybrid"
    value_hidden_dim: int = 512                      # value head MLP hidden dimension
    value_lr: float = 1e-4                           # separate LR for value head
    target_kl: Optional[float] = None                # KL threshold for early stopping within epoch
    num_updates_per_rollout: int = 1                 # gradient steps per batch of rollouts


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


@dataclass
class T5PPOConfig_v1(T5PPOConfig):
    """PPO v1: learned baseline, moderate KL penalty."""
    name: str = "t5_ft_ppo_v1"
    rl_algorithm: str = "ppo"
    kl_beta: float = 0.02
    value_coef: float = 0.5
    entropy_coef: float = 0.01
