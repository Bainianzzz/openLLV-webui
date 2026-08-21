from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

KINDS = ("enhancement", "training", "dataset_download")
EVENT_TYPES = ("started", "succeeded", "failed")
CONTROL_TYPES = ("cancel", "shutdown", "finalize", "discard")


@dataclass(frozen=True)
class TaskCommand:
    task_id: str
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    storage_paths: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"unsupported worker kind: {self.kind}")


@dataclass(frozen=True)
class ControlMessage:
    task_id: str | None
    type: str

    def __post_init__(self):
        if self.type not in CONTROL_TYPES:
            raise ValueError(f"unsupported control type: {self.type}")


@dataclass(frozen=True)
class TaskEvent:
    task_id: str
    kind: str
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    emitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if self.kind not in KINDS or self.type not in EVENT_TYPES:
            raise ValueError("invalid task event")
