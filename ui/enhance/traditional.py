"""Traditional-algorithm enhancement components for the web UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gradio as gr

from inference import OUTPUT_DIR
from inference.enhance import batch_enhance, enhance

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


def _sync_batch_button(value: str | None) -> dict:
    """Return a button update enabled only when an input folder is provided."""
    return gr.update(interactive=bool(value and value.strip()))


def _run_batch(
    method: str,
    params: str,
    input_dir: str,
    output_dir: str,
    max_workers: int,
    queue_size: int,
) -> str:
    """Run batch enhancement on a folder and report how many images were processed."""
    if not Path(input_dir).is_dir():
        return f"Input folder does not exist: {input_dir}"
    count = batch_enhance(
        method,
        input_dir,
        output_dir,
        "traditional",
        params=parse_params(params),
        max_workers=max_workers,
        queue_size=queue_size,
    )
    return f"Enhanced {count} images"


def build_traditional_section(algorithms: list) -> dict:
    """Create the traditional-algorithm enhancement components.

    The section holds two tabs: single-image enhancement (unchanged layout)
    and folder batch enhancement.
    """
    algorithm_choices = method_choices(algorithms)

    with gr.Tabs():
        with gr.Tab("Single"):
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
            single = {
                "method": method,
                "params": params,
                "image": image,
                "output": output,
                "enhance_button": enhance_btn,
            }

        with gr.Tab("Batch"):
            with gr.Row():
                with gr.Column():
                    batch_method = gr.Dropdown(
                        choices=algorithm_choices,
                        value="Gamma",
                        label="Method",
                    )
                    batch_params = gr.Textbox(
                        label="Main Parameters (JSON)",
                        lines=5,
                        placeholder="{\n\tgamma=0.6\n}",
                    )
                with gr.Column():
                    input_dir = gr.Textbox(
                        label="Input Folder",
                    )
                    output_dir = gr.Textbox(
                        value=str(OUTPUT_DIR),
                        label="Output Folder",
                    )
                    max_workers = gr.Number(
                        value=4,
                        label="Workers",
                        precision=0,
                        minimum=1,
                    )
                    queue_size = gr.Number(
                        value=10,
                        label="Queue Size",
                        precision=0,
                        minimum=1,
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
                    batch_params,
                    input_dir,
                    output_dir,
                    max_workers,
                    queue_size,
                ],
                outputs=[status],
            )
            batch = {
                "method": batch_method,
                "params": batch_params,
                "input_dir": input_dir,
                "output_dir": output_dir,
                "max_workers": max_workers,
                "queue_size": queue_size,
                "batch_button": batch_btn,
                "status": status,
            }

    return {"single": single, "batch": batch}
