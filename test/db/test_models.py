from datetime import datetime, timezone

from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.models import (
    Artifact,
    Dataset,
    DatasetDownloadJob,
    EnhancementJob,
    Task,
    TrainingJob,
)
from backend.db.session import create_all, get_engine, get_session_factory


def test_simplified_task_and_job_columns_have_no_runtime_process_state():
    task_columns = set(Task.__table__.columns.keys())
    assert task_columns == {
        "id",
        "kind",
        "status",
        "message",
        "error_code",
        "error_detail",
        "created_at",
        "started_at",
        "finished_at",
    }
    assert set(EnhancementJob.__table__.columns.keys()) == {
        "task_id",
        "backend",
        "method",
        "input_artifact_id",
        "checkpoint_artifact_id",
        "params",
        "device",
        "output_artifact_id",
    }
    assert set(TrainingJob.__table__.columns.keys()) == {
        "task_id",
        "model",
        "dataset_id",
        "hyperparameters",
        "device",
        "num_workers",
        "checkpoint_artifact_id",
        "history",
        "best_val_loss",
        "swanlab_url",
    }
    forbidden = {
        "worker_pid",
        "worker_pgid",
        "token",
        "cancel_requested_at",
        "revision",
        "progress",
    }
    assert not forbidden.intersection(task_columns)


def test_jobs_and_artifacts_round_trip_with_foreign_keys():
    engine = get_engine("sqlite:///:memory:")
    create_all(engine)
    sessions = get_session_factory(engine)
    now = datetime.now(timezone.utc)

    with sessions() as session:
        dataset = Dataset(
            id="dataset-1",
            dataset_key="demo",
            display_name="Demo",
            repo_id="org/demo",
            relative_path="demo",
            status="available",
            created_at=now,
            updated_at=now,
        )
        task = Task(id="task-1", kind="training", status="queued", created_at=now)
        artifact = Artifact(
            id="artifact-1",
            kind="checkpoint",
            storage_kind="checkpoints",
            path_type="file",
            relative_path="task-1/model.pt",
            task_id=task.id,
            created_at=now,
        )
        session.add_all([dataset, task])
        session.flush()
        session.add(artifact)
        session.flush()
        session.add(
            TrainingJob(
                task_id=task.id,
                model="ZeroDCE",
                dataset_id=dataset.id,
                hyperparameters={"epochs": 1},
                device="cpu",
                num_workers=0,
                checkpoint_artifact_id=artifact.id,
                history=[],
            )
        )
        session.commit()

    with sessions() as session:
        loaded = session.scalar(select(TrainingJob).where(TrainingJob.task_id == "task-1"))
        assert loaded is not None
        assert loaded.dataset_id == "dataset-1"
        assert loaded.checkpoint_artifact_id == "artifact-1"


def test_sqlite_foreign_keys_and_value_checks_are_enabled():
    engine = get_engine("sqlite:///:memory:")
    create_all(engine)
    sessions = get_session_factory(engine)

    with sessions() as session:
        session.add(Task(id="bad", kind="not-a-kind", status="queued"))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("invalid task kind should be rejected")

        session.add(
            Artifact(
                id="orphan",
                kind="image",
                storage_kind="uploads",
                path_type="file",
                relative_path="image.jpg",
                task_id="missing",
            )
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("foreign keys should be enforced")


def test_database_contains_expected_tables_and_indexes():
    engine = get_engine("sqlite:///:memory:")
    create_all(engine)
    tables = set(inspect(engine).get_table_names())
    assert tables == {
        "tasks",
        "enhancement_jobs",
        "training_jobs",
        "dataset_download_jobs",
        "datasets",
        "artifacts",
    }
