"""Task-lifecycle recorder shared by the background runners."""

from __future__ import annotations

from datetime import datetime, timezone

from inference import SessionLocal

from .worker import Status


class TaskStorage:
    """Record one task row's lifecycle: ``begin`` creates it, ``finish`` updates it.

    The runners delegate their ``SessionLocal`` bookkeeping here so they stay
    pure business logic. ``begin`` inserts the row with status ``running``;
    ``finish`` sets the final status, ``finish_at``, and any outcome fields
    (``output_path``/``checkpoint_dir``) or ``error``.
    """

    def __init__(self, model) -> None:
        self._model = model
        self._task_id: int | None = None

    def begin(self, **fields) -> None:
        """Insert the task row and remember its id for ``finish``."""
        with SessionLocal() as session:
            task = self._model(status=Status.RUNNING.value, **fields)
            session.add(task)
            session.commit()
            self._task_id = task.id

    def finish(self, status: Status, *, error: str | None = None, **fields) -> None:
        """Mark the task as ``status`` and record ``finish_at`` plus any outcome fields."""
        with SessionLocal() as session:
            task = session.get(self._model, self._task_id)
            if task is None:
                return
            task.status = status.value
            task.finish_at = datetime.now(timezone.utc)
            if error is not None:
                task.error = error
            for key, value in fields.items():
                setattr(task, key, value)
            session.commit()


__all__ = ["TaskStorage"]
