# Symphony Pipeline

Date: 2026-06-19

This repository uses Symphony as the execution harness and Linear as the work queue.

The goal is to let the user describe work in Codex, then have agents execute, review, validate, and release it with explicit guardrails.

## Linear State Machine

Recommended issue states:

- `Backlog`
- `Todo`
- `In Progress`
- `In Review`
- `Approved`
- `Releasing`
- `Done`
- `Canceled`

## Agent Roles

### 1. Intake Agent

Input:
- user task in Codex
- optional markdown draft

Responsibilities:
- create or refine the issue body;
- split large work into bounded implementation issues when necessary;
- create the Linear issue via `scripts/linear_issue.py`;
- attach the correct labels.

### 2. Implementation Agent

Trigger:
- label `symphony`
- state `Todo` or `In Progress`

Responsibilities:
- clone repo into isolated workspace;
- move `Todo` -> `In Progress`;
- implement only the scoped issue;
- update tests, docs, changelog;
- run local gates;
- leave `SYMPHONY_WORK_RESULT.md`;
- move to `In Review`.

Guardrails:
- no push;
- no tags;
- no release;
- no Docker publish;
- no destructive API writes;
- no secrets written to files.

### 3. Review Agent

Trigger:
- label `symphony`
- state `In Review`

Responsibilities:
- inspect the isolated workspace diff;
- verify acceptance criteria, tests, docs, and boundaries;
- either:
  - comment findings and send back to `Todo`, or
  - mark `Approved`.

Guardrails:
- default posture is review, not feature implementation;
- no release operations.

### 4. Release Agent

Trigger:
- label `symphony`
- state `Approved`

Responsibilities:
- merge the validated change into the main repo;
- run full local gates;
- run live validation;
- bump version;
- update release notes;
- commit;
- push;
- create public/pro tags;
- create GitHub Release;
- move issue to `Done`.

Guardrails:
- release only after all gates are green;
- publish only using the project-approved artifact channels.

## Labels

Minimum labels:

- `symphony`
- task-specific labels such as `wordstat`, `dashboard`, `release`, `bug`, `enhancement`

Optional routing labels:

- `release`
- `live-validation`
- `needs-review`

## Required Local Gates

Implementation agent:

- `python -m compileall -q src/mcp_yandex_ad`
- `pytest -q`
- `python scripts/agent_lint.py`

Release agent:

- `python -m compileall -q src/mcp_yandex_ad`
- `pytest -q`
- `python scripts/agent_lint.py`
- `python scripts/live_validation.py`
- `python scripts/release_guard.py --version X.Y.Z --require-release-notes`

## GitHub Actions

The repo should treat GitHub Actions as an independent arbiter, not as a substitute for local agent checks.

Required workflows:

- CI
- live validation
- GitHub Release publish
- Docker Publish (Public)
- Docker Publish (Pro)

## Slack Notification

Preferred completion signal:

- release agent moves issue to `Done`;
- Linear sends project/channel notification to Slack;
- GitHub Release and Docker workflows provide the technical source of truth.

This avoids sending “done” notifications before the actual release artifacts exist.
