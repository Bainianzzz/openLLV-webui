"""SwanLab utilities: resolve web URLs for the configured account."""

from __future__ import annotations

from swanlab import Api

from .config import config


def project_url() -> str:
    """Return the web URL of the configured SwanLab project overview page.

    Authenticates with ``config().swanlab_api_key`` through the SwanLab
    OpenAPI to resolve the account username, then builds
    ``<web-host>/@<username>/<project>/overview`` using the web host resolved
    from the current SwanLab settings and the project name from
    ``config().swanlab_project``.
    """
    api = Api(api_key=config().swanlab_api_key)
    # The web host lives on the authenticated client's context, mirroring the
    # SDK's own ``_build_web_url`` so self-hosted instances are covered.
    return f"{api._ctx.web_host}/@{api.username}/{config().swanlab_project}/overview"


__all__ = ["project_url"]
