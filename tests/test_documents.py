"""Documents, versions, labels, diff, collections/schemas, query, materialized and trees (sync + async)."""

from __future__ import annotations

import asyncio
import time

import pytest

from wren import (
    AsyncWrenClient,
    PromotedDocument,
    TreePromoteResult,
    WrenClient,
    WrenError,
    WrenNotFoundError,
)

from conftest import uid

MISSING = "00000000-0000-0000-0000-000000000000"


class TestDocuments:
    def test_create_get_update_delete(self, wren: WrenClient) -> None:
        col = f"articles-{uid()}"
        doc = wren.documents.create(col, {"title": "Hello", "summary": None})
        assert doc.version == 1
        # The document itself is the body, None values included
        assert doc.data == {"title": "Hello", "summary": None}
        assert wren.documents.get(col, doc.id).data == {"title": "Hello", "summary": None}
        v2 = wren.documents.update(col, doc.id, {"title": "Updated"})
        assert v2.version == 2
        assert v2.data == {"title": "Updated"}
        assert wren.documents.delete(col, doc.id) == {"id": doc.id, "deleted": True}
        with pytest.raises(WrenNotFoundError):
            wren.documents.get(col, doc.id)

    def test_list_with_label_where_select_limit_offset(self, wren: WrenClient) -> None:
        col = f"list-{uid()}"
        a = wren.documents.create(col, {"title": "a", "kind": "odd"})
        b = wren.documents.create(col, {"title": "b", "kind": "even"})
        assert wren.documents.list(col).total == 2
        assert len(wren.documents.list(col, limit=1).items) == 1
        # Newest first, so the second page of one holds the older document
        page2 = wren.documents.list(col, limit=1, offset=1)
        assert page2.total == 2 and [d.id for d in page2.items] == [a.id]
        res = wren.documents.list(col, where="kind:odd", select="title")
        assert [d.data for d in res.items] == [{"title": "a"}]
        wren.labels.set(col, a.id, "published")
        published = wren.documents.list(col, label="published")
        assert [d.id for d in published.items] == [a.id]
        assert published.items[0].labels == ["published"]
        assert wren.documents.get(col, b.id).labels == []

    def test_get_at_label_and_depth(self, wren: WrenClient) -> None:
        col = f"lbl-{uid()}"
        target = wren.documents.create(col, {"title": "target"})
        doc = wren.documents.create(col, {"title": "draft", "link": {"$ref": f"{col}/{target.id}"}})
        wren.labels.set(col, doc.id, "published")
        wren.documents.update(col, doc.id, {"title": "newer"})
        assert wren.documents.get(col, doc.id, label="published").version == 1
        assert wren.documents.get(col, doc.id, depth=1).id == doc.id
        assert wren.documents.list(col, depth=0).total == 2
        with pytest.raises(WrenNotFoundError):
            wren.documents.get(col, target.id, label="published")

    def test_ids_are_url_encoded(self, wren: WrenClient) -> None:
        with pytest.raises(WrenNotFoundError):
            wren.documents.get("anything", "no/such id")

    def test_get_paths(self, wren: WrenClient) -> None:
        col = f"paths-{uid()}"
        tree = f"site-{uid()}"
        doc = wren.documents.create(col, {"title": "x"})
        wren.trees.assign(tree, "/blog/x", doc.id)
        assert wren.documents.get_paths(col, doc.id).paths == [{"tree": tree, "path": "/blog/x"}]

    def test_natural_keys(self, wren: WrenClient) -> None:
        col = f"pages-{uid()}"
        wren.collections.set_schema(col, natural_key="slug")
        created = wren.documents.upsert_by_key(col, "about", {"slug": "about", "title": "About"})
        assert created.version == 1
        updated = wren.documents.upsert_by_key(col, "about", {"slug": "about", "title": "About us"})
        assert updated.id == created.id and updated.version == 2
        assert wren.documents.get_by_key(col, "about").data["title"] == "About us"
        with pytest.raises(WrenNotFoundError):
            wren.documents.get_by_key(col, "about", label="published", depth=0)
        odd = wren.documents.upsert_by_key(col, "a b/c", {"slug": "a b/c"})
        assert wren.documents.get_by_key(col, "a b/c").id == odd.id
        assert wren.documents.delete_by_key(col, "about") == {"id": created.id, "deleted": True}


