"""Tests for ``inference.utils`` image helpers."""

from pathlib import Path
from unittest import mock

import numpy as np
import pytest
from PIL import Image

from inference.utils import save_image, to_pil
from test.mock import TEST_IMAGE


def test_pil_image() -> None:
    result = to_pil(Image.open(TEST_IMAGE))
    assert isinstance(result, Image.Image)
    assert result.mode == "RGB"


def test_numpy_array() -> None:
    result = to_pil(np.zeros((4, 5, 3), dtype=np.uint8))
    assert isinstance(result, Image.Image)
    assert result.mode == "RGB"


def test_unsupported_type() -> None:
    with pytest.raises(TypeError):
        to_pil("not an image")


def test_save_image(tmp_path: Path) -> None:
    """A PIL image is saved with a timestamped name and its path returned."""
    image = Image.open(TEST_IMAGE)
    with mock.patch.object(image, "save") as save_mock:
        path = save_image(image, tmp_path)

    assert path.startswith(str(tmp_path))
    assert path.endswith(".png")
    save_mock.assert_called_once_with(Path(path))
