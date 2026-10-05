"""Server 0.9/0.10 features (sync + async): unchanged writes and force, conditional
writes (if_version -> 412), restore to a label, undelete, label removal, deep and
label diffs, schema PATCH and files by name."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from wren import (
    AsyncWrenClient,
    LabelRemoved,
    RestoreResult,
    TreeRestoreResult,
    UndeleteResult,
    WrenClient,
    WrenError,
    WrenNotFoundError,
    WrenVersionMismatchError,
)
from wren._http import _condition, _raise_for_status

from conftest import uid


class TestUnchangedAndConditional:
    def test_unchanged_and_force(self, wren: WrenClient) -> None:
        col = f"same-{uid()}"
        doc = wren.documents.create(col, {"a": 1, "b": {"c": [1, 2]}})
        assert doc.unchanged is None
        again = wren.documents.update(col, doc.id, {"b": {"c": [1, 2]}, "a": 1})
        assert again.version == 1 and again.unchanged is True
        forced = wren.documents.update(col, doc.id, {"a": 1, "b": {"c": [1, 2]}}, force=True)
        assert forced.version == 2 and forced.unchanged is None

        keyed = f"samek-{uid()}"
        wren.collections.set_schema(keyed, natural_key="slug")
        first = wren.documents.upsert_by_key(keyed, "x1", {"slug": "x1", "n": 1})
        assert first.natural_key == "x1" and first.unchanged is None
        same = wren.documents.upsert_by_key(keyed, "x1", {"n": 1, "slug": "x1"})
        assert (same.version, same.unchanged, same.natural_key) == (1, True, "x1")
        assert wren.documents.upsert_by_key(keyed, "x1", {"slug": "x1", "n": 1}, force=True).version == 2

    def test_if_version_by_id(self, wren: WrenClient) -> None:
        col = f"cond-{uid()}"
        doc = wren.documents.create(col, {"n": 1})
        assert wren.documents.update(col, doc.id, {"n": 2}, if_version=1).version == 2
        with pytest.raises(WrenVersionMismatchError) as exc:
            wren.documents.update(col, doc.id, {"n": 3}, if_version=1)
        assert exc.value.status == 412 and exc.value.current_version == 2
        assert isinstance(exc.value, WrenError)
        assert wren.documents.get(col, doc.id).data == {"n": 2}
        assert wren.documents.update(col, doc.id, {"n": 3}, if_version="*").version == 3
        with pytest.raises(WrenVersionMismatchError):
            wren.documents.delete(col, doc.id, if_version=1)
        assert wren.documents.delete(col, doc.id, if_version=3) == {"id": doc.id, "deleted": True}

    def test_if_version_by_key(self, wren: WrenClient) -> None:
        col = f"condkey-{uid()}"
        wren.collections.set_schema(col, natural_key="sku")
        assert wren.documents.upsert_by_key(col, "a1", {"sku": "a1", "qty": 5}, if_version=0).version == 1
        with pytest.raises(WrenVersionMismatchError) as exc:  # create-only must not overwrite
            wren.documents.upsert_by_key(col, "a1", {"sku": "a1", "qty": 0}, if_version=0)
        assert exc.value.current_version == 1
        with pytest.raises(WrenVersionMismatchError) as exc:  # "*" only updates
            wren.documents.upsert_by_key(col, "b2", {"sku": "b2"}, if_version="*")
        assert exc.value.current_version == 0
        assert wren.documents.upsert_by_key(col, "a1", {"sku": "a1", "qty": 4}, if_version="*").version == 2
        with pytest.raises(WrenVersionMismatchError):
            wren.documents.delete_by_key(col, "a1", if_version=1)
        assert wren.documents.delete_by_key(col, "a1", if_version=2)["deleted"] is True

    def test_if_version_type_checked(self, wren: WrenClient) -> None:
        with pytest.raises(TypeError):
            wren.documents.update("x", "y", {}, if_version="3")
        with pytest.raises(TypeError):
            _condition(True)

    def test_412_mapping(self) -> None:
        with pytest.raises(WrenVersionMismatchError) as exc:
            _raise_for_status(412, {"error": "Version mismatch", "currentVersion": 7})
        assert exc.value.current_version == 7 and str(exc.value) == "Version mismatch"
        with pytest.raises(WrenVersionMismatchError) as exc:
            _raise_for_status(412, "Precondition Failed")
        assert exc.value.current_version == 0


class TestRestoreUndeleteLabels:
    def test_collection_restore(self, wren: WrenClient) -> None:
        col = f"rest-{uid()}"
        a = wren.documents.create(col, {"name": "a1"})
        b = wren.documents.create(col, {"name": "b1"})
        c = wren.documents.create(col, {"name": "c1"})
        for d in (a, b, c):
            wren.labels.set(col, d.id, "fixture")
        wren.documents.update(col, a.id, {"name": "a2"})
        wren.documents.delete(col, b.id)
        made = wren.documents.create(col, {"name": "made by the test"})

        res = wren.documents.restore(col, "fixture", delete_unlabeled=True)
        assert res == RestoreResult(label="fixture", restored=1, undeleted=1, deleted=1, unchanged=1, collections=[col])
        assert wren.documents.get(col, a.id).data == {"name": "a1"}
        assert wren.documents.get(col, b.id).data == {"name": "b1"}
        with pytest.raises(WrenNotFoundError):
            wren.documents.get(col, made.id)

        # Without delete_unlabeled, documents without the label stay
        extra = wren.documents.create(col, {"name": "e"})
        again = wren.documents.restore(col, "fixture")
        assert (again.restored, again.deleted, again.unchanged) == (0, 0, 3)
        assert wren.documents.get(col, extra.id).id == extra.id
        with pytest.raises(WrenNotFoundError):
            wren.documents.restore(col, "nope")

    def test_tree_restore(self, wren: WrenClient) -> None:
        col = f"rtpages-{uid()}"
        tree = f"rt-{uid()}"
        page = wren.documents.create(col, {"title": "v1"})
        wren.trees.assign(tree, "/index", page.id)
        wren.trees.promote(tree, label="release-1")
        wren.documents.update(col, page.id, {"title": "v2"})
        res = wren.trees.restore(tree, "release-1")
        assert isinstance(res, TreeRestoreResult)
        assert (res.tree, res.label, res.restored, res.collections) == (tree, "release-1", 1, [col])
        assert wren.documents.get(col, page.id).data == {"title": "v1"}
        with pytest.raises(WrenNotFoundError):
            wren.trees.restore(tree, "nope")

    def test_undelete(self, wren: WrenClient) -> None:
        col = f"undel-{uid()}"
        doc = wren.documents.create(col, {"v": 1})
        wren.documents.update(col, doc.id, {"v": 2})
        wren.documents.delete(col, doc.id)
        assert wren.documents.undelete(col, doc.id) == UndeleteResult(id=doc.id, undeleted=True, version=2)
        assert wren.documents.get(col, doc.id).data == {"v": 2}
        assert len(wren.versions.list(col, doc.id).versions) == 2
        with pytest.raises(WrenNotFoundError):  # not deleted
            wren.documents.undelete(col, doc.id)

        keyed = f"undelk-{uid()}"
        wren.collections.set_schema(keyed, natural_key="slug")
        old = wren.documents.upsert_by_key(keyed, "k", {"slug": "k", "n": 1})
        wren.documents.delete_by_key(keyed, "k")
        wren.documents.upsert_by_key(keyed, "k", {"slug": "k", "n": 2})
        with pytest.raises(WrenError) as exc:  # the natural key is taken
            wren.documents.undelete(keyed, old.id)
        assert exc.value.status == 409

    def test_label_remove(self, wren: WrenClient) -> None:
        col = f"unlab-{uid()}"
        doc = wren.documents.create(col, {"v": 1})
        wren.labels.set(col, doc.id, "snap")
        assert wren.labels.remove(col, doc.id, "snap") == LabelRemoved(id=doc.id, label="snap", removed=True, version=1)
        with pytest.raises(WrenNotFoundError):
            wren.labels.remove(col, doc.id, "snap")
        with pytest.raises(WrenNotFoundError):
            wren.documents.get(col, doc.id, label="snap")


class TestDiffSchemaFiles:
    def test_diff_deep_and_labels(self, wren: WrenClient) -> None:
        col = f"diff-{uid()}"
        doc = wren.documents.create(col, {"a": {"b": 1, "c": [1, 2]}, "x": 1})
        wren.labels.set(col, doc.id, "before")
        wren.documents.update(col, doc.id, {"a": {"b": 2, "c": [1, 2, 3]}, "x": 1})
        shallow = wren.diff.compare(col, doc.id, "before", 2)
        assert shallow.v1 == 1 and [d.path for d in shallow.diff] == ["/a"]
        deep = wren.diff.compare(col, doc.id, "before", 2, deep=True)
        by_path = {d.path: d for d in deep.diff}
        assert set(by_path) == {"/a/b", "/a/c/2"}
        assert (by_path["/a/b"].op, by_path["/a/b"].value, by_path["/a/b"].old_value) == ("replace", 2, 1)
        with pytest.raises(WrenNotFoundError):
            wren.diff.compare(col, doc.id, "nope", 2)

    def test_patch_schema(self, wren: WrenClient) -> None:
        col = f"patch-{uid()}"
        wren.collections.set_schema(
            col, schema={"type": "object", "required": ["sku"]}, display_name="Stock", list_columns=["sku"]
        )
        wren.documents.create(col, {"sku": "p1"})
        res = wren.collections.patch_schema(col, natural_key="sku")
        assert (res.natural_key, res.display_name, res.list_columns, res.keys_registered) == ("sku", "Stock", ["sku"], 1)
        assert res.schema == {"type": "object", "required": ["sku"]}
        cleared = wren.collections.patch_schema(col, {"displayName": None})
        assert cleared.display_name is None and cleared.natural_key == "sku"
        assert wren.collections.get_schema(col).keys_registered is None
        with pytest.raises(WrenError) as exc:  # unknown fields are refused
            wren.collections.patch_schema(col, {"naturalkey": "sku"})
        assert exc.value.status == 400
        fresh = wren.collections.patch_schema(f"patchnew-{uid()}", collection_type="binary", natural_key="filename")
        assert (fresh.collection_type, fresh.natural_key) == ("binary", "filename")

    def test_files_by_name(self, wren: WrenClient, tmp_path: Path) -> None:
        col = f"byname-{uid()}"
        wren.collections.patch_schema(col, collection_type="binary", natural_key="filename")
        created = wren.files.upload_by_name(col, "logo.svg", b"<svg>1</svg>", if_version=0)
        assert (created.version, created.natural_key, created.data["filename"]) == (1, "logo.svg", "logo.svg")
        assert created.data["mimeType"] == "image/svg+xml"
        same = wren.files.upload_by_name(col, "logo.svg", io.BytesIO(b"<svg>1</svg>"))
        assert (same.version, same.unchanged) == (1, True)
        path = tmp_path / "logo.svg"
        path.write_bytes(b"<svg>2</svg>")
        nxt = wren.files.upload_by_name(col, "logo.svg", str(path), if_version=1)
        assert nxt.version == 2 and nxt.id == created.id
        with pytest.raises(WrenVersionMismatchError) as exc:
            wren.files.upload_by_name(col, "logo.svg", path, if_version=1)
        assert exc.value.current_version == 2

        wren.labels.set(col, created.id, "v1", version=1)
        assert wren.files.download_by_name(col, "logo.svg") == b"<svg>2</svg>"
        assert wren.files.download_by_name(col, "logo.svg", version=1) == b"<svg>1</svg>"
        assert wren.files.download_by_name(col, "logo.svg", label="v1") == b"<svg>1</svg>"
        with pytest.raises(WrenNotFoundError):
            wren.files.download_by_name(col, "missing.svg")

        blob = wren.files.upload_by_name(col, "data.unknownext", bytearray(b"\x00\x01"), content_type=None)
        assert blob.data["mimeType"] == "application/octet-stream"
        typed = wren.files.upload_by_name(col, "notes", b"hi", content_type="text/plain")
        assert typed.version == 1 and wren.files.download_by_name(col, "notes") == b"hi"
        assert typed.data["mimeType"].startswith("text/plain"), typed.data


class TestAsync:
    async def test_writes_restore_undelete_labels(self, awren: AsyncWrenClient) -> None:
        col = f"async-v-{uid()}"
        doc = await awren.documents.create(col, {"n": 1})
        assert (await awren.documents.update(col, doc.id, {"n": 1})).unchanged is True
        assert (await awren.documents.update(col, doc.id, {"n": 1}, force=True)).version == 2
        await awren.labels.set(col, doc.id, "fixture")
        with pytest.raises(WrenVersionMismatchError) as exc:
            await awren.documents.update(col, doc.id, {"n": 2}, if_version=1)
        assert exc.value.current_version == 2
        assert (await awren.documents.update(col, doc.id, {"n": 2}, if_version=2)).version == 3

        res = await awren.documents.restore(col, "fixture", delete_unlabeled=True)
        assert (res.label, res.restored, res.collections) == ("fixture", 1, [col])
        assert (await awren.documents.get(col, doc.id)).data == {"n": 1}

        removed = await awren.labels.remove(col, doc.id, "fixture")
        assert (removed.removed, removed.version) == (True, 2)
        diff = await awren.diff.compare(col, doc.id, 3, 4, deep=True)
        assert [(d.op, d.path) for d in diff.diff] == [("replace", "/n")]

        with pytest.raises(WrenVersionMismatchError):
            await awren.documents.delete(col, doc.id, if_version=1)
        await awren.documents.delete(col, doc.id, if_version="*")
        undeleted = await awren.documents.undelete(col, doc.id)
        assert (undeleted.undeleted, undeleted.version) == (True, 4)

        keyed = f"async-vk-{uid()}"
        await awren.collections.set_schema(keyed, natural_key="sku")
        made = await awren.documents.upsert_by_key(keyed, "a", {"sku": "a"}, if_version=0)
        same = await awren.documents.upsert_by_key(keyed, "a", {"sku": "a"}, if_version="*")
        assert (same.id, same.unchanged) == (made.id, True)
        assert (await awren.documents.upsert_by_key(keyed, "a", {"sku": "a"}, force=True)).version == 2
        with pytest.raises(WrenVersionMismatchError):
            await awren.documents.delete_by_key(keyed, "a", if_version=1)
        assert (await awren.documents.delete_by_key(keyed, "a", if_version=2))["deleted"] is True

    async def test_tree_schema_files(self, awren: AsyncWrenClient) -> None:
        col = f"async-rt-{uid()}"
        tree = f"async-tree-{uid()}"
        page = await awren.documents.create(col, {"title": "v1"})
        await awren.trees.assign(tree, "/p", page.id)
        await awren.trees.promote(tree, label="release")
        await awren.documents.update(col, page.id, {"title": "v2"})
        res = await awren.trees.restore(tree, "release")
        assert (res.tree, res.restored) == (tree, 1)

        files = f"async-files-{uid()}"
        schema = await awren.collections.patch_schema(files, collection_type="binary", natural_key="filename")
        assert schema.natural_key == "filename"
        up = await awren.files.upload_by_name(files, "a.txt", b"one", content_type="text/plain", if_version=0)
        assert up.version == 1
        with pytest.raises(WrenVersionMismatchError):
            await awren.files.upload_by_name(files, "a.txt", b"two", if_version=0)
        await awren.files.upload_by_name(files, "a.txt", b"two")
        assert await awren.files.download_by_name(files, "a.txt") == b"two"
        assert await awren.files.download_by_name(files, "a.txt", version=1) == b"one"
        await awren.labels.set(files, up.id, "first", version=1)
        assert await awren.files.download_by_name(files, "a.txt", label="first") == b"one"
