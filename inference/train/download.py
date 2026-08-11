"""Hugging Face dataset downloads for the web UI."""

from __future__ import annotations

from huggingface_hub import snapshot_download

from inference.utils import config


def download_dataset(repo: str) -> str:
    """Download a Hugging Face dataset repo into the configured datasets dir.

    Returns the local directory the dataset was downloaded into.
    """
    target = config().datasets_dir / repo.split("/")[-1]
    target.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=repo, repo_type="dataset", local_dir=str(target))
    return str(target)


__all__ = ["download_dataset"]
