"""Value head for PPO in T5 encoder-decoder RL training.

Predicts expected reward for a given NL query by mean-pooling
the encoder hidden states and passing through a small MLP.
Used as the learned baseline in PPO advantage estimation:
  A = R - V(query)
"""

import torch
import torch.nn as nn


class T5ValueHead(nn.Module):
    """MLP value head on mean-pooled T5 encoder hidden states.

    Architecture: mean_pool(encoder_out) -> Linear(d, h) -> ReLU -> Linear(h, 1)

    Args:
        d_model: T5 encoder hidden dimension (512 for T5-small, 768 for T5-base)
        hidden_dim: MLP hidden layer size
    """

    def __init__(self, d_model: int = 768, hidden_dim: int = 512):
        super().__init__()
        self.head = nn.Sequential(
            nn.Linear(d_model, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )
        # Zero-init output layer so V(s) ≈ 0 at start (rewards are in [-1, 1])
        nn.init.zeros_(self.head[-1].weight)
        nn.init.zeros_(self.head[-1].bias)

    def forward(self, encoder_hidden_states: torch.Tensor,
                attention_mask: torch.Tensor) -> torch.Tensor:
        """Predict expected reward from encoder hidden states.

        Args:
            encoder_hidden_states: (B, T, d_model) from T5 encoder
            attention_mask: (B, T) binary mask for valid tokens

        Returns:
            values: (B,) predicted values
        """
        mask = attention_mask.unsqueeze(-1).float()  # (B, T, 1)
        pooled = (encoder_hidden_states * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        return self.head(pooled).squeeze(-1)  # (B,)
