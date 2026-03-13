# Testing Patterns

**Analysis Date:** 2026-03-13

## Test Framework

**Runner:**
- pytest 7.4.4 (pinned in `requirements.txt`)
- hypothesis 6.96.1 (property-based testing, listed as dependency but no test files yet written)
- Config: no `pytest.ini`, `setup.cfg [tool:pytest]`, or `pyproject.toml [tool.pytest]` section detected

**Assertion Library:**
- pytest built-in assertions (no separate assertion library)

**Run Commands:**
```bash
pytest                         # Run all tests
pytest -v                      # Verbose output
pytest --tb=short              # Shorter tracebacks
```

## Test File Organization

**Location:**
- No test files currently exist in the project (`test_*.py` or `*_test.py` not found anywhere)
- pytest and hypothesis are installed as dev dependencies (`pyproject.toml` `[project.optional-dependencies] dev`) but are unused

**Naming (prescribed by installed framework):**
- Test files should follow pytest convention: `test_<module>.py`
- Test functions: `test_<behavior>()`
- Test classes: `Test<Module>`

**Structure:**
```
(no tests directory exists — tests would need to be placed alongside modules or in a dedicated tests/ dir)
```

## Test Structure

**Suite Organization:**
- No existing test suites to reference
- Validation logic that could become tests exists in `script/validate_data.py`:
  - Dataset size assertions (train=4225, dev=466, test=432)
  - BOS token ID check (`_BOS_ID == 32099`)
  - Restricted vocab coverage check

**Patterns that exist in non-test validation scripts:**
```python
# script/validate_data.py — manual assertions used as validation checks
from part1.data import T5Dataset
ds = T5Dataset("data", "train")
actual = len(ds)
ok = actual == 4225
print(f"  train: {actual} (expected 4225) {'OK' if ok else 'FAIL'}")
```

**Patterns:**
- Setup pattern: project root added to `sys.path` in each script before imports
- Teardown pattern: no teardown (no test fixtures exist)
- Assertion pattern: `ok = condition; if not ok: sys.exit(1)`

## Mocking

**Framework:** Not used (no `unittest.mock`, `pytest-mock`, or `MagicMock` imports found)

**Patterns:**
- No mocking patterns established in codebase
- Defensive `getattr(cfg, 'field', default)` used in production code as a form of duck-typing tolerance

**What to Mock (recommended for future tests):**
- `wandb.init` / `wandb.log` — to avoid W&B API calls during unit tests
- `torch.cuda.is_available()` — to allow CPU-only test environments
- File I/O (`open`, `pickle.load`) — for unit tests that test parsing logic
- `sqlite3.connect` — for metric computation tests

**What NOT to Mock:**
- `T5Dataset` data loading when testing data pipeline end-to-end
- `FlightSQLVocab` construction (it reads real data files)

## Fixtures and Factories

**Test Data:**
- No pytest fixtures exist
- Real data files in `data/` directory are used by `script/validate_data.py` directly
- Actual database at `data/flight_database.db` used for all SQL execution

**Location:**
- No dedicated fixtures directory
- `records/ground_truth_dev.pkl` serves as a fixed ground-truth artifact for evaluation

## Coverage

**Requirements:** None enforced (no coverage config, no CI pipeline requiring coverage thresholds)

**View Coverage:**
```bash
pytest --cov=. --cov-report=html   # Requires pytest-cov (not installed)
```

## Test Types

**Unit Tests:**
- Not implemented. Candidates based on pure functions in codebase:
  - `utils.compute_sql_exact_match` — deterministic, no I/O
  - `utils.compute_record_exact_match` — deterministic, no I/O
  - `utils.compute_record_F1` — deterministic, no I/O
  - `prompting_utils.extract_sql_query` — deterministic, no I/O
  - `src.config.resolve_device` — conditional on environment
  - `src.config.BaseConfig.from_dict` / `to_dict` — JSON round-trip

**Integration Tests:**
- Not implemented. `script/validate_data.py` is the closest equivalent:
  - Verifies data pipeline produces correct dataset sizes
  - Verifies tokenizer BOS token ID
  - Verifies restricted vocab covers all dev SQL tokens
  - Run as: `python script/validate_data.py`

**E2E Tests:**
- Not implemented. The graded evaluation workflow serves as manual E2E testing:
```bash
python evaluate.py \
  --predicted_sql results/t5_ft_dev.sql \
  --predicted_records records/t5_ft_dev.pkl \
  --development_sql data/dev.sql \
  --development_records records/ground_truth_dev.pkl
```

## Common Patterns

**Async Testing:**
- Not applicable (no async tests)
- The two-phase async eval pattern (`ThreadPoolExecutor` for SQL) is tested manually via training runs

**Error Testing:**
- `script/validate_data.py` uses `sys.exit(1)` for failure, suitable for CI gates:
```python
if not all_pass:
    sys.exit(1)
```

**Property-Based Testing (hypothesis installed but unused):**
- Hypothesis is pinned at 6.96.1 but no `@given` decorators or hypothesis strategies appear anywhere
- Potential candidates: `compute_record_F1` (invariants: score in [0,1], perfect match = 1.0)

## Closest Thing to Automated Tests

The `script/validate_data.py` script serves as the only automated correctness check:
- Location: `script/validate_data.py`
- Run: `python script/validate_data.py`
- Checks: dataset sizes, empty sequences, BOS token ID, restricted vocab coverage
- Exit code: 0 (all pass) or 1 (any fail)

The `part1/eval_checkpoint.py` and `part2/eval_checkpoint.py` scripts serve as manual integration probes — they load a checkpoint and run full dev evaluation, printing metrics and example predictions.

---

*Testing analysis: 2026-03-13*
