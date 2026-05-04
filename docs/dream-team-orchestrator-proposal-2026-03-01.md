# Dream Team Orchestrator proposal — separate repo (Self-hosted → SaaS-ready)

Date: 2026-03-01

This document proposes a **separate repository**: an orchestrator CLI that runs the “Dream Team” workflows using MCP backends (starting with `yandex.ad`), stores knowledge artifacts, and standardizes plan/apply/QA loops.

## 1) What the orchestrator is (and is not)

**It is:**
- A CLI “control plane” for marketing operations.
- A workflow runner that calls MCP tools, writes artifacts, and enforces safety gates.
- A reproducible pipeline executor (snapshot → research → plan → apply → verify → QA → evaluate).

**It is not:**
- A replacement for MCP backends.
- A giant set of ad-platform API wrappers.

## 2) Core outcomes (why it will feel better than “just MCP servers”)

- **Reproducibility:** every run produces artifacts (inputs, outputs, decisions) with ids.
- **Safety:** write actions are always two-phase, with explicit confirmation and post-checks.
- **Consistency:** the same runbooks and formats across projects/accounts.
- **Memory:** knowledge store accumulates learnings/experiments/hypotheses in a consistent schema.

## 3) Proposed repo name and boundaries

Suggested repo: `marketing-dream-team` (or `dream-team-orchestrator`)

Hard boundary:
- Backend repo = integrations + MCP tools + optional operator CLI.
- Orchestrator repo = workflows/skills/runbooks + knowledge store + scheduling hooks.

## 4) MVP command surface (v0)

### 4.1 `init`

- `dream-team init --workspace .`

Creates folders and baseline config:
- `knowledge/` (NDJSON + docs)
- `runs/` (execution logs/artifacts)
- `configs/` (profiles)

### 4.2 Profiles (projects/accounts)

- `dream-team profile add --name <project> --backend yandex-ad --mcp <config-ref>`
- `dream-team profile list`

Profiles define:
- which MCP backend(s) to use
- which accounts/counters are in scope
- safety policy defaults (limits, allowlists)

### 4.3 Read-only pipeline (must come first)

- `dream-team snapshot --profile <project> --range last_7d`
- `dream-team weekly-review --profile <project>`

Artifacts:
- snapshot NDJSON files + derived summary markdown
- minimal “exec summary” and “alerts” for the Analyst role

### 4.4 Plan → Apply (PRO-only workflows)

This is where we enforce the same safety posture we already use in the backend repo:

- `dream-team plan --profile <project> --task <slug> --inputs <json>`
  - Produces a plan artifact (no writes)
  - Outputs `plan_id`
- `dream-team apply --plan-id <id> --confirm`
  - Requires explicit confirmation flag (and optionally a second factor like a short code)
  - Calls backend PRO tools (two-phase writes)
  - Produces an “apply record” artifact (diff + result + verification)
- `dream-team verify --plan-id <id>`
  - Runs post-apply checks and stores results

### 4.5 QA commands (operator-grade)

- `dream-team qa preflight --profile <project> --plan-id <id>`
- `dream-team qa post24h --profile <project> [--since-run <run_id>]`

Preflight focuses on preventing avoidable mistakes (UTM policy, landing/ad consistency, conversion tracking sanity).
Post24h focuses on early anomaly detection and rollback triggers.

### 4.6 Knowledge store commands

- `dream-team knowledge add --type hypothesis|experiment|learning --text ... --meta <json>`
- `dream-team knowledge rebuild-duckdb`
- `dream-team knowledge export --format ndjson|csv`

## 5) Artifact contracts (minimal, v0)

Two artifact families should be stable from day one:

### 5.1 Run record (every CLI invocation)

- `runs/YYYY-MM-DD/<run_id>/run.json`
- contains: `{run_id, started_at, finished_at, command, profile, status, inputs, outputs, errors[]}`

### 5.2 Plan record (for PRO workflows)

- `runs/.../<plan_id>/plan.json`
- contains: `{plan_id, created_at, profile, intent, proposed_changes[], limits, requires_confirm: true}`

## 6) Backend integration (how orchestrator calls MCP)

We should keep this as a pluggable backend interface because we’ll later add Google Ads and others.

Recommended integration options (choose one for MVP):

1) **Use a Python MCP client library** (if supported by `mcp` in our target versions).
2) **Spawn MCP server subprocess** (stdio) and speak MCP protocol programmatically.
3) **Remote mode**: call Streamable HTTP directly (later SaaS phase).

Start with the simplest that is reliable in CI and on macOS.

## 7) SaaS evolution hooks (design now, implement later)

Add interfaces early:
- `TokenStore` (local file → later Postgres/KMS)
- `AuditStore` (local NDJSON → later Postgres)
- `TenantContext` (single-tenant now → multi-tenant later)

## 8) Open questions

- Where do “skills” live: in orchestrator repo (recommended) or in a third repo?
- Do we want to run LLM steps inside orchestrator (agent mode), or keep orchestrator purely deterministic and let the LLM client drive decisions?
- What is the minimum viable QA checklist to enforce for all writes?
