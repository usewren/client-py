from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _enc, _HttpClient
from wren._types import (
    FullTree,
    TreeInfo,
    TreeNodeResult,
    TreePromoteResult,
    TreeRestoreResult,
    _parse_full_tree,
    _parse_tree_info,
    _parse_tree_node_result,
    _parse_tree_promote_result,
    _parse_tree_restore_result,
)


def _normalize_path(path: str) -> str:
    """Ensure the path starts with exactly one leading slash."""
    return "/" + path.lstrip("/")


class TreesResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list(self) -> list[TreeInfo]:
        data = self._http.request("GET", "/tree")
        return [_parse_tree_info(t) for t in data.get("trees", [])]

    def snapshot(self, tree_name: str) -> FullTree:
        data = self._http.request("GET", f"/tree/{_enc(tree_name)}", params={"full": "true"})
        return _parse_full_tree(data)

    def get_node(self, tree_name: str, path: str) -> TreeNodeResult:
        norm = _normalize_path(path)
        data = self._http.request("GET", f"/tree/{_enc(tree_name)}{norm}")
        return _parse_tree_node_result(data)

    def assign(self, tree_name: str, path: str, document_id: str) -> dict[str, Any]:
        norm = _normalize_path(path)
        return self._http.request(  # type: ignore[return-value]
            "PUT",
            f"/tree/{_enc(tree_name)}{norm}",
            body={"documentId": document_id},
        )

    def unassign(self, tree_name: str, path: str) -> dict[str, Any]:
        norm = _normalize_path(path)
        return self._http.request("DELETE", f"/tree/{_enc(tree_name)}{norm}")  # type: ignore[return-value]

    def promote(
        self, tree_name: str, *, label: Optional[str] = None, from_: Optional[str] = None
    ) -> TreePromoteResult:
        """Atomically point ``label`` (server default ``"published"``) at, for every
        document in the tree, the version carrying ``from_`` -- or its current
        version when ``from_`` is omitted. Documents without ``from_`` are left
        alone. One transaction: readers never see a half-promoted tree.

        Raises WrenNotFoundError if the tree is empty (or nothing carries
        ``from_``) and WrenForbiddenError if a collection isn't writable.
        """
        data = self._http.request(
            "POST", f"/tree/{_enc(tree_name)}/_promote", body={"label": label, "from": from_}
        )
        return _parse_tree_promote_result(data)

    def restore(self, tree_name: str, label: str) -> TreeRestoreResult:
        """Restore every document mounted in the tree (files included) to the
        version carrying ``label``, in one transaction -- e.g. back to a release
        made with :meth:`promote`. Raises WrenNotFoundError if nothing carries the
        label and WrenForbiddenError if a collection isn't writable."""
        data = self._http.request("POST", f"/tree/{_enc(tree_name)}/_restore", body={"label": label})
        return _parse_tree_restore_result(data)


class AsyncTreesResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list(self) -> list[TreeInfo]:
        data = await self._http.request("GET", "/tree")
        return [_parse_tree_info(t) for t in data.get("trees", [])]

    async def snapshot(self, tree_name: str) -> FullTree:
        data = await self._http.request("GET", f"/tree/{_enc(tree_name)}", params={"full": "true"})
        return _parse_full_tree(data)

    async def get_node(self, tree_name: str, path: str) -> TreeNodeResult:
        norm = _normalize_path(path)
        data = await self._http.request("GET", f"/tree/{_enc(tree_name)}{norm}")
        return _parse_tree_node_result(data)

    async def assign(self, tree_name: str, path: str, document_id: str) -> dict[str, Any]:
        norm = _normalize_path(path)
        return await self._http.request(  # type: ignore[return-value]
            "PUT",
            f"/tree/{_enc(tree_name)}{norm}",
            body={"documentId": document_id},
        )

    async def unassign(self, tree_name: str, path: str) -> dict[str, Any]:
        norm = _normalize_path(path)
        return await self._http.request("DELETE", f"/tree/{_enc(tree_name)}{norm}")  # type: ignore[return-value]

    async def promote(
        self, tree_name: str, *, label: Optional[str] = None, from_: Optional[str] = None
    ) -> TreePromoteResult:
        """Atomically point ``label`` (server default ``"published"``) at, for every
        document in the tree, the version carrying ``from_`` -- or its current
        version when ``from_`` is omitted. Documents without ``from_`` are left
        alone. One transaction: readers never see a half-promoted tree.

        Raises WrenNotFoundError if the tree is empty (or nothing carries
        ``from_``) and WrenForbiddenError if a collection isn't writable.
        """
        data = await self._http.request(
            "POST", f"/tree/{_enc(tree_name)}/_promote", body={"label": label, "from": from_}
        )
        return _parse_tree_promote_result(data)

    async def restore(self, tree_name: str, label: str) -> TreeRestoreResult:
        """Restore every document mounted in the tree (files included) to the
        version carrying ``label``, in one transaction -- e.g. back to a release
        made with :meth:`promote`. Raises WrenNotFoundError if nothing carries the
        label and WrenForbiddenError if a collection isn't writable."""
        data = await self._http.request("POST", f"/tree/{_enc(tree_name)}/_restore", body={"label": label})
        return _parse_tree_restore_result(data)
