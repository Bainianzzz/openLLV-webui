"""Tests for the dataset download service and its stop behaviour."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from inference.train.download import download_dataset, stop_download
from inference.utils import DownloadCancelled
from test.mock import mock_hf_download


def test_download_starts_and_can_be_stopped(tmp_path) -> None:
    """A download starts, keeps running, and stops on request."""
    with (
        mock_hf_download(datasets_dir=tmp_path) as started,
        ThreadPoolExecutor(max_workers=1) as pool,
    ):
        future = pool.submit(download_dataset, "user/lolv1")
        assert started.wait(5)  # the fake 20s download has begun
        assert not future.done()  # it is still running
        stop_download()
        with pytest.raises(DownloadCancelled):
            future.result(timeout=10)


def test_stop_before_download_is_cleared_on_next_run(tmp_path) -> None:
    """A stop requested outside a download does not cancel the following run."""
    stop_download()
    with (
        mock_hf_download(datasets_dir=tmp_path) as started,
        ThreadPoolExecutor(max_workers=1) as pool,
    ):
        future = pool.submit(download_dataset, "user/lolv1")
        assert started.wait(5)  # the flag was reset, the download starts
        stop_download()
        with pytest.raises(DownloadCancelled):
            future.result(timeout=10)
