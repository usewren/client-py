from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _HttpClient
from wren._types import (
    CollectionInfo,
    Schema,
    ValidateSchemaResult,
    _parse_collection_info,
    _parse_schema,
    _parse_validate_schema_result,
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
        natural_key: Optional[str] = None,
        list_columns: Optional[list[str]] = None,
        indexes: Optional[list[dict[str, Any]]] = None,
    ) -> Schema:
        body: dict[str, Any] = {
            "schema": schema,
            "displayName": display_name,
            "collectionType": collection_type,
            "naturalKey": natural_key,
            "listColumns": list_columns,
            "indexes": indexes,
        }
        data = self._http.request("PUT", f"/api/collections/{collection}/schema", body=body)
        return _parse_schema(data)

    def delete_schema(self, collection: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"/api/collections/{collection}/schema")  # type: ignore[return-value]

    def validate(
        self,
        collection: str,
        proposed_schema: Optional[dict[str, Any]] = None,
    ) -> ValidateSchemaResult:
        body: dict[str, Any] = {"schema": proposed_schema} if proposed_schema is not None else {}
        data = self._http.request("POST", f"/api/collections/{collection}/schema/validate", body=body)
        return _parse_validate_schema_result(data)


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
        natural_key: Optional[str] = None,
        list_columns: Optional[list[str]] = None,
        indexes: Optional[list[dict[str, Any]]] = None,
    ) -> Schema:
        body: dict[str, Any] = {
            "schema": schema,
            "displayName": display_name,
            "collectionType": collection_type,
            "naturalKey": natural_key,
            "listColumns": list_columns,
            "indexes": indexes,
        }
        data = await self._http.request("PUT", f"/api/collections/{collection}/schema", body=body)
        return _parse_schema(data)

    async def delete_schema(self, collection: str) -> dict[str, Any]:
        return await self._http.request("DELETE", f"/api/collections/{collection}/schema")  # type: ignore[return-value]

    async def validate(
        self,
        collection: str,
        proposed_schema: Optional[dict[str, Any]] = None,
    ) -> ValidateSchemaResult:
        body: dict[str, Any] = {"schema": proposed_schema} if proposed_schema is not None else {}
        data = await self._http.request("POST", f"/api/collections/{collection}/schema/validate", body=body)
        return _parse_validate_schema_result(data)
