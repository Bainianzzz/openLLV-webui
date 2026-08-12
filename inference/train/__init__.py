"""Training service: dataset download, model training, and record queries."""

from __future__ import annotations

from inference.utils.threads import Slot, Worker

from .download import DownloadSlot, DownloadWorker
from .records import list_records
from .run import _train


class TrainWorker(Worker[str]):
    """One training session: ``pause``/``result`` control it.

    A ``TrainingTask`` row is inserted when the run starts (status
    ``running``) and updated with the outcome when it finishes
    (``success``/``failed``/``stopped``). Whether the session is recorded in
    SwanLab is decided by ``config().swanlab_api_key`` inside the runner. A
    run is launched by a :class:`TrainSlot`.
    """

    def pause(self) -> bool | None:
        """Stop the run on this worker; ``None`` idle, ``True`` stopped, ``False`` stopping."""
        if not self.is_alive():
            return None
        return self.stop()

    def result(self) -> str | None:
        """Wait for the run on this worker to finish and return its checkpoint dir."""
        self.join()
        return self.outcome


class TrainSlot(Slot[str]):
    """One training slot: ``start`` launches a session, ``pause``/``result`` control it.

    A ``None`` device lets openLLV pick the best available device and a
    ``None`` ``output_dir`` keeps its default checkpoint location.
    """

    def _spawn(
        self,
        model: str,
        dataset: str,
        root_dir: str,
        epochs: int,
        batch_size: int,
        lr: float,
        resize: int,
        device: str | None,
        output_dir: str | None,
    ) -> TrainWorker:
        return TrainWorker(
            _train,
            model,
            dataset,
            root_dir,
            epochs,
            batch_size,
            lr,
            resize,
            device,
            output_dir,
            name="openllv-train",
        )


__all__ = ["DownloadSlot", "DownloadWorker", "TrainSlot", "TrainWorker", "list_records"]
