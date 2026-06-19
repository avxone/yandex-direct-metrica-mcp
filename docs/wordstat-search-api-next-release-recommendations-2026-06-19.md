# Wordstat Search API next-release recommendations - 2026-06-19

## Purpose

This document turns the June 2026 review of the new Yandex Search API Wordstat surface into an actionable next-release plan for `yandex-direct-metrica-mcp`.

Sources reviewed:
- Habr: "Wordstat API in Yandex Cloud Search API: endpoints, pitfalls, minimal Python wrapper (2026)" - https://habr.com/ru/articles/1030276/
- AI Studio documentation, Wordstat concept page - https://aistudio.yandex.ru/docs/en/search-api/concepts/wordstat.html
- Yandex Cloud proto spec - https://github.com/yandex-cloud/cloudapi/blob/master/yandex/cloud/searchapi/v2/wordstat_service.proto
- Current project implementation around `src/mcp_yandex_ad/wordstat_client.py`, `src/mcp_yandex_ad/server.py`, `src/mcp_yandex_ad/hf_wordstat.py`, and Wordstat docs.

The short conclusion: the project is already on the correct API generation. The next release should focus on correctness fixes, better use of the new response fields, and clearer operator guidance.

## Current State

The core migration is already done:

- Runtime calls use `https://searchapi.api.cloud.yandex.net/v2/wordstat/`.
- Search API credentials are loaded from:
  - `YANDEX_SEARCH_API_FOLDER_ID`
  - `YANDEX_SEARCH_API_API_KEY`
  - optional `YANDEX_SEARCH_API_IAM_TOKEN`
  - optional `YANDEX_SEARCH_API_WORDSTAT_BASE_URL`
- `folderId` is injected automatically.
- `regions` are converted to strings for the provider API.
- `devices` are normalized to `DEVICE_*` enum values.
- `period` is normalized to `PERIOD_*` enum values.
- `getRegionsTree` is cacheable.
- `topRequests` multi-phrase input is handled by looping phrase-by-phrase because the new Search API accepts one phrase per request.
- Public mode remains safe-by-default: Wordstat is read-only from the MCP user's perspective, and Direct writes remain outside the public contract.

This is materially stronger than the minimal wrapper described in the Habr article. The project has guardrails, retries, rate limits, a public/pro contract, dashboard integration, and an HF layer.

## Release Recommendation

Recommended next release scope: **v2.0.12 Wordstat Search API hardening**.

Primary goal:

Make the Wordstat Search API migration reliable enough that downstream agents can use Wordstat without knowing the provider quirks.

Recommended inclusion:

1. Fix `wordstat.regions` payload mapping.
2. Include `associations` in HF keyword suggestions and dashboard Wordstat blocks.
3. Harden `wordstat.dynamics` date handling.
4. Clarify `wordstat.user_info` semantics.
5. Update README, `.env.example`, LLM usage docs, and release notes with Search API role/scope requirements and provider limitations.
6. Add focused tests for the provider-specific quirks.

Recommended exclusion:

- Do not add Direct write/apply behavior to public mode.
- Do not add broad `wordstat.raw_call` in public mode.
- Do not introduce a heavyweight SDK solely for Wordstat.
- Do not disable TLS verification as a macOS workaround.

## Priority 0: Fix `wordstat.regions` Payload

### Problem

The Yandex Search API proto defines `GetRegionsDistributionRequest.region` as an enum:

- `REGION_ALL`
- `REGION_CITIES`
- `REGION_REGIONS`

The Habr example also sends:

```json
{
  "phrase": "chat bot for business",
  "region": "REGION_REGIONS",
  "folderId": "..."
}
```

Current code builds:

```python
payload["regionType"] = str(region_type).strip()
```

That field name looks like the legacy/design-time naming, not the Search API v2 JSON field. This can make `wordstat.regions` fail or silently ignore the requested distribution type.

### Recommendation

Change the builder to emit `region`, not `regionType`.

Add a small normalizer:

