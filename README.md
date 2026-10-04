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
    wren.trees.set("site", "/blog/hello", doc.id)
```

- Python >= 3.9
- Sync (`WrenClient`) and async (`AsyncWrenClient`) via httpx
- Typed dataclass responses
- Resources: documents, versions, labels, diff, collections, trees, keys, members, invites, permissions

## Links

- **Website:** https://wren.aemwip.com
- **All repos:** [github.com/usewren](https://github.com/usewren)
- **Tutorial:** https://wren.aemwip.com/tutorial
- **API Docs:** https://wren.aemwip.com/docs

## License

Apache-2.0
