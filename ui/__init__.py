"""UI package for the openLLV Gradio web interface."""

from __future__ import annotations

import gradio as gr

from .enhance import build_enhance
from .train import build_train


def build() -> gr.Blocks:
    """Assemble the full interface from its sections."""
    with gr.Blocks(title="openLLV Image Enhancement") as demo:
        gr.Markdown("# OpenLLV WebUI")
        with gr.Tabs():
            with gr.Tab("Enhance"):
                build_enhance()
            with gr.Tab("Train"):
                build_train()

    return demo


__all__ = ["build"]
