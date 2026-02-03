# Гайд для LLM (Public Read‑Only MCP)

Документ предназначен для **LLM‑агентов** (Claude, ChatGPT и др.), которые подключаются к этому MCP‑серверу и должны получить максимум пользы **без write‑доступа**.

Область: **public read‑only** toolset (целевой контракт v1.0.0).

## Что здесь значит “read‑only” (Public v1.0.0)

Определение: **read‑only = не менять управляемые сущности** в Direct/Метрике/Audience (никаких create/update/delete кампаний, сегментов, целей и т.п.).

Разрешённые side effects (всё ещё считаются “read‑only” в рамках public‑контракта):
- **Wordstat**: запросы, которые создают/считают отчёты на стороне провайдера.
- **Metrica Logs API** export jobs (`metrica.logs_export`) для анализа/join’ов (без изменения настроек счётчика).

Запрещено в public:
- Любые Direct write (`direct.create_*`, `direct.update_*`) и любые “escape hatch” write (`*.raw_call`).
- Любые Audience write (создание/обновление/удаление сегментов, загрузки, активация в Direct).
- Любые write в Management API Метрики (например, CRUD целей).

## Базовые правила (public contract mindset)

1) **Считайте read‑only дефолтом.** Не вызывайте инструменты, которых нет в `tools/list`.
2) **Явно выбирайте аккаунт**, когда возможно:
  - Предпочитайте `account_id` (маппит Direct `Client-Login` + дефолтные счётчики Метрики).
  - `counter_id` используйте только если у профиля несколько счётчиков или нужен override.
3) **Ограничивайте объём данных.** Используйте `limit`, `max_rows` и caps dashboard/wordstat.
4) **Сначала используйте HF.** `direct.hf.*`, `metrica.hf.*`, `wordstat.hf.*`, `join.hf.*` — до raw инструментов.
5) **Считайте ответы “raw‑ish JSON”.** Не предполагайте, что опциональные ключи всегда есть. Устойчиво обрабатывайте partial coverage.

## Минимальный “хороший агент” (workflow)

1) Обнаружьте аккаунты:
   - `accounts.list`
   - Если пользователь обновил `accounts.json` — `accounts.reload`

2) Быстрый “снимок ситуации”:
   - Direct: `direct.hf.get_campaign_summary` или `direct.hf.report_performance`
   - Metrica: `metrica.hf.report_time_series` + `metrica.hf.report_landing_pages`

3) Join Direct ↔ Metrica (если нужно):
   - `join.hf.direct_vs_metrica_by_utm` — более стабильное сравнение на уровне кампаний
   - `join.hf.direct_vs_metrica_by_yclid` — связывание кликов и визитов (best effort; тяжелее)

4) Сгенерируйте дашборд для человека:
   - `dashboard.generate_option1` с `output_dir` и `return_data=false`
   - Multi‑account: `all_accounts=true` (в UI будет переключатель аккаунтов)
   - Опционально: `include_audience=true` чтобы добавить блоки Audience (каталог + пересечения)

5) Добавьте семантику/спрос (Wordstat):
   - Raw: `wordstat.top_requests` / `wordstat.dynamics` / `wordstat.regions`
   - HF: `wordstat.hf.suggest_keywords` (возобновляемо по `cursor`) + `wordstat.hf.suggest_negative_keywords`

6) Добавьте аудитории (Audience):
   - Raw: `audience.segments.list` / `audience.segments.get` / `audience.segments.overlap`
   - HF: `audience.hf.catalog` + `audience.hf.find_segment` + `audience.hf.segment_perf` (best effort)

## Accounts и multi‑account поведение

### Когда использовать `account_id`

Когда нужен “project‑aware” режим:
- корректный Direct `Client-Login`
- корректные allow‑list/дефолты по счётчикам Метрики
- multi‑account dashboard

### Как делать multi‑account dashboards

- Предпочтительно одним вызовом:
  - `dashboard.generate_option1` с `all_accounts=true`
- Или явно перечислить:
  - `dashboard.generate_option1` с `account_ids=["a","b","c"]`

### Шаблон запроса к пользователю (что спросить)

