# LLM Usage Guide (Public Read-Only MCP)

This document is written for **LLM agents** (Claude, ChatGPT, etc.) that connect to this MCP server and need to extract the most value **without write access**.

Scope: **public read-only** toolset (v1.0.0 contract target).

## What “read-only” means here (Public v1.0.0)

Definition: **read-only = no changes to managed entities** in Direct/Metrica/Audience (no create/update/delete of campaigns, segments, goals, etc.).

Allowed side effects (still considered “read-only” for the public contract):
- **Wordstat** requests that create/compute report-like data on the provider side.
- **Metrica Logs API** export jobs (`metrica.logs_export`) used for analysis/joins (no counter configuration changes).

Not allowed in public:
- Any Direct entity writes (`direct.create_*`, `direct.update_*`) and any “escape hatch” writes (`*.raw_call`).
- Any Audience writes (segment create/update/delete, uploads, activation in Direct).
- Any Metrica management writes (e.g., goals CRUD).

## Core rules (public contract mindset)

1) **Assume read-only by default.** Never attempt tool names that are not returned by `tools/list`.
2) **Always pick an account explicitly** when possible:
  - Prefer `account_id` (maps to Direct `Client-Login` + optional default Metrica counters).
   - Use `counter_id` only when the account has multiple counters or you need an override.
3) **Always bound data volume.** Use `limit`, `max_rows`, and dashboard/wordstat caps to keep runs fast and stable.
4) **Prefer HF tools first.** Use `direct.hf.*`, `metrica.hf.*`, `wordstat.hf.*`, and `join.hf.*` unless you truly need raw endpoints.
5) **Treat outputs as “raw-ish JSON”.** Do not assume optional keys exist. Be resilient to missing fields and partial coverage.

## Minimal “good agent” workflow

1) Discover accounts:
   - Call `accounts.list`
   - If the user changed `accounts.json`, call `accounts.reload`

2) Get a quick situation snapshot:
   - Direct: `direct.hf.get_campaign_summary` or `direct.hf.report_performance`
   - Metrica: `metrica.hf.report_time_series` + `metrica.hf.report_landing_pages`

3) Join Direct ↔ Metrica (if needed):
   - Use `join.hf.direct_vs_metrica_by_utm` for stable campaign-level comparisons
   - Use `join.hf.direct_vs_metrica_by_yclid` for click-to-visit linking (best effort; heavier)

4) Generate a dashboard for humans:
   - Use `dashboard.generate_option1` with `output_dir` and `return_data=false`
   - Multi-account: set `all_accounts=true` (UI will show an account switcher)
   - Optional: set `include_audience=true` to add Audience blocks (catalog + overlaps)

5) Add keyword intelligence (Wordstat):
   - Raw: `wordstat.top_requests` / `wordstat.dynamics` / `wordstat.regions`
   - HF: `wordstat.hf.suggest_keywords` (resumable via cursor) + `wordstat.hf.suggest_negative_keywords`

6) Add audiences intelligence (Audience):
   - Raw: `audience.segments.list` / `audience.segments.get` / `audience.segments.overlap`
   - HF: `audience.hf.catalog` + `audience.hf.find_segment` + `audience.hf.segment_perf` (best effort)

## Accounts and multi-account behavior

### When to use `account_id`
- When the user wants “project-aware” behavior:
  - Correct Direct `Client-Login`
  - Correct allow-list/defaults for Metrica counters
  - Dashboard multi-account mode

### How to handle multi-account dashboards
- Prefer one call:
  - `dashboard.generate_option1` with `all_accounts=true`
- Or pick accounts explicitly:
  - `dashboard.generate_option1` with `account_ids=["a","b","c"]`

### Recommended agent prompt template (for user input)
Ask the user to provide:
- `account_id` (or “all accounts”)
- `date_from`, `date_to` (YYYY-MM-DD; “to yesterday” is often best)
- What they want: **dashboard**, **analysis**, **keywords**, **join**, or **raw export**
- Any constraints: max time, max rows, language/regions/devices for Wordstat

## Dashboard (`dashboard.generate_option1`) best practices

Use the dashboard when you need:
- A human-readable overview (HTML)
- A JSON dataset that can be saved and analyzed later
- A **multi-account** summary with a UI account switcher

Recommended defaults:
- `output_dir` set (so artifacts are saved)
- `return_data=false` (prevents huge payloads in chat)
- `include_raw_reports=true` only when you actually need raw payloads for debugging
- `include_wordstat=true` only when Wordstat credentials exist and time budget allows
- `include_audience=true` only when Audience credentials exist and you want audience blocks

Example (multi-account, 30d, write files only):
```json
{
  "all_accounts": true,
  "date_from": "2026-01-04",
  "date_to": "2026-02-02",
  "output_dir": "/data/dashboards",
  "return_data": false,
  "include_wordstat": true,
  "include_audience": true,
  "wordstat_max_campaigns": 5,
  "wordstat_num_phrases": 50
}
```

Notes:
- The server may auto-shift `date_to` to **yesterday** if you pass today/future.
- In multi-account mode, the HTML includes an account selector and updates the view client-side.
- Wordstat dashboard block is **best effort** and bounded by `wordstat_*` caps.

## Direct tools: when to use raw vs HF

### Prefer HF tools for analysis
Use these for “what’s going on?” questions:
- `direct.hf.get_campaign_summary`
- `direct.hf.report_performance`
- `direct.hf.report_search_phrases` (search terms analysis)
- `direct.hf.report_keywords` / `direct.hf.report_ads` / `direct.hf.report_adgroups`
- `direct.hf.get_bids_summary` (bidding snapshot)

