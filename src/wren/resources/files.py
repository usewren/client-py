from __future__ import annotations

import mimetypes
import os
from typing import IO, Any, Optional, Union

from wren._http import FilePart, _AsyncHttpClient, _condition, _enc, _HttpClient
from wren._types import DocumentResponse, _parse_document_response

# File contents: bytes, a binary file object, or a path to read
FileData = Union[bytes, bytearray, IO[bytes], "os.PathLike[str]", str]


def _file_part(name: str, data: FileData, content_type: Optional[str]) -> dict[str, FilePart]:
    content: Any
    if isinstance(data, (bytes, bytearray)):
        content = bytes(data)
    elif isinstance(data, (str, os.PathLike)):
        with open(data, "rb") as fh:
            content = fh.read()
    else:
        content = data.read()
    mime = content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
    return {"file": (name, content, mime)}


def _raw_params(version: Optional[int], label: Optional[str]) -> dict[str, Any]:
    return {"version": version, "label": label}


class FilesResource:
    """Files addressed by name, in a binary collection whose natural key is the
    file name (schema ``collection_type="binary", natural_key="filename"``)."""

    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def upload_by_name(
        self,
        collection: str,
        name: str,
        data: FileData,
        *,
        content_type: Optional[str] = None,
        if_version: Optional[Union[int, str]] = None,
    ) -> DocumentResponse:
        """Create or update the file called ``name``. ``data`` is bytes, a binary
        file object or a path. Uploading the same bytes again makes no version
        (``unchanged=True``). ``content_type`` defaults to a guess from the name;
        ``if_version`` works as in :meth:`DocumentsResource.upsert_by_key`."""
        resp = self._http.request(
            "PUT",
            f"/{collection}/by-key/{_enc(name)}",
            files=_file_part(name, data, content_type),
            headers=_condition(if_version),
        )
        return _parse_document_response(resp)

    def download_by_name(
        self, collection: str, name: str, *, version: Optional[int] = None, label: Optional[str] = None
    ) -> bytes:
        """The bytes of the file called ``name``: its current version, or ``version``
        or the version carrying ``label``."""
        content: bytes = self._http.request(
            "GET", f"/{collection}/by-key/{_enc(name)}/raw", params=_raw_params(version, label), raw=True
        )
        return content


class AsyncFilesResource:
    """Files addressed by name; see :class:`FilesResource`."""

    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def upload_by_name(
        self,
        collection: str,
        name: str,
        data: FileData,
        *,
        content_type: Optional[str] = None,
        if_version: Optional[Union[int, str]] = None,
    ) -> DocumentResponse:
        """See :meth:`FilesResource.upload_by_name`."""
        resp = await self._http.request(
            "PUT",
            f"/{collection}/by-key/{_enc(name)}",
            files=_file_part(name, data, content_type),
            headers=_condition(if_version),
        )
        return _parse_document_response(resp)

    async def download_by_name(
        self, collection: str, name: str, *, version: Optional[int] = None, label: Optional[str] = None
    ) -> bytes:
        """See :meth:`FilesResource.download_by_name`."""
        content: bytes = await self._http.request(
            "GET", f"/{collection}/by-key/{_enc(name)}/raw", params=_raw_params(version, label), raw=True
        )
        return content