class TestVersionsLabelsDiff:
    def test_versions(self, wren: WrenClient) -> None:
        col = f"v-{uid()}"
        doc = wren.documents.create(col, {"title": "one"})
        wren.documents.update(col, doc.id, {"title": "two"})
        assert [v.version for v in wren.versions.list(col, doc.id).versions] == [1, 2]
        assert wren.versions.get(col, doc.id, 1).data == {"title": "one"}
        assert wren.versions.rollback(col, doc.id, 1) == {"id": doc.id, "version": 3, "rolledBackTo": 1}
        assert wren.documents.get(col, doc.id).data == {"title": "one"}

    def test_labels_and_diff(self, wren: WrenClient) -> None:
        col = f"l-{uid()}"
        doc = wren.documents.create(col, {"title": "Old", "draft": True})
        wren.documents.update(col, doc.id, {"title": "New"})
        assert wren.labels.set(col, doc.id, "published") == {"id": doc.id, "label": "published", "version": 2}
        assert wren.labels.set(col, doc.id, "staging", version=1)["version"] == 1
        versions = {v.version: v for v in wren.versions.list(col, doc.id).versions}
        assert versions[1].labels == ["staging"] and versions[2].labels == ["published"]
        diff = wren.diff.compare(col, doc.id, 1, 2)
        ops = {d.path: d for d in diff.diff}
        assert ops["/title"].op == "replace" and ops["/title"].old_value == "Old"
        assert ops["/draft"].op == "remove"


class TestCollectionsQueryMaterialized:
    def test_schemas(self, wren: WrenClient) -> None:
        col = f"s-{uid()}"
        schema = {"type": "object", "required": ["title"]}
        set_ = wren.collections.set_schema(
            col, schema=schema, display_name="{title}", collection_type="json",
            natural_key="slug", list_columns=["title"], indexes=[],
        )
        assert set_.schema == schema
        got = wren.collections.get_schema(col)
        assert got.display_name == "{title}" and got.natural_key == "slug" and got.list_columns == ["title"]
        wren.documents.create(col, {"title": "t", "slug": "t"})
        assert any(c.name == col for c in wren.collections.list())
        assert wren.collections.validate(col).schema_source == "current"
        assert wren.collections.validate(col, {"type": "object"}).schema_source == "proposed"
        assert wren.collections.delete_schema(col) == {"collection": col, "deleted": True}

    def test_query(self, wren: WrenClient) -> None:
        col = f"q-{uid()}"
        wren.documents.create(col, {"title": "a", "category": "news"})
        wren.documents.create(col, {"title": "b", "category": "sport"})
        res = wren.query.run(col, where="category:news", select=["title"], limit=10)
        assert res.items and [i["data"] for i in res.items] == [{"title": "a"}]
        agg = wren.query.run(col, aggregate={"groupBy": ["category"], "metrics": {"n": {"count": "title"}}})
        assert agg.rows and sorted(r["n"] for r in agg.rows) == [1, 1]
        first = wren.query.run(col, limit=1)
        assert first.cursor
        # Page contents are not asserted: the server orders by created_at but pages
        # by id (sandbox handleQuery), so the next page is not deterministic.
        assert len(wren.query.run(col, limit=1, cursor=first.cursor).items or []) <= 1
        # An undecodable cursor is rejected, which proves the client sends it.
        with pytest.raises(WrenError) as exc:
            wren.query.run(col, label="published", cursor="not-a-cursor")
        assert exc.value.status == 400

    def test_materialized(self, wren: WrenClient) -> None:
        col = f"m-{uid()}"
        wren.documents.create(col, {"title": "a"})
        mq = wren.materialized.set(col, "slim", {"select": ["title"]})
        assert mq.name == "slim" and mq.refresh_on == "write"
        assert [m.name for m in wren.materialized.list(col)] == ["slim"]
        for _ in range(50):  # the first refresh runs in the background
            try:
                assert wren.materialized.get(col, "slim").name == "slim"
                break
            except WrenNotFoundError:
                time.sleep(0.1)
        else:
            pytest.fail("materialized result never appeared")
        assert wren.materialized.delete(col, "slim")["deleted"] is True


