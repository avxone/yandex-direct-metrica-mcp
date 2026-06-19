# Issue Draft: Harden Wordstat Search API integration for the next release

## Title

Harden Yandex Search API Wordstat integration: regions payload, associations, dynamics dates, access checks, docs

## Type

Feature hardening / bug fix / documentation

## Suggested Labels

- `wordstat`
- `search-api`
- `bug`
- `enhancement`
- `docs`
- `next-release`

## Background

The project has already migrated Wordstat runtime calls from the retired legacy Wordstat API to Yandex Search API Wordstat:

- base URL: `https://searchapi.api.cloud.yandex.net/v2/wordstat/`
- credentials:
  - `YANDEX_SEARCH_API_FOLDER_ID`
  - `YANDEX_SEARCH_API_API_KEY` or `YANDEX_SEARCH_API_IAM_TOKEN`
- current client: `src/mcp_yandex_ad/wordstat_client.py`
- current handlers/builders: `src/mcp_yandex_ad/server.py`
- current HF layer: `src/mcp_yandex_ad/hf_wordstat.py`

The migration is directionally correct and already better than a minimal wrapper: it has MCP guardrails, public/pro separation, retries, rate limiting, cache support, HF tools, and dashboard integration.

However, a follow-up review against:

- Habr article: https://habr.com/ru/articles/1030276/
- AI Studio Wordstat docs: https://aistudio.yandex.ru/docs/en/search-api/concepts/wordstat.html
- Yandex Cloud proto spec: https://github.com/yandex-cloud/cloudapi/blob/master/yandex/cloud/searchapi/v2/wordstat_service.proto

found several hardening items that should be completed before the next release.

Detailed planning document:

- `docs/wordstat-search-api-next-release-recommendations-2026-06-19.md`
- `docs/ru/wordstat-search-api-next-release-recommendations-2026-06-19.md`

## Goal

Make Wordstat Search API support reliable enough that downstream agents and dashboard workflows can use it without knowing provider-specific quirks.

The next release should remove known API-shape mismatches, improve semantic quality by using `associations`, and document the operational requirements for Yandex Search API credentials.

## Non-Goals

- Do not add Direct write/apply behavior to public mode.
- Do not add a broad public `wordstat.raw_call` escape hatch.
- Do not introduce a heavyweight Yandex SDK solely for Wordstat.
- Do not disable TLS verification as a workaround.
- Do not add live Search API calls to default CI.

## Scope

### 1. Fix `wordstat.regions` payload mapping

Current issue:

`_build_wordstat_regions_payload()` emits:

```python
payload["regionType"] = str(region_type).strip()
```

Yandex Search API v2 expects the field `region`, with enum values:

- `REGION_ALL`
- `REGION_CITIES`
- `REGION_REGIONS`

Implement normalization:

```text
all -> REGION_ALL
cities -> REGION_CITIES
regions -> REGION_REGIONS
REGION_ALL -> REGION_ALL
REGION_CITIES -> REGION_CITIES
REGION_REGIONS -> REGION_REGIONS
```

Keep `params` raw override unchanged.

Acceptance criteria:

- `wordstat.regions` with `region_type="regions"` sends `{"region": "REGION_REGIONS"}`.
- `wordstat.regions` with `region_type="cities"` sends `{"region": "REGION_CITIES"}`.
- `wordstat.regions` with `region_type="all"` sends `{"region": "REGION_ALL"}`.
- `wordstat.regions` without `region_type` omits `region`.
- Tests cover aliases and raw `params` passthrough.
- Tool schema/docs mention the `REGION_*` mapping.

### 2. Include `associations` in HF keyword suggestions

Current issue:

`wordstat.hf.suggest_keywords` reads only `topRequests` / `results`.

Search API `topRequests` returns:

- `results`: popular queries containing the phrase/words.
- `associations`: semantically related queries.

The `associations` field can contain the best keyword candidate, spelling variant, or broader head term. Ignoring it reduces recommendation quality.

Implement:

- Extract both `results` and `associations`.
- Aggregate candidates from both lists.
- Preserve source metadata in HF output.

Recommended candidate shape:

```json
{
  "phrase": "чатбот",
  "score": 7371,
  "sources": ["чат бот для бизнеса"],
  "provider_sources": ["association"]
}
```

