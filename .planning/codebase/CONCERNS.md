# Codebase Concerns

**Analysis Date:** 2026-03-13

## Tech Debt

**Silent optimizer fallback in `t5_utils.py`:**
- Issue: `initialize_optimizer()` has an `else: pass` branch when `optimizer_type != "AdamW"`. The function returns an unbound variable `optimizer`, causing a `NameError` at runtime if any non-AdamW optimizer is configured.
- Files: `t5_utils.py:83-90`
- Impact: Any config setting `optimizer` to something other than `"AdamW"` will crash at optimizer construction time with a confusing `NameError` rather than a helpful message.
- Fix approach: Raise `ValueError(f"Unknown optimizer: {args.optimizer_type}")` in the `else` branch.

**`t5_utils.py` is a dead stub wrapper:**
- Issue: `t5_utils.py` imports `wandb` and defines a no-op `setup_wandb(args): pass`. The real W&B integration lives in `src/wandb_utils.py`. The stub is a graded file so it cannot be removed, but it imports `wandb` at module level, which adds an import dependency.
- Files: `t5_utils.py:8,12-14`
- Impact: If `wandb` is not installed, importing `t5_utils` fails even though it never uses wandb. Diverges from the real wandb integration pattern (`try/except ImportError`).
- Fix approach: Wrap the `import wandb` in a `try/except ImportError` block matching the pattern in `src/wandb_utils.py`.

**`part2/model.py` and `part2/data.py` are pure re-export shims:**
- Issue: Both files contain only `from part1.X import ...` re-exports. Any structural divergence between Part 1 and Part 2 (e.g., different model configs) requires duplicating logic rather than updating the re-export.
- Files: `part2/model.py`, `part2/data.py`
- Impact: Fragile coupling — Part 2 behaviour is fully determined by Part 1 code, which is not obvious from the project structure description in `CLAUDE.md`.
- Fix approach: Acceptable for an assignment; document the coupling explicitly if Part 2 needs its own model init in future.

**Hardcoded timestamp path in `T5DPOConfig`:**
- Issue: `base_checkpoint_path` in `T5DPOConfig` is hardcoded to `"output/t5_ft_restricted_v3_20260311_054501/checkpoints/model_best.pt"`. This path does not exist in the current repository state.
- Files: `part1/config.py:349`
- Impact: Running DPO training with the default config will immediately `AssertionError` because the file is missing. Every new training run produces a new timestamped directory.
- Fix approach: Set default to `None` (already supported via `base_checkpoint_path: Optional[str] = None` on related configs). Add validation logic that auto-discovers the latest `t5_ft_restricted_v3_*` checkpoint, mirroring the warmstart pattern at `part1/train.py:774-778`.

**Duplicate training loop logic across Part 1 and Part 2:**
- Issue: `part1/train.py` and `part2/train.py` contain near-identical implementations of `_collect_async_sql`, `_forward_and_loss`, `train`, `train_epoch`, `eval_epoch_gpu`, `eval_epoch_sql`, `eval_epoch`, and `test_inference`. The Part 2 loop has minor additions (STOP file deletion, `_preflight_check`, sequential multi-config runner) but the core ~700 lines are duplicated.
- Files: `part1/train.py:129-621`, `part2/train.py:127-550`
- Impact: Bug fixes applied to one loop are silently absent from the other. Seen historically with repetition penalty and early-stopping fixes.
- Fix approach: Extract shared training loop into `src/training_loop.py`; have both parts delegate to it with part-specific hooks.

**`CLAUDE.md` documents non-existent `--finetune` flag:**
- Issue: `CLAUDE.md` documents `python train_t5.py --finetune` as the Part 1 invocation. The `train_t5.py` entry point (and `part1/train.py:parse_args`) has no `--finetune` argument. `finetune=True` is the default in `T5FineTuneConfig`.
- Files: `CLAUDE.md:58,82`, `train_t5.py`, `part1/train.py:640-681`
- Impact: Misleads developers; the flag is silently ignored by argparse (no error), so it would just be treated as an unknown argument (or cause a parse error on newer argparse).
- Fix approach: Remove `--finetune` from `CLAUDE.md` examples; document `--config` as the correct way to select variant.

