from backend.db import Artifact, Dataset, DatasetDownloadJob, EnhancementJob, Task, TrainingJob

from test.helpers import database_session
from test.api.test_artifacts import PNG


def _upload(client):
    response = client.post(
        "/api/v1/artifacts/images",
        files=[("files", ("input.png", PNG, "image/png"))],
    )
    return response.json()["id"]


def test_create_enhancement_persists_job_and_submits_after_commit(client, session_factory, supervisor):
    artifact_id = _upload(client)
    response = client.post(
        "/api/v1/enhancements",
        json={
            "backend": "traditional",
            "method": "Gamma",
            "input_artifact_id": artifact_id,
            "params": {"gamma": 0.6},
        },
    )

    assert response.status_code == 202
    task_id = response.json()["id"]
    with database_session(session_factory) as session:
        assert session.get(Task, task_id).status == "queued"
        job = session.get(EnhancementJob, task_id)
        assert job.input_artifact_id == artifact_id
        assert job.backend == "traditional"
        assert job.method == "Gamma"
        assert job.params == {"gamma": 0.6}
        assert job.device == "auto"
    assert supervisor.commands[-1].payload["method"] == "Gamma"
    assert supervisor.commands[-1].storage_paths["input"].endswith(".png")
    assert supervisor.commands[-1].storage_paths["output"].endswith(task_id)


def test_create_training_accepts_optional_swanlab_without_enabled_field(client, session_factory, supervisor):
    dataset_path = client.app.state.storage.root / "datasets" / "managed"
    dataset_path.mkdir()
    with database_session(session_factory) as session:
        session.add(
            Dataset(
                id="dataset-1",
                dataset_key="managed",
                display_name="Managed",
                repo_id="example/managed",
                relative_path="managed",
                status="available",
            )
        )

    payload = {
        "model": "ZeroDCE",
        "dataset_id": "dataset-1",
        "epochs": 2,
        "batch_size": 1,
        "lr": 0.001,
        "resize": 256,
        "swanlab": {"project": "openLLV", "experiment": "test"},
    }
    response = client.post("/api/v1/trainings", json=payload)

    assert response.status_code == 202
    command_payload = supervisor.commands[-1].payload
    assert command_payload["swanlab"] == payload["swanlab"]
    assert command_payload["hyperparameters"] == {
        "epochs": 2,
        "batch_size": 1,
        "lr": 0.001,
        "resize": 256,
    }
    assert supervisor.commands[-1].storage_paths == {
        "dataset": str(dataset_path),
        "output": str(client.app.state.storage.root / "checkpoints" / response.json()["id"]),
    }
    with database_session(session_factory) as session:
        job = session.get(TrainingJob, response.json()["id"])
        assert job.hyperparameters == {"epochs": 2, "batch_size": 1, "lr": 0.001, "resize": 256}


def test_create_deep_enhancement_passes_managed_checkpoint_path(client, session_factory, supervisor):
    artifact_id = _upload(client)
    checkpoint_path = client.app.state.storage.root / "checkpoints" / "model.pth"
    checkpoint_path.write_bytes(b"checkpoint")
    with database_session(session_factory) as session:
        session.add(
            Artifact(
                id="checkpoint-1",
                kind="checkpoint",
                storage_kind="checkpoints",
                path_type="file",
                relative_path="model.pth",
                display_name="model.pth",
            )
        )

    response = client.post(
        "/api/v1/enhancements",
        json={
            "backend": "deep",
            "method": "ZeroDCE",
            "input_artifact_id": artifact_id,
            "checkpoint_artifact_id": "checkpoint-1",
        },
    )

    assert response.status_code == 202
    assert supervisor.commands[-1].storage_paths["checkpoint"] == str(checkpoint_path)


def test_create_dataset_download_snapshots_configured_repo(client, session_factory, supervisor):
    response = client.post(
        "/api/v1/datasets/downloads",
        json={"dataset_key": "LOLv1", "overwrite": False},
    )

    assert response.status_code == 202
    with database_session(session_factory) as session:
        job = session.get(DatasetDownloadJob, response.json()["id"])
        assert job.repo_id == "example/lolv1"
        assert job.dataset_key == "LOLv1"
    assert supervisor.commands[-1].kind == "dataset_download"
    assert supervisor.commands[-1].storage_paths["output"].endswith("datasets/LOLv1")
