# search_serp MCP tool - 2026-06-28

## Completed

- Added the read-only `search_serp` MCP tool for Yandex Search API Web Search.
- Implemented synchronous `/v2/web/search` request building with Search API
  credentials, configured default region, device-specific `userAgent`, and bounded
  `n_results`.
- Added MCP-side normalization for HTML SERP ads/organic results and XML organic
  debugging output.
- Kept raw HTML/XML out of the default response; `include_raw=true` is required.
- Added focused unit tests for payload building, HTML/XML parsing, and server
  helper behavior.
- Updated README, env example, Web Search notes, tool coverage, changelog, and
  the Marketing2025 handoff document.

## To Do

- Run live Search API validation outside this feature lane when credentials are
  available: `python scripts/live_validation.py --suite search`.
- Let the PR lane run full non-live gates, create the publishable branch commit,
  push, and open the GitHub PR.
- Let the release lane publish the image after PR review, because this feature
  carries `release-required`.
