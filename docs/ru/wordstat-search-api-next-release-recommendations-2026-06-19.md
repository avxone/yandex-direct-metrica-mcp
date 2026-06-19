# Рекомендации по доработке Wordstat Search API для следующего релиза - 2026-06-19

## Назначение

Документ переводит обзор новой поверхности Yandex Search API Wordstat в конкретный план доработок для следующего релиза `yandex-direct-metrica-mcp`.

Источники:
- Habr: "Wordstat API в Yandex Cloud Search API: разбор endpoints, подводные камни, минимальный Python wrapper (2026)" - https://habr.com/ru/articles/1030276/
- Документация AI Studio, Wordstat - https://aistudio.yandex.ru/docs/en/search-api/concepts/wordstat.html
- Proto-спецификация Yandex Cloud - https://github.com/yandex-cloud/cloudapi/blob/master/yandex/cloud/searchapi/v2/wordstat_service.proto
- Текущая реализация проекта: `src/mcp_yandex_ad/wordstat_client.py`, `src/mcp_yandex_ad/server.py`, `src/mcp_yandex_ad/hf_wordstat.py`, документация Wordstat.

Короткий вывод: проект уже перешел на правильное поколение API. Следующий релиз должен быть не "миграцией с нуля", а релизом hardening: исправить несколько полей, лучше использовать новые данные ответа и снизить количество операторских ошибок.

## Текущее состояние

Основная миграция уже сделана:

- Runtime-вызовы идут в `https://searchapi.api.cloud.yandex.net/v2/wordstat/`.
- Search API credentials читаются из:
  - `YANDEX_SEARCH_API_FOLDER_ID`
  - `YANDEX_SEARCH_API_API_KEY`
  - опционально `YANDEX_SEARCH_API_IAM_TOKEN`
  - опционально `YANDEX_SEARCH_API_WORDSTAT_BASE_URL`
- `folderId` добавляется автоматически.
- `regions` приводятся к строкам для provider API.
- `devices` нормализуются в enum-значения `DEVICE_*`.
- `period` нормализуется в enum-значения `PERIOD_*`.
- `getRegionsTree` кешируется.
- Множественные фразы для `topRequests` обрабатываются циклом по одной фразе, потому что новый Search API принимает одну `phrase` на запрос.
- Public mode остается safe-by-default: Wordstat для MCP-пользователя read-only, а Direct writes не входят в public-контракт.

Это уже сильнее минимального wrapper из статьи: в проекте есть guardrails, retries, rate limits, public/pro contract, dashboard integration и HF-слой.

## Рекомендация по релизу

Рекомендуемый scope следующего релиза: **v2.0.12 Wordstat Search API hardening**.

Основная цель:

Сделать работу с Wordstat Search API достаточно надежной, чтобы downstream-агенты могли пользоваться Wordstat без знания quirks провайдера.

Что включить:

1. Исправить mapping payload для `wordstat.regions`.
2. Использовать `associations` в HF keyword suggestions и Wordstat-блоках dashboard.
3. Усилить обработку дат в `wordstat.dynamics`.
4. Уточнить семантику `wordstat.user_info`.
5. Обновить README, `.env.example`, LLM usage docs и release notes: роли, scopes, ограничения provider API.
6. Добавить focused tests на provider-specific quirks.

Что не включать:

- Не добавлять Direct write/apply поведение в public mode.
- Не добавлять широкий `wordstat.raw_call` в public mode.
- Не тащить тяжелый SDK только ради Wordstat.
- Не отключать TLS verification как workaround для macOS.

## Priority 0: исправить payload `wordstat.regions`

### Проблема

В proto Yandex Search API `GetRegionsDistributionRequest.region` описан как enum:

- `REGION_ALL`
- `REGION_CITIES`
- `REGION_REGIONS`

В статье на Habr пример тоже отправляет:

```json
{
  "phrase": "чат бот для бизнеса",
  "region": "REGION_REGIONS",
  "folderId": "..."
}
```

Текущий код строит:

```python
payload["regionType"] = str(region_type).strip()
```

