# Session: Issue capability contract for Symphony

Date: 2026-06-29

## Completed

- Added explicit capability and secret-dependency requirements to the Symphony issue templates:
  - `Required Capabilities`
  - `External Inputs / Secrets`
  - `Blocked Input Policy`
- Updated intake guidance, issue-writing rules, and the intake skill/checklist so capability requirements are mandatory during issue shaping.
- Added `docs/automation/capability-matrix.md` to formalize:
  - browser mode selection
  - live API expectations
  - manual-check ownership
  - `Backlog` vs `Todo` blocker routing

## To Do

- Apply the new capability contract to the active `GEO-9` issue body.
- Decide whether browser-visible SERP comparison for `GEO-9` is:
  - `playwright`
  - `chrome-devtools`
  - or `operator-browser`
- Extend release-stage templates and PR/release follow-up issue generation if stage-specific capability declarations are needed there too.
