"""Enhancement service: run enhancement tasks and query their records."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from PIL import Image

from inference import INPUT_DIR, OUTPUT_DIR
from inference.utils import TaskPool

from .enhance import _batch_enhance, _enhance
from .records import list_records

_IMAGE_SUFFIXES = frozenset({".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"})


def enhance(
    method: str,
    image: Image.Image | None,
    task_cls: Literal["traditional", "deepLearning"],
    model_path: str | None = None,
    params: Mapping[str, Any] = {},
) -> Image.Image:
    """Enhance one image through the method selected in the web UI.

    ``task_cls`` selects the table the run is recorded into. A row is inserted
    when the run starts (status ``pending``) and updated with the result
    when it finishes (``success``/``failed``).
    """
    return _enhance(method, image, task_cls, model_path, params, INPUT_DIR, OUTPUT_DIR)


def batch_enhance(
    method: str,
    input_dir: str | Path,
    output_dir: str | Path,
    task_cls: Literal["traditional", "deepLearning"],
    model_path: str | None = None,
    params: Mapping[str, Any] = {},
    max_workers: int = 4,
    queue_size: int = 10,
) -> int:
    """Enhance every image under ``input_dir`` through a per-run thread pool.

    One enhancement task is created per image and submitted to a ``TaskPool``
    created for this run; each run is recorded and saved under ``input_dir`` /
    ``output_dir`` just like ``enhance``. Returns the number of images
    submitted.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    images = sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in _IMAGE_SUFFIXES
    )
    pool = TaskPool(
        max_workers=max_workers, queue_size=queue_size, name="batch-enhance"
    )
    try:
        futures = [
            pool.submit(
                _batch_enhance,
                method,
                path,
                input_dir,
                output_dir,
                task_cls,
                model_path=model_path,
                params=params,
            )
            for path in images
        ]
        for future in futures:
            future.result()
    finally:
        pool.stop()
    return len(futures)


__all__ = ["batch_enhance", "enhance", "list_records"]
