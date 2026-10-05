from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _enc, _HttpClient
from wren._types import (
    Webhook,
    WebhookCreated,
    WebhookDelivery,
    _parse_webhook,
    _parse_webhook_created,
    _parse_webhook_delivery,
)


class WebhooksResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list(self) -> list[Webhook]:
        data = self._http.request("GET", "/webhooks")
        return [_parse_webhook(w) for w in data.get("webhooks", [])]

    def create(
        self,
        url: str,
        events: Optional[list[str]] = None,
    ) -> WebhookCreated:
        body: dict[str, Any] = {
            "url": url,
            "events": events,
        }
        data = self._http.request("POST", "/webhooks", body=body)
        return _parse_webhook_created(data)

    def update(
        self,
        id: str,
        *,
        url: Optional[str] = None,
        events: Optional[list[str]] = None,
        enabled: Optional[bool] = None,
    ) -> dict[str, Any]:
        """Update a webhook. The server answers ``{"id": ..., "updated": True}``,
        not the webhook itself; call ``list()`` to read the new state."""
        body: dict[str, Any] = {
            "url": url,
            "events": events,
            "enabled": enabled,
        }
        return self._http.request("PUT", f"/webhooks/{_enc(id)}", body=body)  # type: ignore[return-value]

    def delete(self, id: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"/webhooks/{_enc(id)}")  # type: ignore[return-value]

    def deliveries(self, id: str) -> list[WebhookDelivery]:
        data = self._http.request("GET", f"/webhooks/{_enc(id)}/deliveries")
        return [_parse_webhook_delivery(d) for d in data.get("deliveries", [])]

    def replay(
        self,
        id: str,
        since: str,
        until: Optional[str] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "since": since,
            "until": until,
        }
        return self._http.request("POST", f"/webhooks/{_enc(id)}/replay", body=body)  # type: ignore[return-value]


class AsyncWebhooksResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list(self) -> list[Webhook]:
        data = await self._http.request("GET", "/webhooks")
        return [_parse_webhook(w) for w in data.get("webhooks", [])]

    async def create(
        self,
        url: str,
        events: Optional[list[str]] = None,
    ) -> WebhookCreated:
        body: dict[str, Any] = {
            "url": url,
            "events": events,
        }
        data = await self._http.request("POST", "/webhooks", body=body)
        return _parse_webhook_created(data)

    async def update(
        self,
        id: str,
        *,
        url: Optional[str] = None,
        events: Optional[list[str]] = None,
        enabled: Optional[bool] = None,
    ) -> dict[str, Any]:
        """Update a webhook. The server answers ``{"id": ..., "updated": True}``,
        not the webhook itself; call ``list()`` to read the new state."""
        body: dict[str, Any] = {
            "url": url,
            "events": events,
            "enabled": enabled,
        }
        return await self._http.request("PUT", f"/webhooks/{_enc(id)}", body=body)  # type: ignore[return-value]

    async def delete(self, id: str) -> dict[str, Any]:
        return await self._http.request("DELETE", f"/webhooks/{_enc(id)}")  # type: ignore[return-value]

    async def deliveries(self, id: str) -> list[WebhookDelivery]:
        data = await self._http.request("GET", f"/webhooks/{_enc(id)}/deliveries")
        return [_parse_webhook_delivery(d) for d in data.get("deliveries", [])]

    async def replay(
        self,
        id: str,
        since: str,
        until: Optional[str] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "since": since,
            "until": until,
        }
        return await self._http.request("POST", f"/webhooks/{_enc(id)}/replay", body=body)  # type: ignore[return-value]
