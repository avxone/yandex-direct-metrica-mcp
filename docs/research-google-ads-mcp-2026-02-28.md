# Google Ads MCP — Market Landscape + Project Brief (Self-hosted → SaaS-ready)

Date: 2026-02-28

This document captures the current Google Ads MCP landscape and a concrete project brief for building a self-hosted Google Ads MCP that can later evolve into a SaaS (remote MCP + OAuth + multi-tenant).

It is written as a “start-from-here” artifact so future work does not restart from a blank slate, and so we can reuse the proven patterns from this repository (public read-only defaults, PRO gating, two-phase writes, error normalization, lightweight tests, and documentation discipline).

## 0. Research plan (completed)

This is the exact research plan used to build this brief:

1. Collect Google Ads MCP landscape
2. Assess write/campaign management coverage
3. Survey “skills” and integrations (plugins/templates/runbooks)
4. Compare to our architecture and safety model
5. Summarize recommendations and a roadmap

## 1. Goals

- Build a **self-hosted** Google Ads MCP server that is **safe-by-default** (read-only).
- Keep the OSS core small, auditable, and reliable: **query + metadata + exports**.
- Add write capability only via a **private PRO plugin** with **plan → confirm → apply → verify** semantics.
- Support “Dream Team / bundles / skills / runbooks” workflows (strategy → execution → QA) instead of exposing raw API surface only.
- Be **SaaS-ready**: design auth/storage boundaries so we can later add remote transport + OAuth + multi-tenant without rewriting core logic.

## 2. Non-goals (for MVP)

- Re-implement the entire Google Ads API as 100+ tools in OSS.
- Provide “agent can spend money immediately” semantics in OSS.
- Store user marketing data by default.

## 3. Current landscape (what already exists)

### 3.1 Read-only / minimal “GAQL wrapper”

These servers mostly provide “run GAQL + list accessible customers”:

- `googleads/google-ads-mcp` (Python, experimental): two tools (`search`, `list_accessible_customers`), includes a note about an extra header used for usage data collection.
- `google-marketing-solutions/google_ads_mcp` (Python): read-only orientation, uses `google-ads.yaml`.
- `cohnen/mcp-google-ads` (Python/FastMCP): run GAQL via REST `googleAds:search`, plus helpful formatting and some “canned analysis” helpers.

### 3.2 Open-source “large API surface” (write-capable)

These projects aim to expose much more of the API, including mutations:

- `promobase/google-ads-mcp` (Python): claims broad v20 service coverage with tests/type-safety.
- `grantweston/google-ads-mcp-complete` (Python): “40+ tools” covering campaign lifecycle (create/pause/budget/keywords/etc.).

### 3.3 Remote/SaaS MCP servers (multi-platform, often write-capable)

These are closer to a product: remote HTTP MCP endpoint + OAuth + multi-account linking + plugins/skills distribution.

- `amekala/ads-mcp` (Adspirer): remote MCP with 100+ tools across Google/Meta/TikTok/LinkedIn; also distributes plugins and skills.
- `jshorwitz/synter-mcp-server` (Synter): write-capable “credit card” messaging; cross-platform.
- `stellagent/presso-setup` (Presso): cross-platform analytics, explicitly read-only.

## 4. Key gaps and opportunities (how we can be “better”)

Most Google Ads MCP servers compete on tool count. Our advantage (based on this repo’s Yandex Direct/Metrica experience) is to compete on **operational safety + workflow quality**:

1) **Safe-by-default + auditable**
- One shared gate: `READONLY=true` in OSS must block any mutation paths even if code is present.
- All calls should emit structured, non-sensitive audit logs (request ids, tool name, customer id masked, timings).

2) **Plan → Apply as a first-class write protocol (PRO only)**
- Mutation tools should not accept arbitrary payloads directly in the first iteration.
- Instead: generate a plan (diff), require explicit confirmation, apply, then verify (post-check queries).

3) **Workflow-level “skills” instead of raw API surface**
- Skills like `campaign-structure-planner`, `utm-audit-fix`, `negative-sweep`, `post-launch-qa-24h` reduce LLM mistakes.
- The skill layer is where the Dream Team roles live (Strategist/Analyst/Ads/QA/Competitors).

4) **Docs/metadata as resources**
- A large portion of “LLM Google Ads errors” are wrong GAQL field usage or invalid enum/resource names.
- Provide a metadata tool/resource (fields, categories, constraints) so the agent can self-correct.

5) **SaaS-ready boundaries**
- Implement interfaces for token storage, audit storage, and per-tenant config so remote mode is an additive change.

## 5. Proposed architecture (self-hosted now, SaaS later)

### 5.1 Components

**A) OSS core (read-only)**
- GAQL query execution + pagination.
- Field/resource metadata.
- Minimal account discovery and hierarchy helpers.
- Exports (JSON/NDJSON/CSV) with strict row limits.

**B) PRO plugin (private, optional install)**
- Write workflows with `plan → confirm → apply → verify`.
- Narrow initial scope: pause/resume, budget changes, negative keywords, ad status, labels.

