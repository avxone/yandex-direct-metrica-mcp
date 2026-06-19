# Linear Intake Harness

Date: 2026-06-19

## Completed

- Added Linear issue templates under `docs/automation/templates/`.
- Added `docs/automation/linear-intake.md` with the Codex-to-Linear intake workflow.
- Added `scripts/linear_issue.py`, a dependency-free CLI that previews or creates Linear issues from Markdown drafts.
- Created local non-secret config at `/path/to/Symphony_yaad/linear.yandexad.json`.
- Created Linear issue `GEO-6` from `docs/wordstat-search-api-hardening-issue-2026-06-19.md`.
- Verified `GEO-6` is in `Backlog`, belongs to project `Yandex.AD`, and has Symphony/Wordstat labels.

## To Do

- Use `preview` before creating future Linear issues from drafts.
- Move a Symphony-labeled issue from `Backlog` to `Todo` only when it is approved for execution.
- Consider adding a dedicated `WORKFLOW.md` once the Linear/Symphony operating model stabilizes.
