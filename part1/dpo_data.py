"""Preference data generation for DPO training.

Implements a hybrid approach:
  Phase A -- Model-generated negatives: sample SQL candidates from the model
             and use execution correctness to identify chosen/rejected pairs.
  Phase B -- Execution-aware perturbations: for queries the model already gets
             right, perturb the gold SQL to produce plausible-but-wrong rejected
             candidates verified by execution against flight_database.db.

Produces (nl_text, chosen_sql, rejected_sql) triplets serialized to JSON.
"""

import hashlib
import json
import os
import pickle
import random
import re
import sqlite3
from typing import List, Optional, Tuple

import torch
from tqdm import tqdm

from part1.data import PAD_IDX, _BOS_ID, _TOKENIZER, _load_schema_string

DB_PATH = "data/flight_database.db"
GOLD_CACHE_PATH = "records/gold_train_records.pkl"

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


# ── In-memory SQLite ───────────────────────────────────────────────────
# flight_database.db is only 15 MB — loading it into RAM eliminates all
# filesystem I/O and connection setup overhead for the 42K+ SQL evals.

_MEM_CONN: Optional[sqlite3.Connection] = None


def _get_mem_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Get (or create) an in-memory copy of the flight database.

    Uses sqlite3.backup() to copy the entire on-disk database into a
    :memory: connection once.  Subsequent calls return the same connection.
    Thread-safe for read-only queries (all DPO SQL is SELECT-only).
    """
    global _MEM_CONN
    if _MEM_CONN is not None:
        return _MEM_CONN
    disk_conn = sqlite3.connect(db_path)
    mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
    disk_conn.backup(mem_conn)
    disk_conn.close()
    mem_conn.execute("PRAGMA cache_size = -50000")  # 50 MB cache
    _MEM_CONN = mem_conn
    return _MEM_CONN


# ── SQL execution helper ────────────────────────────────────────────────


def _execute_sql(sql: str, db_path: str = DB_PATH, timeout: float = 10.0,
                 conn: Optional[sqlite3.Connection] = None) -> Optional[frozenset]:
    """Execute SQL and return records as frozenset, or None on error.

    If `conn` is provided, reuses that connection (for in-memory DB).
    A progress handler aborts queries exceeding `timeout` seconds.
    Otherwise falls back to opening a new disk connection with busy_timeout.
    """
    own_conn = False
    try:
        if conn is None:
            conn = sqlite3.connect(db_path, timeout=timeout)
            conn.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
            own_conn = True
        else:
            # In-memory connections need a progress handler for timeouts
            # since there's no file lock to time out on.
            import time as _time
            _deadline = _time.monotonic() + timeout

            def _check_timeout():
                return 1 if _time.monotonic() > _deadline else 0

            # Check every 10000 SQLite VM instructions (~1-5ms intervals)
            conn.set_progress_handler(_check_timeout, 10000)

        cursor = conn.cursor()
        cursor.execute(sql)
        records = frozenset(cursor.fetchall())

        if not own_conn:
            conn.set_progress_handler(None, 0)  # clear handler
        if own_conn:
            conn.close()
        return records
    except Exception:
        if not own_conn and conn is not None:
            conn.set_progress_handler(None, 0)  # clear handler on error too
        if own_conn:
            try:
                conn.close()
            except Exception:
                pass
        return None


def _execute_sql_sequential(
    sql_list: List[str], conn: sqlite3.Connection, timeout: float = 10.0,
) -> List[Optional[frozenset]]:
    """Execute SQL queries sequentially on a single connection.

    No ThreadPoolExecutor overhead, no file-level lock contention.
    Used with an in-memory connection for maximum throughput.
    """
    results = []
    for sql in sql_list:
        results.append(_execute_sql(sql, conn=conn, timeout=timeout))
    return results


# ── Gold records caching ──────────────────────────────────────────────
# Gold SQL records are deterministic (static DB + static train.sql).
# Computing them takes ~30 min with disk SQLite.  Cache to pickle so
# subsequent runs load in <1 second.


def _sql_list_hash(sql_list: List[str]) -> str:
    """Content hash of the SQL list for cache invalidation."""
    h = hashlib.sha256()
    for s in sql_list:
        h.update(s.encode())
    return h.hexdigest()[:16]


def _load_or_compute_gold_records(
    sql_lines: List[str], db_path: str = DB_PATH,
) -> List[Optional[frozenset]]:
    """Load cached gold records or compute and cache them.

    Cache key is a content hash of all SQL queries, so the cache
    auto-invalidates if train.sql changes.
    """
    current_hash = _sql_list_hash(sql_lines)

    # Try loading from cache
    if os.path.exists(GOLD_CACHE_PATH):
        try:
            with open(GOLD_CACHE_PATH, "rb") as f:
                cached = pickle.load(f)
            if (isinstance(cached, dict)
                    and cached.get("hash") == current_hash
                    and len(cached["records"]) == len(sql_lines)):
                print(f"Loaded cached gold records from {GOLD_CACHE_PATH} "
                      f"({len(cached['records'])} queries)")
                return cached["records"]
            else:
                print("Cache hash mismatch — recomputing gold records")
        except Exception as e:
            print(f"Cache load failed ({e}) — recomputing")

    # Compute using in-memory SQLite (fast sequential).
    # 5s timeout per query — most valid queries finish in <100ms; anything
    # longer is a pathologically complex nested query that yields None.
    print("Computing gold SQL records (in-memory SQLite)...")
    mem_conn = _get_mem_conn(db_path)
    records = _execute_sql_sequential(sql_lines, mem_conn, timeout=5.0)

    # Save cache
    os.makedirs(os.path.dirname(GOLD_CACHE_PATH) or ".", exist_ok=True)
    with open(GOLD_CACHE_PATH, "wb") as f:
        pickle.dump({"hash": current_hash, "records": records}, f)
    print(f"Cached gold records to {GOLD_CACHE_PATH}")

    return records


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
    mem_conn: Optional[sqlite3.Connection] = None,
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
        perturbed_records = _execute_sql(perturbed, db_path, conn=mem_conn)
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

    # Load in-memory SQLite for fast SQL execution
    mem_conn = _get_mem_conn(db_path)

    # Pre-compute gold records (cached to disk across runs)
    gold_records_list = _load_or_compute_gold_records(sql_lines, db_path)
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

            # Execute each candidate against in-memory DB
            correct_candidates = []
            wrong_candidates = []
            for cand in candidates:
                cand = cand.strip()
                if not cand:
                    continue
                cand_records = _execute_sql(cand, db_path, conn=mem_conn)
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
            gold_sql, gold_records, max_pairs_per_example, db_path, rng,
            mem_conn=mem_conn,
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
    """Save preference triplets to JSON as list of dicts."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = [{"nl": t[0], "chosen": t[1], "rejected": t[2]} for t in triplets]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(triplets)} triplets to {path}")


def load_preference_data(path: str) -> List[Tuple[str, str, str]]:
    """Load preference triplets from JSON."""
    with open(path) as f:
        data = json.load(f)
    # Support both dict format and legacy tuple format
    if data and isinstance(data[0], dict):
        return [(d["nl"], d["chosen"], d["rejected"]) for d in data]
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
    parser.add_argument("--model_checkpoint", type=str, default="google-t5/t5-small",
                        help="HuggingFace model ID (google-t5/t5-small or google-t5/t5-base)")
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
    base_model = T5ForConditionalGeneration.from_pretrained(args.model_checkpoint)
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
