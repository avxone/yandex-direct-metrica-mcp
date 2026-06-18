# Wordstat Search API migration - 2026-06-18

## Completed
- Confirmed the local state `.env` now provides `YANDEX_SEARCH_API_FOLDER_ID` and `YANDEX_SEARCH_API_API_KEY`.
- Migrated the Wordstat HTTP client from `https://api.wordstat.yandex.net/v1/` to `https://searchapi.api.cloud.yandex.net/v2/wordstat/`.
- Added Search API credential loading for `YANDEX_SEARCH_API_FOLDER_ID`, `YANDEX_SEARCH_API_API_KEY`, optional `YANDEX_SEARCH_API_IAM_TOKEN`, and optional `YANDEX_SEARCH_API_WORDSTAT_BASE_URL`.
- Updated Wordstat runtime checks so `wordstat.*` tools require Search API folder credentials instead of legacy Wordstat app-token variables.
- Preserved existing tool names while adapting payloads for the new API, including `folderId`, device/period enum normalization, and single-phrase looping for `topRequests`.
- Updated `.env.example`, `README.md`, tests, and `CHANGELOG.md`.
- Verified locally with `pytest -q` (`130 passed`).
- Verified live `topRequests` through the Python client and through the rebuilt Docker image `yandex-direct-metrica-mcp-pro:dev`.
- Added short Web Search async operator notes in `docs/yandex-search-api-web-search-2026-06-18.md` and `docs/ru/yandex-search-api-web-search-2026-06-18.md`.
- Removed legacy `auth.*` Wordstat wording and refreshed older docs to reference Yandex Search API credentials.

## To Do
- Monitor the next GitHub release workflows after the cleaned `v2.0.11` tag is published.
