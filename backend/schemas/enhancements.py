from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EnhancementCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: Literal["traditional", "deep"]
    method: str
    input_artifact_id: str
    checkpoint_artifact_id: str | None = None
    params: dict = Field(default_factory=dict)
    device: str = "auto"


class EnhancementJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    input_artifact_id: str
    output_artifact_id: str | None = None
