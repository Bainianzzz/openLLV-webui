"""Tests for ``inference.enhance``."""

from pathlib import Path
from unittest import mock

import numpy as np
import openLLV as llv
import pytest
from PIL import Image

from inference.enhance import batch_enhance, enhance
from test.mock.db import mock_db


def _image() -> Image.Image:
    return Image.fromarray(np.zeros((4, 5, 3), dtype=np.uint8))


@pytest.fixture(autouse=True)
def db_session():
    """Mock the database session for every test in this module."""
    with mock_db() as session:
        yield session


def test_enhance_deep_learning(db_session, tmp_path: Path) -> None:
    """A deep-learning run is recorded with all its database fields."""
    image_path = tmp_path / "input.png"
    _image().save(image_path)
    predicted = np.full((4, 5, 3), 255, dtype=np.uint8)

    with mock.patch.object(llv, "predict", return_value=(predicted, None)) as predict:
        result = enhance(
            "ZeroDCE", str(image_path), "deepLearning", model_path="models/zero_dce.pt"
        )

    predict.assert_called_once_with("ZeroDCE", mock.ANY, save=False)
    assert isinstance(result, Image.Image)
    assert result.mode == "RGB"
    assert db_session.task.id == 1
    assert db_session.task.method == "ZeroDCE"
    assert db_session.task.model_path == "models/zero_dce.pt"
    assert db_session.task.input_path == str(image_path)
    assert db_session.task.output_path.endswith(".png")
    assert db_session.task.status == "success"
    assert db_session.task.error is None
    assert db_session.task.finish_at is not None


def test_enhance_traditional(db_session, tmp_path: Path) -> None:
    """A traditional-algorithm run stores its parameters."""
    image_path = tmp_path / "input.png"
    _image().save(image_path)
    predicted = np.full((4, 5, 3), 255, dtype=np.uint8)

    with mock.patch.object(llv, "predict", return_value=(predicted, None)):
        enhance("Gamma", str(image_path), "traditional", params={"gamma": 0.6})

    assert db_session.task.method == "Gamma"
    assert db_session.task.params == {"gamma": 0.6}
    assert db_session.task.input_path == str(image_path)
    assert db_session.task.status == "success"
    assert db_session.task.finish_at is not None


def test_enhance_failure_records_error(db_session, tmp_path: Path) -> None:
    """A failed run is recorded with its error message."""
    image_path = tmp_path / "input.png"
    _image().save(image_path)

    with (
        pytest.raises(ValueError, match="Enhancement failed"),
        mock.patch.object(llv, "predict", side_effect=RuntimeError("boom")),
    ):
        enhance("SomeMethod", str(image_path), "deepLearning")

    assert db_session.task.status == "failed"
    assert db_session.task.error == "boom"
    assert db_session.task.finish_at is not None


def test_batch_enhance_records_each_image(db_session, tmp_path: Path) -> None:
    """Batch enhancement records every processed image in the mock database."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    for i in range(5):
        Image.fromarray(np.full((4, 5, 3), i * 40, dtype=np.uint8)).save(
            input_dir / f"img{i}.png"
        )

    predicted = np.full((4, 5, 3), 255, dtype=np.uint8)
    with mock.patch.object(llv, "predict", return_value=(predicted, None)):
        count = batch_enhance(
            "Gamma",
            input_dir,
            output_dir,
            "traditional",
            params={"gamma": 0.6},
        )

    assert count == 5
    assert len(db_session.tasks) == 5
