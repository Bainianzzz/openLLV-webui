"""Mock for the Hugging Face dataset download services.

``mock_hf_download`` replaces the download call with a blocking loop that
observes the worker's cancel event, so tests can stop it cooperatively
through ``pause`` (which sets the event, no ``KeyboardInterrupt`` injection).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from importlib import import_module
from pathlib import Path
from unittest import mock

from inference.utils.task import Cancelled

from .config import mock_config


@contextmanager
def mock_hf_download(datasets_dir: Path) -> Generator[threading.Event, None, None]:
    """Patch the download module with a blocking fake download.

    The patched ``config`` points the datasets dir at ``datasets_dir`` so the
    download does not touch the real ``datasets/`` folder.

    Yields an event that is set as soon as the fake download starts, so tests
    can wait for the download to begin before stopping it.
    """
    started = threading.Event()

    def download_file(*args, **kwargs) -> None:
        """Simulate a slow download that stops when the worker's cancel event fires."""
        started.set()
        worker = threading.current_thread()
        while not worker.cancel_event.is_set():
            time.sleep(0.01)
        raise Cancelled

    module = import_module("inference.train.download")
    with (
        mock_config(module, datasets_dir=datasets_dir),
        mock.patch.object(module, "list_repo_files", return_value=["low/0.jpg"]),
        mock.patch.object(module, "hf_hub_download", side_effect=download_file),
    ):
        yield started


__all__ = ["mock_hf_download"]
