"""Restricted SQL output vocabulary for T5 on the flight database.

Implements Option B (subset projection): the encoder uses the full T5 vocabulary
to understand English NL queries, but the decoder output is projected against only
the ~600 embedding rows that correspond to valid SQL tokens.  This reduces the
softmax width by ~54x, concentrating gradient signal and cutting memory usage.
"""

import torch
import torch.nn as nn
from transformers import T5ForConditionalGeneration, T5TokenizerFast

# ── Extra SQL tokens to include beyond what appears in train/dev data ────────

EXTRA_SQL_KEYWORDS = [
    # Ordering / grouping
    "GROUP BY", "ORDER BY", "ASC", "DESC", "HAVING",
    # Joins
    "JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "OUTER JOIN", "ON", "USING",
    # Set operations
    "UNION", "UNION ALL", "INTERSECT", "EXCEPT",
    # Subquery / existence
    "IN", "EXISTS", "ANY", "ALL",
    # Conditional
    "CASE", "WHEN", "THEN", "ELSE", "END",
    # Aggregates
    "SUM", "AVG", "COUNT",
    # Misc SQL
    "AS", "LIKE", "LIMIT", "OFFSET",
    "CAST", "COALESCE",
    # Comparison operators
    ">=", "<=", "<>", "!=",
    # Common numeric literals that may appear in test queries
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
    "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31",
    "100", "200", "500", "1000", "2000",
    "0000", "0800", "0900", "1200", "1700", "1800", "2100", "2200", "2359",
]


# ── FlightSQLVocab ──────────────────────────────────────────────────────────


class FlightSQLVocab:
    """Builds and manages a restricted SQL output vocabulary.

    Scans training SQL files to collect every token ID that appears, adds extra
    SQL keywords and special tokens, then provides forward/reverse mappings
    between the original T5 token space and the restricted index space.
    """

    def __init__(
        self,
        tokenizer=None,
        sql_paths=("data/train.sql", "data/dev.sql"),
        extra_keywords=None,
        full_vocab_size=32128,
    ):
        if tokenizer is None:
            tokenizer = T5TokenizerFast.from_pretrained("google-t5/t5-small")
        self.tokenizer = tokenizer
        self.full_vocab_size = full_vocab_size

        # Collect token IDs from SQL data files
        token_ids = set()
        for path in sql_paths:
            with open(path) as f:
                for line in f:
                    ids = tokenizer.encode(line.strip(), add_special_tokens=True)
                    token_ids.update(ids)

        # Add extra SQL keyword tokens
        for kw in (extra_keywords or EXTRA_SQL_KEYWORDS):
            ids = tokenizer.encode(kw, add_special_tokens=False)
            token_ids.update(ids)

        # Ensure special tokens are present
        token_ids.update({0, 1, 32099})  # PAD, EOS, BOS (<extra_id_0>)

        # Sort for deterministic indexing (PAD=0 will be at index 0)
        sorted_ids = sorted(token_ids)

        self.sql_token_ids = torch.tensor(sorted_ids, dtype=torch.long)
        self.vocab_size = len(sorted_ids)

        # Reverse mapping: original_token_id → restricted_index  (-1 = unmapped)
        self._orig_to_restricted = torch.full(
            (full_vocab_size,), -1, dtype=torch.long
        )
        for restricted_idx, orig_id in enumerate(sorted_ids):
            self._orig_to_restricted[orig_id] = restricted_idx

        # Convenience indices
        self.restricted_pad_idx = self._orig_to_restricted[0].item()
        self.restricted_eos_idx = self._orig_to_restricted[1].item()
        self.restricted_bos_idx = self._orig_to_restricted[32099].item()

    # ── mapping helpers ──────────────────────────────────────────────────

    def remap_targets(self, targets):
        """Map original token IDs → restricted indices.  Unmapped IDs become -1."""
        return self._orig_to_restricted.to(targets.device)[targets]

    def get_prefix_allowed_tokens_fn(self):
        """Return a closure suitable for ``model.generate(prefix_allowed_tokens_fn=...)``."""
        allowed = self.sql_token_ids.tolist()
        return lambda _batch_id, _input_ids: allowed

    # ── device management ────────────────────────────────────────────────

    def to(self, device):
        self.sql_token_ids = self.sql_token_ids.to(device)
        self._orig_to_restricted = self._orig_to_restricted.to(device)
        return self

    # ── verification ─────────────────────────────────────────────────────

    def verify_coverage(self, sql_path):
        """Check that every token in *sql_path* is covered by the restricted vocab.

        Returns a dict with ``total_tokens``, ``covered``, ``missing`` counts,
        and ``missing_examples`` (up to 20 decoded examples).
        """
        missing_ids = set()
        total = 0
        with open(sql_path) as f:
            for line in f:
                ids = self.tokenizer.encode(line.strip(), add_special_tokens=True)
                for tid in ids:
                    total += 1
                    if self._orig_to_restricted[tid].item() == -1:
                        missing_ids.add(tid)

        missing_examples = [
            (tid, self.tokenizer.decode([tid])) for tid in sorted(missing_ids)[:20]
        ]
        return {
            "total_tokens": total,
            "covered": total - len(missing_ids),
            "missing": len(missing_ids),
            "missing_examples": missing_examples,
        }


