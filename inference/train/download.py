"""Hugging Face dataset downloads for the web UI."""

from __future__ import annotations

import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from huggingface_hub import hf_hub_download, list_repo_files

from inference.utils import DownloadCancelled, config

# `snapshot_download` has no cancellation API, so the repo files are downloaded
# one by one and checked against this flag so the user can stop a download.
_stop_requested = threading.Event()


def stop_download() -> None:
    """Signal the in-flight dataset download to stop at the next file boundary."""
    _stop_requested.set()


def download_dataset(repo: str) -> str:
    """Download a Hugging Face dataset repo into the configured datasets dir.

    Returns the local directory the dataset was downloaded into.
    """
    _stop_requested.clear()
    target = config().datasets_dir / repo.split("/")[-1]
    target.mkdir(parents=True, exist_ok=True)

    def download_file(filename: str) -> None:
        hf_hub_download(
            repo_id=repo,
            filename=filename,
            repo_type="dataset",
            local_dir=str(target),
        )

    files = list_repo_files(repo_id=repo, repo_type="dataset")
    pool = ThreadPoolExecutor(max_workers=8)
    try:
        pending = {pool.submit(download_file, filename) for filename in files}
        while pending:
            if _stop_requested.is_set():
                pool.shutdown(wait=False, cancel_futures=True)
                raise DownloadCancelled
            # Poll so a stop lands quickly even while one large file is downloading.
            done, pending = wait(pending, timeout=0.2, return_when=FIRST_COMPLETED)
            for future in done:
                future.result()
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
        _stop_requested.clear()
    return str(target)


__all__ = ["download_dataset", "stop_download"]
