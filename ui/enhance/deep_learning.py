"""Deep-learning model enhancement components for the web UI."""

from __future__ import annotations

from pathlib import Path

import gradio as gr

from inference import batch_enhance, config, enhance

from . import example_images, image_display, method_choices


def _sync_batch_button(value: str | None) -> dict:
    """Return a button update enabled only when an input folder is provided."""
    return gr.update(interactive=bool(value and value.strip()))


def _run_batch(
    method: str,
    model_file: str | None,
    input_dir: str,
    output_dir: str,
) -> str:
    """Run batch enhancement on a folder and report how many images were processed."""
    if not Path(input_dir).is_dir():
        return f"Input folder does not exist: {input_dir}"
    output = batch_enhance(
        method,
        input_dir,
        output_dir,
        "deepLearning",
        model_path=model_file,
    )
    return f"Enhanced to {output}"


def build_deep_learning_section(models: list) -> dict:
    """Create the deep-learning model enhancement components.

    The section holds two tabs: single-image enhancement (unchanged layout)
    and folder batch enhancement.
    """
    model_choices = method_choices(models)

    with gr.Tabs():
        with gr.Tab("Single"):
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
            single = {
                "method": method,
                "model_file": model_file,
                "image": image,
                "output": output,
                "enhance_button": enhance_btn,
            }

        with gr.Tab("Batch"):
            with gr.Row():
                with gr.Column():
                    batch_method = gr.Dropdown(
                        choices=model_choices,
                        value=model_choices[0],
                        label="Method",
                    )
                    batch_model_file = gr.File(
                        type="filepath",
                        label="Model Weights (optional, .pt/.pth)",
                        file_types=[".pt", ".pth"],
                    )
                with gr.Column():
                    input_dir = gr.Textbox(
                        label="Input Folder",
                    )
                    output_dir = gr.Textbox(
                        value=str(config().output_dir),
                        label="Output Folder",
                    )

            batch_btn = gr.Button("Batch Enhance", variant="primary", interactive=False)
            status = gr.Textbox(label="Status", interactive=False)

            input_dir.input(
                fn=_sync_batch_button,
                inputs=[input_dir],
                outputs=[batch_btn],
            )
            input_dir.change(
                fn=_sync_batch_button,
                inputs=[input_dir],
                outputs=[batch_btn],
            )

            batch_btn.click(
                fn=_run_batch,
                inputs=[
                    batch_method,
                    batch_model_file,
                    input_dir,
                    output_dir,
                ],
                outputs=[status],
            )
            batch = {
                "method": batch_method,
                "model_file": batch_model_file,
                "input_dir": input_dir,
                "output_dir": output_dir,
                "batch_button": batch_btn,
                "status": status,
            }

    return {"single": single, "batch": batch}
