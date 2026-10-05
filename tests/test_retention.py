"""Retention policies: set / get / preview / apply / remove, sync and async."""

from __future__ import annotations

from typing import Optional

import pytest

from wren import (
    AsyncWrenClient,
    RetentionCount,
    RetentionOverview,
    RetentionPolicy,
    RetentionResult,
    WrenClient,
    WrenError,
    WrenNotFoundError,
)

from conftest import WREN_URL, TestUser, create_user


@pytest.fixture(scope="module")
def owner() -> TestUser:
    # Its own org, so the policies don't touch the other test modules' data
    return create_user("retention")


@pytest.fixture
def client(owner: TestUser) -> WrenClient:
    return WrenClient(WREN_URL, api_key=owner.api_key)


def doc_with_versions(wren: WrenClient, collection: str, n: int, label_v1: Optional[str] = None) -> str:
    doc = wren.documents.create(collection, {"title": "v1"})
    for v in range(2, n + 1):
        wren.documents.update(collection, doc.id, {"title": f"v{v}"})
    if label_v1:
        wren.labels.set(collection, doc.id, label_v1, version=1)
    return doc.id


class TestRetention:
    def test_nothing_set_yet(self, client: WrenClient) -> None:
        assert client.retention.get() == RetentionOverview(default=None, collections=[], runs=[])

    def test_set_get_preview_apply_remove(self, client: WrenClient, owner: TestUser) -> None:
        a = doc_with_versions(client, "notes", 4, label_v1="approved")
        doc_with_versions(client, "notes", 4)
        doc_with_versions(client, "posts", 3)

        policy = client.retention.set("notes", max_versions=2)
        assert isinstance(policy, RetentionPolicy)
        assert (policy.collection, policy.labeled_only, policy.max_versions, policy.max_age_days, policy.after_label) == (
            "notes", False, 2, None, None)
        assert policy.updated_by == owner.user_id and policy.updated_at
        default = client.retention.set("*", labeled_only=True, max_age_days=30, after_label="live")
        assert (default.collection, default.labeled_only, default.max_age_days, default.after_label) == ("*", True, 30, "live")
        exempt = client.retention.set("archive")  # no rule: keeps everything
        assert (exempt.labeled_only, exempt.max_versions, exempt.max_age_days, exempt.after_label) == (False, None, None, None)

        overview = client.retention.get()
        assert overview.default is not None and overview.default.collection == "*"
        assert [p.collection for p in overview.collections] == ["archive", "notes"]

        # Saved policy: a loses v2 (v1 is labeled), the other loses v1 and v2
        saved = client.retention.preview("notes")
        assert isinstance(saved, RetentionResult)
        assert (saved.total.versions, saved.total.documents, saved.total.collection) == (3, 2, None)
        assert saved.total.bytes > 0
        assert saved.collections == [RetentionCount(3, 2, saved.total.bytes, "notes")]
        # Proposed rules
        assert client.retention.preview("notes", max_versions=10).total == RetentionCount(0, 0, 0)
        # The default covers posts only
        assert [(c.collection, c.versions) for c in client.retention.preview("*").collections] == [("posts", 2)]
        assert client.versions.get("notes", a, 2).version == 2

        applied = client.retention.apply()
        assert (applied.total.versions, applied.total.documents) == (5, 3)
        assert sorted(c.collection or "" for c in applied.collections) == ["notes", "posts"]
        with pytest.raises(WrenNotFoundError):
            client.versions.get("notes", a, 2)
        assert client.versions.get("notes", a, 1).version == 1
        assert client.documents.get("notes", a).version == 4

        runs = client.retention.get().runs
        assert sorted((r.collection, r.versions_removed, r.triggered_by) for r in runs) == [
            ("notes", 3, owner.user_id), ("posts", 2, owner.user_id)]
        assert runs[0].bytes_freed > 0 and runs[0].ran_at
        assert client.retention.apply().total.versions == 0

        assert client.retention.remove("notes") == {"collection": "notes", "deleted": True}
        assert client.retention.remove("*") == {"collection": "*", "deleted": True}
        with pytest.raises(WrenNotFoundError):
            client.retention.remove("notes")
        assert client.retention.get().default is None
        client.retention.remove("archive")

    def test_invalid_rules_and_internal_collections_raise_400(self, client: WrenClient) -> None:
        with pytest.raises(WrenError) as exc:
            client.retention.set("notes", max_versions=0)
        assert exc.value.status == 400
        with pytest.raises(WrenError) as exc:
            client.retention.preview("_events")
        assert exc.value.status == 400

    async def test_async(self, owner: TestUser) -> None:
        async with AsyncWrenClient(WREN_URL, api_key=owner.api_key) as awren:
            doc = await awren.documents.create("drafts", {"title": "v1"})
            await awren.documents.update("drafts", doc.id, {"title": "v2"})
            await awren.documents.update("drafts", doc.id, {"title": "v3"})
            policy = await awren.retention.set("drafts", max_versions=1)
            assert policy.max_versions == 1
            assert [p.collection for p in (await awren.retention.get()).collections] == ["drafts"]
            preview = await awren.retention.preview("drafts")
            assert (preview.total.versions, preview.total.documents) == (2, 1)
            assert (await awren.retention.preview("drafts", labeled_only=False, max_versions=5)).total.versions == 0
            assert (await awren.retention.apply()).total.versions == 2
            assert (await awren.documents.get("drafts", doc.id)).version == 3
            assert await awren.retention.remove("drafts") == {"collection": "drafts", "deleted": True}
