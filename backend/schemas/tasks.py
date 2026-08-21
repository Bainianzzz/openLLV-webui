from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

TaskKind = Literal["enhancement", "training", "dataset_download"]
TaskStatus = Literal["queued", "running", "cancelling", "succeeded", "failed", "cancelled"]


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    kind: TaskKind
    status: TaskStatus
    message: str | None = None
    error_code: str | None = None
    error_detail: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class TaskDetail(TaskRead):
    enhancement: object | None = None
    training: object | None = None
    dataset_download: object | None = None