Это похоже на legacy/design-time naming, а не на JSON-поле Search API v2. Из-за этого `wordstat.regions` может падать или игнорировать выбранный тип распределения.

### Рекомендация

Изменить builder так, чтобы он отправлял `region`, а не `regionType`.

Добавить нормализатор:

```text
all -> REGION_ALL
cities -> REGION_CITIES
regions -> REGION_REGIONS
REGION_ALL -> REGION_ALL
REGION_CITIES -> REGION_CITIES
REGION_REGIONS -> REGION_REGIONS
```

`params` raw override оставить без изменений для advanced users.

### Acceptance Criteria

- `wordstat.regions` с `region_type="regions"` отправляет `{"region": "REGION_REGIONS"}`.
- `wordstat.regions` с `region_type="cities"` отправляет `{"region": "REGION_CITIES"}`.
- `wordstat.regions` без `region_type` не отправляет `region` и оставляет default API.
- Тесты покрывают aliases.
- Tool schema description явно описывает mapping в `REGION_*`.

### Риск

Низкий. Это correctness fix для вероятного mismatch с provider field.

## Priority 0: сделать `associations` полноценным источником keyword candidates

### Проблема

Новый ответ `topRequests` содержит два полезных списка:

- `results`: популярные запросы, содержащие фразу/слова.
- `associations`: семантически похожие запросы.

Текущие HF и dashboard paths агрегируют только `topRequests` / `results`. Самый ценный практический вывод из статьи: `associations` часто содержит лучшую формулировку, spelling variant или более широкий head term. Игнорирование этого поля снижает качество рекомендаций.

Текущее поведение:

- `wordstat.hf.suggest_keywords` читает `topRequests` или `results`.
- Dashboard Wordstat block читает `topRequests` или `results`.
- Raw `wordstat.top_requests` уже возвращает provider response, поэтому raw-пользователь может увидеть `associations`; HF/dashboard от этого пока не выигрывают.

### Рекомендация

Включить оба списка в HF aggregation:

```text
candidate source = results + associations
```

Сохранять metadata источника:

```json
{
  "phrase": "чатбот",
  "score": 7371,
  "sources": ["чат бот для бизнеса"],
  "provider_sources": ["association"]
}
```

Если phrase встретилась в обоих списках:

```json
"provider_sources": ["result", "association"]
```

Возможные варианты scoring:

- Option A: одинаковый вес для `results` и `associations`.
- Option B: умножать `associations` на `association_weight`, default `1.0`.
- Option C: оставлять raw counts как score и просто показывать source type.

Рекомендация для ближайшего релиза: **Option C**. Это проще объяснить и не создает искусственную ranking model.

### Рекомендация для dashboard

Для `dashboard.generate_option1` / PRO HTML Wordstat block:

- Объединить `results` и `associations`.
- Сохранить source type в hidden/raw JSON.
- В UI rows по возможности добавить короткую метку:
  - `result`
  - `association`
  - `both`
- Если UI не входит в scope релиза, минимум включить associations в scoring и вернуть их в JSON.

### Acceptance Criteria

- HF suggestions включают candidates из `associations`.
- Candidate metadata показывает, пришел candidate из `results`, `associations` или обоих списков.
- Dashboard Wordstat candidates могут включать associations.
- Тесты покрывают:
  - response только с `results`
  - response только с `associations`
  - duplicate phrase в обоих списках
  - missing/empty `associations`

### Риск

Средне-низкий. Это изменит ranking output. Изменение additive и повышает качество, но snapshots/downstream expectations могут потребовать обновления.

## Priority 1: усилить обработку дат в `wordstat.dynamics`

### Проблема

Search API `dynamics` требует:

- `period`: `PERIOD_MONTHLY`, `PERIOD_WEEKLY`, `PERIOD_DAILY`.
- `fromDate`: RFC3339 timestamp.
- `toDate`: RFC3339 timestamp.

У провайдера есть неочевидная validation rule:

- для monthly `toDate` должен быть последним днем месяца;
- для weekly `toDate` должен быть последним днем недели.