**`CLAUDE.md` documents `--max_n_epochs` but the flag is `--num_epochs`:**
- Issue: `CLAUDE.md:82` shows `--max_n_epochs 20` but the actual CLI argument in `part1/train.py:648` is `--num_epochs`.
- Files: `CLAUDE.md:82`, `part1/train.py:648`
- Impact: Copy-pasting the example command will fail or silently use the default epoch count.
- Fix approach: Update `CLAUDE.md` example to use `--num_epochs`.

---

## Known Bugs

**Bare `except:` swallows all errors during SQL evaluation:**
- Symptoms: If any exception occurs during `compute_records()` (e.g., database lock, OOM, network issue), the outer `except:` catches it silently, fills remaining queries with `"Query timed out"` error messages, and continues.
- Files: `utils.py:108-112`
- Trigger: Concurrent database access under load or unexpected runtime errors in `ThreadPoolExecutor` callbacks.
- Workaround: The per-query `compute_record` function catches individual query errors; the bare `except` only fires on `ThreadPoolExecutor.as_completed` timeout or on futures pool errors.

**`auto_batch_size` in Part 1 catches `(RuntimeError, Exception)` redundantly:**
- Symptoms: `except (RuntimeError, Exception)` is equivalent to `except Exception` since `RuntimeError` is a subclass. Non-OOM `RuntimeError`s (e.g., CUDA device mismatches) are silently swallowed.
- Files: `part1/train.py:142`
- Trigger: Any non-OOM runtime error during batch size probing.
- Workaround: Part 2's version at `part2/train.py:605` correctly checks `"out of memory" in str(e).lower()` before swallowing.

**`DPODataset` uses `test_batch_size` for DPO loader but config lacks `test_batch_size`:**
- Symptoms: `dpo_train.py:364` creates `DataLoader` with `cfg.batch_size`, but `T5DPOConfig` sets `batch_size: int = 8`. Correct. However the `load_t5_data` call at line 370 passes `cfg.test_batch_size` which is inherited from `T5FineTuneConfig` as `16`, not configured for DPO-scale training.
- Files: `part1/dpo_train.py:370`, `part1/config.py:338-349`
- Impact: Minor — dev evaluation uses batch size 16 which is fine, but it is an implicit dependency on the parent config.

---

## Security Considerations

**Arbitrary SQL execution from model-generated output:**
- Risk: `utils.compute_record()` executes arbitrary SQL strings against `data/flight_database.db` with no query sanitization or SQL injection protection.
- Files: `utils.py:128-141`, `part1/dpo_data.py:50-65`
- Current mitigation: The database is read-only (SELECT-only task); SQLite's `cursor.execute()` does not support multi-statement execution by default. Errors are caught per query.
- Recommendations: Add `PRAGMA query_only = ON` to each connection to enforce read-only mode; use `sqlite3.connect(..., isolation_level=None)` with the `check_same_thread=False` flag only in thread pool contexts.

**Hardcoded W&B project name exposes run data to any W&B account with access:**
- Risk: `src/wandb_utils.py:39` hardcodes `project="nlp_as3"`. All runs regardless of user or environment push to this project.
- Files: `src/wandb_utils.py:39`
- Current mitigation: W&B access is gated by the API key in the environment.
- Recommendations: Make project name configurable via environment variable or config field.

---

## Performance Bottlenecks

**Sequential per-example LLM inference in `exp_kshot`:**
- Problem: `prompting.py:125` iterates one example at a time through the LLM inference loop with no batching. Each call to `model.generate()` processes a single input.
- Files: `prompting.py:125-148`
- Cause: The generation loop is `for i, sentence in tqdm(enumerate(inputs))`.
- Improvement path: Batch tokenize inputs and call `model.generate()` on padded batches. For Gemma 2B this could provide 4-8x throughput improvement at the cost of memory and padding overhead.

**`FlightSQLVocab.__init__` re-tokenizes all SQL on every process start:**
- Problem: `part1/model_flightdb.py:66-78` re-reads and re-tokenizes all training and dev SQL files every time a `FlightSQLVocab` instance is created. This runs at startup for both policy and reference model loads in DPO training.
- Files: `part1/model_flightdb.py:53-97`
- Cause: No disk caching of the computed vocabulary mapping.
- Improvement path: Cache the sorted token ID list to a `.pkl` file alongside the SQL data on first build; load from cache on subsequent calls. Estimated savings: 2-5 seconds per startup.

