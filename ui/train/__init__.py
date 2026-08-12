"""Training UI package: dataset download, selection, training, and records."""

from __future__ import annotations

import gradio as gr
import openLLV as llv


def name_choices(rows) -> list[str]:
    """Turn ``llv.list_available()`` rows into Gradio dropdown choices."""
    return sorted(row["name"] for row in rows)


def build_train() -> dict:
    """Assemble the training page as tabs.

    The "Train" tab holds the dataset config (download and selection) and the
    hyperparameters; the "Records" tab browses stored training records.
    Training consumes the dataset root picked on the left.
    """
    from .dataset import build_dataset_section
    from .download import build_download_section, run_download, run_stop
    from .manage import build_manage_section
    from .train import build_training_section

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
                training = build_training_section(
                    dataset["root_dir"], dataset["dataset"], available["models"]
                )
        with gr.Tab("Records"):
            manage = build_manage_section()

    download["download_button"].click(
        fn=run_download,
        inputs=[download["dataset"], dataset["root_dir"]],
        outputs=[download["status"], dataset["root_dir"]],
    )
    download["stop_button"].click(
        fn=run_stop,
        outputs=[download["status"]],
    )

    return {
        "download": download,
        "dataset": dataset,
        "train": training,
        "manage": manage,
    }


__all__ = ["build_train"]
