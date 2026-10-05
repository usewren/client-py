"""Keys, invites, members, permissions, webhooks and public access (sync + async)."""

from __future__ import annotations

import httpx
import pytest

from wren import (
    ApiKey,
    ApiKeyCreated,
    AsyncWrenClient,
    Invite,
    InviteCreated,
    Member,
    Permission,
    Webhook,
    WebhookCreated,
    WrenClient,
    WrenError,
    WrenForbiddenError,
    WrenNotFoundError,
    WrenUnauthorizedError,
)

from conftest import WREN_URL, TestUser, create_key_in_org, create_user, uid

MISSING = "00000000-0000-0000-0000-000000000000"


def raw(user: TestUser, method: str, path: str, body: object = None) -> httpx.Response:
    """Call the API directly, for steps that should not depend on the client under test."""
    return httpx.request(
        method,
        f"{WREN_URL}/api/v1{path}",
        json=body,
        headers={"Accept": "application/json", "Authorization": f"Bearer {user.api_key}"},
    )


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------


class TestKeys:
    def test_create_list_revoke(self, wren: WrenClient) -> None:
        created = wren.keys.create("ci deploy")
        assert isinstance(created, ApiKeyCreated)
        assert created.key.startswith("wren_")
        assert created.name == "ci deploy"
        assert created.key_prefix == created.key[:12]

        listed = [k for k in wren.keys.list() if k.id == created.id]
        assert len(listed) == 1
        assert isinstance(listed[0], ApiKey)
        assert listed[0].revoked_at is None

        with WrenClient(WREN_URL, api_key=created.key) as fresh:
            fresh.keys.list()
            assert wren.keys.revoke(created.id) == {"id": created.id, "revoked": True}
            with pytest.raises(WrenUnauthorizedError) as exc:
                fresh.keys.list()
            assert exc.value.status == 401

    def test_revoke_unknown_raises_not_found(self, wren: WrenClient) -> None:
        with pytest.raises(WrenNotFoundError) as exc:
            wren.keys.revoke(MISSING)
        assert exc.value.status == 404
        assert str(exc.value) == "Not found"

    def test_create_without_name_raises_400(self, wren: WrenClient) -> None:
        with pytest.raises(WrenError) as exc:
            wren.keys.create("")
        assert exc.value.status == 400
        assert str(exc.value) == "name is required"

    async def test_async_create_list_revoke(self, awren: AsyncWrenClient) -> None:
        created = await awren.keys.create("async key")
        assert created.key.startswith("wren_")
        assert any(k.id == created.id for k in await awren.keys.list())
        assert await awren.keys.revoke(created.id) == {"id": created.id, "revoked": True}


# ---------------------------------------------------------------------------
# Auth and transport
# ---------------------------------------------------------------------------


class TestAuth:
    def test_no_api_key_raises_unauthorized(self) -> None:
        with WrenClient(WREN_URL) as anon:
            with pytest.raises(WrenUnauthorizedError) as exc:
                anon.keys.list()
        assert exc.value.body == {"error": "Unauthorized"}

    def test_invalid_api_key_raises_unauthorized(self) -> None:
        with WrenClient(WREN_URL, api_key="wren_not-a-real-key") as bad:
            with pytest.raises(WrenUnauthorizedError):
                bad.members.list()

    def test_trailing_slash_on_base_url(self, user: TestUser) -> None:
        with WrenClient(WREN_URL + "/", api_key=user.api_key) as c:
            assert isinstance(c.keys.list(), list)

    def test_close_without_context_manager(self, user: TestUser) -> None:
        c = WrenClient(WREN_URL, api_key=user.api_key)
        c.keys.list()
        c.close()
        with pytest.raises(RuntimeError):
            c.keys.list()

    async def test_async_no_api_key_raises_unauthorized(self) -> None:
        async with AsyncWrenClient(WREN_URL) as anon:
            with pytest.raises(WrenUnauthorizedError):
                await anon.keys.list()

    async def test_async_aclose(self, user: TestUser) -> None:
        c = AsyncWrenClient(WREN_URL, api_key=user.api_key)
        await c.members.list()
        await c.aclose()
        with pytest.raises(RuntimeError):
            await c.members.list()

    def test_non_json_bodies_are_returned_as_text(self, wren: WrenClient, user: TestUser) -> None:
        from conftest import upload_asset

        col = f"files-{uid()}"
        assert raw(user, "PUT", f"/{col}/_schema", {"collectionType": "binary"}).status_code == 200
        asset = upload_asset(user.api_key, col, "hello.txt", b"hello world")
        assert wren._http.request("GET", f"/{col}/{asset['id']}/raw") == "hello world"

    async def test_async_non_json_bodies_are_returned_as_text(self, awren: AsyncWrenClient, user: TestUser) -> None:
        from conftest import upload_asset

        col = f"files-{uid()}"
        raw(user, "PUT", f"/{col}/_schema", {"collectionType": "binary"})
        asset = upload_asset(user.api_key, col, "a.txt", b"async bytes")
        assert await awren._http.request("GET", f"/{col}/{asset['id']}/raw") == "async bytes"


