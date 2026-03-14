# Phase 5: Explore RL Algorithm from Minimax Model for Part 1 Fine-Tuning - Research

**Researched:** 2026-03-14 (updated with CISPO deep dive)
**Domain:** Reinforcement learning for seq2seq NL-to-SQL (CISPO / GRPO policy optimization)
**Confidence:** MEDIUM

## Summary

The "newest MiniMax model" (MiniMax-M1, June 2025) uses an RL algorithm called **CISPO (Clipped Importance Sampling Policy Optimization)**, not GRPO. CISPO is a variant of the REINFORCE/policy gradient family that clips importance sampling weights rather than token-level updates, which preserves gradient contributions from all tokens -- especially low-frequency "reflective" tokens. It uses group-relative advantage estimation (borrowed from GRPO) but abandons the PPO trust-region constraint and KL penalty.

For this project's T5 encoder-decoder NL-to-SQL task, the most practical approach is to implement a **custom GRPO/CISPO-style trainer** built on top of the existing DPO infrastructure. The codebase already has the key building blocks: `compute_restricted_log_probs` for per-token log probabilities, `T5ForFlightSQL` with constrained decoding, and SQL execution-based evaluation. The natural reward signal is **execution accuracy** -- whether the generated SQL returns the same records as the gold SQL against the flight database. This is a well-established reward for Text-to-SQL RL (dating back to Seq2SQL, 2017).

**Primary recommendation:** Implement a minimal custom GRPO/CISPO trainer in `part1/rl_train.py` that reuses the existing model, data, constrained decoding, and SQL execution infrastructure. Use execution-based reward (binary: correct records = +1, incorrect = -1, SQL error = -1). Group size of 8-16 completions per query. No TRL dependency -- build from scratch on the existing DPO code patterns. Implement both GRPO and CISPO losses as selectable variants. **For T5 on this task, start with GRPO (better understood) and try CISPO as a variant.**

## Deep Dive: CISPO

### Algorithm Origin and Motivation

CISPO was introduced in the MiniMax-M1 technical report (arXiv 2506.13585, June 2025). MiniMax observed that existing policy gradient methods (PPO, GRPO, DAPO) share a fundamental problem when training long chain-of-thought reasoning: **they clip token-level updates via the PPO surrogate objective, which can zero out gradients for rare but critical tokens.**

The specific failure mode: tokens that trigger reflective behaviors ("Wait", "However", "Recheck") are rare under the base policy (low probability). When the new policy increases their probability, the per-token importance ratio r_{i,t} becomes large. PPO/GRPO's `min(r * A, clip(r) * A)` operation then zeros the gradient for these tokens. After even the first on-policy update, these "fork tokens" that scaffold reasoning are clipped out, preventing the emergence of deep chain-of-thought behavior.

CISPO addresses this by **clipping the importance sampling weight itself (as a detached coefficient) rather than clipping the surrogate objective**. The gradient always flows through `log pi_theta`, so every token contributes to the policy update regardless of how large its importance ratio becomes.

### Mathematical Formulation

**CISPO Objective (per the MiniMax-M1 paper, Equation 4):**

```
J_CISPO(theta) = E[ (1 / sum_i |o_i|) * sum_i sum_t  sg(r_hat_{i,t}(theta)) * A_hat_{i,t} * log pi_theta(o_{i,t} | q, o_{i,<t}) ]
```

Where:
- `r_{i,t}(theta) = pi_theta(o_{i,t} | q, o_{i,<t}) / pi_theta_old(o_{i,t} | q, o_{i,<t})` is the per-token importance sampling ratio
- `r_hat_{i,t}(theta) = clip(r_{i,t}(theta), 1 - epsilon_low^IS, 1 + epsilon_high^IS)` is the clipped IS weight
- `sg()` (stop-gradient / detach) prevents backpropagation through the clipped weight
- `A_hat_{i,t}` is the group-relative advantage (same for all tokens in response i)
- The denominator `sum_i |o_i|` normalizes by total completion tokens (token-level normalization)

**The critical loss to implement (negated for minimization):**

```
L_CISPO = -( 1/N_total_tokens ) * sum_i sum_t  detach(clamp(r_{i,t}, max=1+epsilon_high)) * A_i * log_pi_theta(o_{i,t})
```

**Note on epsilon_low:** The MiniMax-M1 paper defines `epsilon_low^IS` but in practice it is set very large (effectively disabling the lower clip). The ms-swift implementation only applies `max` clamping. For our implementation, only `epsilon_high` matters.

### How CISPO Differs from GRPO, DAPO, and PPO

**The fundamental difference is WHERE clipping happens and HOW it affects gradients:**

**PPO / GRPO -- Clip the surrogate objective:**
```
L_PPO = -min(r_{i,t} * A_i, clip(r_{i,t}, 1-eps, 1+eps) * A_i)
```
The `min()` selects the more pessimistic estimate. When `r > 1+eps` and `A > 0`, the min picks the clipped branch: gradient w.r.t. theta is `A * d/d_theta [clip(r)]`. Since `clip(r) = 1+eps` (constant), **the gradient is ZERO for that token**. The token is effectively dropped from the update.

