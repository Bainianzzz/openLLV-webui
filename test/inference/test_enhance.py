"""Tests for ``inference.enhance``."""

from unittest import mock

import numpy as np
import openLLV as llv
import pytest
from PIL import Image

from inference.enhance import enhance
from test.mock.db import mock_db


def _image() -> Image.Image:
    return Image.fromarray(np.zeros((4, 5, 3), dtype=np.uint8))


@pytest.fixture(autouse=True)
def db_session():
    """Mock the database session for every test in this module."""
    with mock_db() as session:
        yield session


def test_enhance_deep_learning(db_session) -> None:
    """A deep-learning run is recorded with all its database fields."""
    image = _image()
    predicted = np.full((4, 5, 3), 255, dtype=np.uint8)

    with mock.patch.object(llv, "predict", return_value=(predicted, None)) as predict:
        result = enhance(
            "ZeroDCE", image, "deepLearning", model_path="models/zero_dce.pt"
        )

    predict.assert_called_once_with("ZeroDCE", image, save=False)
    assert isinstance(result, Image.Image)
    assert result.mode == "RGB"
    assert db_session.task.id == 1
    assert db_session.task.method == "ZeroDCE"
    assert db_session.task.model_path == "models/zero_dce.pt"
    assert db_session.task.input_path.endswith(".png")
    assert db_session.task.output_path.endswith(".png")
    assert db_session.task.status == "success"
    assert db_session.task.error is None
    assert db_session.task.finish_at is not None


def test_enhance_traditional(db_session) -> None:
    """A traditional-algorithm run stores its parameters."""
    image = _image()
    predicted = np.full((4, 5, 3), 255, dtype=np.uint8)

    with mock.patch.object(llv, "predict", return_value=(predicted, None)):
        enhance("Gamma", image, "traditional", params={"gamma": 0.6})

    assert db_session.task.method == "Gamma"
    assert db_session.task.params == {"gamma": 0.6}
    assert db_session.task.status == "success"
    assert db_session.task.finish_at is not None


def test_enhance_failure_records_error(db_session) -> None:
    """A failed run is recorded with its error message."""
    image = _image()

    with (
        pytest.raises(ValueError, match="Enhancement failed"),
        mock.patch.object(llv, "predict", side_effect=RuntimeError("boom")),
    ):
        enhance("SomeMethod", image, "deepLearning")

    assert db_session.task.status == "failed"
    assert db_session.task.error == "boom"
    assert db_session.task.finish_at is not None
