# Черновик issue: hardening интеграции Wordstat Search API для следующего релиза

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

Проект уже мигрировал runtime-вызовы Wordstat со старого legacy Wordstat API на Yandex Search API Wordstat:

- base URL: `https://searchapi.api.cloud.yandex.net/v2/wordstat/`
- credentials:
  - `YANDEX_SEARCH_API_FOLDER_ID`
  - `YANDEX_SEARCH_API_API_KEY` или `YANDEX_SEARCH_API_IAM_TOKEN`
- текущий client: `src/mcp_yandex_ad/wordstat_client.py`
- текущие handlers/builders: `src/mcp_yandex_ad/server.py`
- текущий HF layer: `src/mcp_yandex_ad/hf_wordstat.py`

Миграция сделана в правильном направлении и уже сильнее минимального wrapper: есть MCP guardrails, public/pro separation, retries, rate limiting, cache support, HF tools и dashboard integration.

Но follow-up review по источникам:

- Habr article: https://habr.com/ru/articles/1030276/
- AI Studio Wordstat docs: https://aistudio.yandex.ru/docs/en/search-api/concepts/wordstat.html
- Yandex Cloud proto spec: https://github.com/yandex-cloud/cloudapi/blob/master/yandex/cloud/searchapi/v2/wordstat_service.proto

нашел несколько hardening-задач, которые желательно закрыть до следующего релиза.

Подробный planning document:

- `docs/wordstat-search-api-next-release-recommendations-2026-06-19.md`
- `docs/ru/wordstat-search-api-next-release-recommendations-2026-06-19.md`

## Goal

Сделать поддержку Wordstat Search API достаточно надежной, чтобы downstream agents и dashboard workflows могли использовать Wordstat без знания provider-specific quirks.

Следующий релиз должен убрать известные API-shape mismatches, повысить качество семантических рекомендаций за счет `associations` и явно задокументировать требования к Yandex Search API credentials.

## Non-Goals

- Не добавлять Direct write/apply behavior в public mode.
- Не добавлять широкий public `wordstat.raw_call` escape hatch.
- Не подключать тяжелый Yandex SDK только ради Wordstat.
- Не отключать TLS verification как workaround.
- Не добавлять live Search API calls в default CI.

## Scope

### 1. Исправить payload mapping для `wordstat.regions`

Текущая проблема:

`_build_wordstat_regions_payload()` отправляет:

```python
payload["regionType"] = str(region_type).strip()
```

Yandex Search API v2 ожидает поле `region` со значениями:

- `REGION_ALL`
- `REGION_CITIES`
- `REGION_REGIONS`

Нужно реализовать normalization:

```text
all -> REGION_ALL
cities -> REGION_CITIES
regions -> REGION_REGIONS
REGION_ALL -> REGION_ALL
REGION_CITIES -> REGION_CITIES
REGION_REGIONS -> REGION_REGIONS
```

Raw override через `params` оставить без изменений.

Acceptance criteria:

- `wordstat.regions` с `region_type="regions"` отправляет `{"region": "REGION_REGIONS"}`.
- `wordstat.regions` с `region_type="cities"` отправляет `{"region": "REGION_CITIES"}`.
- `wordstat.regions` с `region_type="all"` отправляет `{"region": "REGION_ALL"}`.
- `wordstat.regions` без `region_type` не отправляет `region`.
- Тесты покрывают aliases и raw `params` passthrough.
- Tool schema/docs упоминают mapping в `REGION_*`.

### 2. Использовать `associations` в HF keyword suggestions

Текущая проблема:

`wordstat.hf.suggest_keywords` читает только `topRequests` / `results`.

Search API `topRequests` возвращает:

- `results`: популярные запросы, содержащие phrase/words.
- `associations`: семантически связанные запросы.

`associations` часто содержит лучший keyword candidate, spelling variant или более широкий head term. Игнорировать это поле - терять качество рекомендаций.

Нужно:

- Извлекать и `results`, и `associations`.
- Агрегировать candidates из обоих списков.
- Сохранять source metadata в HF output.

Рекомендуемая форма candidate:

```json
{
  "phrase": "чатбот",
  "score": 7371,
  "sources": ["чат бот для бизнеса"],
  "provider_sources": ["association"]
}
```

Если phrase есть в обоих списках:

```json
"provider_sources": ["result", "association"]
```

Для этого релиза использовать raw provider counts как score. Не вводить weighting model.

Acceptance criteria:

- HF suggestions включают candidates из `associations`.
- Output различает `result`, `association` и `both`.
- Duplicate phrases из двух списков объединяются.
- Empty/missing `associations` не ломает вызов.
- Cursor/resumable behavior остается intact.

### 3. Использовать `associations` в dashboard Wordstat candidates

Текущая проблема:

Dashboard Wordstat block агрегирует только `topRequests` / `results`.

Нужно:

- Объединить `results` и `associations` при построении campaign-level Wordstat candidates.
- Сохранить source type в возвращаемом JSON.
- Если UI scope слишком большой, для этого релиза достаточно source type в raw JSON.

Acceptance criteria:

- Dashboard Wordstat block может показывать candidates из `associations`.
- Candidate JSON содержит source type metadata.
- Existing dashboard fallback/warning behavior не ломается.
- Tests покрывают response, где полезные candidates есть только в `associations`.

### 4. Усилить date handling в `wordstat.dynamics`

Текущая проблема:

Search API `dynamics` имеет provider constraints:

- `period` должен быть `PERIOD_MONTHLY`, `PERIOD_WEEKLY` или `PERIOD_DAILY`.
- monthly `toDate` должен быть последним днем месяца.
- weekly `toDate` должен быть последним днем недели.

