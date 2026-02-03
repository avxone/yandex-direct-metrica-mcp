# 2026-02-03 — Audience + BI Option 2 implementation

## Completed

- Implemented Audience config + HTTP client + error normalization.
- Added Audience tools:
  - Raw: `audience.*` (read-only) + pro-only write (`segments.*`, `upload.*`) + `audience.raw_call`.
  - HF: `audience.hf.*` (read-only) + pro-only activation (`activation_plan`, `apply_activation_plan`).
- Implemented BI Option 2 tools:
  - `dashboard.schema`
  - `dashboard.dataset.audience_segments`
  - `dashboard.dataset.audience_overlap`
  - `dashboard.dataset.audience_segment_perf_daily` (best effort)
  - `dashboard.sync.start` / `dashboard.sync.next` (cursor + NDJSON)
- Integrated Audience into Option 1 dashboard:
  - `dashboard.generate_option1` supports `include_audience=true`
  - Option 1 HTML template renders an Audience card (segments + overlaps).
- Updated public tools snapshot and added tests for Option 2 sync.

## To Do

- Tighten Audience API path coverage based on real API responses (overlap/stats/upload endpoints are best-effort).
- Extend `audience.hf.segment_perf` to include Metrica metrics where feasible (documented limitations).
- Implement bid modifiers / richer activation targets for `audience.hf.apply_activation_plan`.
- Decide whether to add pro-only `audience.raw_call` allowlist constraints (Option A hardening).

