from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _HttpClient
from wren._types import (
    CollectionInfo,
    Schema,
    _parse_collection_info,
    _parse_schema,
)


class CollectionsResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list(self) -> list[CollectionInfo]:
        data = self._http.request("GET", "/api/collections")
        return [_parse_collection_info(c) for c in data.get("collections", [])]

    def get_schema(self, collection: str) -> Schema:
        data = self._http.request("GET", f"/api/collections/{collection}/schema")
        return _parse_schema(data)

    def set_schema(
        self,
        collection: str,
        *,
        schema: Optional[dict[str, Any]] = None,
        display_name: Optional[str] = None,
        collection_type: Optional[str] = None,
    ) -> Schema:
        body: dict[str, Any] = {
            "schema": schema,
            "displayName": display_name,
            "collectionType": collection_type,
        }
        data = self._http.request("PUT", f"/api/collections/{collection}/schema", body=body)
        return _parse_schema(data)

    def delete_schema(self, collection: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"/api/collections/{collection}/schema")  # type: ignore[return-value]


class AsyncCollectionsResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list(self) -> list[CollectionInfo]:
        data = await self._http.request("GET", "/api/collections")
        return [_parse_collection_info(c) for c in data.get("collections", [])]

    async def get_schema(self, collection: str) -> Schema:
        data = await self._http.request("GET", f"/api/collections/{collection}/schema")
        return _parse_schema(data)

    async def set_schema(
        self,
        collection: str,
        *,
        schema: Optional[dict[str, Any]] = None,
        display_name: Optional[str] = None,
        collection_type: Optional[str] = None,
    ) -> Schema:
        body: dict[str, Any] = {
            "schema": schema,
            "displayName": display_name,
            "collectionType": collection_type,
        }
        data = await self._http.request("PUT", f"/api/collections/{collection}/schema", body=body)
        return _parse_schema(data)

    async def delete_schema(self, collection: str) -> dict[str, Any]:
        return await self._http.request("DELETE", f"/api/collections/{collection}/schema")  # type: ignore[return-value]
