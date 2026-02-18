# Гайд для LLM (PRO MCP)

Документ предназначен для **LLM‑агентов**, которые подключаются к этому MCP‑серверу и должны получить максимум пользы **с включёнными PRO‑инструментами** (включая write‑инструменты под guardrails: `apply=true` + env flags).

Область: **PRO** toolset (Direct + Metrica + Wordstat + Audience), включая **BI Option 2** (датасеты + инкрементальный sync) **через PRO plug-in**.

## Правила безопасности (PRO mindset)

1) **Даже в PRO — safe by default.** Делайте write только если пользователь явно попросил и соблюдены guardrails (`apply=true`, write flags включены, sandbox‑only policy).
2) **Для Direct изменений — plan/apply.** Предпочитайте `direct.hf.plan_changes` → ревью пользователя → `direct.hf.apply_plan`.
3) **Ограничивайте объём данных.** `date_from/date_to`, `chunk_days`, per‑day limits, pagination.
4) **Предпочитайте account‑aware вызовы.** Используйте `account_id`, когда возможно; он резолвит Direct `Client-Login` и опциональный default `counter_id`.

## Включение PRO (чеклист оператора)

Типичный набор:
- `MCP_PUBLIC_READONLY=false`
- For Direct/Audience writes: `MCP_WRITE_ENABLED=true`
- For HF writes: `HF_WRITE_ENABLED=true`
- For destructive HF (deletes): `HF_DESTRUCTIVE_ENABLED=true` (only if you really mean it)
- Оставьте sandbox‑only writes: `MCP_WRITE_SANDBOX_ONLY=true` (рекомендуется)

## Индекс инструментов (PRO)

Правило: `tools/list` — источник истины. Индекс ниже — практическая карта namespaces и рекомендуемых entrypoints.

Accounts:
- `accounts.list`, `accounts.reload`, `accounts.upsert`, `accounts.delete` (writes guarded by `MCP_ACCOUNTS_WRITE_ENABLED`)

Dashboard (Option 1):
- `dashboard.generate_option1` (multi-account, optional Wordstat/Audience blocks)

Dashboard (BI Option 2: датасеты + sync, PRO plug-in):
- `dashboard.schema`
- `dashboard.dataset.*` (Variant B: Direct/Metrica/Wordstat/Join + Audience)
- `dashboard.sync.start`, `dashboard.sync.next`

Direct (raw):
- Reporting: `direct.report`, `direct.get_changes`
- Entities: `direct.list_*` / `direct.get_*`
- Writes: `direct.create_*`, `direct.update_*` (guarded by `MCP_WRITE_ENABLED` + sandbox policy)
- Escape hatch (advanced): `direct.raw_call` (guarded; избегайте без необходимости)

Direct (HF):
- Read helpers: `direct.hf.find_*`, `direct.hf.get_*`, `direct.hf.report_*`
- Write helpers (guarded by `HF_WRITE_ENABLED` + `apply=true`):
  - Plan/apply: `direct.hf.plan_changes`, `direct.hf.apply_plan`
  - Campaign lifecycle / assets / geo / bids / keywords / ads (see `direct.hf.*` in `tools/list`)
  - Destructive: `direct.hf.delete_*` (also requires `HF_DESTRUCTIVE_ENABLED=true`)

Metrica (raw):
- Reports: `metrica.report`, `metrica.list_counters`, `metrica.counter_info`
- Logs API: `metrica.logs_export` (create/evaluate/download/clean/cancel)
- Management writes: `metrica.goals.*` (create/update/delete)
- Escape hatch (advanced): `metrica.raw_call` (избегайте без необходимости)

Metrica (HF):
- Read helpers: `metrica.hf.*` reports + `metrica.hf.counter_summary`
- Writes (apply-guarded): `metrica.hf.create_goal`, `metrica.hf.update_goal`, `metrica.hf.delete_goal`

Audience (raw):
- Read: `audience.user_info`, `audience.segments.list/get/stats/overlap`, `audience.pixels.*`, `audience.lookalikes.*`
- Writes (guarded by `MCP_WRITE_ENABLED` + sandbox policy): `audience.segments.create/update/delete`, `audience.upload.*`
- Escape hatch (advanced): `audience.raw_call` (избегайте без необходимости)

Audience (HF):
- Read helpers: `audience.hf.find_segment`, `audience.hf.catalog`, `audience.hf.segment_perf`
- Activation (write, apply-guarded): `audience.hf.activation_plan` (preview), `audience.hf.apply_activation_plan` (exec)

Wordstat (raw + HF):
- Raw: `wordstat.user_info`, `wordstat.get_regions_tree`, `wordstat.top_requests`, `wordstat.dynamics`, `wordstat.regions`
- HF: `wordstat.hf.suggest_keywords` (resumable via `cursor`), `wordstat.hf.suggest_negative_keywords`