```text
all -> REGION_ALL
cities -> REGION_CITIES
regions -> REGION_REGIONS
REGION_ALL -> REGION_ALL
REGION_CITIES -> REGION_CITIES
REGION_REGIONS -> REGION_REGIONS
```

Keep `params` raw override as-is for advanced users.

### Acceptance Criteria

- `wordstat.regions` with `region_type="regions"` sends `{"region": "REGION_REGIONS"}`.
- `wordstat.regions` with `region_type="cities"` sends `{"region": "REGION_CITIES"}`.
- `wordstat.regions` with no `region_type` omits `region` and lets the API default apply.
- Tests cover all aliases.
- Tool schema description explicitly names `REGION_*` mapping.

### Risk

Low. This is a correctness fix for a likely provider-field mismatch.

## Priority 0: Use `associations` as First-Class Keyword Candidates

### Problem

The new `topRequests` response has two useful lists:

- `results`: popular queries containing the phrase/words.
- `associations`: semantically related queries.

The current HF and dashboard paths only aggregate `topRequests` / `results`. The Habr article's strongest practical insight is that `associations` often contains the better formulation, spelling variant, or broader head term. Ignoring it loses the highest-value signal.

Relevant current behavior:

- `wordstat.hf.suggest_keywords` reads `topRequests` or `results`.
- Dashboard Wordstat block reads `topRequests` or `results`.
- Raw `wordstat.top_requests` already returns the provider response, so raw users can see `associations`; HF/dashboard users do not benefit from it.

### Recommendation

Include both lists in HF aggregation:

```text
candidate source = results + associations
```

Preserve source metadata:

```json
{
  "phrase": "chatbot",
  "score": 7371,
  "sources": ["chat bot for business"],
  "provider_sources": ["association"]
}
```

For candidates seen in both lists, keep both source labels:

```json
"provider_sources": ["result", "association"]
```

Consider a simple weighting rule:

- Option A: same weight for `results` and `associations`.
- Option B: multiply `associations` by `association_weight`, default `1.0`.
- Option C: keep raw counts as score and expose source type only.

Recommended for next release: **Option C**. It is easiest to explain and avoids inventing a ranking model.

### Dashboard Recommendation

For `dashboard.generate_option1` / PRO HTML Wordstat block:

- Merge `results` and `associations`.
- Preserve source type in hidden/raw JSON.
- In UI rows, add a compact source label if feasible:
  - `result`
  - `association`
  - `both`
- If UI scope is too large for this release, at least include associations in scoring and expose them in JSON.

### Acceptance Criteria

- HF suggestions include candidates from `associations`.
- Candidate metadata identifies whether a candidate came from `results`, `associations`, or both.
- Dashboard Wordstat candidates can include associations.
- Tests cover:
  - response with only `results`
  - response with only `associations`
  - duplicate phrase across both lists
  - missing/empty `associations`

### Risk

Medium-low. This changes ranking output. It is additive and improves quality, but snapshots or downstream expectations may need updates.

## Priority 1: Harden `wordstat.dynamics` Date Handling

### Problem

Search API `dynamics` requires:

- `period`: `PERIOD_MONTHLY`, `PERIOD_WEEKLY`, or `PERIOD_DAILY`.
- `fromDate`: RFC3339 timestamp.
- `toDate`: RFC3339 timestamp.

The provider has a non-obvious validation rule:

- monthly `toDate` must be the last day of the month.
- weekly `toDate` must be the last day of the week.

Current code handles `YYYY-MM` as month start/end, which is good for monthly use, but it does not explicitly handle weekly period boundaries. If the user passes a plain `YYYY-MM-DD`, `_wordstat_date_time(..., end=True)` currently returns `YYYY-MM-DDT00:00:00Z`, not the end of the day/week.

### Recommendation

Add period-aware normalization:

```text
period=monthly:
  YYYY-MM -> first day / last day of month
  YYYY-MM-DD to_date -> validate it is last day of month or adjust only if explicit flag says auto_adjust

period=weekly:
  YYYY-MM-DD to_date -> adjust/validate to week end

period=daily:
  YYYY-MM-DD to_date -> same day timestamp is acceptable
```

