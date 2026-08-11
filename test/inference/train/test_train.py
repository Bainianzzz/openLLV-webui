"""Tests for the ``inference.train`` training lifecycle recording."""

import threading
import time
from unittest import mock

import openLLV as llv
import pytest

import inference.train.train as train_module
from inference.train.train import pause, result, start
from test.mock import mock_train_db

TRAIN_ARGS = ("ZeroDCE", "CommonDataset", "/data/datasets/common", 10, 4, 1e-4, 512)


@pytest.fixture(autouse=True)
def db_session():
    """Mock the database session for every test in this module."""
    with mock_train_db() as session:
        yield session


@pytest.fixture(autouse=True)
def reset_train_state():
    """Clear the module-wide training state after each test."""
    yield
    thread = train_module._train_thread
    if thread is not None and thread.is_alive():
        train_module._raise_keyboard_interrupt(thread)
        thread.join(timeout=5)
    train_module._train_thread = None
    train_module._train_status = None


def _start(device: str | None = None) -> str:
    """Start training with the shared fixture arguments."""
    return start(*TRAIN_ARGS, device)


def _blocking_train(entered: threading.Event):
    """A train mock that blocks until it is interrupted by ``pause``."""

    def train(*args, **kwargs):
        entered.set()
        while True:
            time.sleep(0.01)

    return train


def test_train_success_records_lifecycle(db_session) -> None:
    """A successful run records the task and updates it with the checkpoint."""
    outcome = {
        "checkpoint_dir": "checkpoints/ZeroDCE_CommonDataset",
        "best_val_loss": 0.123,
    }

    with mock.patch.object(llv, "train", return_value=outcome) as train:
        assert _start() == "Training started."
        assert (
            result()
            == "Training finished. Checkpoint: checkpoints/ZeroDCE_CommonDataset"
        )

    train.assert_called_once_with(
        "ZeroDCE",
        root_dir="/data/datasets/common",
        epochs=10,
        batch_size=4,
        lr=1e-4,
        resize=512,
        device=None,
    )
    task = db_session.task
    assert task.status == "success"
    assert task.model == "ZeroDCE"
    assert task.dataset == "CommonDataset"
    assert task.dataset_path == "/data/datasets/common"
    assert task.epochs == 10
    assert task.batch_size == 4
    assert task.lr == 1e-4
    assert task.resize == 512
    assert task.device == "auto"  # a None device is recorded as "auto"
    assert task.checkpoint_dir == "checkpoints/ZeroDCE_CommonDataset"
    assert task.error is None
    assert task.finish_at is not None


def test_train_failure_records_error(db_session) -> None:
    """A failed run records its error message and no checkpoint."""
    with mock.patch.object(llv, "train", side_effect=RuntimeError("boom")):
        assert _start("cuda") == "Training started."
        assert result() == "Training failed: boom"

    assert db_session.task.status == "failed"
    assert db_session.task.error == "boom"
    assert db_session.task.checkpoint_dir is None
    assert db_session.task.finish_at is not None
    assert db_session.task.device == "cuda"


def test_pause_records_stopped(db_session) -> None:
    """Pausing a running session records the task as stopped."""
    entered = threading.Event()
    with mock.patch.object(llv, "train", side_effect=_blocking_train(entered)):
        assert _start() == "Training started."
        assert entered.wait(5)
        assert db_session.task.status == "running"  # recorded when training starts
        assert pause() == "Training stopped."
        assert result() == "Training stopped."

    assert db_session.task.status == "stopped"
    assert db_session.task.error is None
    assert db_session.task.checkpoint_dir is None
    assert db_session.task.finish_at is not None


def test_start_while_running_is_rejected(db_session) -> None:
    """A second start while training runs is rejected without a new record."""
    entered = threading.Event()
    with mock.patch.object(llv, "train", side_effect=_blocking_train(entered)):
        assert _start() == "Training started."
        assert entered.wait(5)
        assert _start() == "Training is already running."
        assert pause() == "Training stopped."

    assert len(db_session.tasks) == 1


def test_result_without_training() -> None:
    """``result`` reports when no session has ever been started."""
    assert result() == "No training has been started."


def test_pause_without_training() -> None:
    """``pause`` reports when no session is running."""
    assert pause() == "No training is running."
