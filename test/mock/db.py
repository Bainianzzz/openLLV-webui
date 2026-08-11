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


_SEARCH_FIELDS = ("method", "status", "input_path", "output_path", "error")


class QuerySession(FakeSession):
    """In-memory session simulating ``scalars`` query semantics.

    Rows without an id get sequential auto-incremented ids on setup, then
    are ordered by ``id`` descending, filtered by the LIKE pattern in the
    statement's where clause, and truncated to the statement limit,
    mirroring what ``list_records`` queries against the real engine.
    """

    def __init__(self, rows: list) -> None:
        super().__init__()
        self.rows = rows
        self._assign_ids()

    def _assign_ids(self) -> None:
        """Give rows created without an id sequential primary keys."""
        next_id = (
            max((task.id for task in self.rows if task.id is not None), default=0) + 1
        )
        for task in self.rows:
            if task.id is None:
                task.id = next_id
                next_id += 1

    def scalars(self, stmt):
        rows = sorted(self.rows, key=lambda task: task.id, reverse=True)
        term = self._search_term(stmt)
        if term:
            rows = [row for row in rows if term.lower() in self._cells(row)]
        limit = stmt._limit_clause.value if stmt._limit_clause is not None else None
        if limit is not None:
            rows = rows[:limit]
        return iter(rows)

    @staticmethod
    def _search_term(stmt):
        """Extract the first LIKE pattern from the statement's where clauses."""
        for criterion in stmt._where_criteria:
            clauses = getattr(criterion, "clauses", None)
            if clauses is None:  # single-column where, not wrapped in or_()
                clauses = [criterion]
            for clause in clauses:
                pattern = getattr(getattr(clause, "right", None), "value", None)
                if isinstance(pattern, str):
                    return pattern.strip("%")
        return None

    @staticmethod
    def _cells(task) -> str:
        """Join the searchable field values of a task for matching."""
        values = (str(getattr(task, field, "") or "") for field in _SEARCH_FIELDS)
        return " ".join(values).lower()


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
