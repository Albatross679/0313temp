# Phase 2: DPO Training - Research

**Researched:** 2026-03-13
**Domain:** Direct Preference Optimization (DPO) for T5 encoder-decoder NL-to-SQL
**Confidence:** HIGH

## Summary

Phase 2 applies DPO (Direct Preference Optimization) to the best fine-tuned T5 model from Phase 1 to improve Record F1 on the NL-to-SQL task. The existing codebase already contains substantial DPO infrastructure: preference data generation (`part1/dpo_data.py`), DPO loss computation (`part1/dpo_loss.py`), and a full DPO training loop (`part1/dpo_train.py`). The config system has a `T5DPOConfig` for full fine-tune DPO. What remains is: (1) fixing a data format incompatibility between generation and training, (2) adding a LoRA DPO variant config and modifying the training loop to support LoRA, (3) running both variants, comparing against baseline, and (4) finalizing test outputs at the correct submission paths.

The RTX 5090 (32GB VRAM) provides ample memory for DPO. Even running two full T5-base models (policy + reference) in FP32 requires only ~1.7GB. The main time constraint is tight deadlines (~1-2 days per STATE.md), so the approach should focus on execution speed: use existing infrastructure, fix the known bug, add LoRA support, run both variants, pick the winner.

**Primary recommendation:** Fix the preference data format mismatch, install `peft`, add `T5DPOConfig_lora`, modify `dpo_train.py` to support LoRA policy models, run both full-FT and LoRA DPO, compare dev F1 against baseline, and copy the winner's outputs to the submission paths.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DPO-01 | Generate preference pairs by sampling multiple SQL outputs from best fine-tuned T5 per query | Existing `part1/dpo_data.py` implements hybrid Phase A (model-generated negatives) + Phase B (execution-aware perturbations). Needs checkpoint path from Phase 1 output. |
| DPO-02 | Rank preference pairs by SQL execution correctness against ground truth | Already implemented in `dpo_data.py` -- candidates are executed against `flight_database.db` and compared to gold records. |
| DPO-03 | Implement DPO training loop for T5 (full fine-tune) | Fully implemented in `part1/dpo_train.py` with `dpo_train()` function. Uses `dpo_loss.py` for loss computation. Has W&B logging, early stopping, checkpointing. **Bug to fix:** data format mismatch between `dpo_data.py` (saves tuples as JSON arrays) and `dpo_train.py` (expects dicts with `"nl"`, `"chosen"`, `"rejected"` keys). |
| DPO-04 | Implement DPO training with LoRA | Needs new `T5DPOConfig_lora` config and modifications to `dpo_train.py` to apply LoRA to the policy model. Can use `peft.disable_adapter()` context manager to get reference logprobs from the base model without loading a separate reference model. `peft` package must be installed first. |
| DPO-05 | Compare DPO with and without LoRA on dev set metrics | Both variants need to run and log dev Record F1 to W&B. Comparison is straightforward from logged metrics. |
| DPO-06 | Evaluate best DPO model on dev set (Record F1, Query EM) | `dpo_train.py` already runs final dev eval with full beam search and saves to `results/t5_dpo_dev.sql`, `records/t5_dpo_dev.pkl`. |
| DPO-07 | If DPO improves dev F1, regenerate test SQL and records | Current code saves to `results/t5_dpo_test.sql` -- needs to be changed to write to `results/t5_ft_test.sql` and `records/t5_ft_test.pkl` (submission paths) when DPO wins, or retain baseline outputs if it does not. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| torch | 2.1.2 | Model training, DPO loss, gradient computation | Already in requirements.txt |
| transformers | 4.40.0 | T5ForConditionalGeneration, tokenizer | Already in requirements.txt |
| peft | latest (>=0.7) | LoRA adapter for DPO variant | **NOT INSTALLED -- must pip install** |
| wandb | 0.15.10 | Experiment tracking | Already in requirements.txt |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlite3 | stdlib | SQL execution for preference pair validation | Already used in dpo_data.py |
| tqdm | 4.66.1 | Progress bars | Already used everywhere |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom DPO loss | HuggingFace TRL DPOTrainer | TRL is heavyweight, not installed, project already has working custom implementation |
| Two full models for LoRA DPO | peft `disable_adapter()` trick | Single model + toggle saves VRAM, simpler code, standard peft pattern |

