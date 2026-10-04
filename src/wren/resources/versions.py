from __future__ import annotations

from typing import Any

from wren._http import _AsyncHttpClient, _enc, _HttpClient
from wren._types import (
    DocumentResponse,
    VersionList,
    _parse_document_response,
    _parse_version_list,
)


class VersionsResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list(self, collection: str, id: str) -> VersionList:
        data = self._http.request("GET", f"/{collection}/{_enc(id)}/versions")
        return _parse_version_list(data)

    def get(self, collection: str, id: str, version: int) -> DocumentResponse:
        data = self._http.request("GET", f"/{collection}/{_enc(id)}/versions/{version}")
        return _parse_document_response(data)

    def rollback(self, collection: str, id: str, version: int) -> dict[str, Any]:
        return self._http.request(  # type: ignore[return-value]
            "POST",
            f"/{collection}/{_enc(id)}/rollback/{version}",
        )


class AsyncVersionsResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list(self, collection: str, id: str) -> VersionList:
        data = await self._http.request("GET", f"/{collection}/{_enc(id)}/versions")
        return _parse_version_list(data)

    async def get(self, collection: str, id: str, version: int) -> DocumentResponse:
        data = await self._http.request(
            "GET", f"/{collection}/{_enc(id)}/versions/{version}"
        )
        return _parse_document_response(data)

    async def rollback(self, collection: str, id: str, version: int) -> dict[str, Any]:
        return await self._http.request(  # type: ignore[return-value]
            "POST",
            f"/{collection}/{_enc(id)}/rollback/{version}",
        )