Текущий код хорошо обрабатывает `YYYY-MM` как начало/конец месяца для monthly usage, но не обрабатывает явно weekly period boundaries. Если пользователь передаст обычный `YYYY-MM-DD`, `_wordstat_date_time(..., end=True)` сейчас вернет `YYYY-MM-DDT00:00:00Z`, а не конец дня/недели.

### Рекомендация

Добавить period-aware normalization:

```text
period=monthly:
  YYYY-MM -> first day / last day of month
  YYYY-MM-DD to_date -> validate last day of month or adjust only with explicit auto_adjust

period=weekly:
  YYYY-MM-DD to_date -> adjust/validate to week end

period=daily:
  YYYY-MM-DD to_date -> same day timestamp is acceptable
```

Рекомендуемый путь:

1. Сохранить текущую простую monthly-логику для `YYYY-MM`.
2. Для `period=weekly` добавить helper, который валидирует или приводит `to_date` к последнему дню недели.
3. Для explicit `params` raw override ничего не менять.
4. В docs описать трансформацию и ограничение провайдера.

Открытое решение: что именно является "последним днем недели" для Yandex Search API.

Статья говорит "последний день недели", но не определяет locale. До auto-adjust лучше подтвердить live behavior или найти официальный пример. Если подтверждения нет, предпочтительнее validation + actionable error, а не silent adjustment.

### Acceptance Criteria

- Monthly `YYYY-MM` по-прежнему отправляет последний момент месяца для `toDate`.
- Weekly path имеет либо:
  - validated input с понятной ошибкой, либо
  - подтвержденное auto-adjust behavior с тестами.
- Error message объясняет, как исправить invalid `to_date`.
- Docs упоминают monthly/weekly provider constraint.

### Риск

Средний. Week boundary может зависеть от locale. Не стоит молча менять даты без подтверждения.

## Priority 1: уточнить семантику `wordstat.user_info`

### Проблема

Старая mental model Wordstat API предполагала user/info. В Search API Wordstat есть четыре метода:

- `GetTop`
- `GetDynamics`
- `GetRegionsDistribution`
- `GetRegionsTree`

Текущий `wordstat.user_info` возвращает local config summary с `available: true`, если credentials есть. Он не проверяет:

- валиден ли API key;
- есть ли у service account нужная роль;
- есть ли у API key нужный scope;
- совпадает ли folder ID с service account.

Это может создавать ложную уверенность.

### Варианты

Option A - оставить имя, изменить поведение:

- `wordstat.user_info` делает lightweight live check.
- Кандидат: `getRegionsTree` с кешем.
- `available=true` возвращается только после успешного provider call.

Option B - оставить поведение, переименовать смысл в docs:

- Документировать как "local Wordstat config summary".
- Возвращать `available=false`, если env отсутствует, но не утверждать provider access.

Option C - добавить новый health tool:

- Сохранить backward compatibility `wordstat.user_info`.
- Добавить `wordstat.health_check` или `wordstat.check_access`.

Рекомендация для следующего релиза: **Option A**, если live access допустим; иначе **Option B**. Не добавлять новый public tool без явного approval tool-list policy.

### Acceptance Criteria

- User-facing docs больше не подразумевают, что в Search API есть настоящий `userInfo` endpoint.
- Если `available=true`, это значит либо:
  - provider access был проверен, либо
  - поле переименовано в `configured=true`.
- Missing-role и invalid-key failures дают actionable hints.

### Риск

Низкий/средний. Изменение behavior может добавить один provider call. Кешировать, чтобы вызов был дешевым.

## Priority 1: документировать роли и scopes Search API

### Проблема

Официальная документация AI Studio Wordstat говорит, что service account нужна роль `search-api.webSearch.user`. В текущих docs проекта env vars описаны, но требования к role/scope для Wordstat указаны не везде. В Web Search note уже есть:

- `search-api.webSearch.user`
- `yc.search-api.execute` для API key scopes

Это должно быть видно и в Wordstat setup.

### Рекомендация

Обновить:

- `README.md`
- `.env.example`
- `docs/quickstart.md`
- `docs/public-mode.md`
- `docs/llm-usage-guide-2026-02-03.md`
- русские версии в `docs/ru/`

