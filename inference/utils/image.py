"""Image utilities for the inference package."""

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def save_image(
    image: Image.Image, directory: Path, image_name: str | None = None
) -> str:
    """Save a PIL image under a ``YYYY-MM-DD`` subfolder and return its path.

    The file is named ``<unix-nanosecond-timestamp>-<image_name>`` so
    concurrent saves never collide. ``image_name`` defaults to ``image.png``.
    """
    now = datetime.now(timezone.utc)
    date_dir = directory / now.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{time.time_ns()}-{image_name or 'image.png'}"
    path = date_dir / filename
    image.save(path)
    return str(path)


def to_pil(result: Any) -> Image.Image:
    """Convert a numpy array or PIL image to a PIL RGB image for Gradio."""
    if isinstance(result, Image.Image):
        return result.convert("RGB")
    if isinstance(result, np.ndarray):
        return Image.fromarray(result).convert("RGB")
    raise TypeError("Unexpected enhancement output type")
