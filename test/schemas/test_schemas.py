from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.schemas import (
    ArtifactRead,
    EnhancementCreate,
    TaskRead,
    TrainingCreate,
)


def test_task_schema_exposes_only_the_simplified_lifecycle_fields():
    task = TaskRead(
        id="task-1",
        kind="enhancement",
        status="queued",
        created_at=datetime.now(timezone.utc),
    )
    assert task.model_dump(exclude_none=True).keys() == {
        "id",
        "kind",
        "status",
        "created_at",
    }
    with pytest.raises(ValidationError):
        TaskRead.model_validate({"id": "task-1", "kind": "enhancement", "status": "queued"})


def test_request_schemas_validate_api_values_without_secret_or_worker_fields():
    enhancement = EnhancementCreate(
        backend="traditional",
        method="Gamma",
        input_artifact_id="artifact-1",
        params={"gamma": 0.6},
    )
    assert enhancement.device == "auto"
    assert "token" not in EnhancementCreate.model_fields
    assert "progress" not in EnhancementCreate.model_fields

    training = TrainingCreate(
        model="ZeroDCE",
        dataset_id="dataset-1",
        epochs=1,
        batch_size=1,
        lr=0.001,
        resize=256,
    )
    assert training.num_workers == 0
    assert "swanlab_api_key" not in TrainingCreate.model_fields

    with pytest.raises(ValidationError):
        TrainingCreate(
            model="ZeroDCE",
            dataset_id="dataset-1",
            epochs=0,
            batch_size=1,
            lr=0.001,
            resize=256,
        )


def test_artifact_schema_returns_managed_metadata_not_a_server_path():
    artifact = ArtifactRead(
        id="artifact-1",
        kind="image",
        path_type="directory",
        display_name="inputs",
        created_at=datetime.now(timezone.utc),
        content_url="/api/v1/artifacts/artifact-1/content",
    )
    assert artifact.path_type == "directory"
    assert "relative_path" not in artifact.model_dump()
