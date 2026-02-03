# Предложение по списку MCP-инструментов — Yandex Audience (minimal contour) — 2026-02-02
Контур: **Direct + Metrica + Wordstat + Audience**.

Цель: добавить **Yandex Audience API** в MCP `yandex-direct-metrica-mcp` так, чтобы:
- в **public** режиме были доступны **read-only** инструменты Audience (сырые + HF),
- write‑операции (создание/обновление сегментов, загрузки, активация в Direct) оставались **только в pro** и выполнялись строго под guardrails (`apply=true` + write flags).

## Термины (public vs pro)

В public 1.x:
- **Запрещено**: любые write (Audience create/update/delete/upload), любые Direct write (create/update), любые escape hatches (`*.raw_call`).
- **Разрешено**: чтение Direct/Metrica/Wordstat/Audience, формирование дашборда, HF read-only (диагностика/каталоги/пресеты).

В pro 1.x:
- Разрешены write инструменты при включённых переменных окружения (см. guards ниже).

## Options (3) — покрытие “всех” raw данных Audience

### Option A — Явные raw инструменты + pro-only escape hatch (recommended)
- Public: только “явные” `audience.*` на ключевые ресурсы.
- Pro: дополнительно `audience.raw_call` (allowlist + write guards) для редких/новых эндпоинтов без немедленного релиза MCP.

### Option B — Только явные raw инструменты
- Максимально безопасно, но придётся чаще релизить MCP при добавлении новых эндпоинтов.

### Option C — Только `audience.raw_call`
- Быстро, но ухудшает UX/валидацию/стабильность и сложнее соблюдать public-readonly политику.

Рекомендуем выбрать Option A.

---

## Уровень G — Audience raw (public, read-only)

### 1) `audience.user_info`
- Назначение: проверка доступа/учётки Audience.
- Параметры: нет.
- Возврат: raw JSON.

### 2) `audience.segments.list`
- Назначение: список сегментов.
- Параметры: `limit?`, `offset?`, `types?`, `statuses?`, `fields?`.
- Возврат: raw JSON списка (как в API).

### 3) `audience.segments.get`
- Назначение: получить сегмент по `segment_id`.
- Параметры: `segment_id` (string, required), `fields?`.
- Возврат: raw JSON сегмента.

### 4) `audience.segments.stats`
- Назначение: получить статистику/размер сегмента (если API поддерживает отдельный метод/поле).
- Параметры: `segment_id` (required), `fields?`.
- Возврат: raw JSON.

### 5) `audience.segments.overlap`
- Назначение: пересечение/оверлап сегментов (если доступно).
- Параметры: `segment_ids` (string[], required), `mode?` (matrix|top_pairs), `limit?`.
- Возврат: raw JSON.

### 6) `audience.pixels.list`
- Назначение: список пикселей (если используется/доступно).
- Параметры: `limit?`, `offset?`, `fields?`.
- Возврат: raw JSON.

### 7) `audience.pixels.get`
- Назначение: пиксель по `pixel_id`.
- Параметры: `pixel_id` (string, required), `fields?`.
- Возврат: raw JSON.

### 8) `audience.lookalikes.list`
- Назначение: список look‑alike сегментов/задач (если доступно аккаунту).
- Параметры: `limit?`, `offset?`, `fields?`.
- Возврат: raw JSON.

### 9) `audience.lookalikes.get`
- Назначение: look‑alike по `lookalike_id`/`segment_id` (в зависимости от API).
- Параметры: `id` (string, required), `fields?`.
- Возврат: raw JSON.

---

## Уровень H — Audience HF (public, read-only)

Принципы HF слоя (как в `docs/human-friendly-tools-2026-01-17.md`):
- small inputs (names, короткие списки id, период)
- возвращаем **и** удобные поля, **и** `raw`/`raw_refs` для трассировки
- никакой тяжёлой нормализации

### 1) `audience.hf.find_segment`
- Назначение: найти сегменты по имени/типу/статусу.
- Вход:
  - `name_contains?` (string)
  - `types?` (string[])
  - `statuses?` (string[])
  - `limit?` (int, default 20)
- Выход:
  - `segments[]`: `{id, name, type, status, updated_at?, size?}`
  - `raw` (optional, when `include_raw=true`)

### 2) `audience.hf.get_segment_summary`
- Назначение: “карточка сегмента” для UI/LLM.
- Вход: `segment_id` (required), `include_raw=true|false`.
- Выход:
  - `summary`: `{id, name, type, status, size?, updated_at?, source?, notes?}`
  - `raw` / `raw_refs`

### 3) `audience.hf.segment_health`
- Назначение: быстрый health-check сегмента (готовность к использованию в рекламе).
- Вход:
  - `segment_id` (required)
  - `min_size?` (int, default 1000)
  - `max_age_days?` (int, default 30)
- Выход:
  - `status`: `ok|warning|error`
  - `hints[]`: `{code, message, severity}`
  - `evidence`: `{size?, updated_at?, status?, last_error?}`
  - `raw_refs`

