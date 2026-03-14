# Phase 5: Explore RL Algorithm from Minimax Model for Part 1 Fine-Tuning - Research

**Researched:** 2026-03-14
**Domain:** Reinforcement learning for seq2seq NL-to-SQL (CISPO / GRPO policy optimization)
**Confidence:** MEDIUM

## Summary

The "newest MiniMax model" (MiniMax-M1, June 2025) uses an RL algorithm called **CISPO (Clipped Importance Sampling Policy Optimization)**, not GRPO. CISPO is a variant of the REINFORCE/policy gradient family that clips importance sampling weights rather than token-level updates, which preserves gradient contributions from all tokens -- especially low-frequency "reflective" tokens. It uses group-relative advantage estimation (borrowed from GRPO) but abandons the PPO trust-region constraint and KL penalty.

For this project's T5 encoder-decoder NL-to-SQL task, the most practical approach is to implement a **custom GRPO/CISPO-style trainer** built on top of the existing DPO infrastructure. The codebase already has the key building blocks: `compute_restricted_log_probs` for per-token log probabilities, `T5ForFlightSQL` with constrained decoding, and SQL execution-based evaluation. The natural reward signal is **execution accuracy** -- whether the generated SQL returns the same records as the gold SQL against the flight database. This is a well-established reward for Text-to-SQL RL (dating back to Seq2SQL, 2017).

**Primary recommendation:** Implement a minimal custom GRPO/CISPO trainer in `part1/rl_train.py` that reuses the existing model, data, constrained decoding, and SQL execution infrastructure. Use execution-based reward (binary: correct records = +1, incorrect = -1, SQL error = -1). Group size of 8-16 completions per query. No TRL dependency -- build from scratch on the existing DPO code patterns.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyTorch | 2.10.0 (installed) | Training loop, loss computation, autograd | Already in project |
| transformers | 5.3.0 (installed) | T5ForConditionalGeneration, tokenizer, `.generate()` | Already in project |
| peft | 0.18.1 (installed) | Optional LoRA for parameter-efficient RL training | Already used in DPO |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlite3 | stdlib | SQL execution for reward computation | Always -- the reward signal |
| wandb | (installed) | Experiment tracking | Always -- project convention |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom GRPO trainer | TRL GRPOTrainer | TRL is not installed; TRL has dropped encoder-decoder support in recent versions; GRPOTrainer is designed for decoder-only models and uses vLLM for generation. Custom is far more practical given existing DPO code. |
| Custom GRPO trainer | OpenRLHF, verl | Heavy dependencies, designed for multi-GPU decoder-only LLM training at scale. Massive overkill for T5-small/base. |
| CISPO | GRPO | CISPO is more novel but less tested outside MiniMax. GRPO is well-understood, has more community implementations. For this project, the differences are minor -- both use group-relative advantage. Implement GRPO first, CISPO clipping as a variant. |
| Execution reward | Graph-Reward (GMNScore) | Graph-reward avoids DB execution overhead but requires training a graph matching network. Execution reward is trivial here -- the flight DB is 15MB and already loaded in-memory for DPO data generation. |

**Installation:**
```bash
# No new packages needed -- everything is already installed
```

## Architecture Patterns

### Recommended Project Structure
```
part1/
  rl_config.py         # T5GRPOConfig dataclass (inherits T5FineTuneConfig)
  rl_loss.py           # grpo_loss(), cispo_loss(), compute_advantages()
  rl_train.py          # GRPO training loop + entry point
  dpo_data.py          # (existing) SQL execution helpers, reused for reward
  dpo_loss.py          # (existing) compute_restricted_log_probs, reused
  dpo_train.py         # (existing) DPO train, pattern reference
```

