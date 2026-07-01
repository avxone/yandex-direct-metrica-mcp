# Session: Search SERP recovery and release

## Completed

- Verified that `main` did not actually contain the `search_serp` runtime despite GEO-10 PR metadata claiming it had been published.
- Recovered the published feature commit `8ece1fea8ccd9f260956d19d35c3636745d13fa8` from GitHub and restored the missing runtime, tests, snapshots, and handoff docs into the current checkout.
- Fixed `scripts/check_wordstat_access.py` so monthly live validation retries a buffered closed month when the freshest closed month is not yet accepted by the provider.
- Verified local validation:
  - `python -m compileall -q src/mcp_yandex_ad scripts/check_wordstat_access.py scripts/check_search_serp_access.py`
  - `pytest -q`
  - `python scripts/agent_lint.py`
- Verified live validation using external credentials from an external state file such as `<state-root>/yandex.ad/.env`:
  - Direct OK
  - Metrica OK
  - Wordstat OK
  - Search SERP OK
- Prepared release metadata for `v2.0.13`.

## To Do

- Run `python scripts/release_guard.py --version 2.0.13 --require-release-notes`.
- Commit the recovered feature plus release metadata.
- Push `main`.
- Create and push tags `v2.0.13` and `pro-v2.0.13`.
- Publish GitHub Release `v2.0.13`.
- Verify GitHub Actions for:
  - `CI`
  - `Docker Publish (Public)`
  - `Docker Publish (Pro)`
  - `GitHub Release`
- Refresh local Docker aliases so `latest` points at the new release artifacts used by downstream consumers.
