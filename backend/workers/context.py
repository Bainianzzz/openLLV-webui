import logging
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Any


@dataclass
class WorkerContext:
    task_id: str
    worker_kind: str
    storage_paths: dict[str, Path] = field(default_factory=dict)
    cancel_event: Event = field(default_factory=Event)
    logger: Any = field(default_factory=lambda: logging.getLogger(__name__))
