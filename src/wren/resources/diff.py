from __future__ import annotations

from wren._http import _AsyncHttpClient, _HttpClient
from wren._types import DiffResult, _parse_diff_result


class DiffResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def compare(self, collection: str, id: str, v1: int, v2: int) -> DiffResult:
        data = self._http.request(
            "GET",
            f"/api/collections/{collection}/documents/{id}/diff",
            params={"v1": v1, "v2": v2},
        )
        return _parse_diff_result(data)


class AsyncDiffResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def compare(self, collection: str, id: str, v1: int, v2: int) -> DiffResult:
        data = await self._http.request(
            "GET",
            f"/api/collections/{collection}/documents/{id}/diff",
            params={"v1": v1, "v2": v2},
        )
        return _parse_diff_result(data)
