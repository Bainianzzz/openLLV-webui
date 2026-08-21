from dataclasses import dataclass, field
from typing import Any

from ..context import WorkerContext


@dataclass(frozen=True)
class TaskResult:
    value: Any = None
    publish: dict[str, Any] = field(default_factory=dict)


class TaskHandler:
    def validate(self, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise ValueError("payload must be a mapping")

    def run(self, payload: dict[str, Any], context: WorkerContext) -> TaskResult:
        raise NotImplementedError

    def build_result(self, outcome: TaskResult, context: WorkerContext) -> dict[str, Any]:
        return {"result": outcome.value, "publish": outcome.publish}

    def cleanup(self, context: WorkerContext) -> None:
        return None
