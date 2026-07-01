# Session: Follow-up issue pipeline for Symphony

Date: 2026-06-27

## Completed

- Replaced the old state-based Symphony design that depended on nonexistent Linear states `Approved` and `Releasing`.
- Updated the active model to:
  - two Symphony lanes: `implementation` and `review`
  - follow-up issue chain: `feature -> PR -> release`
  - routing labels: `issue-type:feature`, `issue-type:pr`, `issue-type:release`
- Extended `scripts/linear_issue.py` with:
  - `followup-pr`
  - `followup-release`
- Added focused follow-up harness tests:
  - `tests/test_linear_issue_followups.py`
- Rewrote the main automation docs and workflow files to match the two-lane follow-up issue model.
- Added a repo-local intake skill:
  - `.codex/skills/linear-symphony-intake/`

## To Do

- Copy the updated workflow files into `<symphony-root>/workflows/`.
- Stop any old PR/release Symphony sessions that still use ports `3323` and `3324`.
- Restart Symphony with only the implementation and review lanes.
- Create the missing PR and release follow-up issues for `GEO-7` using the updated harness.
- Run the new pipeline end to end on `GEO-7` and confirm Linear state transitions, PR creation, release publication, and local Docker alias refresh behave as expected.
