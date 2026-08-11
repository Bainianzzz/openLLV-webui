"""In-memory database mocks and shared test fixtures.

- ``mock_db``: mock the enhance session so task writes are recorded in memory.
- ``mock_records_db``: mock the records session so queries return matching rows.
- ``mock_train_db``: mock the training session so run writes are recorded in memory.
- ``mock_train_records_db``: mock the training-records session so queries return matching rows.
- ``TEST_IMAGE``: shared tiny test photo used by tests that need an image.
"""

from pathlib import Path

from .db import mock_db, mock_records_db, mock_train_db, mock_train_records_db

TEST_IMAGE = str(Path(__file__).resolve().parents[1] / "assets" / "tiny.png")

__all__ = [
    "TEST_IMAGE",
    "mock_db",
    "mock_records_db",
    "mock_train_db",
    "mock_train_records_db",
]