### Pattern 1: GRPO/CISPO Training Loop
**What:** Online RL training loop that samples multiple completions per query, computes execution-based rewards, normalizes advantages within each group, and applies a clipped policy gradient update.
**When to use:** After SFT/DPO fine-tuning to further improve the model using execution feedback.
**Core loop:**
```python
# Source: Synthesized from MiniMax-M1 paper + DeepSeekMath GRPO + existing DPO code patterns

def grpo_train_step(policy_model, old_log_probs, batch, optimizer,
                    rewards, advantages, epsilon=0.2, grad_clip_norm=1.0,
                    device="cuda", use_amp=True, loss_type="grpo"):
    """Single GRPO/CISPO training step.

    Args:
        policy_model: T5ForFlightSQL being trained
        old_log_probs: (B*G, T) log probs from the sampling policy (detached)
        batch: encoder inputs + decoder inputs for all G completions per query
        optimizer: optimizer for policy_model
        rewards: (B*G,) per-completion reward scores
        advantages: (B*G,) group-normalized advantages
        epsilon: clipping parameter
        loss_type: "grpo" (PPO-style clip) or "cispo" (IS-weight clip)
    """
    # Compute current policy log probs
    current_log_probs = compute_restricted_log_probs(
        policy_model, enc_ids, enc_mask, dec_input, dec_targets
    )  # (B*G,)

    # Policy ratio: pi_theta / pi_old (per-token, then sum)
    log_ratio = current_log_probs - old_log_probs  # (B*G,)
    ratio = torch.exp(log_ratio)

    if loss_type == "grpo":
        # PPO-style clipping on the surrogate objective
        clipped_ratio = torch.clamp(ratio, 1 - epsilon, 1 + epsilon)
        loss = -torch.min(ratio * advantages, clipped_ratio * advantages).mean()
    elif loss_type == "cispo":
        # CISPO: clip IS weights, multiply with advantages and log probs
        clamped_ratio = torch.clamp(ratio, max=1 + epsilon).detach()
        loss = -(clamped_ratio * advantages * current_log_probs).mean()

    optimizer.zero_grad()
    loss.backward()
    grad_norm = torch.nn.utils.clip_grad_norm_(
        policy_model.parameters(), grad_clip_norm
    ).item()
    optimizer.step()

    return {"loss": loss.item(), "grad_norm": grad_norm}
```

### Pattern 2: Group Sampling with Constrained Decoding
**What:** Generate G completions per query using temperature sampling with the restricted SQL vocabulary constraint.
**When to use:** Every GRPO training iteration to produce the group of candidates.
**Example:**
```python
# Source: Adapted from existing dpo_data.py _generate_candidates_batch

def sample_group(model, vocab, tokenizer, nl_texts, device,
                 group_size=8, temperature=1.0, top_k=50, max_new_tokens=512):
    """Sample G SQL completions per NL query using constrained decoding.

    Returns:
        completions: list of list of str (B x G SQL strings)
        log_probs: (B*G,) sequence-level log probs for each completion
    """
    schema_str = _load_schema_string(mode="tables")
    prefixed = [schema_str + t for t in nl_texts]
    encoded = tokenizer(prefixed, padding=True, truncation=True, return_tensors="pt")
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)

    # Expand for group sampling
    expanded_ids = input_ids.repeat_interleave(group_size, dim=0)
    expanded_mask = attention_mask.repeat_interleave(group_size, dim=0)

    gen_model = model.model  # inner HF model
    with torch.inference_mode():
        outputs = gen_model.generate(
            input_ids=expanded_ids,
            attention_mask=expanded_mask,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_k=top_k,
            num_return_sequences=1,
            decoder_start_token_id=32099,
            prefix_allowed_tokens_fn=vocab.get_prefix_allowed_tokens_fn(),
            output_scores=True,         # needed for log prob computation
            return_dict_in_generate=True,
        )
    # Decode and compute log probs from scores
    ...
```

