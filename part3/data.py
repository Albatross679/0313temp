"""Part 3 data: load NL/SQL text files for prompting (no tokenization)."""

import os


def _load_lines(path):
    with open(path) as f:
        return [line.strip() for line in f.readlines()]


def load_prompting_data(data_folder="data"):
    """Load train/dev/test splits as raw text lists.

    Returns:
        train_x, train_y, dev_x, dev_y, test_x
    """
    train_x = _load_lines(os.path.join(data_folder, "train.nl"))
    train_y = _load_lines(os.path.join(data_folder, "train.sql"))
    dev_x = _load_lines(os.path.join(data_folder, "dev.nl"))
    dev_y = _load_lines(os.path.join(data_folder, "dev.sql"))
    test_x = _load_lines(os.path.join(data_folder, "test.nl"))
    return train_x, train_y, dev_x, dev_y, test_x


def build_bm25_index(train_x):
    """Build a BM25 index over training NL questions.

    Args:
        train_x: List of training NL questions.

    Returns:
        BM25Okapi index object.
    """
    from rank_bm25 import BM25Okapi

    tokenized_corpus = [q.lower().split() for q in train_x]
    return BM25Okapi(tokenized_corpus)


def select_examples_bm25(query, train_x, train_y, bm25_index, k):
    """Select top-k training examples most similar to query using BM25.

    Args:
        query: NL question string.
        train_x: List of training NL questions.
        train_y: List of training SQL queries.
        bm25_index: BM25Okapi index.
        k: Number of examples to select.

    Returns:
        List of (nl, sql) tuples.
    """
    tokenized_query = query.lower().split()
    scores = bm25_index.get_scores(tokenized_query)
    top_k_indices = scores.argsort()[-k:][::-1]
    return [(train_x[i], train_y[i]) for i in top_k_indices]
