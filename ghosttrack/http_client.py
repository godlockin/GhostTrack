"""Shared HTTP layer: connection pooling, timeouts, TTL response cache."""

from __future__ import annotations

import time

import requests
from requests.adapters import HTTPAdapter

DEFAULT_TIMEOUT = (5, 10)  # (connect, read) seconds
USER_AGENT = "GhostTrack/2.2 (+https://github.com/godlockin/GhostTrack)"


class CachedSession:
    """`requests.Session` wrapper with a small TTL cache keyed by (method, url).

    Only successful GET/HEAD responses are cached. External network stays
    behind one session so TCP/TLS connections are reused.
    """

    def __init__(
        self,
        session: requests.Session | None = None,
        ttl_seconds: int = 300,
        max_entries: int = 128,
    ) -> None:
        self._session = session or requests.Session()
        adapter = HTTPAdapter(pool_connections=16, pool_maxsize=16)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)
        self._session.headers.update({"User-Agent": USER_AGENT})
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._cache: dict[tuple[str, str], tuple[float, requests.Response]] = {}

    def request(
        self,
        method: str,
        url: str,
        *,
        timeout: tuple[int, int] = DEFAULT_TIMEOUT,
        use_cache: bool = True,
        stream: bool = False,
    ) -> requests.Response:
        key = (method.upper(), url)
        if use_cache:
            hit = self._cache_get(key)
            if hit is not None:
                return hit

        response = self._session.request(
            method, url, timeout=timeout, stream=stream, allow_redirects=True
        )

        if use_cache and response.status_code < 400 and not stream:
            self._cache_put(key, response)
        return response

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def head(self, url: str, **kwargs) -> requests.Response:
        return self.request("HEAD", url, **kwargs)

    def close(self) -> None:
        self._session.close()

    def _cache_get(self, key: tuple[str, str]) -> requests.Response | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        expires_at, response = entry
        if time.monotonic() > expires_at:
            self._cache.pop(key, None)
            return None
        return response

    def _cache_put(self, key: tuple[str, str], response: requests.Response) -> None:
        if len(self._cache) >= self._max_entries:
            oldest = next(iter(self._cache))
            self._cache.pop(oldest, None)
        self._cache[key] = (time.monotonic() + self._ttl, response)