Попросите пользователя дать:
- `account_id` (или “all accounts”)
- `date_from`, `date_to` (YYYY-MM-DD; “до вчера” обычно лучше)
- цель: **dashboard**, **analysis**, **keywords**, **join**, **raw export**
- ограничения: бюджет времени, max rows, язык/регионы/устройства для Wordstat

## Dashboard (`dashboard.generate_option1`) best practices

Используйте dashboard, когда нужно:
- Читабельное резюме (HTML)
- JSON датасет “на потом”
- **multi‑account** summary с переключателем в UI

Рекомендованные дефолты:
- `output_dir` задан (чтобы артефакты сохранялись)
- `return_data=false` (чтобы не тащить гигантские payload’ы в чат)
- `include_raw_reports=true` — только если реально нужен дебаг raw payload’ов
- `include_wordstat=true` — только если есть Wordstat креды и хватает time‑budget
- `include_audience=true` — только если есть Audience креды и нужен блок по аудиториям

Пример (multi‑account, 30 дней, только запись файлов):
```json
{
  "all_accounts": true,
  "date_from": "2026-01-04",
  "date_to": "2026-02-02",
  "output_dir": "/data/dashboards",
  "return_data": false,
  "include_wordstat": true,
  "include_audience": true,
  "wordstat_max_campaigns": 5,
  "wordstat_num_phrases": 50
}
```

Примечания:
- Сервер может автоматически сдвинуть `date_to` на **вчера**, если вы передали сегодня/будущее.
- В multi‑account режиме HTML содержит переключатель аккаунтов и обновляет view на клиенте.
- Wordstat блок в дашборде — **best effort** и ограничен `wordstat_*` caps.

## Direct: когда raw, а когда HF

### Для анализа — сначала HF

Используйте для вопросов “что происходит?”:
- `direct.hf.get_campaign_summary`
- `direct.hf.report_performance`
- `direct.hf.report_search_phrases` (анализ поисковых фраз)
- `direct.hf.report_keywords` / `direct.hf.report_ads` / `direct.hf.report_adgroups`
- `direct.hf.get_bids_summary` (снимок ставок)

### Raw инструменты — когда нужен “как в API”
Используйте, если нужен дебаг или кастомный маппинг:
- `direct.report` (custom reports)
- `direct.list_campaigns`, `direct.list_adgroups`, `direct.list_ads`, `direct.list_keywords`, etc.

Подсказки по эффективности:
- Начинайте с HF summary → затем углубляйтесь в raw списки.
- Для инкрементальных сценариев “что изменилось?” используйте `direct.get_changes` (легче, чем полный refresh).

## Metrica: быстрые отчёты vs тяжёлые логи

### Для dashboard/аналитики — HF отчёты
- `metrica.hf.report_time_series`
- `metrica.hf.report_landing_pages`
- `metrica.hf.report_utm_campaigns`
- `metrica.hf.report_geo`
- `metrica.hf.report_devices`
- `metrica.hf.counter_summary`

### Logs API мощный, но тяжелее
- `metrica.logs_export` используется в `join.hf.direct_vs_metrica_by_yclid`
- Сначала пробуйте join’ы/dashboard; к логам переходите только если нужно линковать клики к визитам

## Audience (public read‑only)

### Raw слой (форма как у Audience API)
- `audience.user_info`
- Сегменты (read): `audience.segments.list`, `audience.segments.get`, `audience.segments.stats`, `audience.segments.overlap`
- Каталоги (read): `audience.pixels.list`, `audience.pixels.get`, `audience.lookalikes.list`, `audience.lookalikes.get`

### HF слой (agent‑friendly)
- `audience.hf.find_segment`
- `audience.hf.catalog`
- `audience.hf.segment_perf` (best effort proxy; bounded; expect partial coverage)

## Join: как выбирать инструмент

### `join.hf.direct_vs_metrica_by_utm` (рекомендуется)
Используйте, когда:
- Нужна дневная динамика и сравнение на уровне кампаний
- Есть стабильная разметка `UTMCampaign` (или вы можете надёжно её вывести)

Типичный вопрос:
- «Клики/расход/лиды Direct по дням vs визиты/лиды Метрики по дням — коррелирует ли?»

### `join.hf.direct_vs_metrica_by_yclid` (best effort, тяжелее)
Используйте, когда:
- Нужно связать click identifiers из Direct с визитами Метрики (Logs API)
- UTMs are missing/unreliable and you need click-level evidence

