"""Root graded stub: delegates T5 data loading to part1.data.

This file is graded by name and must export the expected symbols.
All implementation lives in part1/data.py.
"""

from part1.data import (
    T5Dataset,
    normal_collate_fn,
    test_collate_fn,
    load_t5_data,
    get_dataloader,
    PAD_IDX,
)

__all__ = [
    "T5Dataset",
    "normal_collate_fn",
    "test_collate_fn",
    "load_t5_data",
    "get_dataloader",
    "PAD_IDX",
]


def load_prompting_data(*args, **kwargs):
    """Delegate to part3.data for prompting data loading."""
    from part3.data import load_prompting_data as _load
    return _load(*args, **kwargs)
