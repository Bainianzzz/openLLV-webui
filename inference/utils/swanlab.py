"""SwanLab utilities: resolve web URLs for the configured account."""

from __future__ import annotations

from swanlab import Api

from .config import config


def project_url() -> str:
    """Return the web URL of the configured SwanLab project overview page.

    Authenticates with ``config().swanlab_api_key`` through the SwanLab
    OpenAPI to resolve the account username, then builds
    ``https://swanlab.cn/@<username>/<project>/overview`` using the default
    cloud host and the project name from ``config().swanlab_project``.
    """
    api = Api(api_key=config().swanlab_api_key)
    return f"https://swanlab.cn/@{api.username}/{config().swanlab_project}/overview"


__all__ = ["project_url"]
