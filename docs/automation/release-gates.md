# Release Gates

Date: 2026-06-19

This document defines the hard gates for agent-driven delivery in this repository.

## Required Flow

Every implementation task must pass these gates in order:

1. Implementation completed in an isolated Symphony workspace.
2. Review completed by a separate agent role.
3. CI checks passed.
4. Live validation passed against real configured providers.
5. Release guard passed.
6. Commit, push, tags, GitHub Release, and image publishing completed.

The release lane must stop on the first failing gate.

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
- only pass the issue forward when findings are empty.

## Gate 3: CI

CI must pass:

- `python -m compileall -q src/mcp_yandex_ad`
- `pytest -q`
- changed-line lint via `python scripts/agent_lint.py`
- public Docker build smoke

Note: repository-wide `ruff check .` is not yet a valid hard gate because the repo has an existing lint baseline outside current agent work. The gate is intentionally scoped to changed lines.

## Gate 4: Live Validation

Live validation must use real credentials and bounded read-only checks:

- `python scripts/live_validation.py`

Current suites:

- `direct`
- `metrica`
- `wordstat`

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
6. verify public and pro Docker workflows succeeded.

## Approval Boundary

The process is agent-driven, but approval-sensitive operations still need explicit release readiness:

- `git push` to the canonical repo;
- tag creation;
- GitHub Release creation;
- public/pro image publication.

Those actions should be executed only after the previous five gates are green.
