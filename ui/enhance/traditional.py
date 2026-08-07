"""Traditional-algorithm enhancement components for the web UI."""

from __future__ import annotations

import gradio as gr

from inference.enhance import enhance, parse_params

from . import example_images, image_display, method_choices


def build_traditional_section(enhancers: dict) -> dict:
    """Create the traditional-algorithm enhancement components."""
    algorithm_choices = method_choices(enhancers["algorithms"])
    image, output = image_display()
    with gr.Row():
        method = gr.Dropdown(
            choices=algorithm_choices,
            value="Gamma",
            label="Method",
        )
        gr.Examples(examples=example_images(), inputs=image, label=".e.g")

    params = gr.Textbox(
        label="Main Parameters (JSON)",
        lines=5,
        placeholder="{\n\tgamma=0.6\n}",
    )

    enhance_btn = gr.Button("Enhance", variant="primary")

    enhance_btn.click(
        fn=lambda method, image, params: enhance(
            method, image, params=parse_params(params)
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
