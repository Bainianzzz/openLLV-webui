"""Image utilities for the inference package."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def save_image(image: Image.Image, directory: Path) -> str:
    """Save a PIL image with a timestamped filename and return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now(timezone.utc):%Y%m%d_%H%M%S_%f}.png"
    path = directory / filename
    image.save(path)
    return str(path)


def to_pil(result: Any) -> Image.Image:
    """Convert a numpy array or PIL image to a PIL RGB image for Gradio."""
    if isinstance(result, Image.Image):
        return result.convert("RGB")
    if isinstance(result, np.ndarray):
        return Image.fromarray(result).convert("RGB")
    raise TypeError("Unexpected enhancement output type")
