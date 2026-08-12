"""Hugging Face dataset download components."""

from __future__ import annotations

from collections.abc import Iterator

import gradio as gr

from inference import DownloadSlot, config

# The download slot: ``run_download`` starts a download on it so ``run_stop``
# can pause it and a new run is rejected while the current one is in flight.
DOWNLOAD_SLOT = DownloadSlot()


def run_download(dataset: str, local_path: str) -> Iterator[tuple[dict, str, str]]:
    """Download the selected dataset and report its local path.

    The Download button is disabled for the duration of the run: the first
    yield disables it immediately, the last yield restores it with the
    outcome. ``local_path`` is the current selection value, kept unchanged
    on failure.
    """
    yield gr.update(interactive=False), "Downloading…", local_path
    worker = DOWNLOAD_SLOT.start(config().managed_datasets[dataset])
    if worker is None:
        yield gr.update(interactive=True), "Download is already running.", local_path
        return
    outcome = worker.result()
    if outcome is not None:
        yield gr.update(interactive=True), f"Downloaded to {outcome}", outcome
    elif worker.cancelled:
        yield gr.update(interactive=True), "Download stopped", local_path
    else:
        yield (
            gr.update(interactive=True),
            f"Download failed: {worker.error}",
            local_path,
        )


def run_stop() -> str:
    """Stop the in-flight download and report the outcome."""
    state = DOWNLOAD_SLOT.pause()
    if state is None:
        return "No download is running."
    if state:
        return "Download stopped."
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
