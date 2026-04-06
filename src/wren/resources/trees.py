from __future__ import annotations

from typing import Any

from wren._http import _AsyncHttpClient, _HttpClient
from wren._types import (
    FullTree,
    TreeInfo,
    TreeNodeResult,
    _parse_full_tree,
    _parse_tree_info,
    _parse_tree_node_result,
)


def _normalize_path(path: str) -> str:
    """Ensure the path starts with exactly one leading slash."""
    return "/" + path.lstrip("/")


class TreesResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list(self) -> list[TreeInfo]:
        data = self._http.request("GET", "/api/trees")
        return [_parse_tree_info(t) for t in data.get("trees", [])]

    def snapshot(self, tree_name: str) -> FullTree:
        data = self._http.request("GET", f"/api/tree/{tree_name}", params={"full": "true"})
        return _parse_full_tree(data)

    def get_node(self, tree_name: str, path: str) -> TreeNodeResult:
        norm = _normalize_path(path)
        data = self._http.request("GET", f"/api/tree/{tree_name}{norm}")
        return _parse_tree_node_result(data)

    def assign(self, tree_name: str, path: str, document_id: str) -> dict[str, Any]:
        norm = _normalize_path(path)
        return self._http.request(  # type: ignore[return-value]
            "PUT",
            f"/api/tree/{tree_name}{norm}",
            body={"documentId": document_id},
        )

    def unassign(self, tree_name: str, path: str) -> dict[str, Any]:
        norm = _normalize_path(path)
        return self._http.request("DELETE", f"/api/tree/{tree_name}{norm}")  # type: ignore[return-value]


class AsyncTreesResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list(self) -> list[TreeInfo]:
        data = await self._http.request("GET", "/api/trees")
        return [_parse_tree_info(t) for t in data.get("trees", [])]

    async def snapshot(self, tree_name: str) -> FullTree:
        data = await self._http.request("GET", f"/api/tree/{tree_name}", params={"full": "true"})
        return _parse_full_tree(data)

    async def get_node(self, tree_name: str, path: str) -> TreeNodeResult:
        norm = _normalize_path(path)
        data = await self._http.request("GET", f"/api/tree/{tree_name}{norm}")
        return _parse_tree_node_result(data)

    async def assign(self, tree_name: str, path: str, document_id: str) -> dict[str, Any]:
        norm = _normalize_path(path)
        return await self._http.request(  # type: ignore[return-value]
            "PUT",
            f"/api/tree/{tree_name}{norm}",
            body={"documentId": document_id},
        )

    async def unassign(self, tree_name: str, path: str) -> dict[str, Any]:
        norm = _normalize_path(path)
        return await self._http.request("DELETE", f"/api/tree/{tree_name}{norm}")  # type: ignore[return-value]
