from __future__ import annotations

from typing import Any

from wren._http import _AsyncHttpClient, _HttpClient
from wren._types import Member, _parse_member


class MembersResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list(self) -> list[Member]:
        data = self._http.request("GET", "/api/members")
        return [_parse_member(m) for m in data.get("members", [])]

    def remove(self, member_id: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"/api/members/{member_id}")  # type: ignore[return-value]


class AsyncMembersResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list(self) -> list[Member]:
        data = await self._http.request("GET", "/api/members")
        return [_parse_member(m) for m in data.get("members", [])]

    async def remove(self, member_id: str) -> dict[str, Any]:
        return await self._http.request("DELETE", f"/api/members/{member_id}")  # type: ignore[return-value]
