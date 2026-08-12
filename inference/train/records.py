"""Read-side queries for training task records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from inference import SessionLocal
from inference.model import TrainingTask

_SEARCH_FIELDS = ("model", "status", "dataset", "error")


def _fmt(value: datetime | None) -> str:
    """Format a datetime column for display."""
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def list_records(
    search: str = "",
    search_field: str = "model",
    limit: int = 50,
) -> list[list]:
    """Return the most recent ``limit`` training records matching ``search``.

    ``search`` matches the column picked by ``search_field`` (default
    "model"), case-insensitively.
    """
    stmt = select(TrainingTask).order_by(TrainingTask.id.desc())
    if search:
        if search_field not in _SEARCH_FIELDS:
            raise ValueError(
                f"Unknown search field: {search_field!r}; expected one of {_SEARCH_FIELDS}"
            )
        stmt = stmt.where(getattr(TrainingTask, search_field).like(f"%{search}%"))
    stmt = stmt.limit(limit)

    rows: list[list] = []
    with SessionLocal() as session:
        for task in session.scalars(stmt):
            rows.append(
                [
                    task.id,
                    task.status,
                    task.model,
                    task.epochs,
                    task.batch_size,
                    task.lr,
                    task.resize,
                    task.device,
                    task.dataset,
                    task.dataset_path,
                    task.checkpoint_dir or "",
                    _fmt(task.created_at),
                    _fmt(task.finish_at),
                    task.error or "",
                ]
            )
    return rows
