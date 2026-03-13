"""Part 3: LLM prompting config. Inherits BaseConfig (no gradient training)."""

from dataclasses import dataclass, field
from typing import Optional
from src.config import BaseConfig


@dataclass
class PromptingConfig(BaseConfig):
    name: str = "llm_v1"

    # ── Model ────────────────────────────────────────────────────────────
    model_name: str = "gemma"            # "gemma" or "codegemma"
    quantize: bool = False               # 4-bit quantization (for codegemma-7b)

    # ── Prompting ────────────────────────────────────────────────────────
    shot: int = 0                        # k-shot (0 = zero-shot)
    prompt_type: int = 0                 # prompt template variant
    max_new_tokens: int = 256
    example_selection: str = "random"    # "random" or "bm25"
    include_schema: bool = True          # include DDL schema in prompt
    include_instructions: bool = True    # include task instructions in prompt

    # ── Evaluation ───────────────────────────────────────────────────────
    eval_splits: list = field(default_factory=lambda: ["dev", "test"])

    # ── Resume / time budget ─────────────────────────────────────────────
    max_wall_clock_hours: Optional[float] = 5


# ── Shot variants ────────────────────────────────────────────────────────

@dataclass
class PromptingConfig_k1(PromptingConfig):
    name: str = "llm_k1"
    shot: int = 1


@dataclass
class PromptingConfig_k3(PromptingConfig):
    name: str = "llm_k3"
    shot: int = 3


# ── BM25 example selection ──────────────────────────────────────────────

@dataclass
class PromptingConfig_bm25(PromptingConfig):
    name: str = "llm_bm25_k3"
    shot: int = 3
    example_selection: str = "bm25"


# ── Ablation configs ────────────────────────────────────────────────────

@dataclass
class AblationNoSchema(PromptingConfig):
    name: str = "ablation_no_schema"
    shot: int = 3
    include_schema: bool = False
    include_instructions: bool = True


@dataclass
class AblationNoInstructions(PromptingConfig):
    name: str = "ablation_no_instructions"
    shot: int = 3
    include_schema: bool = True
    include_instructions: bool = False


@dataclass
class AblationNoExamples(PromptingConfig):
    name: str = "ablation_no_examples"
    shot: int = 0
    include_schema: bool = True
    include_instructions: bool = True


@dataclass
class AblationSchemaOnly(PromptingConfig):
    name: str = "ablation_schema_only"
    shot: int = 0
    include_schema: bool = True
    include_instructions: bool = False


# ── CodeGemma ────────────────────────────────────────────────────────────

@dataclass
class CodeGemmaConfig(PromptingConfig):
    name: str = "llm_codegemma"
    model_name: str = "codegemma"
    quantize: bool = True
    shot: int = 3
