"""Generic bounded thread pool with per-task timeout supervision."""

from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Callable
from concurrent.futures import Future
from typing import Any

logger = logging.getLogger(__name__)

_Task = tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any], float | None, Future]


class TaskPool:
    """Execute tasks on a fixed set of workers with a bounded queue and timeout.

    - At most ``queue_size`` tasks wait in the queue; ``submit`` blocks while
      the queue is full, so pending work stays bounded.
    - Each task runs under a timeout (per-task, or ``default_timeout``). When a
      task exceeds the limit, the pool logs the failure and abandons it, so a
      hung task can never block a worker or its caller forever.
    - The timeout counts execution time only, not time spent queued.

    Workers are daemon threads, so a stuck task never prevents the process
    from exiting.
    """

    def __init__(
        self,
        max_workers: int = 4,
        queue_size: int = 10,
        default_timeout: float | None = None,
        name: str = "TaskPool",
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        if queue_size < 1:
            raise ValueError("queue_size must be at least 1")
        self._queue: queue.Queue[_Task | None] = queue.Queue(maxsize=queue_size)
        self._default_timeout = default_timeout
        self._lock = threading.Lock()
        self._stopped = False
        self._workers = [
            threading.Thread(target=self._worker, name=f"{name}-{i}", daemon=True)
            for i in range(max_workers)
        ]
        for worker in self._workers:
            worker.start()

    def submit(
        self,
        fn: Callable[..., Any],
        /,
        *args: Any,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Future:
        """Queue ``fn(*args, **kwargs)`` and return a ``Future`` for its result.

        Blocks while more than ``queue_size`` tasks are already waiting.
        """
        with self._lock:
            if self._stopped:
                raise RuntimeError("TaskPool is stopped")
        future: Future = Future()
        self._queue.put((fn, args, kwargs, timeout, future))
        return future

    def execute(
        self,
        fn: Callable[..., Any],
        /,
        *args: Any,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Any:
        """Submit ``fn(*args, **kwargs)`` and wait for its result."""
        return self.submit(fn, *args, timeout=timeout, **kwargs).result()

    def stop(self, wait: bool = True) -> None:
        """Stop accepting tasks and shut the workers down."""
        with self._lock:
            if self._stopped:
                return
            self._stopped = True
        for _ in self._workers:
            self._queue.put(None)
        if wait:
            for worker in self._workers:
                worker.join()

    def _worker(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                return
            fn, args, kwargs, timeout, future = item
            self._supervise(fn, args, kwargs, timeout, future)

    def _supervise(
        self,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        timeout: float | None,
        future: Future,
    ) -> None:
        runner = threading.Thread(
            target=self._invoke, args=(fn, args, kwargs, future), daemon=True
        )
        runner.start()
        limit = self._default_timeout if timeout is None else timeout
        runner.join(limit)
        if runner.is_alive():
            # A running thread cannot be killed; report the failure and stop
            # awaiting it so the worker (and the caller) never deadlock.
            message = (
                f"Task {getattr(fn, '__name__', fn)!r} timed out after "
                f"{limit}s and was stopped"
            )
            logger.error(message)
            if not future.done():
                future.set_exception(TimeoutError(message))

    @staticmethod
    def _invoke(
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        future: Future,
    ) -> None:
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - must forward any task error to its future
            if not future.done():
                future.set_exception(exc)
            return
        if not future.done():
            future.set_result(result)


__all__ = ["TaskPool"]
