"""Hugging Face dataset download components."""

from __future__ import annotations

from collections.abc import Iterator

import gradio as gr

from inference import DownloadCancelled, config, download_dataset, stop_download


def run_download(dataset: str, local_path: str) -> Iterator[tuple[dict, str, str]]:
    """Download the selected dataset and report its local path.

    The Download button is disabled for the duration of the run: the first
    yield disables it immediately, the last yield restores it with the
    outcome. ``local_path`` is the current selection value, kept unchanged
    on failure.
    """
    yield gr.update(interactive=False), "Downloading…", local_path
    try:
        path = download_dataset(config().managed_datasets[dataset])
    except DownloadCancelled:
        yield gr.update(interactive=True), "Download stopped", local_path
        return
    except Exception as exc:  # noqa: BLE001 - report any download failure in the status box
        yield gr.update(interactive=True), f"Download failed: {exc}", local_path
        return
    yield gr.update(interactive=True), f"Downloaded to {path}", path


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
