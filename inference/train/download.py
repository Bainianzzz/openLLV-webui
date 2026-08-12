"""Hugging Face dataset downloads for the web UI."""

from __future__ import annotations

from huggingface_hub import hf_hub_download, list_repo_files

from inference.utils import config
from inference.utils.threads import BackgroundWorker


def start(
    worker: BackgroundWorker[str] | None,
    repo: str,
) -> BackgroundWorker[str] | None:
    """Start downloading ``repo`` on the given worker slot.

    ``worker`` is the slot's current worker (``None`` when idle): when it is
    still running the start is rejected and ``None`` is returned; otherwise a
    new daemon worker is started and returned for the caller to store back
    into the slot.
    """
    if worker is not None and worker.is_alive():
        return None
    worker = BackgroundWorker(_download, repo, name="dataset-download")
    worker.start()
    return worker


def pause(worker: BackgroundWorker[str] | None) -> bool | None:
    """Stop the download on ``worker``; ``None`` idle, ``True`` stopped, ``False`` stopping."""
    if worker is None or not worker.is_alive():
        return None
    return worker.stop()


def result(worker: BackgroundWorker[str] | None) -> str | None:
    """Wait for the download on ``worker`` to finish and return its local dir."""
    if worker is not None:
        worker.join()
    return worker.outcome if worker is not None else None


def _download(repo: str) -> str:
    """Download a Hugging Face dataset repo into the configured datasets dir.

    Returns the local directory the dataset was downloaded into. The repo
    files are downloaded one by one so a ``KeyboardInterrupt`` from
    ``BackgroundWorker.stop`` lands at a file boundary.
    """
    target = config().datasets_dir / repo.split("/")[-1]
    target.mkdir(parents=True, exist_ok=True)
    for filename in list_repo_files(repo_id=repo, repo_type="dataset"):
        hf_hub_download(
            repo_id=repo,
            filename=filename,
            repo_type="dataset",
            local_dir=str(target),
        )
    return str(target)


__all__ = ["pause", "result", "start"]
