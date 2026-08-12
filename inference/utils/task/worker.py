"""Background task worker: run a callable on a daemon thread and stop it on demand."""

from __future__ import annotations

import ctypes
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import Any, Generic, TypeVar

# How long ``Worker.stop`` waits for an interrupted run to unwind
# before reporting back. The injected ``KeyboardInterrupt`` lands at the next
# bytecode boundary, so the run usually stops within a step; a bounded wait
# keeps the UI event handler responsive even when the interrupt lands slowly.
STOP_WAIT_SECONDS = 20.0

T = TypeVar("T")


class Status(str, Enum):
    """The lifecycle state of a task run, mirrored in the database ``status`` column."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    STOPPED = "stopped"


class Cancelled(Exception):
    """A cooperative runner stopped because its cancel event was set."""


class Worker(threading.Thread, ABC, Generic[T]):
    """Run a blocking callable on a daemon thread and stop it on demand.

    A :class:`Slot` owns a worker and implements the run lifecycle —
    ``start`` launches a new run, ``pause`` stops the running call,
    ``result`` waits for it and returns its outcome — while this base class
    owns the shared thread mechanics. The runner is invoked with the
    arguments passed to
    ``__init__``; its return value is published as :attr:`outcome`, and how
    the run ended is published as :attr:`status` (with :attr:`error` holding
    the exception that ended a failed run), so the caller can ``join()`` (or
    ``stop()``) and inspect how the run ended. A cooperative runner is handed
    :attr:`cancel_event` and unwinds on its own; a blocking runner (such as
    ``llv.predict()``/``llv.train()``) needs ``stop()`` to inject a
    ``KeyboardInterrupt`` — the only portable way to unwind it from another
    thread. ``stop()`` waits up to ``STOP_WAIT_SECONDS`` for the run to
    unwind, so a hung call can never block its caller forever. The thread is
    a daemon, so a stuck run never prevents the process from exiting.
    """

    #: Cooperative runners check :attr:`cancel_event` and unwind on their own;
    #: blocking runners additionally need a ``KeyboardInterrupt`` injection.
    cooperative: bool = False

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
        self._cancel_event = threading.Event()
        self._interrupted = False
        self._status = Status.RUNNING
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
            if self.cooperative:
                outcome = self._runner(
                    *self._args, cancel=self._cancel_event, **self._kwargs
                )
            else:
                outcome = self._runner(*self._args, **self._kwargs)
        except (KeyboardInterrupt, Cancelled):
            with self._lock:
                self._status = Status.STOPPED
        except BaseException as exc:  # noqa: BLE001 - any runner failure is published
            with self._lock:
                self._status = Status.FAILED
                self._error = exc
        else:
            with self._lock:
                self._status = Status.SUCCESS
                self._outcome = outcome

    def stop(self, timeout: float = STOP_WAIT_SECONDS) -> bool:
        """Request the running call to stop and wait up to ``timeout`` seconds.

        A cooperative runner is signalled via :attr:`cancel_event`; a blocking
        runner additionally has a ``KeyboardInterrupt`` injected into it.
        Returns ``True`` when the worker finished (the run unwound or
        completed on its own); returns ``False`` when the run is still
        unwinding after the wait. Repeated calls on the same run do not
        inject a second ``KeyboardInterrupt``.
        """
        self._cancel_event.set()
        if not self.is_alive():
            return True
        if not self.cooperative and not self._interrupted:
            if not _raise_keyboard_interrupt(self):
                return False
            self._interrupted = True
        self.join(timeout=timeout)
        return not self.is_alive()

    @property
    def status(self) -> Status:
        """The lifecycle state of this run (``RUNNING``/``SUCCESS``/``FAILED``/``STOPPED``)."""
        with self._lock:
            return self._status

    @property
    def outcome(self) -> T | None:
        """The runner's return value, or ``None`` when it did not finish successfully."""
        with self._lock:
            return self._outcome

    @property
    def error(self) -> BaseException | None:
        """The exception that ended the run, or ``None`` when it did not fail."""
        with self._lock:
            return self._error

    @property
    def cancel_event(self) -> threading.Event:
        """The event a cooperative runner checks to stop at its next boundary."""
        return self._cancel_event


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


__all__ = ["Cancelled", "Status", "Worker"]
