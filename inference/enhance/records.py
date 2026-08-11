"""Read-side queries for enhancement task records."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select

from .. import SessionLocal
from ..model import DeepLearningTask, TraditionalTask


def _fmt(value: datetime | None) -> str:
    """Format a datetime column for display."""
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def list_records(task_type: str = "traditional") -> list[list]:
    """Return the display rows for one task type, newest first.

    ``task_type`` selects the table ("traditional"/"deepLearning"); any
    other value raises ``ValueError``. The type-specific field
    (``params``/``model_path``) sits at index 3 so the UI can align it with
    its own column headers.
    """
    if task_type == "traditional":
        model = TraditionalTask
    elif task_type == "deepLearning":
        model = DeepLearningTask
    else:
        raise ValueError(
            f"Unknown task type: {task_type!r}; expected 'traditional' or 'deepLearning'"
        )

    rows: list[list] = []
    with SessionLocal() as session:
        stmt = select(model).order_by(model.id.desc())
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
