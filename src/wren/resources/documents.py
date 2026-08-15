from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _HttpClient
from wren._types import (
    DocumentList,
    DocumentPaths,
    DocumentResponse,
    _parse_document_list,
    _parse_document_paths,
    _parse_document_response,
)


class DocumentsResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list(
        self,
        collection: str,
        *,
        label: Optional[str] = None,
        filter: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        facets: Optional[str] = None,
        select: Optional[str] = None,
        where: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> DocumentList:
        params: dict[str, Any] = {
            "label": label,
            "filter": filter,
            "limit": limit,
            "cursor": cursor,
            "facets": facets,
            "select": select,
            "where": where,
            "depth": depth,
        }
        data = self._http.request("GET", f"/api/collections/{collection}/documents", params=params)
        return _parse_document_list(data)

    def get(
        self,
        collection: str,
        id: str,
        *,
        label: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> DocumentResponse:
        params: dict[str, Any] = {"label": label, "depth": depth}
        data = self._http.request("GET", f"/api/collections/{collection}/documents/{id}", params=params)
        return _parse_document_response(data)

    def create(self, collection: str, document_data: dict[str, Any]) -> DocumentResponse:
        data = self._http.request(
            "POST",
            f"/api/collections/{collection}/documents",
            body={"data": document_data},
        )
        return _parse_document_response(data)

    def update(self, collection: str, id: str, document_data: dict[str, Any]) -> DocumentResponse:
        data = self._http.request(
            "PUT",
            f"/api/collections/{collection}/documents/{id}",
            body={"data": document_data},
        )
        return _parse_document_response(data)

    def delete(self, collection: str, id: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"/api/collections/{collection}/documents/{id}")  # type: ignore[return-value]

    def get_paths(self, collection: str, id: str) -> DocumentPaths:
        data = self._http.request("GET", f"/api/collections/{collection}/documents/{id}/paths")
        return _parse_document_paths(data)

    def get_by_key(
        self,
        collection: str,
        key_value: str,
        *,
        label: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> DocumentResponse:
        params: dict[str, Any] = {"label": label, "depth": depth}
        data = self._http.request("GET", f"/api/collections/{collection}/documents/key/{key_value}", params=params)
        return _parse_document_response(data)

    def upsert_by_key(
        self,
        collection: str,
        key_value: str,
        data: dict[str, Any],
    ) -> DocumentResponse:
        resp = self._http.request(
            "PUT",
            f"/api/collections/{collection}/documents/key/{key_value}",
            body={"data": data},
        )
        return _parse_document_response(resp)

    def delete_by_key(self, collection: str, key_value: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"/api/collections/{collection}/documents/key/{key_value}")  # type: ignore[return-value]


class AsyncDocumentsResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list(
        self,
        collection: str,
        *,
        label: Optional[str] = None,
        filter: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        facets: Optional[str] = None,
        select: Optional[str] = None,
        where: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> DocumentList:
        params: dict[str, Any] = {
            "label": label,
            "filter": filter,
            "limit": limit,
            "cursor": cursor,
            "facets": facets,
            "select": select,
            "where": where,
            "depth": depth,
        }
        data = await self._http.request("GET", f"/api/collections/{collection}/documents", params=params)
        return _parse_document_list(data)

    async def get(
        self,
        collection: str,
        id: str,
        *,
        label: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> DocumentResponse:
        params: dict[str, Any] = {"label": label, "depth": depth}
        data = await self._http.request("GET", f"/api/collections/{collection}/documents/{id}", params=params)
        return _parse_document_response(data)

    async def create(self, collection: str, document_data: dict[str, Any]) -> DocumentResponse:
        data = await self._http.request(
            "POST",
            f"/api/collections/{collection}/documents",
            body={"data": document_data},
        )
        return _parse_document_response(data)

    async def update(self, collection: str, id: str, document_data: dict[str, Any]) -> DocumentResponse:
        data = await self._http.request(
            "PUT",
            f"/api/collections/{collection}/documents/{id}",
            body={"data": document_data},
        )
        return _parse_document_response(data)

    async def delete(self, collection: str, id: str) -> dict[str, Any]:
        return await self._http.request("DELETE", f"/api/collections/{collection}/documents/{id}")  # type: ignore[return-value]

    async def get_paths(self, collection: str, id: str) -> DocumentPaths:
        data = await self._http.request("GET", f"/api/collections/{collection}/documents/{id}/paths")
        return _parse_document_paths(data)

    async def get_by_key(
        self,
        collection: str,
        key_value: str,
        *,
        label: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> DocumentResponse:
        params: dict[str, Any] = {"label": label, "depth": depth}
        data = await self._http.request("GET", f"/api/collections/{collection}/documents/key/{key_value}", params=params)
        return _parse_document_response(data)

    async def upsert_by_key(
        self,
        collection: str,
        key_value: str,
        data: dict[str, Any],
    ) -> DocumentResponse:
        resp = await self._http.request(
            "PUT",
            f"/api/collections/{collection}/documents/key/{key_value}",
            body={"data": data},
        )
        return _parse_document_response(resp)

    async def delete_by_key(self, collection: str, key_value: str) -> dict[str, Any]:
        return await self._http.request("DELETE", f"/api/collections/{collection}/documents/key/{key_value}")  # type: ignore[return-value]
