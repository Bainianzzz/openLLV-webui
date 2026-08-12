"""Enhancement service: run enhancement tasks and query their records."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from PIL import Image

from inference.utils import config
from inference.utils.threads import BackgroundWorker

from .records import list_records
from .run import _enhance


def start(
    worker: BackgroundWorker[Image.Image | str] | None,
    method: str,
    source: str | Path,
    task_cls: Literal["traditional", "deepLearning"],
    model_path: str | None = None,
    params: Mapping[str, Any] = {},
    output_dir: str | Path | None = None,
) -> BackgroundWorker[Image.Image | str] | None:
    """Start one enhancement run on the given worker slot.

    ``worker`` is the slot's current worker (``None`` when idle): when it is
    still running the start is rejected and ``None`` is returned; otherwise a
    new daemon worker is started and returned for the caller to store back
    into the slot. ``source`` is an image file for a single run or a folder
    for a batch run; ``output_dir`` selects where the output goes (``None``
    keeps ``config().output_dir``). A task row is inserted when the run
    starts (status ``pending``) and updated with the outcome when it
    finishes (``success``/``failed``/``stopped``).
    """
    if worker is not None and worker.is_alive():
        return None
    worker = BackgroundWorker(
        _enhance,
        method,
        source,
        task_cls,
        model_path,
        params,
        output_dir or config().output_dir,
        name="openllv-enhance",
    )
    worker.start()
    return worker


def pause(worker: BackgroundWorker[Image.Image | str] | None) -> bool | None:
    """Stop the run on ``worker``; ``None`` idle, ``True`` stopped, ``False`` stopping."""
    if worker is None or not worker.is_alive():
        return None
    return worker.stop()


def result(
    worker: BackgroundWorker[Image.Image | str] | None,
) -> Image.Image | str | None:
    """Wait for the run on ``worker`` to finish and return its outcome.

    A single run returns the enhanced PIL image, a batch run returns the
    output folder path; ``None`` means the run did not finish successfully.
    """
    if worker is not None:
        worker.join()
    return worker.outcome if worker is not None else None


__all__ = ["list_records", "pause", "result", "start"]
