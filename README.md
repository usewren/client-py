# WREN Python Client

Official Python client for the [WREN](https://wren.aemwip.com) API.

```bash
pip install usewren-client
```

```python
from wren import WrenClient

with WrenClient("https://wren.aemwip.com", api_key="wren_...") as wren:
    doc = wren.documents.create("articles", {"title": "Hello"})
    wren.labels.set("articles", doc.id, "published")
    wren.trees.assign("site", "/blog/hello", doc.id)

    # Promote a whole tree atomically: point "published" at every document's
    # "preview" version in one transaction (omit from_ to promote current versions).
    result = wren.trees.promote("site", label="published", from_="preview")
    for p in result.promoted:
        print(p.path, p.collection, p.version)

    page = wren.documents.list("articles", where="title:Hello", limit=20, offset=0)
    pinned = wren.documents.get("articles", doc.id, label="published")
```

```python
import asyncio
from wren import AsyncWrenClient

async def main() -> None:
    async with AsyncWrenClient("https://wren.aemwip.com", api_key="wren_...") as wren:
        doc = await wren.documents.create("articles", {"title": "Hello"})
        await wren.labels.set("articles", doc.id, "published")

asyncio.run(main())
```

Retention policies (org owner or admin) remove old versions; a document's current version and every labeled version are always kept:

```python
result = wren.retention.preview("*", max_versions=20)  # what it would remove; changes nothing
print(result.total.versions, result.total.documents, result.total.bytes)
wren.retention.set("*", max_versions=20)               # org default
wren.retention.set("contracts")                         # no rule: keep everything
wren.retention.apply()                                  # now, or wait for the hourly run
```

- Python >= 3.9
- Sync (`WrenClient`) and async (`AsyncWrenClient`) via httpx
- Typed dataclass responses
- Resources: documents, versions, labels, diff, collections, trees, query, materialized, keys, members, invites, permissions, webhooks, retention

## Running the tests

The tests in `tests/` are integration tests: they run against a real WREN server and
sign up their own throwaway users. With Docker and the WREN sources checked out next to
this repo (`../sandbox`, `../db`, `../auth` …), one command builds the server image,
starts Postgres and the server on a private network, runs pytest with coverage and
cleans up:

```bash
sh tests/run-local.sh                    # all tests
sh tests/run-local.sh tests/test_org.py -k webhooks
```

Against a server you already run:

```bash
pip install -e ".[dev]"
WREN_URL=http://localhost:4000 pytest --cov
```

Use a disposable server only — the tests create users, keys, invites and webhooks.

## Links

- **Website:** https://wren.aemwip.com
- **All repos:** [github.com/usewren](https://github.com/usewren)
- **Tutorial:** https://wren.aemwip.com/tutorial
- **API Docs:** https://wren.aemwip.com/docs

## License

Apache-2.0