Join (HF):
- `join.hf.direct_vs_metrica_by_utm`
- `join.hf.direct_vs_metrica_by_yclid` (heavier; uses Logs API; resumable via `request_id`)

## BI Option 2 (датасеты + инкрементальный sync)

Примечание:
- Инструменты BI Option 2 появляются только если установлен PRO plug-in. `tools/list` — источник истины.

### Базовый API

1) Посмотреть схему:
- `dashboard.schema`

2) Стартовать sync:
- `dashboard.sync.start`
  - Обязательные: `datasets[]`, `account_ids[]`, `date_from`, `date_to`
  - Опционально: `chunk_days`, `limit_per_day`, `goal_ids`, `segment_ids`

3) Забирать страницы:
- `dashboard.sync.next` with `cursor`
  - Возвращает `ndjson` (по одному JSON‑объекту на строку) вида:
    - `{ "dataset": "...", "account_id": "...", "row": { ... } }`

### Рекомендуемый набор датасетов (Variant B)

Direct (dims + facts):
- `dashboard.dataset.direct_campaigns_dim`
- `dashboard.dataset.direct_adgroups_dim`
- `dashboard.dataset.direct_keywords_dim`
- `dashboard.dataset.direct_campaign_daily`
- `dashboard.dataset.direct_keyword_daily` (тяжёлый; лучше чанки по 1 дню)
- `dashboard.dataset.direct_ads_daily` (тяжёлый; лучше чанки по 1 дню)
- `dashboard.dataset.direct_search_phrases_daily` (очень тяжёлый; только при необходимости)
- `dashboard.dataset.direct_bids_snapshot`

Metrica (facts):
- `dashboard.dataset.metrica_daily`
- `dashboard.dataset.metrica_devices_daily`
- `dashboard.dataset.metrica_geo_daily`
- `dashboard.dataset.metrica_goals_daily` (требует `goal_ids`)
- `dashboard.dataset.metrica_utm_campaigns_daily` (ограничен `limit_per_day`)
- `dashboard.dataset.metrica_landing_pages_daily` (ограничен `limit_per_day`)

Audience:
- `dashboard.dataset.audience_segments`
- `dashboard.dataset.audience_overlap` (требует `segment_ids`)
- `dashboard.dataset.audience_segment_perf_daily` (требует `segment_ids` + даты)

Wordstat (manual / ad‑hoc):
- `dashboard.dataset.wordstat_top_requests`

Join (manual / ad‑hoc):
- `dashboard.dataset.join_direct_vs_metrica_utm_daily`
- `dashboard.dataset.join_direct_vs_metrica_yclid_daily` (Logs API; may return `status=pending` + resumable `request_id`)

## Рекомендации ключей → применение (Direct plan/apply)

Рекомендуемый workflow:

1) Собрать кандидатов:
- `direct.hf.report_search_phrases` (search terms)
- `wordstat.hf.suggest_keywords` (expansion, resumable via `cursor`)
- `wordstat.hf.suggest_negative_keywords` (heuristic negatives)

2) Собрать action plan (только preview):
- `direct.hf.plan_changes`
  - Поддерживаемые операции:
    - `keywords.add` (adgroup)
    - `negatives.merge` (campaign/adgroup)
    - `bids.set` (keyword ids)

3) Ревью пользователем:
- Show `preview.calls[]` + `warnings[]`
- Confirm target account / scope

4) Применить (writes):
- `direct.hf.apply_plan` with `apply=true`

## Metrica PRO writes (Variant 1+2)

Raw goals management (write):
- `metrica.goals.create`
- `metrica.goals.update`
- `metrica.goals.delete`

HF goals management (write, apply‑guarded):
- `metrica.hf.create_goal`
- `metrica.hf.update_goal`
- `metrica.hf.delete_goal`

Операции Logs API остаются отдельными и всё ещё полезны для join’ов на уровне кликов.

## Audience PRO workflows (жизненный цикл сегментов + activation)

Типичный flow:
1) Inspect segments:
   - `audience.segments.list` / `audience.hf.catalog`
2) Create or update:
   - `audience.segments.create` / `audience.segments.update` (writes)
3) Upload data (potential PII):
   - `audience.upload.start` / `audience.upload.status` / `audience.upload.errors`
4) Apply in Direct (retargeting activation):
   - `audience.hf.activation_plan` (preview-only)
   - `audience.hf.apply_activation_plan` with `apply=true`

Важно:
- Считайте payload’ы Audience upload чувствительными (потенциально PII): не логируйте и не сохраняйте.