**Installation:**
```bash
pip install peft
```

## Architecture Patterns

### Existing DPO Architecture (already in codebase)
```
part1/
├── config.py           # T5DPOConfig (full FT DPO) -- needs T5DPOConfig_lora
├── dpo_data.py         # Preference data generation (Phase A + B)
├── dpo_loss.py         # compute_restricted_log_probs, dpo_loss, dpo_train_step
├── dpo_train.py        # DPODataset, dpo_collate_fn, dpo_train loop, main()
├── model_flightdb.py   # FlightSQLVocab, T5ForFlightSQL (restricted vocab wrapper)
├── model.py            # initialize_model, save_model, load_model_from_checkpoint
└── train.py            # _generate_predictions, eval_epoch_gpu, eval_epoch_sql, test_inference
```

### Pattern 1: DPO Training Pipeline (Existing)
**What:** Load base checkpoint -> create policy + frozen reference -> train DPO -> evaluate -> test inference
**When to use:** Full fine-tune DPO (DPO-03)
**Key code path:** `dpo_train.py::main()` -> loads T5DPOConfig -> builds DPODataset -> calls dpo_train() -> final eval + test

### Pattern 2: LoRA DPO with disable_adapter (New)
**What:** Load base checkpoint -> apply LoRA -> use `model.disable_adapter_layers()` for reference logprobs -> train only LoRA params
**When to use:** LoRA DPO variant (DPO-04)
**Example:**
```python
# Source: peft documentation + andersonbcdefg/dpo-lora pattern
from peft import LoraConfig, get_peft_model, TaskType

# Apply LoRA to the inner HF model
lora_config = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                         target_modules=["q", "v"], task_type=TaskType.SEQ_2_SEQ_LM)

# For T5ForFlightSQL wrapper:
inner = policy_model.model  # the HF T5ForConditionalGeneration
peft_model = get_peft_model(inner, lora_config)
policy_model.model = peft_model

# Reference logprobs: disable LoRA adapters temporarily
with peft_model.disable_adapter_layers():
    ref_logprobs = compute_restricted_log_probs(policy_model, ...)
# Policy logprobs: LoRA active (default)
policy_logprobs = compute_restricted_log_probs(policy_model, ...)
```

### Pattern 3: Preference Data Generation (Existing)
**What:** Two-phase hybrid approach: (A) sample candidates from model, rank by execution correctness; (B) perturbation-based negatives for correct queries
**When to use:** DPO-01, DPO-02
**Key function:** `dpo_data.py::generate_preference_data()` -- uses `_generate_candidates_batch()` for Phase A and `_generate_perturbation_pairs()` for Phase B

### Anti-Patterns to Avoid
- **Loading two full copies for LoRA DPO:** Wasteful when peft `disable_adapter_layers()` provides reference logprobs from the same model with LoRA temporarily disabled.
- **Hardcoding checkpoint paths in config:** The T5DPOConfig hardcodes `base_checkpoint_path` to a specific restricted_v3 path. After Phase 1, the best model path may differ (could be T5-base). The executor must update this path based on Phase 1 outcome.
- **Saving DPO test outputs to wrong path:** Current code saves to `results/t5_dpo_test.sql` not the submission path `results/t5_ft_test.sql`. Must be fixed or a copy step added.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LoRA adapter management | Custom weight masking | `peft` LoraConfig + get_peft_model | Handles gradient routing, merge/unload, save/load, disable_adapter |
| Reference model log probs in LoRA | Loading second full model | `peft_model.disable_adapter_layers()` | Standard pattern, saves VRAM, avoids synchronization bugs |
| DPO loss function | Custom derivation | Existing `dpo_loss.py::dpo_loss()` | Already implemented and correct: L = -log(sigmoid(beta * (pi_chosen - ref_chosen - pi_rejected + ref_rejected))) |
| Preference data generation | Custom sampling pipeline | Existing `dpo_data.py` | Already implements hybrid Phase A + B with execution-aware validation |

**Key insight:** The codebase already has 90% of the DPO infrastructure. The main work is fixing bugs, adding LoRA support, and orchestrating the pipeline.

## Common Pitfalls

