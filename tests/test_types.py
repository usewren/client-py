"""Response parsing and error mapping.

The parsers in ``wren._types`` are fed real server responses, fetched on the
documented routes through the client's own HTTP layer, so this checks that the
dataclasses match what the server actually sends independently of the resource
methods (see test_documents.py).
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from wren import (
    CollectionInfo,
    DiffEntry,
    DocumentList,
    DocumentResponse,
    FullTree,
    MaterializedQuery,
    MaterializedResult,
    QueryResult,
    Schema,
    TreeNodeResult,
    ValidateSchemaResult,
    VersionList,
    WrenClient,
    WrenError,
    WrenForbiddenError,
    WrenNotFoundError,
    WrenUnauthorizedError,
    WrenValidationError,
)
from wren import _types as t
from wren._http import _filter_none, _raise_for_status

from conftest import uid


def api(wren: WrenClient, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    return wren._http.request(method, path, body=body)


class TestDocumentParsers:
    def test_document_response_list_versions_diff_paths(self, wren: WrenClient) -> None:
        col = f"parse-{uid()}"
        created = api(wren, "POST", f"/{col}", {"title": "Old", "draft": True})
        api(wren, "PUT", f"/{col}/{created['id']}", {"title": "New"})
        api(wren, "POST", f"/{col}/{created['id']}/labels", {"label": "published"})

        doc = t._parse_document_response(api(wren, "GET", f"/{col}/{created['id']}"))
        assert isinstance(doc, DocumentResponse)
        assert doc.collection == col
        assert doc.version == 2
        assert doc.data == {"title": "New"}
        assert doc.created_at and doc.updated_at
        assert doc.labels == ["published"]

        lst = t._parse_document_list(api(wren, "GET", f"/{col}"))
        assert isinstance(lst, DocumentList)
        assert lst.total == 1
        assert lst.items[0].id == created["id"]

        versions = t._parse_version_list(api(wren, "GET", f"/{col}/{created['id']}/versions"))
        assert isinstance(versions, VersionList)
        assert sorted(v.version for v in versions.versions) == [1, 2]
        assert all(v.created_at and v.created_by for v in versions.versions)

        diff = t._parse_diff_result(api(wren, "GET", f"/{col}/{created['id']}/diff?v1=1&v2=2"))
        ops = {d.path: d for d in diff.diff}
        assert isinstance(ops["/title"], DiffEntry)
        assert ops["/title"].op == "replace"
        assert ops["/title"].old_value == "Old"
        assert ops["/draft"].op == "remove"

        api(wren, "PUT", f"/tree/site-{uid()}/a", {"documentId": created["id"]})
        paths = t._parse_document_paths(api(wren, "GET", f"/{col}/{created['id']}/paths"))
        assert paths.id == created["id"] and len(paths.paths) == 1

    def test_empty_document_list(self) -> None:
        lst = t._parse_document_list({})
        assert lst.items == [] and lst.total == 0


class TestCollectionParsers:
    def test_schema_collections_validate(self, wren: WrenClient) -> None:
        col = f"schema-{uid()}"
        api(wren, "POST", f"/{col}", {"title": "a"})
        body = {
            "schema": {"type": "object"},
            "displayName": "{title}",
            "naturalKey": "slug",
            "listColumns": ["title"],
            "indexes": [{"path": "title", "kind": "btree"}],
        }
        schema = t._parse_schema(api(wren, "PUT", f"/{col}/_schema", body))
        assert isinstance(schema, Schema)
        assert schema.collection_type == "json"
        assert schema.display_name == "{title}"
        assert schema.natural_key == "slug"
        assert schema.list_columns == ["title"]
        assert schema.indexes == [{"path": "title", "kind": "btree"}]

        cols = [t._parse_collection_info(c) for c in api(wren, "GET", "/collections")["collections"]]
        info = next(c for c in cols if c.name == col)
        assert isinstance(info, CollectionInfo)
        assert info.count == 1 and info.updated_at

        result = t._parse_validate_schema_result(
            api(wren, "POST", f"/{col}/_schema/validate", {"schema": {"type": "object", "required": ["x"]}})
        )
        assert isinstance(result, ValidateSchemaResult)
        assert result.schema_source == "proposed"
        assert result.checked == 1 and result.invalid == 1
        assert result.failures[0]["errors"]

    def test_query_and_materialized(self, wren: WrenClient) -> None:
        col = f"query-{uid()}"
        api(wren, "POST", f"/{col}", {"title": "a", "category": "news"})
        q = t._parse_query_result(api(wren, "POST", f"/{col}/_query", {"select": ["title"]}))
        assert isinstance(q, QueryResult)
        assert q.items and q.items[0]["data"] == {"title": "a"}
        assert q.rows is None

        agg = t._parse_query_result(
            api(wren, "POST", f"/{col}/_query", {"aggregate": {"groupBy": ["category"], "metrics": {"n": {"count": "title"}}}})
        )
        assert agg.rows and agg.rows[0]["n"] == 1

        mq = t._parse_materialized_query(api(wren, "PUT", f"/{col}/_materialized/slim", {"query": {"select": ["title"]}}))
        assert isinstance(mq, MaterializedQuery)
        assert mq.name == "slim" and mq.refresh_on == "write" and mq.result_doc_id

        listed = api(wren, "GET", f"/{col}/_materialized")
        assert [t._parse_materialized_query(m).name for m in listed["materialized"]] == ["slim"]

        for _ in range(50):  # the first refresh runs in the background
            try:
                res = t._parse_materialized_result(api(wren, "GET", f"/{col}/_materialized/slim"))
                break
            except WrenNotFoundError:
                time.sleep(0.1)
        else:
            pytest.fail("materialized result never appeared")
        assert isinstance(res, MaterializedResult)
        assert res.name == "slim" and res.result["data"]


class TestTreeParsers:
    def test_tree_node_full_tree_and_list(self, wren: WrenClient) -> None:
        col = f"tree-{uid()}"
        tree = f"site-{uid()}"
        doc = api(wren, "POST", f"/{col}", {"title": "Hello"})
        api(wren, "PUT", f"/tree/{tree}/blog/hello", {"documentId": doc["id"]})

        node = t._parse_tree_node_result(api(wren, "GET", f"/tree/{tree}/blog/hello"))
        assert isinstance(node, TreeNodeResult)
        assert node.path == "/blog/hello"
        assert node.document is not None and node.document.id == doc["id"]

        folder = t._parse_tree_node_result(api(wren, "GET", f"/tree/{tree}/blog"))
        assert folder.document is None
        assert [c.path for c in folder.children] == ["/blog/hello"]
        assert folder.children[0].document_id == doc["id"]

        full = t._parse_full_tree(api(wren, "GET", f"/tree/{tree}?full=true"))
        assert isinstance(full, FullTree)
        assert full.tree == tree
        assert full.nodes[0].document_id == doc["id"]
        assert full.nodes[0].document.data == {"title": "Hello"}

        trees = [t._parse_tree_info(x) for x in api(wren, "GET", "/tree")["trees"]]
        assert any(x.name == tree and x.count >= 1 for x in trees)


class TestGenericParse:
    def test_parse_maps_camel_case_and_nested_lists(self) -> None:
        tree = t._parse(t.FullTree, {"tree": "s", "nodes": [{"path": "/a", "documentId": "d", "document": None}], "extra": 1})
        assert tree.tree == "s"
        assert isinstance(tree.nodes[0], t.FullTreeNode)
        assert tree.nodes[0].document_id == "d"

    def test_to_snake(self) -> None:
        assert t._to_snake("assignmentDocId") == "assignment_doc_id"
        assert t._to_snake("id") == "id"


class TestErrorMapping:
    def test_status_codes_map_to_error_classes(self) -> None:
        _raise_for_status(200, {})
        with pytest.raises(WrenUnauthorizedError):
            _raise_for_status(401, {"error": "Unauthorized"})
        with pytest.raises(WrenForbiddenError):
            _raise_for_status(403, {"error": "Forbidden"})
        with pytest.raises(WrenNotFoundError):
            _raise_for_status(404, "not json")

    def test_422_carries_details(self) -> None:
        with pytest.raises(WrenValidationError) as exc:
            _raise_for_status(422, {"error": "Schema validation failed", "details": ["/ must have required property 't'"]})
        assert exc.value.details == ["/ must have required property 't'"]
        assert exc.value.status == 422
        assert str(exc.value) == "Validation error: / must have required property 't'"
        with pytest.raises(WrenValidationError) as exc:
            _raise_for_status(422, {"error": "Invalid JSON Schema", "details": "bad type"})
        assert exc.value.details == ["bad type"]
        with pytest.raises(WrenValidationError) as exc:
            _raise_for_status(422, "plain text")
        assert exc.value.details == []

    def test_other_statuses_use_the_server_message(self) -> None:
        with pytest.raises(WrenError) as exc:
            _raise_for_status(409, {"error": "Invite already accepted"})
        assert str(exc.value) == "Invite already accepted"
        assert exc.value.status == 409
        with pytest.raises(WrenError) as exc:
            _raise_for_status(500, "<html>")
        assert str(exc.value) == "HTTP 500"
        assert exc.value.body == "<html>"

    def test_live_422_from_schema_validation(self, wren: WrenClient) -> None:
        col = f"strict-{uid()}"
        api(wren, "PUT", f"/{col}/_schema", {"schema": {"type": "object", "required": ["title"]}})
        with pytest.raises(WrenValidationError) as exc:
            api(wren, "POST", f"/{col}", {"nope": 1})
        assert exc.value.details == ["/ must have required property 'title'"]

    def test_filter_none(self) -> None:
        assert _filter_none(None) is None
        assert _filter_none({"a": None, "b": 0, "c": False}) == {"b": 0, "c": False}
