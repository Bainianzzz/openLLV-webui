"""Manage view: browse enhancement records stored in the database."""

from __future__ import annotations

import gradio as gr

from inference import list_records
from ui.components import build_table, render_table

TASK_TYPES = ["traditional", "deepLearning"]

SEARCH_FIELDS = ["method", "status", "input_path", "output_path", "error"]

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


def _records(task_type: str, search_field: str, search: str = "") -> str:
    """Render the record table HTML for one task type."""
    headers = (
        TRADITIONAL_COLUMNS if task_type == "traditional" else DEEP_LEARNING_COLUMNS
    )
    return render_table(
        list_records(task_type, search=search, search_field=search_field),
        headers,
    )


def _reset() -> tuple[str, str, str, str]:
    """Restore task type, search field, clear the search and reload records."""
    return "traditional", "method", "", _records("traditional", "method")


def build_manage_section() -> dict:
    """Create the enhancement-record browsing components."""
    with gr.Row():
        task_type = gr.Dropdown(
            choices=TASK_TYPES,
            value="traditional",
            label="Task Type",
        )
        search_field = gr.Dropdown(
            choices=SEARCH_FIELDS,
            value="method",
            label="Search Field",
        )
        search_box = gr.Textbox(
            label="Search",
            placeholder="search term",
        )
    with gr.Row():
        reset_btn = gr.Button("Reset", variant="secondary")
        refresh_btn = gr.Button("Refresh", variant="primary")

    records = build_table(list_records("traditional"), TRADITIONAL_COLUMNS)

    reset_btn.click(
        fn=_reset,
        outputs=[task_type, search_field, search_box, records],
    )

    search_box.submit(
        fn=_records,
        inputs=[task_type, search_field, search_box],
        outputs=records,
    )

    refresh_btn.click(
        fn=_records,
        inputs=[task_type, search_field, search_box],
        outputs=records,
    )

    return {
        "task_type": task_type,
        "search_field": search_field,
        "search_box": search_box,
        "reset_button": reset_btn,
        "refresh_button": refresh_btn,
        "records": records,
    }
