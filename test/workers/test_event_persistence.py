from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db import Artifact, Base, Dataset, DatasetDownloadJob, EnhancementJob, Task, TrainingJob
from backend.api.storage import ManagedStorage
from backend.workers.events import apply_task_event
from backend.workers.protocol import TaskEvent


def _database(tmp_path):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_success_creates_output_artifact_and_links_enhancement(tmp_path):
    factory = _database(tmp_path)
    storage = ManagedStorage(tmp_path)
    output = storage.task_directory("output", "task-1") / "result.png"
    output.write_bytes(b"image")
    with factory() as session:
        session.add(Task(id="task-1", kind="enhancement", status="running"))
        session.add(EnhancementJob(task_id="task-1", backend="traditional", method="Gamma", input_artifact_id="input"))
        session.add(Artifact(id="input", kind="image", storage_kind="uploads", path_type="file", relative_path="input.png"))
        session.commit()

    apply_task_event(
        factory,
        storage,
        TaskEvent("task-1", "enhancement", "succeeded", {"publish": {"kind": "output", "path_type": "file", "path": output}}),
    )

    with factory() as session:
        task = session.get(Task, "task-1")
        job = session.get(EnhancementJob, "task-1")
        artifact = session.get(Artifact, job.output_artifact_id)
        assert task.status == "succeeded"
        assert artifact.relative_path == "task-1/result.png"
        assert artifact.path_type == "file"


def test_success_while_cancelling_does_not_publish(tmp_path):
    factory = _database(tmp_path)
    storage = ManagedStorage(tmp_path)
    output = storage.task_directory("output", "task-1")
    with factory() as session:
        session.add(Task(id="task-1", kind="enhancement", status="cancelling"))
        session.add(EnhancementJob(task_id="task-1", backend="traditional", method="Gamma", input_artifact_id="input"))
        session.add(Artifact(id="input", kind="image", storage_kind="uploads", path_type="file", relative_path="input.png"))
        session.commit()

    apply_task_event(factory, storage, TaskEvent("task-1", "enhancement", "succeeded", {"publish": {"kind": "output", "path_type": "directory", "path": output}}))

    with factory() as session:
        assert session.get(Task, "task-1").status == "cancelled"
        assert session.query(Artifact).filter(Artifact.task_id == "task-1").count() == 0


def test_training_result_and_dataset_download_update_details(tmp_path):
    factory = _database(tmp_path)
    storage = ManagedStorage(tmp_path)
    checkpoint = storage.task_directory("checkpoints", "train-1")
    (checkpoint / "model.pth").write_bytes(b"weights")
    dataset_path = storage.task_directory("datasets", "LOLv1")
    (dataset_path / "a.txt").write_bytes(b"abc")
    with factory() as session:
        session.add(Dataset(id="dataset-1", dataset_key="LOLv1", display_name="LOLv1", repo_id="repo", relative_path="LOLv1", status="downloading"))
        session.add(Task(id="train-1", kind="training", status="running"))
        session.add(TrainingJob(task_id="train-1", model="ZeroDCE", dataset_id="dataset-1", device="cpu"))
        session.add(Task(id="download-1", kind="dataset_download", status="running"))
        session.add(DatasetDownloadJob(task_id="download-1", dataset_id="dataset-1", dataset_key="LOLv1", repo_id="repo", target_relative_path="LOLv1"))
        session.commit()

    apply_task_event(factory, storage, TaskEvent("train-1", "training", "succeeded", {"result": {"history": [{"loss": 1}], "best_val_loss": 0.2}, "publish": {"kind": "checkpoint", "path_type": "directory", "path": checkpoint}}))
    apply_task_event(factory, storage, TaskEvent("download-1", "dataset_download", "succeeded", {"publish": {"kind": "dataset", "path_type": "directory", "path": dataset_path}}))

    with factory() as session:
        training = session.get(TrainingJob, "train-1")
        dataset = session.get(Dataset, "dataset-1")
        download = session.get(DatasetDownloadJob, "download-1")
        assert training.history == [{"loss": 1}]
        assert training.best_val_loss == 0.2
        assert training.checkpoint_artifact_id
        assert dataset.status == "available"
        assert dataset.file_count == download.file_count == 1
        assert dataset.total_bytes == download.downloaded_bytes == 3


def test_publish_path_outside_managed_root_fails_task(tmp_path):
    factory = _database(tmp_path)
    storage = ManagedStorage(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("bad")
    with factory() as session:
        session.add(Task(id="task-1", kind="enhancement", status="running"))
        session.commit()

    apply_task_event(factory, storage, TaskEvent("task-1", "enhancement", "succeeded", {"publish": {"kind": "output", "path_type": "file", "path": outside}}))

    with factory() as session:
        task = session.get(Task, "task-1")
        assert task.status == "failed"
        assert task.error_code == "publish_invalid"
