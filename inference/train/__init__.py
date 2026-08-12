"""Training service: dataset download, model training, and record queries."""

from __future__ import annotations

from inference.utils.threads import BackgroundWorker

from .download import pause as pause_download
from .download import result as result_download
from .download import start as start_download
from .records import list_records
from .run import _train


def start(
    worker: BackgroundWorker[str] | None,
    model: str,
    dataset: str,
    root_dir: str,
    epochs: int,
    batch_size: int,
    lr: float,
    resize: int,
    device: str | None,
    output_dir: str | None,
) -> BackgroundWorker[str] | None:
    """Start one openLLV training session on the given worker slot.

    ``worker`` is the slot's current worker (``None`` when idle): when it is
    still running the start is rejected and ``None`` is returned; otherwise a
    new daemon worker is started and returned for the caller to store back
    into the slot. A ``None`` device lets openLLV pick the best available
    device and a ``None`` ``output_dir`` keeps its default checkpoint
    location. A ``TrainingTask`` row is inserted when the run starts (status
    ``running``) and updated with the outcome when it finishes. Whether the
    session is recorded in SwanLab is decided by ``config().swanlab_api_key``
    inside the runner.
    """
    if worker is not None and worker.is_alive():
        return None
    worker = BackgroundWorker(
        _train,
        model,
        dataset,
        root_dir,
        epochs,
        batch_size,
        lr,
        resize,
        device,
        output_dir,
        name="openllv-train",
    )
    worker.start()
    return worker


def pause(worker: BackgroundWorker[str] | None) -> bool | None:
    """Stop the run on ``worker``; ``None`` idle, ``True`` stopped, ``False`` stopping."""
    if worker is None or not worker.is_alive():
        return None
    return worker.stop()


def result(worker: BackgroundWorker[str] | None) -> str | None:
    """Wait for the run on ``worker`` to finish and return its checkpoint dir."""
    if worker is not None:
        worker.join()
    return worker.outcome if worker is not None else None


__all__ = [
    "list_records",
    "pause",
    "pause_download",
    "result",
    "result_download",
    "start",
    "start_download",
]