class TestTrees:
    def test_trees(self, wren: WrenClient) -> None:
        col = f"t-{uid()}"
        tree = f"site-{uid()}"
        doc = wren.documents.create(col, {"title": "Hello"})
        assert wren.trees.assign(tree, "blog/hello", doc.id)["documentId"] == doc.id
        node = wren.trees.get_node(tree, "/blog/hello")
        assert node.document is not None and node.document.id == doc.id
        assert [c.path for c in wren.trees.get_node(tree, "blog").children] == ["/blog/hello"]
        snap = wren.trees.snapshot(tree)
        assert [n.path for n in snap.nodes] == ["/blog/hello"]
        assert any(t.name == tree for t in wren.trees.list())
        assert wren.trees.unassign(tree, "/blog/hello")["removed"] is True
        with pytest.raises(WrenNotFoundError):
            wren.trees.get_node(tree, "/blog/hello")

    def test_promote(self, wren: WrenClient) -> None:
        col = f"t-{uid()}"
        tree = f"site-{uid()}"
        a = wren.documents.create(col, {"title": "A1"})
        b = wren.documents.create(col, {"title": "B1"})
        wren.labels.set(col, a.id, "preview")
        wren.documents.update(col, a.id, {"title": "A2"})
        wren.trees.assign(tree, "/a", a.id)
        wren.trees.assign(tree, "/b", b.id)

        # Default: every document's current version becomes "published".
        res = wren.trees.promote(tree)
        assert isinstance(res, TreePromoteResult)
        assert (res.tree, res.label, res.from_) == (tree, "published", None)
        by_path = {p.path: p for p in res.promoted}
        assert by_path["/a"] == PromotedDocument(path="/a", document_id=a.id, collection=col, version=2)
        assert by_path["/b"].version == 1
        assert wren.documents.get(col, a.id, label="published").data == {"title": "A2"}

        # From a label: only documents carrying it move, under a custom label.
        res = wren.trees.promote(tree, label="live", from_="preview")
        assert (res.label, res.from_) == ("live", "preview")
        assert [(p.path, p.version) for p in res.promoted] == [("/a", 1)]
        assert wren.documents.get(col, a.id, label="live").data == {"title": "A1"}

        with pytest.raises(WrenNotFoundError):
            wren.trees.promote(f"nope-{uid()}")


