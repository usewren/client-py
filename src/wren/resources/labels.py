from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _enc, _HttpClient
from wren._types import LabelRemoved, _parse_label_removed


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
            f"/{collection}/{_enc(id)}/labels",
            body=body,
        )



    def remove(self, collection: str, id: str, label: str) -> LabelRemoved:
        """Remove a label from a document. Raises WrenNotFoundError if it doesn't carry it."""
        data = self._http.request("DELETE", f"/{collection}/{_enc(id)}/labels/{_enc(label)}")
        return _parse_label_removed(data)


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
            f"/{collection}/{_enc(id)}/labels",
            body=body,
        )

    async def remove(self, collection: str, id: str, label: str) -> LabelRemoved:
        """Remove a label from a document. Raises WrenNotFoundError if it doesn't carry it."""
        data = await self._http.request("DELETE", f"/{collection}/{_enc(id)}/labels/{_enc(label)}")
        return _parse_label_removed(data)
