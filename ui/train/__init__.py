"""Training UI package: dataset download, selection, training, and records."""

from __future__ import annotations

import gradio as gr
import openLLV as llv

from inference import BackgroundWorker

# One worker slot per background task on this page: dataset download and
# training run independently. Each module stores the worker returned by its
# ``start_*`` function back into its slot.
WORKER_SLOTS: dict[str, BackgroundWorker | None] = {
    "download": None,
    "train": None,
}


def name_choices(rows) -> list[str]:
    """Turn ``llv.list_available()`` rows into Gradio dropdown choices."""
    return sorted(row["name"] for row in rows)


def build_train() -> dict:
    """Assemble the training page as tabs.

    The "Train" tab holds the dataset config (download and selection) and the
    hyperparameters; the "Records" tab browses stored training records; the
    "Extension" tab holds optional SwanLab experiment recording. Training
    consumes the dataset root picked on the left and the SwanLab API key and
    project from the extension tab.
    """
    from .dataset import build_dataset_section
    from .download import build_download_section, run_download, run_stop
    from .extension import build_extension_section
    from .manage import build_manage_section
    from .train import build_training_section, run_training, stop_training

    available = llv.list_available()
    with gr.Tabs():
        with gr.Tab("Train"), gr.Row():
            with gr.Column():
                gr.Markdown("## Dataset Download")
                download = build_download_section()
                gr.Markdown("## Dataset Selection")
                dataset = build_dataset_section(available["datasets"])
            with gr.Column():
                gr.Markdown("## Training")
                training = build_training_section(available["models"])
        with gr.Tab("Records"):
            manage = build_manage_section()
        with gr.Tab("Extension"):
            extension = build_extension_section()

    download["download_button"].click(
        fn=run_download,
        inputs=[download["dataset"], dataset["root_dir"]],
        outputs=[
            download["download_button"],
            download["status"],
            dataset["root_dir"],
        ],
    )
    download["stop_button"].click(
        fn=run_stop,
        outputs=[download["status"]],
    )
    training["train_button"].click(
        fn=run_training,
        inputs=[
            dataset["root_dir"],
            dataset["dataset"],
            training["model"],
            training["epochs"],
            training["batch_size"],
            training["lr"],
            training["resize"],
            training["device"],
            training["output_dir"],
            extension["api_key"],
            extension["project"],
        ],
        outputs=[training["status"]],
    )
    training["stop_button"].click(
        fn=stop_training,
        outputs=[training["status"]],
    )

    return {
        "download": download,
        "dataset": dataset,
        "train": training,
        "manage": manage,
        "extension": extension,
    }


__all__ = ["build_train"]
