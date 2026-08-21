from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base
from backend.main import create_app


class FakeSupervisor:
    def __init__(self):
        self.commands = []
        self.cancelled = []
        self.started = False

    def start(self):
        self.started = True

    def submit(self, command):
        self.commands.append(command)

    def cancel(self, task_id, kind):
        self.cancelled.append((task_id, kind))
        return True

    def worker_states(self):
        return {
            "enhancement": "idle",
            "training": "idle",
            "dataset_download": "idle",
        }

    def shutdown(self):
        self.started = False


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    engine.dispose()


@pytest.fixture
def supervisor():
    return FakeSupervisor()


@pytest.fixture
def client(tmp_path: Path, session_factory, supervisor):
    app = create_app(
        session_factory=session_factory,
        storage_root=tmp_path,
        supervisor=supervisor,
        catalog_provider=lambda: {
            "algorithms": [{"name": "Gamma", "aliases": ["gamma"]}],
            "models": [{"name": "ZeroDCE", "aliases": ["zero_dce"]}],
            "datasets": [{"name": "CommonDataset", "aliases": []}],
        },
        dataset_downloads={"LOLv1": "example/lolv1"},
    )
    with TestClient(app) as test_client:
        yield test_client
