from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _HttpClient
from wren._types import (
    Invite,
    InviteCreated,
    ReceivedInvite,
    _parse_invite,
    _parse_invite_created,
    _parse_received_invite,
)


class InvitesResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list_sent(self) -> list[Invite]:
        data = self._http.request("GET", "/api/invites")
        return [_parse_invite(i) for i in data.get("invites", [])]

    def create(self, email: str, role: Optional[str] = None) -> InviteCreated:
        body: dict[str, Any] = {"email": email}
        if role is not None:
            body["role"] = role
        data = self._http.request("POST", "/api/invites", body=body)
        return _parse_invite_created(data)

    def revoke(self, invite_id: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"/api/invites/{invite_id}")  # type: ignore[return-value]

    def list_received(self) -> list[ReceivedInvite]:
        data = self._http.request("GET", "/api/invites/received")
        return [_parse_received_invite(i) for i in data.get("invites", [])]

    def accept(self, token: str) -> dict[str, Any]:
        return self._http.request("POST", "/api/invites/accept", body={"token": token})  # type: ignore[return-value]

    def accept_by_id(self, invite_id: str) -> dict[str, Any]:
        return self._http.request("POST", f"/api/invites/{invite_id}/accept")  # type: ignore[return-value]


class AsyncInvitesResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list_sent(self) -> list[Invite]:
        data = await self._http.request("GET", "/api/invites")
        return [_parse_invite(i) for i in data.get("invites", [])]

    async def create(self, email: str, role: Optional[str] = None) -> InviteCreated:
        body: dict[str, Any] = {"email": email}
        if role is not None:
            body["role"] = role
        data = await self._http.request("POST", "/api/invites", body=body)
        return _parse_invite_created(data)

    async def revoke(self, invite_id: str) -> dict[str, Any]:
        return await self._http.request("DELETE", f"/api/invites/{invite_id}")  # type: ignore[return-value]

    async def list_received(self) -> list[ReceivedInvite]:
        data = await self._http.request("GET", "/api/invites/received")
        return [_parse_received_invite(i) for i in data.get("invites", [])]

    async def accept(self, token: str) -> dict[str, Any]:
        return await self._http.request("POST", "/api/invites/accept", body={"token": token})  # type: ignore[return-value]

    async def accept_by_id(self, invite_id: str) -> dict[str, Any]:
        return await self._http.request("POST", f"/api/invites/{invite_id}/accept")  # type: ignore[return-value]