**Unified mask view:** PPO/GRPO applies a binary mask:
```
M_{i,t} = 0  if (A > 0 and r > 1+eps) or (A < 0 and r < 1-eps)
M_{i,t} = 1  otherwise
```
Masked-out tokens contribute nothing to the gradient.

**CISPO -- Clip the IS weight, preserve gradient flow:**
```
L_CISPO = -detach(clamp(r_{i,t}, max=1+eps_high)) * A_i * log_pi_theta(o_{i,t})
```
The clipped weight is **detached** (stop-gradient). It serves as a constant scaling coefficient. The gradient always flows through `log pi_theta(o_{i,t})`, which is the standard REINFORCE gradient. No token is ever masked out. The clipping only bounds the **magnitude** of the weight, preventing outlier gradient variance, but never zeros it.

**DAPO -- Asymmetric clipping + dynamic sampling:**
```
L_DAPO = -min(r_{i,t} * A_i, clip(r_{i,t}, 1-eps_low, 1+eps_high) * A_i)
```
DAPO uses asymmetric clipping bounds (eps_high > eps_low) to allow more exploration. It also filters out "dead" groups where all completions have identical rewards (dynamic sampling). But DAPO still uses the PPO-style `min()` operation, so it can still zero out token gradients.

### Detailed Algorithm Comparison

| Property | PPO | GRPO | DAPO | CISPO |
|----------|-----|------|------|-------|
| **Clipping target** | Surrogate objective (min) | Surrogate objective (min) | Surrogate objective (min, asymmetric) | IS weight (detach) |
| **Gradient for out-of-range tokens** | Zero (dropped) | Zero (dropped) | Zero (dropped, but higher ceiling) | Nonzero (scaled by capped weight) |
| **Advantage estimation** | Learned value function (critic) | Group-relative normalization | Group-relative normalization | Group-relative normalization |
| **Value/critic network** | Required | Not required | Not required | Not required |
| **KL penalty** | Optional | Optional (beta term) | None | None |
| **Clipping bounds** | Symmetric [1-eps, 1+eps] | Symmetric [1-eps, 1+eps] | Asymmetric [1-eps_low, 1+eps_high] | Upper-only (max=1+eps_high) |
| **Normalization** | Per-sample | Per-sample (1/|o_i|) | Per-token global (1/sum|o_i|) | Per-token global (1/sum|o_i|) |
| **Dynamic sampling** | No | No | Yes (filters all-same-reward groups) | No (not in original paper) |
| **Entropy preservation** | Entropy bonus term | Implicit (symmetric clip) | Clip-higher + dynamic sampling | Implicit (no token dropout) |
| **Typical eps values** | eps=0.2 | eps=0.2 | eps_low=0.2, eps_high=0.28 | eps_high=0.3 (small-scale); 5.0 (large-scale per ms-swift) |
| **Memory overhead** | High (critic model) | Low (no critic) | Low (no critic) | Low (no critic) |
| **Training speed vs DAPO** | Slower | Similar | Baseline | ~2x faster (empirical) |

### Why CISPO Achieves 2x Speedup Over DAPO

The MiniMax-M1 paper (Figure 2) shows CISPO matching DAPO's asymptotic performance on AIME 2024 (Qwen2.5-32B-base) in approximately 50% of the training steps. The speedup comes from two mechanisms:

1. **No token dropout:** Every token contributes to every gradient update. DAPO's min() operation drops high-ratio tokens from the gradient, effectively wasting those samples. CISPO uses all of them, just with bounded weight. This means more useful gradient signal per batch.

2. **Faster emergence of reasoning patterns:** Because rare "fork" tokens (that trigger reflective reasoning) are never dropped, the model learns these patterns earlier. DAPO requires more steps because it must rediscover these token patterns after they are clipped out in early updates.

**Caveat for this project (MEDIUM confidence):** The 2x speedup was demonstrated on large models (32B) with long reasoning traces. For T5-small/base on short SQL sequences (typically 20-50 tokens), the token dropout issue is less severe. The speedup advantage of CISPO may be smaller or negligible for our use case. The SQL vocabulary is constrained (~600 tokens), and there are no "reflective" reasoning tokens. The main advantage of CISPO for us is implementation simplicity -- the loss function is simpler than PPO/GRPO's min() operation.

### CISPO on Encoder-Decoder Models (T5 Feasibility)

**Confidence: MEDIUM** -- No published work applies CISPO (or GRPO) to encoder-decoder T5. All published GRPO/CISPO work uses decoder-only models. However:

**Why it should work in principle:**
1. CISPO/GRPO are architecture-agnostic policy gradient methods. They operate on per-token log probabilities, which encoder-decoder models produce just as decoder-only models do.
2. The T5 decoder generates tokens autoregressively, exactly like a decoder-only model. The encoder provides context (like a prompt), and the decoder generates the response (the SQL).
3. `compute_restricted_log_probs()` in `dpo_loss.py` already computes per-token log probs for T5 with restricted vocabulary -- this is the same quantity CISPO needs.
4. The existing DPO implementation already applies per-token log prob computation to T5, confirming the feasibility of the underlying operation.