### Use raw tools when you need exact API payloads
Use these for debugging or custom mapping:
- `direct.report` (custom reports)
- `direct.list_campaigns`, `direct.list_adgroups`, `direct.list_ads`, `direct.list_keywords`, etc.

Efficiency hints:
- Start with HF summary → only then drill down into raw lists.
- Use `direct.get_changes` for incremental/“what changed?” workflows (lighter than full refresh).

## Metrica tools: quick reports vs heavy logs

### Prefer HF reports for dashboards and analysis
- `metrica.hf.report_time_series`
- `metrica.hf.report_landing_pages`
- `metrica.hf.report_utm_campaigns`
- `metrica.hf.report_geo`
- `metrica.hf.report_devices`
- `metrica.hf.counter_summary`

### Logs API is powerful but heavier
- `metrica.logs_export` is used by `join.hf.direct_vs_metrica_by_yclid`
- Prefer joins/dashboard first; only fall back to logs when you must link clicks to visits

## Audience tools (public read-only)

### Raw layer (Audience API-shaped)
- `audience.user_info`
- Segments (read): `audience.segments.list`, `audience.segments.get`, `audience.segments.stats`, `audience.segments.overlap`
- Catalogs (read): `audience.pixels.list`, `audience.pixels.get`, `audience.lookalikes.list`, `audience.lookalikes.get`

### HF layer (agent-friendly)
- `audience.hf.find_segment`
- `audience.hf.catalog`
- `audience.hf.segment_perf` (best effort proxy; bounded; expect partial coverage)

## Join tools: how to choose

### `join.hf.direct_vs_metrica_by_utm` (recommended)
Use when:
- You want daily series comparison at campaign level
- You have stable `UTMCampaign` tagging or can infer it reliably

Typical question it answers:
- “Direct clicks/cost/leads per day vs Metrica visits/leads per day — do they correlate?”

### `join.hf.direct_vs_metrica_by_yclid` (best effort, heavier)
Use when:
- You need to link Direct click identifiers to Metrica visits (Logs API)
- UTMs are missing/unreliable and you need click-level evidence

Operational tips:
- Keep `max_rows` bounded (default is already capped)
- Use `request_id` to resume a run if it times out
- Expect partial joins: logs fields may be missing or data may not cover all clicks

## Wordstat tools (public read-only keyword intelligence)

### Raw layer (API-shaped data)
- `wordstat.user_info` — validates access & shows account/context
- `wordstat.get_regions_tree` — region ids catalog
- `wordstat.top_requests` — related queries for one phrase (or a list)
- `wordstat.dynamics` — time dynamics for a phrase
- `wordstat.regions` — region distribution for a phrase

Use raw tools when you need:
- Maximum flexibility (you will interpret the payload yourself)
- Exact response fields for export/audit

### HF layer (agent-friendly)

#### `wordstat.hf.suggest_keywords` (resumable)
Use when:
- You have **seed phrases** and want a consolidated shortlist of candidates

Important:
- This tool may return `status="pending"` with `preview.cursor`.
- If pending, call the tool again with `cursor` until it returns `status="ok"`.

Example loop:
1) Call with `seed_phrases`
2) If pending, call again with `cursor`
3) Stop when `status="ok"`

#### `wordstat.hf.suggest_negative_keywords` (lexicon-based)
Use when:
- You already have phrases (from search terms, Wordstat, landing pages) and want **negative token candidates**
- You need a quick heuristic list without calling external APIs

## Putting it together: “keyword recommendations for running campaigns”

Good pattern for a public read-only agent:
1) Identify top-spend or top-click campaigns:
   - `direct.hf.report_performance` (bounded)
2) Extract seed terms:
   - `direct.hf.find_keywords` (per campaign/adgroup) or `direct.hf.report_search_phrases`
3) Get expansion candidates:
   - `wordstat.top_requests` (raw) or `wordstat.hf.suggest_keywords` (HF)
4) Suggest negatives:
   - `wordstat.hf.suggest_negative_keywords` on the phrase list (from step 2–3)
5) Present an “apply plan” (but do not apply):
   - Group by campaign/adgroup
   - Provide rationale + expected impact
   - Flag that actual edits require Pro/write tools

## Error handling: what to do when tools fail

When a tool returns an MCP error:
- Surface the **provider** (`direct`, `metrica`, `wordstat`) and any `request_id`/ids.
- Provide an actionable hint:
  - missing access → check account permissions
  - invalid token → refresh/re-auth and re-run
  - rate limit → reduce caps / retry later
  - missing `account_id` mapping → check `/data/accounts.json` and call `accounts.reload`

Recommended retry logic in an LLM:
- Retry only on clearly transient failures (timeouts/5xx/rate limit).
- Do not blindly retry 4xx (usually configuration/permission).

## Tool index (public read-only)

Accounts:
- `accounts.list`, `accounts.reload`

Dashboard:
- `dashboard.generate_option1`

BI Option 2 (datasets/sync):
- Not part of public surface (PRO-only): `dashboard.schema`, `dashboard.dataset.*`, `dashboard.sync.*`

Direct (raw):
- `direct.report`, `direct.get_changes`, `direct.list_*`

Direct (HF):
- `direct.hf.find_*`, `direct.hf.report_*`, `direct.hf.get_*`

Metrica (raw):
- `metrica.report`, `metrica.logs_export`, `metrica.list_counters`, `metrica.counter_info`

Metrica (HF):
- `metrica.hf.*`

Audience (raw + HF):
- `audience.*` (read-only subset), `audience.hf.*` (read-only subset)

Joins (HF):
- `join.hf.direct_vs_metrica_by_utm`, `join.hf.direct_vs_metrica_by_yclid`

Wordstat (raw + HF):
- `wordstat.*`, `wordstat.hf.*`