### Pitfall 1: Preference Data Format Mismatch (CRITICAL BUG)
**What goes wrong:** `dpo_data.py::save_preference_data()` saves triplets as JSON arrays `[[nl, chosen, rejected], ...]` but `dpo_train.py::load_preference_data()` expects dicts `[{"nl": ..., "chosen": ..., "rejected": ...}, ...]`. Loading will crash with `TypeError: tuple indices must be integers or slices, not str`.
**Why it happens:** Two functions written independently with different serialization formats.
**How to avoid:** Fix either the save function (to emit dicts) or the load function (to accept arrays). Recommended: fix the save function in `dpo_data.py` to save dicts for clarity, since dicts are self-documenting.
**Warning signs:** `KeyError: 'nl'` or `TypeError` when loading preference data.

### Pitfall 2: Checkpoint Path Dependency on Phase 1
**What goes wrong:** `T5DPOConfig.base_checkpoint_path` is hardcoded to `output/t5_ft_restricted_v3_20260311_054501/checkpoints/model_best.pt`. After Phase 1, the best model might be T5-base or a different T5-small run.
**Why it happens:** Config was written before Phase 1 restructuring.
**How to avoid:** The executor must dynamically set `base_checkpoint_path` based on Phase 1 outcome (either via CLI override `--base_checkpoint_path` or by auto-detecting the latest best checkpoint).
**Warning signs:** `AssertionError: Base checkpoint not found`.

### Pitfall 3: Test Output Path Mismatch
**What goes wrong:** `dpo_train.py` saves test outputs to `results/t5_dpo_test.sql` and `records/t5_dpo_test.pkl`, but the submission requires `results/t5_ft_test.sql` and `records/t5_ft_test.pkl`.
**Why it happens:** DPO code uses its own naming, separate from the graded submission paths.
**How to avoid:** After DPO evaluation, if DPO improves F1, copy/rename outputs to the submission paths. Or modify the code to accept configurable output paths.
**Warning signs:** Missing submission files after DPO run.

### Pitfall 4: peft Not Installed
**What goes wrong:** `ModuleNotFoundError: No module named 'peft'` when attempting LoRA DPO.
**Why it happens:** `peft` is not in `requirements.txt` and is not installed in the environment.
**How to avoid:** Run `pip install peft` before LoRA DPO training.
**Warning signs:** Import error at runtime.

### Pitfall 5: LoRA + Restricted Vocab Interaction
**What goes wrong:** When LoRA is applied to the inner HF model inside `T5ForFlightSQL`, the `restricted_forward()` and `state_dict()` methods need to correctly handle the peft-wrapped model.
**Why it happens:** `T5ForFlightSQL.state_dict()` already has peft key cleaning logic, but `compute_restricted_log_probs()` calls `model.restricted_forward()` which calls `self.model.encoder()` and `self.model.decoder()`. With peft wrapping, `self.model` becomes a PeftModel that still exposes `.encoder()` and `.decoder()` via delegation.
**How to avoid:** Test that `restricted_forward()` works correctly with peft-wrapped inner model. The existing code already handles this (line 173-191 of model_flightdb.py accesses `self.model.encoder` and `self.model.decoder`; peft delegates these correctly).
**Warning signs:** AttributeError or dimension mismatch during forward pass.

### Pitfall 6: DPO Beta Too High or Too Low
**What goes wrong:** DPO loss diverges (beta too low, policy drifts too far from reference) or DPO has no effect (beta too high, policy stays too close to reference).
**Why it happens:** Beta controls the KL penalty strength. Default is 0.1 which is standard for DPO.
**How to avoid:** Keep beta=0.1 (the config default). If reward accuracy stays at ~0.5, beta may be too high. If reward accuracy is 1.0 but F1 drops, beta may be too low.
**Warning signs:** reward_accuracy near 0.5 (no learning) or F1 degradation.

## Code Examples

### Preference Data Generation (Existing)
```python
# Source: part1/dpo_data.py (existing code, proven working)
# Run from CLI:
python part1/dpo_data.py \
    --checkpoint output/<best_model>/checkpoints/model_best.pt \
    --output output/dpo_preference_data.json \
    --n_candidates 10 --temperature 1.0 --top_k 50 --max_pairs 3 --batch_size 8
```

### DPO Training - Full Fine-Tune (Existing)
```python
# Source: part1/dpo_train.py (existing code)
python part1/dpo_train.py \
    --base_checkpoint_path output/<best_model>/checkpoints/model_best.pt \
    --preference_data_path output/dpo_preference_data.json
```

