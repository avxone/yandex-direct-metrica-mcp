# Public vs Pro (tool access model)

Goal: publish a safe public build focused on **read-only** analytics, and keep Direct write operations in a separate **Pro** distribution.

## Public (read-only)

Recommended setting:
- `MCP_PUBLIC_READONLY=true`

Effect:
- Write tools are hidden/blocked (Direct create/update, raw calls).
- Designed for reporting, joins, and dashboard generation.
 - BI Option 2 tools (`dashboard.schema`, `dashboard.dataset.*`, `dashboard.sync.*`) are **not** part of the public surface.

Recommended artifact model (release 1.0.0):
- Public Docker image: `ghcr.io/<OWNER>/yandex-direct-metrica-mcp:<tag>` and `:latest`
  - Safe-by-default: public edition forces read-only even if runtime env vars are misconfigured.
- Pro Docker image: `ghcr.io/<OWNER>/yandex-direct-metrica-mcp-pro:<tag>` (separate artifact)

See also:
- `docs/public-mode.md` (public contract spec)
- `docs/compatibility-semver.md` (compatibility policy)

## Pro (full)

Recommended setting:
- `MCP_PUBLIC_READONLY=false`

Effect:
- Full toolset is available (still guarded by existing safety env flags like `MCP_WRITE_ENABLED`, sandbox-only policies, etc.).
 - Includes BI Option 2 datasets + incremental sync (for warehouse/BI pipelines).
 - Includes HF write tools (guarded by `apply=true`) such as Direct plan/apply and Metrica goals CRUD.

## Why this split

- Reduces risk for public users (no accidental writes).
- Keeps the public surface smaller and easier to support.
- Allows a paid/pro offering without changing the core architecture.