### Pattern 3: Execution-Based Reward
**What:** Run generated SQL against the in-memory flight database and compare records to gold.
**When to use:** To compute the reward signal for each completion in the group.
**Example:**
```python
# Source: Adapted from existing dpo_data.py _execute_sql

def compute_execution_reward(generated_sql, gold_sql, mem_conn):
    """Compute binary execution reward.

    Returns:
        +1.0 if generated SQL returns identical records to gold SQL
        -1.0 if generated SQL returns different records or errors
    """
    gold_records = _execute_sql(gold_sql, conn=mem_conn)
    if gold_records is None:
        return 0.0  # gold SQL failed -- skip
    gen_records = _execute_sql(generated_sql, conn=mem_conn)
    if gen_records is None:
        return -1.0  # SQL error
    if gen_records == gold_records:
        return 1.0   # correct
    return -1.0       # wrong records
```

### Pattern 4: Group-Relative Advantage Normalization
**What:** Normalize rewards within each query's group to compute advantages.
**When to use:** After computing rewards for all G completions of each query.
**Example:**
```python
# Source: DeepSeekMath GRPO paper + MiniMax-M1 paper

def compute_group_advantages(rewards, group_size):
    """Normalize rewards within each group of G completions.

    Args:
        rewards: (B*G,) flat tensor of rewards
        group_size: G completions per query

    Returns:
        advantages: (B*G,) normalized advantages
    """
    B = rewards.shape[0] // group_size
    rewards_grouped = rewards.view(B, group_size)
    mean = rewards_grouped.mean(dim=1, keepdim=True)
    std = rewards_grouped.std(dim=1, keepdim=True) + 1e-8
    advantages = ((rewards_grouped - mean) / std).view(-1)
    return advantages
```

### Anti-Patterns to Avoid
- **Using TRL GRPOTrainer directly:** TRL has been moving away from encoder-decoder support. GRPOTrainer expects decoder-only models and integrates tightly with vLLM. Forcing it to work with T5 would require extensive monkey-patching.
- **Training a separate reward model:** The flight database provides a perfect deterministic reward signal. Training a neural reward model adds complexity with no benefit for this specific task.
- **Large group sizes (G > 16):** With T5-small (60M params) or T5-base (220M params), generation is fast but 4,225 training queries times G = 32 would mean 135,200 SQL executions per epoch. G = 8-16 is the sweet spot for this dataset size.
- **Removing the reference/old policy entirely:** While GRPO-Zero shows KL-free training works for large models, for a small T5 model on a small dataset, unconstrained policy updates can cause catastrophic forgetting. Keep either KL regularization or trust-region clipping.
- **Applying RL without prior SFT/DPO:** RL works best for refinement after the model already generates mostly correct SQL. Starting RL from a weak policy produces noisy gradients and slow convergence.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SQL execution for rewards | Custom DB connector | Existing `_execute_sql()` + `_get_mem_conn()` from `dpo_data.py` | Already handles in-memory SQLite, timeout, error recovery. Battle-tested on 42K+ queries. |
| Constrained SQL decoding | Custom beam search | Existing `FlightSQLVocab.get_prefix_allowed_tokens_fn()` | Already restricts output to ~600 valid SQL tokens. Works with HF `.generate()`. |
| Per-token log prob computation | Custom forward pass | Existing `compute_restricted_log_probs()` from `dpo_loss.py` | Already handles restricted vocab remapping, padding masks, sequence-level log prob sums. |
| W&B tracking | Direct wandb calls | Existing `src/wandb_utils.py` helpers | Project convention; handles sweep detection, metric namespacing, artifact upload. |
| Training loop boilerplate | From scratch | Pattern from existing `dpo_train.py` | Checkpointing, early stopping, graceful stop, wall-clock budget, GPU lock -- all reusable. |
| Gold SQL record caching | Recompute each time | Existing `_load_or_compute_gold_records()` from `dpo_data.py` | Cached to `records/gold_train_records.pkl`, loads in <1s vs 30min recompute. |

**Key insight:** The DPO codebase already contains 80% of the infrastructure needed for GRPO/CISPO. The main new code is: (1) the GRPO/CISPO loss function (~50 lines), (2) the group sampling + reward computation loop (~100 lines), and (3) config/training loop wiring (~150 lines). This is a modest extension, not a ground-up build.

