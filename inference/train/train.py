"""Shared training core run from the web UI."""

from __future__ import annotations

import ctypes
import threading

from .run import run

_lock = threading.Lock()
_train_thread: threading.Thread | None = None
_train_status: str | None = None
_interrupted_thread: threading.Thread | None = None

# How long ``pause`` waits for an interrupted run to unwind before reporting
# back. The injected ``KeyboardInterrupt`` lands at the next bytecode
# boundary, so the run usually stops within a training step; a bounded wait
# keeps the UI event handler responsive even when the interrupt lands slowly.
_STOP_WAIT_SECONDS = 20.0


def start(
    model: str,
    dataset: str,
    root_dir: str,
    epochs: int,
    batch_size: int,
    lr: float,
    resize: int,
    device: str | None,
    output_dir: str | None,
) -> str:
    """Start one openLLV training session and return a short status message.

    Training runs on a background daemon thread so the web UI keeps
    responding; the running thread is stored module-wide so that ``pause()``
    can stop it. A ``None`` device lets openLLV pick the best available
    device and a ``None`` ``output_dir`` keeps its default checkpoint
    location. A ``TrainingTask`` row is inserted when the run starts (status
    ``running``) and updated with the outcome when it finishes. Whether the
    session is recorded in SwanLab is decided by ``config().swanlab_api_key``
    inside the runner.
    """
    global _train_thread, _train_status
    with _lock:
        if _train_thread is not None and _train_thread.is_alive():
            return "Training is already running."
        _train_status = None
        _train_thread = threading.Thread(
            target=_run,
            args=(
                model,
                dataset,
                root_dir,
                epochs,
                batch_size,
                lr,
                resize,
                device,
                output_dir,
            ),
            name="openllv-train",
            daemon=True,
        )
        _train_thread.start()
    return "Training started."


def pause() -> str:
    """Stop the running training session and return a status message.

    A Python thread cannot be killed, so the running thread is interrupted
    with a ``KeyboardInterrupt`` that unwinds the blocking ``llv.train()``
    call. The wait for the run to unwind is bounded; if it has not stopped
    in time, a status message is returned instead of blocking the caller
    forever. Repeated calls on the same run do not inject a second
    ``KeyboardInterrupt`` into the already-interrupted thread.
    """
    global _interrupted_thread
    thread = _train_thread
    if thread is None or not thread.is_alive():
        _interrupted_thread = None
        return "No training is running."
    if thread is not _interrupted_thread:
        if not _raise_keyboard_interrupt(thread):
            return "Training could not be stopped."
        _interrupted_thread = thread
    thread.join(timeout=_STOP_WAIT_SECONDS)
    if thread.is_alive():
        return "Training is stopping…"
    return "Training stopped."


def result() -> str:
    """Wait for the running session to finish and return its outcome."""
    thread = _train_thread
    if thread is not None:
        thread.join()
    with _lock:
        return _train_status or "No training has been started."


def _run(
    model: str,
    dataset: str,
    root_dir: str,
    epochs: int,
    batch_size: int,
    lr: float,
    resize: int,
    device: str | None,
    output_dir: str | None,
) -> None:
    """Execute one training session and publish its final status message.

    Runs as the daemon thread started by ``start()``: delegates the session
    to ``run.run()``, then records the outcome in the module-wide status so
    ``result()`` can report it, keeping the thread cleared for the next run.
    """
    global _train_thread, _train_status
    try:
        message = run(
            model,
            dataset,
            root_dir,
            epochs,
            batch_size,
            lr,
            resize,
            device,
            output_dir,
        )
    finally:
        with _lock:
            _train_thread = None
    with _lock:
        _train_status = message


def _raise_keyboard_interrupt(thread: threading.Thread) -> bool:
    """Raise ``KeyboardInterrupt`` inside ``thread``.

    Returns whether the interrupt was delivered. Injecting the exception at
    the next bytecode boundary is the only portable way to unwind a blocking
    call such as ``llv.train()`` from another thread.
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


__all__ = ["pause", "result", "start"]
