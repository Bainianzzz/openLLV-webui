from collections.abc import Callable, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from backend.db import create_all, get_engine, get_session_factory
from backend.workers import WorkerSupervisor

from .api import api_router, health_router
from .api.catalog import default_catalog_provider
from .api.errors import APIError, api_error_handler, internal_error_handler, validation_error_handler
from .api.storage import ManagedStorage
from .workers.events import apply_task_event


def create_app(
    *,
    session_factory=None,
    storage=None,
    storage_root: Path | str = Path("data"),
    supervisor=None,
    catalog_provider: Callable[[], dict] | None = None,
    dataset_downloads: Mapping[str, str] | None = None,
) -> FastAPI:
    owned_engine = None
    if supervisor is None:
        supervisor = WorkerSupervisor()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal owned_engine
        if app.state.session_factory is None:
            database_path = Path(storage_root) / "app.db"
            database_path.parent.mkdir(parents=True, exist_ok=True)
            owned_engine = get_engine(f"sqlite:///{database_path}")
            create_all(owned_engine)
            app.state.session_factory = get_session_factory(owned_engine)
        if app.state.storage is None:
            app.state.storage = ManagedStorage(Path(storage_root))
        app.state.shutting_down = False
        if hasattr(supervisor, "set_event_callback"):
            supervisor.set_event_callback(
                lambda event: apply_task_event(app.state.session_factory, app.state.storage, event)
            )
        supervisor.start()
        try:
            yield
        finally:
            app.state.shutting_down = True
            supervisor.shutdown()
            if owned_engine is not None:
                owned_engine.dispose()

    app = FastAPI(title="openLLV WebUI API", lifespan=lifespan)
    app.state.session_factory = session_factory
    app.state.storage = storage
    app.state.supervisor = supervisor
    app.state.catalog_provider = catalog_provider or default_catalog_provider
    app.state.dataset_downloads = dict(dataset_downloads or {})

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id") or f"req-{uuid4().hex}"
        response = await call_next(request)
        response.headers["x-request-id"] = request.state.request_id
        return response

    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, internal_error_handler)
    app.include_router(health_router)
    app.include_router(api_router)
    return app


app = create_app()


__all__ = ["app", "create_app"]
