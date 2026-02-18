# PRO plug-ins (private)

This repo supports **private PRO plug-ins** that can register additional tools and handlers at runtime (for example, **BI Option 2** datasets + incremental sync).

## Loading

Core discovers plug-ins via Python entry points:
- group: `mcp_yandex_ad.plugins`

Docker builds can install private plug-ins via:
- `Dockerfile` build arg `MCP_PLUGIN_PIP` (a pip spec, e.g. `package==1.2.3` or a private index URL)

Example (git URL, pinned to tag):
```bash
docker build \
  --build-arg MCP_EDITION=pro \
  --build-arg MCP_PUBLIC_READONLY=false \
  --build-arg MCP_PLUGIN_PIP="git+https://github.com/<OWNER>/<PRIVATE_PLUGIN_REPO>.git@vX.Y.Z" \
  -t yandex-direct-metrica-mcp:pro .
```

Optional dev-only loading (no packaging) is supported via:
- `MCP_PLUGIN_MODULES=module[:attr],...`
  - if `:attr` is omitted, `register` is used

## Plug-in API (minimal contract)

A plug-in can be any of:
- an object with `register(registry)`
- a callable `register(registry)`
- a factory callable that returns one of the above

The `registry` provides:
- `registry.add_tools(list[Tool])`
- `registry.add_tool_handler(name, handler)` where `handler(ctx, args) -> dict`
- `registry.add_prefix_handler(prefix, handler)` where `handler(ctx, name, args) -> dict`

Notes:
- Tool availability is enforced at runtime: if a tool name is not present in `tools/list`, the server rejects the call.
- Public read-only mode hides any `dashboard.dataset.*` tools even if a plug-in is present.

## BI Option 2 (example datasets)

A PRO BI plug-in can provide additional `dashboard.*` tools, for example:
- `dashboard.schema`
- `dashboard.dataset.join_direct_vs_metrica_yclid_daily` (Metrica Logs API export + join by `yclid`/Direct click id; may return `status=pending` with a resumable `request_id`)
- `dashboard.sync.start` / `dashboard.sync.next` (NDJSON; sync may need to retry when a dataset is pending)