Добавить короткий checklist:

```text
Wordstat via Yandex Search API:
- service account находится в целевом folder
- service account имеет search-api.webSearch.user
- API key создан для этого service account
- API key включает yc.search-api.execute, если scopes настроены
- YANDEX_SEARCH_API_FOLDER_ID совпадает с folder
```

### Acceptance Criteria

- Новый оператор может настроить Wordstat без чтения статьи на Habr.
- Missing role/scope symptoms описаны в troubleshooting.
- Docs объясняют, что Direct OAuth не используется для Search API Wordstat.

### Риск

Низкий.

## Priority 2: улучшить совместимость raw/HF полей

### Проблема

Новый Search API JSON использует lower camelCase после protobuf JSON conversion:

- `totalCount`
- `numPhrases`
- `folderId`
- `fromDate`
- `toDate`
- `affinityIndex`

Код поддерживает часть исторических имен (`topRequests`) и новых (`results`). Это полезно, но должно быть intentional и покрыто тестами.

### Рекомендация

Стандартизировать internal helper для извлечения top response:

```text
results = response.results or response.topRequests or []
associations = response.associations or []
```

Использовать его в:

- `hf_wordstat.py`
- dashboard Wordstat block
- будущих PRO dataset/export paths

Также документировать: raw tools возвращают provider-shaped JSON, HF tools возвращают normalized agent-friendly shapes.

### Acceptance Criteria

- Один helper отвечает за extraction `results` / `topRequests` / `associations`.
- Тесты покрывают old-shaped и new-shaped mock responses.
- HF output schema стабилен и описан.

### Риск

Низкий.

## Priority 2: описать ограничения provider API

### Проблема

Search API Wordstat не равен web Wordstat UI. Важные ограничения:

- Операторы `!word`, `+word`, `[phrase]` не дают full web-Wordstat exact semantics.
- Multi-phrase comparison не является native single API call.
- `count` в raw responses сериализуется строкой, потому что protobuf `int64` в JSON становится string.
- `associations` может быть пустым или отсутствовать.
- Для названий регионов нужен mapping через `getRegionsTree`.

Часть этого уже неявно обработана в коде, но не описана достаточно ясно для agents/operators.

### Рекомендация

Добавить section "Provider limitations" в Wordstat docs и LLM guide.

Для dashboard/HF seed handling:

- Сохранить cleaning Direct keyword syntax для dashboard seeds.
- Рассмотреть такой же optional cleaning в HF suggestions, но не менять raw `wordstat.top_requests`.

### Acceptance Criteria

- LLM usage guide объясняет, когда использовать raw vs HF Wordstat.
- Docs предупреждают, что exact web-Wordstat operator behavior ожидать нельзя.
- Dashboard docs объясняют, что Direct keyword operators очищаются перед Wordstat expansion.

### Риск

Низкий.

## Priority 2: улучшить error hints для Search API Wordstat

### Проблема

Текущая error normalization обрабатывает HTTP status и дает generic token/rate-limit hints. Для Search API setup есть частые специфические failures:

- missing `folderId`;
- folder mismatch service account;
- API key без role/scope;
- invalid enum value;
- monthly/weekly `toDate` boundary error.

### Рекомендация

Улучшить normalization `WordstatError`, аккуратно читая response body:

- Не выводить secrets.
- Для 400 errors включать provider message.
- Добавить специфические hints для:
  - `folderId`
  - `PERIOD_`
  - `last day of the month`
  - `last day of the week`
  - permission/role failures

### Acceptance Criteria

- Invalid `period="monthly"` уже исправляется нормализатором enum.
- Если provider вернул monthly boundary error, MCP error предлагает использовать `YYYY-MM` или последний день месяца.
- Если permission denied, MCP error предлагает проверить `search-api.webSearch.user`.

### Риск

Низкий. Главное - не логировать secrets и full request bodies.

## Priority 3: optional SEO/content HF convenience

### Возможность

Статья описывает content workflow:

