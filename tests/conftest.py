"""Shared fakes for tests — no network access."""

from __future__ import annotations

_UNSET = object()


class FakeResponse:
    def __init__(self, status_code: int = 200, json_data: object = _UNSET, text: str = ""):
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def json(self):
        if self._json is _UNSET:
            raise ValueError("not JSON")
        return self._json


class FakeRawSession:
    """Minimal stand-in for requests.Session used by CachedSession."""

    def __init__(self, responses: dict[str, FakeResponse]):
        self._responses = responses
        self.headers: dict[str, str] = {}

    def mount(self, *args):
        pass

    def request(self, method, url, timeout=None, stream=False, allow_redirects=True):
        return self._responses[url]

    def close(self):
        pass
