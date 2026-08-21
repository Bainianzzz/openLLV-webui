from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class SwanLabCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project: str
    experiment: str


class TrainingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    dataset_id: str
    epochs: Annotated[int, Field(gt=0)]
    batch_size: Annotated[int, Field(gt=0)]
    lr: Annotated[float, Field(gt=0)]
    resize: Annotated[int, Field(gt=0)] | list[Annotated[int, Field(gt=0)]]
    device: str = "auto"
    num_workers: Literal[0] = 0
    swanlab: SwanLabCreate | None = None


class TrainingJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    model: str
    dataset_id: str
    hyperparameters: dict
    device: str
    num_workers: int
    checkpoint_artifact_id: str | None = None
    history: list | None = None
    best_val_loss: float | None = None
    swanlab_url: str | None = None
