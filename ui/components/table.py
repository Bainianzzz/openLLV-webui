"""Display-only HTML table component."""

from __future__ import annotations

import html

import gradio as gr

_TABLE_CSS = """
table.record-table {
    border-collapse: collapse;
    width: 100%;
    font-size: 14px;
}
table.record-table th,
table.record-table td {
    border: 1px solid var(--border-color-primary, #ccc);
    padding: 6px 10px;
    text-align: left;
    white-space: nowrap;
}
table.record-table thead th {
    position: sticky;
    top: 0;
    background: var(--background-fill-primary, #fff);
}
"""


def render_table(rows: list[list], headers: list[str]) -> str:
    """Build an escaped HTML table from display rows and column headers."""
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return (
        '<table class="record-table">'
        f"<thead><tr>{head}</tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table>"
    )


def build_table(rows: list[list], headers: list[str], max_height: int = 480) -> gr.HTML:
    """Create a display-only HTML table component."""
    return gr.HTML(
        value=render_table(rows, headers),
        css_template=_TABLE_CSS,
        max_height=max_height,
    )
