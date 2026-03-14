"""Preference data generation for DPO training.

Implements a hybrid approach:
  Phase A -- Model-generated negatives: sample SQL candidates from the model
             and use execution correctness to identify chosen/rejected pairs.
  Phase B -- Execution-aware perturbations: for queries the model already gets
             right, perturb the gold SQL to produce plausible-but-wrong rejected
             candidates verified by execution against flight_database.db.

Produces (nl_text, chosen_sql, rejected_sql) triplets serialized to JSON.
"""

import json
import os
import random
import re
import sqlite3
from typing import List, Optional, Tuple

import torch
from tqdm import tqdm

from part1.data import PAD_IDX, _BOS_ID, _TOKENIZER, _load_schema_string

DB_PATH = "data/flight_database.db"

# ── City names (extracted lazily from training data) ─────────────────────

_CITY_NAMES_CACHE: Optional[List[str]] = None


def _get_city_names(sql_path: str = "data/train.sql") -> List[str]:
    """Extract unique city names from training SQL.  Cached after first call."""
    global _CITY_NAMES_CACHE
    if _CITY_NAMES_CACHE is not None:
        return _CITY_NAMES_CACHE
    pattern = re.compile(r"city_name\s*=\s*'([A-Z\s]+)'")
    names = set()
    with open(sql_path) as f:
        for line in f:
            for m in pattern.finditer(line):
                names.add(m.group(1))
    _CITY_NAMES_CACHE = sorted(names)
    return _CITY_NAMES_CACHE


# ── SQL execution helper ────────────────────────────────────────────────


def _execute_sql(sql: str, db_path: str = DB_PATH, timeout: float = 10.0) -> Optional[frozenset]:
    """Execute SQL and return records as frozenset, or None on error/timeout."""
    try:
        conn = sqlite3.connect(db_path, timeout=timeout)
        conn.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
        cursor = conn.cursor()
        cursor.execute(sql)
        records = frozenset(cursor.fetchall())
        conn.close()
        return records
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        return None


def _execute_sql_batch(
    sql_list: List[str], db_path: str = DB_PATH, num_threads: int = 16, timeout: float = 10.0,
) -> List[Optional[frozenset]]:
    """Execute a list of SQL queries in parallel using ThreadPoolExecutor."""
    from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutTimeoutError

    results: dict = {}
    with ThreadPoolExecutor(max_workers=num_threads) as pool:
        futures = {
            pool.submit(_execute_sql, sql, db_path, timeout): i
            for i, sql in enumerate(sql_list)
        }
        try:
            for future in as_completed(futures, timeout=timeout * len(sql_list)):
                idx = futures[future]
                try:
                    results[idx] = future.result(timeout=timeout)
                except Exception:
                    results[idx] = None
        except FutTimeoutError:
            # Some futures didn't complete -- cancel them
            for f in futures:
                if not f.done():
                    f.cancel()

    return [results.get(i, None) for i in range(len(sql_list))]


# ── Perturbation functions ──────────────────────────────────────────────
# Each returns a modified SQL string, or None if the pattern is not found.

def perturb_swap_city(sql: str, rng: random.Random = random) -> Optional[str]:
    """Replace one city_name='X' with a different city from training data."""
    cities = _get_city_names()
    pattern = re.compile(r"city_name\s*=\s*'([A-Z\s]+)'")
    matches = list(pattern.finditer(sql))
    if not matches:
        return None
    match = rng.choice(matches)
    original_city = match.group(1)
    other_cities = [c for c in cities if c != original_city]
    if not other_cities:
        return None
    new_city = rng.choice(other_cities)
    return sql[:match.start(1)] + new_city + sql[match.end(1):]


def perturb_swap_from_to(sql: str) -> Optional[str]:
    """Swap from_airport and to_airport references (reverse flight direction)."""
    if "from_airport" in sql and "to_airport" in sql:
        result = sql.replace("from_airport", "__TEMP_FROM__")
        result = result.replace("to_airport", "from_airport")
        result = result.replace("__TEMP_FROM__", "to_airport")
        return result
    return None


