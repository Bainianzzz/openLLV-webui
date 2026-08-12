"""Shared enhancement core used by single-image and folder runs."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

import openLLV as llv
from PIL import Image

from inference.model import DeepLearningTask, TraditionalTask
from inference.utils import save_image, to_pil
from inference.utils.task import Status, TaskStorage


def _enhance(
    method: str,
    source: str | Path,
    task_cls: Literal["traditional", "deepLearning"],
    model_path: str | None,
    params: Mapping[str, Any],
    output_dir: str | Path,
) -> Image.Image | str:
    """Run one enhancement, recording the run and saving the output.

    ``source`` is an image file (single run, returns the enhanced PIL image)
    or a folder (batch run, processed by ``llv.predict``, returns the output
    folder path). The source path is recorded as-is in ``input_path``.
    Output goes under ``output_dir``: a single image is saved with a
    timestamped name, a folder keeps openLLV's own layout.
    """
    source = Path(source)
    output_dir = Path(output_dir)
    task_model = TraditionalTask if task_cls == "traditional" else DeepLearningTask
    record: dict[str, Any] = {
        "method": method or model_path,
        "input_path": str(source),
    }
    if task_model is TraditionalTask:
        record["params"] = dict(params)
    else:
        record["model_path"] = model_path

    store = TaskStorage(task_model)
    store.begin(**record)

    result: Image.Image | str
    output_path: str
    try:
        if source.is_dir():
            result = str(
                llv.predict(
                    method or model_path,
                    source,
                    output=output_dir,
                    progress_bar=False,
                    **params,
                )
            )
            output_path = result
        else:
            enhanced, _ = llv.predict(
                method or model_path, source, save=False, **params
            )
            result = to_pil(enhanced)
            output_path = save_image(result, output_dir, image_name=source.name)
    except KeyboardInterrupt:
        store.finish(Status.STOPPED)
        raise
    except Exception as exc:
        store.finish(Status.FAILED, error=str(exc))
        raise

    store.finish(Status.SUCCESS, output_path=output_path)
    return result


__all__ = ["_enhance"]
