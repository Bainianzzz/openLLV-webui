from pathlib import Path
from threading import Event

import pytest

from backend.workers.context import WorkerContext
from backend.workers.handlers.dataset_download import DatasetDownloadHandler


def make_context(output: Path, cancel_event: Event | None = None) -> WorkerContext:
    return WorkerContext(
        task_id="task-1",
        worker_kind="dataset_download",
        storage_paths={"output": output},
        cancel_event=cancel_event or Event(),
    )


def test_downloads_all_files_and_publishes_one_directory(tmp_path):
    downloads = []

    def download(repo_id, filename, destination):
        downloads.append((repo_id, filename))
        path = destination / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(filename)
        return path

    output = tmp_path / "dataset"
    outcome = DatasetDownloadHandler(
        list_files=lambda repo_id: ["train/a.txt", "README.md"],
        download_file=download,
    ).run(
        {"dataset_key": "demo", "repo_id": "org/demo", "overwrite": False},
        make_context(output),
    )

    assert downloads == [("org/demo", "train/a.txt"), ("org/demo", "README.md")]
    assert output.joinpath("train/a.txt").read_text() == "train/a.txt"
    assert outcome.publish == {"kind": "dataset", "path_type": "directory", "path": output}
    assert list(tmp_path.glob(".demo-*")) == []


def test_cancellation_between_files_leaves_no_output(tmp_path):
    cancel_event = Event()
    calls = 0

    def download(repo_id, filename, destination):
        nonlocal calls
        calls += 1
        path = destination / filename
        path.write_text(filename)
        cancel_event.set()
        return path

    output = tmp_path / "dataset"
    with pytest.raises(InterruptedError, match="cancelled"):
        DatasetDownloadHandler(
            list_files=lambda repo_id: ["one.txt", "two.txt"],
            download_file=download,
        ).run(
            {"dataset_key": "demo", "repo_id": "org/demo", "overwrite": False},
            make_context(output, cancel_event),
        )

    assert calls == 1
    assert not output.exists()
    assert list(tmp_path.glob(".demo-*")) == []


def test_download_failure_preserves_existing_output(tmp_path):
    output = tmp_path / "dataset"
    output.mkdir()
    output.joinpath("old.txt").write_text("old")

    def download(repo_id, filename, destination):
        destination.joinpath(filename).write_text("partial")
        raise RuntimeError("download failed")

    with pytest.raises(RuntimeError, match="download failed"):
        DatasetDownloadHandler(
            list_files=lambda repo_id: ["new.txt"],
            download_file=download,
        ).run(
            {"dataset_key": "demo", "repo_id": "org/demo", "overwrite": True},
            make_context(output),
        )

    assert output.joinpath("old.txt").read_text() == "old"
    assert not output.joinpath("new.txt").exists()
