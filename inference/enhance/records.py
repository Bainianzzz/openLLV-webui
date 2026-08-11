"""Read-side queries for enhancement task records."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select

_SEARCH_FIELDS = ("method", "status", "input_path", "output_path", "error")

from .. import SessionLocal
from ..model import DeepLearningTask, TraditionalTask


def _fmt(value: datetime | None) -> str:
    """Format a datetime column for display."""
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def list_records(
    task_type: str = "traditional",
    search: str = "",
    search_field: str = "method",
    limit: int = 50,
) -> list[list]:
    """Return the most recent ``limit`` records matching ``search``.

    ``task_type`` selects the table ("traditional"/"deepLearning"); any
    other value raises ``ValueError``. ``search`` matches the column picked
    by ``search_field`` (default "method"), case-insensitively. The
    type-specific field (``params``/``model_path``) sits at index 3 so the
    UI can align it with its own column headers.
    """
    if task_type == "traditional":
        model = TraditionalTask
    elif task_type == "deepLearning":
        model = DeepLearningTask
    else:
        raise ValueError(
            f"Unknown task type: {task_type!r}; expected 'traditional' or 'deepLearning'"
        )

    stmt = select(model).order_by(model.id.desc())
    if search:
        if search_field not in _SEARCH_FIELDS:
            raise ValueError(
                f"Unknown search field: {search_field!r}; expected one of {_SEARCH_FIELDS}"
            )
        stmt = stmt.where(getattr(model, search_field).like(f"%{search}%"))
    stmt = stmt.limit(limit)

    rows: list[list] = []
    with SessionLocal() as session:
        for task in session.scalars(stmt):
            if isinstance(task, TraditionalTask):
                extra = json.dumps(task.params, ensure_ascii=False)
            else:
                extra = task.model_path or ""
            rows.append(
                [
                    task.id,
                    task.status,
                    task.method,
                    extra,
                    _fmt(task.created_at),
                    _fmt(task.finish_at),
                    task.input_path,
                    task.output_path or "",
                    task.error or "",
                ]
            )
    return rows
