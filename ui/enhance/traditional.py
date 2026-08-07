"""Traditional-algorithm enhancement components for the web UI."""

from __future__ import annotations

import json
from typing import Any

import gradio as gr

from inference.enhance import enhance

from . import example_images, image_display, method_choices


def parse_params(text: str | None) -> dict[str, Any]:
    """Parse a JSON object from the textarea into a parameter dict."""
    if not text or not text.strip():
        return {}
    try:
        params = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Parameters are not valid JSON: {exc.msg}") from exc
    return params


def build_traditional_section(algorithms: list) -> dict:
    """Create the traditional-algorithm enhancement components."""
    algorithm_choices = method_choices(algorithms)
    image, output = image_display()
    with gr.Row():
        with gr.Column():
            method = gr.Dropdown(
                choices=algorithm_choices,
                value="Gamma",
                label="Method",
            )
            params = gr.Textbox(
                label="Main Parameters (JSON)",
                lines=5,
                placeholder="{\n\tgamma=0.6\n}",
            )
        gr.Examples(examples=example_images(), inputs=image, label=".e.g")



    enhance_btn = gr.Button("Enhance", variant="primary")

    enhance_btn.click(
        fn=lambda method, image, params: enhance(
            method, image, "traditional", params=parse_params(params)
        ),
        inputs=[method, image, params],
        outputs=[output],
    )

    return {
        "method": method,
        "params": params,
        "image": image,
        "output": output,
        "enhance_button": enhance_btn,
    }
