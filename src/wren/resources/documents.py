from __future__ import annotations

from typing import Any, Optional, Union

from wren._http import _AsyncHttpClient, _condition, _enc, _HttpClient
from wren._types import (
    DocumentList,
    DocumentPaths,
    DocumentResponse,
    RestoreResult,
    UndeleteResult,
    _parse_document_list,
    _parse_document_paths,
    _parse_document_response,
    _parse_restore_result,
    _parse_undelete_result,
)

IfVersion = Optional[Union[int, str]]


def _write_options(if_version: IfVersion, force: bool = False) -> tuple[dict[str, Any], dict[str, str]]:
    return {"force": "true" if force else None}, _condition(if_version)


def _restore_body(label: str, delete_unlabeled: bool) -> dict[str, Any]:
    return {"label": label, "deleteUnlabeled": True if delete_unlabeled else None}


def _list_params(
    label: Optional[str],
    where: Optional[str],
    select: Optional[str],
    limit: Optional[int],
    offset: Optional[int],
    depth: Optional[int],
) -> dict[str, Any]:
    return {
        "label": label,
        "where": where,
        "select": select,
        "limit": limit,
        "offset": offset,
        "depth": depth,
    }


class DocumentsResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list(
        self,
        collection: str,
        *,
        label: Optional[str] = None,
        where: Optional[str] = None,
        select: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        depth: Optional[int] = None,
    ) -> DocumentList:
        """List documents, newest first.

        ``where`` is a filter expression such as ``"status:published"`` or
        ``"price>10"``; ``select`` is a comma-separated list of field paths.
        Page with ``limit`` (default 50, max 200) and ``offset``.
        """
        params = _list_params(label, where, select, limit, offset, depth)
        data = self._http.request("GET", f"/{collection}", params=params)
        return _parse_document_list(data)

    def get(
        self,
        collection: str,
        id: str,
        *,
        label: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> DocumentResponse:
        params: dict[str, Any] = {"label": label, "depth": depth}
        data = self._http.request("GET", f"/{collection}/{_enc(id)}", params=params)
        return _parse_document_response(data)

    def create(self, collection: str, document_data: dict[str, Any]) -> DocumentResponse:
        data = self._http.request("POST", f"/{collection}", document=document_data)
        return _parse_document_response(data)

    def update(
        self,
        collection: str,
        id: str,
        document_data: dict[str, Any],
        *,
        if_version: IfVersion = None,
        force: bool = False,
    ) -> DocumentResponse:
        """Write a new version. Sending the same data as the current version makes
        none (the response has ``unchanged=True``) unless ``force=True``.

        ``if_version`` makes the write conditional: an int is the version the
        document must be at, ``"*"`` only requires it to exist. On a mismatch
        :class:`~wren.WrenVersionMismatchError` is raised (with ``current_version``).
        """
        params, headers = _write_options(if_version, force)
        data = self._http.request(
            "PUT", f"/{collection}/{_enc(id)}", document=document_data, params=params, headers=headers
        )
        return _parse_document_response(data)

    def delete(self, collection: str, id: str, *, if_version: IfVersion = None) -> dict[str, Any]:
        return self._http.request(  # type: ignore[no-any-return]
            "DELETE", f"/{collection}/{_enc(id)}", headers=_condition(if_version)
        )

    def undelete(self, collection: str, id: str) -> UndeleteResult:
        """Bring back a deleted document with its history. Raises WrenNotFoundError
        if it isn't deleted, and a 409 WrenError if another document took its
        natural key meanwhile."""
        data = self._http.request("POST", f"/{collection}/{_enc(id)}/undelete")
        return _parse_undelete_result(data)

    def restore(self, collection: str, label: str, *, delete_unlabeled: bool = False) -> RestoreResult:
        """Restore every document of a collection to the version carrying ``label``,
        in one transaction: changed documents get the labeled content (as a new
        version), deleted ones come back, and with ``delete_unlabeled`` documents
        without the label are deleted. Raises WrenNotFoundError if no document
        carries the label."""
        data = self._http.request(
            "POST", f"/{collection}/_restore", body=_restore_body(label, delete_unlabeled)
        )
        return _parse_restore_result(data)

    def get_paths(self, collection: str, id: str) -> DocumentPaths:
        data = self._http.request("GET", f"/{collection}/{_enc(id)}/paths")
        return _parse_document_paths(data)

    def get_by_key(
        self,
        collection: str,
        key_value: str,
        *,
        label: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> DocumentResponse:
        params: dict[str, Any] = {"label": label, "depth": depth}
        data = self._http.request("GET", f"/{collection}/by-key/{_enc(key_value)}", params=params)
        return _parse_document_response(data)

    def upsert_by_key(
        self,
        collection: str,
        key_value: str,
        data: dict[str, Any],
        *,
        if_version: IfVersion = None,
        force: bool = False,
    ) -> DocumentResponse:
        """Create or update the document with this natural key. ``if_version=0``
        only creates, ``"*"`` only updates, an int requires that version; see
        :meth:`update` for ``force`` and ``unchanged``."""
        params, headers = _write_options(if_version, force)
        resp = self._http.request(
            "PUT", f"/{collection}/by-key/{_enc(key_value)}", document=data, params=params, headers=headers
        )
        return _parse_document_response(resp)

    def delete_by_key(self, collection: str, key_value: str, *, if_version: IfVersion = None) -> dict[str, Any]:
        return self._http.request(  # type: ignore[no-any-return]
            "DELETE", f"/{collection}/by-key/{_enc(key_value)}", headers=_condition(if_version)
        )


class AsyncDocumentsResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list(
        self,
        collection: str,
        *,
        label: Optional[str] = None,
        where: Optional[str] = None,
        select: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        depth: Optional[int] = None,
    ) -> DocumentList:
        """List documents, newest first. See :meth:`DocumentsResource.list`."""
        params = _list_params(label, where, select, limit, offset, depth)
        data = await self._http.request("GET", f"/{collection}", params=params)
        return _parse_document_list(data)

    async def get(
        self,
        collection: str,
        id: str,
        *,
        label: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> DocumentResponse:
        params: dict[str, Any] = {"label": label, "depth": depth}
        data = await self._http.request("GET", f"/{collection}/{_enc(id)}", params=params)
        return _parse_document_response(data)

    async def create(self, collection: str, document_data: dict[str, Any]) -> DocumentResponse:
        data = await self._http.request("POST", f"/{collection}", document=document_data)
        return _parse_document_response(data)

    async def update(
        self,
        collection: str,
        id: str,
        document_data: dict[str, Any],
        *,
        if_version: IfVersion = None,
        force: bool = False,
    ) -> DocumentResponse:
        """Write a new version. Sending the same data as the current version makes
        none (the response has ``unchanged=True``) unless ``force=True``.

        ``if_version`` makes the write conditional: an int is the version the
        document must be at, ``"*"`` only requires it to exist. On a mismatch
        :class:`~wren.WrenVersionMismatchError` is raised (with ``current_version``).
        """
        params, headers = _write_options(if_version, force)
        data = await self._http.request(
            "PUT", f"/{collection}/{_enc(id)}", document=document_data, params=params, headers=headers
        )
        return _parse_document_response(data)

    async def delete(self, collection: str, id: str, *, if_version: IfVersion = None) -> dict[str, Any]:
        return await self._http.request(  # type: ignore[no-any-return]
            "DELETE", f"/{collection}/{_enc(id)}", headers=_condition(if_version)
        )

    async def undelete(self, collection: str, id: str) -> UndeleteResult:
        """Bring back a deleted document with its history. Raises WrenNotFoundError
        if it isn't deleted, and a 409 WrenError if another document took its
        natural key meanwhile."""
        data = await self._http.request("POST", f"/{collection}/{_enc(id)}/undelete")
        return _parse_undelete_result(data)

    async def restore(self, collection: str, label: str, *, delete_unlabeled: bool = False) -> RestoreResult:
        """Restore every document of a collection to the version carrying ``label``,
        in one transaction: changed documents get the labeled content (as a new
        version), deleted ones come back, and with ``delete_unlabeled`` documents
        without the label are deleted. Raises WrenNotFoundError if no document
        carries the label."""
        data = await self._http.request(
            "POST", f"/{collection}/_restore", body=_restore_body(label, delete_unlabeled)
        )
        return _parse_restore_result(data)

    async def get_paths(self, collection: str, id: str) -> DocumentPaths:
        data = await self._http.request("GET", f"/{collection}/{_enc(id)}/paths")
        return _parse_document_paths(data)

    async def get_by_key(
        self,
        collection: str,
        key_value: str,
        *,
        label: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> DocumentResponse:
        params: dict[str, Any] = {"label": label, "depth": depth}
        data = await self._http.request("GET", f"/{collection}/by-key/{_enc(key_value)}", params=params)
        return _parse_document_response(data)

    async def upsert_by_key(
        self,
        collection: str,
        key_value: str,
        data: dict[str, Any],
        *,
        if_version: IfVersion = None,
        force: bool = False,
    ) -> DocumentResponse:
        """Create or update the document with this natural key. ``if_version=0``
        only creates, ``"*"`` only updates, an int requires that version; see
        :meth:`update` for ``force`` and ``unchanged``."""
        params, headers = _write_options(if_version, force)
        resp = await self._http.request(
            "PUT", f"/{collection}/by-key/{_enc(key_value)}", document=data, params=params, headers=headers
        )
        return _parse_document_response(resp)

    async def delete_by_key(self, collection: str, key_value: str, *, if_version: IfVersion = None) -> dict[str, Any]:
        return await self._http.request(  # type: ignore[no-any-return]
            "DELETE", f"/{collection}/by-key/{_enc(key_value)}", headers=_condition(if_version)
        )