If the same phrase appears in both lists:

```json
"provider_sources": ["result", "association"]
```

Use raw provider counts as score for this release. Do not introduce weighting yet.

Acceptance criteria:

- HF suggestions include candidates from `associations`.
- Output distinguishes `result`, `association`, and `both`.
- Duplicate phrases across both lists are merged.
- Empty/missing `associations` is handled without errors.
- Cursor/resumable behavior remains intact.

### 3. Include `associations` in dashboard Wordstat candidates

Current issue:

Dashboard Wordstat block aggregates only `topRequests` / `results`.

Implement:

- Merge `results` and `associations` when building campaign-level Wordstat candidates.
- Preserve source type in returned JSON.
- If UI scope is too large, it is acceptable to expose source type only in raw JSON for this release.

Acceptance criteria:

- Dashboard Wordstat block can surface candidates from `associations`.
- Candidate JSON includes source type metadata.
- Existing dashboard fallback/warning behavior remains unchanged.
- Tests cover a response where useful candidates exist only in `associations`.

### 4. Harden `wordstat.dynamics` date handling

Current issue:

Search API `dynamics` has provider constraints:

- `period` must be `PERIOD_MONTHLY`, `PERIOD_WEEKLY`, or `PERIOD_DAILY`.
- monthly `toDate` must be the last day of the month.
- weekly `toDate` must be the last day of the week.

Current code handles `YYYY-MM` monthly conversion, but weekly boundaries are not explicit. Plain `YYYY-MM-DD` `to_date` currently becomes midnight of that day, which may fail provider validation for weekly/monthly cases.

Implement:

- Keep existing `YYYY-MM` monthly behavior.
- Add period-aware validation or normalization for `to_date`.
- Do not modify raw `params` passthrough.
- Prefer clear validation over silent adjustment if the provider's week boundary is not confirmed.

Open decision:

Confirm whether Yandex Search API treats week end as Sunday, Monday, or another provider-specific boundary before auto-adjusting weekly dates.

Acceptance criteria:

- Monthly `YYYY-MM` still emits a last-day-of-month `toDate`.
- Weekly path either validates with an actionable error or uses confirmed auto-adjust behavior.
- Error messages explain how to fix invalid `to_date`.
- Tests cover monthly and weekly behavior.
- Docs mention the monthly/weekly `toDate` constraint.

### 5. Clarify `wordstat.user_info` semantics

Current issue:

Search API Wordstat exposes four methods:

- `GetTop`
- `GetDynamics`
- `GetRegionsDistribution`
- `GetRegionsTree`

There is no real Search API `userInfo` endpoint. Current `wordstat.user_info` returns a local config summary and may report `available=true` when env vars exist, without verifying provider access.

Choose one implementation:

Option A, preferred:

- Keep the tool name.
- Make it perform a lightweight live access check, likely `getRegionsTree` with cache.
- Return `available=true` only after provider success.

Option B:

- Keep current behavior.
- Rename/clarify output semantics so it returns `configured=true`, not verified availability.
- Update docs to call it a local config summary.

Do not add a new public tool unless the approved tool-list policy allows it.

Acceptance criteria:

- Docs no longer imply Search API has a native `userInfo` endpoint.
- `available=true` means provider access was actually verified, or the field is replaced/clarified.
- Invalid key / missing role errors produce actionable hints.

### 6. Document Search API role/scope requirements

Current issue:

Docs mention Search API env vars but do not consistently document access requirements.

Add setup guidance:

```text
Wordstat via Yandex Search API:
- service account belongs to the target folder
- service account has search-api.webSearch.user
- API key is created for that service account
- API key includes yc.search-api.execute if API key scopes are configured
- YANDEX_SEARCH_API_FOLDER_ID matches the folder
```

Update:

- `README.md`
- `.env.example`
- `docs/quickstart.md`
- `docs/public-mode.md`
- `docs/llm-usage-guide-2026-02-03.md`
- Russian equivalents in `docs/ru/`

Acceptance criteria:

- A new operator can configure Wordstat without reading the Habr article.
- Docs explicitly say Direct OAuth is not used for Search API Wordstat.
- Troubleshooting covers missing role/scope symptoms.

### 7. Document provider limitations

Add a provider limitations section:

