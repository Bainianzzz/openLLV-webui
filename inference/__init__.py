"""Inference package for the openLLV Gradio web interface."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .model import Base
from .utils import config, project_url
from .utils.threads import BackgroundWorker

_cfg = config()

engine = create_engine(_cfg.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create the data directory and task tables at startup."""
    _cfg.db_path.parent.mkdir(parents=True, exist_ok=True)
    _cfg.output_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


from .enhance import list_records as list_enhance_records
from .enhance import pause as pause_enhance
from .enhance import result as result_enhance
from .enhance import start as start_enhance
from .train import list_records as list_train_records
from .train import pause as pause_train
from .train import pause_download, result_download, start_download
from .train import result as result_train
from .train import start as start_train

__all__ = [  # noqa: RUF022 - ordered by domain, not alphabetically
    # init
    "init_db",
    # utils
    "config",
    "BackgroundWorker",
    "project_url",
    # enhance
    "start_enhance",
    "pause_enhance",
    "result_enhance",
    "list_enhance_records",
    # train
    "start_train",
    "pause_train",
    "result_train",
    "list_train_records",
    # download
    "start_download",
    "pause_download",
    "result_download",
]
