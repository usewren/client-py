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


# patch_schema field names: snake_case -> the API's camelCase
_SCHEMA_FIELDS = {
    "schema": "schema",
    "display_name": "displayName",
    "collection_type": "collectionType",
    "natural_key": "naturalKey",
    "list_columns": "listColumns",
    "indexes": "indexes",
}


def _patch_body(fields: Optional[dict[str, Any]], kwargs: dict[str, Any]) -> dict[str, Any]:
    merged = {**(fields or {}), **kwargs}
    # Unknown names pass through unchanged, so the server can reject them (400).
    return {_SCHEMA_FIELDS.get(k, k): v for k, v in merged.items()}


class CollectionsResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list(self) -> list[CollectionInfo]:
        data = self._http.request("GET", "/collections")
        return [_parse_collection_info(c) for c in data.get("collections", [])]

    def get_schema(self, collection: str) -> Schema:
        data = self._http.request("GET", f"/{collection}/_schema")
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
        data = self._http.request("PUT", f"/{collection}/_schema", body=body)
        return _parse_schema(data)

    def patch_schema(self, collection: str, fields: Optional[dict[str, Any]] = None, **kwargs: Any) -> Schema:
        """Change only the given schema settings (``schema``, ``display_name``,
        ``collection_type``, ``natural_key``, ``list_columns``, ``indexes``), as
        keyword arguments or a dict (snake_case or camelCase keys); ``None``
        clears a setting. Creates the schema if there is none. Setting a natural
        key registers it for existing documents (``keys_registered``)."""
        data = self._http.request("PATCH", f"/{collection}/_schema", document=_patch_body(fields, kwargs))
        return _parse_schema(data)

    def delete_schema(self, collection: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"/{collection}/_schema")  # type: ignore[return-value]

    def validate(
        self,
        collection: str,
        proposed_schema: Optional[dict[str, Any]] = None,
    ) -> ValidateSchemaResult:
        # Without a body the server validates against the stored schema
        body: Optional[dict[str, Any]] = {"schema": proposed_schema} if proposed_schema is not None else None
        data = self._http.request("POST", f"/{collection}/_schema/validate", body=body)
        return _parse_validate_schema_result(data)


class AsyncCollectionsResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list(self) -> list[CollectionInfo]:
        data = await self._http.request("GET", "/collections")
        return [_parse_collection_info(c) for c in data.get("collections", [])]

    async def get_schema(self, collection: str) -> Schema:
        data = await self._http.request("GET", f"/{collection}/_schema")
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
        data = await self._http.request("PUT", f"/{collection}/_schema", body=body)
        return _parse_schema(data)

    async def patch_schema(self, collection: str, fields: Optional[dict[str, Any]] = None, **kwargs: Any) -> Schema:
        """Change only the given schema settings (``schema``, ``display_name``,
        ``collection_type``, ``natural_key``, ``list_columns``, ``indexes``), as
        keyword arguments or a dict (snake_case or camelCase keys); ``None``
        clears a setting. Creates the schema if there is none. Setting a natural
        key registers it for existing documents (``keys_registered``)."""
        data = await self._http.request("PATCH", f"/{collection}/_schema", document=_patch_body(fields, kwargs))
        return _parse_schema(data)

    async def delete_schema(self, collection: str) -> dict[str, Any]:
        return await self._http.request("DELETE", f"/{collection}/_schema")  # type: ignore[return-value]

    async def validate(
        self,
        collection: str,
        proposed_schema: Optional[dict[str, Any]] = None,
    ) -> ValidateSchemaResult:
        # Without a body the server validates against the stored schema
        body: Optional[dict[str, Any]] = {"schema": proposed_schema} if proposed_schema is not None else None
        data = await self._http.request("POST", f"/{collection}/_schema/validate", body=body)
        return _parse_validate_schema_result(data)
