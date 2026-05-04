# Предложение по совместной работе `Marketing2025` + `yandex.ad` — 2026-05-04

## Зачем нужен этот документ

Сейчас уже видно, что `Marketing2025` нельзя рассматривать как “ещё одного MCP-клиента”.

По weekly Analyst workflow и по pipeline runs для `Voicexpert` фактическая архитектура выглядит так:

- `yandex.ad` — это **backend capability layer**
- `Marketing2025` — это **workflow / orchestrator layer**
- LLM-клиенты (`Claude`, `Codex`, `Gemini` и т.д.) — это **взаимозаменяемые frontends**

Цель этого документа — зафиксировать понятную модель совместной работы, которую можно обсуждать с маркетингом и использовать как основу для совместного планирования.

## Целевая архитектура

### Ответственность `yandex.ad`

В `yandex.ad` должны жить:

- интеграция с API Yandex и MCP transport
- стабильные MCP tool contracts
- auth, retries, rate limits, write guards
- компактные domain read models
- небольшое число фиксированных high-ROI read workflows, если они реально уменьшают orchestration cost

В `yandex.ad` не должны жить:

- project-specific workflow policy
- pipeline orchestration
- backlog lifecycle
- управление run history и артефактами
- freeform planning logic внутри сервера

### Ответственность `Marketing2025`

В `Marketing2025` должны жить:

- project profiles и account bundles
- workflow execution (`snapshot -> research -> synthesize -> decide -> QA -> execute`)
- хранение артефактов и run history
- стабильные ids для runs, recommendations, evidence и approvals
- quality gates и workflow policy
- CLI / orchestrator surface

В `Marketing2025` не должны жить:

- raw Yandex API transport logic
- дублирование retry/auth/rate-limit behavior
- дублирование platform wrappers, которые уже есть в `yandex.ad`

### Ответственность client / agent layer

LLM-клиенты должны отвечать за:

- user interaction
- ad hoc exploration
- human-in-the-loop review
- planning assistance, когда это полезно

Они не должны быть главным источником workflow state или artifact truth.

## Предлагаемая модель совместной работы

### Основной принцип

Команды должны взаимодействовать через **явные контракты**, а не через неформальные prompt-conventions.

Главные contract surfaces:

1. MCP tool contracts из `yandex.ad`
2. workflow / artifact contracts из `Marketing2025`
3. общие review и acceptance criteria

### Граница ответственности

Правило для принятия решения:

- “Как безопасно получить или изменить данные Yandex?” -> `yandex.ad`
- “Какой workflow запускать, в каком порядке, с какими артефактами и quality gates?” -> `Marketing2025`
- “Как человеку или агенту удобно с этим взаимодействовать?” -> client / skill / UI layer

### Что нельзя дублировать

Нельзя дублировать между двумя репозиториями:

- tool semantics
- campaign/account resolution rules
- write safety policy
- output schemas
- QA status semantics
- workflow routing logic

Если одно и то же правило живёт в двух местах, один из репозиториев обязательно начнёт drift’ить, а качество pipeline будет ухудшаться.

## Ближайшие общие цели

Следующий этап должен оптимизировать реального текущего пользователя, а не гипотетическую платформенную полноту.

### Цель 1 — Сделать read path дешевле и стабильнее

Это главная зона ценности для:

- weekly Analyst work
- pipeline snapshot
- pipeline pre-synthesis data collection

Ожидаемый результат:

- меньше MCP round-trips
- меньше context cost
- меньше downstream parsing failures

### Цель 2 — Сделать pipeline contracts явными

Pipeline уже зависит от machine-consumed outputs.

Ожидаемый результат:

- стабильные JSON shapes
- явные ids и status fields
- меньше glue code в downstream gates
- проще дебажить `Voicexpert`-подобные прогоны

### Цель 3 — Не затаскивать orchestration внутрь backend

Не нужно превращать `yandex.ad` в скрытый workflow engine.

Ожидаемый результат:

