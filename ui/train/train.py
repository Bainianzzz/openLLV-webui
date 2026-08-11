"""Hyperparameter tuning and training components."""

from __future__ import annotations

from collections.abc import Iterator

import gradio as gr

from inference import pause, result, start

from . import name_choices


def _run_training(
    root_dir: str,
    model: str,
    epochs: int,
    batch_size: int,
    lr: float,
    resize: int,
    device: str,
) -> Iterator[str]:
    """Start one training session and stream its outcome.

    Training itself runs on a background thread, so the first yield reports
    the start immediately and the second blocks until the session finishes
    (naturally or through the Stop button).
    """
    yield start(
        model,
        root_dir,
        epochs,
        batch_size,
        lr,
        resize,
        None if device == "auto" else device,
    )
    yield result()


def _stop_training() -> str:
    """Stop the running training session."""
    return pause()


def build_training_section(root_dir: gr.Textbox, models: list) -> dict:
    """Create the training components.

    ``root_dir`` is the dataset root picked in the dataset-preparation
    section; hyperparameters can be tuned before starting training.
    """
    choices = name_choices(models)

    with gr.Column():
        model = gr.Dropdown(choices=choices, value=choices[0], label="Model")
        epochs = gr.Number(value=10, label="Epochs", precision=0, minimum=1)
        batch_size = gr.Number(value=4, label="Batch Size", precision=0, minimum=1)
        lr = gr.Number(value=1e-4, label="Learning Rate")
        resize = gr.Number(value=512, label="Resize", precision=0, minimum=1)
        device = gr.Dropdown(
            choices=["auto", "cuda", "cpu", "mps"],
            value="auto",
            label="Device",
        )
        with gr.Row():
            train_btn = gr.Button("Train", variant="primary")
            stop_btn = gr.Button("Stop", variant="stop")
        status = gr.Textbox(label="Status", interactive=False)

    train_btn.click(
        fn=_run_training,
        inputs=[root_dir, model, epochs, batch_size, lr, resize, device],
        outputs=[status],
    )
    stop_btn.click(fn=_stop_training, outputs=[status])

    return {
        "model": model,
        "epochs": epochs,
        "batch_size": batch_size,
        "lr": lr,
        "resize": resize,
        "device": device,
        "train_button": train_btn,
        "stop_button": stop_btn,
        "status": status,
    }
