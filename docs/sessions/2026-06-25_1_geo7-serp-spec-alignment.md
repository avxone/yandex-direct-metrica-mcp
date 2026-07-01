# Session: Align GEO-7 with Marketing2025 SERP API spec

Date: 2026-06-25

## Completed

- Read `Marketing2025/docs/serp-via-yandex-search-api-spec.md`.
- Reworked `docs/yandex-search-api-web-tools-issue-2026-06-20.md` to match the approved consumer need.
- Reworked `docs/ru/yandex-search-api-web-tools-issue-2026-06-20.md` to match the same scope in Russian.
- Narrowed the task from a generic “first consumer integration” to a concrete migration of `gap-overlay-report` off Playwright onto `search_serp`.
- Added `update` support to `scripts/linear_issue.py` for existing Linear tasks.
- Updated `docs/automation/linear-intake.md` with the issue-update flow.
- Updated live Linear issue `GEO-7` from the revised markdown draft.

## To Do

- Confirm whether the first implementation keeps `mode=sync` as default or introduces async immediately.
- Start execution against the revised Linear scope.
