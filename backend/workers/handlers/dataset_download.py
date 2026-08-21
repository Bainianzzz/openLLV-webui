import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterable

from ..context import WorkerContext
from .base import TaskHandler, TaskResult


def _list_files(repo_id: str) -> Iterable[str]:
    from huggingface_hub import HfApi

    return HfApi().list_repo_files(repo_id=repo_id, repo_type="dataset")


def _download_file(repo_id: str, filename: str, destination: Path) -> Path:
    from huggingface_hub import hf_hub_download

    return Path(
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="dataset",
            local_dir=destination,
        )
    )


class DatasetDownloadHandler(TaskHandler):
    def __init__(
        self,
        list_files: Callable[[str], Iterable[str]] | None = None,
        download_file: Callable[[str, str, Path], Path] | None = None,
    ) -> None:
        self._list_files = list_files or _list_files
        self._download_file = download_file or _download_file

    def validate(self, payload: dict[str, Any]) -> None:
        super().validate(payload)
        for key in ("dataset_key", "repo_id"):
            if not isinstance(payload.get(key), str) or not payload[key]:
                raise ValueError(f"{key} must be a non-empty string")
        if not isinstance(payload.get("overwrite"), bool):
            raise ValueError("overwrite must be a boolean")

    def run(self, payload: dict[str, Any], context: WorkerContext) -> TaskResult:
        self.validate(payload)
        output = context.storage_paths.get("output")
        if not isinstance(output, Path):
            raise ValueError("managed output path is required")
        if output.exists() and not payload["overwrite"]:
            raise FileExistsError(f"dataset output already exists: {output}")

        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=f".{payload['dataset_key']}-", dir=output.parent))
        try:
            for filename in self._list_files(payload["repo_id"]):
                if context.cancel_event.is_set():
                    raise InterruptedError("cancelled")
                if not isinstance(filename, str) or not filename:
                    raise ValueError("Hugging Face returned an invalid filename")
                self._download_file(payload["repo_id"], filename, temporary)

            if context.cancel_event.is_set():
                raise InterruptedError("cancelled")
            self._publish(temporary, output, overwrite=payload["overwrite"])
            temporary = None
            return TaskResult(
                publish={"kind": "dataset", "path_type": "directory", "path": output}
            )
        finally:
            if temporary is not None:
                shutil.rmtree(temporary, ignore_errors=True)

    @staticmethod
    def _publish(temporary: Path, output: Path, overwrite: bool) -> None:
        backup: Path | None = None
        if output.exists():
            if not overwrite:
                raise FileExistsError(f"dataset output already exists: {output}")
            backup = Path(tempfile.mkdtemp(prefix=f".{output.name}-old-", dir=output.parent))
            backup.rmdir()
            output.rename(backup)
        try:
            temporary.rename(output)
        except Exception:
            if backup is not None and not output.exists():
                backup.rename(output)
            raise
        if backup is not None:
            shutil.rmtree(backup, ignore_errors=True)