- стабильный MCP surface
- лучшая debuggability
- лучшая portability между host’ами и моделями

## Что нужно строить сейчас

### В `yandex.ad`

#### Workstream A — Усиление контрактов

Deliverables:

- `outputSchema` для наиболее используемых read tools
- явные annotations про read/write intent
- единый HF response envelope для downstream machine use

Критерии успеха:

- pipeline code больше не зависит от ad hoc parsing для каждого tool
- core read tools публикуют стабильные output contracts

#### Workstream B — Узкие read workflows

Новый MCP functionality добавлять только если он заменяет длинную multi-call chain.

Первые допустимые кандидаты:

- account snapshot
- structure snapshot
- attribution audit

Guardrail:

- не раздувать tool surface широко
- не делать dynamic tool generation внутри сервера

Критерии успеха:

- каждый новый workflow заменяет существенно более длинную цепочку вызовов
- каждый workflow возвращает контракт, полезный и для LLM, и для deterministic pipeline code

### В `Marketing2025`

#### Workstream C — CLI-first orchestrator

`Marketing2025` должен двигаться к operator-grade CLI/control plane.

Первичная поверхность:

- `snapshot`
- `weekly-review`
- `pipeline run`
- `qa preflight`
- `qa review`

Критерии успеха:

- у каждого run есть стабильный run id
- каждый run пишет артефакты в предсказуемые locations и schemas
- один и тот же workflow можно запускать человеком, cron, CI или LLM-assisted operator

#### Workstream D — Artifact и quality contracts

Нужно явно описать контракты для:

- run record
- recommendation record
- evidence record
- preflight report
- review report

Критерии успеха:

- downstream scripts не пытаются извлекать state из prose
- QA gates работают по явным statuses и ids

## Общий процесс review

### Классы изменений

#### Backend contract change

Примеры:

- новый MCP tool
- изменение output shape
- изменение safety behavior

Обязательный review:

- owner `yandex.ad`
- owner `Marketing2025` workflow layer

#### Workflow contract change

Примеры:

- новая artifact schema
- новая semantics для statuses
- изменение смысла QA gate

Обязательный review:

- owner `Marketing2025`
- owner `yandex.ad`, если по-новому используются MCP outputs

### RFC rule

Любое изменение, которое влияет на cross-repo contracts, должно быть записано до реализации:

- purpose
- current pain
- proposed contract
- migration impact
- acceptance criteria

## Рекомендуемый cadence

### Weekly

- review текущих Analyst pain points
- глубокий review одного pipeline run
- решение, относится ли следующее улучшение к backend или к orchestrator

### На каждый implementation cycle

1. определить contract change
2. реализовать в одном repo
3. адаптировать consuming repo
4. проверить на одном реальном project run
5. оставить или откатить

## Решения, которые уже приняты

Ниже — уже фактически принятые ограничения:

- `yandex.ad` остаётся backend capability layer
- `Marketing2025` становится workflow/control-plane layer
- нужна portability между разными model vendors и MCP clients
- сначала оптимизируем Analyst + Pipeline read paths, а не richer UI
- проблему нельзя решать просто за счёт добавления большого числа новых tools

## Что не является целью этого этапа

В ближайший этап не нужно вкладываться в:

- широкое расширение write workflows
- реализацию MCP Apps runtime
- dynamic tool generation из свободного natural-language task
- host-specific hacks под одного клиента
- project-specific business logic внутри `yandex.ad`

## Предлагаемый следующий шаг

Этот proposal можно использовать для согласования с product/marketing одной конкретной delivery-модели:

1. `yandex.ad` улучшает **contracts + очень маленькое число read workflows**
2. `Marketing2025` улучшает **CLI orchestration + artifacts + QA gates**
3. после каждой итерации обе стороны смотрят один реальный `Voicexpert`-style run

Если этот split принимается, следующий implementation note должен уже зафиксировать:

- какие backend contracts усиливаем первыми
- какие orchestrator commands стандартизируем первыми
- какой первый реальный workflow валидируем end-to-end
