# Session: Stage-specific validation for Symphony follow-up issues

Date: 2026-06-28

## Completed

- Updated the Symphony intake guidance, issue-writing rules, release gates, and workflow prompts to require stage-specific validation sections:
  - `Feature Validation`
  - `PR Validation`
  - `Release Validation`
- Added explicit `Execution Profile` guidance with `Issue Class` and `Risk` fields for Symphony-managed issues.
- Updated `scripts/linear_issue.py` so auto-generated PR and release follow-up issues include execution profile metadata and the new stage-scoped validation sections.
- Updated `tests/test_linear_issue_followups.py` and verified the repo test suite passes with `PYTHONPATH=. pytest -q`.
- Rewrote the local `search_serp` redo draft to use the new validation model.
- Updated the live Linear issue `GEO-9` so Symphony will read the corrected validation contract instead of the older mixed-stage checklist.

## To Do

- Commit and push the workflow/process changes so Symphony can run from a clean base.
- Refresh the external Symphony workflow files under `<symphony-root>/workflows/` if they differ from the repo copies.
- Re-launch the implementation and review lanes against the updated `GEO-9` issue.
- Observe one full `Todo -> In Progress -> In Review -> Done` pass for the feature issue before creating any PR or release follow-up issues.