Операционные советы:
- Держите `max_rows` ограниченным (по умолчанию уже есть cap)
- Используйте `request_id`, чтобы продолжить прогон при таймауте
- Ожидайте partial join: поля логов могут отсутствовать, а данные могут не покрывать все клики

## Wordstat (public read‑only: семантика/спрос)

### Raw слой (форма как у API)
- `wordstat.user_info` — проверка доступа и контекста аккаунта
- `wordstat.get_regions_tree` — каталог region ids
- `wordstat.top_requests` — related queries for one phrase (or a list)
- `wordstat.dynamics` — time dynamics for a phrase
- `wordstat.regions` — region distribution for a phrase

Raw используйте, когда нужно:
- Максимальная гибкость (вы сами интерпретируете payload)
- Точные поля ответа для выгрузки/аудита

### HF слой (agent‑friendly)

#### `wordstat.hf.suggest_keywords` (resumable)
Используйте, когда:
- Есть **seed phrases** и нужен консолидированный shortlist кандидатов

Важно:
- Инструмент может вернуть `status="pending"` и `preview.cursor`.
- Если pending — вызывайте ещё раз с `cursor`, пока не получите `status="ok"`.

Пример цикла:
1) Call with `seed_phrases`
2) If pending, call again with `cursor`
3) Stop when `status="ok"`

#### `wordstat.hf.suggest_negative_keywords` (lexicon-based)
Используйте, когда:
- Уже есть список фраз (из поисковых фраз, Wordstat, лендингов) и нужны кандидаты **минус‑слов/токенов**
- Нужен быстрый эвристический список без внешних API вызовов

## Сборка сценария: “рекомендации ключей для запущенных кампаний”

Хороший паттерн для public read‑only агента:
1) Identify top-spend or top-click campaigns:
   - `direct.hf.report_performance` (bounded)
2) Extract seed terms:
   - `direct.hf.find_keywords` (per campaign/adgroup) or `direct.hf.report_search_phrases`
3) Get expansion candidates:
   - `wordstat.top_requests` (raw) or `wordstat.hf.suggest_keywords` (HF)
4) Suggest negatives:
   - `wordstat.hf.suggest_negative_keywords` on the phrase list (from step 2–3)
5) Present an “apply plan” (but do not apply):
   - Group by campaign/adgroup
   - Provide rationale + expected impact
   - Flag that actual edits require Pro/write tools

## Ошибки: как действовать, когда tool падает

Когда инструмент вернул MCP‑ошибку:
- Выведите **provider** (`direct`, `metrica`, `wordstat`, `audience`) и любые `request_id`/ids.
- Дайте практичный hint:
  - нет доступа → проверьте права на аккаунт/счётчик/логин
  - невалидный токен → обновить/перепройти OAuth и повторить
  - rate limit → уменьшить caps / повторить позже
  - нет маппинга `account_id` → проверить `accounts.json` и вызвать `accounts.reload`

Рекомендации по ретраям:
- Повторяйте только при явно временных ошибках (timeout/5xx/rate limit).
- Не ретрайте “вслепую” 4xx (обычно это конфиг/права).

## Индекс инструментов (public read‑only)

Accounts:
- `accounts.list`, `accounts.reload`

Dashboard:
- `dashboard.generate_option1`

BI Option 2 (datasets/sync):
- Not part of public surface (PRO-only): `dashboard.schema`, `dashboard.dataset.*`, `dashboard.sync.*`

Direct (raw):
- `direct.report`, `direct.get_changes`, `direct.list_*`

Direct (HF):
- `direct.hf.find_*`, `direct.hf.report_*`, `direct.hf.get_*`

Metrica (raw):
- `metrica.report`, `metrica.logs_export`, `metrica.list_counters`, `metrica.counter_info`

Metrica (HF):
- `metrica.hf.*`

Audience (raw + HF):
- `audience.*` (read-only subset), `audience.hf.*` (read-only subset)

Joins (HF):
- `join.hf.direct_vs_metrica_by_utm`, `join.hf.direct_vs_metrica_by_yclid`

Wordstat (raw + HF):
- `wordstat.*`, `wordstat.hf.*`
