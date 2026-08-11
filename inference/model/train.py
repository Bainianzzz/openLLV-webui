"""Data models for training tasks stored in SQLite."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class TrainingTask(Base):
    """A single model-training run recorded by the web UI.

    The row is inserted when training starts (status ``running``) and updated
    with the outcome when it finishes (``success``/``failed``/``stopped``).
    Hyperparameters and the dataset used are stored as explicit columns so the
    records table can display them directly.
    """

    __tablename__ = "training_tasks"

    model: Mapped[str] = mapped_column(String(64))
    dataset: Mapped[str] = mapped_column(String(64))
    dataset_path: Mapped[str] = mapped_column(String(256))
    epochs: Mapped[int]
    batch_size: Mapped[int]
    lr: Mapped[float]
    resize: Mapped[int]
    device: Mapped[str] = mapped_column(String(16))
    checkpoint_dir: Mapped[str | None] = mapped_column(String(256))
