"""Manage view: browse training records stored in the database."""

from __future__ import annotations

import gradio as gr

from inference import list_train_records
from ui.components import build_table, render_table

SEARCH_FIELDS = ["model", "status", "dataset", "error"]

COLUMNS = [
    "id",
    "status",
    "model",
    "epochs",
    "batch_size",
    "lr",
    "resize",
    "device",
    "dataset",
    "dataset_path",
    "checkpoint_dir",
    "created_at",
    "finish_at",
    "error",
]


def _records(search_field: str, search: str = "") -> str:
    """Render the record table HTML for the current search."""
    return render_table(
        list_train_records(search=search, search_field=search_field),
        COLUMNS,
    )


def _reset() -> tuple[str, str, str]:
    """Clear the search and reload records."""
    return "model", "", _records("model")


def build_manage_section() -> dict:
    """Create the training-record browsing components."""
    with gr.Row():
        search_field = gr.Dropdown(
            choices=SEARCH_FIELDS,
            value="model",
            label="Search Field",
        )
        search_box = gr.Textbox(
            label="Search",
            placeholder="search term",
        )
    with gr.Row():
        reset_btn = gr.Button("Reset", variant="secondary")
        refresh_btn = gr.Button("Refresh", variant="primary")

    records = build_table(list_train_records(), COLUMNS)

    reset_btn.click(
        fn=_reset,
        outputs=[search_field, search_box, records],
    )

    search_box.submit(
        fn=_records,
        inputs=[search_field, search_box],
        outputs=records,
    )

    refresh_btn.click(
        fn=_records,
        inputs=[search_field, search_box],
        outputs=records,
    )

    return {
        "search_field": search_field,
        "search_box": search_box,
        "reset_button": reset_btn,
        "refresh_button": refresh_btn,
        "records": records,
    }
