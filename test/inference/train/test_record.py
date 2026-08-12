"""Tests for ``inference.train.records``."""

from datetime import datetime

import pytest

from inference.model import TrainingTask
from inference.train.records import list_records
from test.mock.db import mock_train_records_db

ROW = {
    "id": 1,
    "status": "success",
    "model": "ZeroDCE",
    "epochs": 10,
    "batch_size": 4,
    "lr": 1e-4,
    "resize": 512,
    "device": "auto",
    "dataset": "CommonDataset",
    "dataset_path": "/data/datasets/common",
    "checkpoint_dir": "checkpoints/ZeroDCE_CommonDataset",
    "created_at": "2026-08-11 06:44:38",
    "finish_at": "2026-08-11 06:44:39",
    "error": "",
}


def _from_display(value: str) -> datetime | None:
    """Rebuild a task timestamp from its displayed string."""
    return datetime.fromisoformat(value) if value else None


def _task(**overrides) -> TrainingTask:
    values = {
        "id": None,  # auto-incremented by the mock
        "status": ROW["status"],
        "model": ROW["model"],
        "epochs": ROW["epochs"],
        "batch_size": ROW["batch_size"],
        "lr": ROW["lr"],
        "resize": ROW["resize"],
        "device": ROW["device"],
        "dataset": ROW["dataset"],
        "dataset_path": ROW["dataset_path"],
        "checkpoint_dir": ROW["checkpoint_dir"] or None,
        "created_at": _from_display(ROW["created_at"]),
        "finish_at": _from_display(ROW["finish_at"]),
        "error": ROW["error"] or None,
    }
    values.update(overrides)
    return TrainingTask(**values)


def _expected(**overrides) -> list:
    """Build the displayed row for the shared fixture, with overrides."""
    values = dict(ROW)
    values.update(overrides)
    return list(values.values())


def test_list_records_newest_first_and_limited() -> None:
    """Training records are newest-first and limited to the 50 most recent."""
    rows = [_task() for _ in range(60)]
    with mock_train_records_db(rows):
        result = list_records()

    assert len(result) == 50
    assert result[0][0] == 60
    assert result[-1][0] == 11
    assert result[0][2] == "ZeroDCE"


def test_list_records_search() -> None:
    """Search filters by the selected column, defaulting to model."""
    with mock_train_records_db(
        [
            _task(error="boom"),
            _task(model="LIME"),
        ]
    ):
        default_field = list_records(search="LIME")
        error_field = list_records(search="boom", search_field="error")

    assert default_field == [_expected(id=2, model="LIME")]
    assert error_field == [_expected(error="boom")]


def test_list_records_stopped_row() -> None:
    """A stopped run shows no checkpoint and keeps its error message."""
    with mock_train_records_db(
        [_task(status="stopped", checkpoint_dir=None, error="boom", finish_at=None)]
    ):
        result = list_records()

    assert result == [
        _expected(id=1, status="stopped", checkpoint_dir="", error="boom", finish_at="")
    ]


def test_list_records_invalid_search_field() -> None:
    """An unknown search field raises ``ValueError``."""
    with pytest.raises(ValueError, match="Unknown search field"):
        list_records(search="x", search_field="bogus")
