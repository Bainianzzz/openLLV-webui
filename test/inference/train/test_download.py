"""Tests for the dataset download service and its stop behaviour."""

from __future__ import annotations

from inference.train.download import pause, result, start
from test.mock import mock_hf_download


def test_download_starts_and_can_be_stopped(tmp_path) -> None:
    """A download starts, keeps running, and stops on request."""
    with mock_hf_download(datasets_dir=tmp_path) as started:
        worker = start(None, "user/lolv1")
        assert worker is not None
        assert started.wait(5)  # the fake download has begun
        assert worker.is_alive()  # it is still running
        assert pause(worker) is True
        assert not worker.is_alive()
        assert worker.cancelled


def test_download_restarts_after_stop(tmp_path) -> None:
    """A new download can start on the slot once the previous one stopped."""
    with mock_hf_download(datasets_dir=tmp_path) as started:
        worker = start(None, "user/lolv1")
        assert worker is not None
        assert started.wait(5)
        assert pause(worker) is True
        assert start(worker, "user/lolv1") is not None


def test_download_without_worker() -> None:
    """``pause``/``result`` report when no download is in flight."""
    assert pause(None) is None
    assert result(None) is None
