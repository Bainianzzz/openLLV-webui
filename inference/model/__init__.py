"""SQLAlchemy data models for the inference package."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .enhance import DeepLearningTask, TraditionalTask


class Base(DeclarativeBase):
    """Declarative base carrying the columns shared by every task model."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    error: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


__all__ = ["DeepLearningTask", "TraditionalTask"]
