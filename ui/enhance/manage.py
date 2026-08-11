"""Manage view: browse enhancement records stored in the database."""

from __future__ import annotations

import gradio as gr

from inference.enhance import list_records
from ui.components import build_table, render_table

TASK_TYPES = ["traditional", "deepLearning"]

TRADITIONAL_COLUMNS = [
    "id",
    "status",
    "method",
    "params",
    "created_at",
    "finish_at",
    "input_path",
    "output_path",
    "error",
]

DEEP_LEARNING_COLUMNS = [
    "id",
    "status",
    "method",
    "model_path",
    "created_at",
    "finish_at",
    "input_path",
    "output_path",
    "error",
]


def _records(task_type: str) -> str:
    """Render the record table HTML for one task type."""
    headers = (
        TRADITIONAL_COLUMNS if task_type == "traditional" else DEEP_LEARNING_COLUMNS
    )
    return render_table(list_records(task_type), headers)


def _reset() -> tuple[str, str]:
    """Restore the task-type dropdown and reload the records."""
    return "traditional", _records("traditional")


def build_manage_section() -> dict:
    """Create the enhancement-record browsing components."""
    with gr.Row():
        task_type = gr.Dropdown(
            choices=TASK_TYPES,
            value="traditional",
            label="Task Type",
        )
        with gr.Column():
            reset_btn = gr.Button("Reset", variant="secondary")
            refresh_btn = gr.Button("Refresh", variant="primary")

    records = build_table(list_records("traditional"), TRADITIONAL_COLUMNS)

    reset_btn.click(
        fn=_reset,
        outputs=[task_type, records],
    )

    refresh_btn.click(
        fn=_records,
        inputs=task_type,
        outputs=records,
    )

    return {
        "task_type": task_type,
        "reset_button": reset_btn,
        "refresh_button": refresh_btn,
        "records": records,
    }
