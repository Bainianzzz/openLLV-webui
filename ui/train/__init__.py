"""Training UI package: dataset download, selection, and training."""

from __future__ import annotations

import gradio as gr
import openLLV as llv


def name_choices(rows) -> list[str]:
    """Turn ``llv.list_available()`` rows into Gradio dropdown choices."""
    return sorted(row["name"] for row in rows)


def build_train() -> dict:
    """Assemble the download, selection, and training sections on one page.

    The selection section consumes the local path produced by the download
    section, and training consumes the selected root directory.
    """
    from .dataset import build_dataset_section
    from .download import build_download_section, run_download
    from .train import build_training_section

    available = llv.list_available()
    gr.Markdown("## Dataset Download")
    download = build_download_section()
    gr.Markdown("## Dataset Selection")
    dataset = build_dataset_section(available["datasets"])
    gr.Markdown("## Training")
    training = build_training_section(dataset["root_dir"], available["models"])

    download["download_button"].click(
        fn=run_download,
        inputs=[download["dataset"], dataset["root_dir"]],
        outputs=[download["status"], dataset["root_dir"]],
    )

    return {"download": download, "dataset": dataset, "train": training}


__all__ = ["build_train"]
