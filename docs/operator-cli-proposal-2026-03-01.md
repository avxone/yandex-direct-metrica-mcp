# Operator CLI (Backend) proposal — `yandex.ad` MCP

Date: 2026-03-01

This document proposes improvements to the **backend repository** (this repo): an “operator-grade” CLI that complements MCP.

Key idea: **MCP is for LLM tool-use; CLI is for humans + automation** (cron/CI/debug), with stable exit codes, JSON output options, and predictable artifacts.

## 1) Why add/expand CLI when we already have MCP?

MCP clients (Claude/Cursor/Codex/etc.) are great for interactive workflows, but they are not ideal for:

- Cron / scheduled snapshots and report generation
- CI checks (auth/config validation, smoke tests)
- Debugging and reproducing issues without an LLM session
- Generating artifacts (dashboards, exports) deterministically
- “Operator workflows” with strict exit codes and machine-readable output

This repo already has:

- A Click-based CLI entrypoint (`[project.scripts]`) and an interactive `auth` command.
- A set of `scripts/*.py` utilities (argparse) for smoke tests, env validation, dashboard generation, and write helpers.

The proposal is to **unify** these into one coherent CLI surface.

## 2) Design goals

- Keep dependencies minimal (reuse `click` already in `pyproject.toml`).
- Keep docs and UX consistent with “public read-only by default”.
- Never log secrets; keep logs actionable and safe.
- Stable exit codes and optional JSON output (`--json`) for automation.
- Don’t expand MCP tool surface as part of CLI work.

## 3) Proposed command surface (v0)

The top-level entry remains `mcp-yandex-ad` (and keep `yandex-direct-metrica-mcp` as an alias for compatibility).

### 3.1 `serve`

Explicit start command (even if default behavior already starts the server):

- `mcp-yandex-ad serve --transport stdio|sse --port 8000 --env-file .env -v|-vv`

Notes:
- `serve` should be the canonical documented entry.
- Keep current “invoke without command starts server” behavior for backward compatibility.

### 3.2 `auth`

Keep existing flow (hybrid/manual/local + `--output-env`), but document it as a first-class operator workflow.

Optionally add:
- `--print-mask` (default on): mask tokens in console output unless user requests full values.

### 3.3 `doctor`

Fast diagnostic command for support/ops:

- `mcp-yandex-ad doctor [--json] [--env-file ...]`

Checks (read-only):
- Required env vars and basic sanity (without printing secrets)
- Reachability/auth checks for Direct/Metrica/Wordstat/Audience (using existing check scripts / lightweight calls)
- Build mode gating (public/pro, tool allowlist enabled, two-phase writes enabled)
- Reports a summary: “OK / WARN / FAIL” + hints

Output contract:
- Human: concise, actionable lines.
- JSON: `{status, checks:[{name,status,details,hint}], meta:{version,mode}}`

### 3.4 `validate-env`

Wrap the existing `scripts/validate_env.py` as:

- `mcp-yandex-ad validate-env [--json] [--env-file ...]`

Exit codes:
- `0` OK
- `2` invalid/missing configuration

### 3.5 `smoke-test`

Wrap `scripts/smoke_test.py`:

- `mcp-yandex-ad smoke-test [--json] [--env-file ...] [--sandbox]`

Exit codes:
- `0` OK
- `1` test failure
- `2` config failure

### 3.6 `dashboard option1`

Wrap `scripts/generate_dashboard_option1.py`:

- `mcp-yandex-ad dashboard option1 --account <id>|--all-accounts --date-from ... --date-to ... --output-dir ...`

Principles:
- No machine-specific paths in docs; default output to `/data/...` in Docker scenarios.
- Enforce safe output directory behavior (path traversal protection if any file writing occurs).

### 3.7 `scripts` (optional compatibility namespace)

If we want a gentle migration path:

- `mcp-yandex-ad scripts <name> ...` as a passthrough to existing `scripts/*.py`

But preferred approach is to properly lift each script into a CLI subcommand over time.

## 4) Implementation plan (backend repo)

### Step 1 — Restructure CLI code (low risk)

Today the Click CLI lives in `src/mcp_yandex_ad/__init__.py`. Recommended:

- Move CLI code to `src/mcp_yandex_ad/cli.py`
- Keep `__init__.py` exporting `main` for backward compatibility.

This reduces import side effects and keeps package init lightweight.

### Step 2 — Introduce `doctor` (highest value)

Implement `doctor` by reusing existing scripts or the underlying functions they call.
Keep checks fast and predictable (avoid long live calls by default; add `--deep` to opt in).

### Step 3 — Wrap scripts with stable UX

Implement `validate-env`, `smoke-test`, `dashboard option1` as wrappers:
- prefer calling existing Python functions, not subprocesses
- add `--json` output mode
- keep logs safe and minimal

### Step 4 — Tests

- Add Click CLI tests using `click.testing.CliRunner`
- Ensure exit codes and JSON schemas are stable

## 5) How this supports the “two-repo” approach

This backend CLI becomes the “operator toolbox” for:
- local debugging
- CI checks
- scheduled artifact generation

The orchestrator (separate repo) can rely on:
- MCP tools for data and actions
- CLI for ops validation (optional)

## 6) Open questions

- Should `doctor` default to fully offline checks, or include one minimal live call per integration?
- Do we want to standardize an `--output-format json|text` option across all commands?
- Should CLI commands write artifacts only under `/data` by default (to match Docker volume patterns)?