- проверить черновой H1;
- сравнить `results` и `associations`;
- отбраковать темы ниже порога частотности;
- переписать heading в сторону более популярной формулировки.

Это рядом с текущими advertising workflows и может быть полезно для `Marketing2025`.

### Варианты

Option A - не добавлять новые tools:

- Улучшить `wordstat.hf.suggest_keywords` и добавить prompts/docs.

Option B - добавить новый HF tool:

- `wordstat.hf.evaluate_phrase`
- Input: `phrase`, `regions`, `devices`, `min_total_count`
- Output: `total_count`, top result, top association, recommendation.

Option C - добавить только prompt/runbook:

- Без расширения MCP surface.
- Добавить examples в `examples/claude-code-prompts.md` или LLM guide.

Рекомендация для следующего релиза: **Option C**. Это дает пользу без расширения approved tool list. Option B стоит вернуться позже, если сценарий будет повторяться.

## План тестирования

Unit tests:

- `WordstatClient._payload`:
  - injection `folderId`
  - conversion region int -> string
  - device aliases
  - period aliases
- `wordstat.regions` builder:
  - `regions` -> `REGION_REGIONS`
  - `cities` -> `REGION_CITIES`
  - `all` -> `REGION_ALL`
  - raw `params` passthrough
- `wordstat.dynamics` builder:
  - monthly `YYYY-MM`
  - date passthrough
  - weekly validation/adjustment behavior
- HF suggestions:
  - only `results`
  - only `associations`
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
- One invalid-credentials check, if safe in non-production environment.

Не добавлять live Search API calls в CI по умолчанию.

## План документации

Обновить English:

- `README.md`
- `.env.example`
- `docs/quickstart.md`
- `docs/public-mode.md`
- `docs/llm-usage-guide-2026-02-03.md`
- release note в `docs/releases/`, когда будет выбран version

Обновить Russian:

- `docs/ru/quickstart.md`
- `docs/ru/public-mode.md`
- `docs/ru/llm-usage-guide-2026-02-03.md`
- release note mirror, если он ведется

Добавить примеры:

```json
{
  "phrase": "чат бот для бизнеса",
  "regions": [213],
  "devices": ["desktop"],
  "num_phrases": 20
}
```

```json
{
  "phrase": "чат бот для бизнеса",
  "period": "monthly",
  "from_date": "2026-01",
  "to_date": "2026-03"
}
```

```json
{
  "phrase": "чат бот для бизнеса",
  "region_type": "regions"
}
```

## Возможность поделиться с сообществом

Проект может написать полезный follow-up article/post, потому что здесь уже не минимальный wrapper, а production-oriented implementation:

- MCP tool design для Search API Wordstat.
- Safe public read-only contract.
- Почему Direct OAuth и Search API credentials должны быть раздельными.
- Checklist: `folderId`, service account role, API key scope.
- Provider enum normalization.
- `associations` как first-class semantic signal.
- Rate limiting и retry strategy.
- Region tree caching.
- Dashboard и agent workflows.

Возможный angle:

> "От Wordstat wrapper к MCP tool: production lessons по Yandex Search API Wordstat"

Не стоит позиционировать это как "исправление" статьи на Habr. Статья полезная и практичная. Наш материал лучше подавать как следующий слой: как безопасно эксплуатировать этот API внутри agent-facing analytics server.

## Proposed Release Checklist

Перед tag следующего релиза:

1. Реализовать P0 fixes.
2. Добавить tests для измененного Wordstat payload behavior.
3. Запустить `pytest -q`.
4. Сделать live smoke test с Search API credentials вне CI.
5. Обновить README и LLM usage docs.
6. Обновить Russian docs, если менялись public setup instructions.
7. Обновить `CHANGELOG.md`.
8. В public release notes явно указать: Search API Wordstat требует `YANDEX_SEARCH_API_FOLDER_ID`, API key/IAM token и роль `search-api.webSearch.user`.

## Рекомендуемая разбивка задач

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
- Release priority: must-have if behavior changes.

Task 6: Community write-up draft

- Scope: `docs/` or external article draft.
- Risk: low.
- Release priority: optional, after code lands.

