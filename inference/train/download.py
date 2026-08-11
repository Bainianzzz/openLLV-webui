"""Hugging Face dataset downloads for the web UI."""

from __future__ import annotations

from huggingface_hub import snapshot_download

from inference import PROJECT_ROOT

# Datasets the web UI can download; display name -> HF dataset repo id.
MANAGED_DATASETS = {
    "LOLv1": "okita-souji/LOLv1",
}

DATASETS_DIR = PROJECT_ROOT / "datasets"


def download_dataset(repo: str) -> str:
    """Download a Hugging Face dataset repo under ``datasets/<name>``.

    Returns the local directory the dataset was downloaded into.
    """
    target = DATASETS_DIR / repo.split("/")[-1]
    target.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=repo, repo_type="dataset", local_dir=str(target))
    return str(target)


__all__ = ["DATASETS_DIR", "MANAGED_DATASETS", "download_dataset"]
