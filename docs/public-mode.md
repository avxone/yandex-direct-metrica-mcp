# Public Mode (v1.0.0 contract)

This document defines the **public read-only** contract for the `yandex-direct-metrica-mcp` Docker image.

## Definition: “read-only” (Contract A)

Read-only means:
- No changes to **managed entities** in Direct/Metrica/Audience (no create/update/delete of campaigns, segments, goals, etc.).

Allowed provider-side side effects (still treated as read-only in this contract):
- Wordstat operations that create/compute report-like data.
- Metrica Logs API export jobs (`metrica.logs_export`) used for analysis/joins (no counter configuration changes).

## Contract surface: tools/list

The public contract is the exact output of `tools/list` for the **public edition**.

Stability guarantee (1.x):
- Tool `name`, `description`, and `inputSchema` are contractually stable.
- The canonical snapshot is stored in `tests/snapshots/public_tools_v1.json`.

## Public artifact model

Public image:
- `ghcr.io/<OWNER>/yandex-direct-metrica-mcp:v1.0.0`
- `ghcr.io/<OWNER>/yandex-direct-metrica-mcp:latest` (stable public)

Pro image (separate artifact, out of public contract):
- `ghcr.io/<OWNER>/yandex-direct-metrica-mcp-pro:v1.0.0`
- `ghcr.io/<OWNER>/yandex-direct-metrica-mcp-pro:latest`

## Safe-by-default guarantee

The **public image** is safe-by-default:
- it includes a build marker (`/app/.mcp_edition=public`)
- the server forces `public_readonly=true` at runtime even if env vars are misconfigured.

Meaning:
- Write tools are not returned by `tools/list`.
- Any attempt to call write-capable entrypoints is rejected with a predictable write-guard error.

## Environment matrix (public)

### Allowed / honored

Credentials (no secrets stored on disk by the server):
- `YANDEX_ACCESS_TOKEN` / `YANDEX_REFRESH_TOKEN`
- `YANDEX_CLIENT_ID` / `YANDEX_CLIENT_SECRET`
- `YANDEX_AUDIENCE_*` (Audience OAuth)
- `YANDEX_WORDSTAT_*` (Wordstat OAuth)

Multi-account registry:
- `MCP_ACCOUNTS_FILE` (read-only mapping `account_id` → Direct `Client-Login` + Metrica counter defaults)

Runtime tuning:
- `MCP_CONTENT_MODE`
- `MCP_CACHE_ENABLED`, `MCP_CACHE_TTL_SECONDS`
- `MCP_*_RATE_LIMIT_RPS`
- `MCP_RETRY_*`
- `MCP_AUDIENCE_ENABLED`, `MCP_WORDSTAT_ENABLED`

### Ignored / forced off (public)

Write-enabling flags are ignored in the public image:
- `MCP_WRITE_ENABLED`
- `HF_WRITE_ENABLED`
- `HF_DESTRUCTIVE_ENABLED`
- `MCP_ACCOUNTS_WRITE_ENABLED`

Escape hatches are not part of the public surface:
- `direct.raw_call`, `metrica.raw_call`, `audience.raw_call`

BI Option 2 is not part of the public surface:
- `dashboard.schema`, `dashboard.dataset.*`, `dashboard.sync.*`

## /data state (public)

Recommended mounted state folder (example: `/data`):
- `accounts.json` (optional): account registry used for multi-account dashboards and `account_id` resolution.

The server does not persist OAuth tokens or user data.
If cache is enabled, the cache may store bounded API responses (no raw tokens).