# ---------------------------------------------------------------------------
# Invites, members, permissions — two users sharing an org
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def member() -> TestUser:
    return create_user("member")


class TestInvitesMembersPermissions:
    """Ordered scenario: the owner (``user``) invites ``member`` and manages their access."""

    def test_invite_and_accept(self, wren: WrenClient, user: TestUser, member: TestUser) -> None:
        inv = wren.invites.create(member.email, role="member")
        assert isinstance(inv, InviteCreated)
        assert inv.token
        assert inv.email == member.email
        assert inv.role == "member"

        sent = [i for i in wren.invites.list_sent() if i.id == inv.id]
        assert len(sent) == 1 and isinstance(sent[0], Invite)
        assert sent[0].accepted_at is None

        with WrenClient(WREN_URL, api_key=member.api_key) as m:
            assert m.invites.accept(inv.token) == {"accepted": True, "orgId": user.user_id}
            with pytest.raises(WrenError) as exc:
                m.invites.accept(inv.token)
            assert exc.value.status == 409

    def test_create_with_default_role_and_revoke(self, wren: WrenClient) -> None:
        inv = wren.invites.create(f"revoke-{uid()}@client-tests.example")
        assert inv.role == "member"
        assert wren.invites.revoke(inv.id) == {"id": inv.id, "revoked": True}
        assert next(i for i in wren.invites.list_sent() if i.id == inv.id).revoked_at

    def test_received_is_empty_until_email_verified(self, member: TestUser) -> None:
        with WrenClient(WREN_URL, api_key=member.api_key) as m:
            assert m.invites.list_received() == []

    def test_accept_by_id_requires_verified_email(self, wren: WrenClient, member: TestUser) -> None:
        inv = wren.invites.create(member.email)
        with WrenClient(WREN_URL, api_key=member.api_key) as m:
            with pytest.raises(WrenForbiddenError) as exc:
                m.invites.accept_by_id(inv.id)
        assert exc.value.status == 403
        wren.invites.revoke(inv.id)

    def test_members_list(self, wren: WrenClient, member: TestUser) -> None:
        found = [m for m in wren.members.list() if m.user_id == member.user_id]
        assert len(found) == 1 and isinstance(found[0], Member)
        assert found[0].email == member.email
        assert found[0].role == "member"
        assert found[0].joined_at

    def test_permissions_grant_and_revoke_access(self, wren: WrenClient, user: TestUser, member: TestUser) -> None:
        col = f"shared-{uid()}"
        assert raw(user, "POST", f"/{col}", {"title": "secret"}).status_code == 201
        member_key = create_key_in_org(member, user.user_id)

        def member_get(path: str) -> int:
            return httpx.get(
                f"{WREN_URL}/api/v1{path}", headers={"Accept": "application/json", "Authorization": f"Bearer {member_key}"}
            ).status_code

        assert member_get(f"/{col}") == 403

        perm = wren.permissions.create(
            f"member:{member.user_id}", f"collection:{col}", "read", audit_reads=True, label_filter=None
        )
        assert isinstance(perm, Permission)
        assert perm.principal == f"member:{member.user_id}"
        assert perm.access == "read"
        assert perm.audit_reads is True
        assert perm.audit_writes is False
        assert member_get(f"/{col}") == 200

        assert any(p.id == perm.id for p in wren.permissions.list())
        assert wren.permissions.delete(perm.id) == {"id": perm.id, "deleted": True}
        assert member_get(f"/{col}") == 403

        # A plain member may not manage rules
        with WrenClient(WREN_URL, api_key=member_key) as m:
            with pytest.raises(WrenForbiddenError):
                m.permissions.create("*", "*", "admin")

    def test_permissions_create_all_options(self, wren: WrenClient) -> None:
        perm = wren.permissions.create(
            "*",
            f"collection:pub-{uid()}",
            "read",
            alias=f"a{uid()}",
            label_filter="published",
            filter_lang="jmespath",
            filter_expr="title",
            audit_writes=True,
        )
        assert perm.label_filter == "published"
        assert perm.filter_lang == "jmespath"
        assert perm.filter_expr == "title"
        assert perm.alias
        assert perm.audit_writes is True
        wren.permissions.delete(perm.id)

    def test_permissions_create_invalid_access_raises_400(self, wren: WrenClient) -> None:
        with pytest.raises(WrenError) as exc:
            wren.permissions.create("*", "*", "everything")
        assert exc.value.status == 400

    def test_permissions_update(self, wren: WrenClient) -> None:
        perm = wren.permissions.create("*", f"collection:upd-{uid()}", "read")
        updated = wren.permissions.update(perm.id, access="write", audit_reads=True)
        assert isinstance(updated, Permission)
        assert updated.access == "write"
        assert updated.audit_reads is True
        wren.permissions.delete(perm.id)

    def test_members_remove(self, wren: WrenClient, member: TestUser) -> None:
        assert wren.members.remove(member.user_id) == {"userId": member.user_id, "removed": True}
        assert all(m.user_id != member.user_id for m in wren.members.list())
        with pytest.raises(WrenNotFoundError):
            wren.members.remove(member.user_id)


