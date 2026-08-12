"""Enhancement service: run enhancement tasks and query their records."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from PIL import Image

from inference.utils import config

from .enhance import _enhance
from .records import list_records


def enhance(
    method: str,
    image: str | None,
    task_cls: Literal["traditional", "deepLearning"],
    model_path: str | None = None,
    params: Mapping[str, Any] = {},
) -> Image.Image:
    """Enhance one image through the method selected in the web UI.

    ``image`` is the uploaded image's file path: it is opened for inference
    and recorded as ``input_path`` without copying the file. ``task_cls``
    selects the table the run is recorded into. A row is inserted when the run
    starts (status ``pending``) and updated with the result when it finishes
    (``success``/``failed``).
    """
    if image is None:
        raise ValueError("Please upload an image first.")
    result = _enhance(method, image, task_cls, model_path, params, config().output_dir)
    if not isinstance(result, Image.Image):
        raise TypeError("Single-image enhancement did not return an image")
    return result


def batch_enhance(
    method: str,
    input_dir: str | Path,
    output_dir: str | Path,
    task_cls: Literal["traditional", "deepLearning"],
    model_path: str | None = None,
    params: Mapping[str, Any] = {},
) -> str:
    """Enhance every image under ``input_dir`` with a single folder prediction.

    Delegates to the shared ``_enhance`` with the folder as the source; one
    task row records the run with the input/output folders. Returns the
    output folder path.
    """
    result = _enhance(method, input_dir, task_cls, model_path, params, output_dir)
    if not isinstance(result, str):
        raise TypeError("Folder prediction did not return the output folder")
    return result


__all__ = ["batch_enhance", "enhance", "list_records"]
