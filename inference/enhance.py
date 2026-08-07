"""Inference glue between the Gradio UI and openLLV enhancement methods."""

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Literal

import openLLV as llv
from PIL import Image

from . import INPUT_DIR, OUTPUT_DIR, SessionLocal
from .model import DeepLearningTask, TraditionalTask
from .utils import save_image, to_pil


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
    if image is None:
        raise ValueError("Please upload an image first.")

    task_model = TraditionalTask if task_cls == "traditional" else DeepLearningTask
    record = {
        "method": method or model_path,
        "input_path": save_image(image, INPUT_DIR),
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
        task.output_path = save_image(output, OUTPUT_DIR)
        task.finish_at = datetime.now(timezone.utc)
        session.commit()

    return output