Recommended implementation path:

1. Keep current simple `YYYY-MM` monthly behavior.
2. For `period=weekly`, add a helper that maps `to_date` to the last day of that week.
3. For explicit `params` raw override, do not modify.
4. Add warnings or docs explaining the transformation.

Open decision: what is "week end" for Yandex Search API?

The article says "last day of week" but does not define locale. Before implementing auto-adjust, confirm live behavior or official examples. If not confirmed, prefer validation plus actionable error message over silent adjustment.

### Acceptance Criteria

- Monthly `YYYY-MM` still emits last second of the target month for `toDate`.
- Weekly path has either:
  - validated input with clear error, or
  - confirmed auto-adjust behavior with tests.
- Error message tells users how to fix invalid `to_date`.
- Docs mention the monthly/weekly provider constraint.

### Risk

Medium. The week boundary can be locale-sensitive. Avoid overcommitting until live behavior is confirmed.

## Priority 1: Clarify `wordstat.user_info`

### Problem

The old Wordstat API had a user/info style mental model. Search API Wordstat exposes four methods:

- `GetTop`
- `GetDynamics`
- `GetRegionsDistribution`
- `GetRegionsTree`

Current `wordstat.user_info` returns a local config summary with `available: true` when credentials are present. It does not verify that:

- the API key is valid,
- the service account has the required role,
- the API key has the right scope,
- the folder ID matches the service account.

This can create false confidence.

### Options

Option A - Keep name, change behavior:

- Make `wordstat.user_info` perform a lightweight live check.
- Candidate check: `getRegionsTree` with cache.
- Return `available=true` only after provider success.

Option B - Keep behavior, rename meaning in docs:

- Document it as "local Wordstat config summary".
- Return `available=false` when env is missing, but avoid claiming provider access.

Option C - Add a new health tool:

- Keep `wordstat.user_info` backward-compatible.
- Add `wordstat.health_check` or `wordstat.check_access`.

Recommended for next release: **Option A** if live access is acceptable, otherwise **Option B**. Do not add a new public tool unless the tool-list policy explicitly approves it.

### Acceptance Criteria

- User-facing docs no longer imply Search API has a real `userInfo` endpoint.
- If `available=true`, it means either:
  - provider access was verified, or
  - the field is renamed to `configured=true`.
- Missing-role and invalid-key failures produce actionable hints.

### Risk

Low to medium. Changing `wordstat.user_info` behavior could add one provider call. Use cache to keep it cheap.

## Priority 1: Document Role and Scope Requirements

### Problem

The official AI Studio Wordstat documentation states that the service account needs the `search-api.webSearch.user` role. Existing project docs mention env vars but do not consistently mention the role/scope requirements for Wordstat. The Web Search note already mentions:

- `search-api.webSearch.user`
- `yc.search-api.execute` scope for API keys

This should also be visible in Wordstat setup docs.

### Recommendation

Update:

- `README.md`
- `.env.example`
- `docs/quickstart.md`
- `docs/public-mode.md`
- `docs/llm-usage-guide-2026-02-03.md`
- Russian equivalents in `docs/ru/`

Add a short checklist:

```text
Wordstat via Yandex Search API:
- service account belongs to the target folder
- service account has search-api.webSearch.user
- API key is created for that service account
- API key includes yc.search-api.execute, if scopes are configured
- YANDEX_SEARCH_API_FOLDER_ID matches the folder
```

### Acceptance Criteria

- A new operator can configure Wordstat without reading the Habr article.
- Missing role/scope symptoms are documented under troubleshooting.
- Docs explain that Direct OAuth is not used for Search API Wordstat.

### Risk

Low.

## Priority 2: Improve Raw/HF Field Compatibility

### Problem

The new Search API JSON uses lower camelCase after protobuf JSON conversion:

