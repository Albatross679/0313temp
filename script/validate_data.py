#!/usr/bin/env python3
"""Standalone data validation for the T5 NL-to-SQL pipeline.

Checks:
  1. Dataset sizes: train=4225, dev=466, test=432
  2. Tokenized lengths: no empty encoder/decoder sequences
  3. BOS token: _BOS_ID == 32099
  4. Restricted vocab coverage on dev.sql: 0 missing tokens

Run:
    python script/validate_data.py
"""

import os
import sys

# Ensure project root is on PYTHONPATH
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/huggingface"))


def main():
    results = []

    # ── 1. Dataset sizes ─────────────────────────────────────────────────
    from part1.data import T5Dataset

    expected_sizes = {"train": 4225, "dev": 466, "test": 432}
    all_sizes_ok = True
    for split, expected in expected_sizes.items():
        ds = T5Dataset("data", split)
        actual = len(ds)
        ok = actual == expected
        if not ok:
            all_sizes_ok = False
        print(f"  {split}: {actual} (expected {expected}) {'OK' if ok else 'FAIL'}")
    results.append(("Dataset sizes", all_sizes_ok))

    # ── 2. Tokenized lengths ─────────────────────────────────────────────
    no_empty = True
    for split in ["train", "dev", "test"]:
        ds = T5Dataset("data", split)
        for i in range(len(ds)):
            sample = ds[i]
            enc = sample[0]
            if len(enc) == 0:
                print(f"  FAIL: empty encoder input at {split}[{i}]")
                no_empty = False
                break
            if split != "test" and len(sample) > 1:
                dec = sample[1]
                if len(dec) == 0:
                    print(f"  FAIL: empty decoder target at {split}[{i}]")
                    no_empty = False
                    break
    results.append(("No empty sequences", no_empty))

    # ── 3. BOS token ─────────────────────────────────────────────────────
    from part1.data import _BOS_ID

    bos_ok = _BOS_ID == 32099
    print(f"  _BOS_ID = {_BOS_ID} (expected 32099) {'OK' if bos_ok else 'FAIL'}")
    results.append(("BOS token == 32099", bos_ok))

    # ── 4. Restricted vocab coverage ─────────────────────────────────────
    from part1.model_flightdb import FlightSQLVocab

    vocab = FlightSQLVocab()
    coverage = vocab.verify_coverage("data/dev.sql")
    missing = coverage["missing"]
    vocab_ok = missing == 0
    print(f"  Restricted vocab: {coverage['covered']}/{coverage['total_tokens']} covered, "
          f"{missing} missing {'OK' if vocab_ok else 'FAIL'}")
    if not vocab_ok and coverage["missing_examples"]:
        for tid, tok in coverage["missing_examples"]:
            print(f"    missing: id={tid} token={tok!r}")
    results.append(("Restricted vocab coverage", vocab_ok))

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    all_pass = True
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
        if not ok:
            all_pass = False

    if all_pass:
        print("\nAll checks PASSED.")
    else:
        print("\nSome checks FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