class TestAsync:
    async def test_documents_and_natural_keys(self, awren: AsyncWrenClient) -> None:
        col = f"async-{uid()}"
        doc = await awren.documents.create(col, {"title": "one"})
        assert doc.data == {"title": "one"}
        await awren.documents.update(col, doc.id, {"title": "two"})
        assert (await awren.documents.get(col, doc.id)).version == 2
        older = await awren.documents.create(col, {"title": "other"})
        lst = await awren.documents.list(col, where="title:two", select="title", limit=5, offset=0, depth=0)
        assert [d.data for d in lst.items] == [{"title": "two"}]
        assert (await awren.documents.list(col, label="none")).total == 0
        assert (await awren.documents.delete(col, older.id))["deleted"] is True

        keyed = f"async-keys-{uid()}"
        await awren.collections.set_schema(keyed, natural_key="slug")
        created = await awren.documents.upsert_by_key(keyed, "home", {"slug": "home", "title": "Home"})
        assert (await awren.documents.get_by_key(keyed, "home", depth=0)).id == created.id
        assert await awren.documents.delete_by_key(keyed, "home") == {"id": created.id, "deleted": True}

    async def test_versions_labels_diff_trees(self, awren: AsyncWrenClient) -> None:
        col = f"async-{uid()}"
        tree = f"async-site-{uid()}"
        doc = await awren.documents.create(col, {"title": "one"})
        await awren.documents.update(col, doc.id, {"title": "two"})
        assert len((await awren.versions.list(col, doc.id)).versions) == 2
        assert (await awren.versions.get(col, doc.id, 1)).data == {"title": "one"}
        assert (await awren.labels.set(col, doc.id, "published", version=1))["version"] == 1
        assert (await awren.diff.compare(col, doc.id, 1, 2)).diff
        assert (await awren.versions.rollback(col, doc.id, 1))["rolledBackTo"] == 1

        await awren.trees.assign(tree, "/a", doc.id)
        assert (await awren.trees.get_node(tree, "a")).document is not None
        assert (await awren.documents.get_paths(col, doc.id)).paths == [{"tree": tree, "path": "/a"}]
        assert [n.path for n in (await awren.trees.snapshot(tree)).nodes] == ["/a"]
        assert any(t.name == tree for t in await awren.trees.list())
        promoted = await awren.trees.promote(tree, label="live", from_="published")
        assert (promoted.tree, promoted.label, promoted.from_) == (tree, "live", "published")
        assert [(p.path, p.document_id, p.version) for p in promoted.promoted] == [("/a", doc.id, 1)]
        current = (await awren.documents.get(col, doc.id)).version
        assert (await awren.trees.promote(tree)).promoted[0].version == current
        assert (await awren.trees.unassign(tree, "/a"))["removed"] is True

    async def test_collections_query_materialized(self, awren: AsyncWrenClient) -> None:
        col = f"async-q-{uid()}"
        await awren.documents.create(col, {"title": "a", "category": "news"})
        schema = await awren.collections.set_schema(col, schema={"type": "object"}, display_name="{title}")
        assert schema.display_name == "{title}"
        assert (await awren.collections.get_schema(col)).schema == {"type": "object"}
        assert any(c.name == col for c in await awren.collections.list())
        assert (await awren.collections.validate(col)).schema_source == "current"
        assert (await awren.collections.validate(col, {"type": "object"})).schema_source == "proposed"
        assert (await awren.collections.delete_schema(col))["deleted"] is True

        res = await awren.query.run(col, where="category:news", select=["title"], label=None, limit=1)
        assert res.items and res.items[0]["data"] == {"title": "a"}
        assert (await awren.query.run(col, aggregate={"groupBy": ["category"], "metrics": {"n": {"count": "title"}}})).rows

        mq = await awren.materialized.set(col, "m", {"select": ["title"]}, refresh_on="manual")
        assert mq.refresh_on == "manual"
        assert [m.name for m in await awren.materialized.list(col)] == ["m"]
        with pytest.raises(WrenNotFoundError):
            await awren.materialized.get(col, "missing")
        assert (await awren.materialized.delete(col, "m"))["deleted"] is True

        await awren.materialized.set(col, "auto", {"select": ["title"]})
        for _ in range(50):  # the first refresh runs in the background
            try:
                assert (await awren.materialized.get(col, "auto")).result["data"]
                break
            except WrenNotFoundError:
                await asyncio.sleep(0.1)
        else:
            pytest.fail("materialized result never appeared")


def test_errors_are_wren_errors(wren: WrenClient) -> None:
    with pytest.raises(WrenError) as exc:
        wren.documents.get("anything", MISSING)
    assert isinstance(exc.value, WrenNotFoundError)
    assert exc.value.status == 404
