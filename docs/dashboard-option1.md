# Dashboard generator (Option 1)

Tool: `dashboard.generate_option1`

Outputs:
- `*.html` (self-contained dashboard)
- `*.json` (same data; convenient for diffs and automated checks)

## Common usage patterns

### Single account

Arguments (example):
- `account_id`: profile id from `accounts.json`
- `date_from`: `YYYY-MM-DD`
- `date_to`: `YYYY-MM-DD` (recommended: **yesterday**)
- `output_dir`: where to write files
- `dashboard_slug`: optional, for nicer filenames
- `return_data=false`: avoid token-limit issues in Claude Code

### Multi-account

Use:
- `all_accounts=true`
or
- `account_ids=[...]`

The generated HTML contains an account selector and switches content client-side.

## Notes

- “Today” data can be incomplete in Direct/Metrica; for daily use set `date_to` to yesterday.
- Campaign-level CPL/leads can be **best-effort** and may be gated if Metrica attribution filters fail (to avoid misleading numbers).

## Wordstat (optional)

You can include Wordstat-based keyword suggestions:
- `include_wordstat=true`
- Optional tuning:
  - `wordstat_max_campaigns`
  - `wordstat_max_seed_phrases_per_campaign`
  - `wordstat_num_phrases`
  - `wordstat_max_candidates_per_campaign`
  - `wordstat_max_negatives_per_campaign`
  - `wordstat_language`
  - `wordstat_regions`, `wordstat_devices`

In multi-account mode (`all_accounts=true` / `account_ids=[...]`) Wordstat suggestions are computed per selected account dataset and switch together with the account selector.

## Audience (optional)

You can include Audience segments + overlaps blocks:
- `include_audience=true`

In multi-account mode (`all_accounts=true` / `account_ids=[...]`) Audience data is computed once per selected account dataset and switches together with the account selector.

