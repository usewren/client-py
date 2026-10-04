from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _HttpClient
from wren._types import QueryResult, _parse_query_result


class QueryResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def run(
        self,
        collection: str,
        *,
        where: Optional[str] = None,
        select: Optional[list[str]] = None,
        aggregate: Optional[dict[str, Any]] = None,
        label: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> QueryResult:
        # ``where`` is a filter expression, e.g. "category:news AND year>=2024"
        body: dict[str, Any] = {
            "where": where,
            "select": select,
            "aggregate": aggregate,
            "label": label,
            "limit": limit,
            "cursor": cursor,
        }
        data = self._http.request("POST", f"/{collection}/_query", body=body)
        return _parse_query_result(data)


class AsyncQueryResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def run(
        self,
        collection: str,
        *,
        where: Optional[str] = None,
        select: Optional[list[str]] = None,
        aggregate: Optional[dict[str, Any]] = None,
        label: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> QueryResult:
        # ``where`` is a filter expression, e.g. "category:news AND year>=2024"
        body: dict[str, Any] = {
            "where": where,
            "select": select,
            "aggregate": aggregate,
            "label": label,
            "limit": limit,
            "cursor": cursor,
        }
        data = await self._http.request("POST", f"/{collection}/_query", body=body)
        return _parse_query_result(data)
