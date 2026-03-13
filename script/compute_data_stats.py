"""Compute data statistics for report Section 1 tables.

Table 1 (Before Preprocessing): raw text stats using T5 tokenizer.
Table 2 (After Preprocessing): per-model tokenized stats with/without schema prefix.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transformers import T5TokenizerFast
from part1.data import _load_schema_string

MODEL_CHECKPOINT = "google-t5/t5-small"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load_lines(path):
    with open(path) as f:
        return [line.strip() for line in f.readlines()]


def main():
    tokenizer = T5TokenizerFast.from_pretrained(MODEL_CHECKPOINT)

    # Load raw data
    splits = {}
    for split in ("train", "dev"):
        nl_lines = load_lines(os.path.join(DATA_DIR, f"{split}.nl"))
        sql_lines = load_lines(os.path.join(DATA_DIR, f"{split}.sql"))
        splits[split] = {"nl": nl_lines, "sql": sql_lines}

    # ===================================================================
    # TABLE 1: Before Preprocessing (raw text stats via T5 tokenizer)
    # ===================================================================
    print("=" * 70)
    print("TABLE 1: Data Statistics Before Preprocessing")
    print("=" * 70)

    table1 = {}
    for split in ("train", "dev"):
        nl = splits[split]["nl"]
        sql = splits[split]["sql"]

        # Tokenize with T5 tokenizer
        nl_tokens = tokenizer(nl, padding=False, truncation=False, return_attention_mask=False)["input_ids"]
        sql_tokens = tokenizer(sql, padding=False, truncation=False, return_attention_mask=False)["input_ids"]

        n_examples = len(nl)
        mean_nl_len = sum(len(t) for t in nl_tokens) / len(nl_tokens)
        mean_sql_len = sum(len(t) for t in sql_tokens) / len(sql_tokens)

        # Vocab size: unique whitespace-split words
        nl_vocab = set()
        for line in nl:
            nl_vocab.update(line.split())
        sql_vocab = set()
        for line in sql:
            sql_vocab.update(line.split())

        table1[split] = {
            "n_examples": n_examples,
            "mean_nl_len": mean_nl_len,
            "mean_sql_len": mean_sql_len,
            "nl_vocab": len(nl_vocab),
            "sql_vocab": len(sql_vocab),
        }

        print(f"\n{split.upper()}:")
        print(f"  Number of examples:        {n_examples}")
        print(f"  Mean sentence length:      {mean_nl_len:.1f} tokens")
        print(f"  Mean SQL query length:     {mean_sql_len:.1f} tokens")
        print(f"  Vocabulary size (NL):      {len(nl_vocab)}")
        print(f"  Vocabulary size (SQL):     {len(sql_vocab)}")

    # LaTeX output for Table 1
    print("\n--- LaTeX rows for Table 1 ---")
    t, d = table1["train"], table1["dev"]
    print(f"Number of examples & {t['n_examples']} & {d['n_examples']} \\\\")
    print(f"Mean sentence length & {t['mean_nl_len']:.1f} & {d['mean_nl_len']:.1f} \\\\")
    print(f"Mean SQL query length & {t['mean_sql_len']:.1f} & {d['mean_sql_len']:.1f} \\\\")
    print(f"Vocabulary size (natural language) & {t['nl_vocab']} & {d['nl_vocab']} \\\\")
    print(f"Vocabulary size (SQL) & {t['sql_vocab']} & {d['sql_vocab']} \\\\")

    # ===================================================================
    # TABLE 2: After Preprocessing (per-model tokenized stats)
    # ===================================================================
    print("\n" + "=" * 70)
    print("TABLE 2: Data Statistics After Preprocessing")
    print("=" * 70)

    schema_string = _load_schema_string(mode="tables")
    print(f"\nSchema prefix ({len(tokenizer.encode(schema_string))} tokens): {schema_string[:80]}...")

    table2 = {}
    for model_name, use_schema in [("T5 Fine-Tune", True), ("T5 From Scratch", False)]:
        print(f"\n--- {model_name} ---")
        prefix = schema_string if use_schema else ""

        for split in ("train", "dev"):
            nl = splits[split]["nl"]
            sql = splits[split]["sql"]

            # Encoder inputs: with or without schema prefix
            enc_inputs = [prefix + line for line in nl] if prefix else nl
            enc_tokens = tokenizer(enc_inputs, padding=False, truncation=False, return_attention_mask=False)["input_ids"]
            dec_tokens = tokenizer(sql, padding=False, truncation=False, return_attention_mask=False)["input_ids"]

            mean_enc_len = sum(len(t) for t in enc_tokens) / len(enc_tokens)
            mean_dec_len = sum(len(t) for t in dec_tokens) / len(dec_tokens)

            # Unique token IDs
            enc_vocab_ids = set()
            for t in enc_tokens:
                enc_vocab_ids.update(t)
            dec_vocab_ids = set()
            for t in dec_tokens:
                dec_vocab_ids.update(t)

            key = (model_name, split)
            table2[key] = {
                "mean_enc_len": mean_enc_len,
                "mean_dec_len": mean_dec_len,
                "enc_vocab": len(enc_vocab_ids),
                "dec_vocab": len(dec_vocab_ids),
            }

            print(f"  {split.upper()}:")
            print(f"    Mean encoder input length:  {mean_enc_len:.1f} tokens")
            print(f"    Mean decoder target length: {mean_dec_len:.1f} tokens")
            print(f"    Encoder token vocab size:   {len(enc_vocab_ids)}")
            print(f"    Decoder token vocab size:   {len(dec_vocab_ids)} (restricted: 598)")

    # LaTeX output for Table 2
    print("\n--- LaTeX rows for Table 2 ---")
    for model_name in ("T5 Fine-Tune", "T5 From Scratch"):
        t = table2[(model_name, "train")]
        d = table2[(model_name, "dev")]
        print(f"\\multicolumn{{3}}{{l}}{{\\textbf{{{model_name}}}}} \\\\")
        print(f"Mean encoder input length & {t['mean_enc_len']:.1f} & {d['mean_enc_len']:.1f} \\\\")
        print(f"Mean decoder target length & {t['mean_dec_len']:.1f} & {d['mean_dec_len']:.1f} \\\\")
        print(f"Encoder token vocab size & {t['enc_vocab']} & {d['enc_vocab']} \\\\")
        print(f"Decoder token vocab size & {t['dec_vocab']} (598 restricted) & {d['dec_vocab']} (598 restricted) \\\\")
        if model_name == "T5 Fine-Tune":
            print("\\midrule")


if __name__ == "__main__":
    main()
