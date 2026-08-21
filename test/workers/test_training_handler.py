from pathlib import Path
from unittest.mock import Mock

import pytest

from backend.workers.context import WorkerContext
from backend.workers.handlers import training
from backend.workers.handlers.training import (
    SwanLabTrainingNotConfigured,
    TrainingHandler,
)


def make_context(tmp_path: Path) -> WorkerContext:
    return WorkerContext(
        task_id="training-1",
        worker_kind="training",
        storage_paths={
            "dataset": tmp_path / "dataset",
            "output": tmp_path / "output",
        },
    )


def test_run_trains_with_managed_paths_and_publishes_checkpoint_directory(
    tmp_path, monkeypatch
):
    train = Mock(
        return_value={
            "history": [{"epoch": 1, "val_loss": 0.2}],
            "best_val_loss": 0.2,
            "checkpoint_dir": str(tmp_path / "output"),
        }
    )
    monkeypatch.setattr(training, "_train", train)

    result = TrainingHandler().run(
        {
            "model": "ZeroDCE",
            "dataset_id": "LOL-v1",
            "hyperparameters": {"epochs": 2, "batch_size": 4, "lr": 0.001},
            "device": "cpu",
        },
        make_context(tmp_path),
    )

    train.assert_called_once_with(
        model="ZeroDCE",
        dataset="LOL-v1",
        root_dir=tmp_path / "dataset",
        output_dir=tmp_path / "output",
        epochs=2,
        batch_size=4,
        lr=0.001,
        device="cpu",
        num_workers=0,
    )
    assert result.value == {
        "history": [{"epoch": 1, "val_loss": 0.2}],
        "best_val_loss": 0.2,
    }
    assert result.publish == {
        "kind": "checkpoint",
        "path_type": "directory",
        "path": tmp_path / "output",
    }
    assert str(tmp_path) not in repr(result.value)


def test_swanlab_config_uses_injectable_adapter(tmp_path):
    adapter = Mock(
        return_value={
            "history": [],
            "best_val_loss": 1.0,
            "checkpoint_dir": "/private/worker/output",
        }
    )
    payload = {
        "model": "ZeroDCE",
        "dataset_id": "LOL-v1",
        "hyperparameters": {"epochs": 1},
        "device": "cpu",
        "swanlab": {"project": "demo", "experiment": "run-1"},
    }

    result = TrainingHandler(swanlab_adapter=adapter).run(
        payload, make_context(tmp_path)
    )

    adapter.assert_called_once_with(
        model="ZeroDCE",
        dataset="LOL-v1",
        root_dir=tmp_path / "dataset",
        output_dir=tmp_path / "output",
        device="cpu",
        num_workers=0,
        hyperparameters={"epochs": 1},
        swanlab_config={"project": "demo", "experiment": "run-1"},
    )
    assert result.value == {"history": [], "best_val_loss": 1.0}
    assert result.publish["path"] == tmp_path / "output"


def test_swanlab_config_without_adapter_fails_clearly(tmp_path):
    with pytest.raises(SwanLabTrainingNotConfigured, match="SwanLab"):
        TrainingHandler().run(
            {
                "model": "ZeroDCE",
                "dataset_id": "LOL-v1",
                "hyperparameters": {},
                "device": "cpu",
                "swanlab": {"project": "demo"},
            },
            make_context(tmp_path),
        )


@pytest.mark.parametrize("missing", ["dataset", "output"])
def test_run_requires_managed_storage_paths(tmp_path, missing):
    context = make_context(tmp_path)
    context.storage_paths.pop(missing)

    with pytest.raises(ValueError, match=missing):
        TrainingHandler().run(
            {
                "model": "ZeroDCE",
                "dataset_id": "LOL-v1",
                "hyperparameters": {},
                "device": "cpu",
            },
            context,
        )
