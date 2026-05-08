# `yandex.ad` contract update for `Marketing2025` consumers - 2026-05-08

## Purpose

This note documents the backend-side response changes that `Marketing2025` can start consuming after the May 8 release of `yandex.ad`.

It is intentionally narrow:

- only the fields and warnings that matter to `Marketing2025`
- no tool catalog review
- no orchestration guidance

## 1. Special / no-structure campaign diagnostics

### Affected tools

- `direct.hf.get_campaign_summary`
- `direct.list_campaigns`

### `direct.hf.get_campaign_summary`

When a campaign has zero structural counts but still shows live delivery/performance, the HF result may now include:

- `result.campaign_type = "SPECIAL_NO_STRUCTURE"`
- `result.campaign_type_hint`
- `result.counts_applicable = false`
- `result.performance_signal`

The HF envelope may also include:

- `warnings[].code = "campaign_type_special_no_structure"`

Interpretation:

- do not treat `0/0/0` counts as proof that the campaign is phantom or moot
- use `counts_applicable=false` as the primary machine signal that structural counts are not authoritative for this campaign
- use `performance_signal` as proof that live delivery still exists

### `direct.list_campaigns`

When an ID-based lookup returns no rows, `direct.list_campaigns` may substitute special campaign candidates based on live performance. In that case:

- `result.Campaigns[]` may contain objects with:
  - `Id`
  - `CampaignType`
  - `CountsApplicable`
  - `PerformanceSignal`
  - `Note`
- `result.Warnings[]` will explain that substitution happened

Interpretation:

- do not treat an empty initial `campaigns.get` result as final if substituted special candidates are present
- prefer live MCP diagnostics over `landing_map` placeholders such as `"(not in snapshot)"`

## 2. Metrica HF stats pagination and truncation warnings

### Affected tools

- `metrica.hf.report_landing_pages`
- `metrica.hf.report_utm_campaigns`
- `metrica.hf.report_geo`
- `metrica.hf.report_devices`

### New behavior

- if `limit` is omitted, these tools now paginate automatically and return the full bounded result set
- if you pass an explicit `limit` and it truncates rows, the HF envelope includes:
  - `warnings[].code = "metrica_rows_truncated"`

Interpretation:

- absence of the warning means the returned rows were not truncated by the explicit caller limit
- if the warning is present, downstream checks should treat the dataset as partial

## 3. Wordstat batch fallback metadata

### Affected tool

- `wordstat.top_requests`

### New behavior

If upstream Wordstat batch mode returns an unexpected response type, the server retries phrase-by-phrase and returns:

- `fallback.mode = "single_phrase_loop"`
- `fallback.reason`
- `fallback.requested_phrases`
- `topRequestsByPhrase[]`

Interpretation:

- downstream callers can continue using the response instead of failing the whole workflow
- if `fallback` is present, treat the response as successful but degraded

## 4. `direct.report` / `direct.hf.report_keywords` compatibility

### Affected tools

- `direct.report`
- `direct.hf.report_keywords`

### New behavior

- `direct.hf.report_keywords` now uses a valid `CUSTOM_REPORT` field set based on `Criterion`
- low-level `direct.report` now fails fast if `CUSTOM_REPORT` is requested with `Keyword`

Interpretation:

- for `CUSTOM_REPORT`, use `Criterion`, optionally with `CriterionId` and `CriterionType`
- do not rely on older `Keyword`-based custom report presets

## 5. Read-only Direct login override semantics

### Affected tools

- read-only `direct.*` calls, including raw read helpers

### New behavior

- for read-only Direct calls, an unknown `account_id` may be interpreted as `direct_client_login`
- read-only calls may also override a profile login with explicit `direct_client_login`

Interpretation:

- this is intended for agency/multi-login read scenarios only
- write flows should continue to use explicit validated account/profile resolution

## 6. `dashboard.generate_option1` side-effect contract

### New behavior

- the tool contract no longer marks `dashboard.generate_option1` as read-only when `output_dir` is used

Interpretation:

- if `output_dir` is set, the tool writes local HTML/JSON artifacts
- if a caller requires no local filesystem side effects, omit `output_dir`

## Migration Checklist For `Marketing2025`

1. In campaign validity, prefer live MCP diagnostics over `landing_map` placeholders.
2. Treat `counts_applicable=false` as a first-class machine signal.
3. Treat `metrica_rows_truncated` as partial coverage.
4. Accept `wordstat.top_requests` fallback responses instead of hard-failing on batch degradation.
5. Stop using `Keyword` for `CUSTOM_REPORT` compatibility assumptions.
