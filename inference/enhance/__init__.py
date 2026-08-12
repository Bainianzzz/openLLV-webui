"""Enhancement service: run enhancement tasks and query their records."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from PIL import Image

from inference.utils import config
from inference.utils.task import Slot, Worker

from .records import list_records
from .run import _enhance


class EnhanceWorker(Worker[Image.Image | str]):
    """One enhancement run: ``pause``/``result`` control it.

    A single run returns the enhanced PIL image, a batch run returns the
    output folder path. A task row is inserted when the run starts (status
    ``pending``) and updated with the outcome when it finishes
    (``success``/``failed``/``stopped``). A run is launched by an
    :class:`EnhanceSlot`.
    """

    def pause(self) -> bool | None:
        """Stop the run on this worker; ``None`` idle, ``True`` stopped, ``False`` stopping."""
        if not self.is_alive():
            return None
        return self.stop()

    def result(self) -> Image.Image | str | None:
        """Wait for the run on this worker to finish and return its outcome.

        A single run returns the enhanced PIL image, a batch run returns the
        output folder path; ``None`` means the run did not finish successfully.
        """
        self.join()
        return self.outcome


class EnhanceSlot(Slot[Image.Image | str]):
    """One enhancement slot: ``start`` launches a run, ``pause``/``result`` control it.

    ``source`` is an image file for a single run or a folder for a batch run;
    ``output_dir`` selects where the output goes (``None`` keeps
    ``config().output_dir``).
    """

    def _spawn(
        self,
        method: str,
        source: str | Path,
        task_cls: Literal["traditional", "deepLearning"],
        model_path: str | None = None,
        params: Mapping[str, Any] | None = None,
        output_dir: str | Path | None = None,
    ) -> EnhanceWorker:
        return EnhanceWorker(
            _enhance,
            method,
            source,
            task_cls,
            model_path,
            params or {},
            output_dir or config().output_dir,
            name="openllv-enhance",
        )


__all__ = ["EnhanceSlot", "EnhanceWorker", "list_records"]
