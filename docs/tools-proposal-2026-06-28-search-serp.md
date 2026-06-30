# Proposed MCP tool - Search API SERP - 2026-06-28

This issue approves one bounded read-only Web Search tool for the public MCP
surface.

## `search_serp`

Purpose: fetch a Yandex Search API Web Search SERP and normalize the fields needed
by downstream SERP analysis clients.

Input:

```json
{
  "query": "гарнитура для колл центра купить",
  "region": 213,
  "device": "desktop",
  "format": "html",
  "mode": "sync",
  "n_results": 10
}
```

Output:

```json
{
  "query": "гарнитура для колл центра купить",
  "region": 213,
  "device": "DEVICE_DESKTOP",
  "format": "html",
  "mode": "sync",
  "n_results": 10,
  "page": 0,
  "search_type": "SEARCH_TYPE_RU",
  "ads": [
    {"domain": "example.ru", "title": "Ad title", "snippet": "Ad snippet", "url": "https://example.ru", "position": 1}
  ],
  "ads_count_top": 1,
  "organic": [
    {"domain": "example.org", "title": "Organic title", "snippet": "Organic snippet", "url": "https://example.org", "position": 1}
  ],
  "captcha": false
}
```

Contract notes:

- Read-only.
- Requires Yandex Search API credentials, not Direct OAuth.
- Uses synchronous Web Search (`/v2/web/search`) for the MCP call.
- `format=html` is the default because ads are required.
- `device` maps to Search API `userAgent`; output is normalized.
- Raw HTML/XML is optional and omitted by default.
- Parser ownership stays in MCP; clients consume normalized fields.
