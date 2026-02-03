# BI Dashboard Generator (Option 1): MCP → Data → HTML

Goal: generate a real BI dashboard (HTML + JSON) for a given `account_id` (or `direct_client_login`) and date range by pulling data from Yandex Direct + Metrica (optionally Wordstat/Audience) via this MCP server.

## Status (2026-01-27)
Implemented:
- Script: `scripts/generate_dashboard_option1.py`
- HTML template (docs): `docs/templates/dashboard-template-2026-01-27.html`
- HTML template (BI UI, used by the MCP tool): `docs/templates/dashboard-template-option1-2026-01-28.html`
- MCP tool: `dashboard.generate_option1` (no separate SSE client required; convenient in Claude Code)

Example (script; requires SSE transport; see `docker-compose.yml`):
```bash
python scripts/generate_dashboard_option1.py \
  --account-id <account_id> \
  --date-from 2026-01-01 \
  --date-to 2026-01-31 \
  --output-dir /path/to/dashboards
```

Example (MCP tool; in Claude Code / any MCP client):
- `dashboard.generate_option1` with `output_dir` returns file paths (`files.html_path`, `files.json_path`).
- If `output_dir` is omitted, you can request HTML inline (`include_html=true`).
- To avoid chat token limits, prefer `output_dir` + `return_data=false` (default is `false` when `output_dir` is set). You still get a compact `summary` + `files.*`, while full rows are saved into JSON/HTML.

## 1) Input parameters
- `account_id` (preferred) — profile ID from `accounts.json` (enables multi-account behavior).
- Multi-account mode (one HTML/JSON with an account switcher):
  - `all_accounts=true` — include all profiles from `accounts.json`.
  - `account_ids=[...]` — include only the listed profiles.
- `date_from`, `date_to` — reporting period (e.g. `2025-12-01` … `2025-12-31`).
- `output_dir` — where to save artifacts (e.g. `/path/to/dashboards`).
- `dashboard_slug` (optional) — for a readable file name.
- `goal_ids` (optional) — Metrica goal IDs used to compute “Leads” (`ym:s:goal{ID}reaches`). If omitted, the generator attempts to include “all goals” via a `ym:s:goal` report (best effort).
- `return_data` (optional) — whether to return full `data` inline (defaults to `false` when `output_dir` is set).

Date note:
- If `date_to` is “today” (or future), `dashboard.generate_option1` auto-shifts `date_to` to **yesterday**, because Direct/Metrica same-day data is often incomplete.

## 2) Output artifacts
1) HTML dashboard (required)
- File name includes the account:
  - `yandexad_dashboard__{account_id}__{date_from}_{date_to}.html`, or
  - `yandexad_dashboard__{direct_client_login}__{date_from}_{date_to}.html`
- Multi-account mode:
  - `yandexad_dashboard__multi__{date_from}_{date_to}__{dashboard_slug}.html` (slug optional)
  - The HTML UI shows an “Account” selector in the top-right.

2) JSON data (recommended)
- `yandexad_dashboard__{account_id}__{date_from}_{date_to}.json`
- Multi-account mode:
  - `yandexad_dashboard__multi__{date_from}_{date_to}__{dashboard_slug}.json`

## 3) Data sources (via MCP)
Minimum:
- Direct: daily performance (impressions/clicks/cost) over the period.
- Metrica: daily visits (and, if possible, goals/leads) over the period.

The output is shaped to match the BI template expectations (see `docs/dashboard-option1.md` for the public spec).

## 4) Attribution caveat (funnels / CPA)
Important: `metrica.current.totals.visits` includes all sources. Using it for ad CPA can be misleading when non-ad traffic dominates.

Therefore the generator attempts to compute **Direct-attributed** series via Stats API slices (`ym:s:lastsignTrafficSource` + `ym:s:lastsignSourceEngine`) and uses those for the “Direct” funnel/CPA (best effort).

## 5) Option C: Search vs RSYA split (via `UTMCampaign`)
The UI campaign filter `All / Search / RSYA` changes Direct metrics based on Direct campaign classification (`search`/`rsya`).

To split Metrica visits/leads into Search/RSYA consistently, Option C uses:
- a Metrica Stats API report with dimensions `ym:s:date,ym:s:UTMCampaign`, mapped back to Direct campaigns.

`UTMCampaign` must be stable and map 1:1 to campaigns:
- recommended: include `campaign_id` inside `utm_campaign`, or
- use unique campaign names (exact match).

Some Direct-attributed traffic can remain **unclassified** (missing/unknown UTMCampaign). The UI explicitly shows coverage/missing values to avoid misleading totals.

## 6) “Recommendations” block
The Option 1 template renders two blocks:
- “Do today” (`recommendations.today_actions`)
- “Discussion questions” (`recommendations.discussion_questions`)

These are produced inside the MCP tool by simple heuristics (see `_dashboard_build_recommendations()` in `src/mcp_yandex_ad/server.py`). The HTML template only displays the data.

## 7) Definition of Done
- Accepts `account_id/date_from/date_to` and generates an HTML file with the correct naming.
- No hardcoded demo numbers in HTML — only MCP-fetched data.
- Recommendations are populated (or contain a meaningful “insufficient data” note).
- Output opens locally without JS errors.

## Notes
- Current BI templates use Chart.js from a CDN. For offline usage, you’ll need a local copy or a simplified chart implementation.
