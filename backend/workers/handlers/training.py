from pathlib import Path
from typing import Any, Callable

from ..context import WorkerContext
from .base import TaskHandler, TaskResult


class SwanLabTrainingNotConfigured(RuntimeError):
    """Raised when a task requests SwanLab without a configured adapter."""


def _train(**kwargs: Any) -> dict[str, Any]:
    """Load openLLV only when a worker actually starts a local training task."""
    import openLLV as llv

    return llv.train(**kwargs)


_SUPPORTED_HYPERPARAMETERS = {
    "batch_size",
    "pin_memory",
    "shuffle",
    "drop_last",
    "train_split",
    "val_split",
    "return_filename",
    "resize",
    "train_input_dir",
    "train_target_dir",
    "val_input_dir",
    "val_target_dir",
    "data_params",
    "train_params",
    "val_params",
    "loss",
    "loss_params",
    "output_index",
    "output_key",
    "optimizer",
    "lr",
    "optimizer_params",
    "scheduler",
    "scheduler_params",
    "epochs",
    "save_every",
    "validate_every",
    "log_every",
    "grad_clip",
    "amp",
    "resume",
    "resume_path",
    "strict_resume",
    "seed",
    "progress_bar",
}


class TrainingHandler(TaskHandler):
    def __init__(
        self,
        swanlab_adapter: Callable[..., dict[str, Any]] | None = None,
    ) -> None:
        self._swanlab_adapter = swanlab_adapter

    def validate(self, payload: dict[str, Any]) -> None:
        super().validate(payload)
        for key in ("model", "dataset_id"):
            if not isinstance(payload.get(key), str) or not payload[key]:
                raise ValueError(f"{key} must be a non-empty string")
        hyperparameters = payload.get("hyperparameters", {})
        if not isinstance(hyperparameters, dict):
            raise ValueError("hyperparameters must be a mapping")
        unsupported = set(hyperparameters) - _SUPPORTED_HYPERPARAMETERS
        if unsupported:
            names = ", ".join(sorted(unsupported))
            raise ValueError(f"unsupported training hyperparameters: {names}")
        if "swanlab" in payload and payload["swanlab"] is not None:
            if not isinstance(payload["swanlab"], dict):
                raise ValueError("swanlab must be a mapping")

    def run(self, payload: dict[str, Any], context: WorkerContext) -> TaskResult:
        self.validate(payload)
        dataset_path = self._storage_path(context, "dataset")
        output_path = self._storage_path(context, "output")
        hyperparameters = dict(payload.get("hyperparameters", {}))
        kwargs: dict[str, Any] = {
            "model": payload["model"],
            "dataset": payload["dataset_id"],
            "root_dir": dataset_path,
            "output_dir": output_path,
            "device": payload.get("device"),
            "num_workers": 0,
        }

        swanlab_config = payload.get("swanlab")
        if swanlab_config is not None:
            if self._swanlab_adapter is None:
                raise SwanLabTrainingNotConfigured(
                    "SwanLab training was requested, but no SwanLab adapter is configured"
                )
            outcome = self._swanlab_adapter(
                **kwargs,
                hyperparameters=hyperparameters,
                swanlab_config=dict(swanlab_config),
            )
        else:
            kwargs.update(hyperparameters)
            outcome = _train(**kwargs)

        if not isinstance(outcome, dict):
            raise ValueError("training adapter returned an invalid result")
        if "history" not in outcome or "best_val_loss" not in outcome:
            raise ValueError("training adapter result lacks history or best_val_loss")
        result = {
            "history": outcome["history"],
            "best_val_loss": outcome["best_val_loss"],
        }
        if outcome.get("swanlab_url") is not None:
            result["swanlab_url"] = outcome["swanlab_url"]
        return TaskResult(
            value=result,
            publish={
                "kind": "checkpoint",
                "path_type": "directory",
                "path": output_path,
            },
        )

    @staticmethod
    def _storage_path(context: WorkerContext, name: str) -> Path:
        path = context.storage_paths.get(name)
        if not isinstance(path, Path):
            raise ValueError(f"managed {name} path is required")
        return path
