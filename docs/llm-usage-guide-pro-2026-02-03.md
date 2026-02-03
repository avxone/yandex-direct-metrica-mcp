# LLM Usage Guide (PRO MCP)

This document is written for **LLM agents** that connect to this MCP server and need to extract the most value **with PRO tools enabled** (including write tools guarded by `apply=true` + env flags).

Scope: **PRO** toolset (Direct + Metrica + Wordstat + Audience) including **BI Option 2** datasets + incremental sync.

## Safety rules (PRO mindset)

1) **Still “safe by default”.** Only execute writes when the user explicitly asks and you can satisfy the guardrails (`apply=true`, write flags enabled, sandbox-only policy).
2) **Use plan/apply for Direct changes.** Prefer `direct.hf.plan_changes` → user review → `direct.hf.apply_plan`.
3) **Always bind data volume.** Use `date_from/date_to`, `chunk_days`, per-day limits, and pagination.
4) **Prefer account-aware calls.** Use `account_id` where possible; it resolves Direct `Client-Login` and optional default `counter_id`.

## Enabling PRO features (operator checklist)

Typical setup:
- `MCP_PUBLIC_READONLY=false`
- For Direct/Audience writes: `MCP_WRITE_ENABLED=true`
- For HF writes: `HF_WRITE_ENABLED=true`
- For destructive HF (deletes): `HF_DESTRUCTIVE_ENABLED=true` (only if you really mean it)
- Keep sandbox-only writes: `MCP_WRITE_SANDBOX_ONLY=true` (recommended)

## Tool index (PRO)

Rule: `tools/list` is the source of truth. The index below is a practical map of namespaces and recommended entrypoints.

Accounts:
- `accounts.list`, `accounts.reload`, `accounts.upsert`, `accounts.delete` (writes guarded by `MCP_ACCOUNTS_WRITE_ENABLED`)

Dashboard (Option 1):
- `dashboard.generate_option1` (multi-account, optional Wordstat/Audience blocks)

Dashboard (BI Option 2 datasets + sync):
- `dashboard.schema`
- `dashboard.dataset.*` (Variant B: Direct/Metrica/Wordstat/Join + Audience)
- `dashboard.sync.start`, `dashboard.sync.next`

Direct (raw):
- Reporting: `direct.report`, `direct.get_changes`
- Entities: `direct.list_*` / `direct.get_*`
- Writes: `direct.create_*`, `direct.update_*` (guarded by `MCP_WRITE_ENABLED` + sandbox policy)
- Escape hatch (advanced): `direct.raw_call` (guarded; avoid unless needed)

Direct (HF):
- Read helpers: `direct.hf.find_*`, `direct.hf.get_*`, `direct.hf.report_*`
- Write helpers (guarded by `HF_WRITE_ENABLED` + `apply=true`):
  - Plan/apply: `direct.hf.plan_changes`, `direct.hf.apply_plan`
  - Campaign lifecycle / assets / geo / bids / keywords / ads (see `direct.hf.*` in `tools/list`)
  - Destructive: `direct.hf.delete_*` (also requires `HF_DESTRUCTIVE_ENABLED=true`)

Metrica (raw):
- Reports: `metrica.report`, `metrica.list_counters`, `metrica.counter_info`
- Logs API: `metrica.logs_export` (create/evaluate/download/clean/cancel)
- Management writes: `metrica.goals.*` (create/update/delete)
- Escape hatch (advanced): `metrica.raw_call` (avoid unless needed)

Metrica (HF):
- Read helpers: `metrica.hf.*` reports + `metrica.hf.counter_summary`
- Writes (apply-guarded): `metrica.hf.create_goal`, `metrica.hf.update_goal`, `metrica.hf.delete_goal`

Audience (raw):
- Read: `audience.user_info`, `audience.segments.list/get/stats/overlap`, `audience.pixels.*`, `audience.lookalikes.*`
- Writes (guarded by `MCP_WRITE_ENABLED` + sandbox policy): `audience.segments.create/update/delete`, `audience.upload.*`
- Escape hatch (advanced): `audience.raw_call` (avoid unless needed)

Audience (HF):
- Read helpers: `audience.hf.find_segment`, `audience.hf.catalog`, `audience.hf.segment_perf`
- Activation (write, apply-guarded): `audience.hf.activation_plan` (preview), `audience.hf.apply_activation_plan` (exec)

