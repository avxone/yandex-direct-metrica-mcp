# Session Note - 2026-06-30 - Stage handoff artifacts for Symphony follow-up issues

## Completed

- Confirmed that the updated browser/evidence workflow now lets `GEO-9` move from `Todo` to `In Review` and then `Done`.
- Confirmed that the review lane now creates `GEO-10` automatically as the PR follow-up issue.
- Identified the next pipeline defect: `GEO-10` starts from a fresh clone on `main` without a portable source diff artifact from `GEO-9`.
- Updated `scripts/linear_issue.py` so PR and release follow-up issue bodies now include:
  - the deterministic source workspace path;
  - mandatory source-stage artifact expectations;
  - explicit source-handoff requirements for PR and release execution.
- Updated the Symphony implementation/review workflow docs so:
  - feature issues must preserve `SYMPHONY_STAGE_PATCH.diff` and `SYMPHONY_STAGE_HANDOFF.md`;
  - PR issues must preserve `SYMPHONY_STAGE_HANDOFF.md` with branch, commit, and PR URL;
  - review must reject approval if those handoff artifacts are missing.
- Updated intake/issue-writing docs to document the new stage-handoff contract.
- Stopped the live `GEO-10` run and moved it back to `Backlog` to avoid burning tokens on a PR stage that lacked source artifacts.

## To Do

- Create the missing `GEO-9` handoff artifacts in the source workspace.
- Sync the updated workflow docs into the live Symphony workflow directory.
- Update `GEO-10` so its body reflects the new source-handoff requirements.
- Restart the implementation lane and move `GEO-10` back to `Todo`.
- Verify that the PR stage produces a real branch, commit, PR URL, and follow-up-ready handoff for release.
