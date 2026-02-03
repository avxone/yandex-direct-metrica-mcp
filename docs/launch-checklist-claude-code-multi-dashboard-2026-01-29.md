# Beta-ready checklist (Claude Code + multi-account dashboard)

Goal: reliably generate a single BI dashboard for multiple `account_id` profiles via the `yandexad` MCP server.

## 1) Accounts registry (`accounts.json`)
- Each profile `id` is **unique**.
- Each profile has `direct_client_login`.
- Each profile has exactly one counter: `metrica_counter_ids: ["<counter_id>"]`.
  - If there are multiple counters, pass `counter_id` explicitly when generating dashboards.
  - If no counter is set, the profile will appear in `accounts_errors` in multi-dashboard mode.

## 2) `.env` / access
- Direct/Metrica tokens are valid and never logged.
- `YANDEX_DIRECT_SANDBOX=false` for production scenarios.
- If you plan to edit `accounts.json` via MCP (pro-only): `MCP_ACCOUNTS_WRITE_ENABLED=true` and a correct `MCP_ACCOUNTS_FILE`.

## 3) Recommended dashboard params
- Multi-account:
  - `all_accounts=true` (or `account_ids=[...]` to exclude problematic profiles).
  - `output_dir` is required (so you don’t hit chat token limits).
  - `return_data=false` (faster/smaller reply; full rows stay in JSON/HTML).
- Date range:
  - `date_to` may be “today” — the server auto-shifts it to **yesterday** because same-day data is often incomplete in Direct/Metrica.

## 4) UI sanity-check (single HTML)
- Switching accounts (top-right) updates KPIs/charts/tables.
- Campaign filter `All / Search / RSYA / Unclassified` works:
  - In `Unclassified`, Direct KPIs may be `—` (no reliable attribution for cost/clicks/impressions).
- Goals:
  - `Direct / All sources` switch works.
  - Goal selector works.
- Sources:
  - No duplicate colors for different lines on the same chart.
- Funnels:
  - “Site (all sources)” and “Direct (Metrica-attributed)” are calculated separately.

## 5) Warnings/errors
- Warning `UTMCampaign engine filter rejected` is acceptable: Search/RSYA split might be less accurate, but data is present.
- If `accounts_errors` is present:
  - Treat as a blocker until the reason is understood (common causes: missing counter access, missing `metrica_counter_ids`, login mismatch).

## 6) Operations
- Canonical artifacts folder example: `/path/to/dashboards`.
- Refresh frequency: at least “once per day in the morning”; “today” is still auto-excluded.