### DPO Training - LoRA Variant (New, to be implemented)
```python
# Pattern for modifying dpo_train.py to support LoRA:
from peft import LoraConfig, get_peft_model, TaskType

# In main(), after loading policy_model:
if getattr(cfg, "use_lora", False):
    lora_config = LoraConfig(
        r=cfg.lora_r, lora_alpha=cfg.lora_alpha,
        lora_dropout=cfg.lora_dropout,
        target_modules=cfg.lora_target_modules,
        task_type=TaskType.SEQ_2_SEQ_LM,
    )
    policy_model.model = get_peft_model(policy_model.model, lora_config)
    # No separate reference model needed -- use disable_adapter_layers()
    ref_model = None  # signal to use disable_adapter approach
```

### LoRA DPO Loss Computation with disable_adapter
```python
# Modified dpo_train_step for LoRA (single model):
def dpo_train_step_lora(policy_model, batch, optimizer, beta=0.1, grad_clip_norm=1.0, device="cuda"):
    prompt_ids, prompt_mask, chosen_dec_in, chosen_tgt, rej_dec_in, rej_tgt = [
        t.to(device) for t in batch
    ]
    # Policy forward (LoRA active)
    policy_chosen = compute_restricted_log_probs(policy_model, prompt_ids, prompt_mask, chosen_dec_in, chosen_tgt)
    policy_rejected = compute_restricted_log_probs(policy_model, prompt_ids, prompt_mask, rej_dec_in, rej_tgt)

    # Reference forward (LoRA disabled = base model)
    with torch.no_grad():
        policy_model.model.disable_adapter_layers()
        ref_chosen = compute_restricted_log_probs(policy_model, prompt_ids, prompt_mask, chosen_dec_in, chosen_tgt)
        ref_rejected = compute_restricted_log_probs(policy_model, prompt_ids, prompt_mask, rej_dec_in, rej_tgt)
        policy_model.model.enable_adapter_layers()

    loss, chosen_reward, rejected_reward = dpo_loss(
        policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta=beta)
    optimizer.zero_grad()
    loss.backward()
    grad_norm = torch.nn.utils.clip_grad_norm_(policy_model.parameters(), grad_clip_norm).item()
    optimizer.step()
    return {"loss": loss.item(), ...}
```