def perturb_alter_time(sql: str, rng: random.Random = random) -> Optional[str]:
    """Change a BETWEEN X AND Y time range."""
    pattern = re.compile(r"BETWEEN\s+(\d+)\s+AND\s+(\d+)")
    match = pattern.search(sql)
    if not match:
        return None
    time_ranges = [(0, 600), (600, 1200), (1200, 1800), (1800, 2400)]
    current = (int(match.group(1)), int(match.group(2)))
    others = [r for r in time_ranges if r != current]
    if not others:
        return None
    new_range = rng.choice(others)
    return (sql[:match.start()]
            + f"BETWEEN {new_range[0]} AND {new_range[1]}"
            + sql[match.end():])


def perturb_alter_date(sql: str, rng: random.Random = random) -> Optional[str]:
    """Change month_number or day_number values."""
    # Try month first
    month_pat = re.compile(r"month_number\s*=\s*(\d+)")
    m = month_pat.search(sql)
    if m:
        old_val = int(m.group(1))
        candidates = [v for v in range(1, 13) if v != old_val]
        new_val = rng.choice(candidates)
        return sql[:m.start(1)] + str(new_val) + sql[m.end(1):]
    # Try day
    day_pat = re.compile(r"day_number\s*=\s*(\d+)")
    m = day_pat.search(sql)
    if m:
        old_val = int(m.group(1))
        candidates = [v for v in range(1, 32) if v != old_val]
        new_val = rng.choice(candidates)
        return sql[:m.start(1)] + str(new_val) + sql[m.end(1):]
    return None


def perturb_drop_where_clause(sql: str, rng: random.Random = random) -> Optional[str]:
    """Remove one AND-joined condition from a WHERE clause."""
    # Match individual AND-joined conditions
    pattern = re.compile(r"\s+AND\s+(\w+\.\w+\s*(?:=|!=|<>|>=|<=|>|<|LIKE)\s*(?:'[^']*'|\d+|\w+\.\w+))")
    matches = list(pattern.finditer(sql))
    if not matches:
        return None
    match = rng.choice(matches)
    # Remove the entire AND + condition
    return sql[:match.start()] + sql[match.end():]


def perturb_swap_aggregation(sql: str, rng: random.Random = random) -> Optional[str]:
    """Swap one aggregation function: MAX<->MIN, COUNT<->SUM."""
    swaps = {"MAX": "MIN", "MIN": "MAX", "COUNT": "SUM", "SUM": "COUNT"}
    pattern = re.compile(r"\b(MAX|MIN|COUNT|SUM|AVG)\s*\(")
    matches = list(pattern.finditer(sql))
    if not matches:
        return None
    match = rng.choice(matches)
    old_fn = match.group(1)
    if old_fn == "AVG":
        new_fn = rng.choice(["MAX", "MIN", "SUM"])
    else:
        new_fn = swaps.get(old_fn, old_fn)
    if new_fn == old_fn:
        return None
    return sql[:match.start(1)] + new_fn + sql[match.end(1):]


def perturb_toggle_distinct(sql: str) -> Optional[str]:
    """Add or remove DISTINCT from the query."""
    if "SELECT DISTINCT" in sql:
        return sql.replace("SELECT DISTINCT", "SELECT", 1)
    elif "SELECT " in sql:
        return sql.replace("SELECT ", "SELECT DISTINCT ", 1)
    return None


def perturb_swap_select_column(sql: str, rng: random.Random = random) -> Optional[str]:
    """Swap a column name in the SELECT clause."""
    # Common column swaps in the flight database
    column_swaps = {
        "flight_id": ["fare_id", "flight_number", "airline_code"],
        "fare_id": ["flight_id", "fare_basis_code"],
        "airline_code": ["flight_id", "flight_number"],
        "flight_number": ["flight_id", "airline_code"],
        "fare_basis_code": ["fare_id"],
        "departure_time": ["arrival_time"],
        "arrival_time": ["departure_time"],
        "one_direction_cost": ["round_trip_cost"],
        "round_trip_cost": ["one_direction_cost"],
    }
    # Find column references in the SELECT clause (before FROM)
    from_idx = sql.upper().find(" FROM ")
    if from_idx < 0:
        return None
    select_part = sql[:from_idx]
    for col, alternatives in column_swaps.items():
        if col in select_part:
            new_col = rng.choice(alternatives)
            # Replace only in the SELECT portion
            new_select = select_part.replace(col, new_col, 1)
            return new_select + sql[from_idx:]
    return None


