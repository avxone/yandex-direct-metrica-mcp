# Publishing (Docker + GHCR) — 2026-01-29 (updated for v1.0.0)

This project publishes Docker images to **GHCR** (GitHub Container Registry).

## Artifacts (Public vs Pro)

Public (read-only, safe-by-default):
- `ghcr.io/<OWNER>/yandex-direct-metrica-mcp:<tag>`
- `ghcr.io/<OWNER>/yandex-direct-metrica-mcp:latest` (stable public)

Pro (separate artifact; intended for paid subscribers; keep GHCR package private):
- `ghcr.io/<OWNER>/yandex-direct-metrica-mcp-pro:<tag>`
- `ghcr.io/<OWNER>/yandex-direct-metrica-mcp-pro:latest` (only when you explicitly publish PRO)

## CI / Workflows

- Tests: `.github/workflows/ci.yml` (pytest, blocking)
- Docker publish (public): `.github/workflows/docker-publish-public.yml`
  - triggers: push to `main` and tags `v*`
  - publishes `:latest` only when pushing a tag
- Docker publish (pro): `.github/workflows/docker-publish-pro.yml`
  - triggers: manual `workflow_dispatch` or tags `pro-v*`

## How to release public

1) Ensure CI is green on `main`.
2) Create and push a tag:
   - `vX.Y.Z`
3) The public publish workflow builds and pushes:
   - `ghcr.io/<OWNER>/yandex-direct-metrica-mcp:vX.Y.Z`
   - `ghcr.io/<OWNER>/yandex-direct-metrica-mcp:latest`

## How to release PRO (restricted)

Recommended:
- Keep `yandex-direct-metrica-mcp-pro` package **private** in GHCR.
- Publish PRO only on demand:
  - manual run (`workflow_dispatch`), or
  - a `pro-vX.Y.Z` tag.

## Manual publish (optional)

If you need to publish manually from your machine, use `docker buildx`:

Public:
```bash
export GHCR_OWNER="<OWNER>"
export VERSION="1.0.0"

echo "<GITHUB_PAT>" | docker login ghcr.io -u "$GHCR_OWNER" --password-stdin

docker buildx build --platform linux/amd64,linux/arm64 \
  --build-arg MCP_PUBLIC_READONLY=true \
  --build-arg MCP_EDITION=public \
  -t "ghcr.io/$GHCR_OWNER/yandex-direct-metrica-mcp:$VERSION" \
  -t "ghcr.io/$GHCR_OWNER/yandex-direct-metrica-mcp:latest" \
  --push .
```

Pro:
```bash
export GHCR_OWNER="<OWNER>"
export VERSION="1.0.0"

echo "<GITHUB_PAT>" | docker login ghcr.io -u "$GHCR_OWNER" --password-stdin

docker buildx build --platform linux/amd64,linux/arm64 \
  --build-arg MCP_PUBLIC_READONLY=false \
  --build-arg MCP_EDITION=pro \
  -t "ghcr.io/$GHCR_OWNER/yandex-direct-metrica-mcp-pro:$VERSION" \
  -t "ghcr.io/$GHCR_OWNER/yandex-direct-metrica-mcp-pro:latest" \
  --push .
```

## Connecting images to Claude Code

Public:
```bash
claude mcp add yandex-direct-metrica-mcp -- \
  docker run --rm -i \
    --env-file /path/to/your/state/.env \
    -e MCP_ACCOUNTS_FILE=/data/accounts.json \
    -v /path/to/your/state:/data \
    ghcr.io/<OWNER>/yandex-direct-metrica-mcp:latest
```

Pro:
```bash
claude mcp add yandex-direct-metrica-mcp-pro -- \
  docker run --rm -i \
    --env-file /path/to/your/state/.env \
    -e MCP_ACCOUNTS_FILE=/data/accounts.json \
    -v /path/to/your/state:/data \
    ghcr.io/<OWNER>/yandex-direct-metrica-mcp-pro:<TAG>
```

