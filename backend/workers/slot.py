from dataclasses import dataclass, field
from queue import Queue
from threading import Lock
from typing import Any

from .protocol import KINDS, TaskCommand


@dataclass
class WorkerSlot:
    kind: str
    process: Any = None
    command_pipe: Any = None
    event_pipe: Any = None
    active_task_id: str | None = None
    state: str = "starting"
    generation: int = 0
    queue: Queue = field(default_factory=Queue)
    task_states: dict[str, str] = field(default_factory=dict)
    lock: Lock = field(default_factory=Lock)

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"unsupported worker kind: {self.kind}")

    def enqueue(self, command: TaskCommand):
        if command.kind != self.kind:
            raise ValueError("command kind does not match slot")
        self.task_states[command.task_id] = "queued"
        self.queue.put(command)

    def queued_task_ids(self):
        return [task_id for task_id, state in self.task_states.items() if state == "queued"]
