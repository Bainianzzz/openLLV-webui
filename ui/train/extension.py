"""Extension components: optional SwanLab experiment recording."""

from __future__ import annotations

import gradio as gr

from inference import config


def build_extension_section() -> dict:
    """Create the extension components (SwanLab API key).

    When the key is filled in, training runs through
    ``BatchSwanLabTrainer`` and the session is recorded in SwanLab. The box
    is pre-filled with the ``config.yaml`` value so a configured key shows up
    without re-entering it.
    """
    with gr.Column():
        gr.Markdown("## SwanLab")
        api_key = gr.Textbox(
            label="API Key",
            type="password",
            value=config().swanlab_api_key or "",
        )

    return {"api_key": api_key}


__all__ = ["build_extension_section"]
