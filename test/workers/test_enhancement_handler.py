from pathlib import Path
from unittest.mock import Mock

import pytest

from backend.workers.context import WorkerContext
from backend.workers.handlers import enhancement
from backend.workers.handlers.enhancement import EnhancementHandler


def make_context(input_path: Path, output_path: Path) -> WorkerContext:
    return WorkerContext(
        task_id="enhancement-1",
        worker_kind="enhancement",
        storage_paths={"input": input_path, "output": output_path},
    )


def test_run_predicts_single_file_and_publishes_saved_file(tmp_path, monkeypatch):
    input_path = tmp_path / "input.png"
    input_path.touch()
    output_root = tmp_path / "outputs"
    output_path = output_root / "input.png"
    predict = Mock(return_value=(object(), output_path))
    monkeypatch.setattr(enhancement, "_predict", predict)

    result = EnhancementHandler().run(
        {
            "backend": "traditional",
            "method": "Gamma",
            "params": {"gamma": 0.6},
            "device": "auto",
            "checkpoint_artifact_id": None,
        },
        make_context(input_path, output_root),
    )

    predict.assert_called_once_with(
        "Gamma",
        input_path,
        output=output_path,
        backend="traditional",
        gamma=0.6,
    )
    assert result.publish == {
        "kind": "output",
        "path_type": "file",
        "path": output_path,
    }
    assert "manifest" not in result.publish


def test_run_predicts_directory_and_publishes_one_directory(tmp_path, monkeypatch):
    input_path = tmp_path / "inputs"
    input_path.mkdir()
    output_path = tmp_path / "outputs"
    saved_paths = [output_path / "a.png", output_path / "nested" / "b.png"]
    predict = Mock(return_value=saved_paths)
    monkeypatch.setattr(enhancement, "_predict", predict)

    result = EnhancementHandler().run(
        {
            "backend": "deep",
            "method": "ZeroDCE",
            "params": {"output_ext": ".png"},
            "device": "cpu",
            "checkpoint_artifact_id": None,
        },
        make_context(input_path, output_path),
    )

    predict.assert_called_once_with(
        "ZeroDCE",
        input_path,
        output=output_path,
        backend="deep",
        device="cpu",
        output_ext=".png",
    )
    assert result.publish == {
        "kind": "output",
        "path_type": "directory",
        "path": output_path,
    }
    assert "manifest" not in result.publish


def test_run_uses_managed_checkpoint_as_prediction_method(tmp_path, monkeypatch):
    input_path = tmp_path / "input.png"
    input_path.touch()
    output_root = tmp_path / "outputs"
    output_path = output_root / "input.png"
    checkpoint_path = tmp_path / "model.pth"
    predict = Mock(return_value=(object(), output_path))
    monkeypatch.setattr(enhancement, "_predict", predict)
    context = make_context(input_path, output_root)
    context.storage_paths["checkpoint"] = checkpoint_path

    EnhancementHandler().run(
        {
            "backend": "deep",
            "method": "ZeroDCE",
            "params": {},
            "device": "auto",
            "checkpoint_artifact_id": "checkpoint-1",
        },
        context,
    )

    predict.assert_called_once_with(
        checkpoint_path,
        input_path,
        output=output_path,
        backend="deep",
    )


@pytest.mark.parametrize("missing_path", ["input", "output"])
def test_run_rejects_missing_managed_storage_path(tmp_path, missing_path):
    storage_paths = {
        "input": tmp_path / "input.png",
        "output": tmp_path / "output.png",
    }
    storage_paths.pop(missing_path)
    context = WorkerContext(
        task_id="enhancement-1",
        worker_kind="enhancement",
        storage_paths=storage_paths,
    )

    with pytest.raises(ValueError, match=missing_path):
        EnhancementHandler().run(
            {
                "backend": "traditional",
                "method": "Gamma",
                "params": {},
                "device": "auto",
                "checkpoint_artifact_id": None,
            },
            context,
        )