Текущий код обрабатывает monthly `YYYY-MM`, но weekly boundaries явно не заданы. Plain `YYYY-MM-DD` `to_date` сейчас превращается в midnight этого дня, что может не пройти provider validation для weekly/monthly.

Нужно:

- Сохранить существующее monthly behavior для `YYYY-MM`.
- Добавить period-aware validation или normalization для `to_date`.
- Не менять raw `params` passthrough.
- Если week boundary не подтвержден, предпочесть понятную validation error вместо silent adjustment.

Open decision:

Нужно подтвердить, что Yandex Search API считает концом недели: Sunday, Monday или provider-specific boundary.

Acceptance criteria:

- Monthly `YYYY-MM` по-прежнему отправляет last-day-of-month `toDate`.
- Weekly path либо валидирует дату с actionable error, либо использует подтвержденное auto-adjust behavior.
- Error messages объясняют, как исправить invalid `to_date`.
- Tests покрывают monthly и weekly behavior.
- Docs упоминают monthly/weekly `toDate` constraint.

### 5. Уточнить семантику `wordstat.user_info`

Текущая проблема:

Search API Wordstat exposes только четыре метода:

- `GetTop`
- `GetDynamics`
- `GetRegionsDistribution`
- `GetRegionsTree`

Реального Search API `userInfo` endpoint нет. Текущий `wordstat.user_info` возвращает local config summary и может показать `available=true`, когда env vars есть, но provider access не проверен.

Выбрать один вариант:

Option A, preferred:

- Оставить tool name.
- Делать lightweight live access check, вероятно `getRegionsTree` с cache.
- Возвращать `available=true` только после provider success.

Option B:

- Оставить текущее поведение.
- Уточнить output semantics: `configured=true`, а не verified availability.
- Обновить docs: это local config summary.

Не добавлять новый public tool без approved tool-list policy.

Acceptance criteria:

- Docs больше не подразумевают, что в Search API есть native `userInfo` endpoint.
- `available=true` означает реально проверенный provider access, либо поле заменено/уточнено.
- Invalid key / missing role errors дают actionable hints.

### 6. Задокументировать Search API role/scope requirements

Текущая проблема:

Docs упоминают Search API env vars, но не везде явно описывают access requirements.

Добавить setup guidance:

```text
Wordstat via Yandex Search API:
- service account belongs to the target folder
- service account has search-api.webSearch.user
- API key is created for that service account
- API key includes yc.search-api.execute if API key scopes are configured
- YANDEX_SEARCH_API_FOLDER_ID matches the folder
```

Обновить:

- `README.md`
- `.env.example`
- `docs/quickstart.md`
- `docs/public-mode.md`
- `docs/llm-usage-guide-2026-02-03.md`
- Russian equivalents in `docs/ru/`

Acceptance criteria:

- Новый оператор может настроить Wordstat без чтения статьи на Habr.
- Docs явно говорят, что Direct OAuth не используется для Search API Wordstat.
- Troubleshooting покрывает missing role/scope symptoms.

### 7. Задокументировать provider limitations

Добавить section provider limitations:

- Web Wordstat operators `!word`, `+word`, `[phrase]` не дают full exact-match web UI semantics в Search API.
- Multi-phrase comparison не native; MCP делает loop phrase-by-phrase.
- Raw `count` fields могут приходить строками, потому что protobuf `int64` сериализуется в JSON как string.
- `associations` может быть пустым или отсутствовать.
- Названия регионов требуют mapping через `getRegionsTree`.

Acceptance criteria:

- LLM guide объясняет, когда использовать raw vs HF Wordstat.
- Dashboard docs объясняют cleaning Direct keyword syntax перед Wordstat expansion.
- Raw tools остаются provider-shaped; HF tools остаются normalized.

### 8. Улучшить error hints для common Search API failures

Текущая проблема:

Error normalization дает generic token/rate-limit hints. Для Search API Wordstat есть типовые setup/payload failures:

- missing `folderId`
- folder mismatch
- missing role/scope
- invalid enum
- monthly/weekly `toDate` boundary error

Нужно:

- Аккуратно parse provider response body для Wordstat errors.
- Не логировать secrets или full request bodies.
- Добавить targeted hints для:
  - `folderId`
  - `PERIOD_*`
  - "last day of the month"
  - "last day of the week"
  - permission/role failures

Acceptance criteria:

- Monthly boundary provider error предлагает использовать `YYYY-MM` или последний день месяца.
- Permission errors предлагают проверить `search-api.webSearch.user`.
- 429 и 5xx retry hints остаются без регрессий.

## Suggested Implementation Order

1. Добавить/обновить tests для Wordstat payload builders.
2. Исправить `wordstat.regions` mapping.
3. Добавить shared extraction helper для `results` / `topRequests` / `associations`.
4. Обновить `wordstat.hf.suggest_keywords`.
5. Обновить dashboard Wordstat candidate aggregation.
6. Усилить `wordstat.dynamics` date handling.
7. Уточнить `wordstat.user_info`.
8. Улучшить error hints.
9. Обновить docs.
10. Запустить tests и gated live smoke test.

## Test Plan

Run:

```bash
pytest -q
```

Добавить focused tests для:

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

Не добавлять live calls в default CI.

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

Начинать лучше с `wordstat.regions` и `associations`: это лучший risk/value ratio.

Единственная потенциально неоднозначная часть - weekly `toDate` для `wordstat.dynamics`. Если live behavior нельзя быстро подтвердить, лучше сделать validation и actionable errors, а не silent date adjustment.

Public mode должен остаться safe-by-default. Wordstat остается read-only с точки зрения MCP-пользователя, хотя provider-side report/stat computation происходит на стороне Yandex Search API.