class TestAsyncInvitesMembersPermissions:
    async def test_full_flow(self, awren: AsyncWrenClient, user: TestUser) -> None:
        other = create_user("amember")
        inv = await awren.invites.create(other.email, role="admin")
        assert inv.role == "admin"
        assert any(i.id == inv.id for i in await awren.invites.list_sent())
        async with AsyncWrenClient(WREN_URL, api_key=other.api_key) as o:
            assert await o.invites.list_received() == []
            assert (await o.invites.accept(inv.token))["accepted"] is True
            extra = await awren.invites.create(other.email)
            with pytest.raises(WrenForbiddenError):
                await o.invites.accept_by_id(extra.id)
        assert (await awren.invites.revoke(extra.id))["revoked"] is True

        members = await awren.members.list()
        assert any(m.user_id == other.user_id and m.role == "admin" for m in members)

        perm = await awren.permissions.create(f"member:{other.user_id}", "collection:*", "write")
        assert perm.access == "write"
        assert any(p.id == perm.id for p in await awren.permissions.list())
        assert (await awren.permissions.update(perm.id, access="read")).access == "read"
        assert (await awren.permissions.delete(perm.id))["deleted"] is True

        assert (await awren.members.remove(other.user_id))["removed"] is True


# ---------------------------------------------------------------------------
# Public access
# ---------------------------------------------------------------------------


class TestPublicAccess:
    def test_public_rule_with_label_filter(self, wren: WrenClient, user: TestUser) -> None:
        col = f"public-{uid()}"
        a = raw(user, "POST", f"/{col}", {"title": "published one"}).json()
        raw(user, "POST", f"/{col}", {"title": "draft"})
        public_url = f"{WREN_URL}/api/v1/orgs/{user.slug}/{col}"
        assert httpx.get(public_url).status_code == 403  # nothing is public by default

        perm = wren.permissions.create("*", f"collection:{col}", "read", label_filter="published")
        assert perm.label_filter == "published"
        raw(user, "POST", f"/{col}/{a['id']}/labels", {"label": "published"})
        raw(user, "PUT", f"/{col}/{a['id']}", {"title": "unpublished edit"})

        res = httpx.get(public_url)
        assert res.status_code == 200
        items = res.json()["items"]
        assert [i["id"] for i in items] == [a["id"]]
        assert items[0]["data"]["title"] == "published one"


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------


class TestWebhooks:
    def test_create_list_deliveries_replay_delete(self, wren: WrenClient, user: TestUser) -> None:
        created = wren.webhooks.create("http://localhost:9/hook", events=["document.created"])
        assert isinstance(created, WebhookCreated)
        assert created.secret
        assert created.events == ["document.created"]
        assert created.enabled is True
        assert created.consec_failures == 0

        listed = [w for w in wren.webhooks.list() if w.id == created.id]
        assert len(listed) == 1 and isinstance(listed[0], Webhook)
        assert listed[0].url == "http://localhost:9/hook"

        assert isinstance(wren.webhooks.deliveries(created.id), list)

        raw(user, "POST", f"/hooked-{uid()}", {"title": "event"})
        replay = wren.webhooks.replay(created.id, "2000-01-01T00:00:00Z")
        assert isinstance(replay["replayed"], int)
        replay = wren.webhooks.replay(created.id, "2000-01-01T00:00:00Z", until="2000-01-02T00:00:00Z")
        assert replay["replayed"] == 0

        assert wren.webhooks.delete(created.id) == {"id": created.id, "deleted": True}
        with pytest.raises(WrenNotFoundError):
            wren.webhooks.deliveries(created.id)

    def test_create_without_events_subscribes_to_all(self, wren: WrenClient) -> None:
        created = wren.webhooks.create("http://localhost:9/all")
        assert created.events == []
        wren.webhooks.delete(created.id)

    def test_create_with_private_address_raises_400(self, wren: WrenClient) -> None:
        with pytest.raises(WrenError) as exc:
            wren.webhooks.create("http://10.0.0.1/hook")
        assert exc.value.status == 400

    def test_update(self, wren: WrenClient) -> None:
        created = wren.webhooks.create("http://localhost:9/upd")
        assert wren.webhooks.update(created.id, enabled=False, events=["label.set"]) == {"id": created.id, "updated": True}
        after = next(w for w in wren.webhooks.list() if w.id == created.id)
        assert after.enabled is False
        assert after.events == ["label.set"]
        wren.webhooks.delete(created.id)

    async def test_async_webhooks(self, awren: AsyncWrenClient) -> None:
        created = await awren.webhooks.create("http://localhost:9/async", events=["label.set"])
        assert created.secret
        assert any(w.id == created.id for w in await awren.webhooks.list())
        assert await awren.webhooks.deliveries(created.id) == []
        assert (await awren.webhooks.replay(created.id, "2100-01-01T00:00:00Z"))["replayed"] == 0
        assert (await awren.webhooks.update(created.id, enabled=False))["updated"] is True
        assert not next(w for w in await awren.webhooks.list() if w.id == created.id).enabled
        assert (await awren.webhooks.delete(created.id))["deleted"] is True
