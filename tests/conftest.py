"""Shared fixtures for the integration tests.

The tests run against a real WREN server whose URL comes from ``WREN_URL``
(or ``WREN_TEST_URL``); see ``tests/run-local.sh`` for a one-command run
against a throwaway server. Each test module signs up its own user, so every
module works in its own org.
"""

from __future__ import annotations

import os
import secrets
import time
from dataclasses import dataclass
from typing import AsyncIterator, Iterator, Optional

import httpx
import pytest

from wren import AsyncWrenClient, WrenClient

WREN_URL = (os.environ.get("WREN_URL") or os.environ.get("WREN_TEST_URL") or "http://localhost:4000").rstrip("/")


def uid() -> str:
    return f"{int(time.time() * 1000):x}{secrets.token_hex(3)}"


@dataclass
class TestUser:
    __test__ = False  # not a test class, despite the name

    email: str
    password: str
    cookie: str
    api_key: str
    key_id: str
    user_id: str
    slug: str


def _auth_post(path: str, body: object, cookie: Optional[str] = None) -> httpx.Response:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        # better-auth rejects cross-site POSTs, so send the server's own origin
        "Origin": WREN_URL,
    }
    if cookie:
        headers["Cookie"] = cookie
    return httpx.post(f"{WREN_URL}{path}", json=body, headers=headers)


def create_user(prefix: str = "py") -> TestUser:
    """Sign up a fresh user, sign in, and create an API key for their own org."""
    email = f"{prefix}-{uid()}@client-tests.example"
    password = "correct-horse-battery-staple"
    res = _auth_post("/api/auth/sign-up/email", {"email": email, "password": password, "name": f"Test {prefix}"})
    assert res.status_code == 200, res.text
    res = _auth_post("/api/auth/sign-in/email", {"email": email, "password": password})
    assert res.status_code == 200, res.text
    cookie = res.headers["set-cookie"].split(";")[0]

    res = _auth_post("/api/v1/keys", {"name": "client-tests"}, cookie)
    assert res.status_code == 201, res.text
    key = res.json()

    me = httpx.get(
        f"{WREN_URL}/api/v1/me",
        headers={"Accept": "application/json", "Authorization": f"Bearer {key['key']}"},
    ).json()
    return TestUser(
        email=email,
        password=password,
        cookie=cookie,
        api_key=key["key"],
        key_id=key["id"],
        user_id=me["user"]["id"],
        slug=me["org"]["slug"],
    )


def create_key_in_org(user: TestUser, org_id: str) -> str:
    """Create an API key for ``user`` in another org they belong to."""
    headers = {"Content-Type": "application/json", "Accept": "application/json", "Origin": WREN_URL, "Cookie": user.cookie}
    res = httpx.put(f"{WREN_URL}/api/v1/org", json={"orgId": org_id}, headers=headers)
    assert res.status_code == 200, res.text
    res = _auth_post("/api/v1/keys", {"name": "member-key"}, user.cookie)
    assert res.status_code == 201, res.text
    httpx.put(f"{WREN_URL}/api/v1/org", json={"orgId": user.user_id}, headers=headers)
    return str(res.json()["key"])


def upload_asset(api_key: str, collection: str, name: str, content: bytes) -> dict[str, object]:
    """Upload a file to a binary collection (the Python client has no asset methods)."""
    res = httpx.post(
        f"{WREN_URL}/api/v1/{collection}",
        files={"file": (name, content, "text/plain")},
        headers={"Accept": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    assert res.status_code == 201, res.text
    return dict(res.json())


@pytest.fixture(scope="module")
def user() -> TestUser:
    return create_user()


@pytest.fixture
def wren(user: TestUser) -> Iterator[WrenClient]:
    with WrenClient(WREN_URL, api_key=user.api_key) as client:
        yield client


@pytest.fixture
async def awren(user: TestUser) -> AsyncIterator[AsyncWrenClient]:
    async with AsyncWrenClient(WREN_URL, api_key=user.api_key) as client:
        yield client
