"""Minimal HTTP with a real browser identity: enough to read product pages."""

from __future__ import annotations

import urllib.error
import urllib.request

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class HttpError(RuntimeError):
    """A fetch that could not deliver bytes worth parsing."""


def fetch(url: str, *, timeout_s: float = 8.0, attempts: int = 2) -> tuple[int, bytes]:
    """GET the URL, return (status, body). Retries transient failures once.

    Any single request's failure is the caller's to survive -- a sweep checks
    many items and one bad store must never end the sweep.
    """
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7"})
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            if error.code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
                last_error = error
                continue
            return error.code, error.read()
        except OSError as error:
            last_error = error
    raise HttpError(f"GET {url} failed: {last_error}")
