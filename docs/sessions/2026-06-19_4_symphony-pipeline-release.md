# Session - 2026-06-19 - Symphony pipeline release prep

## Completed
- Merged the `GEO-6` Wordstat Search API hardening changes into the main working tree.
- Added a first explicit Symphony/Linear delivery pipeline layer:
  - `docs/automation/release-gates.md`
  - `docs/automation/symphony-pipeline.md`
  - `scripts/agent_lint.py`
  - `scripts/check_wordstat_access.py`
  - `scripts/live_validation.py`
  - `scripts/release_guard.py`
  - `.github/workflows/live-validation.yml`
  - `.github/workflows/github-release.yml`
- Expanded CI with compile and Docker public build smoke checks.
- Ran local validation:
  - `python -m compileall -q src/mcp_yandex_ad`
  - targeted Wordstat tests
  - `pytest -q`
  - changed-line lint
- Ran real live validation against the state folder credentials in `/path/to/yandex.ad/.env`:
  - Direct
  - Metrica
  - Search API Wordstat
- Prepared release metadata for `v2.0.12`:
  - `pyproject.toml`
  - `CHANGELOG.md`
  - `docs/releases/v2.0.12.md`

## To Do
- Create the release commit.
- Push `main`.
- Push tag `v2.0.12`.
- Push gated pro tag `pro-v2.0.12`.
- Confirm GitHub Actions results for:
  - `CI`
  - `GitHub Release`
  - `Docker Publish (Public)`
  - `Docker Publish (Pro)`
- Verify Linear/Slack completion signaling on the next task through the same pipeline.