- `totalCount`
- `numPhrases`
- `folderId`
- `fromDate`
- `toDate`
- `affinityIndex`

The internal code supports some historical names (`topRequests`) and new names (`results`). This compatibility is useful, but it should be intentional and tested.

### Recommendation

Standardize an internal helper for top response extraction:

```text
results = response.results or response.topRequests or []
associations = response.associations or []
```

Use it consistently in:

- `hf_wordstat.py`
- dashboard Wordstat block
- any future PRO dataset/export code

Also document that raw tools return provider-shaped JSON, while HF tools return normalized agent-friendly shapes.

### Acceptance Criteria

- One helper owns extraction of `results` / `topRequests` / `associations`.
- Tests cover old-shaped and new-shaped mock responses.
- HF output schema is stable and documented.

### Risk

Low.

## Priority 2: Add Provider Limit Documentation

### Problem

The Search API Wordstat surface is not the web Wordstat UI. Important limitations:

- Operators such as `!word`, `+word`, and `[phrase]` do not provide full web-Wordstat exact semantics.
- Multi-phrase comparison is not a native single API call.
- `count` fields are serialized as strings in raw responses because protobuf `int64` becomes JSON string.
- `associations` can be empty or missing.
- Region names require `getRegionsTree` mapping.

Some of this is implicitly handled in code, but not clearly documented for agents and operators.

### Recommendation

Add a "Provider limitations" section to Wordstat docs and LLM guide.

For dashboard/HF seed handling:

- Keep cleaning Direct keyword syntax for dashboard seeds.
- Consider similar optional cleaning in HF suggestions, but do not alter raw `wordstat.top_requests`.

### Acceptance Criteria

- LLM usage guide tells agents when to use raw vs HF Wordstat.
- Docs tell users not to expect exact web-Wordstat operator behavior.
- Dashboard docs explain that Direct keyword operators are stripped before Wordstat expansion.

### Risk

Low.

## Priority 2: Better Error Hints for Search API Wordstat

### Problem

Current error normalization handles HTTP status and gives generic token/rate-limit hints. Search API setup has common specific failures:

- missing `folderId`,
- service account folder mismatch,
- API key missing role/scope,
- invalid enum value,
- monthly/weekly `toDate` boundary error.

### Recommendation

Enhance `WordstatError` normalization by parsing a small amount of response body when safe:

- Keep secrets masked.
- Include provider message for 400 errors.
- Add specific hints for:
  - `folderId`
  - `PERIOD_`
  - `last day of the month`
  - `last day of the week`
  - permission/role failures

### Acceptance Criteria

- Invalid `period="monthly"` without enum normalization remains fixed by current normalizer.
- If provider returns monthly boundary error, MCP error suggests using `YYYY-MM` or the last day of month.
- If permission is denied, MCP error suggests `search-api.webSearch.user`.

### Risk

Low. Avoid logging secrets or full request bodies.

## Priority 3: Optional SEO/Content HF Convenience

### Opportunity

The Habr article frames a content workflow:

- test a draft H1,
- compare `results` and `associations`,
- reject topics below a frequency threshold,
- rewrite headings toward higher-demand formulations.

This is adjacent to current advertising workflows and could be useful to `Marketing2025`.

### Options

Option A - Add no new tools:

- Improve `wordstat.hf.suggest_keywords` and document prompts.

Option B - Add a new HF tool:

- `wordstat.hf.evaluate_phrase`
- Input: `phrase`, `regions`, `devices`, `min_total_count`
- Output: `total_count`, top result, top association, recommendation.

Option C - Add this only as a prompt/runbook:

- No MCP surface expansion.
- Add examples to `examples/claude-code-prompts.md` or LLM guide.

Recommended for next release: **Option C**. It gives value without expanding the approved tool list. Reconsider Option B later if repeated use proves it is worth a contract addition.

## Testing Plan

Unit tests:

- `WordstatClient._payload`:
  - `folderId` injection
  - region int to string conversion
  - device aliases
  - period aliases