- Web Wordstat operators such as `!word`, `+word`, and `[phrase]` do not provide full exact-match web UI semantics in Search API.
- Multi-phrase comparison is not native; this MCP loops phrase-by-phrase.
- Raw `count` fields can arrive as strings because protobuf `int64` is JSON-serialized as string.
- `associations` can be empty or missing.
- Region names require `getRegionsTree` mapping.

Acceptance criteria:

- LLM guide explains when to use raw vs HF Wordstat.
- Dashboard docs explain Direct keyword syntax cleaning before Wordstat expansion.
- Raw tools remain provider-shaped; HF tools remain normalized.

### 8. Improve error hints for common Search API failures

Current issue:

Error normalization gives generic token/rate-limit hints. Search API Wordstat has recurring setup and payload failures:

- missing `folderId`
- folder mismatch
- missing role/scope
- invalid enum
- monthly/weekly `toDate` boundary error

Implement:

- Safely parse provider response body for Wordstat errors.
- Do not log secrets or full request bodies.
- Add targeted hints for:
  - `folderId`
  - `PERIOD_*`
  - "last day of the month"
  - "last day of the week"
  - permission/role failures

Acceptance criteria:

- Monthly boundary provider error suggests using `YYYY-MM` or last day of month.
- Permission errors suggest checking `search-api.webSearch.user`.
- 429 and 5xx retry hints remain unchanged.

## Suggested Implementation Order

1. Add/adjust tests for Wordstat payload builders.
2. Fix `wordstat.regions` mapping.
3. Add shared extraction helper for `results` / `topRequests` / `associations`.
4. Update `wordstat.hf.suggest_keywords`.
5. Update dashboard Wordstat candidate aggregation.
6. Harden `wordstat.dynamics` date handling.
7. Clarify `wordstat.user_info`.
8. Improve error hints.
9. Update docs.
10. Run tests and a gated live smoke test.

## Test Plan

Run:

```bash
pytest -q
```

Add focused tests for:

- `WordstatClient._payload`
  - `folderId` injection
  - region int to string conversion
  - device alias normalization
  - period alias normalization
- `wordstat.regions` builder
  - `regions` -> `REGION_REGIONS`
  - `cities` -> `REGION_CITIES`
  - `all` -> `REGION_ALL`
  - raw `params` passthrough
- `wordstat.dynamics` builder
  - monthly `YYYY-MM`
  - weekly validation/normalization
  - raw `params` passthrough
- HF Wordstat suggestions
  - response with only `results`
  - response with only `associations`
  - duplicate phrase in both lists
  - missing/empty `associations`
  - cursor behavior preserved
- Dashboard Wordstat block
  - association-only candidate is included
  - warnings are preserved when Wordstat calls fail

Manual/gated live smoke tests:

- `wordstat.top_requests` with one phrase.
- `wordstat.get_regions_tree`.
- `wordstat.regions` with `region_type=regions`.
- `wordstat.dynamics` monthly with `YYYY-MM` range.

Do not add live calls to default CI.

## Release Notes Draft

```markdown
Wordstat: hardened Yandex Search API integration after the v2 migration. Fixed region distribution payload mapping, added `associations` to HF/dashboard keyword candidates, clarified Search API access checks, improved `dynamics` date handling, and documented the required `search-api.webSearch.user` role plus common provider limitations.
```

## Definition of Done

- P0 fixes implemented:
  - `wordstat.regions` uses `region: REGION_*`.
  - HF and dashboard paths consume `associations`.
- P1 hardening implemented or explicitly deferred with rationale:
  - `dynamics` dates.
  - `wordstat.user_info` semantics.
  - role/scope docs.
- Tests added and passing with `pytest -q`.
- Docs updated in English and Russian where setup instructions changed.
- `CHANGELOG.md` updated.
- One live Search API smoke test completed outside CI, if credentials are available.

## Handoff Notes

Start with `wordstat.regions` and `associations`; these have the best risk/value ratio.

The only potentially ambiguous implementation detail is weekly `toDate` handling for `wordstat.dynamics`. If live behavior cannot be confirmed quickly, implement validation and actionable errors instead of silent date adjustment.

Keep public mode safe-by-default. Wordstat remains read-only from the MCP user's perspective, even though provider-side report/stat computation happens upstream.

