"""Part 1: T5 fine-tune configs. Inherits SLNeuralClsConfig."""

import os
from dataclasses import dataclass, field
from typing import Optional

from src.config import CheckpointingConfig, SLNeuralClsConfig


# ═══════════════════════════════════════════════════════════════════════════
#  Base config (T5-small fine-tune)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class T5FineTuneConfig(SLNeuralClsConfig):
    name: str = "t5_ft_v3"
    model_checkpoint: str = "google-t5/t5-small"
    finetune: bool = True

    # ── Training ──────────────────────────────────────────────────────────
    num_epochs: int = 30
    batch_size: int = 32
    test_batch_size: int = 16
    learning_rate: float = 3e-5
    weight_decay: float = 0.01
    scheduler: str = "cosine"
    num_warmup_epochs: int = 2
    grad_clip_norm: float = 1.0
    dropout: float = 0.1

    # ── Early stopping ────────────────────────────────────────────────────
    # patience counts eval cycles (not raw epochs); with eval_every_n_epochs=4
    # effective patience = 7 * 4 = 28 training epochs
    patience_epochs: int = 7
    patience_tolerance: float = 0.005     # min F1 improvement to reset patience

    # ── Layer freezing ────────────────────────────────────────────────────
    freeze_encoder: bool = False
    freeze_embeddings: bool = False
    unfreeze_last_n_decoder: Optional[int] = None

    # ── Input formatting ──────────────────────────────────────────────────
    input_prefix: str = ""
    include_schema: bool = False

    # ── LoRA ────────────────────────────────────────────────────────────────
    use_lora: bool = False
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list = field(default_factory=lambda: ["q", "v"])

    # ── MLP projection head ─────────────────────────────────────────────────
    use_mlp_head: bool = False
    mlp_dim: int = 1024
    mlp_dropout: float = 0.1

    # ── Restricted output vocabulary ──────────────────────────────────────
    use_restricted_vocab: bool = False

    # ── Decoding ──────────────────────────────────────────────────────────
    max_new_tokens: int = 512
    num_beams: int = 1

    # ── Evaluation ────────────────────────────────────────────────────────
    eval_every_n_epochs: int = 4
    eval_num_beams: int = 1       # greedy during training eval; full beams at final
    eval_subset_size: int = 150   # dev subset during training; full set at final
    sql_num_threads: int = field(default_factory=lambda: min(423, os.cpu_count() or 32))

    # ── Batch size auto-tuning ─────────────────────────────────────────────
    auto_batch_size: bool = True  # try to maximize VRAM usage at startup

    # ── Resume / time budget ──────────────────────────────────────────────
    resume_run_dir: Optional[str] = None
    max_wall_clock_hours: Optional[float] = 5

    # ── Infrastructure ────────────────────────────────────────────────────
    checkpointing: CheckpointingConfig = field(
        default_factory=lambda: CheckpointingConfig(save_training_state=False),
    )

# ═══════════════════════════════════════════════════════════════════════════
#  Restricted-vocab configs
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class T5FineTuneConfig_restricted(T5FineTuneConfig):
    name: str = "t5_ft_restricted"
    use_restricted_vocab: bool = True
    num_beams: int = 4


@dataclass
class T5FineTuneConfig_base_restricted(T5FineTuneConfig):
    name: str = "t5_ft_base_restricted"
    model_checkpoint: str = "google-t5/t5-base"
    use_restricted_vocab: bool = True
    batch_size: int = 16
    num_beams: int = 4


@dataclass
class T5FineTuneConfig_base_v1(T5FineTuneConfig):
    """T5-base fine-tune with restricted_v3 best settings.
    Mirrors T5FineTuneConfig_restricted_v3 but with google-t5/t5-base (~220M params).
    Batch size lowered (16) for VRAM; auto_batch_size will find optimal.
    bf16 AMP enabled by default (inherited from SLNeuralConfig.use_amp=True).
    """
    name: str = "t5_ft_base_v1"
    model_checkpoint: str = "google-t5/t5-base"
    use_restricted_vocab: bool = True
    learning_rate: float = 3e-4
    label_smoothing: float = 0.1
    num_epochs: int = 80
    num_warmup_epochs: int = 2
    include_schema: bool = True
    schema_mode: str = "tables"
    num_beams: int = 4
    min_new_tokens: int = 10
    length_penalty: float = 1.0
    batch_size: int = 16
    max_wall_clock_hours: float = 5.0


# ═══════════════════════════════════════════════════════════════════════════
#  Restricted-vocab experiment configs (10 variants)
# ═══════════════════════════════════════════════════════════════════════════
#
# All use restricted vocab (~600 tokens). Ordered by priority — executor
# runs sequentially and user can `touch STOP` to halt between configs.
#
# Run 1 issues:  F1=0.47, date hallucination (93%), truncation (9.9%)
# Key insight:   from-scratch with LR=3e-4 + label_smoothing=0.1 → F1=0.64+
#
# LoRA variants run first (fastest to train, most promising).

