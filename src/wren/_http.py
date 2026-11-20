from __future__ import annotations

from typing import Any, Optional, Union
from urllib.parse import quote

import httpx

from wren._errors import (
    WrenError,
    WrenForbiddenError,
    WrenNotFoundError,
    WrenUnauthorizedError,
    WrenValidationError,
    WrenVersionMismatchError,
)

# A multipart file part: (filename, content, content type)
FilePart = tuple[str, Any, str]


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
    if status == 412:
        raise WrenVersionMismatchError(body)
    if status == 422:
        # Schema violations carry a list of messages; an invalid schema carries one string.
        raw = body.get("details", []) if isinstance(body, dict) else []
        details: list[str] = [raw] if isinstance(raw, str) else [str(d) for d in raw]
        raise WrenValidationError(body, details)
    raise WrenError(status, body, message)


def _enc(value: str) -> str:
    """URL-encode one path segment (ids, natural keys, names)."""
    return quote(value, safe="")


def _condition(if_version: Optional[Union[int, str]]) -> dict[str, str]:
    """The ``If-Match`` header for a conditional write: an int is the version the
    document must be at (0 = must not exist yet), ``"*"`` means it must exist."""
    if if_version is None:
        return {}
    if if_version == "*":
        return {"If-Match": "*"}
    if isinstance(if_version, bool) or not isinstance(if_version, int):
        raise TypeError('if_version must be an int or "*"')
    return {"If-Match": f'"{if_version}"'}


def _filter_none(d: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if d is None:
        return None
    return {k: v for k, v in d.items() if v is not None}


def _handle(response: httpx.Response, raw: bool) -> Any:
    if raw and response.status_code < 400:
        return response.content
    try:
        data: Any = response.json()
    except Exception:
        data = response.text
    _raise_for_status(response.status_code, data)
    return data


class _HttpClient:
    """Synchronous HTTP client backed by ``httpx.Client``."""

    def __init__(self, base_url: str, *, api_key: Optional[str] = None) -> None:
        self._base_url = base_url.rstrip("/")
        # No default Content-Type: httpx sets it per request (JSON or multipart).
        headers: dict[str, str] = {"Accept": "application/json"}
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
        document: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        files: Optional[dict[str, FilePart]] = None,
        raw: bool = False,
    ) -> Any:
        """Send a request and return the parsed JSON body (or the bytes if ``raw``).

        ``files`` sends a multipart form instead of a JSON body.
        """
        url = f"{self._base_url}/api/v1{path}"
        filtered_params = _filter_none(params)
        # A document is user data and is sent as-is; None-valued options are
        # dropped from every other body.
        filtered_body = document if document is not None else _filter_none(body)

        response = self._client.request(
            method,
            url,
            json=None if files is not None else filtered_body,
            files=files,
            params=filtered_params,
            headers=headers,
        )
        return _handle(response, raw)

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
        # No default Content-Type: httpx sets it per request (JSON or multipart).
        headers: dict[str, str] = {"Accept": "application/json"}
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
        document: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        files: Optional[dict[str, FilePart]] = None,
        raw: bool = False,
    ) -> Any:
        """Send a request and return the parsed JSON body (or the bytes if ``raw``).

        ``files`` sends a multipart form instead of a JSON body.
        """
        url = f"{self._base_url}/api/v1{path}"
        filtered_params = _filter_none(params)
        # A document is user data and is sent as-is; None-valued options are
        # dropped from every other body.
        filtered_body = document if document is not None else _filter_none(body)

        response = await self._client.request(
            method,
            url,
            json=None if files is not None else filtered_body,
            files=files,
            params=filtered_params,
            headers=headers,
        )
        return _handle(response, raw)

    # ------------------------------------------------------------------
    # Context manager / lifecycle
    # ------------------------------------------------------------------

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "_AsyncHttpClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
