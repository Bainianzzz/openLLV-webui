"""Shared mock for the runtime ``config()`` used by the web UI services.

The real ``AppConfig`` class is instantiated with in-memory defaults instead
of reading ``config.yaml``, and no SwanLab API key is provided; tests
override individual fields through ``mock_config``'s keyword arguments.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import replace
from importlib import import_module
from pathlib import Path
from types import ModuleType
from unittest import mock

from inference.utils.config import AppConfig


@contextmanager
def mock_config(
    module: ModuleType | str, **overrides
) -> Generator[AppConfig, None, None]:
    """Patch ``config`` in ``module`` to return a test-safe ``AppConfig``.

    ``module`` is the module object (or import path) whose module-level
    ``config`` reference is replaced, matching how the services bind it.
    The config is built from in-memory defaults without a SwanLab API key;
    overrides replace individual fields. Yields the config so tests can
    inspect it.
    """
    target = import_module(module) if isinstance(module, str) else module
    config = replace(
        AppConfig(
            project_root=Path("."),
            config_file=Path("config.yaml"),
            db_path=Path("data/app.db"),
            database_url="sqlite:///data/app.db",
            output_dir=Path("data/output"),
            datasets_dir=Path("datasets"),
            managed_datasets={},
        ),
        **overrides,
    )
    with mock.patch.object(target, "config", return_value=config):
        yield config


__all__ = ["mock_config"]
