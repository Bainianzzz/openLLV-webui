"""Deep-learning model enhancement components for the web UI."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import gradio as gr

from inference import EnhanceSlot, EnhanceWorker, config

from . import example_images, image_display, method_choices

# One slot per entry in this panel: the single and batch tabs run
# independently, each owning its current worker.
SINGLE_SLOT = EnhanceSlot()
BATCH_SLOT = EnhanceSlot()


def _make_stop(slot: EnhanceSlot) -> Callable[[], str]:
    """Return the Stop-button handler for the worker in ``slot``."""

    def stop() -> str:
        state = slot.pause()
        if state is None:
            return "No enhancement is running."
        if state:
            return "Enhancement stopped."
        return "Enhancement is stopping…"

    return stop


def _status(worker: EnhanceWorker | None, batch: bool) -> str:
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
    model_file: str | None,
) -> Iterator[tuple[str, Any]]:
    """Start one enhancement run and stream its status and result image."""
    if image is None:
        yield "Please upload an image first.", gr.update()
        return
    worker = SINGLE_SLOT.start(
        method,
        image,
        "deepLearning",
        model_path=model_file,
    )
    if worker is None:
        yield "Enhancement is already running.", gr.update()
        return
    outcome = worker.result()
    yield (
        _status(worker, batch=False),
        (outcome if outcome is not None else gr.update()),
    )


def run_batch(
    method: str,
    model_file: str | None,
    input_dir: str,
    output_dir: str,
) -> Iterator[str]:
    """Start a batch run and stream its status."""
    if not Path(input_dir).is_dir():
        yield f"Input folder does not exist: {input_dir}"
        return
    worker = BATCH_SLOT.start(
        method,
        input_dir,
        "deepLearning",
        model_path=model_file,
        output_dir=output_dir,
    )
    if worker is None:
        yield "Enhancement is already running."
        return
    worker.result()
    yield _status(worker, batch=True)


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

            with gr.Row():
                enhance_btn = gr.Button("Enhance", variant="primary")
                stop_btn = gr.Button("Stop", variant="secondary")
            status = gr.Textbox(label="Status", interactive=False)

            enhance_btn.click(
                fn=run_single_enhance,
                inputs=[method, image, model_file],
                outputs=[status, output],
            )
            stop_btn.click(
                fn=_make_stop(SINGLE_SLOT),
                outputs=[status],
            )
            single = {
                "method": method,
                "model_file": model_file,
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
                    batch_model_file,
                    input_dir,
                    output_dir,
                ],
                outputs=[status],
            )
            batch_stop_btn.click(
                fn=_make_stop(BATCH_SLOT),
                outputs=[status],
            )
            batch = {
                "method": batch_method,
                "model_file": batch_model_file,
                "input_dir": input_dir,
                "output_dir": output_dir,
                "batch_button": batch_btn,
                "stop_button": batch_stop_btn,
                "status": status,
            }

    return {"single": single, "batch": batch}
