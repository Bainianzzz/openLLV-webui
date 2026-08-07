"""UI package for the openLLV Gradio web interface."""

from __future__ import annotations

import gradio as gr

from .enhance import build_enhance


def build() -> gr.Blocks:
    """Assemble the full interface from its sections."""
    with gr.Blocks(title="openLLV Image Enhancement") as demo:
        gr.Markdown("# OpenLLV WebUI")
        build_enhance()

    return demo


__all__ = ["build"]
