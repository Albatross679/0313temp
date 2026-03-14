---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 05-03-PLAN.md
last_updated: "2026-03-14T21:21:00.000Z"
last_activity: "2026-03-14 - Completed 05-03: ML workflow audit fixes and PPO algorithm"
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 9
  completed_plans: 4
  percent: 44
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-13)

**Core value:** Get the assignment fully submission-ready -- complete report with real metrics, DPO-improved Part 1 model, and all required output files.
**Current focus:** Phase 5: RL Fine-Tuning (GRPO/CISPO)

## Current Position

Phase: 5 of 5 (RL Fine-Tuning)
Plan: 4 of 4 in current phase (Plans 01-03 complete)
Status: Executing Phase 5
Last activity: 2026-03-14 - Completed 05-03: ML workflow audit fixes and PPO algorithm

Progress: [████░░░░░░] 44%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 04 P01 | 3min | 2 tasks | 2 files |
| Phase 05 P01 | 4min | 2 tasks | 3 files |
| Phase 05 P02 | 5min | 2 tasks | 1 files |
| Phase 05 P03 | 8min | 5 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Fine-tune T5-base instead of just T5-small for Part 1 (potentially stronger baseline)
- DPO on best fine-tuned model (base or small) to further improve Record F1
- Preference data strategy: sample multiple SQL outputs, rank by execution correctness
- Compare DPO with and without LoRA
- [Phase quick-1]: SQL EM artifact is in SentencePiece decode, not model -- regex post-processing recommended
- [Phase 04]: Used 7 mutually exclusive error categories with priority-based classification to prevent double-counting
- [Phase 04]: Classified LLM truncation separately from wrong-reference since 82% of LLM errors are truncation-caused
- [Phase 05]: CISPO uses .detach() on clamped IS ratio so gradient always flows through log_pi
- [Phase 05]: Graded reward (+1/+0.5/-0.5/-1) instead of binary for better gradient signal
- [Phase 05]: LoRA r=32 alpha=64 on q,k,v,o attention projections for RL training
- [Phase 05-02]: Log probs recomputed via compute_restricted_log_probs, not generate() scores
- [Phase 05-02]: Dead groups advantages zeroed out (not removed) for consistent tensor shapes
- [Phase 05-02]: LoRA reference policy via disable/enable_adapter_layers toggle (single model copy)
- [Phase 05-03]: PPO value head uses mean-pooled encoder hidden states (state=NL query)
- [Phase 05-03]: Thread-local SQLite connections for safe parallel reward computation
- [Phase 05-03]: KL always computed even when kl_beta=0 for drift monitoring
- [Phase 05-03]: max_wall_clock_hours=None per config; --max_hours at sweep level

### Roadmap Evolution

- 2026-03-13: Roadmap restructured — new Phase 1 (T5-Base Fine-Tuning) added, existing phases renumbered 2/3/4
- Phase 5 added: Explore RL algorithm from Minimax model for Part 1 fine-tuning

### Pending Todos

None yet.

### Blockers/Concerns

- T5-base is ~220M params vs T5-small ~60M — may need adjusted batch size for GPU VRAM
- DPO preference data generation strategy needs implementation details (sampling temperature, number of samples per query)
- Timeline is tight (due ~2026-03-14/15)

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | Investigate why SQL exact match rate is so low via W&B logs and online research | 2026-03-14 | c0d590c | [1-investigate-why-sql-exact-match-rate-is-](./quick/1-investigate-why-sql-exact-match-rate-is-/) |
| 2 | Split T5 results table into T5-small and T5-base tables with Params (M) column | 2026-03-14 | fd4c0b7 | [2-look-into-part-1-fine-tune-t5-base-model](./quick/2-look-into-part-1-fine-tune-t5-base-model/) |

## Session Continuity

Last session: 2026-03-14T21:21:00.000Z
Stopped at: Completed 05-03-PLAN.md
Resume file: None
