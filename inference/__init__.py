"""Inference package for the openLLV Gradio web interface."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .model import Base
from .utils import config, project_url
from .utils.threads import Slot, Worker

_cfg = config()

engine = create_engine(_cfg.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create the data directory and task tables at startup."""
    _cfg.db_path.parent.mkdir(parents=True, exist_ok=True)
    _cfg.output_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


from .enhance import EnhanceSlot, EnhanceWorker
from .enhance import list_records as list_enhance_records
from .train import DownloadSlot, DownloadWorker, TrainSlot, TrainWorker
from .train import list_records as list_train_records

__all__ = [  # noqa: RUF022 - ordered by domain, not alphabetically
    # init
    "init_db",
    # utils
    "config",
    "Slot",
    "Worker",
    "project_url",
    # enhance
    "EnhanceSlot",
    "EnhanceWorker",
    "list_enhance_records",
    # train
    "TrainSlot",
    "TrainWorker",
    "DownloadSlot",
    "DownloadWorker",
    "list_train_records",
]
