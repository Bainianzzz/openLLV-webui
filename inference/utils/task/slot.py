"""A worker slot owning at most one running task."""

from __future__ import annotations

import threading
from typing import Any, Generic

from .worker import T, Worker


class Slot(Generic[T]):
    """Own one worker slot: ``start`` launches, ``pause``/``result`` control it.

    Encapsulates the slot bookkeeping that callers used to do by hand — keep
    the current worker, reject a ``start`` while it is still running, and
    store the new worker back. Subclasses build their worker in ``_spawn``;
    :meth:`start` guards the slot and starts the returned worker on its
    daemon thread.
    """

    def __init__(self) -> None:
        self._worker: Worker[T] | None = None

    @property
    def worker(self) -> Worker[T] | None:
        """The current worker, or ``None`` when the slot is idle."""
        return self._worker

    def _spawn(self, *args: Any, **kwargs: Any) -> Worker[T]:
        """Build the worker for this slot without starting its thread."""
        raise NotImplementedError

    def start(self, *args: Any, **kwargs: Any) -> Worker[T] | None:
        """Start a new run on this slot.

        Returns the new worker, or ``None`` when the slot is still running
        its current worker and the start is rejected.
        """
        if self._worker is not None and self._worker.is_alive():
            return None
        self._worker = self._spawn(*args, **kwargs)
        threading.Thread.start(self._worker)
        return self._worker

    def pause(self) -> bool | None:
        """Stop the run on this slot; ``None`` idle, ``True`` stopped, ``False`` stopping."""
        return self._worker.pause() if self._worker is not None else None

    def result(self) -> T | None:
        """Wait for the run on this slot to finish and return its outcome."""
        return self._worker.result() if self._worker is not None else None


__all__ = ["Slot"]
