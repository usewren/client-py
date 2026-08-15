from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _HttpClient
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
    ) -> Webhook:
        body: dict[str, Any] = {
            "url": url,
            "events": events,
            "enabled": enabled,
        }
        data = self._http.request("PATCH", f"/webhooks/{id}", body=body)
        return _parse_webhook(data)

    def delete(self, id: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"/webhooks/{id}")  # type: ignore[return-value]

    def deliveries(self, id: str) -> list[WebhookDelivery]:
        data = self._http.request("GET", f"/webhooks/{id}/deliveries")
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
        return self._http.request("POST", f"/webhooks/{id}/replay", body=body)  # type: ignore[return-value]


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
    ) -> Webhook:
        body: dict[str, Any] = {
            "url": url,
            "events": events,
            "enabled": enabled,
        }
        data = await self._http.request("PATCH", f"/webhooks/{id}", body=body)
        return _parse_webhook(data)

    async def delete(self, id: str) -> dict[str, Any]:
        return await self._http.request("DELETE", f"/webhooks/{id}")  # type: ignore[return-value]

    async def deliveries(self, id: str) -> list[WebhookDelivery]:
        data = await self._http.request("GET", f"/webhooks/{id}/deliveries")
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
        return await self._http.request("POST", f"/webhooks/{id}/replay", body=body)  # type: ignore[return-value]