# ── T5ForFlightSQL ──────────────────────────────────────────────────────────


class T5ForFlightSQL(nn.Module):
    """Wraps ``T5ForConditionalGeneration`` with a restricted SQL output head.

    * ``restricted_forward()`` projects decoder hidden states against only the
      SQL subset of ``shared.weight``, producing logits of shape ``(B, T, V_sql)``
      where ``V_sql ≈ 600`` instead of ``32 128``.
    * ``generate()`` delegates to the inner HF model with
      ``prefix_allowed_tokens_fn`` for constrained beam search.
    * ``state_dict`` / ``load_state_dict`` delegate to the inner model so
      checkpoints are fully compatible with vanilla ``T5ForConditionalGeneration``.
    """

    def __init__(self, base_model, vocab):
        super().__init__()
        self.model = base_model
        self.vocab = vocab
        self.model_dim = base_model.model_dim
        self.config = base_model.config
        self.register_buffer("sql_token_ids", vocab.sql_token_ids.clone())

    # ── restricted forward (training) ────────────────────────────────────

    def restricted_forward(self, input_ids, attention_mask, decoder_input_ids):
        """Encoder → decoder → subset projection.  Returns logits ``(B, T, V_sql)``."""
        encoder_outputs = self.model.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        decoder_outputs = self.model.decoder(
            input_ids=decoder_input_ids,
            encoder_hidden_states=encoder_outputs[0],
            encoder_attention_mask=attention_mask,
        )
        hidden = decoder_outputs[0]  # (B, T, d_model)

        # Replicate T5's pre-lm_head scaling
        if getattr(self.config, "scale_decoder_outputs", False):
            hidden = hidden * (self.model_dim ** -0.5)

        # Subset projection: only the SQL rows of the shared embedding
        sql_embeddings = self.model.shared.weight[self.sql_token_ids]  # (V_sql, d)
        logits = torch.matmul(hidden, sql_embeddings.T)  # (B, T, V_sql)
        return logits

    # ── target remapping ─────────────────────────────────────────────────

    def remap_targets(self, targets):
        return self.vocab.remap_targets(targets)

    def get_restricted_pad_idx(self):
        return self.vocab.restricted_pad_idx

    # ── inference (delegates to inner HF model) ──────────────────────────

    def generate(self, **kwargs):
        return self.model.generate(**kwargs)

    # ── checkpoint compatibility ─────────────────────────────────────────
    # Save / load the inner T5 model's state dict directly, so checkpoints
    # are interchangeable with vanilla T5ForConditionalGeneration.

    def state_dict(self, *args, **kwargs):
        state = self.model.state_dict(*args, **kwargs)
        # If model is wrapped with peft (LoRA), clean prefixes and preserve
        # both base weights and LoRA adapter weights so checkpoints are complete.
        cleaned = {}
        needs_clean = any(k.startswith("base_model.model.") for k in state)
        if needs_clean:
            for k, v in state.items():
                if k.startswith("base_model.model."):
                    new_key = k[len("base_model.model."):]
                    # LoRA layers have .base_layer. in the key -- flatten to original
                    new_key = new_key.replace(".base_layer.", ".")
                elif k.startswith("base_model."):
                    new_key = k[len("base_model."):]
                else:
                    new_key = k
                cleaned[new_key] = v
            return cleaned
        return state

    def load_state_dict(self, state_dict, *args, **kwargs):
        # If the inner model is peft-wrapped, re-add the base_model.model. prefix
        # and restore .base_layer. for non-LoRA keys so peft can load them.
        is_peft = any(k.startswith("base_model.model.") for k in self.model.state_dict())
        has_lora_keys = any(".lora_A." in k or ".lora_B." in k for k in state_dict)
        if is_peft and not any(k.startswith("base_model.model.") for k in state_dict):
            remapped = {}
            for k, v in state_dict.items():
                if ".lora_A." in k or ".lora_B." in k:
                    # LoRA adapter key: base_model.model.<key>
                    remapped[f"base_model.model.{k}"] = v
                else:
                    # Base weight key: check if peft expects .base_layer. inserted
                    peft_key = f"base_model.model.{k}"
                    if peft_key not in self.model.state_dict():
                        # Try inserting .base_layer. before the weight name
                        # e.g. encoder.block.0.layer.0.SelfAttention.q.weight
                        #   -> encoder.block.0.layer.0.SelfAttention.q.base_layer.weight
                        parts = k.rsplit(".", 1)
                        if len(parts) == 2:
                            alt_key = f"base_model.model.{parts[0]}.base_layer.{parts[1]}"
                            if alt_key in self.model.state_dict():
                                remapped[alt_key] = v
                                continue
                    remapped[peft_key] = v
            return self.model.load_state_dict(remapped, *args, **kwargs)
        return self.model.load_state_dict(state_dict, *args, **kwargs)

    # ── delegation ───────────────────────────────────────────────────────

    def parameters(self, recurse=True):
        return self.model.parameters(recurse=recurse)

    def named_parameters(self, prefix="", recurse=True):
        return self.model.named_parameters(prefix=prefix, recurse=recurse)

    def train(self, mode=True):
        self.model.train(mode)
        return self

    def eval(self):
        self.model.eval()
        return self


