from collections.abc import Mapping

from .handlers.dataset_download import DatasetDownloadHandler
from .handlers.enhancement import EnhancementHandler
from .handlers.training import TrainingHandler
from .protocol import KINDS

DEFAULT_HANDLERS = {
    "enhancement": EnhancementHandler,
    "training": TrainingHandler,
    "dataset_download": DatasetDownloadHandler,
}


def make_registry(handlers: Mapping[str, object] | None = None) -> dict[str, object]:
    registry = dict(DEFAULT_HANDLERS)
    if handlers:
        unknown = set(handlers) - set(KINDS)
        if unknown:
            raise ValueError(f"unsupported handler kinds: {sorted(unknown)}")
        registry.update(handlers)
    return registry


def get_handler(registry, kind):
    handler = registry[kind]
    return handler() if isinstance(handler, type) else handler
