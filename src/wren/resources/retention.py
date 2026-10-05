"""Version retention policies (org owner or admin).

The target is a collection name, or ``"*"`` for the org default. A version is
removed if any rule of its collection's policy says so; a document's current
version and every labeled version are always kept.
"""

from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _enc, _HttpClient
from wren._types import (
    RetentionOverview,
    RetentionPolicy,
    RetentionResult,
    _parse_retention_overview,
    _parse_retention_policy,
    _parse_retention_result,
)


def _rules(
    labeled_only: Optional[bool],
    max_versions: Optional[int],
    max_age_days: Optional[int],
    after_label: Optional[str],
) -> dict[str, Any]:
    return {
        "labeledOnly": labeled_only,
        "maxVersions": max_versions,
        "maxAgeDays": max_age_days,
        "afterLabel": after_label,
    }


def _proposed(rules: dict[str, Any]) -> Optional[dict[str, Any]]:
    """The rules to preview, or None (no body) to preview the saved policy."""
    return rules if any(v is not None for v in rules.values()) else None


class RetentionResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def get(self) -> RetentionOverview:
        """The org default, each collection's own policy and the last 20 runs."""
        return _parse_retention_overview(self._http.request("GET", "/retention"))

    def set(
        self,
        collection: str,
        *,
        labeled_only: bool = False,
        max_versions: Optional[int] = None,
        max_age_days: Optional[int] = None,
        after_label: Optional[str] = None,
    ) -> RetentionPolicy:
        """Replace the policy of ``collection`` (or ``"*"``). Without any rule the
        collection keeps everything, which exempts it from the org default."""
        body = _rules(labeled_only, max_versions, max_age_days, after_label)
        return _parse_retention_policy(self._http.request("PUT", f"/retention/{_enc(collection)}", body=body))

    def remove(self, collection: str) -> dict[str, Any]:
        """Remove a policy; the collection falls back to the org default."""
        return self._http.request("DELETE", f"/retention/{_enc(collection)}")  # type: ignore[no-any-return]

    def preview(
        self,
        collection: str,
        *,
        labeled_only: Optional[bool] = None,
        max_versions: Optional[int] = None,
        max_age_days: Optional[int] = None,
        after_label: Optional[str] = None,
    ) -> RetentionResult:
        """What the saved policy would remove, or the proposed one when any rule is
        given. Changes nothing. For ``"*"``, covers the collections without a
        policy of their own."""
        body = _proposed(_rules(labeled_only, max_versions, max_age_days, after_label))
        data = self._http.request("POST", f"/retention/{_enc(collection)}/_preview", body=body)
        return _parse_retention_result(data)

    def apply(self) -> RetentionResult:
        """Apply all of the org's policies now (they also run hourly)."""
        return _parse_retention_result(self._http.request("POST", "/retention/_apply"))


class AsyncRetentionResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def get(self) -> RetentionOverview:
        """The org default, each collection's own policy and the last 20 runs."""
        return _parse_retention_overview(await self._http.request("GET", "/retention"))

    async def set(
        self,
        collection: str,
        *,
        labeled_only: bool = False,
        max_versions: Optional[int] = None,
        max_age_days: Optional[int] = None,
        after_label: Optional[str] = None,
    ) -> RetentionPolicy:
        """Replace the policy of ``collection`` (or ``"*"``). Without any rule the
        collection keeps everything, which exempts it from the org default."""
        body = _rules(labeled_only, max_versions, max_age_days, after_label)
        return _parse_retention_policy(await self._http.request("PUT", f"/retention/{_enc(collection)}", body=body))

    async def remove(self, collection: str) -> dict[str, Any]:
        """Remove a policy; the collection falls back to the org default."""
        return await self._http.request("DELETE", f"/retention/{_enc(collection)}")  # type: ignore[no-any-return]

    async def preview(
        self,
        collection: str,
        *,
        labeled_only: Optional[bool] = None,
        max_versions: Optional[int] = None,
        max_age_days: Optional[int] = None,
        after_label: Optional[str] = None,
    ) -> RetentionResult:
        """What the saved policy would remove, or the proposed one when any rule is
        given. Changes nothing."""
        body = _proposed(_rules(labeled_only, max_versions, max_age_days, after_label))
        data = await self._http.request("POST", f"/retention/{_enc(collection)}/_preview", body=body)
        return _parse_retention_result(data)

    async def apply(self) -> RetentionResult:
        """Apply all of the org's policies now (they also run hourly)."""
        return _parse_retention_result(await self._http.request("POST", "/retention/_apply"))
