"""Training service: dataset download and model training."""

from .download import MANAGED_DATASETS, download_dataset
from .train import train

__all__ = ["MANAGED_DATASETS", "download_dataset", "train"]
