"""Inference package for the openLLV Gradio web interface."""

from pathlib import Path

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .model import Base

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = PROJECT_ROOT / "config.yaml"


def load_config() -> dict:
    """Load the project configuration from the root config.yaml."""
    with CONFIG_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_path(path: str) -> Path:
    """Resolve a config-relative path against the project root."""
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


_config = load_config()

DB_PATH = _resolve_path(_config["storage"]["db_path"])
DATABASE_URL = f"sqlite:///{DB_PATH}"

INPUT_DIR = DB_PATH.parent / "input"
OUTPUT_DIR = DB_PATH.parent / "output"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create the data directories and task tables at startup."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


from .enhance import batch_enhance, enhance, list_records

__all__ = ["batch_enhance", "enhance", "init_db", "list_records"]
