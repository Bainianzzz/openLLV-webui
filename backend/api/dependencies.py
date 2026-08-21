from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session


def get_session(request: Request) -> Generator[Session, None, None]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_storage(request: Request):
    return request.app.state.storage


def get_supervisor(request: Request):
    return request.app.state.supervisor


def get_catalog_provider(request: Request):
    return request.app.state.catalog_provider


def get_dataset_downloads(request: Request) -> dict[str, str]:
    return request.app.state.dataset_downloads