# Registry of all perturbation functions
_PERTURBATION_FNS = [
    perturb_swap_city,
    perturb_swap_from_to,
    perturb_alter_time,
    perturb_alter_date,
    perturb_drop_where_clause,
    perturb_swap_aggregation,
    perturb_toggle_distinct,
    perturb_swap_select_column,
]


# ── Phase B: Execution-aware perturbations ──────────────────────────────


def _generate_perturbation_pairs(
    gold_sql: str,
    gold_records: frozenset,
    max_pairs: int,
    db_path: str,
    rng: random.Random,
) -> List[Tuple[str, str]]:
    """Generate (chosen=gold, rejected=perturbed) pairs for one example.

    Only keeps perturbations where:
    (a) perturbed SQL executes without error, AND
    (b) perturbed SQL returns DIFFERENT records than original.
    """
    pairs = []
    # Shuffle perturbation order for variety
    fns = list(_PERTURBATION_FNS)
    rng.shuffle(fns)

    for fn in fns:
        if len(pairs) >= max_pairs:
            break
        try:
            perturbed = fn(gold_sql, rng) if "rng" in fn.__code__.co_varnames else fn(gold_sql)
        except Exception:
            continue
        if perturbed is None or perturbed == gold_sql:
            continue
        perturbed_records = _execute_sql(perturbed, db_path)
        if perturbed_records is None:
            continue  # SQL error
        if perturbed_records == gold_records:
            continue  # Same records -- not useful
        pairs.append((gold_sql, perturbed))
    return pairs


# ── Phase A: Model-generated negatives ──────────────────────────────────


def _generate_candidates_batch(
    model,
    vocab,
    tokenizer,
    nl_texts: List[str],
    device: torch.device,
    n_candidates: int,
    temperature: float,
    top_k: int,
    schema_str: str,
    max_new_tokens: int = 512,
) -> List[List[str]]:
    """Generate n_candidates SQL per NL text using sampling from the model.

    Returns a list (one per NL text) of lists of candidate SQL strings.
    """
    # Tokenize inputs with schema prefix
    prefixed = [schema_str + t for t in nl_texts]
    encoded = tokenizer(
        prefixed, padding=True, truncation=True, return_tensors="pt"
    )
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)

    gen_model = model.model  # inner HF model for .generate()

    with torch.inference_mode():
        # Generate n_candidates per input
        # HuggingFace generate with num_return_sequences repeats each input
        # We need to expand input_ids to match
        batch_size = input_ids.shape[0]
        expanded_input_ids = input_ids.repeat_interleave(n_candidates, dim=0)
        expanded_mask = attention_mask.repeat_interleave(n_candidates, dim=0)

        outputs = gen_model.generate(
            input_ids=expanded_input_ids,
            attention_mask=expanded_mask,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_k=top_k,
            num_return_sequences=1,  # already expanded
            decoder_start_token_id=32099,
            prefix_allowed_tokens_fn=vocab.get_prefix_allowed_tokens_fn(),
        )

    decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    decoded = [re.sub(r'(?<=[a-zA-Z0-9_)])\s*,\s*', ' , ', s) for s in decoded]

    # Re-group into per-input lists
    result = []
    for i in range(batch_size):
        start = i * n_candidates
        end = start + n_candidates
        result.append(decoded[start:end])
    return result


# ── Main generation function ────────────────────────────────────────────


