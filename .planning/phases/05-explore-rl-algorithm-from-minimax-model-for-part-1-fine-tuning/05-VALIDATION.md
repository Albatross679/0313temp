---
phase: 05
slug: explore-rl-algorithm-from-minimax-model-for-part-1-fine-tuning
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (if installed) / manual evaluation |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `python -c "from part1.rl_loss import grpo_loss; print('OK')"` |
| **Full suite command** | `python part1/rl_train.py --num_epochs 1 --batch_size 2` |
| **Estimated runtime** | ~120 seconds (1-epoch smoke test with group sampling) |

---

## Sampling Rate

- **After every task commit:** Run `python -c "from part1.rl_loss import grpo_loss; print('OK')"`
- **After every plan wave:** Run `python part1/rl_train.py --num_epochs 1 --batch_size 2`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | RL-01 | unit | `python -c "from part1.rl_loss import grpo_loss, cispo_loss; print('OK')"` | N/A Wave 0 | pending |
| 05-01-02 | 01 | 1 | RL-02 | smoke | `python -c "..."` (requires GPU) | N/A Wave 0 | pending |
| 05-01-03 | 01 | 1 | RL-03 | unit | `python -c "from part1.rl_train import compute_execution_reward; ..."` | N/A Wave 0 | pending |
| 05-01-04 | 01 | 1 | RL-04 | integration | `python part1/rl_train.py --num_epochs 1 --batch_size 2` | N/A Wave 0 | pending |
| 05-01-05 | 01 | 1 | RL-05 | manual | Check W&B dashboard | N/A manual-only | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `part1/rl_config.py` — GRPO/CISPO config dataclass
- [ ] `part1/rl_loss.py` — GRPO and CISPO loss functions
- [ ] `part1/rl_train.py` — training loop with group sampling and execution reward

*These files must exist before any automated validation can run.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dev Record F1 improvement over baseline | RL-05 | Requires full training run + W&B comparison | Run full training, check W&B dashboard for F1 vs SFT/DPO baseline |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
