# BI Option 2 (PRO): datasets + incremental sync — proposal — 2026-02-03

Цель: дать PRO-пользователю “BI-ready” контур **Direct + Metrica + Wordstat + Audience** в виде:
- стабильных **датасетов** (таблицы/строки),
- **инкрементального sync** (cursor/watermark, NDJSON-friendly),
- минимальной нормализации (raw-first, но с полезными ключами/полями).

## Для кого (практические задачи)

### SEO-аналитик
- Поисковые запросы (search phrases) → посадочные/конверсии.
- Сегментация по регионам/устройствам, динамика по времени.
- Идеи ключей/минус-слов (Wordstat) как вход в план контента/семантики.

### Performance/маркетолог
- Ежедневная эффективность кампаний/групп/объявлений/ключей (CPC/CTR/CPA/CPL).
- Сквозная аналитика: сопоставление Direct расходов/кликов с Metrica визитами/целями.
- Аудитории/ретаргетинг (Audience): каталог сегментов, пересечения, “где применено” и best-effort perf.

## Принципы дизайна датасетов

1) **Разделяем “dimensions” и “facts”**
   - Dimensions: кампании/группы/ключи/аудитории (редко меняются)
   - Facts: дневные метрики, поисковые запросы, лендинги (растут по времени)
2) **Ключи и детерминизм**
   - Каждая строка имеет `primary_key` (напр. `account_id + campaign_id + date`)
3) **Инкрементальность**
   - Для facts: watermark по `date` (партитирование по дням/неделям)
   - Для dimensions: watermark по `updated_at` (если доступно) или периодический полный refresh
4) **Ограничение объёма**
   - параметр `date_from/date_to`, `limit`, `page_size`
   - в sync делаем chunk’и (например 7 дней на job) для устойчивости
5) **Traceability**
   - `raw_refs` в результатах датасет-инструментов (что именно вызвали/с какими params)

## Предлагаемый набор датасетов (3 варианта)

### Variant A — Minimal (самое востребованное)

**Direct**
- `dashboard.dataset.direct_campaigns_dim`
- `dashboard.dataset.direct_campaign_daily` (Date, CampaignId, Impressions, Clicks, Cost, optional Leads/CPL)
- `dashboard.dataset.direct_search_phrases_daily` (SEARCH_QUERY_PERFORMANCE_REPORT: Query, MatchedKeyword, MatchType + metrics)

**Metrica**
- `dashboard.dataset.metrica_daily` (visits/users/bounce/duration + optional goals)
- `dashboard.dataset.metrica_landing_pages_daily` (top landing pages, best-effort)
- `dashboard.dataset.metrica_utm_campaigns_daily`

**Wordstat**
- `dashboard.dataset.wordstat_top_requests` (seed → candidates, bounded)

**Audience**
- `dashboard.dataset.audience_segments` (уже реализовано)
- `dashboard.dataset.audience_overlap` (уже реализовано)

**Join**
- `dashboard.dataset.join_direct_vs_metrica_utm_daily` (на базе `join.hf.direct_vs_metrica_by_utm`)

### Variant B — Standard (для ежедневного BI)

Variant A +:

**Direct**
- `dashboard.dataset.direct_adgroups_dim`
- `dashboard.dataset.direct_keywords_dim`
- `dashboard.dataset.direct_keyword_daily`
- `dashboard.dataset.direct_ads_daily`
- `dashboard.dataset.direct_bids_snapshot` (bids/bidmodifiers на дату)

**Metrica**
- `dashboard.dataset.metrica_devices_daily`
- `dashboard.dataset.metrica_geo_daily`
- `dashboard.dataset.metrica_goals_daily` (пер-цель или “all goals”)

**Audience**
- `dashboard.dataset.audience_segment_perf_daily` (уже реализовано; best effort proxy)

### Variant C — Max (для агентств/форензики)

Variant B +:

**Join**
- `dashboard.dataset.join_direct_vs_metrica_yclid` (тяжёлый; через Logs API; лучше как отдельный экспорт)

**Metrica logs**
- `dashboard.dataset.metrica_logs_exports` (метаданные о request_id, статусах, частях, без PII)

**Wordstat**
- `dashboard.dataset.wordstat_dynamics` (для мониторинга трендов по ключевым фразам)
- `dashboard.dataset.wordstat_regions` (гео-структура спроса по фразе)

## Sync API (инкрементальный)

Инструменты:
- `dashboard.sync.start` → возвращает `cursor` (base64url JSON)
- `dashboard.sync.next` → возвращает `ndjson` + обновлённый `cursor`

