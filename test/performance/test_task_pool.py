"""Performance tests for ``inference.utils.TaskPool``."""

import time

import pytest

from inference.utils import TaskPool


def test_ten_one_second_tasks_finish_within_five_seconds() -> None:
    """A default pool runs 10 one-second tasks in parallel within 5s."""
    pool = TaskPool(max_workers=10)
    start = time.monotonic()
    try:
        futures = [pool.submit(time.sleep, 1) for _ in range(10)]
        for future in futures:
            future.result()
        elapsed = time.monotonic() - start
        assert elapsed < 5.0
    finally:
        pool.stop()


def test_overrun_task_times_out_with_error() -> None:
    """A 3s task on a pool with a 1s timeout fails with TimeoutError quickly."""
    pool = TaskPool(default_timeout=1)
    start = time.monotonic()
    try:
        with pytest.raises(TimeoutError):
            pool.execute(time.sleep, 3)
        elapsed = time.monotonic() - start
        assert elapsed < 3.0
    finally:
        pool.stop()
