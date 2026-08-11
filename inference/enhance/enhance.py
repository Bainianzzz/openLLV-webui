"""Shared per-image enhancement core used by single and batch enhance."""

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import openLLV as llv
from PIL import Image

from .. import SessionLocal
from ..model import DeepLearningTask, TraditionalTask
from ..utils import save_image, to_pil


def _enhance(
    method: str,
    image: Image.Image | None,
    task_cls: Literal["traditional", "deepLearning"],
    model_path: str | None,
    params: Mapping[str, Any],
    input_dir: Path,
    output_dir: Path,
) -> Image.Image:
    """Run one enhancement, recording the run and saving under the given dirs."""
    if image is None:
        raise ValueError("Please upload an image first.")

    task_model = TraditionalTask if task_cls == "traditional" else DeepLearningTask
    record = {
        "method": method or model_path,
        "input_path": save_image(image, input_dir),
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
    path: Path,
    input_dir: Path,
    output_dir: Path,
    task_cls: Literal["traditional", "deepLearning"],
    model_path: str | None,
    params: Mapping[str, Any],
) -> Image.Image:
    """Load one batch image and run the shared enhancement core."""
    image = to_pil(Image.open(path))
    return _enhance(method, image, task_cls, model_path, params, input_dir, output_dir)