**C) Skills/Runbooks repository**
- A separate directory/repo with role-specific skills and runbooks.
- Skills write artifacts into a knowledge store (NDJSON as source of truth + rebuildable analytical cache).

### 5.2 Self-hosted → SaaS evolution path

**Self-hosted phase**
- Transport: stdio (works with Claude/Cursor/Codex).
- Auth: local `google-ads.yaml` (refresh token), optionally ADC for advanced users.
- Storage: local volume `/data` for non-sensitive state (plans, audit, cached metadata).

**SaaS phase**
- Transport: streamable HTTP (remote MCP).
- Auth: OAuth (PKCE) + tenant scoping; per-tenant token storage.
- Storage: Postgres (audit logs, plan artifacts, minimal metadata cache).

## 6. Tool surface proposal (v0)

This section is for the **future Google Ads project**. It does not modify this repository’s approved tool lists.

**OSS core tools (read-only)**
- `google_ads.list_accessible_customers`
- `google_ads.gaql.search` (with `customer_id`, `query`, `page_size`, `max_rows`, `timeout_ms`)
- `google_ads.gaql.fields` (field metadata / constraints)
- `google_ads.account.hierarchy` (optional, if manager flows are common)
- `google_ads.reports.export` (optional; server-side export with limits)

**PRO plugin tools (write, two-phase)**
- `google_ads.mutate.plan` (inputs are high-level intent, outputs are a plan + diff)
- `google_ads.mutate.confirm` (explicit confirmation token/TTL)
- `google_ads.mutate.apply`
- `google_ads.mutate.verify`

## 7. Safety policy (minimum)

- OSS core must be read-only by default.
- PRO must be explicitly enabled/configured.
- Never log:
  - refresh/access tokens
  - developer token
  - full customer ids (mask them)
- Retry only transient errors (timeouts, 5xx, rate limits) with backoff and a hard cap.
- Enforce limits (`max_rows`, `max_mutations`, `max_customer_scope`) to prevent runaway operations.

## 8. Repo split recommendation

If we proceed, it is cleaner to create a separate project repo:

- `google.ads` (or `google-ads-mcp-core`) — OSS read-only core
- `google.ads.pro` — private PRO plugin (write workflows)
- `marketing-skills` — skills/runbooks/knowledge model (Dream Team bundles)

We can still reuse code patterns from this repo by extracting them as:

- small internal “shared” package (error normalization, env validation, logging filters, two-phase write scaffolding), or
- copy-with-attribution inside the new repo to keep dependencies light.

## 9. Bootstrap checklist (so we don’t start from zero)

- Copy “public vs pro” approach from this repo:
  - build args/env flags that default to public read-only
  - explicit gating for PRO plugin loading
  - tool allowlist enforcement (only tools returned by `tools/list` are callable)
- Reuse the “two-phase writes” concept:
  - a plan artifact with TTL
  - explicit confirm
  - apply with strict limits
  - post-apply verification queries
- Keep docs discipline:
  - `docs/` for research and contracts
  - `docs/sessions/` for session notes (“Completed” + “To Do”)
  - `CHANGELOG.md` updated each session

## 9.1 Suggested repo structure (v0)

For a new self-hosted project, this structure keeps the core small and makes the SaaS path incremental:

```
google-ads-mcp-core/
  src/google_ads_mcp/
    server.py              # MCP server entry
    config.py              # env + config parsing (read-only default)
    logging.py             # structured logging + redaction filters
    errors.py              # normalized errors + retriable classification
    auth/
      yaml_credentials.py  # google-ads.yaml loader
      adc.py               # optional: ADC support
    gaql/
      client.py            # google-ads-python client wrapper
      search.py            # GAQL execution, paging, limits
      fields.py            # GoogleAdsField metadata helpers
    policy/
      readonly.py          # shared gate for mutations
      limits.py            # max rows/timeouts/customer scope
    storage/
      plans_fs.py          # local /data plan artifacts (self-hosted)
      audit_fs.py          # local /data audit trail (self-hosted)
  docs/
  tests/
  Dockerfile               # default public/read-only
  pyproject.toml
```

PRO plugin can be a separate package that imports the same error/policy interfaces.

## 9.2 “Port from yandex.ad” checklist

Reusable patterns from this repo that should be carried into the Google Ads project:

- Public/read-only defaults controlled by build args/env flags.
- Tool allowlist enforcement: server rejects calls to tools not present in current `tools/list`.
- Two-phase writes scaffold (plan artifact + TTL confirm + apply + verify).
- Error normalization contract and “retriable only” backoff policy.
- Logging redaction (never print secrets) + correlation ids in errors.
- Docs hygiene: session notes + changelog discipline.

## 10. Open questions

- Authentication priority: `google-ads.yaml` only for MVP, or support ADC from day one?
- Should OSS core expose only GAQL, or also provide a few “human-friendly” report presets (still read-only)?
- What is the minimum “write set” for PRO that unlocks real value without adding high risk?
