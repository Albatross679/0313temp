---
name: DPO preference data generation is slow
description: dpo_data.py took ~1.5 hours due to SQLite concurrency bottleneck and lack of caching — fixed with in-memory SQLite + disk caching
type: issue
status: resolved
severity: medium
subtype: performance
created: 2026-03-14
updated: 2026-03-14
tags: [dpo, performance, sqlite, data-generation]
aliases: [dpo-slow-datagen]
---

## Problem

`part1/dpo_data.py` took ~1-1.5 hours to generate preference data for 4,225
training examples. Three sequential bottlenecks:

1. **Gold SQL pre-computation** (~30-74 min): `_execute_sql_batch()` ran 4,225
   queries through `ThreadPoolExecutor(max_workers=16)`, but SQLite uses
   file-level locking, so threads serialized at the lock.

2. **Phase A candidate SQL evaluation** (~30-45 min): up to 42,250 individual
   `_execute_sql()` calls, each opening/closing a disk connection.

3. **Phase B perturbation SQL evaluation** (~5-15 min): same per-query
   connection overhead for perturbation validation.

## Root Causes

### 1. Fake parallelism (ThreadPoolExecutor + SQLite file lock)
SQLite's default journal mode uses file-level write locks. 16 threads compete
for the same lock, making execution effectively serial while paying thread
context-switch overhead. The `as_completed` timeout was set to
`10s × 4225 = 42,250s` (11.7 hours!) as a generous ceiling.

### 2. No persistent caching
Gold SQL records are deterministic (static DB + static `train.sql`), but were
recomputed from scratch on every `dpo_data.py` invocation.

### 3. Per-query connection overhead
Each `_execute_sql()` call performed `sqlite3.connect()` → `execute()` →
`fetchall()` → `close()`. For 42,250+ calls, connection setup/teardown added
significant overhead.

### 4. Expensive queries dominate wall time
Per-query benchmarks on in-memory SQLite showed:
- ~75% of queries execute in <100ms (fast)
- ~20% take 1-4 seconds (complex JOINs)
- ~5% hit the timeout (pathologically nested subqueries)

Even with zero I/O, the slow 25% of queries dominate total execution time.
This means in-memory SQLite helps but doesn't eliminate the bottleneck for
first-run computation.

## Fix Applied (2026-03-14)

Two complementary optimizations in `part1/dpo_data.py`:

### Fix 1: In-memory SQLite (`_get_mem_conn`)

Loads the 15 MB `flight_database.db` into a `:memory:` SQLite connection using
`sqlite3.backup()`. All subsequent SQL execution (gold records, Phase A
candidate validation, Phase B perturbation checks) runs against this in-memory
copy.

**What this does:**
- Eliminates all filesystem I/O for SQL execution
- Eliminates per-query `sqlite3.connect()` / `.close()` overhead — one
  connection is reused for all ~46K queries
- Replaces `ThreadPoolExecutor` with sequential single-connection execution,
  removing fake-parallelism thread overhead

**What this doesn't fix:**
- Queries with expensive execution plans still take 1-5 seconds each, even
  in memory. The SQLite query planner is the bottleneck, not I/O.

**Safety:**
- A `set_progress_handler` callback enforces per-query timeouts (5s default)
  by checking `time.monotonic()` every 10,000 SQLite VM instructions.
  Previously, only `busy_timeout` was used (which only handles lock contention,
  not CPU-bound query execution).
- `check_same_thread=False` is safe because all queries are read-only SELECTs.

### Fix 2: Gold records disk cache (`_load_or_compute_gold_records`)

Caches computed gold records to `records/gold_train_records.pkl` with a
SHA-256 content hash of all SQL queries as a cache key. The cache auto-
invalidates if `train.sql` changes.

**What this does:**
- First run: computes gold records (~10 min with in-memory SQLite, 5s timeout)
  and saves to pickle
- Subsequent runs: loads from pickle in **~5 seconds** (13.9 MB pickle file
  with 4,225 frozensets)
- Cache key is content-based, not timestamp-based, so it's correct even if
  the file is touched without changing

**Benchmark results:**

| Scenario | Gold records time | Phase A+B SQL time | Total est. |
|----------|------------------|--------------------|------------|
| **Before** (disk, ThreadPoolExecutor) | ~30-74 min | ~35-60 min | ~90 min |
| **After, first run** (in-memory, sequential) | ~10 min | ~15-20 min | ~25-30 min |
| **After, cached** (pickle load) | ~5 sec | ~15-20 min | ~15-20 min |

The remaining ~15-20 min is GPU-bound candidate generation (Phase A), which
is the correct bottleneck.

## Files Changed

- `part1/dpo_data.py`:
  - Added `_get_mem_conn()` — loads DB into `:memory:` once, reuses connection
  - Added `_load_or_compute_gold_records()` — compute-once-then-cache pattern
  - Added `_execute_sql_sequential()` — replaces ThreadPoolExecutor
  - Modified `_execute_sql()` — accepts optional `conn` param, adds
    `set_progress_handler` timeout for in-memory connections
  - Modified `_generate_perturbation_pairs()` — accepts `mem_conn` param
  - Modified `generate_preference_data()` — wires up both optimizations
