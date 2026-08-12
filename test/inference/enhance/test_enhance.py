"""Tests for ``inference.enhance``."""

from pathlib import Path
from shutil import copyfile
from unittest import mock

import numpy as np
import openLLV as llv
import pytest
from PIL import Image

from inference.enhance import batch_enhance, enhance
from test.mock import TEST_IMAGE, mock_db


@pytest.fixture(autouse=True)
def db_session():
    """Mock the database session for every test in this module."""
    with mock_db() as session:
        yield session


def test_enhance_deep_learning(db_session) -> None:
    """A deep-learning run is recorded with all its database fields."""
    predicted = np.full((4, 5, 3), 255, dtype=np.uint8)

    with mock.patch.object(llv, "predict", return_value=(predicted, None)) as predict:
        result = enhance(
            "ZeroDCE",
            TEST_IMAGE,
            "deepLearning",
            model_path="models/zero_dce.pt",
        )

    predict.assert_called_once_with("ZeroDCE", mock.ANY, save=False)
    assert isinstance(result, Image.Image)
    assert result.mode == "RGB"
    assert db_session.task.id == 1
    assert db_session.task.method == "ZeroDCE"
    assert db_session.task.model_path == "models/zero_dce.pt"
    assert db_session.task.input_path == TEST_IMAGE
    assert db_session.task.output_path.endswith(".png")
    assert db_session.task.status == "success"
    assert db_session.task.error is None
    assert db_session.task.finish_at is not None


def test_enhance_traditional(db_session) -> None:
    """A traditional-algorithm run stores its parameters."""
    predicted = np.full((4, 5, 3), 255, dtype=np.uint8)

    with mock.patch.object(llv, "predict", return_value=(predicted, None)):
        enhance("Gamma", TEST_IMAGE, "traditional", params={"gamma": 0.6})

    assert db_session.task.method == "Gamma"
    assert db_session.task.params == {"gamma": 0.6}
    assert db_session.task.input_path == TEST_IMAGE
    assert db_session.task.status == "success"
    assert db_session.task.finish_at is not None


def test_enhance_failure_records_error(db_session) -> None:
    """A failed run is recorded with its error message."""
    with (
        pytest.raises(ValueError, match="Enhancement failed"),
        mock.patch.object(llv, "predict", side_effect=RuntimeError("boom")),
    ):
        enhance("SomeMethod", TEST_IMAGE, "deepLearning")

    assert db_session.task.status == "failed"
    assert db_session.task.error == "boom"
    assert db_session.task.finish_at is not None


def test_batch_enhance_records_one_run(db_session, tmp_path: Path) -> None:
    """A batch run records one task with the input/output folders."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    for i in range(5):
        copyfile(TEST_IMAGE, input_dir / f"img{i}.png")

    with mock.patch.object(llv, "predict", return_value=str(output_dir)) as predict:
        output = batch_enhance(
            "Gamma",
            input_dir,
            output_dir,
            "traditional",
            params={"gamma": 0.6},
        )

    predict.assert_called_once_with(
        "Gamma",
        input_dir,
        output=output_dir,
        progress_bar=False,
        gamma=0.6,
    )
    assert output == str(output_dir)
    assert len(db_session.tasks) == 1
    task = db_session.task
    assert task.status == "success"
    assert task.input_path == str(input_dir)
    assert task.output_path == str(output_dir)
    assert task.params == {"gamma": 0.6}
    assert task.finish_at is not None


def test_batch_enhance_failure_records_error(db_session, tmp_path: Path) -> None:
    """A failed batch run is recorded with its error message."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    copyfile(TEST_IMAGE, input_dir / "img0.png")

    with (
        pytest.raises(ValueError, match="Enhancement failed"),
        mock.patch.object(llv, "predict", side_effect=RuntimeError("boom")),
    ):
        batch_enhance("Gamma", input_dir, output_dir, "traditional")

    assert db_session.task.status == "failed"
    assert db_session.task.error == "boom"
    assert db_session.task.input_path == str(input_dir)
    assert db_session.task.output_path is None
    assert db_session.task.finish_at is not None
