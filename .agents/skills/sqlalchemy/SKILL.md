---
name: sqlalchemy
description: SQLAlchemy 2.x usage for database connections and basic CRUD in this project, following Gradio's official "Connecting to a Database" guide. Use when creating engines, reading database content into pandas DataFrames for Gradio components, defining ORM models, or writing create/read/update/delete queries.
---

# SQLAlchemy: Database Connection and Basic CRUD

Reference for connecting to a database and performing basic CRUD with SQLAlchemy (2.x style) in this project. The Gradio integration pattern follows the official guide at https://gradio.app/guides/connecting-to-a-database.

## Dependency Status

`sqlalchemy` is **not yet a project dependency**. Before writing any code that imports it:

1. Add it with `uv add sqlalchemy` plus a database driver (e.g. `uv add "psycopg[binary]"` for PostgreSQL, `uv add pymysql` for MySQL; SQLite needs no extra driver).
2. Per project rules, adding a dependency must be reported to the user — do not add it silently.

## 1. Engine and Connection

Create one engine per application and reuse it. The engine is a connection-pooled singleton; do not create one per request.

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg://user:password@localhost:5432/dbname",
    pool_size=5,
    max_overflow=10,
    echo=False,  # set True to log generated SQL for debugging
)
```

Connection URL formats:

| Database           | URL                                               |
| ------------------ | ------------------------------------------------- |
| SQLite (relative)  | `sqlite:///data/app.db`                           |
| SQLite (absolute)  | `sqlite:////absolute/path/app.db`                 |
| SQLite (in-memory) | `sqlite:///:memory:`                              |
| PostgreSQL         | `postgresql+psycopg://user:pass@host:5432/dbname` |
| MySQL              | `mysql+pymysql://user:pass@host:3306/dbname`      |

## 2. Session Management

Sessions are cheap; create one per request/operation. Never share a session across threads.

```python
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Preferred: context manager commits on success, rolls back on exception
with SessionLocal() as session:
    ...
```

- `expire_on_commit=False` keeps loaded attributes usable after `commit()` without a refresh.
- The context manager rolls back uncommitted changes when the `with` block raises — there is no need to call `rollback()` manually in that path.

## 3. Gradio Integration (official guide pattern)

This project is a Gradio webui, so the primary use of SQLAlchemy is to pull database content into pandas DataFrames and hand them to Gradio components. Create the engine once at module level and run queries inside event handlers or render callbacks.

SQLite example, straight from the guide:

```python
from sqlalchemy import create_engine
import pandas as pd
import gradio as gr

engine = create_engine("sqlite:///your_database.db")

with gr.Blocks() as demo:
    gr.LinePlot(
        pd.read_sql_query("SELECT time, price FROM flight_info;", engine),
        x="time",
        y="price",
    )
```

Interactive filters build the query inside the handler:

```python
with gr.Blocks() as demo:
    origin = gr.Dropdown(["DFW", "DAL", "HOU"], value="DFW", label="Origin")

    gr.LinePlot(
        lambda origin: pd.read_sql_query(
            "SELECT time, price FROM flight_info WHERE origin = ?",
            engine,
            params=(origin,),
        ),
        inputs=origin,
        x="time",
        y="price",
    )
```

For PostgreSQL, MySQL, Oracle, or other databases, only the engine URL changes:

```python
engine = create_engine("postgresql://username:password@host:port/database_name")
engine = create_engine("mysql://username:password@host:port/database_name")
engine = create_engine("oracle://username:password@host:port/database_name")
```

Notes:

- The guide renders query results with `pd.read_sql_query(sql, engine)`; the result is a DataFrame usable directly by Gradio plot and data components.
- When user input (e.g. a Dropdown value) is embedded in SQL, prefer parameterized queries (`params=`) over f-string interpolation to avoid injection.
- Reference: https://gradio.app/guides/connecting-to-a-database

## 4. Declarative Models

Use the SQLAlchemy 2.x `Mapped`/`mapped_column` style. The project requires Python >= 3.10, so `X | None` unions are fine.

```python
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    age: Mapped[int | None]  # nullable column, no explicit type needed
```

Create tables (development only — prefer a migration tool such as Alembic for production):

```python
Base.metadata.create_all(engine)
```

## 5. CRUD Operations

### Create

```python
with SessionLocal() as session:
    user = User(name="alice", age=30)
    session.add(user)
    session.commit()          # persists the transaction
    session.refresh(user)     # loads server-generated values such as id
```

### Read

```python
from sqlalchemy import select

with SessionLocal() as session:
    stmt = select(User).where(User.name == "alice")
    user = session.scalar(stmt)              # single row or None
    # user = session.scalar_one(stmt)        # raises when 0 or >1 rows
    # users = session.scalars(stmt).all()    # list of rows

    # ordering and pagination
    stmt = select(User).order_by(User.id.desc()).limit(10).offset(0)
```

### Update

```python
with SessionLocal() as session:
    user = session.scalar(select(User).where(User.name == "alice"))
    if user:
        user.age = 31
        session.commit()
```

Bulk update without loading rows:

```python
from sqlalchemy import update

with SessionLocal() as session:
    session.execute(update(User).where(User.age < 18).values(age=0))
    session.commit()
```

### Delete

```python
from sqlalchemy import delete

with SessionLocal() as session:
    session.execute(delete(User).where(User.name == "bob"))
    session.commit()
```

Or delete a loaded object:

```python
with SessionLocal() as session:
    user = session.scalar(select(User).where(User.id == 1))
    if user:
        session.delete(user)
        session.commit()
```

## 6. Transactions

- `session.commit()` persists the current transaction; `session.flush()` sends SQL but keeps the transaction open.
- Read-only work needs no commit.
- Wrap multiple writes in one `with SessionLocal() as session:` block so they commit or roll back together.

## 7. Project Conventions

- Trust the ORM and driver return values — do not add redundant validation logic.
- Import paths: relative within the same package; absolute from the project root across packages.
- Python environment is managed with `uv`; tests use `unittest`.
