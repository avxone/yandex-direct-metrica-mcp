# AGENTS

Working principles for the Yandex Direct + Metrica MCP server (Python stack).

## Scope
- Language: Python.
- Libraries: `tapi-yandex-direct`, `tapi-yandex-metrika`.
- MVP: Direct read/write, Metrica read-only exports.
- Runtime: Docker on macOS M1, minimal footprint.

## Objectives
- Provide reliable MCP tools for Direct and Metrica.
- Prefer raw data responses; avoid heavy normalization in MVP.
- Keep dependencies light and memory usage low.

## MCP tools policy
- Use the approved tool list in `yandex.ad/docs/tools-proposal-YYYY-MM-DD.md`.
- Add new tools only after explicit approval.
- Provide a generic `raw_call` tool only if absolutely necessary.

## Data rules
- Do not store user data unless explicitly required.
- Do not embed secrets in files; load from environment.
- For write operations, prefer Sandbox or test accounts where possible.

## Auth and secrets
- OAuth tokens must be provided via environment variables or an external secret store.
- Never log raw tokens; mask credentials in logs.

## Error handling
- Normalize API errors into clear MCP errors.
- Retry only on transient errors (timeouts, 5xx, rate limits) with backoff.
- Make errors actionable: include endpoint, request id, and hint.

## Logging
- Log requests at info level without sensitive data.
- Log errors with minimal payload and IDs for correlation.

## Testing
- Keep tests lightweight.
- Prefer mocked API responses for unit tests.
- Avoid live API calls in CI.
- Use a Python test framework (pytest recommended) once tests are added.
- Keep tests green before committing; TDD is encouraged but optional.

## Documentation
- Keep research and planning docs in `yandex.ad/docs/`.
- Update docs when the tool list or architecture changes.
- Store session notes in `yandex.ad/docs/sessions/YYYY-MM-DD_<n>_<slug>.md`.
- Each session file must include explicit sections: "Completed" and "To Do".
- Keep `yandex.ad/README.md` as the entry point for this MCP project.
- Update `yandex.ad/CHANGELOG.md` at the end of each session; latest changes go first.

## Workflow
- Changes should be incremental and reversible.
- Validate configuration and tool list before expanding scope.
- When addressing problems or decisions, propose at least three options.
- Soft guideline: split files once they exceed ~300 LOC to keep modules readable.
- Optional: add `ast-grep` rules for recurring checks if/when the tool is introduced.
- Add short, focused comments only for tricky logic or non-obvious integrations.

## Release & Distribution (Public v1.x + Pro)

### Contract summary (v1.0.0 baseline)
- **Public contract**: read-only tools + `dashboard.generate_option1` + read-only HF/join tools.
- **Pro tools**: anything write-related, escape hatches, BI Option 2 datasets/sync, etc. are **out of public contract**.

### Branching / docs languages
- `docs/` is **English** (official).
- `docs/ru/` is **Russian** (official).
- The docs site must link both ways:
  - EN landing `docs/index.html` → `/ru/`
  - RU landing `docs/ru/index.html` → `../`

### Pre-tag checklist (release gate)
1) Tests: `pytest -q`
2) Versioning:
   - bump `pyproject.toml` version
   - update `CHANGELOG.md` (new section, latest first)
3) Public safety:
   - public build must be **safe-by-default** (read-only)
   - verify PRO publish is gated (no automatic public publish)
4) Docs:
   - `README.md` reflects the current scope (Direct/Metrica/Wordstat/Audience)
   - `docs/` and `docs/ru/` updated (no machine-specific paths like `/Users/...` or `~/...`)

### Tag + release checklist
- Tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
- GitHub Release: create/update notes (keep public vs pro artifacts clear).

### Docker image channels (public only by default)
**Primary: GHCR**
- Public image: `ghcr.io/<owner>/yandex-direct-metrica-mcp:vX.Y.Z` and `:latest`
- Public workflow should publish `:latest` **only** on tags.

**Optional mirror: Docker Hub**
- Public image: `docker.io/<owner>/yandex-direct-metrica-mcp:vX.Y.Z` and `:latest`
- Keep tags consistent with GHCR (`vX.Y.Z` + `latest`).

**Pro image**
- Never publish PRO automatically.
- Keep PRO package **private** and publish only via gated workflow (e.g. `workflow_dispatch` or `pro-v*` tags).

### Dockerfile defaults (important for external builders like docker/mcp-registry)
- The root `Dockerfile` must build **public read-only** by default:
  - `ARG MCP_EDITION=public`
  - `ARG MCP_PUBLIC_READONLY=true`
- Building PRO locally requires explicit build args:
  - `docker build --build-arg MCP_EDITION=pro --build-arg MCP_PUBLIC_READONLY=false -t yandex-direct-metrica-mcp:pro .`

### Docker Hub publishing (multi-arch)
When mirroring a release to Docker Hub, build from the **tag** to match the released source:
```bash
git checkout vX.Y.Z
docker buildx build --platform linux/amd64,linux/arm64 --push \
  -t docker.io/<owner>/yandex-direct-metrica-mcp:vX.Y.Z \
  -t docker.io/<owner>/yandex-direct-metrica-mcp:latest \
  --build-arg MCP_PUBLIC_READONLY=true \
  --build-arg MCP_EDITION=public \
  .
```

### GHCR verification (tags/digests)
When debugging “latest looks old”, verify digests via registry manifest calls (avoid relying on UI caching).

### PR hygiene (GitHub CLI + shells)
- When using `gh pr create` / `gh pr comment`, avoid backticks in shell-quoted strings.
  - Prefer `--body-file` (write markdown to a file, then pass the file).

## Docker MCP Registry (docker/mcp-registry) — Option A

Goal: have Docker build and host a trusted image in `mcp/<server-name>`.

Key constraints:
- The registry pins `source.commit` to a specific SHA1 (required).
- Docker will build using the repo’s Dockerfile defaults: must be public/read-only by default.
- `server.yaml` secrets must be `prefix.name` format.
- CI may require manual approval for PRs from forks (expected).

Submission checklist:
1) Ensure our repo default Dockerfile is public/read-only (see above).
2) Fork `docker/mcp-registry`.
3) Add `servers/<name>/server.yaml` with:
   - `image: mcp/<name>` (Option A)
   - `source.project` pointing to this repo
   - `source.commit` pinned to the audited SHA
   - `run.env.MCP_PUBLIC_READONLY: "true"`
   - a configurable `/data` volume for state (accounts.json, dashboard artifacts)
4) Open PR and wait for Docker team review + workflow approvals.
