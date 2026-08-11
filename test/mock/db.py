"""In-memory mocks for the database operations used by ``inference.enhance``."""

from collections.abc import Generator
from contextlib import contextmanager
from importlib import import_module
from unittest import mock

from .session import FakeSession, QuerySession


@contextmanager
def mock_db() -> Generator[FakeSession, None, None]:
    """Patch the ``SessionLocal`` used by the enhancement core with a fake session.

    The enhancement core (``_enhance``) lives in the ``inference.enhance.enhance``
    module, so the patch targets that module directly: the package-level
    ``enhance`` attribute is the public function, not the module.

    Yields the ``FakeSession`` so tests can inspect the recorded task
    (``session.task``) after running ``enhance``.
    """
    session = FakeSession()
    enhance_module = import_module("inference.enhance.enhance")
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
