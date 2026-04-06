from __future__ import annotations

import dataclasses
import re
from typing import Any, Optional, TypeVar

T = TypeVar("T")


def _to_snake(s: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()


def _parse(cls: type[T], data: dict[str, Any]) -> T:
    """Convert a camelCase-keyed dict into an instance of cls (a dataclass).

    Handles one level of nesting: if a field's type annotation is
    ``list[SomeDataclass]``, each element is parsed recursively.
    """
    fields = {f.name: f for f in dataclasses.fields(cls)}  # type: ignore[arg-type]
    hints = {}
    try:
        import typing
        hints = typing.get_type_hints(cls)
    except Exception:
        pass

    kwargs: dict[str, Any] = {}
    for k, v in data.items():
        snake = _to_snake(k)
        if snake not in fields:
            continue

        hint = hints.get(snake)
        # Attempt to detect list[SomeDataclass] annotations
        if hint is not None and v is not None:
            origin = getattr(hint, "__origin__", None)
            args = getattr(hint, "__args__", ())
            if origin is list and args:
                item_type = args[0]
                if dataclasses.is_dataclass(item_type) and isinstance(v, list):
                    v = [_parse(item_type, item) if isinstance(item, dict) else item for item in v]  # type: ignore[arg-type]

        kwargs[snake] = v

    return cls(**kwargs)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Document types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class FacetValue:
    value: str
    count: int


@dataclasses.dataclass
class DocumentResponse:
    collection: str
    id: str
    version: int
    labels: dict[str, str]
    created_at: str
    updated_at: str
    data: dict[str, Any]


@dataclasses.dataclass
class DocumentList:
    collection: str
    total: int
    cursor: Optional[str]
    facets: dict[str, list[FacetValue]]
    items: list[DocumentResponse]


@dataclasses.dataclass
class DocumentPaths:
    id: str
    collection: str
    paths: list[dict[str, str]]


# ---------------------------------------------------------------------------
# Version types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class VersionMeta:
    version: int
    labels: dict[str, str]
    created_at: str
    created_by: str


@dataclasses.dataclass
class VersionList:
    collection: str
    id: str
    versions: list[VersionMeta]


# ---------------------------------------------------------------------------
# Diff types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class DiffEntry:
    op: str  # Literal["add", "remove", "replace"]
    path: str
    value: Optional[Any] = None
    old_value: Optional[Any] = None


@dataclasses.dataclass
class DiffResult:
    id: str
    collection: str
    v1: int
    v2: int
    diff: list[DiffEntry]


# ---------------------------------------------------------------------------
# Collection types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class CollectionInfo:
    name: str
    count: int
    updated_at: str


@dataclasses.dataclass
class Schema:
    collection: str
    collection_type: str
    schema: Optional[dict[str, Any]]
    display_name: Optional[str]
    updated_at: str


# ---------------------------------------------------------------------------
# Tree types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class TreeInfo:
    name: str
    count: int


@dataclasses.dataclass
class TreeChild:
    path: str
    document_id: Optional[str]


@dataclasses.dataclass
class TreeNodeResult:
    path: str
    document: Optional[DocumentResponse]
    assignment_doc_id: Optional[str]
    children: list[TreeChild]


@dataclasses.dataclass
class FullTreeNode:
    path: str
    document_id: str
    document: DocumentResponse


@dataclasses.dataclass
class FullTree:
    tree: str
    nodes: list[FullTreeNode]


# ---------------------------------------------------------------------------
# API key types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ApiKey:
    id: str
    name: str
    key_prefix: str
    created_at: str
    last_used_at: Optional[str]
    revoked_at: Optional[str]


@dataclasses.dataclass
class ApiKeyCreated(ApiKey):
    key: str = ""


# ---------------------------------------------------------------------------
# Member / invite types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class Member:
    user_id: str
    name: str
    email: str
    role: str
    joined_at: str


@dataclasses.dataclass
class Invite:
    id: str
    email: str
    role: str
    created_at: str
    expires_at: str
    accepted_at: Optional[str]
    revoked_at: Optional[str]


@dataclasses.dataclass
class InviteCreated(Invite):
    token: str = ""


@dataclasses.dataclass
class ReceivedInvite:
    id: str
    org_id: str
    org_name: str
    org_email: str
    role: str
    created_at: str
    expires_at: str
    accepted_at: Optional[str]
    revoked_at: Optional[str]


# ---------------------------------------------------------------------------
# Permission types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class Permission:
    id: str
    principal: str
    resource: str
    access: str  # Literal["none", "read", "write", "admin"]
    label_filter: Optional[str]
    filter_lang: Optional[str]  # Literal["jq", "jmespath", "jsonata"] | None
    filter_expr: Optional[str]
    audit_reads: bool
    audit_writes: bool
    created_at: str


# ---------------------------------------------------------------------------
# Explicit factory helpers for complex nested types
# ---------------------------------------------------------------------------

def _parse_document_response(data: dict[str, Any]) -> DocumentResponse:
    return DocumentResponse(
        collection=data.get("collection", ""),
        id=data.get("id", ""),
        version=data.get("version", 0),
        labels=data.get("labels", {}),
        created_at=data.get("createdAt", data.get("created_at", "")),
        updated_at=data.get("updatedAt", data.get("updated_at", "")),
        data=data.get("data", {}),
    )


def _parse_facet_value(data: dict[str, Any]) -> FacetValue:
    return FacetValue(
        value=data.get("value", ""),
        count=data.get("count", 0),
    )


def _parse_document_list(data: dict[str, Any]) -> DocumentList:
    raw_facets: dict[str, Any] = data.get("facets", {})
    facets: dict[str, list[FacetValue]] = {
        k: [_parse_facet_value(fv) for fv in v]
        for k, v in raw_facets.items()
    }
    return DocumentList(
        collection=data.get("collection", ""),
        total=data.get("total", 0),
        cursor=data.get("cursor"),
        facets=facets,
        items=[_parse_document_response(item) for item in data.get("items", [])],
    )


def _parse_document_paths(data: dict[str, Any]) -> DocumentPaths:
    return DocumentPaths(
        id=data.get("id", ""),
        collection=data.get("collection", ""),
        paths=data.get("paths", []),
    )


def _parse_version_meta(data: dict[str, Any]) -> VersionMeta:
    return VersionMeta(
        version=data.get("version", 0),
        labels=data.get("labels", {}),
        created_at=data.get("createdAt", data.get("created_at", "")),
        created_by=data.get("createdBy", data.get("created_by", "")),
    )


def _parse_version_list(data: dict[str, Any]) -> VersionList:
    return VersionList(
        collection=data.get("collection", ""),
        id=data.get("id", ""),
        versions=[_parse_version_meta(v) for v in data.get("versions", [])],
    )


def _parse_diff_entry(data: dict[str, Any]) -> DiffEntry:
    return DiffEntry(
        op=data.get("op", ""),
        path=data.get("path", ""),
        value=data.get("value"),
        old_value=data.get("oldValue", data.get("old_value")),
    )


def _parse_diff_result(data: dict[str, Any]) -> DiffResult:
    return DiffResult(
        id=data.get("id", ""),
        collection=data.get("collection", ""),
        v1=data.get("v1", 0),
        v2=data.get("v2", 0),
        diff=[_parse_diff_entry(e) for e in data.get("diff", [])],
    )


def _parse_collection_info(data: dict[str, Any]) -> CollectionInfo:
    return CollectionInfo(
        name=data.get("name", ""),
        count=data.get("count", 0),
        updated_at=data.get("updatedAt", data.get("updated_at", "")),
    )


def _parse_schema(data: dict[str, Any]) -> Schema:
    return Schema(
        collection=data.get("collection", ""),
        collection_type=data.get("collectionType", data.get("collection_type", "")),
        schema=data.get("schema"),
        display_name=data.get("displayName", data.get("display_name")),
        updated_at=data.get("updatedAt", data.get("updated_at", "")),
    )


def _parse_tree_info(data: dict[str, Any]) -> TreeInfo:
    return TreeInfo(
        name=data.get("name", ""),
        count=data.get("count", 0),
    )


def _parse_tree_child(data: dict[str, Any]) -> TreeChild:
    return TreeChild(
        path=data.get("path", ""),
        document_id=data.get("documentId", data.get("document_id")),
    )


def _parse_tree_node_result(data: dict[str, Any]) -> TreeNodeResult:
    raw_doc = data.get("document")
    return TreeNodeResult(
        path=data.get("path", ""),
        document=_parse_document_response(raw_doc) if raw_doc else None,
        assignment_doc_id=data.get("assignmentDocId", data.get("assignment_doc_id")),
        children=[_parse_tree_child(c) for c in data.get("children", [])],
    )


def _parse_full_tree_node(data: dict[str, Any]) -> FullTreeNode:
    return FullTreeNode(
        path=data.get("path", ""),
        document_id=data.get("documentId", data.get("document_id", "")),
        document=_parse_document_response(data["document"]),
    )


def _parse_full_tree(data: dict[str, Any]) -> FullTree:
    return FullTree(
        tree=data.get("tree", ""),
        nodes=[_parse_full_tree_node(n) for n in data.get("nodes", [])],
    )


def _parse_api_key(data: dict[str, Any]) -> ApiKey:
    return ApiKey(
        id=data.get("id", ""),
        name=data.get("name", ""),
        key_prefix=data.get("keyPrefix", data.get("key_prefix", "")),
        created_at=data.get("createdAt", data.get("created_at", "")),
        last_used_at=data.get("lastUsedAt", data.get("last_used_at")),
        revoked_at=data.get("revokedAt", data.get("revoked_at")),
    )


def _parse_api_key_created(data: dict[str, Any]) -> ApiKeyCreated:
    return ApiKeyCreated(
        id=data.get("id", ""),
        name=data.get("name", ""),
        key_prefix=data.get("keyPrefix", data.get("key_prefix", "")),
        created_at=data.get("createdAt", data.get("created_at", "")),
        last_used_at=data.get("lastUsedAt", data.get("last_used_at")),
        revoked_at=data.get("revokedAt", data.get("revoked_at")),
        key=data.get("key", ""),
    )


def _parse_member(data: dict[str, Any]) -> Member:
    return Member(
        user_id=data.get("userId", data.get("user_id", "")),
        name=data.get("name", ""),
        email=data.get("email", ""),
        role=data.get("role", ""),
        joined_at=data.get("joinedAt", data.get("joined_at", "")),
    )


def _parse_invite(data: dict[str, Any]) -> Invite:
    return Invite(
        id=data.get("id", ""),
        email=data.get("email", ""),
        role=data.get("role", ""),
        created_at=data.get("createdAt", data.get("created_at", "")),
        expires_at=data.get("expiresAt", data.get("expires_at", "")),
        accepted_at=data.get("acceptedAt", data.get("accepted_at")),
        revoked_at=data.get("revokedAt", data.get("revoked_at")),
    )


def _parse_invite_created(data: dict[str, Any]) -> InviteCreated:
    return InviteCreated(
        id=data.get("id", ""),
        email=data.get("email", ""),
        role=data.get("role", ""),
        created_at=data.get("createdAt", data.get("created_at", "")),
        expires_at=data.get("expiresAt", data.get("expires_at", "")),
        accepted_at=data.get("acceptedAt", data.get("accepted_at")),
        revoked_at=data.get("revokedAt", data.get("revoked_at")),
        token=data.get("token", ""),
    )


def _parse_received_invite(data: dict[str, Any]) -> ReceivedInvite:
    return ReceivedInvite(
        id=data.get("id", ""),
        org_id=data.get("orgId", data.get("org_id", "")),
        org_name=data.get("orgName", data.get("org_name", "")),
        org_email=data.get("orgEmail", data.get("org_email", "")),
        role=data.get("role", ""),
        created_at=data.get("createdAt", data.get("created_at", "")),
        expires_at=data.get("expiresAt", data.get("expires_at", "")),
        accepted_at=data.get("acceptedAt", data.get("accepted_at")),
        revoked_at=data.get("revokedAt", data.get("revoked_at")),
    )


def _parse_permission(data: dict[str, Any]) -> Permission:
    return Permission(
        id=data.get("id", ""),
        principal=data.get("principal", ""),
        resource=data.get("resource", ""),
        access=data.get("access", "none"),
        label_filter=data.get("labelFilter", data.get("label_filter")),
        filter_lang=data.get("filterLang", data.get("filter_lang")),
        filter_expr=data.get("filterExpr", data.get("filter_expr")),
        audit_reads=data.get("auditReads", data.get("audit_reads", False)),
        audit_writes=data.get("auditWrites", data.get("audit_writes", False)),
        created_at=data.get("createdAt", data.get("created_at", "")),
    )
