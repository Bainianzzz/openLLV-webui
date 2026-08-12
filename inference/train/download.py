"""Hugging Face dataset downloads for the web UI."""

from __future__ import annotations

import threading

from huggingface_hub import hf_hub_download, list_repo_files

from inference.utils import config
from inference.utils.task import Cancelled, Slot, Worker


class DownloadWorker(Worker[str]):
    """One dataset download: ``pause``/``result`` control it.

    A download is launched by a :class:`DownloadSlot`. It is cooperative:
    ``pause`` stops it cleanly at the next file boundary without a
    ``KeyboardInterrupt`` injection.
    """

    cooperative = True

    def pause(self) -> bool | None:
        """Stop the download on this worker; ``None`` idle, ``True`` stopped, ``False`` stopping."""
        if not self.is_alive():
            return None
        return self.stop()

    def result(self) -> str | None:
        """Wait for the download on this worker to finish and return its local dir."""
        self.join()
        return self.outcome


class DownloadSlot(Slot[str]):
    """One download slot: ``start`` launches a download, ``pause``/``result`` control it."""

    def _spawn(self, repo: str) -> DownloadWorker:
        return DownloadWorker(_download, repo, name="dataset-download")


def _download(repo: str, *, cancel: threading.Event) -> str:
    """Download a Hugging Face dataset repo into the configured datasets dir.

    Returns the local directory the dataset was downloaded into. The repo
    files are downloaded one by one, checking ``cancel`` before each file so
    a stop lands cleanly at a file boundary.
    """
    target = config().datasets_dir / repo.split("/")[-1]
    target.mkdir(parents=True, exist_ok=True)
    for filename in list_repo_files(repo_id=repo, repo_type="dataset"):
        if cancel.is_set():
            raise Cancelled
        hf_hub_download(
            repo_id=repo,
            filename=filename,
            repo_type="dataset",
            local_dir=str(target),
        )
    return str(target)


__all__ = ["DownloadSlot", "DownloadWorker"]
