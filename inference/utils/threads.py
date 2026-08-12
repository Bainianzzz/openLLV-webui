"""Thread helpers shared by the background web UI task runners."""

from __future__ import annotations

import ctypes
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, TypeVar

# How long ``BackgroundWorker.stop`` waits for an interrupted run to unwind
# before reporting back. The injected ``KeyboardInterrupt`` lands at the next
# bytecode boundary, so the run usually stops within a step; a bounded wait
# keeps the UI event handler responsive even when the interrupt lands slowly.
STOP_WAIT_SECONDS = 20.0

T = TypeVar("T")


class Worker(threading.Thread, ABC, Generic[T]):
    """Run a blocking callable on a daemon thread and stop it on demand.

    A :class:`Slot` owns a worker and implements the run lifecycle —
    ``start`` launches a new run, ``pause`` stops the running call,
    ``result`` waits for it and returns its outcome — while this base class
    owns the shared thread mechanics. The runner is invoked with the
    arguments passed to
    ``__init__``; its return value is published as :attr:`outcome`, and an
    interruption or failure is published as :attr:`cancelled`/:attr:`error`,
    so the caller can ``join()`` (or ``stop()``) and inspect how the run
    ended. ``stop()`` injects a ``KeyboardInterrupt`` into the running call —
    the only portable way to unwind a blocking call such as ``llv.predict()``
    or ``llv.train()`` from another thread — and waits up to
    ``STOP_WAIT_SECONDS`` for the run to unwind, so a hung call can never
    block its caller forever. The thread is a daemon, so a stuck run never
    prevents the process from exiting.
    """

    def __init__(
        self,
        runner: Callable[..., T],
        /,
        *args: Any,
        name: str = "openllv-worker",
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, daemon=True)
        self._runner = runner
        self._args = args
        self._kwargs = kwargs
        self._lock = threading.Lock()
        self._interrupted = False
        self._cancelled = False
        self._error: BaseException | None = None
        self._outcome: T | None = None

    @abstractmethod
    def pause(self) -> bool | None:
        """Stop the run on this worker; ``None`` idle, ``True`` stopped, ``False`` stopping."""

    @abstractmethod
    def result(self) -> T | None:
        """Wait for the run on this worker to finish and return its outcome."""

    def run(self) -> None:
        """Thread body: invoke the runner and publish how the run ended."""
        try:
            outcome = self._runner(*self._args, **self._kwargs)
        except KeyboardInterrupt:
            with self._lock:
                self._cancelled = True
        except BaseException as exc:  # noqa: BLE001 - any runner failure is published
            with self._lock:
                self._error = exc
        else:
            with self._lock:
                self._outcome = outcome

    def stop(self, timeout: float = STOP_WAIT_SECONDS) -> bool:
        """Interrupt the running call and wait up to ``timeout`` seconds.

        Returns ``True`` when the worker finished (the interrupt was
        delivered and the run unwound, or the run completed on its own);
        returns ``False`` when the interrupt could not be delivered or the
        run is still unwinding after the wait. Repeated calls on the same
        run do not inject a second ``KeyboardInterrupt``.
        """
        if not self.is_alive():
            return True
        if not self._interrupted:
            if not _raise_keyboard_interrupt(self):
                return False
            self._interrupted = True
        self.join(timeout=timeout)
        return not self.is_alive()

    @property
    def outcome(self) -> T | None:
        """The runner's return value, or ``None`` when it did not finish."""
        with self._lock:
            return self._outcome

    @property
    def error(self) -> BaseException | None:
        """The exception that ended the run, or ``None`` when it finished."""
        with self._lock:
            return self._error

    @property
    def cancelled(self) -> bool:
        """Whether the run was stopped by a ``KeyboardInterrupt``."""
        with self._lock:
            return self._cancelled

    @property
    def interrupted(self) -> bool:
        """Whether ``stop`` has injected the interrupt into this run."""
        return self._interrupted


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


def _raise_keyboard_interrupt(thread: threading.Thread) -> bool:
    """Raise ``KeyboardInterrupt`` inside ``thread``.

    Returns whether the interrupt was delivered. Injecting the exception at
    the next bytecode boundary is the only portable way to unwind a blocking
    call such as ``llv.predict()``/``llv.train()`` from another thread.
    """
    ident = thread.ident
    if ident is None or not thread.is_alive():
        return False
    injected = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_ulong(ident), ctypes.py_object(KeyboardInterrupt)
    )
    if injected > 1:
        # The exception landed in more than one thread state: undo the injection.
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(ident), None)
        return False
    return injected == 1


__all__ = ["Slot", "Worker"]
