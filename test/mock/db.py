"""In-memory mocks for the database operations used by ``inference.enhance``."""

from collections.abc import Generator
from contextlib import contextmanager
from importlib import import_module
from typing import Any
from unittest import mock

from typing_extensions import Self


class FakeSession:
    """In-memory stand-in for a SQLAlchemy ``Session``."""

    def __init__(self) -> None:
        self.task: Any = None
        self.commits = 0

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        return None

    def add(self, task) -> None:
        """Record the ORM task instance passed to ``session.add``."""
        self.task = task

    def commit(self) -> None:
        """Pretend to flush and commit, assigning a primary key."""
        self.commits += 1
        if self.task is not None and self.task.id is None:
            self.task.id = self.commits

    def get(self, model, task_id):
        """Return the recorded task so updates are visible to the test."""
        return self.task


@contextmanager
def mock_db() -> Generator[FakeSession, None, None]:
    """Patch ``inference.enhance.SessionLocal`` with a fake in-memory session.

    The patch targets the module object directly: the ``inference.enhance``
    package attribute is shadowed by the ``enhance`` function, so a string
    patch target would resolve to the function instead of the module.

    Yields the ``FakeSession`` so tests can inspect the recorded task
    (``session.task``) after running ``enhance``.
    """
    session = FakeSession()
    enhance_module = import_module("inference.enhance")
    with mock.patch.object(enhance_module, "SessionLocal", return_value=session):
        yield session


class QuerySession(FakeSession):
    """In-memory session that returns preset model rows from ``scalars``."""

    def __init__(self, rows: list) -> None:
        super().__init__()
        self.rows = rows

    def scalars(self, stmt):
        """Return the preset rows, ignoring the select statement."""
        return iter(self.rows)


@contextmanager
def mock_records_db(rows: list) -> Generator[QuerySession, None, None]:
    """Patch ``inference.enhance.records.SessionLocal`` with a fake session.

    ``session.scalars`` returns ``rows`` unchanged so tests can verify the
    ``list_records`` row formatting without a real database.

    Yields the ``QuerySession`` so tests can inspect it if needed.
    """
    session = QuerySession(rows)
    records_module = import_module("inference.enhance.records")
    with mock.patch.object(records_module, "SessionLocal", return_value=session):
        yield session
