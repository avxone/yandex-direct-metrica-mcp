---
name: yandexad-release-distribution
description: Release, PR hygiene, docs bilingual policy, and Docker image distribution (GHCR/Docker Hub + docker/mcp-registry Option A) for yandex-direct-metrica-mcp.
---

# YandexAd Release & Distribution

Use this skill when you need to:
- Prepare a release (SemVer, changelog, tag, GitHub release).
- Ensure public vs pro separation (public read-only only).
- Publish/verify Docker images in GHCR and Docker Hub.
- Maintain bilingual docs (`docs/` EN, `docs/ru/` RU).
- Submit the server to Docker MCP Registry (`docker/mcp-registry`) using **Option A** (Docker-built `mcp/<name>` image).

## Non-negotiables (safety + contract)

- **Public** must be **read-only** and **safe-by-default**.
- **Pro** must never be auto-published publicly; keep PRO distribution gated/private.
- Never commit secrets; never log raw tokens.
- Do not add tools outside the approved proposals without explicit approval.

## PR hygiene

- Keep PRs scoped (docs vs code vs CI).
- Run `pytest -q` before committing.
- When using `gh pr create` / `gh pr comment` in a shell, avoid backticks in inline strings.
  - Prefer `--body-file` to prevent shell expansion.

## Docs policy (official set)

- English official docs: `docs/`
- Russian official docs: `docs/ru/`
- Remove any machine-specific paths from docs (`/Users/...`, `~/...`); use `/path/to/...`.
- Ensure the docs site cross-links languages:
  - `docs/index.html` links to `ru/`
  - `docs/ru/index.html` links to `../`

## Release checklist (public)

1) Tests
- `pytest -q`

2) Version + changelog
- Update version in `pyproject.toml`.
- Update `CHANGELOG.md` (new release section; latest first).

3) Tag
- `git tag vX.Y.Z`
- `git push origin vX.Y.Z`

4) GitHub Release
- Create release notes emphasizing:
  - public read-only contract
  - pro is separate and gated/private

## Docker build defaults (required for external builders)

Docker MCP Registry Option A builds from your repo without your GH Actions build-args.
Therefore the root `Dockerfile` must default to:
- `ARG MCP_EDITION=public`
- `ARG MCP_PUBLIC_READONLY=true`

Building PRO locally must require explicit build args:
```bash
docker build --build-arg MCP_EDITION=pro --build-arg MCP_PUBLIC_READONLY=false -t yandex-direct-metrica-mcp:pro .
```

## Distribution channels

### GHCR (primary)

Expected tags:
- `ghcr.io/<owner>/yandex-direct-metrica-mcp:vX.Y.Z`
- `ghcr.io/<owner>/yandex-direct-metrica-mcp:latest` (stable public)

Verification tip:
- Validate manifest existence/digest via registry HTTP calls (UI can lag/cache).

### Docker Hub (optional mirror)

Build from the git tag for reproducibility:
```bash
git checkout vX.Y.Z
docker buildx build --platform linux/amd64,linux/arm64 --push \
  -t docker.io/<owner>/yandex-direct-metrica-mcp:vX.Y.Z \
  -t docker.io/<owner>/yandex-direct-metrica-mcp:latest \
  --build-arg MCP_PUBLIC_READONLY=true \
  --build-arg MCP_EDITION=public \
  .
```

## Docker MCP Registry (Option A)

Goal: get a Docker-built image in the Docker Hub `mcp/` namespace.

Constraints:
- Must pin `source.commit` (40-char lowercase SHA1).
- Ensure secret names use `prefix.name` format.
- `run.env.MCP_PUBLIC_READONLY` must be `"true"`.
- CI may require maintainer approval for workflows on fork PRs (expected).

Suggested `server.yaml` shape:
- `name: yandex-direct-metrica-mcp`
- `image: mcp/yandex-direct-metrica-mcp`
- `source.project: https://github.com/<owner>/yandex-direct-metrica-mcp`
- `source.commit: <pinned-sha>`
- `run.volumes`: mount configurable host `state_dir` to `/data`
- `config.secrets`: at least `YANDEX_ACCESS_TOKEN`; optionally Wordstat/Audience tokens

## What to do when something looks wrong

- “Docker Hub shows old tags”: you might be looking at Docker Hub while CI publishes to GHCR. Ensure the mirror step was run.
- “GHCR latest looks old”: verify via manifest digest rather than UI.
- “mcp-registry PR CI is blocked”: fork PR workflows often require maintainer approval; wait or ping maintainers.
