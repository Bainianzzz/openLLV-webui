"""In-memory mocks for the database operations used by the inference services."""

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
def mock_train_db() -> Generator[FakeSession, None, None]:
    """Patch the ``SessionLocal`` used by the training core with a fake session.

    The training core (``_run``) lives in the ``inference.train.train`` module,
    so the patch targets that module directly: the package-level ``train``
    attribute is the service module, not the training function.

    Yields the ``FakeSession`` so tests can inspect the recorded task
    (``session.task``) after running ``start``/``pause``/``result``.
    """
    session = FakeSession()
    train_module = import_module("inference.train.train")
    with mock.patch.object(train_module, "SessionLocal", return_value=session):
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


@contextmanager
def mock_train_records_db(rows: list) -> Generator[QuerySession, None, None]:
    """Patch ``inference.train.records.SessionLocal`` with a fake session.

    ``session.scalars`` returns ``rows`` filtered by the training search
    fields (model/status/dataset/error), mirroring what ``list_records``
    queries against the real engine.

    Yields the ``QuerySession`` so tests can inspect it if needed.
    """
    session = QuerySession(rows, search_fields=("model", "status", "dataset", "error"))
    records_module = import_module("inference.train.records")
    with mock.patch.object(records_module, "SessionLocal", return_value=session):
        yield session
