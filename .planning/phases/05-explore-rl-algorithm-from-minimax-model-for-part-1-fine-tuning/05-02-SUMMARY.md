---
phase: 05-explore-rl-algorithm-from-minimax-model-for-part-1-fine-tuning
plan: 02
subsystem: ml-training
tags: [rl, grpo, cispo, training-loop, t5, lora, group-sampling, execution-reward, part1]

# Dependency graph
requires:
  - phase: 05-explore-rl-algorithm-from-minimax-model-for-part-1-fine-tuning
    plan: 01
    provides: "T5GRPOConfig, GRPO/CISPO loss functions, per-token log prob support"
  - phase: 01-t5-base-fine-tuning
    provides: "Best T5-base checkpoint for warm-starting RL training"
provides:
  - "Complete GRPO/CISPO training pipeline (sample -> reward -> advantage -> loss -> update -> eval)"
  - "Group sampling with constrained decoding and temperature sampling (G=8 per query)"
  - "Execution-based graded reward computation via in-memory SQLite"
  - "RL training loop with W&B logging, early stopping, checkpointing, graceful stop"
  - "Gradient norm spike detection for training stability"
  - "Standalone CLI entry point with --rl_algorithm flag for GRPO/CISPO selection"
affects: [05-03-PLAN]

# Tech tracking
tech-stack:
  added: [peft]
  patterns: ["LoRA adapter toggle for reference policy (disable/enable_adapter_layers)", "on-policy group sampling with constrained decoding", "gradient norm spike detection with EMA tracking"]

key-files:
  created: [part1/rl_train.py, logs/rl-train-pipeline.md]
  modified: []

key-decisions:
  - "Log probs recomputed via compute_restricted_log_probs rather than using generate() scores to avoid precision mismatches"
  - "Dead groups have advantages zeroed out (not removed) so tensor shapes remain consistent"
  - "LoRA reference policy via disable/enable_adapter_layers toggle (single model copy, no separate reference)"
  - "Gradient norm spike detection skips optimizer step if grad_norm > factor * EMA"

patterns-established:
  - "RL training step: eval mode for sampling, train mode for updates"
  - "Group expansion via repeat_interleave(G, dim=0) for batched generation"
  - "On-policy training: shuffle and regenerate completions every epoch"

requirements-completed: [RL-04, RL-05, RL-06]

# Metrics
duration: 5min
completed: 2026-03-14
---

# Phase 5 Plan 02: RL Training Pipeline Summary

**Complete GRPO/CISPO training loop with group sampling, execution reward, gradient spike detection, and LoRA adapter toggle for reference policy**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-14T18:23:53Z
- **Completed:** 2026-03-14T18:28:53Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Built complete RL training pipeline in 811 lines implementing the full SAMPLE -> REWARD -> ADVANTAGE -> LOSS -> UPDATE -> EVAL loop
- Group sampling generates G=8 SQL completions per query using constrained decoding with temperature sampling
- Execution rewards computed via graded scheme (+1.0/+0.5/-0.5/-1.0) by running SQL against in-memory flight database
- Dead groups (all-same reward) have advantages zeroed out per DAPO convention, contributing zero gradient
- Training loop includes W&B logging, early stopping, wall clock budget, graceful stop, and gradient norm spike detection
- CLI entry point with --rl_algorithm flag switches between GRPO and CISPO configs
- GPU lock wrapping in __name__ block per project convention

## Task Commits

Each task was committed atomically:

1. **Task 1: Build group sampling and reward computation functions** - `f0d9a24` (feat)
2. **Task 2: Build the RL training loop, main entry point, and CLI** - `4fda271` (feat)

## Files Created/Modified
- `part1/rl_train.py` - Complete GRPO/CISPO training pipeline (811 lines): group sampling, reward computation, training step, training loop, main_with_config, CLI, GPU lock
- `logs/rl-train-pipeline.md` - Documentation log for the RL training pipeline

## Decisions Made
- Log probs are recomputed via compute_restricted_log_probs() rather than using .generate() scores to avoid precision mismatches (research pitfall #3)
- Dead groups have advantages zeroed out (not removed from batch) to keep tensor shapes consistent for the loss computation
- LoRA reference policy uses disable_adapter_layers()/enable_adapter_layers() toggle pattern (same as dpo_train_step_lora) rather than a separate frozen model copy
- Gradient norm EMA initialized from first observed gradient norm (not a fixed value) for better spike detection calibration

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- rl_train.py is ready for Plan 03 to run actual GRPO/CISPO training experiments
- All 7 functions verified importable: sample_group_completions, compute_old_log_probs, grpo_train_step, grpo_train, main_with_config, parse_args, main
- CLI --help prints correctly with all expected arguments
- Training can be launched with: `python3 -m part1.rl_train --rl_algorithm grpo --num_epochs 1 --batch_size 2`

## Self-Check: PASSED

All files exist and all commits verified:
- part1/rl_train.py: FOUND
- logs/rl-train-pipeline.md: FOUND
- 05-02-SUMMARY.md: FOUND
- Commit f0d9a24: FOUND
- Commit 4fda271: FOUND

---
*Phase: 05-explore-rl-algorithm-from-minimax-model-for-part-1-fine-tuning*
*Completed: 2026-03-14*
