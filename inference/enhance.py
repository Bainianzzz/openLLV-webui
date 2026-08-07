"""Inference glue between the Gradio UI and openLLV enhancement methods."""

import json
from collections.abc import Mapping
from typing import Any

import numpy as np
import openLLV as llv
from PIL import Image


def available_enhancers() -> dict[str, Any]:
    """Return the enhancement-related groups from ``llv.list_available()``."""
    available = llv.list_available()
    return {
        "algorithms": available["algorithms"],
        "models": available["models"],
    }


def _to_pil(result: Any) -> Image.Image:
    """Convert a numpy array or PIL image to a PIL RGB image for Gradio."""
    if isinstance(result, Image.Image):
        return result.convert("RGB")
    if isinstance(result, np.ndarray):
        return Image.fromarray(result).convert("RGB")
    raise TypeError("Unexpected enhancement output type")


def enhance(
    method: str,
    image: Image.Image | None,
    model_path: str | None = None,
    params: Mapping[str, Any] = {},
) -> Image.Image:
    """Enhance one image through the method selected in the web UI."""
    if image is None:
        raise ValueError("Please upload an image first.")

    try:
        enhanced, _ = llv.predict(method or model_path, image, save=False, **params)
    except Exception as exc:
        raise ValueError(f"Enhancement failed: {exc}") from exc
    return _to_pil(enhanced)


def parse_params(text: str | None) -> dict[str, Any]:
    """Parse a JSON object from the textarea into a parameter dict."""
    if not text or not text.strip():
        return {}
    try:
        params = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Parameters are not valid JSON: {exc.msg}") from exc
    return params
