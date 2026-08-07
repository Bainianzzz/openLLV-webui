"""Data models for enhancement tasks stored in SQLite."""

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class _EnhanceTaskBase(Base):
    """Columns shared by every enhancement task."""

    __abstract__ = True

    method: Mapped[str] = mapped_column(String(64))
    input_path: Mapped[str] = mapped_column(String(256))
    output_path: Mapped[str | None] = mapped_column(String(256))


class TraditionalTask(_EnhanceTaskBase):
    """A traditional-algorithm enhancement run (e.g. Gamma, LIME)."""

    __tablename__ = "traditional_tasks"

    params: Mapped[dict] = mapped_column(JSON, default=dict)


class DeepLearningTask(_EnhanceTaskBase):
    """A deep-learning model enhancement run (e.g. ZeroDCE)."""

    __tablename__ = "deep_learning_tasks"

    model_path: Mapped[str | None] = mapped_column(String(256))