## Common Pitfalls

### Pitfall 1: Reward Sparsity with Binary Execution Reward
**What goes wrong:** If most model completions are correct (reward +1) or most are wrong (reward -1), the group variance is near-zero and advantages become uninformative.
**Why it happens:** Binary reward has no gradient between "totally wrong" and "almost right." After SFT, many queries are already correct.
**How to avoid:** Use a composite reward: execution accuracy (+1/0/-1) as primary, plus a soft partial credit signal. Options: (a) Jaccard similarity of records (partial match), (b) n-gram overlap with gold SQL, (c) schema-linking accuracy. Start with binary, add partial credit only if reward sparsity is observed (check `frac_reward_zero_std` metric).
**Warning signs:** `frac_reward_zero_std` > 0.5 (majority of groups have all-same reward), zero gradient norm, no improvement in eval metrics.

### Pitfall 2: Catastrophic Forgetting Under RL
**What goes wrong:** The model's Record F1 drops below the SFT baseline after a few RL epochs.
**Why it happens:** Policy gradient updates can be aggressive, especially with small models and small datasets. The model forgets patterns it learned during SFT.
**How to avoid:** (a) Use a very low learning rate (1e-6 to 5e-6), (b) apply KL regularization with beta=0.01-0.1 against the SFT checkpoint, (c) use LoRA to constrain the update space, (d) evaluate after every epoch and early-stop aggressively (patience=3-5).
**Warning signs:** Dev Record F1 decreasing monotonically from epoch 1, train reward increasing but dev reward decreasing (overfitting to training reward).

### Pitfall 3: Log Probability Computation Mismatch
**What goes wrong:** The policy ratio `pi_new / pi_old` explodes or collapses because log probs are computed differently during sampling vs. training.
**Why it happens:** During `.generate()`, the model uses constrained decoding and potentially different precision (bf16 vs fp32). During the training forward pass, the same tokens may get slightly different log probs.
**How to avoid:** (a) Compute old_log_probs using the same `compute_restricted_log_probs()` function used in training, not from `.generate()` scores. (b) Recompute old policy log probs with the frozen old model weights AFTER generation. (c) Clamp the ratio to [0.5, 2.0] as a safety rail.
**Warning signs:** Policy ratio values > 10 or < 0.1, NaN loss, extremely high gradient norms.

### Pitfall 4: Memory Pressure from Group Sampling
**What goes wrong:** OOM during the generation phase when expanding inputs by group_size.
**Why it happens:** Generating G=16 completions for a batch of B=8 queries means 128 concurrent sequences in the decoder.
**How to avoid:** (a) Generate in mini-batches (e.g., 4 queries at a time with G=16 = 64 sequences). (b) Use `torch.inference_mode()` during generation. (c) Clear CUDA cache between generation and training. (d) With RTX 5090 (32GB), T5-base + G=16 should fit if generation batch size is kept reasonable.
**Warning signs:** CUDA OOM during `.generate()`, not during training forward pass.

### Pitfall 5: Slow SQL Execution Bottleneck
**What goes wrong:** Training is bottlenecked by SQL execution, not GPU computation.
**Why it happens:** Each training step requires executing B * G SQL queries against the database.
**How to avoid:** (a) Reuse the in-memory SQLite connection from DPO (already implemented). (b) Cache gold SQL records (already cached in `records/gold_train_records.pkl`). (c) Use sequential execution on the in-memory DB (faster than ThreadPoolExecutor for this workload). (d) With G=8 and B=8, that's 64 SQL executions per step, taking ~10-50ms total on in-memory SQLite.
**Warning signs:** GPU utilization < 30% during training, most time spent in reward computation.

### Pitfall 6: CISPO vs GRPO Confusion
**What goes wrong:** Mixing up the two algorithms' clipping mechanisms.
**Why it happens:** Both clip something, but they clip different things.
**How to avoid:** GRPO clips the surrogate objective: `min(ratio * advantage, clip(ratio) * advantage)`. CISPO clips the importance sampling weight and detaches it: `clip(ratio).detach() * advantage * log_prob`. Implement both as separate loss functions, selectable via config.
**Warning signs:** Unexpected gradient magnitudes, training instability.

