# Wordstat next-release recommendations - 2026-06-19

## Completed
- Reviewed the current Wordstat Search API implementation against the Habr article, AI Studio Wordstat docs, and Yandex Cloud proto spec.
- Added English and Russian next-release recommendation documents:
  - `docs/wordstat-search-api-next-release-recommendations-2026-06-19.md`
  - `docs/ru/wordstat-search-api-next-release-recommendations-2026-06-19.md`
- Captured recommended next-release scope:
  - fix `wordstat.regions` payload mapping to `region: REGION_*`;
  - include `associations` in HF keyword suggestions and dashboard Wordstat candidates;
  - harden `wordstat.dynamics` date handling;
  - clarify `wordstat.user_info` semantics;
  - document Search API role/scope requirements and provider limitations.

## To Do
- Implement the P0 Wordstat fixes in code and tests.
- Refresh setup/LLM docs with `search-api.webSearch.user` and API key scope guidance.
- Run `pytest -q` and one gated live Search API smoke test before tagging the next release.

