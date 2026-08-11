"""Shared per-image enhancement core used by single and batch enhance."""

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import openLLV as llv
from PIL import Image

from inference import SessionLocal
from inference.model import DeepLearningTask, TraditionalTask
from inference.utils import save_image, to_pil


def _enhance(
    method: str,
    image: Image.Image,
    task_cls: Literal["traditional", "deepLearning"],
    model_path: str | None,
    params: Mapping[str, Any],
    input_dir: str,
    output_dir: Path,
) -> Image.Image:
    """Run one enhancement, recording the run and saving the output.

    ``input_dir`` is the source image's path, recorded as-is in the database;
    the input image itself is never copied. The output is saved directly
    under ``output_dir``.
    """
    task_model = TraditionalTask if task_cls == "traditional" else DeepLearningTask
    record = {
        "method": method or model_path,
        "input_path": input_dir,
    }
    if task_model is TraditionalTask:
        record["params"] = dict(params)
    else:
        record["model_path"] = model_path

    with SessionLocal() as session:
        task = task_model(**record)
        session.add(task)
        session.commit()
        task_id = task.id

    try:
        enhanced, _ = llv.predict(method or model_path, image, save=False, **params)
    except Exception as exc:
        with SessionLocal() as session:
            task = session.get(task_model, task_id)
            if task is None:
                raise RuntimeError(f"Task {task_id} not found") from exc
            task.status = "failed"
            task.error = str(exc)
            task.finish_at = datetime.now(timezone.utc)
            session.commit()
        raise ValueError(f"Enhancement failed: {exc}") from exc

    output = to_pil(enhanced)
    with SessionLocal() as session:
        task = session.get(task_model, task_id)
        if task is None:
            raise RuntimeError(f"Task {task_id} not found")
        task.status = "success"
        task.output_path = save_image(output, output_dir)
        task.finish_at = datetime.now(timezone.utc)
        session.commit()

    return output


def _batch_enhance(
    method: str,
    input_dir: Path,
    output_dir: Path,
    task_cls: Literal["traditional", "deepLearning"],
    model_path: str | None,
    params: Mapping[str, Any],
) -> Image.Image:
    """Load one batch image and run the shared enhancement core.

    The source file path is recorded as ``input_path``.
    """
    image = to_pil(Image.open(input_dir))
    return _enhance(
        method, image, task_cls, model_path, params, str(input_dir), output_dir
    )
