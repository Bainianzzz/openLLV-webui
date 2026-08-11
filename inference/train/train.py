"""Shared training core run from the web UI."""

from __future__ import annotations

import openLLV as llv


def train(
    model: str,
    root_dir: str,
    epochs: int,
    batch_size: int,
    lr: float,
    resize: int,
    device: str | None,
) -> str:
    """Run one openLLV training session and summarize the outcome.

    A ``None`` device lets openLLV pick the best available device.
    """
    result = llv.train(
        model,
        root_dir=root_dir,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        resize=resize,
        device=device,
    )
    return f"Training finished. Checkpoint: {result['checkpoint_dir']}"


__all__ = ["train"]
