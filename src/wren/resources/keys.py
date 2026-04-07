from __future__ import annotations

from typing import Any

from wren._http import _AsyncHttpClient, _HttpClient
from wren._types import ApiKey, ApiKeyCreated, _parse_api_key, _parse_api_key_created


class KeysResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list(self) -> list[ApiKey]:
        data = self._http.request("GET", "/keys")
        return [_parse_api_key(k) for k in data.get("keys", [])]

    def create(self, name: str) -> ApiKeyCreated:
        data = self._http.request("POST", "/keys", body={"name": name})
        return _parse_api_key_created(data)

    def revoke(self, id: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"/keys/{id}")  # type: ignore[return-value]


class AsyncKeysResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list(self) -> list[ApiKey]:
        data = await self._http.request("GET", "/keys")
        return [_parse_api_key(k) for k in data.get("keys", [])]

    async def create(self, name: str) -> ApiKeyCreated:
        data = await self._http.request("POST", "/keys", body={"name": name})
        return _parse_api_key_created(data)

    async def revoke(self, id: str) -> dict[str, Any]:
        return await self._http.request("DELETE", f"/keys/{id}")  # type: ignore[return-value]
