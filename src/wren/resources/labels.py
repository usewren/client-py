from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _HttpClient


class LabelsResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def set(
        self,
        collection: str,
        id: str,
        label: str,
        version: Optional[int] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"label": label}
        if version is not None:
            body["version"] = version
        return self._http.request(  # type: ignore[return-value]
            "POST",
            f"/api/collections/{collection}/documents/{id}/labels",
            body=body,
        )


class AsyncLabelsResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def set(
        self,
        collection: str,
        id: str,
        label: str,
        version: Optional[int] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"label": label}
        if version is not None:
            body["version"] = version
        return await self._http.request(  # type: ignore[return-value]
            "POST",
            f"/api/collections/{collection}/documents/{id}/labels",
            body=body,
        )