# ── T5ForFlightSQLWithMLP ─────────────────────────────────────────────────


class T5ForFlightSQLWithMLP(T5ForFlightSQL):
    """Adds a trainable MLP head between decoder hidden states and the
    restricted subset projection.

    Architecture: decoder_output → LayerNorm → Linear(d, mlp_dim) → GELU
                  → Dropout → Linear(mlp_dim, d) → residual add → subset projection

    The MLP gives the model extra capacity to transform decoder representations
    before projecting onto the SQL embedding subspace. The residual connection
    ensures it can degrade gracefully to the base T5ForFlightSQL behavior.
    """

    def __init__(self, base_model, vocab, mlp_dim=1024, mlp_dropout=0.1):
        super().__init__(base_model, vocab)
        d = self.model_dim
        self.mlp_norm = nn.LayerNorm(d)
        self.mlp = nn.Sequential(
            nn.Linear(d, mlp_dim),
            nn.GELU(),
            nn.Dropout(mlp_dropout),
            nn.Linear(mlp_dim, d),
            nn.Dropout(mlp_dropout),
        )
        # Initialize near-zero so residual starts as identity
        nn.init.zeros_(self.mlp[-2].weight)
        nn.init.zeros_(self.mlp[-2].bias)

    def restricted_forward(self, input_ids, attention_mask, decoder_input_ids):
        """Encoder → decoder → MLP → subset projection."""
        encoder_outputs = self.model.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        decoder_outputs = self.model.decoder(
            input_ids=decoder_input_ids,
            encoder_hidden_states=encoder_outputs[0],
            encoder_attention_mask=attention_mask,
        )
        hidden = decoder_outputs[0]  # (B, T, d_model)

        # MLP with residual connection
        hidden = hidden + self.mlp(self.mlp_norm(hidden))

        # Replicate T5's pre-lm_head scaling
        if getattr(self.config, "scale_decoder_outputs", False):
            hidden = hidden * (self.model_dim ** -0.5)

        # Subset projection
        sql_embeddings = self.model.shared.weight[self.sql_token_ids]
        logits = torch.matmul(hidden, sql_embeddings.T)
        return logits

    def state_dict(self, *args, **kwargs):
        # Include both base model and MLP parameters
        state = self.model.state_dict(*args, **kwargs)
        for k, v in self.mlp_norm.state_dict().items():
            state[f"mlp_norm.{k}"] = v
        for k, v in self.mlp.state_dict().items():
            state[f"mlp.{k}"] = v
        return state

    def load_state_dict(self, state_dict, *args, **kwargs):
        mlp_norm_state = {}
        mlp_state = {}
        base_state = {}
        for k, v in state_dict.items():
            if k.startswith("mlp_norm."):
                mlp_norm_state[k[len("mlp_norm."):]] = v
            elif k.startswith("mlp."):
                mlp_state[k[len("mlp."):]] = v
            else:
                base_state[k] = v
        result = self.model.load_state_dict(base_state, *args, **kwargs)
        if mlp_norm_state:
            self.mlp_norm.load_state_dict(mlp_norm_state)
        if mlp_state:
            self.mlp.load_state_dict(mlp_state)
        return result

    def parameters(self, recurse=True):
        import itertools
        return itertools.chain(
            self.model.parameters(recurse=recurse),
            self.mlp_norm.parameters(),
            self.mlp.parameters(),
        )

    def named_parameters(self, prefix="", recurse=True):
        import itertools
        return itertools.chain(
            self.model.named_parameters(prefix=prefix, recurse=recurse),
            self.mlp_norm.named_parameters(prefix=f"{prefix}mlp_norm." if prefix else "mlp_norm.", recurse=recurse),
            self.mlp.named_parameters(prefix=f"{prefix}mlp." if prefix else "mlp.", recurse=recurse),
        )
