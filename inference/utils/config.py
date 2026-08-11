"""Centralized runtime configuration for the openLLV web UI.

All file-save locations and other runtime constants come from ``config.yaml``
and are exposed through a single ``config()`` helper.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from types import SimpleNamespace

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_FILE = PROJECT_ROOT / "config.yaml"


def load_config() -> dict:
    """Load the project configuration from the root config.yaml."""
    with CONFIG_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_path(path: str) -> Path:
    """Resolve a config-relative path against the project root."""
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


@cache
def config() -> SimpleNamespace:
    """Return the runtime paths and settings read from ``config.yaml``."""
    raw = load_config()
    db_path = _resolve_path(raw["storage"]["db_path"])
    return SimpleNamespace(
        project_root=PROJECT_ROOT,
        config_file=CONFIG_FILE,
        db_path=db_path,
        database_url=f"sqlite:///{db_path}",
        output_dir=_resolve_path(raw["output"]["dir"]),
        datasets_dir=_resolve_path(raw["datasets"]["dir"]),
        managed_datasets=dict(raw["datasets"]["download"]),
    )


__all__ = ["config"]