## Code Examples

Verified patterns from existing codebase and algorithm papers:

### Config Dataclass (follows project convention)
```python
# Source: Project convention from part1/config.py

@dataclass
class T5GRPOConfig(T5FineTuneConfig):
    """GRPO/CISPO RL training on fine-tuned T5 for NL-to-SQL."""
    name: str = "t5_ft_grpo"
    model_checkpoint: str = "google-t5/t5-base"
    use_restricted_vocab: bool = True
    include_schema: bool = True
    schema_mode: str = "tables"

    # RL-specific
    rl_algorithm: str = "grpo"          # "grpo" or "cispo"
    group_size: int = 8                  # G: completions per query
    sampling_temperature: float = 1.0    # temperature for group sampling
    sampling_top_k: int = 50             # top-k for group sampling
    epsilon: float = 0.2                 # clipping parameter
    epsilon_high: float = 0.3            # CISPO upper clip (only for cispo)
    kl_beta: float = 0.0                # KL penalty weight (0 = no KL)
    reward_type: str = "binary"          # "binary" or "partial"

    # Training (conservative for RL)
    learning_rate: float = 5e-6
    num_epochs: int = 9999
    batch_size: int = 8                  # queries per batch (generates G*B completions)
    patience_epochs: int = 5
    eval_every_n_epochs: int = 1
    eval_subset_size: int = 0            # full dev set
    num_beams: int = 4
    grad_clip_norm: float = 1.0
    max_wall_clock_hours: Optional[float] = None

    # Base model to start RL from
    base_checkpoint_path: str = "output/t5_ft_base_sweep_1i8vr3_20260314_012024/checkpoints/model_best.pt"
```

### Advantage Computation (from DeepSeekMath + MiniMax-M1 papers)
```python
# Source: DeepSeekMath paper (2402.03300) + MiniMax-M1 paper (2506.13585)

def compute_advantages(rewards: torch.Tensor, group_size: int,
                       scale_by_std: bool = True) -> torch.Tensor:
    """Group-relative advantage normalization.

    rewards: (B*G,) flat reward tensor
    group_size: G completions per query
    Returns: (B*G,) advantages
    """
    B = rewards.shape[0] // group_size
    grouped = rewards.view(B, group_size)  # (B, G)
    mean = grouped.mean(dim=1, keepdim=True)
    if scale_by_std:
        std = grouped.std(dim=1, keepdim=True).clamp(min=1e-8)
        advantages = (grouped - mean) / std
    else:
        advantages = grouped - mean
    return advantages.view(-1)  # (B*G,)
```

### GRPO Loss Function
```python
# Source: DeepSeekMath paper + TRL GRPOTrainer formulation

def grpo_loss(current_log_probs, old_log_probs, advantages, epsilon=0.2):
    """Standard GRPO loss with PPO-style clipping.

    current_log_probs: (N,) sequence log probs under current policy
    old_log_probs: (N,) sequence log probs under old/sampling policy (detached)
    advantages: (N,) group-normalized advantages
    epsilon: clipping range
    """
    log_ratio = current_log_probs - old_log_probs
    ratio = torch.exp(log_ratio)
    clipped = torch.clamp(ratio, 1 - epsilon, 1 + epsilon)
    loss = -torch.min(ratio * advantages, clipped * advantages).mean()

    clip_frac = ((ratio < 1 - epsilon) | (ratio > 1 + epsilon)).float().mean()
    return loss, {"clip_frac": clip_frac.item(), "mean_ratio": ratio.mean().item()}
```

