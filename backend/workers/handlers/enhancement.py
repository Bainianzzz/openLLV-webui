from pathlib import Path
from typing import Any

from ..context import WorkerContext
from .base import TaskHandler, TaskResult


def _predict(method: str | Path, source: Path, **kwargs: Any) -> Any:
    import openLLV as llv

    return llv.predict(method, source, **kwargs)


class EnhancementHandler(TaskHandler):
    def validate(self, payload: dict[str, Any]) -> None:
        super().validate(payload)
        if payload.get("backend") not in {"traditional", "deep"}:
            raise ValueError("backend must be traditional or deep")
        if not isinstance(payload.get("method"), str) or not payload["method"]:
            raise ValueError("method must be a non-empty string")
        if not isinstance(payload.get("params"), dict):
            raise ValueError("params must be a mapping")
        if payload.get("checkpoint_artifact_id") and payload["backend"] != "deep":
            raise ValueError("checkpoint artifacts require the deep backend")

    def run(
        self, payload: dict[str, Any], context: WorkerContext
    ) -> TaskResult:
        self.validate(payload)
        input_path = self._storage_path(context, "input")
        output_root = self._storage_path(context, "output")
        output_path = output_root if input_path.is_dir() else output_root / input_path.name

        method: str | Path = payload["method"]
        if payload.get("checkpoint_artifact_id"):
            method = self._storage_path(context, "checkpoint")

        kwargs = dict(payload["params"])
        kwargs["backend"] = payload["backend"]
        device = payload.get("device")
        if payload["backend"] == "deep" and device not in {None, "auto"}:
            kwargs["device"] = device

        output_root.mkdir(parents=True, exist_ok=True)
        outcome = _predict(method, input_path, output=output_path, **kwargs)
        if input_path.is_dir():
            publish_path = output_path
            path_type = "directory"
        else:
            if not isinstance(outcome, tuple) or len(outcome) != 2:
                raise ValueError("openLLV returned an invalid single-file result")
            saved_path = outcome[1]
            if saved_path is None:
                raise ValueError("openLLV did not save the enhanced image")
            publish_path = Path(saved_path)
            path_type = "file"

        return TaskResult(
            publish={
                "kind": "output",
                "path_type": path_type,
                "path": publish_path,
            }
        )

    @staticmethod
    def _storage_path(context: WorkerContext, name: str) -> Path:
        path = context.storage_paths.get(name)
        if not isinstance(path, Path):
            raise ValueError(f"managed {name} path is required")
        return path
