---
phase: 2
slug: dpo-training
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4.4 |
| **Config file** | pyproject.toml (if exists) or default |
| **Quick run command** | `python -c "<inline verification>"` |
| **Full suite command** | `python -m pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds (smoke tests) |

---

## Sampling Rate

- **After every task commit:** Run inline verification command for that task
- **After every plan wave:** Run all smoke tests for that wave's requirements
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | DPO-01 | smoke | `python -c "import json; d=json.load(open('output/dpo_preference_data.json')); assert len(d) > 100; print(f'{len(d)} triplets')"` | Depends on Wave 0 | ⬜ pending |
| 02-01-02 | 01 | 1 | DPO-02 | smoke | `python -c "import json; d=json.load(open('output/dpo_preference_data.json')); t=d[0]; assert 'nl' in t and 'chosen' in t and 'rejected' in t; print('Format OK')"` | Depends on Wave 0 | ⬜ pending |
| 02-01-03 | 01 | 1 | DPO-03 | integration | `python -c "from part1.dpo_train import load_preference_data, DPODataset, dpo_collate_fn; print('DPO imports OK')"` | ✅ (part1/dpo_train.py) | ⬜ pending |
| 02-01-04 | 01 | 1 | DPO-04 | integration | `python -c "from peft import LoraConfig; from part1.config import T5DPOConfig_lora; print('LoRA DPO config OK')"` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | DPO-05 | manual-only | Compare W&B logged metrics for full-FT vs LoRA DPO runs | N/A | ⬜ pending |
| 02-02-02 | 02 | 2 | DPO-06 | smoke | `python -c "import os; assert os.path.exists('results/t5_dpo_dev.sql'); print('Dev eval output exists')"` | Depends on DPO run | ⬜ pending |
| 02-02-03 | 02 | 2 | DPO-07 | smoke | `python -c "import os; assert os.path.exists('results/t5_ft_test.sql') and os.path.getsize('results/t5_ft_test.sql') > 0; print('Test outputs OK')"` | Depends on DPO outcome | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pip install peft` — required for LoRA DPO (DPO-04)
- [ ] Fix `dpo_data.py::save_preference_data()` to save dicts instead of tuples — required for DPO-01/DPO-03 compatibility
- [ ] Create `T5DPOConfig_lora` in `part1/config.py` — required for DPO-04
- [ ] Update `T5DPOConfig.base_checkpoint_path` to use Phase 1 best model — required for all DPO reqs

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| DPO variant comparison on dev F1 | DPO-05 | Requires running both variants and comparing W&B metrics | Compare dev Record F1 between full-FT DPO and LoRA DPO runs in W&B dashboard |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
