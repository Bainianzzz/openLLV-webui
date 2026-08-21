"""SQLAlchemy models for the refactored task database."""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base for all database models."""


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("kind IN ('enhancement', 'training', 'dataset_download')", name="ck_tasks_kind"),
        CheckConstraint(
            "status IN ('queued', 'running', 'cancelling', 'succeeded', 'failed', 'cancelled')",
            name="ck_tasks_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    message: Mapped[str | None] = mapped_column(String(512))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    enhancement_job: Mapped["EnhancementJob | None"] = relationship(back_populates="task", uselist=False)
    training_job: Mapped["TrainingJob | None"] = relationship(back_populates="task", uselist=False)
    dataset_download_job: Mapped["DatasetDownloadJob | None"] = relationship(back_populates="task", uselist=False)


class EnhancementJob(Base):
    __tablename__ = "enhancement_jobs"

    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    backend: Mapped[str] = mapped_column(String(16))
    method: Mapped[str] = mapped_column(String(128))
    input_artifact_id: Mapped[str] = mapped_column(ForeignKey("artifacts.id"))
    checkpoint_artifact_id: Mapped[str | None] = mapped_column(ForeignKey("artifacts.id"))
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    device: Mapped[str] = mapped_column(String(32), default="auto")
    output_artifact_id: Mapped[str | None] = mapped_column(ForeignKey("artifacts.id"))

    task: Mapped[Task] = relationship(back_populates="enhancement_job")


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    model: Mapped[str] = mapped_column(String(128))
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"))
    hyperparameters: Mapped[dict] = mapped_column(JSON, default=dict)
    device: Mapped[str] = mapped_column(String(32))
    num_workers: Mapped[int] = mapped_column(Integer, default=0)
    checkpoint_artifact_id: Mapped[str | None] = mapped_column(ForeignKey("artifacts.id"))
    history: Mapped[list | None] = mapped_column(JSON)
    best_val_loss: Mapped[float | None] = mapped_column(Float)
    swanlab_url: Mapped[str | None] = mapped_column(String(512))

    task: Mapped[Task] = relationship(back_populates="training_job")
    dataset: Mapped["Dataset"] = relationship(back_populates="training_jobs")


class DatasetDownloadJob(Base):
    __tablename__ = "dataset_download_jobs"

    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    dataset_id: Mapped[str | None] = mapped_column(ForeignKey("datasets.id"))
    dataset_key: Mapped[str] = mapped_column(String(128))
    repo_id: Mapped[str] = mapped_column(String(256))
    target_relative_path: Mapped[str] = mapped_column(String(512))
    file_count: Mapped[int | None] = mapped_column(Integer)
    downloaded_bytes: Mapped[int | None] = mapped_column(Integer)
    overwrite: Mapped[bool] = mapped_column(Boolean, default=False)

    task: Mapped[Task] = relationship(back_populates="dataset_download_job")
    dataset: Mapped["Dataset | None"] = relationship(back_populates="download_jobs")


class Dataset(Base):
    __tablename__ = "datasets"
    __table_args__ = (UniqueConstraint("dataset_key", name="uq_datasets_dataset_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_key: Mapped[str] = mapped_column(String(128))
    display_name: Mapped[str] = mapped_column(String(256))
    repo_id: Mapped[str] = mapped_column(String(256))
    relative_path: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32))
    file_count: Mapped[int | None] = mapped_column(Integer)
    total_bytes: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    training_jobs: Mapped[list[TrainingJob]] = relationship(back_populates="dataset")
    download_jobs: Mapped[list[DatasetDownloadJob]] = relationship(back_populates="dataset")


class Artifact(Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        UniqueConstraint("storage_kind", "relative_path", name="uq_artifacts_storage_path"),
        CheckConstraint("path_type IN ('file', 'directory')", name="ck_artifacts_path_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32))
    storage_kind: Mapped[str] = mapped_column(String(32))
    path_type: Mapped[str] = mapped_column(String(16))
    relative_path: Mapped[str] = mapped_column(String(1024))
    display_name: Mapped[str | None] = mapped_column(String(256))
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
