"""Part 1 model: T5 fine-tune initialization, save, and load."""

import copy
import os
import torch
from transformers import T5ForConditionalGeneration, T5Config

DEFAULT_CHECKPOINT = "google-t5/t5-small"


def initialize_model(finetune=True, model_checkpoint=DEFAULT_CHECKPOINT, dropout=0.0,
                     freeze_encoder=False, freeze_embeddings=False,
                     unfreeze_last_n_decoder=None, device="cuda"):
    """
    Load T5-small for fine-tuning (pretrained weights) or from scratch (random init).
    Optionally freeze encoder, embeddings, or all but last N decoder layers.
    """
    if finetune:
        model = T5ForConditionalGeneration.from_pretrained(model_checkpoint)
        if dropout > 0.0:
            model.config.dropout_rate = dropout
    else:
        config = T5Config.from_pretrained(model_checkpoint)
        if dropout > 0.0:
            config.dropout_rate = dropout
        model = T5ForConditionalGeneration(config)

    if freeze_embeddings:
        model.shared.requires_grad_(False)

    if freeze_encoder:
        model.encoder.requires_grad_(False)

    if unfreeze_last_n_decoder is not None:
        model.decoder.requires_grad_(False)
        for layer in model.decoder.block[-unfreeze_last_n_decoder:]:
            layer.requires_grad_(True)
        model.decoder.final_layer_norm.requires_grad_(True)

    return model.to(device)


def _get_inner_model(model):
    """Get the inner HF model, unwrapping T5ForFlightSQL if present."""
    # Avoid importing T5ForFlightSQL at module level to prevent circular imports.
    from part1.model_flightdb import T5ForFlightSQL
    if isinstance(model, T5ForFlightSQL):
        return model.model
    return model


def _is_peft_model(inner):
    """Check if the inner model is wrapped with peft (LoRA)."""
    return hasattr(inner, 'merge_and_unload')


def save_model(checkpoint_dir, model, best=False,
               best_filename="model_best.pt", last_filename="model_last.pt"):
    """Save model state_dict to checkpoint_dir.

    For LoRA (peft) models: deep-copies the inner model, calls merge_and_unload()
    on the copy to merge adapter weights into base weights, then saves the
    resulting vanilla T5 state_dict. The original model is not modified, so
    training can continue with LoRA adapters intact.
    """
    os.makedirs(checkpoint_dir, exist_ok=True)
    filename = best_filename if best else last_filename
    path = os.path.join(checkpoint_dir, filename)

    inner = _get_inner_model(model)
    if _is_peft_model(inner):
        # Deep-copy the peft model, merge adapters into base weights, save
        inner_copy = copy.deepcopy(inner)
        merged = inner_copy.merge_and_unload()
        torch.save(merged.state_dict(), path)
        del inner_copy, merged
    else:
        torch.save(model.state_dict(), path)


def save_training_state(checkpoint_dir, model, optimizer, scheduler,
                        epoch, best_val, epochs_since_improvement):
    """Save full training state for resuming."""
    os.makedirs(checkpoint_dir, exist_ok=True)
    state = {
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict() if scheduler is not None else None,
        "epoch": epoch,
        "best_val": best_val,
        "epochs_since_improvement": epochs_since_improvement,
    }
    torch.save(state, os.path.join(checkpoint_dir, "training_state.pt"))


def load_training_state(checkpoint_dir, model, optimizer, scheduler, device="cuda"):
    """Load full training state. Returns (epoch, best_val, epochs_since_improvement)."""
    path = os.path.join(checkpoint_dir, "training_state.pt")
    state = torch.load(path, map_location=device, weights_only=False)
    model.load_state_dict(state["model"])
    optimizer.load_state_dict(state["optimizer"])
    if scheduler is not None and state["scheduler"] is not None:
        scheduler.load_state_dict(state["scheduler"])
    return (state["epoch"], state["best_val"], state["epochs_since_improvement"])


def load_model_from_checkpoint(checkpoint_dir, finetune=True, model_checkpoint=DEFAULT_CHECKPOINT,
                               dropout=0.0, best=True, device="cuda",
                               best_filename="model_best.pt", last_filename="model_last.pt"):
    """Load model from a saved checkpoint."""
    filename = best_filename if best else last_filename
    path = os.path.join(checkpoint_dir, filename)

    model = initialize_model(finetune=finetune, model_checkpoint=model_checkpoint,
                             dropout=dropout, device=device)
    model.load_state_dict(torch.load(path, map_location=device, weights_only=True))
    return model
