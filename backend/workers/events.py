"""Persistence boundary for worker lifecycle events."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.db import Artifact, Dataset, DatasetDownloadJob, EnhancementJob, Task, TrainingJob
from backend.workers.protocol import TaskEvent


_PUBLISH_ROOTS = {
    "output": "output",
    "checkpoint": "checkpoints",
    "dataset": "datasets",
}


def _now(event: TaskEvent) -> datetime:
    return event.emitted_at or datetime.now(timezone.utc)


def _publish_artifact(event: TaskEvent, payload: dict, storage) -> Artifact:
    publish = payload.get("publish")
    if not isinstance(publish, dict):
        raise ValueError("worker result did not contain publish information")
    kind = publish.get("kind")
    storage_kind = _PUBLISH_ROOTS.get(kind)
    path_type = publish.get("path_type")
    if storage_kind is None or path_type not in {"file", "directory"}:
        raise ValueError("worker publish information is invalid")

    raw_path = publish.get("path")
    if not isinstance(raw_path, (str, Path)):
        raise ValueError("worker publish path is invalid")
    root = (storage.root / storage_kind).resolve()
    raw = Path(raw_path)
    if raw.is_symlink():
        raise ValueError("worker publish path cannot be a symlink")
    path = raw.resolve()
    if not path.is_relative_to(root) or path.is_symlink():
        raise ValueError("worker publish path is outside managed storage")
    if not path.exists() or (path_type == "file" and not path.is_file()) or (
        path_type == "directory" and not path.is_dir()
    ):
        raise ValueError("worker publish path does not match its path type")

    return Artifact(
        id=str(uuid4()),
        kind=kind,
        storage_kind=storage_kind,
        path_type=path_type,
        relative_path=str(path.relative_to(root)),
        display_name=publish.get("display_name") or path.name,
        task_id=event.task_id,
    )


def _dataset_stats(path: Path) -> tuple[int, int]:
    files = [item for item in path.rglob("*") if item.is_file() and not item.is_symlink()]
    return len(files), sum(item.stat().st_size for item in files)


def apply_task_event(session_factory, storage, event: TaskEvent) -> None:
    """Apply one worker event using a new independent database session."""
    with session_factory() as session:
        task = session.get(Task, event.task_id)
        if task is None or task.kind != event.kind:
            return
        timestamp = _now(event)

        if event.type == "started":
            if task.status == "queued":
                task.status = "running"
                task.started_at = timestamp
                task.message = "Task is running"
            session.commit()
            return

        if event.type == "failed":
            if task.status in {"succeeded", "failed", "cancelled"}:
                return
            cancelled = task.status == "cancelling" or event.payload.get("error_code") == "cancelled"
            task.status = "cancelled" if cancelled else "failed"
            task.error_code = None if cancelled else event.payload.get("error_code", "handler_error")
            task.error_detail = None if cancelled else str(event.payload.get("safe_message", "Task failed"))[:512]
            task.message = "Task was cancelled" if cancelled else "Task failed"
            task.finished_at = timestamp
            if event.kind == "dataset_download":
                job = session.get(DatasetDownloadJob, task.id)
                if job and job.dataset_id:
                    dataset = session.get(Dataset, job.dataset_id)
                    if dataset:
                        dataset.status = "failed"
                        dataset.error_code = task.error_code
                        dataset.updated_at = timestamp
            session.commit()
            return

        if event.type != "succeeded" or task.status in {"succeeded", "failed", "cancelled"}:
            return
        if task.status == "cancelling":
            task.status = "cancelled"
            task.message = "Task was cancelled"
            task.finished_at = timestamp
            session.commit()
            return

        try:
            artifact = _publish_artifact(event, event.payload, storage)
        except (OSError, ValueError) as exc:
            task.status = "failed"
            task.error_code = "publish_invalid"
            task.error_detail = str(exc)[:512]
            task.message = "Task failed"
            task.finished_at = timestamp
            session.commit()
            return

        session.add(artifact)
        result = event.payload.get("result")
        if event.kind == "enhancement":
            job = session.get(EnhancementJob, task.id)
            if job:
                job.output_artifact_id = artifact.id
        elif event.kind == "training":
            job = session.get(TrainingJob, task.id)
            if job:
                job.checkpoint_artifact_id = artifact.id
                if isinstance(result, dict):
                    job.history = result.get("history")
                    job.best_val_loss = result.get("best_val_loss")
                    job.swanlab_url = result.get("swanlab_url")
        elif event.kind == "dataset_download":
            job = session.get(DatasetDownloadJob, task.id)
            if job and job.dataset_id:
                dataset = session.get(Dataset, job.dataset_id)
                if dataset:
                    count, total = _dataset_stats(storage.root / "datasets" / artifact.relative_path)
                    dataset.status = "available"
                    dataset.file_count = count
                    dataset.total_bytes = total
                    dataset.error_code = None
                    dataset.updated_at = timestamp
                    job.file_count = count
                    job.downloaded_bytes = total

        task.status = "succeeded"
        task.message = "Task completed"
        task.finished_at = timestamp
        session.commit()