Wordstat (raw + HF):
- Raw: `wordstat.user_info`, `wordstat.get_regions_tree`, `wordstat.top_requests`, `wordstat.dynamics`, `wordstat.regions`
- HF: `wordstat.hf.suggest_keywords` (resumable via `cursor`), `wordstat.hf.suggest_negative_keywords`

Join (HF):
- `join.hf.direct_vs_metrica_by_utm`
- `join.hf.direct_vs_metrica_by_yclid` (heavier; uses Logs API; resumable via `request_id`)

## BI Option 2 (datasets + incremental sync)

### The core API

1) Discover schema:
- `dashboard.schema`

2) Start sync:
- `dashboard.sync.start`
  - Provide: `datasets[]`, `account_ids[]`, `date_from`, `date_to`
  - Optional: `chunk_days`, `limit_per_day`, `goal_ids`, `segment_ids`

3) Consume pages:
- `dashboard.sync.next` with `cursor`
  - Returns `ndjson` (one JSON object per line) with the shape:
    - `{ "dataset": "...", "account_id": "...", "row": { ... } }`

### Recommended Variant B dataset set

Direct (dims + facts):
- `dashboard.dataset.direct_campaigns_dim`
- `dashboard.dataset.direct_adgroups_dim`
- `dashboard.dataset.direct_keywords_dim`
- `dashboard.dataset.direct_campaign_daily`
- `dashboard.dataset.direct_keyword_daily` (heavy; prefer 1-day chunks)
- `dashboard.dataset.direct_ads_daily` (heavy; prefer 1-day chunks)
- `dashboard.dataset.direct_search_phrases_daily` (very heavy; only when needed)
- `dashboard.dataset.direct_bids_snapshot`

Metrica (facts):
- `dashboard.dataset.metrica_daily`
- `dashboard.dataset.metrica_devices_daily`
- `dashboard.dataset.metrica_geo_daily`
- `dashboard.dataset.metrica_goals_daily` (requires `goal_ids`)
- `dashboard.dataset.metrica_utm_campaigns_daily` (bounded by `limit_per_day`)
- `dashboard.dataset.metrica_landing_pages_daily` (bounded by `limit_per_day`)

Audience:
- `dashboard.dataset.audience_segments`
- `dashboard.dataset.audience_overlap` (requires `segment_ids`)
- `dashboard.dataset.audience_segment_perf_daily` (requires `segment_ids` + dates)

Wordstat (manual / ad-hoc):
- `dashboard.dataset.wordstat_top_requests`

Join (manual / ad-hoc):
- `dashboard.dataset.join_direct_vs_metrica_utm_daily`

## Keyword recommendations → apply (Direct plan/apply)

Recommended workflow:

1) Extract candidates:
- `direct.hf.report_search_phrases` (search terms)
- `wordstat.hf.suggest_keywords` (expansion, resumable via `cursor`)
- `wordstat.hf.suggest_negative_keywords` (heuristic negatives)

2) Build an action plan (preview-only):
- `direct.hf.plan_changes`
  - Operations supported:
    - `keywords.add` (adgroup)
    - `negatives.merge` (campaign/adgroup)
    - `bids.set` (keyword ids)

3) User review:
- Show `preview.calls[]` + `warnings[]`
- Confirm target account / scope

4) Apply (writes):
- `direct.hf.apply_plan` with `apply=true`

## Metrica PRO writes (Variant 1+2)

Raw goals management (write):
- `metrica.goals.create`
- `metrica.goals.update`
- `metrica.goals.delete`

HF goals management (write, apply-guarded):
- `metrica.hf.create_goal`
- `metrica.hf.update_goal`
- `metrica.hf.delete_goal`

Logs API operations remain separate and are still useful for click-level joins.

## Audience PRO workflows (segment lifecycle + activation)

Typical flow:
1) Inspect segments:
   - `audience.segments.list` / `audience.hf.catalog`
2) Create or update:
   - `audience.segments.create` / `audience.segments.update` (writes)
3) Upload data (potential PII):
   - `audience.upload.start` / `audience.upload.status` / `audience.upload.errors`
4) Apply in Direct (retargeting activation):
   - `audience.hf.activation_plan` (preview-only)
   - `audience.hf.apply_activation_plan` with `apply=true`

Important:
- Treat Audience upload payloads as sensitive: do not log them, do not persist them.
