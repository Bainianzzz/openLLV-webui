"""Tests for the ``inference.train`` training lifecycle recording."""

import threading
import time
from pathlib import Path
from unittest import mock

import openLLV as llv
import pytest

import inference.train.run as run_module
from inference import Status
from inference.train import TrainSlot
from test.mock import mock_config, mock_train_db

TRAIN_ARGS = ("ZeroDCE", "CommonDataset", "/data/datasets/common", 10, 4, 1e-4, 512)


@pytest.fixture(autouse=True)
def no_swanlab_key():
    """Replace the runner's config lookup with a mock without a SwanLab key.

    The runner switches to ``BatchSwanLabTrainer`` whenever
    ``config().swanlab_api_key`` is set, which would bypass the mocked
    ``llv.train``; these tests exercise the plain training path, so the
    runner's ``config`` is patched through the shared ``test.mock.mock_config``
    instead of reading or mutating the real ``config.yaml`` value.
    """
    with mock_config(run_module):
        yield


@pytest.fixture(autouse=True)
def db_session():
    """Mock the database session for every test in this module."""
    with mock_train_db() as session:
        yield session


def _start(device: str | None = None, output_dir: str | None = None, slot=None):
    """Start training with the shared fixture arguments."""
    slot = slot or TrainSlot()
    return slot.start(*TRAIN_ARGS, device, output_dir)


def _blocking_train(entered: threading.Event):
    """A train mock that blocks until it is interrupted by ``pause``."""

    def train(*args, **kwargs):
        entered.set()
        while True:
            time.sleep(0.01)

    return train


@pytest.mark.parametrize(
    "output_dir, checkpoint_dir",
    [
        (None, "checkpoints/ZeroDCE_CommonDataset"),
        ("/data/checkpoints/custom", "checkpoints/custom/checkpoints"),
    ],
)
def test_train_success_records_lifecycle(
    db_session, output_dir, checkpoint_dir
) -> None:
    """A successful run records the task and returns the checkpoint dir."""
    outcome = {"checkpoint_dir": checkpoint_dir, "best_val_loss": 0.123}

    with mock.patch.object(llv, "train", return_value=outcome) as train:
        worker = _start(output_dir=output_dir)
        assert worker is not None
        assert worker.result() == db_session.task.checkpoint_dir
        assert worker.error is None
        assert worker.status is Status.SUCCESS

    train.assert_called_once_with(
        "ZeroDCE",
        dataset="CommonDataset",
        root_dir="/data/datasets/common",
        epochs=10,
        batch_size=4,
        lr=1e-4,
        resize=512,
        device=None,
        output_dir=output_dir,
        num_workers=0,
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
    assert Path(task.checkpoint_dir).is_absolute()
    assert task.checkpoint_dir.endswith(checkpoint_dir)
    assert task.error is None
    assert task.finish_at is not None


def test_train_failure_records_error(db_session) -> None:
    """A failed run records its error message and no checkpoint."""
    with mock.patch.object(llv, "train", side_effect=RuntimeError("boom")):
        worker = _start("cuda")
        assert worker is not None
        assert worker.result() is None

    assert isinstance(worker.error, RuntimeError)
    assert db_session.task.status == "failed"
    assert db_session.task.error == "boom"
    assert db_session.task.checkpoint_dir is None
    assert db_session.task.finish_at is not None
    assert db_session.task.device == "cuda"


@pytest.mark.parametrize(
    "checkpoint",
    [None, "/abs/checkpoints/SCI_CommonDataset"],
)
def test_pause_records_stopped(db_session, checkpoint) -> None:
    """Pausing records the task as stopped with any weights found on disk."""
    entered = threading.Event()
    with (
        mock.patch.object(llv, "train", side_effect=_blocking_train(entered)),
        mock.patch.object(run_module, "_find_checkpoint_dir", return_value=checkpoint),
    ):
        worker = _start()
        assert worker is not None
        assert entered.wait(5)
        assert db_session.task.status == "running"  # recorded when training starts
        assert worker.pause() is True
        assert worker.result() is None

    assert worker.status is Status.STOPPED
    assert db_session.task.status == "stopped"
    assert db_session.task.error is None
    assert db_session.task.checkpoint_dir == checkpoint
    assert db_session.task.finish_at is not None


def test_find_checkpoint_dir_detects_weights(tmp_path) -> None:
    """Only a checkpoint dir containing weight files is reported."""
    weights = tmp_path / "checkpoints"
    weights.mkdir()
    assert (
        run_module._find_checkpoint_dir("SCI", "CommonDataset", str(tmp_path)) is None
    )
    (weights / "last.pt").write_bytes(b"state")
    assert run_module._find_checkpoint_dir(
        "SCI", "CommonDataset", str(tmp_path)
    ) == str(tmp_path.resolve())


def test_find_checkpoint_dir_default_location(tmp_path, monkeypatch) -> None:
    """A None output dir checks the openLLV default location."""
    weights = tmp_path / "checkpoints" / "SCI_CommonDataset" / "checkpoints"
    weights.mkdir(parents=True)
    (weights / "best.pt").write_bytes(b"state")
    monkeypatch.chdir(tmp_path)
    assert run_module._find_checkpoint_dir("SCI", "CommonDataset", None) == str(
        (tmp_path / "checkpoints" / "SCI_CommonDataset").resolve()
    )


def test_start_while_running_is_rejected(db_session) -> None:
    """A second start on the same slot while training runs is rejected."""
    entered = threading.Event()
    with mock.patch.object(llv, "train", side_effect=_blocking_train(entered)):
        slot = TrainSlot()
        worker = _start(slot=slot)
        assert worker is not None
        assert entered.wait(5)
        assert _start(slot=slot) is None
        assert worker.pause() is True

    assert len(db_session.tasks) == 1


def test_pause_after_finish(db_session) -> None:
    """``pause`` reports idle once the session has finished."""
    outcome = {
        "checkpoint_dir": "checkpoints/ZeroDCE_CommonDataset",
        "best_val_loss": 0.123,
    }
    with mock.patch.object(llv, "train", return_value=outcome):
        worker = _start()
        assert worker is not None
        worker.result()
    assert worker.pause() is None


def test_result_after_finish(db_session) -> None:
    """``result`` on a finished worker returns its checkpoint dir again."""
    outcome = {
        "checkpoint_dir": "checkpoints/ZeroDCE_CommonDataset",
        "best_val_loss": 0.123,
    }
    with mock.patch.object(llv, "train", return_value=outcome):
        worker = _start()
        assert worker is not None
        first = worker.result()
    assert first is not None
    assert worker.result() == first