**`compute_records` uses 32 threads by default but SQL timeout is 120 seconds:**
- Problem: `utils.py:96-113` sets a 120-second total timeout for the `as_completed` call but spawns 32 threads. If more than one query hangs, total time can approach 120 seconds even if only a small fraction of queries are slow.
- Files: `utils.py:86-126`
- Cause: The `timeout_secs` applies to the entire batch, not per query.
- Improvement path: Use a per-query timeout via SQLite `PRAGMA busy_timeout` and `conn.set_trace_callback` or a per-future deadline, rather than a global pool timeout.

**`eval_epoch_gpu` computes dev loss AND generates predictions in a single call:**
- Problem: During training (non-final) eval, `_maybe_subset_loader` restricts inference to `eval_subset_size` (default 150) examples, but `_compute_dev_loss` also runs on this subset rather than the full dev set. The dev loss metric therefore tracks different data distributions across epochs.
- Files: `part1/train.py:564-590`
- Cause: Both the loss and generation use the same `loader` variable.
- Improvement path: Compute dev loss on the full dev set always (cheap teacher-forced pass), and only restrict the autoregressive generation to the subset.

---

## Fragile Areas

**`T5ForFlightSQL.state_dict` / `load_state_dict` key remapping:**
- Files: `part1/model_flightdb.py:210-256`
- Why fragile: The key remapping logic manually strips and reconstructs PEFT/LoRA key prefixes (`base_model.model.`, `.base_layer.`). This is sensitive to PEFT library version changes. A PEFT upgrade that changes key naming conventions will silently load mismatched weights (strict=False is not enforced in all paths).
- Safe modification: Always test checkpoint save/load round-trips after any PEFT version change. The `weights_only=True` flag in `load_model_from_checkpoint` does not detect key name mismatches.
- Test coverage: No automated tests for checkpoint round-trip correctness.

**`_generate_predictions` hardcodes `decoder_start_token_id=32099`:**
- Files: `part1/train.py:185`, `part2/train.py:101`, `part1/dpo_data.py:327`
- Why fragile: The token ID `32099` (`<extra_id_0>`) is specific to T5-small's tokenizer vocabulary. It is hardcoded in three separate places. If the model is swapped for one with a different vocabulary (e.g., T5-base uses the same IDs but a different tokenizer config would not), or if T5 config changes, generation will silently produce wrong outputs.
- Safe modification: Derive the BOS token ID programmatically: `_TOKENIZER.convert_tokens_to_ids("<extra_id_0>")` (already done in `part1/data.py:16` for the training-time BOS). Pass this value through configs/function parameters rather than hardcoding.

**`prompting.py` hardcodes Gemma end-of-turn token ID 107:**
- Files: `prompting.py:123`
- Why fragile: The end-of-turn token `eot_token_id = 107` is hardcoded for Gemma. The tokenizer already exposes this via its special tokens. If CodeGemma or a future model uses a different EOT token ID, generation will not stop correctly.
- Safe modification: Derive from tokenizer: `tokenizer.convert_tokens_to_ids("<end_of_turn>")` or check `tokenizer.additional_special_tokens`.

**`T5DPOConfig.base_checkpoint_path` is a hardcoded timestamp path that doesn't exist:**
- Files: `part1/config.py:349`
- Why fragile: Any `part1/dpo_train.py` invocation with the default config will `AssertionError` on line 379 because the path is tied to a specific training run that produced the output checkpoint, which may have been created on a different machine or session.
- Safe modification: Follow the warmstart pattern at `part1/train.py:774-778` which uses `glob.glob` to auto-discover the latest matching checkpoint.

**Async eval overlaps with next training epoch (race conditions in file writes):**
- Files: `part1/train.py:385-394`, `part2/train.py:250-254`
- Why fragile: The design uses epoch-specific file paths (`dev_pred_e{epoch}.sql`) to avoid file conflicts, but the `_sql_pool` is a single-worker `ThreadPoolExecutor` with no flushing guarantee before the next epoch's GPU work finishes. If the SQL worker is slow and early-stopping fires before its result is collected, `epochs_since_improvement` may be off by one for the epoch whose metrics weren't processed.
- Test coverage: No tests for the async overlap path.

---

## Scaling Limits