### CISPO Loss Function
```python
# Source: MiniMax-M1 paper (2506.13585) + swift docs

def cispo_loss(current_log_probs, old_log_probs, advantages, epsilon_high=0.3):
    """CISPO: Clipped Importance Sampling Policy Optimization.

    Clips the IS weight (detached) rather than the surrogate objective.
    """
    log_ratio = current_log_probs - old_log_probs
    ratio = torch.exp(log_ratio)
    clamped = torch.clamp(ratio, max=1 + epsilon_high).detach()
    loss = -(clamped * advantages * current_log_probs).mean()

    clip_frac = (ratio > 1 + epsilon_high).float().mean()
    return loss, {"clip_frac": clip_frac.item(), "mean_ratio": ratio.mean().item()}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PPO with critic network | GRPO (no critic) | DeepSeekMath, Feb 2024 | Eliminates value network, saves ~33% memory |
| GRPO with KL penalty | GRPO without KL (beta=0) | Open-Reasoner-Zero, Mar 2025 | KL penalty found unnecessary for many tasks |
| GRPO (clip surrogate) | CISPO (clip IS weights) | MiniMax-M1, Jun 2025 | Better gradient flow for rare tokens, 2x faster than DAPO |
| Binary execution reward | Composite reward (execution + schema + n-gram) | Reasoning-SQL, Mar 2025 | Addresses reward sparsity for Text-to-SQL |
| DPO for alignment | GRPO/CISPO for online RL | DeepSeek-R1, Jan 2025 | Online RL outperforms offline preference optimization for reasoning tasks |

**Key distinction: DPO vs GRPO/CISPO**
- DPO is offline: learns from pre-collected preference pairs (chosen vs rejected). No online generation.
- GRPO/CISPO is online: generates new completions each iteration, gets fresh reward feedback, updates policy. More compute-intensive but can explore and improve beyond the training distribution.
- For NL-to-SQL, the execution reward makes online RL particularly attractive -- the reward is deterministic, cheap to compute, and perfectly aligned with the evaluation metric.

**Deprecated/outdated:**
- PPO for LLM alignment: Still works but GRPO is simpler and equally effective for most tasks.
- RLHF with trained reward models for code/SQL: Execution-based rewards are more accurate and cheaper.

## Open Questions

1. **How much improvement can RL give over SFT/DPO for T5-small/base?**
   - What we know: Reasoning-SQL shows 6.77% improvement from GRPO on 7B Qwen model. SLM-SQL shows GRPO works on 0.5-1.5B models.
   - What's unclear: T5 is encoder-decoder (60M/220M), much smaller than models in published GRPO papers. The NL-to-SQL dataset is small (4,225 training examples). RL gains may be smaller or non-existent.
   - Recommendation: This is exploratory -- set expectations accordingly. Run for a few epochs with aggressive early stopping. If no improvement after 5-10 epochs, conclude that RL does not help for this model/data scale.

2. **Should RL start from the SFT checkpoint or the DPO checkpoint?**
   - What we know: RL works best when the base policy already generates reasonable outputs. DPO should produce a stronger starting policy than SFT alone.
   - What's unclear: DPO training hasn't completed yet (Phase 2). The starting checkpoint depends on Phase 2 results.
   - Recommendation: Default to the best available checkpoint when Phase 5 executes. If DPO improves over SFT, use the DPO model. Otherwise, use the best SFT model.

3. **Optimal group size G for T5-small/base on this dataset?**
   - What we know: Published works use G=16-64 for 7B+ models. Smaller models generate faster but may need fewer samples.
   - What's unclear: No published ablation on group size for T5-sized models.
   - Recommendation: Start with G=8, try G=16 if training is stable. Monitor `frac_reward_zero_std` -- if > 0.5, increase G to get more reward variance.

4. **Per-token vs per-sequence log probability for the policy ratio?**
   - What we know: GRPO uses per-token ratios with sequence-level advantages. The existing `compute_restricted_log_probs` returns sequence-level log probs (sum of per-token).
   - What's unclear: Whether per-sequence ratio (simpler, matches existing code) vs per-token ratio (more granular, matches GRPO paper) matters for T5.
   - Recommendation: Start with sequence-level (reuses existing infrastructure). Per-token is an optimization if needed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (if installed) / manual evaluation |
| Config file | none -- see Wave 0 |
| Quick run command | `python -c "from part1.rl_loss import grpo_loss; print('OK')"` |
| Full suite command | `python part1/rl_train.py --num_epochs 1 --batch_size 2` |

### Phase Requirements --> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RL-01 | GRPO/CISPO loss computes correctly | unit | `python -c "from part1.rl_loss import grpo_loss, cispo_loss; print('OK')"` | N/A Wave 0 |
| RL-02 | Group sampling produces G completions per query | smoke | `python -c "..."` (requires GPU) | N/A Wave 0 |
| RL-03 | Execution reward returns correct values | unit | `python -c "from part1.rl_train import compute_execution_reward; ..."` | N/A Wave 0 |
| RL-04 | Full training loop runs 1 epoch without error | integration | `python part1/rl_train.py --num_epochs 1 --batch_size 2` | N/A Wave 0 |
| RL-05 | Dev Record F1 is tracked and compared to baseline | manual | Check W&B dashboard | N/A manual-only |

### Sampling Rate
- **Per task commit:** Import test for new modules
- **Per wave merge:** 1-epoch smoke test
- **Phase gate:** Dev F1 compared to SFT/DPO baseline

### Wave 0 Gaps
- [ ] `part1/rl_config.py` -- GRPO config dataclass
- [ ] `part1/rl_loss.py` -- GRPO and CISPO loss functions
- [ ] `part1/rl_train.py` -- training loop with group sampling and execution reward

## Sources

### Primary (HIGH confidence)
- [MiniMax-M1 paper (arXiv 2506.13585)](https://arxiv.org/html/2506.13585v1) - CISPO algorithm definition, loss function, advantage estimation
- [DeepSeekMath paper (arXiv 2402.03300)](https://arxiv.org/abs/2402.03300) - Original GRPO algorithm definition
- [TRL GRPOTrainer documentation](https://huggingface.co/docs/trl/grpo_trainer) - GRPO implementation reference, confirms encoder-decoder not supported
- [Reasoning-SQL (arXiv 2503.23157)](https://arxiv.org/html/2503.23157v1) - GRPO applied to Text-to-SQL with composite rewards

### Secondary (MEDIUM confidence)
- [GRPO Illustrated Breakdown](https://epichka.com/blog/2025/grpo/) - Step-by-step GRPO formulation
- [Cameron Wolfe GRPO deep dive](https://cameronrwolfe.substack.com/p/grpo) - Comprehensive GRPO explanation with PPO comparison
- [GRPO-Zero GitHub](https://github.com/policy-gradient/GRPO-Zero) - Minimal from-scratch GRPO implementation (confirms feasibility of custom build)
- [Swift CISPO documentation](https://swift.readthedocs.io/en/latest/Instruction/GRPO/AdvancedResearch/CISPO.html) - CISPO implementation reference with epsilon_high parameter

### Tertiary (LOW confidence)
- [Graph-Reward-SQL (arXiv 2505.12380)](https://arxiv.org/html/2505.12380v1) - Alternative reward signals for SQL RL (not directly applicable)
- [SLM-SQL (arXiv 2507.22478)](https://arxiv.org/html/2507.22478v1) - GRPO on small (0.5-1.5B) models for SQL (decoder-only, not T5)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new libraries needed, all infrastructure exists in project
- Architecture: MEDIUM - Algorithm is well-documented but applying GRPO/CISPO to encoder-decoder T5 is novel territory with no published precedent for this exact combination
- Pitfalls: MEDIUM - Pitfalls are informed by published papers and general RL experience, but T5-specific failure modes are hypothesized rather than empirically verified
- Feasibility: MEDIUM - The algorithm should work in principle (GRPO is architecture-agnostic), but gains on T5-small/base with 4K training examples are uncertain

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (30 days -- algorithms are stable, ecosystem is fast-moving)
