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
class DocumentResponse:
    collection: str
    id: str
    version: int
    labels: list[str]
    created_at: str
    updated_at: str
    data: dict[str, Any]


@dataclasses.dataclass
class DocumentList:
    collection: str
    total: int
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
    labels: list[str]
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
    natural_key: Optional[str] = None
    list_columns: Optional[list[str]] = None
    indexes: Optional[list[dict[str, Any]]] = None


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


@dataclasses.dataclass
class PromotedDocument:
    path: str
    document_id: str
    collection: str
    version: int


@dataclasses.dataclass
class TreePromoteResult:
    tree: str
    label: str
    from_: Optional[str]
    promoted: list[PromotedDocument]


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
    alias: Optional[str] = None


# ---------------------------------------------------------------------------
# Explicit factory helpers for complex nested types
# ---------------------------------------------------------------------------

def _parse_document_response(data: dict[str, Any]) -> DocumentResponse:
    return DocumentResponse(
        collection=data.get("collection", ""),
        id=data.get("id", ""),
        version=data.get("version", 0),
        labels=data.get("labels", []),
        created_at=data.get("createdAt", data.get("created_at", "")),
        updated_at=data.get("updatedAt", data.get("updated_at", "")),
        data=data.get("data", {}),
    )


def _parse_document_list(data: dict[str, Any]) -> DocumentList:
    return DocumentList(
        collection=data.get("collection", ""),
        total=data.get("total", 0),
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
        labels=data.get("labels", []),
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
        natural_key=data.get("naturalKey", data.get("natural_key")),
        list_columns=data.get("listColumns", data.get("list_columns")),
        indexes=data.get("indexes"),
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


def _parse_promoted_document(data: dict[str, Any]) -> PromotedDocument:
    return PromotedDocument(
        path=data.get("path", ""),
        document_id=data.get("documentId", data.get("document_id", "")),
        collection=data.get("collection", ""),
        version=data.get("version", 0),
    )


def _parse_tree_promote_result(data: dict[str, Any]) -> TreePromoteResult:
    return TreePromoteResult(
        tree=data.get("tree", ""),
        label=data.get("label", ""),
        from_=data.get("from"),
        promoted=[_parse_promoted_document(p) for p in data.get("promoted", [])],
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
        alias=data.get("alias"),
    )


# ---------------------------------------------------------------------------
# Query types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class QueryResult:
    items: Optional[list[dict[str, Any]]] = None
    rows: Optional[list[dict[str, Any]]] = None
    cursor: Optional[str] = None


def _parse_query_result(data: dict[str, Any]) -> QueryResult:
    return QueryResult(
        items=data.get("items"),
        rows=data.get("rows"),
        cursor=data.get("cursor"),
    )


# ---------------------------------------------------------------------------
# Materialized query types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class MaterializedQuery:
    name: str
    refresh_on: str
    result_doc_id: Optional[str]
    created_at: str
    updated_at: str


@dataclasses.dataclass
class MaterializedResult:
    collection: str
    name: str
    result: dict[str, Any]


def _parse_materialized_query(data: dict[str, Any]) -> MaterializedQuery:
    return MaterializedQuery(
        name=data.get("name", ""),
        refresh_on=data.get("refreshOn", data.get("refresh_on", "")),
        result_doc_id=data.get("resultDocId", data.get("result_doc_id")),
        created_at=data.get("createdAt", data.get("created_at", "")),
        updated_at=data.get("updatedAt", data.get("updated_at", "")),
    )


def _parse_materialized_result(data: dict[str, Any]) -> MaterializedResult:
    return MaterializedResult(
        collection=data.get("collection", ""),
        name=data.get("name", ""),
        result=data.get("result", {}),
    )


# ---------------------------------------------------------------------------
# Webhook types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class Webhook:
    id: str
    url: str
    events: list[str]
    enabled: bool
    consec_failures: int
    created_at: str
    updated_at: str


@dataclasses.dataclass
class WebhookCreated(Webhook):
    secret: str = ""


@dataclasses.dataclass
class WebhookDelivery:
    id: str
    batch_key: str
    event_count: int
    attempt: int
    status_code: Optional[int]
    error: Optional[str]
    delivered_at: str


def _parse_webhook(data: dict[str, Any]) -> Webhook:
    return Webhook(
        id=data.get("id", ""),
        url=data.get("url", ""),
        events=data.get("events", []),
        enabled=data.get("enabled", True),
        consec_failures=data.get("consecFailures", data.get("consec_failures", 0)),
        created_at=data.get("createdAt", data.get("created_at", "")),
        updated_at=data.get("updatedAt", data.get("updated_at", "")),
    )


def _parse_webhook_created(data: dict[str, Any]) -> WebhookCreated:
    return WebhookCreated(
        id=data.get("id", ""),
        url=data.get("url", ""),
        events=data.get("events", []),
        enabled=data.get("enabled", True),
        consec_failures=data.get("consecFailures", data.get("consec_failures", 0)),
        created_at=data.get("createdAt", data.get("created_at", "")),
        updated_at=data.get("updatedAt", data.get("updated_at", "")),
        secret=data.get("secret", ""),
    )


def _parse_webhook_delivery(data: dict[str, Any]) -> WebhookDelivery:
    return WebhookDelivery(
        id=data.get("id", ""),
        batch_key=data.get("batchKey", data.get("batch_key", "")),
        event_count=data.get("eventCount", data.get("event_count", 0)),
        attempt=data.get("attempt", 0),
        status_code=data.get("statusCode", data.get("status_code")),
        error=data.get("error"),
        delivered_at=data.get("deliveredAt", data.get("delivered_at", "")),
    )


# ---------------------------------------------------------------------------
# Schema validation types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ValidateSchemaResult:
    collection: str
    schema_source: str
    checked: int
    valid: int
    invalid: int
    failures: list[dict[str, Any]]


def _parse_validate_schema_result(data: dict[str, Any]) -> ValidateSchemaResult:
    return ValidateSchemaResult(
        collection=data.get("collection", ""),
        schema_source=data.get("schemaSource", data.get("schema_source", "")),
        checked=data.get("checked", 0),
        valid=data.get("valid", 0),
        invalid=data.get("invalid", 0),
        failures=data.get("failures", []),
    )


# ---------------------------------------------------------------------------
# Retention types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class RetentionPolicy:
    """A retention policy; ``collection`` is ``"*"`` for the org default. A version
    is removed if any rule says so; current and labeled versions are always kept.
    A policy without rules keeps everything."""

    collection: str
    labeled_only: bool
    max_versions: Optional[int]
    max_age_days: Optional[int]
    after_label: Optional[str]
    updated_at: str
    updated_by: Optional[str]


@dataclasses.dataclass
class RetentionRun:
    collection: str
    versions_removed: int
    bytes_freed: int
    triggered_by: Optional[str]  # a user id, or "schedule" for the hourly run
    ran_at: str


@dataclasses.dataclass
class RetentionOverview:
    default: Optional[RetentionPolicy]
    collections: list[RetentionPolicy]
    runs: list[RetentionRun]


@dataclasses.dataclass
class RetentionCount:
    """Versions, documents and bytes removed (or that would be); ``collection``
    is None for the total."""

    versions: int
    documents: int
    bytes: int
    collection: Optional[str] = None


@dataclasses.dataclass
class RetentionResult:
    collections: list[RetentionCount]  # only collections where something is removed
    total: RetentionCount


def _parse_retention_policy(data: dict[str, Any]) -> RetentionPolicy:
    return RetentionPolicy(
        collection=data.get("collection", ""),
        labeled_only=data.get("labeledOnly", False),
        max_versions=data.get("maxVersions"),
        max_age_days=data.get("maxAgeDays"),
        after_label=data.get("afterLabel"),
        updated_at=data.get("updatedAt", ""),
        updated_by=data.get("updatedBy"),
    )


def _parse_retention_overview(data: dict[str, Any]) -> RetentionOverview:
    default = data.get("default")
    return RetentionOverview(
        default=_parse_retention_policy(default) if default else None,
        collections=[_parse_retention_policy(p) for p in data.get("collections", [])],
        runs=[
            RetentionRun(
                collection=r.get("collection", ""),
                versions_removed=r.get("versionsRemoved", 0),
                bytes_freed=r.get("bytesFreed", 0),
                triggered_by=r.get("triggeredBy"),
                ran_at=r.get("ranAt", ""),
            )
            for r in data.get("runs", [])
        ],
    )


def _parse_retention_count(data: dict[str, Any]) -> RetentionCount:
    return RetentionCount(
        versions=data.get("versions", 0),
        documents=data.get("documents", 0),
        bytes=data.get("bytes", 0),
        collection=data.get("collection"),
    )


def _parse_retention_result(data: dict[str, Any]) -> RetentionResult:
    return RetentionResult(
        collections=[_parse_retention_count(c) for c in data.get("collections", [])],
        total=_parse_retention_count(data.get("total", {})),
    )
