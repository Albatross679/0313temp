---
phase: 05-explore-rl-algorithm-from-minimax-model-for-part-1-fine-tuning
plan: 01
subsystem: ml-training
tags: [rl, grpo, cispo, loss-functions, config, t5, lora, part1]

# Dependency graph
requires:
  - phase: 01-t5-base-fine-tuning
    provides: "Best T5-base checkpoint for warm-starting RL training"
provides:
  - "T5GRPOConfig dataclass with all RL-specific fields"
  - "GRPO loss function (sequence-level PPO-style clipped surrogate)"
  - "CISPO loss function (detached clamped IS weights)"
  - "Per-token CISPO loss (MiniMax-M1 Equation 4)"
  - "Group-relative advantage computation with dead group detection"
  - "Graded execution reward (+1/+0.5/-0.5/-1)"
  - "Per-token log prob support in compute_restricted_log_probs"
affects: [05-02-PLAN, 05-03-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: ["detached IS weight clipping (CISPO)", "group-relative advantage normalization"]

key-files:
  created: [part1/rl_config.py, part1/rl_loss.py]
  modified: [part1/dpo_loss.py]

key-decisions:
  - "CISPO uses .detach() on clamped ratio so gradient always flows through log_pi"
  - "Graded reward scheme (+1/+0.5/-0.5/-1) instead of binary for better gradient signal"
  - "LoRA r=32 alpha=64 on q,k,v,o attention projections for RL training"
  - "Dr.GRPO variant supported via use_std_normalization=False flag"

patterns-established:
  - "CISPO detached weight pattern: clamp(ratio, max=1+eps).detach() * A * log_pi"
  - "Group-relative advantages: reshape (B*G,) -> (B, G), normalize per group, flatten back"

requirements-completed: [RL-01, RL-02, RL-03]

# Metrics
duration: 4min
completed: 2026-03-14
---

# Phase 5 Plan 01: RL Config and Loss Functions Summary

**T5GRPOConfig dataclass with GRPO/CISPO loss functions, per-token IS clipping, and graded execution reward**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-14T18:11:07Z
- **Completed:** 2026-03-14T18:15:24Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created T5GRPOConfig inheriting T5FineTuneConfig with all RL-specific fields and two variant configs (GRPO with KL, CISPO without KL)
- Implemented both GRPO and CISPO loss functions that are differentiable and produce correct gradients
- Added per-token CISPO loss matching MiniMax-M1 Equation 4 with proper masking for variable-length sequences
- Extended compute_restricted_log_probs with backward-compatible per_token parameter for token-level log probs

## Task Commits

Each task was committed atomically:

1. **Task 1: Create T5GRPOConfig dataclass and GRPO/CISPO variant configs** - `f1ce708` (feat)
2. **Task 2: Modify compute_restricted_log_probs for per-token return and create RL loss functions** - `bf7bb3d` (feat)

## Files Created/Modified
- `part1/rl_config.py` - T5GRPOConfig dataclass with RL algorithm selection, loss hyperparameters, reward config, stability params; GRPO and CISPO variant configs
- `part1/rl_loss.py` - GRPO loss, CISPO loss (sequence and per-token), group advantages, execution reward, KL penalty
- `part1/dpo_loss.py` - Added per_token parameter to compute_restricted_log_probs (backward compatible)

## Decisions Made
- Used .detach() on clamped IS ratio in CISPO to preserve gradient flow through log_pi (core CISPO innovation from MiniMax-M1)
- Graded reward (+1/+0.5/-0.5/-1) instead of binary per user decision for richer gradient signal
- LoRA r=32 alpha=64 on all attention projections (q,k,v,o) for wider adapter capacity during RL
- Renamed internal variable from `per_token` to `token_log_probs` in dpo_loss.py to avoid shadowing the new parameter name

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- rl_config.py and rl_loss.py are ready for Plan 02 to build the training loop against
- compute_restricted_log_probs with per_token=True is ready for token-level CISPO in the training loop
- All loss functions verified differentiable via backward() tests

## Self-Check: PASSED

All files exist and all commits verified:
- part1/rl_config.py: FOUND
- part1/rl_loss.py: FOUND
- part1/dpo_loss.py: FOUND
- 05-01-SUMMARY.md: FOUND
- Commit f1ce708: FOUND
- Commit bf7bb3d: FOUND

---
*Phase: 05-explore-rl-algorithm-from-minimax-model-for-part-1-fine-tuning*
*Completed: 2026-03-14*
