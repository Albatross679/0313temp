---
name: rl-thread-local-sqlite-hang
description: RL reward computation hangs due to shared SQLite connection across ThreadPoolExecutor threads
type: issue
status: resolved
severity: high
subtype: training
created: 2026-03-14
updated: 2026-03-14
tags: [rl, sqlite, threading, deadlock, reward]
aliases: []
---

## Symptom

After the first generate() call completes in PPO training, the process hangs
indefinitely with 0% GPU, low CPU, all threads in `futex_wait_queue`. No reward
values or batch metrics are ever produced.

## Root Cause

`_get_thread_conn()` returned the global `_MEM_CONN` singleton — all 16
ThreadPoolExecutor threads shared a single SQLite in-memory connection.

Two interacting bugs:

1. **Progress handler race:** `_execute_sql()` calls `conn.set_progress_handler()`
   to enforce a 10-second timeout. With 16 threads sharing one connection, each
   thread's `set_progress_handler()` overwrites the previous thread's handler.
   When thread A finishes and clears the handler (`set_progress_handler(None, 0)`),
   thread B's query loses its timeout protection.

2. **SQLite serialization:** In-memory SQLite with `check_same_thread=False`
   serializes all operations through an internal lock. If thread B has a slow
   query with no timeout (handler cleared by thread A), all other threads block
   on SQLite's lock indefinitely.

## Fix

Give each thread its own in-memory copy of the database:

```python
def _get_thread_conn():
    if not hasattr(_thread_local, 'conn'):
        disk = sqlite3.connect("data/flight_database.db")
        mem = sqlite3.connect(":memory:", check_same_thread=False)
        disk.backup(mem)
        disk.close()
        _thread_local.conn = mem
    return _thread_local.conn
```

Each thread-local copy is ~5 MB. With 16 threads, total overhead is ~80 MB.

## Files Modified

- `part1/rl_train.py:77-91` — `_get_thread_conn()` now creates per-thread copies

## Related

- `issues/rl-ppo-hang-batch-size-8.md` — earlier hang (different root cause)
