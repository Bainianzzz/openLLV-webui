"""Traditional-algorithm enhancement components for the web UI."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import gradio as gr

from inference import BackgroundWorker, config, result_enhance, start_enhance

from . import (
    WORKER_SLOTS,
    _make_stop_enhance,
    example_images,
    image_display,
    method_choices,
)


def parse_params(text: str | None) -> dict[str, Any]:
    """Parse a JSON object from the textarea into a parameter dict."""
    if not text or not text.strip():
        return {}
    try:
        params = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Parameters are not valid JSON: {exc.msg}") from exc
    return params


def _status(worker: BackgroundWorker | None, batch: bool) -> str:
    """Derive the status text of a finished run in this panel."""
    if worker is None:
        return "No enhancement has been started."
    if worker.outcome is not None:
        return f"Enhanced to {worker.outcome}" if batch else "Enhancement finished."
    if worker.cancelled:
        return "Enhancement stopped."
    if worker.error is not None:
        return f"Enhancement failed: {worker.error}"
    return "No enhancement has been started."


def _sync_batch_button(value: str | None) -> dict:
    """Return a button update enabled only when an input folder is provided."""
    return gr.update(interactive=bool(value and value.strip()))


def run_single_enhance(
    method: str,
    image: str | None,
    params: str,
) -> Iterator[tuple[str, Any]]:
    """Start one enhancement run and stream its status and result image."""
    if image is None:
        yield "Please upload an image first.", gr.update()
        return
    worker = start_enhance(
        WORKER_SLOTS["traditional_single"],
        method,
        image,
        "traditional",
        params=parse_params(params),
    )
    if worker is None:
        yield "Enhancement is already running.", gr.update()
        return
    WORKER_SLOTS["traditional_single"] = worker
    outcome = result_enhance(worker)
    yield (
        _status(worker, batch=False),
        (outcome if outcome is not None else gr.update()),
    )


def run_batch(
    method: str,
    params: str,
    input_dir: str,
    output_dir: str,
) -> Iterator[str]:
    """Start a batch run and stream its status."""
    if not Path(input_dir).is_dir():
        yield f"Input folder does not exist: {input_dir}"
        return
    worker = start_enhance(
        WORKER_SLOTS["traditional_batch"],
        method,
        input_dir,
        "traditional",
        params=parse_params(params),
        output_dir=output_dir,
    )
    if worker is None:
        yield "Enhancement is already running."
        return
    WORKER_SLOTS["traditional_batch"] = worker
    result_enhance(worker)
    yield _status(worker, batch=True)


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

            with gr.Row():
                enhance_btn = gr.Button("Enhance", variant="primary")
                stop_btn = gr.Button("Stop", variant="secondary")
            status = gr.Textbox(label="Status", interactive=False)

            enhance_btn.click(
                fn=run_single_enhance,
                inputs=[method, image, params],
                outputs=[status, output],
            )
            stop_btn.click(
                fn=_make_stop_enhance("traditional_single"),
                outputs=[status],
            )
            single = {
                "method": method,
                "params": params,
                "image": image,
                "output": output,
                "status": status,
                "enhance_button": enhance_btn,
                "stop_button": stop_btn,
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
                        value=str(config().output_dir),
                        label="Output Folder",
                    )

            with gr.Row():
                batch_btn = gr.Button(
                    "Batch Enhance", variant="primary", interactive=False
                )
                batch_stop_btn = gr.Button("Stop", variant="secondary")
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
                fn=run_batch,
                inputs=[
                    batch_method,
                    batch_params,
                    input_dir,
                    output_dir,
                ],
                outputs=[status],
            )
            batch_stop_btn.click(
                fn=_make_stop_enhance("traditional_batch"),
                outputs=[status],
            )
            batch = {
                "method": batch_method,
                "params": batch_params,
                "input_dir": input_dir,
                "output_dir": output_dir,
                "batch_button": batch_btn,
                "stop_button": batch_stop_btn,
                "status": status,
            }

    return {"single": single, "batch": batch}
