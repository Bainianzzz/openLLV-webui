"""Centralized runtime configuration for the openLLV web UI.

All file-save locations and other runtime constants come from ``config.yaml``
and are exposed through a single ``config()`` helper returning the cached
``AppConfig`` object.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

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


@dataclass
class AppConfig:
    """Runtime settings read from ``config.yaml``.

    Fields are plain attributes; ``set_swanlab_api_key`` updates the
    in-memory SwanLab API key for the current process.
    """

    project_root: Path
    config_file: Path
    db_path: Path
    database_url: str
    output_dir: Path
    datasets_dir: Path
    managed_datasets: dict[str, str]
    swanlab_api_key: str | None = None

    def set_swanlab_api_key(self, api_key: str | None) -> None:
        """Update the runtime SwanLab API key (e.g. from the web UI).

        An empty string is normalized to ``None``.
        """
        self.swanlab_api_key = api_key or None


@cache
def config() -> AppConfig:
    """Return the runtime paths and settings read from ``config.yaml``.

    The returned object stays cached for the process lifetime, so runtime
    updates through ``set_swanlab_api_key`` are visible to every caller.
    """
    raw = load_config()
    db_path = _resolve_path(raw["storage"]["db_path"])
    return AppConfig(
        project_root=PROJECT_ROOT,
        config_file=CONFIG_FILE,
        db_path=db_path,
        database_url=f"sqlite:///{db_path}",
        output_dir=_resolve_path(raw["output"]["dir"]),
        datasets_dir=_resolve_path(raw["datasets"]["dir"]),
        managed_datasets=dict(raw["datasets"]["download"]),
        swanlab_api_key=raw.get("swanlab", {}).get("api_key"),
    )


__all__ = ["config"]