**Key adaptation for encoder-decoder:**
- The importance ratio `r_{i,t} = pi_theta(o_{i,t} | q, o_{i,<t}) / pi_old(o_{i,t} | q, o_{i,<t})` is computed identically -- both the encoder output (from `q`) and the decoder autoregressive context (from `o_{i,<t}`) are handled by the standard T5 forward pass.
- Group sampling uses `model.generate()` with `do_sample=True`, which works the same way for T5 as for decoder-only models.
- The only difference is that T5 has a separate encoder pass. For efficiency, compute the encoder output once per query and reuse it across all G completions (via `repeat_interleave` on the encoder hidden states or by using `encoder_outputs` argument).

**Practical concern:** The existing `compute_restricted_log_probs()` returns sequence-level log probs (sum of per-token). For true CISPO (which clips per-token), we need to modify this function to return per-token log probs. This is a minor change -- remove the `.sum()` call and return the tensor before summation.

### Open-Source Implementations

**Confidence: HIGH** -- Multiple verified implementations exist:

| Implementation | Location | Status | Notes |
|----------------|----------|--------|-------|
| **ms-swift (ModelScope)** | [github.com/modelscope/ms-swift](https://github.com/modelscope/ms-swift) | Production | `--loss_type cispo --epsilon_high 5.0`. Full GRPO framework with CISPO as loss variant. Decoder-only models only. |
| **TorchRL** | [docs.pytorch.org/rl/main/_modules/torchrl/objectives/llm/grpo.html](https://docs.pytorch.org/rl/main/_modules/torchrl/objectives/llm/grpo.html) | Production | `CISPOLoss` class inheriting from `GRPOLoss`. Clean PyTorch implementation with asymmetric clipping support. |
| **RLHF Book (Nathan Lambert)** | [github.com/natolambert/rlhf-book/tree/main/code](https://github.com/natolambert/rlhf-book/tree/main/code) | Educational | `policy_gradients/` directory with CISPO config and implementation. Good reference for understanding. |
| **MiniMax-M1 repo** | [github.com/MiniMax-AI/MiniMax-M1](https://github.com/MiniMax-AI/MiniMax-M1) | Reference only | Paper repo with model weights. No standalone CISPO trainer code. Has open issues about gradient norm explosion (#31). |

**None of these implementations support encoder-decoder models.** All assume decoder-only architecture. Our custom implementation is required.

### Reference Implementation (from ms-swift, adapted for clarity)

The ms-swift implementation is the most production-tested. The core loss computation:

```python
# Source: ms-swift CISPO loss (adapted from swift/plugin/loss_scale/loss_scale.py)
# Original operates on decoder-only; adapted below for encoder-decoder

def cispo_loss_per_token(
    per_token_logps: torch.Tensor,      # (B*G, T) current policy per-token log probs
    old_per_token_logps: torch.Tensor,  # (B*G, T) old policy per-token log probs (detached)
    advantages: torch.Tensor,            # (B*G,) group-normalized advantages
    completion_mask: torch.Tensor,       # (B*G, T) mask for valid completion tokens
    epsilon_high: float = 0.3,
) -> tuple[torch.Tensor, dict]:
    """Per-token CISPO loss, matching the MiniMax-M1 formulation.

    Key difference from GRPO: clamp(ratio).detach() * advantage * log_prob
    instead of min(ratio * advantage, clip(ratio) * advantage).
    """
    # Per-token importance ratio
    log_ratio = per_token_logps - old_per_token_logps  # (B*G, T)
    importance_weights = torch.exp(log_ratio)            # (B*G, T)

    # Clip IS weights and detach -- gradients only flow through per_token_logps
    clamped_ratios = torch.clamp(importance_weights, max=1 + epsilon_high).detach()

    # Per-token loss: weight * advantage * log_prob
    # advantages are sequence-level, broadcast to token dim
    per_token_loss = -clamped_ratios * advantages.unsqueeze(1) * per_token_logps  # (B*G, T)

    # Mask and normalize by total valid tokens
    masked_loss = (per_token_loss * completion_mask).sum()
    total_tokens = completion_mask.sum().clamp(min=1)
    loss = masked_loss / total_tokens

    # Diagnostics
    clip_frac = ((importance_weights > 1 + epsilon_high) * completion_mask).sum() / total_tokens
    mean_ratio = (importance_weights * completion_mask).sum() / total_tokens

    return loss, {
        "clip_frac": clip_frac.item(),
        "mean_ratio": mean_ratio.item(),
    }
```

### Sequence-Level CISPO (Simplified for Our Use Case)

For T5 on short SQL sequences, the per-token vs sequence-level distinction matters less than for long reasoning traces. The sequence-level variant is simpler and reuses existing `compute_restricted_log_probs()` directly:

```python
# Source: Adapted from MiniMax-M1 paper for sequence-level application

def cispo_loss_sequence(
    current_log_probs: torch.Tensor,  # (N,) sequence-level log probs under current policy
    old_log_probs: torch.Tensor,      # (N,) sequence-level log probs under old policy (detached)
    advantages: torch.Tensor,          # (N,) group-normalized advantages
    epsilon_high: float = 0.3,
) -> tuple[torch.Tensor, dict]:
    """Sequence-level CISPO loss. Simpler, reuses existing log prob infrastructure.

    This is a pragmatic approximation: the IS ratio is computed at sequence level
    rather than per-token. For short SQL sequences (20-50 tokens), the difference
    from per-token CISPO is minor.
    """
    log_ratio = current_log_probs - old_log_probs
    ratio = torch.exp(log_ratio)

    # Clip IS weight and detach
    clamped = torch.clamp(ratio, max=1 + epsilon_high).detach()

    # CISPO loss: weight * advantage * log_prob
    loss = -(clamped * advantages * current_log_probs).mean()

    clip_frac = (ratio > 1 + epsilon_high).float().mean()
    return loss, {"clip_frac": clip_frac.item(), "mean_ratio": ratio.mean().item()}
```

### CISPO Step-by-Step Training Loop

```
CISPO Training Loop (per epoch):
=================================

1. SAMPLE PHASE (torch.inference_mode):
   For each mini-batch of B queries from training data:
     a. Encode queries through T5 encoder (once per query)
     b. Generate G completions per query using model.generate(do_sample=True)
        with constrained decoding (FlightSQLVocab prefix_allowed_tokens_fn)
     c. Collect generated SQL strings: B*G total completions

2. REWARD PHASE (CPU, no gradients):
   For each of the B*G generated SQL strings:
     a. Execute against in-memory flight database
     b. Compare records to gold SQL records
     c. Assign reward: +1 (correct), -1 (wrong/error)
   Result: rewards tensor of shape (B*G,)

3. ADVANTAGE PHASE:
   For each query i (group of G completions):
     a. Compute group mean: mu_i = mean(rewards[i*G : (i+1)*G])
     b. Compute group std:  sigma_i = std(rewards[i*G : (i+1)*G])
     c. Advantage: A_{i,j} = (reward_{i,j} - mu_i) / max(sigma_i, 1e-8)
     d. SKIP groups where sigma_i < 1e-6 (all-same-reward, zero information)
   Result: advantages tensor of shape (B*G,)

4. OLD LOG-PROB PHASE (torch.no_grad):
   For each completion:
     a. Run T5 forward pass with old/frozen policy weights
     b. Compute per-token log probs for the generated sequence
     c. Store as old_per_token_logps (detached)
   Result: old_logps tensor of shape (B*G, T) or (B*G,) if sequence-level

5. UPDATE PHASE (gradients enabled):
   For mu update iterations (typically mu=1 for on-policy):
     a. Run T5 forward pass with current policy weights
     b. Compute per-token log probs: per_token_logps
     c. Compute IS ratio: r = exp(per_token_logps - old_per_token_logps)
     d. Clip IS weight: r_hat = clamp(r, max=1+epsilon_high)
     e. Detach: r_hat = r_hat.detach()
     f. Compute loss: L = -(1/N_tokens) * sum(r_hat * A * per_token_logps * mask)
     g. Backward pass: L.backward()
     h. Gradient clipping: clip_grad_norm_(params, max_norm=1.0)
     i. Optimizer step: optimizer.step()

6. LOGGING:
   Log to W&B: loss, clip_frac, mean_ratio, mean_reward, frac_zero_std_groups,
   grad_norm, policy_entropy_estimate

7. EVALUATION (every eval_every_n_epochs):
   Run beam search on dev set, compute Record F1, compare to baseline.
   Early stop if no improvement for patience_epochs.

8. REFRESH OLD POLICY:
   Copy current model weights to old/frozen model (or: regenerate samples = on-policy).
   Recommended: regenerate every epoch (fully on-policy) given small dataset.
```

### Hyperparameter Recommendations for T5 + NL-to-SQL

| Parameter | GRPO Value | CISPO Value | Rationale |
|-----------|-----------|-------------|-----------|
| `epsilon` / `epsilon_high` | 0.2 | 0.3 | CISPO uses slightly larger clip since it only clips the weight, not the objective. Start conservative. |
| `group_size` (G) | 8 | 8 | Small dataset (4225 queries). G=8 gives 33,800 completions/epoch. Increase to 16 if reward variance is low. |
| `learning_rate` | 5e-6 | 5e-6 | Conservative for small model + small dataset. Standard for RL fine-tuning. |
| `kl_beta` | 0.0 - 0.05 | 0.0 | CISPO was designed without KL. GRPO can optionally use small KL. |
| `grad_clip_norm` | 1.0 | 1.0 | Essential. CISPO has open GitHub issues about gradient explosion without proper clipping. |
| `mu` (update iterations per sample) | 1 | 1 | On-policy is safest for small models. Off-policy (mu>1) risks stale IS ratios. |
| `temperature` (sampling) | 0.8 - 1.0 | 0.8 - 1.0 | Enough diversity for group variance. |
| `advantage_std_normalization` | Yes | Yes (or Dr. GRPO: No) | Standard normalization. Dr. GRPO suggests removing std to avoid difficulty bias, but for binary rewards with uniform difficulty, either works. |

### Known Stability Issues

**Gradient norm explosion (from MiniMax-M1 GitHub Issue #31):**
- Users report gradient norms stable at ~0.2 for 40 steps, then suddenly spiking to tens.
- Reported on Qwen2.5-7B and Qwen3-30B-A3B with CISPO + DAPO in verl framework.
- Suspected causes: missing modified Adam optimizer parameters, absent mask-based clipping from the MiniMax technical report.
- The exact `epsilon_low^IS` and `epsilon_high^IS` values used by MiniMax are not publicly disclosed.
- **Mitigation for our project:** (a) Use conservative `epsilon_high=0.3` (not the ms-swift default of 5.0 which is for large-scale training). (b) Monitor gradient norms closely. (c) Add gradient norm spike detection: if grad_norm > 10 * running_average, skip that update step. (d) Consider falling back to GRPO if CISPO shows instability.

### When to Use Which Algorithm

| Scenario | Recommended Algorithm | Why |
|----------|----------------------|-----|
| **This project (T5 + short SQL)** | GRPO first, CISPO as variant | GRPO is better understood, more community support. CISPO's advantages (token preservation) matter less for short sequences. |
| **Long reasoning traces (CoT)** | CISPO | Token dropout problem is severe for long traces with rare reflective tokens. |
| **Exploration-heavy tasks** | DAPO or CISPO | DAPO's clip-higher + dynamic sampling prevents entropy collapse. CISPO inherently preserves exploration. |
| **Small model + small data** | GRPO with KL | Conservative approach prevents catastrophic forgetting. |
| **Large model + large data** | CISPO | 2x speedup matters at scale. Token preservation improves sample efficiency. |
| **Maximum simplicity** | CISPO (sequence-level) | The loss function is simpler than PPO/GRPO's min() operation -- just clamp, detach, multiply. |

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

def grpo_train_step(policy_model, ref_model, batch, optimizer,
                    group_size, epsilon=0.2, epsilon_high=0.3,
                    grad_clip_norm=1.0, loss_type="grpo",
                    device="cuda"):
    """Single GRPO/CISPO training step.

    Steps:
    1. Generate G completions per query (sampling phase)
    2. Compute execution rewards for each completion
    3. Compute group-relative advantages
    4. Compute old policy log probs (from ref_model or frozen snapshot)
    5. Compute current policy log probs
    6. Apply GRPO or CISPO loss
    """
    # --- Step 5-6: Policy update (after steps 1-4 completed externally) ---
    # current_log_probs: (B*G,) or (B*G, T) depending on per-token vs sequence
    # old_log_probs: same shape, detached
    # advantages: (B*G,) group-normalized

    if loss_type == "grpo":
        log_ratio = current_log_probs - old_log_probs
        ratio = torch.exp(log_ratio)
        clipped_ratio = torch.clamp(ratio, 1 - epsilon, 1 + epsilon)
        loss = -torch.min(ratio * advantages, clipped_ratio * advantages).mean()
    elif loss_type == "cispo":
        log_ratio = current_log_probs - old_log_probs
        ratio = torch.exp(log_ratio)
        # CISPO: clip IS weight and DETACH -- gradient flows through log_probs only
        clamped_ratio = torch.clamp(ratio, max=1 + epsilon_high).detach()
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

def compute_group_advantages(rewards, group_size, use_std=True):
    """Normalize rewards within each group of G completions.

    Args:
        rewards: (B*G,) flat tensor of rewards
        group_size: G completions per query
        use_std: if True, divide by std (standard GRPO). If False, subtract mean only (Dr. GRPO).

    Returns:
        advantages: (B*G,) normalized advantages
        zero_std_frac: fraction of groups with zero reward variance (diagnostic)
    """
    B = rewards.shape[0] // group_size
    rewards_grouped = rewards.view(B, group_size)
    mean = rewards_grouped.mean(dim=1, keepdim=True)

    if use_std:
        std = rewards_grouped.std(dim=1, keepdim=True)
        # Track groups with zero variance (uninformative for learning)
        zero_std_mask = std.squeeze() < 1e-6
        zero_std_frac = zero_std_mask.float().mean().item()
        std = std.clamp(min=1e-8)
        advantages = (rewards_grouped - mean) / std
    else:
        # Dr. GRPO variant: no std normalization
        advantages = rewards_grouped - mean
        zero_std_frac = (rewards_grouped.std(dim=1) < 1e-6).float().mean().item()

    return advantages.view(-1), zero_std_frac
```

### Anti-Patterns to Avoid
- **Using TRL GRPOTrainer directly:** TRL has been moving away from encoder-decoder support. GRPOTrainer expects decoder-only models and integrates tightly with vLLM. Forcing it to work with T5 would require extensive monkey-patching.
- **Training a separate reward model:** The flight database provides a perfect deterministic reward signal. Training a neural reward model adds complexity with no benefit for this specific task.
- **Large group sizes (G > 16):** With T5-small (60M params) or T5-base (220M params), generation is fast but 4,225 training queries times G = 32 would mean 135,200 SQL executions per epoch. G = 8-16 is the sweet spot for this dataset size.
- **Removing the reference/old policy entirely:** While GRPO-Zero shows KL-free training works for large models, for a small T5 model on a small dataset, unconstrained policy updates can cause catastrophic forgetting. Keep either KL regularization or trust-region clipping.
- **Applying RL without prior SFT/DPO:** RL works best for refinement after the model already generates mostly correct SQL. Starting RL from a weak policy produces noisy gradients and slow convergence.
- **Using ms-swift's default `epsilon_high=5.0` for small models:** This is tuned for large-scale training (100B+ tokens). For T5-small/base on 4K queries, use `epsilon_high=0.3` to start. The MiniMax-M1 GitHub issue #31 documents gradient explosion with inappropriate epsilon values.
- **Computing old_log_probs from `.generate()` scores:** The scores from generate() may differ in precision and masking from the training forward pass. Always recompute old_log_probs using the same forward pass function (e.g., `compute_restricted_log_probs()`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SQL execution for rewards | Custom DB connector | Existing `_execute_sql()` + `_get_mem_conn()` from `dpo_data.py` | Already handles in-memory SQLite, timeout, error recovery. Battle-tested on 42K+ queries. |
| Constrained SQL decoding | Custom beam search | Existing `FlightSQLVocab.get_prefix_allowed_tokens_fn()` | Already restricts output to ~600 valid SQL tokens. Works with HF `.generate()`. |
| Per-token log prob computation | Custom forward pass | Existing `compute_restricted_log_probs()` from `dpo_loss.py` | Already handles restricted vocab remapping, padding masks, sequence-level log prob sums. Minor modification needed for per-token return. |
| W&B tracking | Direct wandb calls | Existing `src/wandb_utils.py` helpers | Project convention; handles sweep detection, metric namespacing, artifact upload. |
| Training loop boilerplate | From scratch | Pattern from existing `dpo_train.py` | Checkpointing, early stopping, graceful stop, wall-clock budget, GPU lock -- all reusable. |
| Gold SQL record caching | Recompute each time | Existing `_load_or_compute_gold_records()` from `dpo_data.py` | Cached to `records/gold_train_records.pkl`, loads in <1s vs 30min recompute. |

**Key insight:** The DPO codebase already contains 80% of the infrastructure needed for GRPO/CISPO. The main new code is: (1) the GRPO/CISPO loss function (~50 lines), (2) the group sampling + reward computation loop (~100 lines), and (3) config/training loop wiring (~150 lines). This is a modest extension, not a ground-up build.

## Common Pitfalls

### Pitfall 1: Reward Sparsity with Binary Execution Reward
**What goes wrong:** If most model completions are correct (reward +1) or most are wrong (reward -1), the group variance is near-zero and advantages become uninformative.
**Why it happens:** Binary reward has no gradient between "totally wrong" and "almost right." After SFT, many queries are already correct.
**How to avoid:** Use a composite reward: execution accuracy (+1/0/-1) as primary, plus a soft partial credit signal. Options: (a) Jaccard similarity of records (partial match), (b) n-gram overlap with gold SQL, (c) schema-linking accuracy. Start with binary, add partial credit only if reward sparsity is observed (check `frac_reward_zero_std` metric). Consider DAPO-style dynamic sampling: skip groups where all completions have identical rewards.
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

### Pitfall 7: CISPO Gradient Norm Explosion (NEW)
**What goes wrong:** After ~40 training steps, gradient norms suddenly spike from ~0.2 to tens or hundreds.
**Why it happens:** CISPO's detached IS weights can create large loss magnitudes when `epsilon_high` is too large or when the policy drifts significantly from the old policy. Reported in MiniMax-M1 GitHub issue #31.
**How to avoid:** (a) Use conservative `epsilon_high=0.3` (not 5.0). (b) Monitor gradient norms and add spike detection. (c) Implement gradient norm anomaly detection: skip update if `grad_norm > 10 * ema_grad_norm`. (d) Ensure fresh on-policy samples each epoch (mu=1). (e) Fall back to GRPO if CISPO is unstable.
**Warning signs:** Sudden gradient norm spike after stable initial training, NaN loss, policy ratio distribution shifting rapidly.

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
    epsilon: float = 0.2                 # clipping parameter (GRPO)
    epsilon_high: float = 0.3            # CISPO upper clip (only for cispo)
    kl_beta: float = 0.0                # KL penalty weight (0 = no KL)
    reward_type: str = "binary"          # "binary" or "partial"
    use_std_normalization: bool = True   # True=GRPO, False=Dr.GRPO advantage

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

    # Stability
    max_grad_norm_spike_factor: float = 10.0  # skip update if grad_norm > factor * ema

    # Base model to start RL from
    base_checkpoint_path: str = "output/t5_ft_base_sweep_1i8vr3_20260314_012024/checkpoints/model_best.pt"
```

### Advantage Computation (from DeepSeekMath + MiniMax-M1 papers)
```python
# Source: DeepSeekMath paper (2402.03300) + MiniMax-M1 paper (2506.13585)

def compute_advantages(rewards: torch.Tensor, group_size: int,
                       scale_by_std: bool = True) -> tuple[torch.Tensor, float]:
    """Group-relative advantage normalization.

    rewards: (B*G,) flat reward tensor
    group_size: G completions per query
    Returns: (B*G,) advantages, fraction of zero-std groups
    """
    B = rewards.shape[0] // group_size
    grouped = rewards.view(B, group_size)  # (B, G)
    mean = grouped.mean(dim=1, keepdim=True)

    std = grouped.std(dim=1, keepdim=True)
    zero_std_frac = (std.squeeze() < 1e-6).float().mean().item()

    if scale_by_std:
        std = std.clamp(min=1e-8)
        advantages = (grouped - mean) / std
    else:
        advantages = grouped - mean
    return advantages.view(-1), zero_std_frac
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
# Source: MiniMax-M1 paper (2506.13585) + ms-swift implementation + TorchRL CISPOLoss

def cispo_loss(current_log_probs, old_log_probs, advantages, epsilon_high=0.3):
    """CISPO: Clipped Importance Sampling Policy Optimization.

    Clips the IS weight (detached) rather than the surrogate objective.
    Gradient flows ONLY through current_log_probs, never through the clipped weight.

    This is the sequence-level variant. For per-token, see cispo_loss_per_token().
    """
    log_ratio = current_log_probs - old_log_probs
    ratio = torch.exp(log_ratio)

    # Core CISPO innovation: clamp and DETACH the IS weight
    clamped = torch.clamp(ratio, max=1 + epsilon_high).detach()

    # Loss = -weight * advantage * log_prob
    # Gradient: d/d_theta L = -clamped * advantage * d/d_theta(log_pi_theta)
    # Every sample contributes gradient (unlike GRPO where clipped samples get zero gradient)
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
| GRPO advantage (mean/std) | Dr. GRPO (mean only, no std) | Mar 2025 | Removes difficulty bias and length bias |
| Binary execution reward | Composite reward (execution + schema + n-gram) | Reasoning-SQL, Mar 2025 | Addresses reward sparsity for Text-to-SQL |
| DPO for alignment | GRPO/CISPO for online RL | DeepSeek-R1, Jan 2025 | Online RL outperforms offline preference optimization for reasoning tasks |
| GRPO for Text-to-SQL | AGRO-SQL (agentic GRPO) | Dec 2025 | Multi-stage GRPO with data synthesis |

**Key distinction: DPO vs GRPO/CISPO**
- DPO is offline: learns from pre-collected preference pairs (chosen vs rejected). No online generation.
- GRPO/CISPO is online: generates new completions each iteration, gets fresh reward feedback, updates policy. More compute-intensive but can explore and improve beyond the training distribution.
- For NL-to-SQL, the execution reward makes online RL particularly attractive -- the reward is deterministic, cheap to compute, and perfectly aligned with the evaluation metric.

**GRPO for Text-to-SQL is a well-established pattern (2025):**
- Reasoning-SQL: GRPO on Qwen 7B, +6.77% execution accuracy
- Multilingual Text-to-SQL: GRPO on Llama-3 3B, +27pp execution accuracy (3K examples)
- AGRO-SQL: Agentic GRPO with data synthesis
- PaVeRL-SQL: Partial-match rewards with GRPO
- All use decoder-only models. No published T5 encoder-decoder GRPO work exists.

**Deprecated/outdated:**
- PPO for LLM alignment: Still works but GRPO is simpler and equally effective for most tasks.
- RLHF with trained reward models for code/SQL: Execution-based rewards are more accurate and cheaper.

## Open Questions

1. **How much improvement can RL give over SFT/DPO for T5-small/base?**
   - What we know: Reasoning-SQL shows 6.77% improvement from GRPO on 7B Qwen model. SLM-SQL shows GRPO works on 0.5-1.5B models. Multilingual Text-to-SQL shows +27pp on Llama-3 3B with just 3K examples (similar to our 4.2K).
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

4. **Per-token vs per-sequence CISPO for T5 on short SQL?**
   - What we know: The original CISPO paper uses per-token ratios. The existing `compute_restricted_log_probs` returns sequence-level log probs. Per-token CISPO's advantage (preserving rare token gradients) matters most for long reasoning traces.
   - What's unclear: Whether per-token offers any benefit for SQL sequences of 20-50 tokens with a constrained 600-token vocabulary.
   - Recommendation: Start with sequence-level (reuses existing code, simpler). Per-token is available as an optimization if sequence-level shows instability or poor convergence.

5. **What epsilon_high value is appropriate for T5-small/base?**
   - What we know: ms-swift defaults to 5.0 (large-scale training). MiniMax-M1 does not disclose their exact values. Emergentmind reports ablations suggesting 0.3 is optimal for variance reduction. MiniMax-M1 issue #31 reports gradient explosion at unspecified epsilon values.
   - What's unclear: No published epsilon_high ablation for small models or short sequences.
   - Recommendation: Start with `epsilon_high=0.3`. If clipping fraction is very low (< 0.01), increase to 0.5. If gradient norms spike, decrease to 0.2.

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
- [MiniMax-M1 paper (arXiv 2506.13585)](https://arxiv.org/html/2506.13585v1) - CISPO algorithm definition, loss function, advantage estimation, Figure 2 ablation
- [DeepSeekMath paper (arXiv 2402.03300)](https://arxiv.org/abs/2402.03300) - Original GRPO algorithm definition
- [TRL GRPOTrainer documentation](https://huggingface.co/docs/trl/grpo_trainer) - GRPO implementation reference, confirms encoder-decoder not supported
- [TorchRL CISPOLoss](https://docs.pytorch.org/rl/main/_modules/torchrl/objectives/llm/grpo.html) - Production PyTorch CISPO implementation with asymmetric clipping
- [ms-swift CISPO documentation](https://swift.readthedocs.io/en/latest/Instruction/GRPO/AdvancedResearch/CISPO.html) - CISPO implementation reference with epsilon_high=5.0 default, per-token code
- [ms-swift loss types](https://swift.readthedocs.io/en/latest/Instruction/GRPO/DeveloperGuide/loss_types.html) - GRPO/BNPO/DAPO/CISPO normalization comparison
- [RLHF Book Chapter 6 (Nathan Lambert)](https://rlhfbook.com/c/06-policy-gradients) - CISPO/GRPO/PPO mathematical comparison, gradient flow analysis
- [Reasoning-SQL (arXiv 2503.23157)](https://arxiv.org/html/2503.23157v1) - GRPO applied to Text-to-SQL with composite rewards

### Secondary (MEDIUM confidence)
- [GRPO++ / Cameron Wolfe](https://cameronrwolfe.substack.com/p/grpo-tricks) - DAPO/Dr. GRPO improvements, practical tips, token-level clipping analysis
- [Beyond PPO (ydnyshhh blog)](https://ydnyshhh.github.io/posts/policy_optimization/) - Unified comparison of PPO/GRPO/DAPO/CISPO/GSPO with mathematical formulations and token mask view
- [EmergentMind CISPO topic](https://www.emergentmind.com/topics/cispo-algorithm) - CISPO hyperparameter recommendations (epsilon_high=0.3), pseudocode workflow
- [RLHF Book code repo](https://github.com/natolambert/rlhf-book/tree/main/code) - Educational CISPO implementation in policy_gradients/
- [Multilingual Text-to-SQL with GRPO (arXiv 2510.13827)](https://arxiv.org/html/2510.13827) - GRPO on Llama-3 3B for SQL, +27pp exec accuracy, lr=5e-6, KL beta=0.02
- [MiniMax-M1 GitHub Issue #31](https://github.com/MiniMax-AI/MiniMax-M1/issues/31) - Gradient norm explosion with CISPO, stability concerns

### Tertiary (LOW confidence)
- [Graph-Reward-SQL (arXiv 2505.12380)](https://arxiv.org/html/2505.12380v1) - Alternative reward signals for SQL RL (not directly applicable)
- [SLM-SQL (arXiv 2507.22478)](https://arxiv.org/html/2507.22478v1) - GRPO on small (0.5-1.5B) models for SQL (decoder-only, not T5)
- [ASPO paper (arXiv 2510.06062)](https://arxiv.org/abs/2510.06062) - Asymmetric IS variant, extends CISPO concept

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new libraries needed, all infrastructure exists in project
- CISPO algorithm: HIGH - Mathematical formulation verified across 5+ independent sources (MiniMax paper, ms-swift code, TorchRL code, RLHF Book, blog analyses)
- CISPO vs GRPO comparison: HIGH - Differences clearly documented in multiple authoritative sources with consistent descriptions
- Architecture (T5 applicability): MEDIUM - Algorithm is architecture-agnostic in principle, but NO published work applies GRPO/CISPO to encoder-decoder T5. Feasibility is reasoned from first principles, not empirically demonstrated.
- Pitfalls: MEDIUM-HIGH - Pitfalls informed by published papers, GitHub issues (gradient explosion), and general RL experience. T5-specific failure modes are hypothesized but the gradient explosion pitfall is empirically documented.
- Open-source implementations: HIGH - Verified in ms-swift, TorchRL, and RLHF Book. None support encoder-decoder.
- Feasibility for this project: MEDIUM - The algorithm should work in principle. Gains on T5-small/base with 4K training examples are uncertain. The main risk is that CISPO's advantages (token preservation for rare reasoning tokens) are irrelevant for short constrained SQL generation.

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (30 days -- algorithms are stable, ecosystem is fast-moving)