def generate_preference_data(
    model,
    vocab,
    tokenizer,
    device: torch.device,
    max_pairs_per_example: int = 3,
    n_candidates: int = 10,
    temperature: float = 1.0,
    top_k: int = 50,
    db_path: str = DB_PATH,
    batch_size: int = 8,
    seed: int = 42,
) -> List[Tuple[str, str, str]]:
    """Generate (nl_text, chosen_sql, rejected_sql) triplets for DPO.

    Hybrid approach:
      Phase A -- Model-generated negatives (for queries the model gets some wrong)
      Phase B -- Execution-aware perturbations (for queries the model gets all right)

    Args:
        model: T5ForFlightSQL instance (policy model for candidate generation)
        vocab: FlightSQLVocab instance
        tokenizer: T5TokenizerFast
        device: torch device
        max_pairs_per_example: max preference pairs per training example
        n_candidates: number of SQL candidates to sample per query
        temperature: sampling temperature
        top_k: top-k sampling parameter
        db_path: path to flight_database.db
        batch_size: batch size for candidate generation
        seed: random seed for reproducibility

    Returns:
        List of (nl_text, chosen_sql, rejected_sql) triplets.
    """
    rng = random.Random(seed)

    # Load training data
    with open("data/train.nl") as f:
        nl_lines = [line.strip() for line in f.readlines()]
    with open("data/train.sql") as f:
        sql_lines = [line.strip() for line in f.readlines()]
    assert len(nl_lines) == len(sql_lines), (
        f"NL/SQL line count mismatch: {len(nl_lines)} vs {len(sql_lines)}"
    )

    schema_str = _load_schema_string(mode="tables")

    # Pre-compute gold records (parallel for speed)
    print("Pre-computing gold SQL records (parallel)...")
    gold_records_list = _execute_sql_batch(sql_lines, db_path, num_threads=16, timeout=10.0)
    valid_gold = sum(1 for r in gold_records_list if r is not None)
    print(f"Gold SQL: {valid_gold}/{len(gold_records_list)} executed successfully")

    model.eval()

    # Phase A: Model-generated negatives
    print(f"\nPhase A: Generating {n_candidates} candidates per query (batch_size={batch_size})...")
    triplets: List[Tuple[str, str, str]] = []
    phase_a_count = 0
    phase_b_count = 0
    skipped_count = 0
    all_correct_indices = []  # indices where model gets all candidates correct

    num_examples = len(nl_lines)
    for batch_start in tqdm(range(0, num_examples, batch_size), desc="Phase A"):
        batch_end = min(batch_start + batch_size, num_examples)
        batch_nl = nl_lines[batch_start:batch_end]

        try:
            batch_candidates = _generate_candidates_batch(
                model, vocab, tokenizer, batch_nl, device,
                n_candidates, temperature, top_k, schema_str,
            )
        except Exception as e:
            print(f"Warning: batch {batch_start}-{batch_end} failed: {e}")
            # Fall back to processing these as all-correct (Phase B)
            for idx in range(batch_start, batch_end):
                all_correct_indices.append(idx)
            continue

        for local_idx, candidates in enumerate(batch_candidates):
            global_idx = batch_start + local_idx
            gold_sql = sql_lines[global_idx]
            gold_records = gold_records_list[global_idx]
            nl_text = nl_lines[global_idx]

            if gold_records is None:
                skipped_count += 1
                continue  # Gold SQL failed -- skip

            # Execute each candidate
            correct_candidates = []
            wrong_candidates = []
            for cand in candidates:
                cand = cand.strip()
                if not cand:
                    continue
                cand_records = _execute_sql(cand, db_path)
                if cand_records is None:
                    continue  # SQL error -- skip this candidate
                if cand_records == gold_records:
                    correct_candidates.append(cand)
                else:
                    wrong_candidates.append(cand)

            if correct_candidates and wrong_candidates:
                # Mix of correct and wrong: use model's own outputs
                pairs_added = 0
                rng.shuffle(correct_candidates)
                rng.shuffle(wrong_candidates)
                for chosen, rejected in zip(correct_candidates, wrong_candidates):
                    if pairs_added >= max_pairs_per_example:
                        break
                    triplets.append((nl_text, chosen, rejected))
                    phase_a_count += 1
                    pairs_added += 1
            elif not correct_candidates and wrong_candidates:
                # All wrong: chosen=gold, rejected=random wrong
                pairs_added = 0
                rng.shuffle(wrong_candidates)
                for rejected in wrong_candidates[:max_pairs_per_example]:
                    triplets.append((nl_text, gold_sql, rejected))
                    phase_a_count += 1
                    pairs_added += 1
            else:
                # All correct (or no valid candidates): Phase B handles this
                all_correct_indices.append(global_idx)

    # Phase B: Execution-aware perturbations for model-correct queries
    print(f"\nPhase B: Generating perturbation pairs for {len(all_correct_indices)} correct queries...")
    for idx in tqdm(all_correct_indices, desc="Phase B"):
        gold_sql = sql_lines[idx]
        gold_records = gold_records_list[idx]
        nl_text = nl_lines[idx]

        if gold_records is None:
            skipped_count += 1
            continue

        pairs = _generate_perturbation_pairs(
            gold_sql, gold_records, max_pairs_per_example, db_path, rng
        )
        for chosen, rejected in pairs:
            triplets.append((nl_text, chosen, rejected))
            phase_b_count += 1

    # Summary stats
    print(f"\n{'='*60}")
    print(f"Preference data generation complete:")
    print(f"  Total triplets:    {len(triplets)}")
    print(f"  Phase A (model):   {phase_a_count}")
    print(f"  Phase B (perturb): {phase_b_count}")
    print(f"  Skipped examples:  {skipped_count}")
    print(f"  All-correct count: {len(all_correct_indices)}")
    print(f"{'='*60}")

    return triplets


