# BI Option 2 (PRO): datasets + incremental sync — proposal/status — 2026-02-03

Goal: provide a **BI-ready** contour for **Direct + Metrica + Wordstat + Audience** as:
- stable **datasets** (tables/rows),
- **incremental sync** (cursor/watermark, NDJSON-friendly),
- minimal normalization (raw-first, but with useful keys/columns).

Status:
- Variant **B (Standard)** is implemented as the current PRO baseline (datasets + sync).

## Who is this for?

### SEO analyst
- Search queries → landing pages / conversions.
- Segmentation by geo / devices, time dynamics.
- Keyword ideas and negatives (Wordstat) as a semantic planning input.

### Performance marketer
- Daily performance by campaign/adgroup/ad/keyword (CPC/CTR/CPA/CPL).
- Cross-check Direct spend/clicks with Metrica visits/goals.
- Audiences/retargeting (Audience): segments catalog + overlaps + best-effort perf proxy.

## Dataset design principles

1) Separate **dimensions** and **facts**
   - Dimensions: campaigns/adgroups/keywords/audiences (change slowly)
   - Facts: daily metrics, search phrases, landings (grow over time)
2) Deterministic keys
   - every row has a stable `primary_key` (e.g. `account_id + campaign_id + date`)
3) Incremental model
   - facts: partition by `date` (day chunks)
   - dimensions: periodic refresh via paging
4) Volume bounds
   - require `date_from/date_to` for heavy facts
   - chunk jobs in sync (7d default, 1d for heavy datasets)
5) Traceability
   - return `raw_refs` describing which raw calls were made (what/with which params).

## Datasets (Variant B — Standard)

### Direct

Dimensions:
- `dashboard.dataset.direct_campaigns_dim`
- `dashboard.dataset.direct_adgroups_dim`
- `dashboard.dataset.direct_keywords_dim`

Facts:
- `dashboard.dataset.direct_campaign_daily`
- `dashboard.dataset.direct_keyword_daily` (heavy; chunked per-day in sync)
- `dashboard.dataset.direct_ads_daily` (heavy; chunked per-day in sync)
- `dashboard.dataset.direct_search_phrases_daily` (very heavy; only when needed)

Snapshots:
- `dashboard.dataset.direct_bids_snapshot`

### Metrica

Facts:
- `dashboard.dataset.metrica_daily`
- `dashboard.dataset.metrica_devices_daily`
- `dashboard.dataset.metrica_geo_daily` (country by default; city optional)
- `dashboard.dataset.metrica_goals_daily` (requires `goal_ids`)
- `dashboard.dataset.metrica_utm_campaigns_daily` (bounded by `limit_per_day`)
- `dashboard.dataset.metrica_landing_pages_daily` (bounded by `limit_per_day`)

### Wordstat (manual / ad-hoc)

- `dashboard.dataset.wordstat_top_requests` (bounded; input-driven)

### Audience

- `dashboard.dataset.audience_segments`
- `dashboard.dataset.audience_overlap` (requires `segment_ids`)
- `dashboard.dataset.audience_segment_perf_daily` (requires `segment_ids` + dates; best-effort proxy)

### Join (manual / ad-hoc)

- `dashboard.dataset.join_direct_vs_metrica_utm_daily`

## Sync API (incremental)

Tools:
- `dashboard.sync.start` → returns `cursor` (base64url JSON)
- `dashboard.sync.next` → returns `ndjson` + next `cursor`

Cursor/job model:
- Jobs are a cartesian product of (`dataset` × `account_id` × `date_chunk`) for date-based facts.
- Output is NDJSON (one JSON per line):
  - `{ "dataset": "...", "account_id": "...", "row": { ... } }`

Recommended consumer behavior:
- Store your own “watermark” (e.g., the last `date` fully ingested).
- Run sync again with the next `date_from`.

## PRO write scope (full contour)

Direct:
- Raw writes: `direct.create_*`, `direct.update_*` (guarded)
- HF writes: use plan/apply:
  - `direct.hf.plan_changes` → `direct.hf.apply_plan`

Audience:
- Raw writes: `audience.segments.create/update/delete`, `audience.upload.*` (guarded)
- HF activation: `audience.hf.activation_plan` (preview) / `audience.hf.apply_activation_plan` (apply)

Wordstat:
- No Direct writes inside Wordstat tools; “write value” is applying recommendations to Direct via `direct.hf.plan_changes` / `direct.hf.apply_plan`.

Metrica:
- Logs API operations are used for joins/exports.
- Management writes: goals CRUD (`metrica.goals.*`, `metrica.hf.*`, apply-guarded).

