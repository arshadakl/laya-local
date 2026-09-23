"""Browser and URL actions.

Opens websites and performs web searches.
"""

from __future__ import annotations

import webbrowser
from typing import Any

import structlog

log = structlog.get_logger()

# Default search engine URL template
_DEFAULT_SEARCH_URL = "https://www.google.com/search?q={query}"


def open_url(target: str, **kwargs: Any) -> dict[str, Any]:
    """Open a URL in the default browser.

    Args:
        target: URL string (e.g., "https://github.com") or domain
                (e.g., "github.com").
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    # Add scheme if missing
    url = target
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    log.info("opening_url", url=url)

    try:
        webbrowser.open(url)
        return {
            "status": "success",
            "action": "open_url",
            "target": url,
            "message": f"Opened {url}",
        }
    except Exception as exc:
        log.error("url_open_failed", url=url, error=str(exc))
        return {
            "status": "error",
            "message": f"Failed to open URL: {exc}",
        }


def search_web(query: str, **kwargs: Any) -> dict[str, Any]:
    """Search the web using the default search engine.

    Args:
        query: Search query string.
        **kwargs: Additional arguments (unused).

    Returns:
        Dictionary with status and details.
    """
    url = _DEFAULT_SEARCH_URL.format(query=query)

    log.info("web_search", query=query, url=url)

    try:
        webbrowser.open(url)
        return {
            "status": "success",
            "action": "search",
            "target": query,
            "message": f"Searched for: {query}",
        }
    except Exception as exc:
        log.error("search_failed", query=query, error=str(exc))
        return {
            "status": "error",
            "message": f"Failed to search: {exc}",
        }
