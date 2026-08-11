"""Background training runner: record the lifecycle and execute ``llv.train``."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import openLLV as llv

from inference import SessionLocal
from inference.model import TrainingTask


def run(
    model: str,
    dataset: str,
    root_dir: str,
    epochs: int,
    batch_size: int,
    lr: float,
    resize: int,
    device: str | None,
    output_dir: str | None,
) -> str:
    """Execute one training session, recording its lifecycle.

    Called from ``train.start`` on a background daemon thread. Inserts a
    ``TrainingTask`` (status ``running``), runs ``llv.train``, updates the
    record to ``success``/``failed``/``stopped``, and returns the final
    status message. ``output_dir`` selects where checkpoints are saved; a
    ``None`` value lets openLLV use its default location. The recorded
    ``checkpoint_dir`` is stored as an absolute path.
    """
    with SessionLocal() as session:
        task = TrainingTask(
            model=model,
            dataset=dataset,
            dataset_path=root_dir,
            epochs=epochs,
            batch_size=batch_size,
            lr=lr,
            resize=resize,
            device=device or "auto",
            status="running",
        )
        session.add(task)
        session.commit()
        task_id = task.id

    try:
        outcome = llv.train(
            model,
            root_dir=root_dir,
            epochs=epochs,
            batch_size=batch_size,
            lr=lr,
            resize=resize,
            device=device,
            output_dir=output_dir or None,
            # Packaged configs default to multiprocessing workers; spawning them
            # from this background thread re-runs the app's ``__main__`` and
            # fails with a ``'__main__'`` error on macOS. Load data in-process.
            num_workers=0,
        )
    except KeyboardInterrupt:
        status, message, error, checkpoint = (
            "stopped",
            "Training stopped.",
            None,
            None,
        )
    except Exception as exc:  # noqa: BLE001 - any trainer failure becomes a status message
        status, message, error, checkpoint = (
            "failed",
            f"Training failed: {exc}",
            str(exc),
            None,
        )
    else:
        status, message, error, checkpoint = (
            "success",
            f"Training finished. Checkpoint: {outcome['checkpoint_dir']}",
            None,
            # openLLV returns a CWD-relative path; store an absolute one so the
            # record stays valid no matter where the app is started from.
            str(Path(outcome["checkpoint_dir"]).resolve()),
        )

    with SessionLocal() as session:
        task = session.get(TrainingTask, task_id)
        if task is not None:
            task.status = status
            task.error = error
            task.checkpoint_dir = checkpoint
            task.finish_at = datetime.now(timezone.utc)
            session.commit()

    return message


__all__ = ["run"]
