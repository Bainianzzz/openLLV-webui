"""Hyperparameter tuning and training components."""

from __future__ import annotations

from collections.abc import Iterator

import gradio as gr

from inference import Status, TrainSlot, config

from . import name_choices

# The training slot: ``run_training`` starts a session on it so
# ``stop_training`` can pause it and a new run is rejected while the current
# one is still in flight.
TRAIN_SLOT = TrainSlot()


def run_training(
    root_dir: str,
    dataset: str,
    model: str,
    epochs: int,
    batch_size: int,
    lr: float,
    resize: int,
    device: str,
    output_dir: str,
    swanlab_api_key: str,
    swanlab_project: str,
) -> Iterator[str]:
    """Start one training session and stream its outcome.

    Training itself runs on a background thread, so the first yield reports
    the start immediately and the second blocks until the session finishes
    (naturally or through the Stop button). ``dataset``, ``root_dir``, and
    ``output_dir`` are recorded with the training record; an empty
    ``output_dir`` keeps openLLV's default checkpoint location. The
    ``swanlab_api_key`` and ``swanlab_project`` are stored on the shared
    config object (overriding the ``config.yaml`` values in memory) so the
    runner picks them up.
    """
    config().set_swanlab_api_key(swanlab_api_key)
    config().set_swanlab_project(swanlab_project)
    worker = TRAIN_SLOT.start(
        model,
        dataset,
        root_dir,
        epochs,
        batch_size,
        lr,
        resize,
        None if device == "auto" else device,
        output_dir or None,
    )
    if worker is None:
        yield "Training is already running."
        return
    outcome = worker.result()
    if worker.status is Status.STOPPED:
        yield "Training stopped."
    elif worker.status is Status.FAILED:
        yield f"Training failed: {worker.error}"
    else:
        yield f"Training finished. Checkpoint: {outcome}"


def stop_training() -> str:
    """Stop the running training session."""
    state = TRAIN_SLOT.pause()
    if state is None:
        return "No training is running."
    if state:
        return "Training stopped."
    return "Training is stopping…"


def build_training_section(models: list) -> dict:
    """Create the training components.

    Hyperparameters can be tuned before starting training; the dataset root
    and name come from the dataset-preparation section and are wired into
    the Train button by ``build_train``.
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
        output_dir = gr.Textbox(
            label="Output Dir",
            placeholder="path/to/checkpoints",
        )
        with gr.Row():
            train_btn = gr.Button("Train", variant="primary")
            stop_btn = gr.Button("Stop", variant="secondary")
        status = gr.Textbox(label="Status", interactive=False)

    return {
        "model": model,
        "epochs": epochs,
        "batch_size": batch_size,
        "lr": lr,
        "resize": resize,
        "device": device,
        "output_dir": output_dir,
        "train_button": train_btn,
        "stop_button": stop_btn,
        "status": status,
    }
