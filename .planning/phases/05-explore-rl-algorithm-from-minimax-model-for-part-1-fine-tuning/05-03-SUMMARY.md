---
phase: 05-explore-rl-algorithm-from-minimax-model-for-part-1-fine-tuning
plan: 03
subsystem: ml-training
tags: [ppo, grpo, cispo, rl, value-head, encoder-caching, thread-pool, metrics-contract]

# Dependency graph
requires:
  - phase: 05-01
    provides: "RL config and loss functions (GRPO/CISPO)"
  - phase: 05-02
    provides: "RL training pipeline with group sampling and execution reward"
provides:
  - "PPO variant with learned value head (T5ValueHead)"
  - "Full RL metrics contract matching rl_fields.md"
  - "Encoder output caching for ~7x compute savings on encoder passes"
  - "Thread-pooled reward computation"
  - "Sequential auto-batch main() for PPO/GRPO/CISPO"
  - "Save-last model checkpoint alongside best"
affects: [05-04, phase-05-training-runs]

# Tech tracking
tech-stack:
  added: [transformers.modeling_outputs.BaseModelOutput, concurrent.futures.ThreadPoolExecutor]
  patterns: [encoder-output-caching, thread-local-sqlite, sequential-auto-batch, always-on-kl]

key-files:
  created:
    - part1/rl_value_head.py
  modified:
    - part1/rl_config.py
    - part1/rl_loss.py
    - part1/rl_train.py

key-decisions:
  - "PPO value head uses mean-pooled encoder hidden states (not decoder) since state=NL query"
  - "Thread-local SQLite connections for safe parallel reward computation"
  - "KL divergence always computed and logged even when kl_beta=0 (monitoring only)"
  - "Tasks 3-5 committed together in rl_train.py since changes are deeply interleaved"
  - "max_wall_clock_hours=None per config; --max_hours at sweep level for total budget"

patterns-established:
  - "Encoder caching pattern: run encoder once, expand via repeat_interleave, pass via BaseModelOutput"
  - "Full RL metrics contract: 16 metric keys from rl_fields.md logged every step"
  - "Sequential auto-batch: main() iterates config list with cleanup_vram() between each"

requirements-completed: [RL-09, RL-10, RL-11, RL-12, RL-13]

# Metrics
duration: 8min
completed: 2026-03-14
---

# Phase 05 Plan 03: ML Workflow Audit Fixes and PPO Algorithm Summary

**PPO with learned value head baseline, full rl_fields.md metrics contract, encoder output caching, thread-pool rewards, and sequential auto-batch across PPO/GRPO/CISPO**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-14T21:12:31Z
- **Completed:** 2026-03-14T21:20:52Z
- **Tasks:** 5
- **Files modified:** 4

## Accomplishments
- Created T5ValueHead module: MLP on mean-pooled encoder hidden states for PPO learned baseline
- Added ppo_policy_loss, ppo_value_loss, compute_entropy, plus ratio_max to all loss diagnostics
- Implemented encoder output caching: ~7x reduction in encoder compute per epoch (G=8)
- Full RL metrics contract: all 16 metric keys from rl_fields.md logged with correct names
- Sequential auto-batch main() runs PPO, GRPO, CISPO in one process with VRAM cleanup
- Thread-pooled reward computation with thread-local SQLite connections
- Save both best and last model checkpoints
- KL divergence always computed (even when kl_beta=0) for drift monitoring

## Task Commits

Each task was committed atomically:

1. **Task 1: Add PPO value head module and update configs** - `b28db41` (feat)
2. **Task 2: Add PPO loss functions and entropy computation** - `00ec4f5` (feat)
3. **Task 3: Encoder caching, thread-pool rewards, full rl_train.py rewrite** - `7e52144` (feat)
4. **Task 4: Full RL metrics contract** - included in `7e52144` (same file rewrite)
5. **Task 5: PPO training step, save-last, sequential auto-batch** - included in `7e52144` (same file rewrite)

## Files Created/Modified
- `part1/rl_value_head.py` - T5ValueHead: MLP on mean-pooled encoder states for PPO baseline
- `part1/rl_config.py` - Added T5PPOConfig, T5PPOConfig_v1, missing GRPO fields (reward_scale, reward_clip, reference_model_update, etc.)
- `part1/rl_loss.py` - Added ppo_policy_loss, ppo_value_loss, compute_entropy; ratio_max to all diagnostics
- `part1/rl_train.py` - Comprehensive rewrite: encoder caching, full metrics contract, PPO support, thread-pool rewards, save-last, sequential auto-batch

## Decisions Made
- PPO value head operates on encoder hidden states (not decoder) since "state" is the NL query
- Thread-local SQLite connections for reward computation (each thread gets its own connection via threading.local)
- Tasks 3-5 implemented in a single rl_train.py rewrite since changes are deeply interleaved (same functions modified)
- max_wall_clock_hours set to None per config; overall time budget via --max_hours CLI arg
- Kept grpo_train_step as single function handling all three algorithms via branches (minimal code duplication)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] max_new_tokens field name alignment**
- **Found during:** Task 1 (config update)
- **Issue:** T5FineTuneConfig uses `max_new_tokens` but rl_fields.md uses `max_completion_length`
- **Fix:** Added `max_completion_length` to T5GRPOConfig (new canonical name), updated sample_group_completions to fall back to `max_new_tokens` if `max_completion_length` not set
- **Files modified:** part1/rl_config.py, part1/rl_train.py
- **Committed in:** b28db41, 7e52144

**2. [Rule 1 - Bug] Tasks 3-5 merged into single commit**
- **Found during:** Task 3 implementation
- **Issue:** Tasks 3, 4, and 5 all modify rl_train.py's core functions (grpo_train_step, grpo_train, main). Partial commits would leave the file in broken intermediate states.
- **Fix:** Implemented all three tasks in a single comprehensive rewrite of rl_train.py, committed as Task 3.
- **Files modified:** part1/rl_train.py
- **Committed in:** 7e52144

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both necessary for correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three RL algorithms (PPO, GRPO, CISPO) are fully implemented and ready for training runs
- Sequential auto-batch enables running all three with `python3 -m part1.rl_train` (no args)
- Next step: Plan 04 (training runs and evaluation)
- Base checkpoint required: `output/t5_ft_base_sweep_1i8vr3_20260314_012024/checkpoints/model_best.pt`

## Self-Check: PASSED

All 4 files verified present. All 3 commits verified in git log.

---
*Phase: 05-explore-rl-algorithm-from-minimax-model-for-part-1-fine-tuning*
*Completed: 2026-03-14*
