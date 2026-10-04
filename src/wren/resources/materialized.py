from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _enc, _HttpClient
from wren._types import (
    MaterializedQuery,
    MaterializedResult,
    _parse_materialized_query,
    _parse_materialized_result,
)


class MaterializedResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list(self, collection: str) -> list[MaterializedQuery]:
        data = self._http.request("GET", f"/{collection}/_materialized")
        return [_parse_materialized_query(m) for m in data.get("materialized", [])]

    def get(self, collection: str, name: str) -> MaterializedResult:
        data = self._http.request("GET", f"/{collection}/_materialized/{_enc(name)}")
        return _parse_materialized_result(data)

    def set(
        self,
        collection: str,
        name: str,
        query: dict[str, Any],
        refresh_on: str = "write",
    ) -> MaterializedQuery:
        body: dict[str, Any] = {
            "query": query,
            "refreshOn": refresh_on,
        }
        data = self._http.request("PUT", f"/{collection}/_materialized/{_enc(name)}", body=body)
        return _parse_materialized_query(data)

    def delete(self, collection: str, name: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"/{collection}/_materialized/{_enc(name)}")  # type: ignore[return-value]


class AsyncMaterializedResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list(self, collection: str) -> list[MaterializedQuery]:
        data = await self._http.request("GET", f"/{collection}/_materialized")
        return [_parse_materialized_query(m) for m in data.get("materialized", [])]

    async def get(self, collection: str, name: str) -> MaterializedResult:
        data = await self._http.request("GET", f"/{collection}/_materialized/{_enc(name)}")
        return _parse_materialized_result(data)

    async def set(
        self,
        collection: str,
        name: str,
        query: dict[str, Any],
        refresh_on: str = "write",
    ) -> MaterializedQuery:
        body: dict[str, Any] = {
            "query": query,
            "refreshOn": refresh_on,
        }
        data = await self._http.request("PUT", f"/{collection}/_materialized/{_enc(name)}", body=body)
        return _parse_materialized_query(data)

    async def delete(self, collection: str, name: str) -> dict[str, Any]:
        return await self._http.request("DELETE", f"/{collection}/_materialized/{_enc(name)}")  # type: ignore[return-value]
