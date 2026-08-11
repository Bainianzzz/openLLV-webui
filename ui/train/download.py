"""Hugging Face dataset download components."""

from __future__ import annotations

import gradio as gr

from inference.train import MANAGED_DATASETS, download_dataset


def run_download(dataset: str, local_path: str) -> tuple[str, str]:
    """Download the selected dataset and report its local path.

    ``local_path`` is the current selection value, kept unchanged on failure.
    """
    try:
        path = download_dataset(MANAGED_DATASETS[dataset])
    except Exception as exc:  # noqa: BLE001 - report any download failure in the status box
        return f"Download failed: {exc}", local_path
    return f"Downloaded to {path}", path


def build_download_section() -> dict:
    """Create the managed-dataset download components."""
    choices = sorted(MANAGED_DATASETS)

    dataset = gr.Dropdown(choices=choices, value=choices[0], label="Dataset")
    download_btn = gr.Button("Download", variant="primary")
    status = gr.Textbox(label="Status", interactive=False)

    return {
        "dataset": dataset,
        "download_button": download_btn,
        "status": status,
    }