- `wordstat.regions` builder:
  - `regions` -> `REGION_REGIONS`
  - `cities` -> `REGION_CITIES`
  - `all` -> `REGION_ALL`
  - raw `params` passthrough
- `wordstat.dynamics` builder:
  - `YYYY-MM` monthly handling
  - date passthrough
  - weekly validation/adjustment behavior
- HF suggestions:
  - results only
  - associations only
  - both
  - duplicate phrase across lists
  - empty associations
- Dashboard Wordstat block:
  - includes association candidates
  - preserves warnings when Wordstat fails

Live smoke tests, manual or gated:

- `wordstat.top_requests` with one phrase.
- `wordstat.get_regions_tree`.
- `wordstat.regions` with `region_type=regions`.
- `wordstat.dynamics` monthly with `YYYY-MM` bounds.
- One invalid-credentials check, if safe in a non-production environment.

Do not add live Search API calls to CI by default.

## Documentation Plan

Update English:

- `README.md`
- `.env.example`
- `docs/quickstart.md`
- `docs/public-mode.md`
- `docs/llm-usage-guide-2026-02-03.md`
- release note under `docs/releases/` when version is chosen

Update Russian:

- `docs/ru/quickstart.md`
- `docs/ru/public-mode.md`
- `docs/ru/llm-usage-guide-2026-02-03.md`
- relevant release note if mirrored

Add examples:

```json
{
  "phrase": "chat bot for business",
  "regions": [213],
  "devices": ["desktop"],
  "num_phrases": 20
}
```

```json
{
  "phrase": "chat bot for business",
  "period": "monthly",
  "from_date": "2026-01",
  "to_date": "2026-03"
}
```

```json
{
  "phrase": "chat bot for business",
  "region_type": "regions"
}
```

## Community Article Opportunity

The project can credibly contribute a follow-up article or post because it has a production-oriented implementation beyond the minimal wrapper:

- MCP tool design for Search API Wordstat.
- Safe public read-only contract.
- Why Direct OAuth and Search API credentials must be separate.
- `folderId`, service account role, and API key scope checklist.
- Provider enum normalization.
- `associations` as a first-class semantic signal.
- Rate limiting and retry strategy.
- Region tree caching.
- Dashboard and agent workflows.

Suggested angle:

> "From Wordstat wrapper to MCP tool: production lessons from Yandex Search API Wordstat"

Do not frame it as a correction of the Habr article. The article is useful and practical. Position the project post as the next layer: operating this API safely inside an agent-facing analytics server.

## Proposed Release Checklist

Before tagging the next release:

1. Implement P0 fixes.
2. Add tests for changed Wordstat payload behavior.
3. Run `pytest -q`.
4. Run one live smoke test with Search API credentials outside CI.
5. Update README and LLM usage docs.
6. Update Russian docs where public setup instructions changed.
7. Update `CHANGELOG.md`.
8. If releasing publicly, mention that Search API Wordstat requires `YANDEX_SEARCH_API_FOLDER_ID` plus API key/IAM token and the `search-api.webSearch.user` role.

## Recommended Task Breakdown

Task 1: Regions payload fix

- Scope: `server.py`, tests, docs.
- Risk: low.
- Release priority: must-have.

Task 2: Associations in HF and dashboard

- Scope: `hf_wordstat.py`, dashboard Wordstat block, tests.
- Risk: medium-low.
- Release priority: must-have.

Task 3: Dynamics date hardening

- Scope: `server.py`, docs, tests, optional live validation.
- Risk: medium.
- Release priority: should-have.

Task 4: User info semantics

- Scope: `server.py`, docs, tests.
- Risk: low/medium depending on whether live check is added.
- Release priority: should-have.

Task 5: Documentation refresh

- Scope: README, public-mode, quickstart, LLM guide, Russian mirrors.
- Risk: low.
- Release priority: must-have if any behavior changes.

Task 6: Community write-up draft

- Scope: `docs/` or external article draft.
- Risk: low.
- Release priority: optional, after code lands.

