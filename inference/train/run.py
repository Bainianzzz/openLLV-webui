"""Background training runner: record the lifecycle and execute ``llv.train``."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import openLLV as llv

from inference import SessionLocal, config
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
    status message. ``dataset`` is the registered dataset name passed to the
    trainer; ``output_dir`` selects where checkpoints are saved; a ``None``
    value lets openLLV use its default location. The recorded
    ``checkpoint_dir`` is stored as an absolute path. A run stopped with
    ``KeyboardInterrupt`` records the checkpoint dir only when weight files
    are found on disk. When
    ``config().swanlab_api_key`` is set, training runs through
    ``BatchSwanLabTrainer`` so the session is recorded in SwanLab under
    ``config().swanlab_project``; otherwise the plain ``llv.train`` path is
    used.
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
        if config().swanlab_api_key:
            from inference.train.monitor import BatchSwanLabTrainer

            outcome = BatchSwanLabTrainer(
                model,
                dataset=dataset,
                root_dir=root_dir,
                epochs=epochs,
                batch_size=batch_size,
                lr=lr,
                resize=resize,
                device=device,
                output_dir=output_dir or None,
                num_workers=0,
                swan_api_key=config().swanlab_api_key,
                swan_project=config().swanlab_project,
                swan_experiment=model,
            ).train()
        else:
            outcome = llv.train(
                model,
                dataset=dataset,
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
            _find_checkpoint_dir(model, dataset, output_dir),
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


def _find_checkpoint_dir(
    model: str, dataset: str, output_dir: str | None
) -> str | None:
    """Return the checkpoint output dir when an interrupted run left weights.

    A stopped run never returns the trainer's ``checkpoint_dir``, so the
    location is reconstructed from the layout openLLV uses: weights are
    written as ``*.pt`` under ``<output_dir>/checkpoints/`` and the recorded
    value is ``<output_dir>`` itself. A ``None`` ``output_dir`` means the
    openLLV default ``checkpoints/<Model>_<Dataset>``; ``None`` is returned
    when no weight file exists.
    """
    base = Path(output_dir) if output_dir else Path("checkpoints", f"{model}_{dataset}")
    weights = base / "checkpoints"
    if not any(weights.glob("*.pt")) and not any(weights.glob("*.pth")):
        return None
    return str(base.resolve())


__all__ = ["run"]
