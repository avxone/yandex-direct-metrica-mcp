# Черновик issue: добавить `search_serp` в yandex.ad и подготовить handoff для Marketing2025

## Title

Add `search_serp` MCP tool and client handoff for Marketing2025 SERP migration

## Type

Feature / integration / documentation

## Release Required

yes

## Suggested Labels

- `symphony`
- `search-api`
- `web-search`
- `marketing2025`
- `feature`
- `release-required`
- `next-release`

## Ownership Boundary

Эта задача принадлежит репозиторию `yandex.ad`.

Разрешено:

- изменения MCP-сервера в этом repo;
- тесты, docs, tool contracts, release notes и handoff docs в этом repo;
- live validation, доказывающая, что сервер отдает нужные клиенту данные.

Не входит в эту задачу, если отдельно не согласовано:

- правки файлов в `Marketing2025/`;
- изменение клиентских prompt/script/workflow;
- непосредственное изменение клиентского artifact format.

Если клиенту нужна адаптация на своей стороне, задача должна завершаться явным handoff, где сказано, что именно надо поменять.

## Background

Сейчас `Marketing2025` использует SERP workflow через Playwright против живых Yandex result pages. Клиент уточнил, какая информация ему нужна от `yandex.ad`:

- organic results;
- ad results;
- число верхних рекламных слотов;
- ad titles/snippets;
- контроль региона и устройства;
- стабильная server-side нормализация;
- понятное описание совместимости с текущим workflow клиента.

Запрос клиента: сначала реализовать MCP-side capability, затем документировать, как клиент может ее использовать. MCP-задача не должна молча разрастаться в прямые правки клиентского repo.

## Goal

Реализовать ограниченный MCP-side `search_serp` в `yandex.ad`, проверить, что он отдает нужные клиенту данные, и подготовить handoff document для `Marketing2025`.

Первый релиз должен:

1. добавить один MCP contract вокруг `search_serp`;
2. доказать, что сервер отдает нужные клиенту данные;
3. сохранить совместимость там, где это возможно, и явно задокументировать несовместимости;
4. подготовить client handoff / release-note style document с шагами по внедрению.

## Decision Options

### Option A - нативный Search API HTML плюс parsing на стороне MCP

Использовать официальный Yandex Search API в режиме `html`, декодировать страницу и парсить рекламу и органику на стороне MCP.

Плюсы:

- first-party provider и существующий billing path;
- убирает CAPTCHA и browser scraping из server-side решения;
- держит parsing в одном детерминированном месте, а не в prompt space.

Минусы:

- HTML parsing остается точкой сопровождения;
- извлечение рекламы нужно валидировать на реальных запросах.

### Option B - только нативный Search API XML

Сделать только структурированную органику из XML.

Плюсы:

- минимальная реализация.

Минусы:

- не покрывает рекламу, число top ad slots и ad copy, которые нужны клиенту.

### Option C - сторонняя обертка со структурированной рекламой

Использовать внешний wrapper, который уже отдает структурированную рекламу.

Плюсы:

- меньше локального parsing.

Минусы:

- появляется third-party dependency и меняется trust/runtime model.

## Recommended Path

Для первой реализации использовать **Option A**.

## Proposed MCP Scope

Основной инструмент:

- `search_serp`

Опциональный supporting tool:

- `search_api.search_preflight`

Явно вне scope этой задачи:

- прямые правки `Marketing2025`;
- широкое расширение search toolkit вне конкретной клиентской потребности;
- cache infrastructure;
- сторонние search wrappers.

## Client Compatibility Target

Сейчас клиент ожидает данные, эквивалентные:

- ads: domain, title, snippet, position;
- top ad slot count;
- organic: domain, title, url, position;
- region-specific response;
- детерминированный server output для downstream aggregation.

Эта задача должна явно ответить:

1. какие из этих потребностей полностью покрыты `search_serp`;
2. какие покрыты частично;
3. какие требуют client-side adaptation;
4. отличается ли response format от текущего внутреннего shape клиента.

## Scope

### 1. Добавить `search_serp` в MCP

Добавить ограниченный MCP tool вокруг Yandex Search API с таким input shape:

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

Ожидаемый нормализованный output:

```json
{
  "query": "...",
  "region": 213,
  "device": "DEVICE_DESKTOP",
  "ads": [
    {"domain": "...", "title": "...", "snippet": "...", "position": 1}
  ],
  "ads_count_top": 3,
  "organic": [
    {"domain": "...", "title": "...", "url": "...", "position": 1}
  ],
  "captcha": false
}
```

Обязательные поведения:

- `region` как параметр с default из server config;
- `device` как параметр;
- поддержка `html` в первой реализации, потому что нужна реклама;
- нормализация рекламы и органики на стороне MCP;
- raw HTML опционален, не default;
- runtime payload и public output schema должны совпадать.

### 2. Держать parsing responsibility внутри MCP

Агент не должен парсить raw SERP HTML в prompt space.

Допустимые варианты:

- перенести/адаптировать существующую parsing logic в MCP;
- или сделать новый MCP-owned parser module и документировать fallback semantics.

### 3. Провалидировать data coverage для клиента

Эта задача должна проверить, что MCP result действительно содержит поля, которые нужны клиенту.

Обязательное сравнение:

- requested client fields;
- actual `search_serp` fields;
- compatibility notes;
- known gaps / caveats.

### 4. Написать client handoff

Добавить handoff doc в этом repo как adoption note для `Marketing2025`.

В нем должно быть:

- какой новый MCP tool вызывать;
- request/response examples;
- какие текущие ожидания клиента сохраняются;
- что отличается от текущего client path;
- что клиенту нужно поменять у себя;
- что может остаться fallback.

### 5. Обновить MCP docs и release notes

Обновить:

- MCP docs для `search_serp`;
- tool proposal / contract docs;
- changelog или release-facing notes;
- session note по работе.

## Non-goals

- не редактировать `Marketing2025` files в этой задаче;
- не менять молча клиентские обязанности;
- не добавлять writes;
- не публиковать release из feature issue;
- не добавлять unrelated search helpers.

## Acceptance Criteria

- MCP публикует ограниченный `search_serp` tool с нормализованной рекламой и органикой;
- public tool contract совпадает с runtime payload;
- задача содержит явные client compatibility notes;
- задача содержит client handoff document;
- docs явно описывают, какие данные доступны и что клиенту нужно адаптировать при необходимости;
- для завершения этой задачи не нужны direct edits в `Marketing2025`.

## Validation

Для implementation task обязательны:

- unit tests на request building и normalized parsing;
- local validation на 3–5 реальных project queries с ручной browser inspection для sanity-check ad extraction;
- compile/test pass в этом repo;
- docs review для MCP contract и client handoff;
- явная coverage table или эквивалентное обоснование, что нужная клиенту информация доступна.

## Release Notes Draft

```markdown
Search API: added `search_serp` to yandex.ad with normalized ads and organic results, plus a client handoff for Marketing2025 SERP migration.
```

## Definition of Done

- approved tool-list change documented if required;
- `search_serp` implemented in MCP;
- runtime payload и published output schema совпадают;
- real-query validation for data coverage passes;
- handoff doc для `Marketing2025` написан в этом repo;
- tests и MCP-side docs обновлены;
- task проходит через feature-issue Symphony pipeline, а затем через release publication, потому что клиенту нужен опубликованный образ для использования результата.

## Handoff Notes

Эта задача заканчивается server-side deliverable и client adoption guidance.

Если позже клиент захочет прямую миграцию prompt/script внутри `Marketing2025`, это нужно оформлять отдельной client-side задачей, которая будет использовать уже готовую серверную capability.