# ── 1. LoRA (baseline): frozen base, adapter-only training ───────────────

@dataclass
class T5FineTuneConfig_lora_v1(T5FineTuneConfig):
    """LoRA r=16, alpha=32 on q,v projections. Fastest variant."""
    name: str = "t5_ft_lora_v1"
    use_restricted_vocab: bool = True
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list = field(default_factory=lambda: ["q", "v"])
    learning_rate: float = 3e-4
    label_smoothing: float = 0.1
    num_epochs: int = 80
    num_warmup_epochs: int = 3
    num_beams: int = 4
    min_new_tokens: int = 10
    length_penalty: float = 1.0


# ── 2. LoRA + tables schema ──────────────────────────────────────────────

@dataclass
class T5FineTuneConfig_lora_v2(T5FineTuneConfig):
    """LoRA with table-name schema augmentation in input."""
    name: str = "t5_ft_lora_v2"
    use_restricted_vocab: bool = True
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list = field(default_factory=lambda: ["q", "v"])
    learning_rate: float = 3e-4
    label_smoothing: float = 0.1
    num_epochs: int = 80
    num_warmup_epochs: int = 3
    include_schema: bool = True
    schema_mode: str = "tables"
    num_beams: int = 4
    min_new_tokens: int = 10
    length_penalty: float = 1.0


# ── 3. LoRA wider: r=32 on q,k,v,o — more adapter capacity ──────────────

@dataclass
class T5FineTuneConfig_lora_v3(T5FineTuneConfig):
    """LoRA r=32, alpha=64 on all attention projections (q,k,v,o)."""
    name: str = "t5_ft_lora_v3"
    use_restricted_vocab: bool = True
    use_lora: bool = True
    lora_r: int = 32
    lora_alpha: int = 64
    lora_dropout: float = 0.05
    lora_target_modules: list = field(default_factory=lambda: ["q", "k", "v", "o"])
    learning_rate: float = 2e-4
    label_smoothing: float = 0.1
    num_epochs: int = 80
    num_warmup_epochs: int = 3
    num_beams: int = 4
    min_new_tokens: int = 10
    length_penalty: float = 1.0


# ── 4. Full fine-tune: higher LR + label smoothing (no schema) ──────────

@dataclass
class T5FineTuneConfig_restricted_v2(T5FineTuneConfig):
    """Conservative fix: higher LR + label smoothing."""
    name: str = "t5_ft_restricted_v2"
    use_restricted_vocab: bool = True
    learning_rate: float = 1e-4
    label_smoothing: float = 0.1
    num_epochs: int = 60
    num_warmup_epochs: int = 3
    num_beams: int = 4
    min_new_tokens: int = 10
    length_penalty: float = 1.0


# ── 5. Full fine-tune + tables schema ────────────────────────────────────

@dataclass
class T5FineTuneConfig_restricted_v3(T5FineTuneConfig):
    """Aggressive: higher LR + label smoothing + schema (tables)."""
    name: str = "t5_ft_restricted_v3"
    use_restricted_vocab: bool = True
    learning_rate: float = 3e-4
    label_smoothing: float = 0.1
    num_epochs: int = 80
    num_warmup_epochs: int = 3
    include_schema: bool = True
    schema_mode: str = "tables"
    num_beams: int = 4
    min_new_tokens: int = 10
    length_penalty: float = 1.0


# ── 6. MLP head: extra layer after decoder, no schema ────────────────────

@dataclass
class T5FineTuneConfig_mlp_v1(T5FineTuneConfig):
    """Post-decoder MLP (1024-dim) with residual before restricted projection."""
    name: str = "t5_ft_mlp_v1"
    use_restricted_vocab: bool = True
    use_mlp_head: bool = True
    mlp_dim: int = 1024
    mlp_dropout: float = 0.1
    learning_rate: float = 1e-4
    label_smoothing: float = 0.1
    num_epochs: int = 80
    num_warmup_epochs: int = 3
    num_beams: int = 4
    min_new_tokens: int = 10
    length_penalty: float = 1.0


# ── 7. MLP head + tables schema ──────────────────────────────────────────

@dataclass
class T5FineTuneConfig_mlp_v2(T5FineTuneConfig):
    """Post-decoder MLP with tables schema augmentation."""
    name: str = "t5_ft_mlp_v2"
    use_restricted_vocab: bool = True
    use_mlp_head: bool = True
    mlp_dim: int = 1024
    mlp_dropout: float = 0.1
    learning_rate: float = 1e-4
    label_smoothing: float = 0.1
    num_epochs: int = 80
    num_warmup_epochs: int = 3
    include_schema: bool = True
    schema_mode: str = "tables"
    num_beams: int = 4
    min_new_tokens: int = 10
    length_penalty: float = 1.0


