"""Root graded entry point for T5 training.

This script delegates entirely to part1.train.main() which handles:
- Config loading (--config flag selects variant from part1.config)
- Data pipeline (via part1.data)
- Model init, training, evaluation, and test inference
- Checkpoint saving/loading

Usage:
    python train_t5.py                          # default config (T5FineTuneConfig)
    python train_t5.py --config T5FineTuneConfig_lora_v1  # specific variant
    python train_t5.py --num_epochs 10 --learning_rate 1e-4  # CLI overrides
"""

import os
import sys

# Ensure project root is on PYTHONPATH for sibling imports
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Ensure HuggingFace cache is set
os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/huggingface"))

from part1.train import main


if __name__ == "__main__":
    from src.utils.gpu_lock import GpuLock
    with GpuLock():
        main()
