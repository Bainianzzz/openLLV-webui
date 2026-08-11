"""Inference package for the openLLV Gradio web interface."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .model import Base
from .utils import config

_cfg = config()

engine = create_engine(_cfg.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create the data directory and task tables at startup."""
    _cfg.db_path.parent.mkdir(parents=True, exist_ok=True)
    _cfg.output_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


from .enhance import batch_enhance, enhance, list_records
from .train import download_dataset, pause, result, start

__all__ = [  # noqa: RUF022 - ordered by domain, not alphabetically
    # init
    "init_db",
    # utils
    "config",
    # enhance
    "enhance",
    "batch_enhance",
    "list_records",
    # train
    "download_dataset",
    "pause",
    "result",
    "start",
]
