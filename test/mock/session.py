"""In-memory stand-in sessions that fake SQLAlchemy ``Session`` behavior."""

from typing import Any

from typing_extensions import Self

_SEARCH_FIELDS = ("method", "status", "input_path", "output_path", "error")


class FakeSession:
    """In-memory stand-in for a SQLAlchemy ``Session``."""

    def __init__(self) -> None:
        self.task: Any = None
        self.tasks: list[Any] = []
        self.commits = 0

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        return None

    def add(self, task) -> None:
        """Record the ORM task instance passed to ``session.add``.

        ``task`` stays the most recently added record, while ``tasks``
        accumulates every record so batch runs can be inspected.
        """
        self.task = task
        self.tasks.append(task)

    def commit(self) -> None:
        """Pretend to flush and commit, assigning a primary key."""
        self.commits += 1
        if self.task is not None and self.task.id is None:
            self.task.id = self.commits

    def get(self, model, task_id):
        """Return the recorded task so updates are visible to the test."""
        return self.task


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
