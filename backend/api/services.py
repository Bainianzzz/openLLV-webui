from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from backend.db import Artifact, Dataset, DatasetDownloadJob, EnhancementJob, Task, TrainingJob
from backend.schemas import DatasetDownloadCreate, EnhancementCreate, TrainingCreate
from backend.workers import TaskCommand

from .catalog import catalog_names
from .errors import APIError

ALLOWED_DEVICES = {"auto", "cpu", "mps", "cuda:0"}


def task_response(task: Task) -> dict:
    return {
        "id": task.id,
        "kind": task.kind,
        "status": task.status,
        "message": task.message,
        "error_code": task.error_code,
        "error_detail": task.error_detail,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "finished_at": task.finished_at,
    }


def create_enhancement(
    session: Session, request: EnhancementCreate, available: dict, storage, supervisor
) -> Task:
    category = "algorithms" if request.backend == "traditional" else "models"
    if request.method.casefold() not in catalog_names(available, category):
        raise APIError(409, "unsupported_method", "Enhancement method is not supported")
    if request.backend == "traditional" and request.checkpoint_artifact_id is not None:
        raise APIError(400, "invalid_request", "Traditional enhancement does not accept a checkpoint")
    if request.device not in ALLOWED_DEVICES:
        raise APIError(400, "invalid_request", "Device is not supported")
    artifact = session.get(Artifact, request.input_artifact_id)
    if artifact is None or artifact.kind != "image":
        raise APIError(404, "artifact_not_found", "Input artifact does not exist")
    checkpoint_artifact = None
    if request.checkpoint_artifact_id is not None:
        checkpoint_artifact = session.get(Artifact, request.checkpoint_artifact_id)
        if checkpoint_artifact is None or checkpoint_artifact.kind != "checkpoint":
            raise APIError(404, "artifact_not_found", "Checkpoint artifact does not exist")

    task = Task(id=str(uuid4()), kind="enhancement", status="queued", message="Enhancement is queued")
    session.add(task)
    session.add(
        EnhancementJob(
            task_id=task.id,
            backend=request.backend,
            method=request.method,
            input_artifact_id=artifact.id,
            checkpoint_artifact_id=request.checkpoint_artifact_id,
            params=request.params,
            device=request.device,
        )
    )
    session.commit()
    storage_paths = {
        "input": str(storage.resolve(artifact.storage_kind, artifact.relative_path)),
        "output": str(storage.task_directory("output", task.id)),
    }
    if checkpoint_artifact is not None:
        storage_paths["checkpoint"] = str(
            storage.resolve(checkpoint_artifact.storage_kind, checkpoint_artifact.relative_path)
        )
    command = TaskCommand(
        task.id,
        task.kind,
        payload=request.model_dump(),
        storage_paths=storage_paths,
    )
    submit_task(supervisor, command)
    return task


def create_training(session: Session, request: TrainingCreate, available: dict, storage, supervisor) -> Task:
    if request.model.casefold() not in catalog_names(available, "models"):
        raise APIError(409, "unsupported_method", "Training model is not supported")
    if request.device not in ALLOWED_DEVICES:
        raise APIError(400, "invalid_request", "Device is not supported")
    dataset = session.get(Dataset, request.dataset_id)
    if dataset is None or dataset.status != "available":
        raise APIError(404, "dataset_not_found", "Available dataset does not exist")

    hyperparameters = request.model_dump(include={"epochs", "batch_size", "lr", "resize"})
    task = Task(id=str(uuid4()), kind="training", status="queued", message="Training is queued")
    session.add(task)
    session.add(
        TrainingJob(
            task_id=task.id,
            model=request.model,
            dataset_id=request.dataset_id,
            hyperparameters=hyperparameters,
            device=request.device,
            num_workers=0,
        )
    )
    session.commit()
    command_payload = {
        "model": request.model,
        "dataset_id": request.dataset_id,
        "device": request.device,
        "hyperparameters": hyperparameters,
    }
    if request.swanlab is not None:
        command_payload["swanlab"] = request.swanlab.model_dump()
    submit_task(
        supervisor,
        TaskCommand(
            task.id,
            task.kind,
            payload=command_payload,
            storage_paths={
                "dataset": str(storage.resolve("datasets", dataset.relative_path)),
                "output": str(storage.task_directory("checkpoints", task.id)),
            },
        ),
    )
    return task


def create_dataset_download(
    session: Session,
    request: DatasetDownloadCreate,
    downloads: dict[str, str],
    storage,
    supervisor,
) -> Task:
    repo_id = downloads.get(request.dataset_key)
    if repo_id is None:
        raise APIError(404, "dataset_not_found", "Dataset download is not configured")
    dataset = session.scalar(select(Dataset).where(Dataset.dataset_key == request.dataset_key))
    if dataset is not None and not request.overwrite:
        raise APIError(409, "duplicate_artifact", "Dataset already exists")
    if dataset is None:
        dataset = Dataset(
            id=str(uuid4()),
            dataset_key=request.dataset_key,
            display_name=request.dataset_key,
            repo_id=repo_id,
            relative_path=request.dataset_key,
            status="downloading",
        )
        session.add(dataset)
    else:
        dataset.status = "downloading"
        dataset.repo_id = repo_id
        dataset.updated_at = datetime.now(timezone.utc)

    task = Task(id=str(uuid4()), kind="dataset_download", status="queued", message="Download is queued")
    session.add(task)
    session.add(
        DatasetDownloadJob(
            task_id=task.id,
            dataset_id=dataset.id,
            dataset_key=request.dataset_key,
            repo_id=repo_id,
            target_relative_path=request.dataset_key,
            overwrite=request.overwrite,
        )
    )
    session.commit()
    payload = {"dataset_key": request.dataset_key, "repo_id": repo_id, "overwrite": request.overwrite}
    submit_task(
        supervisor,
        TaskCommand(
            task.id,
            task.kind,
            payload=payload,
            storage_paths={"output": str(storage.target("datasets", dataset.relative_path))},
        ),
    )
    return task


def cancel_task(session: Session, task_id: str, supervisor) -> Task:
    task = session.get(Task, task_id)
    if task is None:
        raise APIError(404, "task_not_found", "Task does not exist")
    now = datetime.now(timezone.utc)
    if task.status == "queued":
        session.execute(
            update(Task)
            .where(Task.id == task_id, Task.status == "queued")
            .values(status="cancelled", finished_at=now, message="Task was cancelled")
        )
        session.commit()
        supervisor.cancel(task_id, task.kind)
    elif task.status == "running":
        session.execute(
            update(Task)
            .where(Task.id == task_id, Task.status == "running")
            .values(status="cancelling", message="Cancellation requested")
        )
        session.commit()
        supervisor.cancel(task_id, task.kind)
    session.refresh(task)
    return task


def list_tasks(
    session: Session,
    page: int,
    page_size: int,
    kind: str | None,
    status: str | None,
    created_after: datetime | None,
    created_before: datetime | None,
):
    filters = []
    if kind is not None:
        filters.append(Task.kind == kind)
    if status is not None:
        filters.append(Task.status == status)
    if created_after is not None:
        filters.append(Task.created_at > created_after)
    if created_before is not None:
        filters.append(Task.created_at < created_before)
    total = session.scalar(select(func.count()).select_from(Task).where(*filters))
    tasks = session.scalars(
        select(Task)
        .where(*filters)
        .order_by(Task.created_at.desc(), Task.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return tasks, total


def submit_task(supervisor, command: TaskCommand) -> None:
    try:
        supervisor.submit(command)
    except Exception as exc:
        raise APIError(409, "worker_unavailable", "Worker is unavailable") from exc
