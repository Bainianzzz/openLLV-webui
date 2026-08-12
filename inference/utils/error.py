"""Project-specific exceptions raised by the inference services.

Custom errors live here so every service and UI layer shares one exception
set instead of each domain module defining its own.
"""

from __future__ import annotations


class DownloadCancelled(Exception):
    """Raised when a dataset download is stopped by the user."""
