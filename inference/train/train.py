"""Shared training core run from the web UI."""

from __future__ import annotations

import ctypes
import threading

import openLLV as llv

_lock = threading.Lock()
_train_thread: threading.Thread | None = None
_train_status: str | None = None


def start(
    model: str,
    root_dir: str,
    epochs: int,
    batch_size: int,
    lr: float,
    resize: int,
    device: str | None,
) -> str:
    """Start one openLLV training session and return a short status message.

    Training runs on a background daemon thread so the web UI keeps
    responding; the running thread is stored module-wide so that ``pause()``
    can stop it. A ``None`` device lets openLLV pick the best available
    device.
    """
    global _train_thread, _train_status
    with _lock:
        if _train_thread is not None and _train_thread.is_alive():
            return "Training is already running."
        _train_status = None
        _train_thread = threading.Thread(
            target=_run,
            args=(model, root_dir, epochs, batch_size, lr, resize, device),
            name="openllv-train",
            daemon=True,
        )
        _train_thread.start()
    return "Training started."


def pause() -> str:
    """Stop the running training session and return a status message.

    A Python thread cannot be killed, so the running thread is interrupted
    with a ``KeyboardInterrupt`` that unwinds the blocking ``llv.train()``
    call.
    """
    thread = _train_thread
    if thread is None or not thread.is_alive():
        return "No training is running."
    if not _raise_keyboard_interrupt(thread):
        return "Training could not be stopped."
    thread.join()
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
    root_dir: str,
    epochs: int,
    batch_size: int,
    lr: float,
    resize: int,
    device: str | None,
) -> None:
    global _train_thread, _train_status
    try:
        outcome = llv.train(
            model,
            root_dir=root_dir,
            epochs=epochs,
            batch_size=batch_size,
            lr=lr,
            resize=resize,
            device=device,
        )
    except KeyboardInterrupt:
        with _lock:
            _train_status = "Training stopped."
    except Exception as exc:  # noqa: BLE001 - any trainer failure becomes a status message
        with _lock:
            _train_status = f"Training failed: {exc}"
    else:
        with _lock:
            _train_status = (
                f"Training finished. Checkpoint: {outcome['checkpoint_dir']}"
            )
    finally:
        with _lock:
            _train_thread = None


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
