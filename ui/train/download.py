"""Hugging Face dataset download components."""

from __future__ import annotations

import gradio as gr

from inference import DownloadCancelled, config, download_dataset, stop_download


def run_download(dataset: str, local_path: str) -> tuple[str, str]:
    """Download the selected dataset and report its local path.

    ``local_path`` is the current selection value, kept unchanged on failure.
    """
    try:
        path = download_dataset(config().managed_datasets[dataset])
    except DownloadCancelled:
        return "Download stopped", local_path
    except Exception as exc:  # noqa: BLE001 - report any download failure in the status box
        return f"Download failed: {exc}", local_path
    return f"Downloaded to {path}", path


def run_stop() -> str:
    """Signal the in-flight download to stop."""
    stop_download()
    return "Stopping download…"


def build_download_section() -> dict:
    """Create the managed-dataset download components."""
    choices = sorted(config().managed_datasets)

    dataset = gr.Dropdown(choices=choices, value=choices[0], label="Dataset")
    with gr.Row():
        download_btn = gr.Button("Download", variant="primary")
        stop_btn = gr.Button("Stop")
    status = gr.Textbox(label="Status", interactive=False)

    return {
        "dataset": dataset,
        "download_button": download_btn,
        "stop_button": stop_btn,
        "status": status,
    }
