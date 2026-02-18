# BI Option 2 (PRO): датасеты + инкрементальный sync — proposal/status — 2026-02-03

Цель: дать **BI-ready** контур для **Direct + Metrica + Wordstat + Audience** в виде:
- стабильных **датасетов** (таблицы/строки),
- **инкрементального sync** (cursor/watermark, NDJSON-friendly),
- минимальной нормализации (raw-first, но с полезными ключами/колонками).

Статус:
- Variant **B (Standard)** реализован как PRO plug-in (датасеты + sync), чтобы не входить в public OSS build.

## Для кого

### SEO-аналитик
- Поисковые запросы → посадочные / конверсии.
- Сегментация по гео / устройствам, динамика во времени.
- Идеи ключей и минус-слов (Wordstat) как вход в семантическое планирование.

### Performance-маркетолог
- Ежедневная эффективность по кампании/группе/объявлению/ключу (CPC/CTR/CPA/CPL).
- Сверка расходов/кликов Direct с визитами/целями Metrica.
- Аудитории/ретаргетинг (Audience): каталог сегментов + пересечения + best-effort perf proxy.

## Принципы дизайна

1) Разделяем **dimensions** и **facts**
   - Dimensions: кампании/группы/ключи/аудитории (редко меняются)
   - Facts: дневные метрики, поисковые фразы, лендинги (растут по времени)
2) Детерминированные ключи
   - у каждой строки есть стабильный `primary_key` (например `account_id + campaign_id + date`)
3) Инкрементальная модель
   - facts: партиционирование по `date` (чанки по дням)
   - dimensions: периодический refresh через пагинацию
4) Ограничение объёма
   - для тяжёлых facts требуем `date_from/date_to`
   - в sync дробим jobs (по умолчанию 7 дней, для тяжёлых датасетов 1 день)
5) Трассируемость
   - возвращаем `raw_refs` с описанием raw-вызовов (что/с какими params).

## Датасеты (Variant B — Standard)

### Direct

Dimensions:
- `dashboard.dataset.direct_campaigns_dim`
- `dashboard.dataset.direct_adgroups_dim`
- `dashboard.dataset.direct_keywords_dim`

Facts:
- `dashboard.dataset.direct_campaign_daily`
- `dashboard.dataset.direct_keyword_daily` (тяжёлый; в sync чанкуется по дням)
- `dashboard.dataset.direct_ads_daily` (тяжёлый; в sync чанкуется по дням)
- `dashboard.dataset.direct_search_phrases_daily` (очень тяжёлый; используйте точечно)

Snapshots:
- `dashboard.dataset.direct_bids_snapshot`

### Metrica

Facts:
- `dashboard.dataset.metrica_daily`
- `dashboard.dataset.metrica_devices_daily`
- `dashboard.dataset.metrica_geo_daily` (по умолчанию country; опционально city)
- `dashboard.dataset.metrica_goals_daily` (нужен `goal_ids`)
- `dashboard.dataset.metrica_utm_campaigns_daily` (ограничено `limit_per_day`)
- `dashboard.dataset.metrica_landing_pages_daily` (ограничено `limit_per_day`)

### Wordstat (manual / ad-hoc)

- `dashboard.dataset.wordstat_top_requests` (ограничено; зависит от входа)

### Audience

- `dashboard.dataset.audience_segments`
- `dashboard.dataset.audience_overlap` (нужен `segment_ids`)
- `dashboard.dataset.audience_segment_perf_daily` (нужны `segment_ids` + даты; best-effort proxy)

### Join (manual / ad-hoc)

- `dashboard.dataset.join_direct_vs_metrica_utm_daily`
- `dashboard.dataset.join_direct_vs_metrica_yclid_daily` (Logs API; может вернуть `status=pending` + `request_id` для resume; обязательно задавайте жёсткие bounds)

## Sync API (инкрементальный)

Инструменты:
- `dashboard.sync.start` → возвращает `cursor` (base64url JSON)
- `dashboard.sync.next` → возвращает `ndjson` + следующий `cursor`

Cursor/job модель:
- Jobs = декартово произведение (`dataset` × `account_id` × `date_chunk`) для датасетов с периодом.
- Выход — NDJSON (по одной JSON-строке):
  - `{ "dataset": "...", "account_id": "...", "row": { ... } }`

Рекомендованное поведение consumer:
- Храните свой “watermark” (например последний `date`, который полностью прогрузили).
- Повторяйте sync со следующим `date_from`.

## PRO write scope (полный контур)

Direct:
- Raw write: `direct.create_*`, `direct.update_*` (guarded)
- HF write: используйте plan/apply:
  - `direct.hf.plan_changes` → `direct.hf.apply_plan`

Audience:
- Raw write: `audience.segments.create/update/delete`, `audience.upload.*` (guarded)
- HF activation: `audience.hf.activation_plan` (preview) / `audience.hf.apply_activation_plan` (apply)

Wordstat:
- Внутри Wordstat инструментов нет Direct write; “write value” — это применение рекомендаций в Direct через `direct.hf.plan_changes` / `direct.hf.apply_plan`.

Metrica:
- Logs API используется для join/exports.
- Management write: goals CRUD (`metrica.goals.*`, `metrica.hf.*`, apply-guarded).