### Fixing Preference Data Format
```python
# Fix in dpo_data.py save_preference_data():
def save_preference_data(triplets, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = [{"nl": t[0], "chosen": t[1], "rejected": t[2]} for t in triplets]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| RLHF with reward model | DPO (reward-free) | 2023 (Rafailov et al.) | Simpler, no reward model needed, stable training |
| Two full model copies for DPO | LoRA + disable_adapter | 2024+ (peft ecosystem) | ~50% VRAM savings, cleaner code |
| Manual LoRA implementation | peft library | 2023+ | Standardized, handles save/load/merge |

**Deprecated/outdated:**
- TRL DPOTrainer: Overly heavyweight for this project's needs. The custom implementation in `dpo_loss.py` is simpler and sufficient.

## Open Questions

1. **What is the Phase 1 best model?**
   - What we know: Could be T5-small (restricted_v3 checkpoint exists at `output/t5_ft_restricted_v3/checkpoints/model_best.pt`, F1=0.618) or T5-base (if Phase 1 produces a better model)
   - What's unclear: Phase 1 hasn't executed yet
   - Recommendation: Plans should handle both cases. The DPO config's `base_checkpoint_path` must be set dynamically by the executor based on Phase 1 outcome. The preference data generation must use the correct model checkpoint.

2. **Is T5-base or T5-small the DPO target?**
   - What we know: If T5-base wins in Phase 1, DPO should be applied to T5-base. The existing `T5DPOConfig` defaults to `google-t5/t5-small`.
   - What's unclear: Which model will win Phase 1
   - Recommendation: The `T5DPOConfig.model_checkpoint` field must match the Phase 1 winner. Plans should instruct the executor to update this.

3. **Expected preference data volume?**
   - What we know: 4,225 training examples. With max_pairs=3 per example, up to ~12,675 triplets. Realistically, Phase A + B produces fewer (not every example yields 3 pairs).
   - What's unclear: Exact yield depends on model quality (better model = more Phase B perturbation pairs)
   - Recommendation: Expect 5,000-10,000 triplets. DPO training with batch_size=8 and 5 epochs is very fast (<30 min for T5-small, <1 hour for T5-base).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4.4 |
| Config file | pyproject.toml (if exists) or default |
| Quick run command | `python -c "<inline verification>"` |
| Full suite command | `python -m pytest tests/ -x` (if tests exist) |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DPO-01 | Preference pairs generated from best T5 model | smoke | `python -c "import json; d=json.load(open('output/dpo_preference_data.json')); assert len(d) > 100; print(f'{len(d)} triplets')"` | Depends on Wave 0 |
| DPO-02 | Pairs ranked by execution correctness | smoke | `python -c "import json; d=json.load(open('output/dpo_preference_data.json')); t=d[0]; assert 'nl' in t and 'chosen' in t and 'rejected' in t; print('Format OK')"` | Depends on Wave 0 |
| DPO-03 | Full FT DPO training loop works | integration | `python -c "from part1.dpo_train import load_preference_data, DPODataset, dpo_collate_fn; print('DPO imports OK')"` | Exists (part1/dpo_train.py) |
| DPO-04 | LoRA DPO variant works | integration | `python -c "from peft import LoraConfig; from part1.config import T5DPOConfig_lora; print('LoRA DPO config OK')"` | Wave 0 (config needs creation) |
| DPO-05 | Comparison of DPO variants on dev F1 | manual-only | Compare W&B logged metrics for full-FT vs LoRA DPO runs | N/A |
| DPO-06 | Best DPO model dev eval | smoke | `python -c "import os; assert os.path.exists('results/t5_dpo_dev.sql'); print('Dev eval output exists')"` | Depends on DPO run |
| DPO-07 | Test outputs at submission paths if DPO wins | smoke | `python -c "import os; assert os.path.exists('results/t5_ft_test.sql') and os.path.getsize('results/t5_ft_test.sql') > 0; print('Test outputs OK')"` | Depends on DPO outcome |

### Sampling Rate
- **Per task commit:** Inline verification commands after each code change
- **Per wave merge:** Run all smoke tests
- **Phase gate:** Verify `results/t5_ft_test.sql` and `records/t5_ft_test.pkl` exist and are non-empty

### Wave 0 Gaps
- [ ] `pip install peft` -- required for LoRA DPO (DPO-04)
- [ ] Fix `dpo_data.py::save_preference_data()` to save dicts instead of tuples -- required for DPO-01/DPO-03 compatibility
- [ ] Create `T5DPOConfig_lora` in `part1/config.py` -- required for DPO-04
- [ ] Update `T5DPOConfig.base_checkpoint_path` to use Phase 1 best model -- required for all DPO reqs

## Sources

### Primary (HIGH confidence)
- **Codebase inspection** -- `part1/dpo_data.py`, `part1/dpo_loss.py`, `part1/dpo_train.py`, `part1/config.py` (read in full)
- **Codebase inspection** -- `part1/train.py`, `part1/model.py`, `part1/model_flightdb.py`, `part1/data.py` (read in full)
- **Codebase inspection** -- `src/config.py`, `src/wandb_utils.py` (read in full)
- [DPO Paper (Rafailov et al., 2023)](https://arxiv.org/abs/2305.18290) -- DPO loss formulation verified against `dpo_loss.py` implementation
- [peft LoRA documentation](https://huggingface.co/docs/peft/main/en/developer_guides/lora) -- disable_adapter_layers pattern
- [andersonbcdefg/dpo-lora](https://github.com/andersonbcdefg/dpo-lora) -- DPO with single model copy via LoRA disable

### Secondary (MEDIUM confidence)
- [TRL DPOTrainer docs](https://huggingface.co/docs/trl/v0.8.0/dpo_trainer) -- reference adapter pattern
- [torchtune disable_adapter](https://docs.pytorch.org/torchtune/stable/generated/torchtune.modules.peft.disable_adapter.html) -- context manager API reference

### Tertiary (LOW confidence)
- None -- all findings verified against codebase or official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use except peft (which is standard and verified to work with transformers 4.40.0)
- Architecture: HIGH - 90% of DPO infrastructure already exists in codebase; patterns verified by reading all source files
- Pitfalls: HIGH - All 6 pitfalls identified by direct code inspection (format mismatch, path issues, missing package)

**Research date:** 2026-03-13
**Valid until:** 2026-03-20 (stable domain, code-specific findings)
