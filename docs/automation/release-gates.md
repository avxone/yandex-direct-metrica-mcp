# Release Gates

Date: 2026-06-19

This document defines the hard gates for agent-driven delivery in this repository.

## Required Flows

### Feature Issue Flow

Every feature or bug issue must pass these gates in order:

1. Implementation completed in an isolated Symphony workspace.
2. Review completed by a separate agent role.
3. `Feature Validation` passed.
4. Feature review passes and the issue moves to `Done`.
5. PR follow-up issue is created.

If the feature has label `release-required`, continue with the release flow only after the PR follow-up issue passes review.

### Release Issue Flow

Every release issue must pass these gates in order:

1. All release-bound changes already landed on the release target branch.
2. CI checks passed.
3. Live validation passed against real configured providers.
4. Release guard passed.
5. Commit, push, tags, GitHub Release, and image publishing completed.

The release implementation step must stop on the first failing gate.

## Gate 1: Implementation

Implementation agent requirements:

- work only in an isolated workspace;
- update code, tests, docs, and `CHANGELOG.md`;
- leave a short handoff file (`SYMPHONY_WORK_RESULT.md`);
- never publish, tag, or push.

## Gate 2: Review

Review agent requirements:

- review from a separate run/state;
- check behavioral regressions, public/pro boundaries, docs drift, missing tests, and secrets exposure;
- return the issue to rework if findings exist;
- only pass the issue forward when findings are empty;
- create the next follow-up issue when the current stage is complete:
  - feature -> PR
  - PR + `release-required` -> release

## Gate 3: Stage-Specific Validation

The current stage must execute only its own validation section from the issue body.

### Feature Validation

Typical feature-stage gates:

- `python -m compileall -q src/mcp_yandex_ad`
- targeted or full `pytest`, as explicitly required by the issue
- changed-line lint via `python scripts/agent_lint.py`
- contract/schema/snapshot alignment when the tool surface changes
- docs/handoff checks when the issue requires them

If the feature issue explicitly requires bounded read-only live validation, that requirement belongs in `Feature Validation` and may be executed at feature stage.

### PR Validation

Typical PR-stage gates:

- `python -m compileall -q src/mcp_yandex_ad`
- `pytest -q`
- `python scripts/agent_lint.py`
- branch / commit / push / PR creation checks

### Release Validation

Typical release-stage gates:

- `python -m compileall -q src/mcp_yandex_ad`
- `pytest -q`
- `python scripts/agent_lint.py`
- `python scripts/live_validation.py`
- `python scripts/release_guard.py --version X.Y.Z --require-release-notes`

Note: repository-wide `ruff check .` is not yet a valid hard gate because the repo has an existing lint baseline outside current agent work. The gate is intentionally scoped to changed lines.

## Gate 4: Live Validation

Live validation must use real credentials and bounded read-only checks when it is required by the current stage validation:

- `python scripts/live_validation.py`

Current suites:

- `direct`
- `metrica`
- `wordstat`
- `search`

Rules:

- use read-only calls only;
- use bounded payloads and short date ranges;
- do not run destructive write paths;
- if a write validation is ever required, it must use sandbox/test accounts only.

## Gate 5: Release Guard

Release guard must pass:

- `python scripts/release_guard.py --version X.Y.Z --require-release-notes`

Current checks:

- `pyproject.toml` version matches the intended release;
- `CHANGELOG.md` has a release section;
- `docs/releases/vX.Y.Z.md` exists;
- Dockerfile defaults remain public safe-by-default;
- docs do not contain machine-specific local paths.

## Gate 6: Publish

Publish steps:

1. commit release changes;
2. push branch / `main`;
3. create and push public tag `vX.Y.Z`;
4. create and push gated pro tag `pro-vX.Y.Z`;
5. create GitHub Release for `vX.Y.Z`;
6. verify public and pro Docker workflows succeeded;
7. pull the published images into local Docker and refresh local `latest` aliases.

## Approval Boundary

The process is agent-driven, but approval-sensitive operations still need explicit release readiness:

- `git push` to the canonical repo;
- tag creation;
- GitHub Release creation;
- public/pro image publication.

Those actions should be executed only after the previous five gates are green.

## PR Publication Gate

The PR follow-up issue must:

1. create the issue branch;
2. commit the approved workspace change;
3. push the branch;
4. open or update the GitHub PR;
5. comment the PR URL back to Linear.

Feature issues should not tag or publish releases directly.
