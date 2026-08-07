"""Deep-learning model enhancement components for the web UI."""

from __future__ import annotations

import gradio as gr

from inference.enhance import enhance

from . import example_images, image_display, method_choices


def build_deep_learning_section(models: list) -> dict:
    """Create the deep-learning model enhancement components."""
    model_choices = method_choices(models)
    image, output = image_display()
    with gr.Row():
        with gr.Column():
            method = gr.Dropdown(
                choices=model_choices,
                value=model_choices[0],
                label="Method",
            )
            model_file = gr.File(
                type="filepath",
                label="Model Weights (optional, .pt/.pth)",
                file_types=[".pt", ".pth"],
                height=160,
            )
        with gr.Column():
            gr.Examples(examples=example_images(), inputs=image, label=".e.g")

    enhance_btn = gr.Button("Enhance", variant="primary")

    enhance_btn.click(
        fn=lambda method, image, model_file: enhance(
            method, image, "deepLearning", model_path=model_file
        ),
        inputs=[method, image, model_file],
        outputs=[output],
    )

    return {
        "method": method,
        "model_file": model_file,
        "image": image,
        "output": output,
        "enhance_button": enhance_btn,
    }
