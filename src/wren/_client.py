from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _HttpClient
from wren.resources.collections import AsyncCollectionsResource, CollectionsResource
from wren.resources.diff import AsyncDiffResource, DiffResource
from wren.resources.documents import AsyncDocumentsResource, DocumentsResource
from wren.resources.files import AsyncFilesResource, FilesResource
from wren.resources.invites import AsyncInvitesResource, InvitesResource
from wren.resources.keys import AsyncKeysResource, KeysResource
from wren.resources.labels import AsyncLabelsResource, LabelsResource
from wren.resources.materialized import AsyncMaterializedResource, MaterializedResource
from wren.resources.members import AsyncMembersResource, MembersResource
from wren.resources.permissions import AsyncPermissionsResource, PermissionsResource
from wren.resources.query import AsyncQueryResource, QueryResource
from wren.resources.retention import AsyncRetentionResource, RetentionResource
from wren.resources.trees import AsyncTreesResource, TreesResource
from wren.resources.versions import AsyncVersionsResource, VersionsResource
from wren.resources.webhooks import AsyncWebhooksResource, WebhooksResource


class WrenClient:
    """Synchronous client for the Wren versioned document store API."""

    def __init__(self, base_url: str, *, api_key: Optional[str] = None) -> None:
        self._http = _HttpClient(base_url, api_key=api_key)
        self.documents = DocumentsResource(self._http)
        self.versions = VersionsResource(self._http)
        self.labels = LabelsResource(self._http)
        self.diff = DiffResource(self._http)
        self.collections = CollectionsResource(self._http)
        self.trees = TreesResource(self._http)
        self.keys = KeysResource(self._http)
        self.members = MembersResource(self._http)
        self.invites = InvitesResource(self._http)
        self.permissions = PermissionsResource(self._http)
        self.query = QueryResource(self._http)
        self.materialized = MaterializedResource(self._http)
        self.webhooks = WebhooksResource(self._http)
        self.retention = RetentionResource(self._http)
        self.files = FilesResource(self._http)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "WrenClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncWrenClient:
    """Asynchronous client for the Wren versioned document store API."""

    def __init__(self, base_url: str, *, api_key: Optional[str] = None) -> None:
        self._http = _AsyncHttpClient(base_url, api_key=api_key)
        self.documents = AsyncDocumentsResource(self._http)
        self.versions = AsyncVersionsResource(self._http)
        self.labels = AsyncLabelsResource(self._http)
        self.diff = AsyncDiffResource(self._http)
        self.collections = AsyncCollectionsResource(self._http)
        self.trees = AsyncTreesResource(self._http)
        self.keys = AsyncKeysResource(self._http)
        self.members = AsyncMembersResource(self._http)
        self.invites = AsyncInvitesResource(self._http)
        self.permissions = AsyncPermissionsResource(self._http)
        self.query = AsyncQueryResource(self._http)
        self.materialized = AsyncMaterializedResource(self._http)
        self.webhooks = AsyncWebhooksResource(self._http)
        self.retention = AsyncRetentionResource(self._http)
        self.files = AsyncFilesResource(self._http)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncWrenClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
