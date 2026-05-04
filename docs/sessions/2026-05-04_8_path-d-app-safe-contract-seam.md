# Session 2026-05-04 (8) — `Path D` app-safe contract seam

## Completed
- Added `docs/rfc/RFC-0003-app-safe-output-contracts.md` to formalize what counts as an app-safe backend payload without introducing MCP Apps runtime.
- Added internal helper functions in `src/mcp_yandex_ad/app_payloads.py`:
  - `compact_sections(payload)`
  - `is_app_safe_payload(payload)`
- Kept the helper intentionally conservative:
  - known bulky raw sections are removed by `compact_sections()`
  - payloads containing such sections fail `is_app_safe_payload()`
  - oversized opaque strings also fail `is_app_safe_payload()`
- Added tests proving:
  - raw-heavy payloads are rejected
  - existing compact dashboard-style outputs are accepted
  - compacting removes known heavy raw blocks
- Kept `Path D` within the agreed boundary:
  - no new MCP tool
  - no `resources`
  - no `ui://`
  - no client-specific widget/runtime behavior

## To Do
- Decide later whether selected `Path A` outputs should be explicitly checked with `is_app_safe_payload()` in tests or CI.
- Wait for approval before introducing any runtime app/resource exposure.
- Revisit per-tool app-safe rules only if a real MCP Apps implementation is approved later.
