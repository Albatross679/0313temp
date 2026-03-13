"""Part 2: T5 from-scratch config — random initialization. Inherits SLNeuralClsConfig."""

import os
from dataclasses import dataclass, field
from typing import Optional
from src.config import SLNeuralClsConfig, CheckpointingConfig


@dataclass
class T5ScratchConfig(SLNeuralClsConfig):
    name: str = "t5_scr_v1"
    model_checkpoint: str = "google-t5/t5-small"
    finetune: bool = False

    # ── Training hyperparameters ─────────────────────────────────────────
    num_epochs: int = 50
    batch_size: int = 32
    test_batch_size: int = 16
    learning_rate: float = 1e-3
    weight_decay: float = 0.01
    scheduler: str = "cosine"
    patience_epochs: int = 10
    num_warmup_epochs: int = 3
    grad_clip_norm: float = 1.0
    dropout: float = 0.1

    # ── Input formatting ─────────────────────────────────────────────────
    input_prefix: str = ""
    include_schema: bool = False

    # ── Resume / time budget ─────────────────────────────────────────────
    resume_run_dir: Optional[str] = None
    max_wall_clock_hours: Optional[float] = 8

    # ── Restricted output vocabulary ─────────────────────────────────────
    use_restricted_vocab: bool = False

    # ── Decoding ─────────────────────────────────────────────────────────
    max_new_tokens: int = 256
    num_beams: int = 1

    # ── Evaluation ───────────────────────────────────────────────────────
    sql_num_threads: int = field(default_factory=lambda: min(423, os.cpu_count() or 32))

    checkpointing: CheckpointingConfig = field(default_factory=lambda: CheckpointingConfig(save_training_state=True))

    # ── Auto batch size tuning ─────────────────────────────────────────
    auto_batch_size: bool = True

    # ── Anti-repetition (decoding) ───────────────────────────────────────
    repetition_penalty: float = 1.0
    no_repeat_ngram_size: int = 0

    # ── Label smoothing ──────────────────────────────────────────────────
    label_smoothing: float = 0.0


@dataclass
class T5ScratchConfig_v2(T5ScratchConfig):
    """Improved from-scratch config: lower LR, longer training, beam search,
    label smoothing, and schema context. No anti-repetition (SQL needs it)."""
    name: str = "t5_scr_v2_fixed"

    # ── Training: lower LR, longer schedule, more warmup ─────────────────
    learning_rate: float = 3e-4
    num_epochs: int = 200
    patience_epochs: int = 5
    num_warmup_epochs: int = 8

    # ── Input: feed schema so the model can copy table/column names ──────
    include_schema: bool = False

    # ── Decoding: beam search (no anti-repetition — SQL needs repeated n-grams)
    num_beams: int = 4
    max_new_tokens: int = 512
    repetition_penalty: float = 1.0
    no_repeat_ngram_size: int = 0

    # ── Eval speedups: greedy + subset during training, full beam for final ──
    eval_num_beams: int = 1
    eval_subset_size: int = 150

    # ── Label smoothing ──────────────────────────────────────────────────
    label_smoothing: float = 0.1

    eval_every_n_epochs: int = 3


@dataclass
class T5ScratchConfig_restricted(T5ScratchConfig_v2):
    """From-scratch with restricted SQL output vocabulary."""
    name: str = "t5_scr_restricted"
    use_restricted_vocab: bool = True

@dataclass
class T5ScratchConfig_restricted_v2(T5ScratchConfig_v2):
    """From-scratch with restricted SQL output vocabulary."""
    name: str = "t5_scr_restricted_v2"

    use_restricted_vocab: bool = True

    label_smoothing: float = 0

    repetition_penalty: float = 1.0

   