Рекомендации по cursor/job модели:
- Jobs = декартово произведение (`dataset` × `account_id` × `date_chunk`)
- `dashboard.sync.next` отдаёт **NDJSON**:
  - по одной строке: `{ "dataset": "...", "account_id": "...", "row": { ... } }`
- Consumer хранит “watermark” (например последний `date`) и вызывает `sync.start` с новым `date_from`.

## PRO write инструменты, необходимые для “полного контура”

Direct: весь набор `direct.hf.*` write из каталога уже есть (budget/geo/ads/keywords/bids/assets/utm).

Audience: есть `audience.segments.*` write + `audience.upload.*` + `audience.hf.apply_activation_plan`.

Wordstat: write как такового нет; PRO-ценность — **apply** рекомендаций в Direct:
- добавить ключи/минус-слова/ставки по результатам Wordstat и search phrases.
Рекомендуется отдельный HF слой “plan → apply” (см. спецификацию ниже).

Metrica: определить, какие write-операции реально нужны (обычно хватает read + Logs API “create/cancel/clean”).

## Открытые вопросы (нужно подтвердить)

1) **Список PRO датасетов**: выбираем Variant A/B/C как “базовый” для 1.0 PRO?
2) **Metrica write**: что считать write-инструментами в PRO?
   - Goals (create/update/delete)?
   - Counter management?
   - Только Logs API операции (create/cancel/clean)?
3) **Wordstat→Direct apply**: какой UX предпочтительнее?
   - Option 1: быстрые инструменты (`direct.hf.apply_wordstat_keywords`, `direct.hf.apply_wordstat_negatives`)
   - Option 2: общий “plan/apply” (`direct.hf.plan_changes` → `direct.hf.apply_plan`) для идемпотентности и аудита

## Wordstat→Direct apply: варианты спецификации (PRO)

Нужно помнить: Wordstat не меняет Direct сущности; “write” здесь = **изменения в Direct** на основе Wordstat/поисковых фраз.

### Option 1 — Fast tools (быстро, минимально)

1) `direct.hf.apply_wordstat_keywords` (add keywords)
- Вход:
  - `adgroup_id` (required)
  - `phrases[]` (required) — уже отфильтрованные/дедуплицированные фразы
  - `max_phrases` (default 50)
  - `dedupe_mode` (`strict|normalize`, default `normalize`)
  - `bid_rub?` (optional) — если задан, то проставляем `Bid` (либо отдельным шагом)
  - `dry_run=true|false`, `apply=true|false`
- Выход:
  - `preview.items[]` (payload для `direct.create_keywords`)
  - `result` (ответ API при apply)

2) `direct.hf.apply_wordstat_negatives` (set negatives)
- Вход:
  - `campaign_id` **или** `adgroup_id`
  - `items[]` (tokens/phrases)
  - `mode=merge|replace` (default `merge`)
  - `dry_run`, `apply`
- Выход:
  - `preview.items[]` (payload для `direct.update_campaigns`/`direct.update_adgroups`)

Плюсы: быстро внедрить. Минусы: сложнее делать идемпотентность и аудит “что именно применили”.

### Option 2 — Plan/apply (рекомендую)

1) `direct.hf.plan_changes` (preview-only)
- Вход:
  - `context`: `{account_id?, direct_client_login?, counter_id?}`
  - `operations[]` (типизированные операции):
    - `{"op":"keywords.add","adgroup_id":..., "phrases":[...], "bid_rub?":...}`
    - `{"op":"negatives.merge","scope":"campaign|adgroup","id":..., "items":[...]}`
    - `{"op":"bids.set","keyword_ids":[...],"bid_rub":...}`
  - `dry_run=true` (фиксируем как preview)
- Выход:
  - `plan_id` (opaque)
  - `preview.calls[]` — точные `direct.*` вызовы (с ресурсом/методом/params)
  - `warnings[]` — PII/объём/лимиты/ambiguous matches

2) `direct.hf.apply_plan` (exec)
- Вход: `plan_id`, `apply=true`
- Выход: `result.calls[]` + сводка ошибок по шагам

Плюсы: идемпотентность, аудит, удобно для LLM и “human in the loop”. Минусы: требуется хранение plan state (in-memory с TTL) или отдавать весь план обратно в cursor.

### Option 3 — “BI-driven apply”

Инструмент принимает **BI Option 2 датасет** (или ссылку на файл) и применяет изменения:
- `direct.hf.apply_recommendations_from_dataset`

Плюсы: хорошо для агентств и пайплайнов. Минусы: сложнее; требует строгой схемы и проверок.

**Рекомендация**: начать с Option 2 (plan/apply) для устойчивости; если хочешь быстрее — Option 1 как MVP, а Option 2 сразу планируем как “2.0 PRO”.
