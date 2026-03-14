# Phase 5: Explore RL Algorithm from Minimax Model for Part 1 Fine-Tuning - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Apply GRPO/CISPO reinforcement learning to the best available T5-base fine-tuned model to explore whether execution-based RL can improve Record F1 beyond SFT/DPO. This is a report-worthy experiment with a dedicated Part 1 subsection regardless of outcome.

</domain>

<decisions>
## Implementation Decisions

### Experiment Scope & Reporting
- Report-worthy exploration: results go in the report regardless of outcome (shows initiative beyond the assignment)
- New subsection in Part 1 ("1.X RL Fine-Tuning") with its own results row in the metrics table
- Time budget: 1-2 hours of compute
- Success threshold: any F1 improvement over the best SFT/DPO baseline counts as success

### Starting Checkpoint
- Model: T5-base (220M params)
- Checkpoint: best available at runtime -- if DPO (Phase 2) improved F1, use DPO checkpoint; otherwise use best SFT checkpoint
- Training approach: LoRA (not full fine-tune)
- LoRA config: r=32, alpha=64, on q,k,v,o projections (wider adapter for more RL capacity)

### Algorithm Priority
- Three algorithms: PPO (learned value baseline), GRPO (group-relative baseline), CISPO (detached IS clipping)
- PPO first (most established), then GRPO, then CISPO — run via sequential auto-batch in a single process
- Group size: G=8 completions per query
- KL regularization: small beta=0.01-0.05 against the SFT/DPO reference model (safety net for small model + small data)
- KL divergence always monitored (even when kl_beta=0 for CISPO) — drift detection per RL stability guidelines
- Loss granularity: per-token policy ratio (true to CISPO paper formulation, requires modifying compute_restricted_log_probs to return per-token log probs)
- PPO value head: MLP on mean-pooled encoder hidden states, separate LR, trained alongside policy

### PPO-Specific Decisions
- Value head architecture: Linear(d_model, hidden_dim) -> ReLU -> Linear(hidden_dim, 1) on mean-pooled encoder output
- Value function clipping (PPO-style): clip_range=0.2
- Entropy bonus: entropy_coef=0.01 to prevent mode collapse
- Advantage type: "learned" (A = R - V(s)), with "hybrid" option available
- Separate optimizer for value head at value_lr=1e-4 (higher than policy LR)
- Value head is NOT LoRA — full parameters (small module ~400K params)

### Reward Signal
- Graded execution reward (not binary):
  - +1.0: generated SQL returns identical records to gold SQL (exact match)
  - +0.5: generated SQL returns partially overlapping records (Jaccard similarity of record sets)
  - -0.5: generated SQL executes successfully but returns wrong records (no overlap)
  - -1.0: generated SQL produces an error (syntax error, runtime error)
- No text/n-gram overlap bonus -- reward is purely execution-based
- Skip dead groups (DAPO-style): groups where all G completions get identical rewards are excluded from gradient computation

### Execution Mode
- Sequential auto-batch: all three configs run in one process with VRAM cleanup between each
- Early stopping is the binding constraint per config (no per-config time budget)
- Overall sweep budget via --max_hours CLI (not per-config max_wall_clock_hours)
- Encoder output caching: compute encoder once per query, reuse across G completions
- Thread pool for parallel SQL execution in reward computation
- Save both best and last model checkpoints
- /loop 10m /babysit-training monitoring after launch
- Full RL metrics contract logged per rl_fields.md

### Claude's Discretion
- Exact learning rate within the 1e-6 to 1e-5 range
- epsilon/epsilon_high values (start conservative per research: epsilon=0.2, epsilon_high=0.3)
- Gradient norm spike detection threshold
- Whether to use Dr. GRPO (no std normalization) vs standard GRPO advantage
- Sampling temperature and top-k for group generation
- Overall time budget across all three configs (recommend 3 hours)

</decisions>

<specifics>
## Specific Ideas

- The Minimax model (MiniMax-M1) uses CISPO -- that's the inspiration for this phase
- CISPO clips importance sampling weights (detached) rather than the PPO surrogate objective, preserving gradient flow for all tokens
- User wants to see if this novel RL approach adds value even on a small encoder-decoder model
- The experiment should be structured as: baseline (SFT/DPO) vs PPO vs GRPO vs CISPO comparison
- PPO adds a learned value head — interesting to compare learned baseline vs group-relative baseline (GRPO)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `part1/dpo_loss.py:compute_restricted_log_probs()`: sequence-level log probs via restricted_forward(). Needs minor modification to return per-token log probs (remove the `.sum()` call)
- `part1/dpo_data.py:_execute_sql()`: SQL execution helper with in-memory SQLite, timeout, error recovery
- `part1/dpo_data.py:_get_mem_conn()`: in-memory flight database connection (15MB, <1ms queries)
- `part1/dpo_data.py:_load_or_compute_gold_records()`: cached gold train records (`records/gold_train_records.pkl`)
- `part1/model.py:T5ForFlightSQL`: model wrapper with constrained decoding (`get_prefix_allowed_tokens_fn()`)
- `part1/config.py:T5DPOConfig`: DPO config pattern to follow for GRPO config
- `part1/dpo_train.py`: training loop pattern (checkpointing, early stopping, W&B logging, graceful stop)
- `src/wandb_utils.py`: W&B integration helpers (setup_run, log_epoch_metrics, etc.)

### Established Patterns
- Hierarchical dataclass configs: `T5FineTuneConfig` -> `T5DPOConfig` -> new `T5GRPOConfig`
- LoRA via peft: disable_adapter_layers() for reference logprobs (single model copy)
- bf16 AMP via `torch.amp.autocast('cuda', dtype=torch.bfloat16)`
- GPU lock serialization via `src/utils/gpu_lock.py`
- `nohup` for long-running training jobs

### Integration Points
- New files: `part1/rl_config.py`, `part1/rl_loss.py`, `part1/rl_train.py`
- Entry point pattern: `if __name__ == "__main__"` with GpuLock wrapping
- W&B project: same as existing experiments
- Output directory: `output/t5_ft_grpo_*/` or `output/t5_ft_cispo_*/`

</code_context>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 05-explore-rl-algorithm-from-minimax-model-for-part-1-fine-tuning*
*Context gathered: 2026-03-14*
