from __future__ import annotations

from typing import Any, Union

from wren._http import _AsyncHttpClient, _enc, _HttpClient
from wren._types import DiffResult, _parse_diff_result

VersionRef = Union[int, str]


def _diff_params(v1: VersionRef, v2: VersionRef, deep: bool) -> dict[str, Any]:
    return {"v1": v1, "v2": v2, "deep": "true" if deep else None}


class DiffResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def compare(
        self, collection: str, id: str, v1: VersionRef, v2: VersionRef, *, deep: bool = False
    ) -> DiffResult:
        """Diff two versions of a document. ``v1``/``v2`` are version numbers or
        label names (the result carries the version numbers). ``deep=True`` reports
        changes inside nested objects and arrays instead of whole top-level fields."""
        data = self._http.request(
            "GET",
            f"/{collection}/{_enc(id)}/diff",
            params=_diff_params(v1, v2, deep),
        )
        return _parse_diff_result(data)


class AsyncDiffResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def compare(
        self, collection: str, id: str, v1: VersionRef, v2: VersionRef, *, deep: bool = False
    ) -> DiffResult:
        """Diff two versions of a document. ``v1``/``v2`` are version numbers or
        label names (the result carries the version numbers). ``deep=True`` reports
        changes inside nested objects and arrays instead of whole top-level fields."""
        data = await self._http.request(
            "GET",
            f"/{collection}/{_enc(id)}/diff",
            params=_diff_params(v1, v2, deep),
        )
        return _parse_diff_result(data)
