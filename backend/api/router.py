from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from backend.db import Artifact, Dataset, Task
from backend.schemas import DatasetDownloadCreate, EnhancementCreate, TrainingCreate

from .catalog import build_catalog
from .dependencies import (
    get_catalog_provider,
    get_dataset_downloads,
    get_session,
    get_storage,
    get_supervisor,
)
from .errors import APIError
from .services import (
    cancel_task,
    create_dataset_download,
    create_enhancement,
    create_training,
    list_tasks,
    task_response,
)

health_router = APIRouter(prefix="/health", tags=["health"])
api_router = APIRouter(prefix="/api/v1")


@health_router.get("/live")
def live():
    return {"status": "ok"}


@health_router.get("/ready")
def ready(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    storage=Depends(get_storage),
    supervisor=Depends(get_supervisor),
):
    try:
        session.execute(text("SELECT 1"))
        storage_ready = storage.ready()
        workers = _worker_states(supervisor)
    except Exception as exc:
        raise APIError(503, "service_not_ready", "Service is not ready") from exc
    if (
        request.app.state.shutting_down
        or not storage_ready
        or set(workers) != {"enhancement", "training", "dataset_download"}
        or any(state not in {"idle", "running"} for state in workers.values())
    ):
        raise APIError(503, "service_not_ready", "Service is not ready")
    return {"status": "ready", "workers": workers}


@api_router.get("/catalog")
def catalog(provider=Depends(get_catalog_provider)):
    return build_catalog(provider())


@api_router.post("/artifacts/images", status_code=201)
async def upload_images(
    files: Annotated[list[UploadFile], File()],
    session: Annotated[Session, Depends(get_session)],
    storage=Depends(get_storage),
):
    saved = await storage.save_images(files)
    artifact = Artifact(
        id=saved["id"],
        kind="image",
        storage_kind="uploads",
        path_type=saved["path_type"],
        relative_path=saved["relative_path"],
        display_name=saved["display_name"],
    )
    try:
        session.add(artifact)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return _artifact_response(artifact)


@api_router.get("/artifacts/{artifact_id}")
def artifact_detail(artifact_id: str, session: Annotated[Session, Depends(get_session)]):
    artifact = session.get(Artifact, artifact_id)
    if artifact is None:
        raise APIError(404, "artifact_not_found", "Artifact does not exist")
    return _artifact_response(artifact)


@api_router.get("/artifacts/{artifact_id}/content")
def artifact_content(
    artifact_id: str,
    session: Annotated[Session, Depends(get_session)],
    storage=Depends(get_storage),
):
    artifact = session.get(Artifact, artifact_id)
    if artifact is None:
        raise APIError(404, "artifact_not_found", "Artifact does not exist")
    path = storage.resolve(artifact.storage_kind, artifact.relative_path)
    if artifact.path_type == "directory":
        return {"items": storage.directory_items(path)}
    return FileResponse(path, filename=artifact.display_name)


@api_router.post("/enhancements", status_code=202)
def enhancements(
    request: EnhancementCreate,
    session: Annotated[Session, Depends(get_session)],
    storage=Depends(get_storage),
    supervisor=Depends(get_supervisor),
    provider=Depends(get_catalog_provider),
):
    return task_response(create_enhancement(session, request, provider(), storage, supervisor))


@api_router.post("/trainings", status_code=202)
def trainings(
    request: TrainingCreate,
    session: Annotated[Session, Depends(get_session)],
    storage=Depends(get_storage),
    supervisor=Depends(get_supervisor),
    provider=Depends(get_catalog_provider),
):
    return task_response(create_training(session, request, provider(), storage, supervisor))


@api_router.post("/datasets/downloads", status_code=202)
def dataset_downloads(
    request: DatasetDownloadCreate,
    session: Annotated[Session, Depends(get_session)],
    storage=Depends(get_storage),
    supervisor=Depends(get_supervisor),
    downloads=Depends(get_dataset_downloads),
):
    return task_response(create_dataset_download(session, request, downloads, storage, supervisor))


@api_router.get("/datasets")
def datasets(
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: Literal["downloading", "available", "failed"] | None = None,
):
    query = select(Dataset)
    count_query = select(Dataset.id)
    if status is not None:
        query = query.where(Dataset.status == status)
        count_query = count_query.where(Dataset.status == status)
    items = session.scalars(
        query.order_by(Dataset.created_at.desc(), Dataset.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    total = session.scalar(select(func.count()).select_from(count_query.subquery()))
    return {
        "items": [_dataset_response(item) for item in items],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@api_router.get("/tasks")
def tasks(
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    kind: Literal["enhancement", "training", "dataset_download"] | None = None,
    status: Literal["queued", "running", "cancelling", "succeeded", "failed", "cancelled"] | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
):
    items, total = list_tasks(
        session,
        page,
        page_size,
        kind,
        status,
        created_after,
        created_before,
    )
    return {
        "items": [task_response(item) for item in items],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@api_router.get("/tasks/{task_id}")
def task_detail(task_id: str, session: Annotated[Session, Depends(get_session)]):
    task = session.get(Task, task_id)
    if task is None:
        raise APIError(404, "task_not_found", "Task does not exist")
    response = task_response(task)
    response["enhancement"] = _job_dict(task.enhancement_job)
    response["training"] = _job_dict(task.training_job)
    response["dataset_download"] = _job_dict(task.dataset_download_job)
    return response


@api_router.post("/tasks/{task_id}/cancel")
def task_cancel(
    task_id: str,
    session: Annotated[Session, Depends(get_session)],
    supervisor=Depends(get_supervisor),
):
    return task_response(cancel_task(session, task_id, supervisor))


def _artifact_response(artifact: Artifact) -> dict:
    return {
        "id": artifact.id,
        "kind": artifact.kind,
        "path_type": artifact.path_type,
        "display_name": artifact.display_name,
        "created_at": artifact.created_at,
        "content_url": f"/api/v1/artifacts/{artifact.id}/content",
    }


def _job_dict(job) -> dict | None:
    if job is None:
        return None
    return {column.name: getattr(job, column.name) for column in job.__table__.columns}


def _dataset_response(dataset: Dataset) -> dict:
    return {
        "id": dataset.id,
        "dataset_key": dataset.dataset_key,
        "display_name": dataset.display_name,
        "status": dataset.status,
        "file_count": dataset.file_count,
        "total_bytes": dataset.total_bytes,
        "error_code": dataset.error_code,
        "created_at": dataset.created_at,
        "updated_at": dataset.updated_at,
    }


def _worker_states(supervisor) -> dict[str, str]:
    if hasattr(supervisor, "worker_states"):
        return supervisor.worker_states()
    states = {}
    for kind, slot in supervisor.slots.items():
        if slot.process is None or slot.state == "dead":
            states[kind] = "unavailable"
        else:
            states[kind] = "running" if slot.state == "busy" else slot.state
    return states