# ── Save / Load helpers ─────────────────────────────────────────────────


def save_preference_data(
    triplets: List[Tuple[str, str, str]], path: str
) -> None:
    """Save preference triplets to JSON."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(triplets, f, indent=2)
    print(f"Saved {len(triplets)} triplets to {path}")


def load_preference_data(path: str) -> List[Tuple[str, str, str]]:
    """Load preference triplets from JSON."""
    with open(path) as f:
        data = json.load(f)
    return [tuple(t) for t in data]


# ── CLI entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    from transformers import T5ForConditionalGeneration

    from part1.model_flightdb import FlightSQLVocab, T5ForFlightSQL

    parser = argparse.ArgumentParser(description="Generate DPO preference data")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Path to model checkpoint (default: auto-detect restricted_v3 best)",
    )
    parser.add_argument("--output", type=str, default="output/dpo_preference_data.json")
    parser.add_argument("--n_candidates", type=int, default=10)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top_k", type=int, default=50)
    parser.add_argument("--max_pairs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Find checkpoint
    ckpt_path = args.checkpoint
    if ckpt_path is None:
        import glob

        matches = glob.glob(
            "output/t5_ft_restricted_v3_*/checkpoints/model_best.pt"
        )
        if not matches:
            raise FileNotFoundError(
                "No restricted_v3 checkpoint found. Provide --checkpoint."
            )
        ckpt_path = sorted(matches)[-1]
    print(f"Loading checkpoint: {ckpt_path}")

    # Load model
    base_model = T5ForConditionalGeneration.from_pretrained("google-t5/t5-small")
    base_model.load_state_dict(
        torch.load(ckpt_path, map_location=device, weights_only=True)
    )
    base_model = base_model.to(device)

    vocab = FlightSQLVocab()
    vocab.to(device)
    model = T5ForFlightSQL(base_model, vocab)
    model.eval()

    tokenizer = vocab.tokenizer

    # Generate preference data
    triplets = generate_preference_data(
        model=model,
        vocab=vocab,
        tokenizer=tokenizer,
        device=device,
        max_pairs_per_example=args.max_pairs,
        n_candidates=args.n_candidates,
        temperature=args.temperature,
        top_k=args.top_k,
        batch_size=args.batch_size,
        seed=args.seed,
    )

    # Save
    save_preference_data(triplets, args.output)

    # Summary
    print(f"\nTotal triplets: {len(triplets)}")
    if triplets:
        print("\nSample triplets:")
        for t in triplets[:3]:
            print(f"  NL:       {t[0][:80]}...")
            print(f"  Chosen:   {t[1][:80]}...")
            print(f"  Rejected: {t[2][:80]}...")
            print()
