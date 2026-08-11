"""In-memory mocks for the database operations used by ``inference.enhance``."""

from collections.abc import Generator
from contextlib import contextmanager
from importlib import import_module
from unittest import mock

from .session import FakeSession, QuerySession


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
