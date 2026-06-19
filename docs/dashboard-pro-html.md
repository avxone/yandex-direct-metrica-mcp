# PRO HTML Dashboard

Tool: `dashboard.generate_pro_html`

Purpose:
- generate a self-contained `HTML + JSON` dashboard without a database
- reuse the existing Option 1 visual shell
- add PRO diagnostics on top of the same artifact

Outputs:
- `*.html`
- `*.json`

## What It Adds Over Option 1

The PRO dashboard keeps the current Option 1 layout and adds extra cards driven by live MCP data:

- PRO summary counters
- campaign watchlist
- top search terms
- top keywords
- findings with severity and recommendations

The payload is attached under `data.pro` in the generated JSON.

## Typical Inputs

Single account:
- `date_from`
- `date_to`
- `output_dir`
- `direct_client_login` or `account_id`
- `counter_id` when it cannot be resolved automatically

Optional PRO tuning:
- `max_campaigns`
- `max_keywords`
- `max_search_phrases`
- `max_findings`
- `include_wordstat`
- `include_audience`

## Current Heuristics

The first version focuses on transparent operational diagnostics:

- expensive search phrases with weak click quality
- expensive high-bounce keywords
- campaigns with spend and no attributed leads
- campaigns with spend growth and no lead growth
- UTMCampaign classification gaps

These are heuristics, not autonomous optimization actions.

## Local Runner

Use the helper script when you want a local artifact directly from `.env`:

```bash
.venv/bin/python scripts/generate_dashboard_pro_html.py \
  --direct-client-login elama-16161182 \
  --counter-id 91450749 \
  --date-from 2026-04-12 \
  --date-to 2026-05-11 \
  --output-dir /private/tmp/yandexad-pro-dashboard-2026-05-12
```

## Notes

- The tool is PRO-only and hidden from the public read-only surface.
- If `output_dir` is provided, the tool writes local files and is therefore side-effecting with respect to the filesystem.
- No historical warehouse is required; the dashboard is built from current-period and previous-period live reads.