### 4) `audience.hf.overlap_matrix`
- Назначение: матрица пересечений для списка сегментов (дедупликация).
- Вход: `segment_ids` (string[], required), `top_k?` (int, default 50)
- Выход:
  - `matrix` (sparse): `{a,b,overlap_share?, overlap_abs?}[]`
  - `top_pairs[]`
  - `raw_refs`

### 5) `audience.hf.segment_perf` (best-effort)
- Назначение: эффективность Audience‑сегмента в разрезе Direct+Metrica.
- Вход:
  - `account_id?` (string) — для резолва `direct_client_login` и дефолтных `counter_id`
  - `direct_client_login?` (string)
  - `counter_id?` (int)
  - `segment_id` (string, required)
  - `date_from` (YYYY-MM-DD, required)
  - `date_to` (YYYY-MM-DD, required)
  - `grain` (day|week|month, default day)
  - `goal_ids?` (int[]) — если нужно считать leads/конверсии
- Выход:
  - `status`: `ok|partial|error`
  - `result.series[]`: `{date, impressions?, clicks?, cost?, visits?, goal_reaches?}`
  - `meta.coverage`: описание, как именно выполнен маппинг сегмента на Direct/Metrica (см. ниже)
  - `raw_refs`: параметры вызовов `direct.report` / `metrica.report`

Маппинг (3 стратегии, выбрать одну на MVP и задокументировать):
1) По Direct ретаргетинг условиям/аудиторным таргетингам (управленческий путь).
2) Через Metrica сегменты/цели как прокси (аналитический путь).
3) Через соглашения именования/теги (операционный путь).

### 6) `audience.hf.catalog` (for dashboards)
- Назначение: “каталог аудиторий” с полезными колонками под фильтры/таблицы.
- Вход: `account_id?`, `limit?`, `offset?`, `include_health=false|true`.
- Выход:
  - `segments[]`: `{id,name,type,status,size?,updated_at?,health?}`
  - `raw_refs`

---

## Pro-only write (Audience + activation in Direct)

### A) Audience write tools (pro)
- `audience.segments.create` / `audience.segments.update` / `audience.segments.delete`
- `audience.upload.start` / `audience.upload.status` / `audience.upload.errors`

Примечание по данным: любые загрузки в Audience могут содержать PII (email/телефон и т.п.). MCP не хранит эти данные, принимает только как краткоживущий payload на время запроса, не логирует содержимое, и маскирует в ошибках.

### B) HF write tools (pro)
- `audience.hf.activation_plan` (preview-only)
  - Вход: `segment_id`, `targets[]` (campaign/adgroup/retargeting list), `apply=false`
  - Выход: `preview.calls[]` (какие `direct.*` вызовы будут сделаны), `warnings[]`
- `audience.hf.apply_activation_plan` (apply=true)
  - Guards: `HF_ENABLED=true`, `HF_WRITE_ENABLED=true`, `MCP_WRITE_ENABLED=true` (+ sandbox-only policy)

---

## Уровень F — Dashboard integration (options)

### Option 1 (быстро): расширить `dashboard.generate_option1`
Добавить в генератор:
- блок “Аудитории” (таблица сегментов + health)
- блок “Пересечения” (top overlaps)
- блок “Эффективность сегмента” (select сегмент → график/таблица)

### Option 2 (рекомендую для BI): датасеты + инкрементальный sync
Добавить tools:
- `dashboard.schema` — версии и описания таблиц/ключей
- `dashboard.dataset.audience_segments`
- `dashboard.dataset.audience_overlap`
- `dashboard.dataset.audience_segment_perf_daily`
- `dashboard.sync.start` / `dashboard.sync.next` — cursor/watermark, NDJSON-friendly

### Option 3: snapshot export (CSV/SQLite)
- `dashboard.export` — генерирует файлы в `output_dir` (только локально), возвращает пути.

---

## Public env-матрица (норма)

Audience обычно использует тот же Yandex OAuth, что и Direct/Metrica (если у приложения включены нужные права). Если нужен отдельный app/token — добавить параллельные переменные по аналогии с Wordstat.

Основной OAuth (по умолчанию общий):
- `YANDEX_CLIENT_ID`, `YANDEX_CLIENT_SECRET`, `YANDEX_REFRESH_TOKEN` (или `YANDEX_ACCESS_TOKEN`)
- `YANDEX_SCOPES` (опционально): добавить Audience‑права, если требуется для OAuth flow

Флаги:
- `MCP_AUDIENCE_ENABLED` (default true)
- `MCP_AUDIENCE_RATE_LIMIT_RPS` (0=disabled)

Guards (public всегда “выключены” на write):
- `MCP_PUBLIC_READONLY=true` — скрывает/вырубает write tools и любые `*.raw_call`
- `MCP_WRITE_ENABLED=false`, `HF_WRITE_ENABLED=false`, `HF_DESTRUCTIVE_ENABLED=false`

---

## Согласование (explicit approval)
Этот документ — только черновик. Добавление новых инструментов `audience.*` и `audience.hf.*` делается **только после явного утверждения списка** (в рамках политики `AGENTS.md`).