**SQLite concurrency under `compute_records` thread pool:**
- Current capacity: 32 threads, each opening and closing a new SQLite connection per query.
- Limit: SQLite's default journal mode limits concurrent readers to the number of file handles the OS supports. Under high concurrency (>32 threads), `sqlite3.OperationalError: database is locked` errors can occur, which are silently caught and recorded as empty records.
- Scaling path: Switch to WAL mode (`PRAGMA journal_mode=WAL`) to allow true concurrent reads.

**T5-small context window limits schema inclusion:**
- Current capacity: T5-small input limit is 512 tokens. The `cols` schema mode produces ~731 tokens, documented as overflowing.
- Limit: Full column-level schema cannot be included for all tables simultaneously. Only `tables` (~93 tokens), `top8_cols` (~221), and `top10_cols` (~298) modes fit.
- Scaling path: Use a schema truncation strategy or switch to T5-base (same 512 limit but larger model capacity).

---

## Dependencies at Risk

**`peft` not in `requirements.txt` or `pyproject.toml`:**
- Risk: LoRA training (`use_lora=True` configs) dynamically imports `peft` at `part1/train.py:794`, but `peft` is absent from both `requirements.txt` and `pyproject.toml`.
- Impact: Fresh environment setup will fail with `ImportError` when running any LoRA config variant.
- Migration plan: Add `peft>=0.9.0` (or current tested version) to both `requirements.txt` and `pyproject.toml`.

**`rank_bm25` not in `requirements.txt` or `pyproject.toml`:**
- Risk: BM25 example selection imports `rank_bm25` dynamically at `part3/data.py:34`, but this package is not declared in either manifest.
- Impact: Running `prompting.py --example_selection bm25` on a fresh environment will fail with `ModuleNotFoundError`.
- Migration plan: Add `rank-bm25>=0.7.2` to both `requirements.txt` and `pyproject.toml`.

**`wandb==0.15.10` is significantly behind current releases:**
- Risk: The pinned version predates several W&B API changes around artifact handling and run resumption.
- Impact: `log_model_artifact` and resume functionality may break on W&B API updates.
- Migration plan: Test with `wandb>=0.16.0` and update pin.

---

## Missing Critical Features

**No automated tests for any module:**
- Problem: `pytest` and `hypothesis` are in dev dependencies but zero test files exist in the codebase for core modules (`utils.py`, `t5_utils.py`, `part1/model.py`, `part1/model_flightdb.py`, etc.).
- Blocks: Cannot verify correctness of metric computation (`compute_record_F1`), restricted vocab remapping, checkpoint save/load, or SQL extraction under refactoring.

**No test for the graded output files:**
- Problem: There is no automated check that `results/t5_ft_test.sql`, `results/t5_scr_test.sql`, `results/llm_test.sql`, and their `.pkl` counterparts exist and have the correct line count matching `data/test.nl`.
- Blocks: Silent submission failures if training is interrupted before final test inference.

---

## Test Coverage Gaps

**`utils.compute_record_F1` edge cases not tested:**
- What's not tested: Behaviour when `gt_set` and `model_set` are both empty (returns F1=1.0 due to `precision=1, recall=1`). Division by near-zero in the `1e-8` guard is never exercised.
- Files: `utils.py:167-192`
- Risk: Silent metric inflation for empty-result queries.
- Priority: Medium

**`T5ForFlightSQL` restricted vocab remapping not tested:**
- What's not tested: `remap_targets` returning `-1` for out-of-vocabulary tokens; `state_dict` / `load_state_dict` round-trip with and without LoRA adapters.
- Files: `part1/model_flightdb.py:101-103`, `part1/model_flightdb.py:210-256`
- Risk: Checkpoint loading silently fails with mismatched keys if PEFT version changes.
- Priority: High

**`extract_sql_query` regex extraction not tested:**
- What's not tested: Edge cases like multiple SQL blocks in a response, missing closing backtick, nested quotes, non-SELECT SQL statements.
- Files: `prompting_utils.py:28-70`
- Risk: Silently falls back to raw model output, inflating SQL error rates without clear diagnosis.
- Priority: Medium

**`auto_batch_size` probing not tested:**
- What's not tested: OOM trigger path, behaviour when `target_vram_pct` is exceeded on the first candidate size.
- Files: `part1/train.py:82-150`
- Risk: Could probe with incorrect synthetic tensor shapes if batch collation changes.
- Priority: Low

---

*Concerns audit: 2026-03-13*
