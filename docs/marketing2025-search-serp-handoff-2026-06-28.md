# Marketing2025 handoff: `search_serp` SERP migration

This is the adoption note for moving eligible `Marketing2025` Yandex SERP
workflows from browser parsing to the `yandex.ad` MCP server.

## New MCP tool

Call `search_serp` from the `yandex.ad` MCP server.

Request example:

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

Response example:

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
    {
      "domain": "example.ru",
      "title": "Ad title",
      "snippet": "Ad snippet",
      "url": "https://example.ru",
      "position": 1
    }
  ],
  "ads_count_top": 1,
  "organic": [
    {
      "domain": "example.org",
      "title": "Organic title",
      "snippet": "Organic snippet",
      "url": "https://example.org",
      "position": 1
    }
  ],
  "captcha": false
}
```

## Coverage

| Client need | `search_serp` field | Notes |
| --- | --- | --- |
| Query echo | `query` | Preserved for traceability. |
| Region control | `region` | Defaults to server `YANDEX_SEARCH_API_DEFAULT_REGION` when omitted. |
| Device control | `device` | Implemented through Search API `userAgent`; response uses `DEVICE_DESKTOP`, `DEVICE_PHONE`, or `DEVICE_TABLET`. |
| Search type | `search_type` | Defaults to `SEARCH_TYPE_RU`; pass another provider enum only when the client needs a different search corpus. |
| Top ad slot count | `ads_count_top` | Counts ads before the first organic result in normalized order. |
| Ad domains/titles/snippets | `ads[]` | Requires `format=html`; parser runs inside MCP. |
| Organic domains/titles/URLs | `organic[]` | Available for `format=html`; XML can be used for organic-only debugging. |
| Captcha detection | `captcha` | True when the returned payload is a captcha/interstitial page. |
| Raw HTML review | `raw_html` | Only returned when `include_raw=true`; do not make prompt-space parsing the default path. |

## What changes for Marketing2025

- Replace Playwright SERP page loading for covered queries with `search_serp`.
- Treat `ads` and `organic` as the source of truth instead of scraping prompt text.
- Keep the existing query list, region IDs, and desktop/mobile intent mapping.
- Map current mobile requests to `device=phone` or `device=mobile`.
- Use `include_raw=true` only for diagnostics or parser review artifacts.

## What can remain fallback

- Keep browser inspection as a manual/debug fallback for visual layout questions.
- Keep Playwright for Yandex SERP elements not covered by the normalized contract.
- Use fallback when `captcha=true`, Search API credentials are absent, or the Search
  API returns no usable result buckets for a query that must be inspected visually.

## Compatibility notes

- `search_serp` is read-only and uses Yandex Search API credentials, not Direct or
  Metrica OAuth.
- `format=html` is the expected first implementation path because ad extraction is
  required.
- XML responses are useful for organic result support/debug fields, but the client
  should not expect ads from XML.
- The MCP response intentionally omits raw HTML by default to keep payloads small
  and prevent client-side prompt parsing from becoming the primary contract.
