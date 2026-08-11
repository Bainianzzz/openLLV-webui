"""Tests for ``inference.enhance.records``."""

import json
from datetime import datetime

import pytest

from inference.enhance.records import list_records
from inference.model import DeepLearningTask, TraditionalTask
from test.mock.db import mock_records_db

DEEP_LEARNING_ROW = {
    "id": 2,
    "status": "failed",
    "method": "ZeroDCE",
    "model_path": "models/zero_dce.pt",
    "created_at": "2026-08-11 07:00:00",
    "finish_at": "",
    "input_path": "/data/input/in2.png",
    "output_path": "",
    "error": "boom",
}

TRADITIONAL_ROW = {
    "id": 1,
    "status": "success",
    "method": "Gamma",
    "params": '{"gamma": 0.6}',
    "created_at": "2026-08-11 06:44:38",
    "finish_at": "2026-08-11 06:44:39",
    "input_path": "/data/input/in.png",
    "output_path": "/data/output/out.png",
    "error": "",
}


def _from_display(value: str) -> datetime | None:
    """Rebuild a task timestamp from its displayed string."""
    return datetime.fromisoformat(value) if value else None


def _traditional_task(**overrides) -> TraditionalTask:
    values = {
        "id": TRADITIONAL_ROW["id"],
        "status": TRADITIONAL_ROW["status"],
        "method": TRADITIONAL_ROW["method"],
        "params": json.loads(TRADITIONAL_ROW["params"]),
        "created_at": _from_display(TRADITIONAL_ROW["created_at"]),
        "finish_at": _from_display(TRADITIONAL_ROW["finish_at"]),
        "input_path": TRADITIONAL_ROW["input_path"],
        "output_path": TRADITIONAL_ROW["output_path"] or None,
        "error": TRADITIONAL_ROW["error"] or None,
    }
    values.update(overrides)
    return TraditionalTask(**values)


def _deep_learning_task(**overrides) -> DeepLearningTask:
    values = {
        "id": DEEP_LEARNING_ROW["id"],
        "status": DEEP_LEARNING_ROW["status"],
        "method": DEEP_LEARNING_ROW["method"],
        "model_path": DEEP_LEARNING_ROW["model_path"],
        "created_at": _from_display(DEEP_LEARNING_ROW["created_at"]),
        "finish_at": _from_display(DEEP_LEARNING_ROW["finish_at"]),
        "input_path": DEEP_LEARNING_ROW["input_path"],
        "output_path": DEEP_LEARNING_ROW["output_path"] or None,
        "error": DEEP_LEARNING_ROW["error"] or None,
    }
    values.update(overrides)
    return DeepLearningTask(**values)


def test_list_records_traditional() -> None:
    """Traditional records expose ``params`` as the type-specific column."""
    with mock_records_db([_traditional_task()]):
        result = list_records("traditional")

    assert result == [list(TRADITIONAL_ROW.values())]


def test_list_records_deep_learning() -> None:
    """Deep-learning records expose ``model_path`` as the type-specific column."""
    with mock_records_db([_deep_learning_task()]):
        result = list_records("deepLearning")

    assert result == [list(DEEP_LEARNING_ROW.values())]


def test_list_records_invalid_type() -> None:
    """An unknown type raises ``ValueError``."""
    with pytest.raises(ValueError, match="Unknown task type"):
        list_records("bogus")
