from __future__ import annotations

from typing import Any, Optional

import httpx

from wren._errors import (
    WrenError,
    WrenForbiddenError,
    WrenNotFoundError,
    WrenUnauthorizedError,
    WrenValidationError,
)


def _raise_for_status(status: int, body: Any) -> None:
    if status < 400:
        return
    if isinstance(body, dict):
        message: str = body.get("error", f"HTTP {status}")
    else:
        message = f"HTTP {status}"

    if status == 401:
        raise WrenUnauthorizedError(body)
    if status == 403:
        raise WrenForbiddenError(body)
    if status == 404:
        raise WrenNotFoundError(body)
    if status == 422:
        details: list[str] = body.get("details", []) if isinstance(body, dict) else []
        raise WrenValidationError(body, details)
    raise WrenError(status, body, message)


def _filter_none(d: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if d is None:
        return None
    return {k: v for k, v in d.items() if v is not None}


class _HttpClient:
    """Synchronous HTTP client backed by ``httpx.Client``."""

    def __init__(self, base_url: str, *, api_key: Optional[str] = None) -> None:
        self._base_url = base_url.rstrip("/")
        headers: dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
        if api_key is not None:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.Client(headers=headers)

    # ------------------------------------------------------------------
    # Core request
    # ------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        url = f"{self._base_url}/api/v1{path}"
        filtered_params = _filter_none(params)
        filtered_body = _filter_none(body)

        response = self._client.request(
            method,
            url,
            json=filtered_body,
            params=filtered_params,
        )

        try:
            data: Any = response.json()
        except Exception:
            data = response.text

        _raise_for_status(response.status_code, data)
        return data

    # ------------------------------------------------------------------
    # Context manager / lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "_HttpClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class _AsyncHttpClient:
    """Asynchronous HTTP client backed by ``httpx.AsyncClient``."""

    def __init__(self, base_url: str, *, api_key: Optional[str] = None) -> None:
        self._base_url = base_url.rstrip("/")
        headers: dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
        if api_key is not None:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(headers=headers)

    # ------------------------------------------------------------------
    # Core request
    # ------------------------------------------------------------------

    async def request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        url = f"{self._base_url}/api/v1{path}"
        filtered_params = _filter_none(params)
        filtered_body = _filter_none(body)

        response = await self._client.request(
            method,
            url,
            json=filtered_body,
            params=filtered_params,
        )

        try:
            data: Any = response.json()
        except Exception:
            data = response.text

        _raise_for_status(response.status_code, data)
        return data

    # ------------------------------------------------------------------
    # Context manager / lifecycle
    # ------------------------------------------------------------------

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "_AsyncHttpClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
