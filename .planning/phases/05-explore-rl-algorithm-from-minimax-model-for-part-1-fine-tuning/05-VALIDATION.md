---
phase: 05
slug: explore-rl-algorithm-from-minimax-model-for-part-1-fine-tuning
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-03-14
updated: 2026-03-14
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Requirements

| ID | Requirement | Plan | Status |
|----|-------------|------|--------|
| RL-01 | T5GRPOConfig dataclass with all RL-specific fields | 01 | done |
| RL-02 | GRPO and CISPO loss functions compute correctly | 01 | done |
| RL-03 | Execution reward returns graded values (+1/+0.5/-0.5/-1) | 01 | done |
| RL-04 | Group sampling generates G completions with constrained decoding | 02 | done |
| RL-05 | Training loop with W&B logging, early stopping, graceful stop | 02 | done |
| RL-06 | rl_train.py runs as standalone entry point with GPU lock | 02 | done |
| RL-07 | All RL experiments complete with dev F1 evaluated | 04 | pending |
| RL-08 | Report contains RL Fine-Tuning subsection with results | 04 | pending |
| RL-09 | T5PPOConfig with value_coef, entropy_coef, value head fields | 03 | pending |
| RL-10 | T5ValueHead module (MLP on mean-pooled encoder states) | 03 | pending |
| RL-11 | Full RL metrics contract logged (reward/*, advantage/*, policy_entropy, kl_divergence, unique_completions, etc.) | 03 | pending |
| RL-12 | Encoder output caching (compute once, reuse across G completions) | 03 | pending |
| RL-13 | Sequential auto-batch main() runs all configs in one process with VRAM cleanup | 03 | pending |

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (if installed) / manual evaluation |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `python -c "from part1.rl_loss import grpo_loss, ppo_policy_loss; print('OK')"` |
| **Full suite command** | `python part1/rl_train.py --rl_algorithm ppo --num_epochs 1 --batch_size 2` |
| **Estimated runtime** | ~180 seconds (1-epoch smoke test with value head + group sampling) |

---

## Sampling Rate

- **After every task commit:** Run `python -c "from part1.rl_loss import grpo_loss, ppo_policy_loss; print('OK')"`
- **After every plan wave:** Run `python part1/rl_train.py --rl_algorithm ppo --num_epochs 1 --batch_size 2`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 05-01-01 | 01 | 1 | RL-01 | unit | `python -c "from part1.rl_config import T5GRPOConfig; ..."` | done |
| 05-01-02 | 01 | 1 | RL-02 | unit | `python -c "from part1.rl_loss import grpo_loss, cispo_loss; ..."` | done |
| 05-01-03 | 01 | 1 | RL-03 | unit | `python -c "from part1.rl_loss import compute_execution_reward; ..."` | done |
| 05-02-01 | 02 | 2 | RL-04 | smoke | `python -c "from part1.rl_train import sample_group_completions; ..."` | done |
| 05-02-02 | 02 | 2 | RL-05,RL-06 | integration | `python part1/rl_train.py --rl_algorithm grpo --num_epochs 1 --batch_size 2` | done |
| 05-03-01 | 03 | 3 | RL-09,RL-10 | unit | `python -c "from part1.rl_value_head import T5ValueHead; from part1.rl_config import T5PPOConfig; ..."` | pending |
| 05-03-02 | 03 | 3 | RL-02 (ext) | unit | `python -c "from part1.rl_loss import ppo_policy_loss, ppo_value_loss, compute_entropy; ..."` | pending |
| 05-03-03 | 03 | 3 | RL-12 | smoke | verify encoder caching in sample_group_completions signature | pending |
| 05-03-04 | 03 | 3 | RL-11 | smoke | verify grpo_train_step returns full metrics contract keys | pending |
| 05-03-05 | 03 | 3 | RL-13 | integration | `python part1/rl_train.py --rl_algorithm ppo --num_epochs 1 --batch_size 2` | pending |
| 05-04-01 | 04 | 4 | RL-07 | manual | sequential auto-batch completes all three configs | pending |
| 05-04-02 | 04 | 4 | RL-08 | manual | report compiles with RL subsection | pending |

---

## Wave 0 Requirements

- [x] `part1/rl_config.py` — GRPO/CISPO config dataclass
- [x] `part1/rl_loss.py` — GRPO and CISPO loss functions
- [x] `part1/rl_train.py` — training loop with group sampling and execution reward
- [ ] `part1/rl_value_head.py` — PPO value head module (Plan 03)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dev Record F1 comparison across PPO/GRPO/CISPO and baseline | RL-07 | Requires full training run + W&B comparison | Run full training, check W&B dashboard |
| Report RL subsection quality | RL-08 | Requires human judgment on writing quality | Review report/report.pdf RL subsection |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