# ── 8. Frozen encoder + LoRA on decoder only ─────────────────────────────

@dataclass
class T5FineTuneConfig_lora_freeze_enc(T5FineTuneConfig):
    """LoRA on decoder q,v + fully frozen encoder — minimal training."""
    name: str = "t5_ft_lora_freeze_enc"
    use_restricted_vocab: bool = True
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list = field(default_factory=lambda: ["q", "v"])
    freeze_encoder: bool = True
    learning_rate: float = 5e-4
    label_smoothing: float = 0.1
    num_epochs: int = 80
    num_warmup_epochs: int = 3
    num_beams: int = 4
    min_new_tokens: int = 10
    length_penalty: float = 1.0


# ── 9. Frozen encoder (full fine-tune, no LoRA) ─────────────────────────

@dataclass
class T5FineTuneConfig_restricted_v5(T5FineTuneConfig):
    """Frozen encoder: only decoder + output head learn SQL generation."""
    name: str = "t5_ft_restricted_v5"
    use_restricted_vocab: bool = True
    learning_rate: float = 3e-4
    label_smoothing: float = 0.1
    num_epochs: int = 80
    num_warmup_epochs: int = 3
    freeze_encoder: bool = True
    num_beams: int = 4
    min_new_tokens: int = 10
    length_penalty: float = 1.0


# ── 10. Warm-start LoRA: adapters on top of best full fine-tune ───────────

@dataclass
class T5FineTuneConfig_lora_warmstart(T5FineTuneConfig):
    """LoRA r=16 on q,v applied on top of the best restricted_v3 checkpoint.
    Warm-start: pretrained T5 -> load FT checkpoint -> apply LoRA -> train adapters only.
    """
    name: str = "t5_ft_lora_warmstart"
    use_restricted_vocab: bool = True
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list = field(default_factory=lambda: ["q", "v"])
    learning_rate: float = 3e-4
    label_smoothing: float = 0.1
    num_epochs: int = 80
    num_warmup_epochs: int = 3
    num_beams: int = 4
    min_new_tokens: int = 10
    length_penalty: float = 1.0
    base_checkpoint_path: Optional[str] = None


# ── 11. Higher dropout + tables schema — regularization variant ──────────

@dataclass
class T5FineTuneConfig_restricted_v7(T5FineTuneConfig):
    """Higher dropout (0.2) + tables schema."""
    name: str = "t5_ft_restricted_v7"
    use_restricted_vocab: bool = True
    learning_rate: float = 1e-4
    label_smoothing: float = 0.1
    dropout: float = 0.2
    num_epochs: int = 80
    num_warmup_epochs: int = 3
    include_schema: bool = True
    schema_mode: str = "tables"
    num_beams: int = 4
    min_new_tokens: int = 10
    length_penalty: float = 1.0


# ═══════════════════════════════════════════════════════════════════════════
#  DPO (Direct Preference Optimization) config
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class T5DPOConfig(T5FineTuneConfig):
    """DPO training on Phase 1 best model (T5-base expert-sweep-1)."""
    name: str = "t5_ft_dpo"
    model_checkpoint: str = "google-t5/t5-base"
    use_restricted_vocab: bool = True
    include_schema: bool = True
    schema_mode: str = "tables"

    # DPO-specific
    dpo_beta: float = 0.1
    learning_rate: float = 5e-6
    num_epochs: int = 9999          # early stopping is the binding constraint
    batch_size: int = 8
    patience_epochs: int = 5        # 5 eval cycles without improvement
    eval_every_n_epochs: int = 1    # eval every epoch (DPO converges fast)
    eval_subset_size: int = 0       # full dev set every epoch
    num_beams: int = 4
    grad_clip_norm: float = 1.0
    max_wall_clock_hours: Optional[float] = None  # no per-run time cap

    # Preference data
    preference_data_path: str = "output/dpo_preference_data.json"
    base_checkpoint_path: str = "output/t5_ft_base_sweep_1i8vr3_20260314_012024/checkpoints/model_best.pt"


@dataclass
class T5DPOConfig_lora(T5DPOConfig):
    """DPO training with LoRA adapters on the policy model.
    Uses peft disable_adapter_layers() for reference logprobs (single model copy).
    """
    name: str = "t5_ft_dpo_lora"
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list = field(default_factory=lambda: ["q", "v"])
    learning_rate: float = 1e-5  # slightly higher than full FT DPO since only adapters train
