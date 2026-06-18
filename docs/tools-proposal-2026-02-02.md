# Предложение по списку MCP-инструментов — Wordstat (public + pro) — 2026-02-02

Цель: добавить **Yandex Wordstat API** в MCP `yandex-direct-metrica-mcp` так, чтобы:
- в **public** режиме были доступны **read-only** инструменты Wordstat (сырые + HF),
- а любые изменения в Direct (добавление ключей/минус-слов и т.п.) оставались **только в pro**.

Важно: Wordstat API, как правило, включает **создание/получение отчётных данных**. Это не изменяет рекламные сущности Direct,
но является операционным сайд‑эффектом. Для public-контракта считаем это допустимым, если явно задокументировано.

## Термины (read-only)

В public 1.x:
- **Запрещено**: любые Direct write (create/update), любые accounts write (upsert/delete), любые escape hatches (`*.raw_call`).
- **Разрешено**: чтение Direct/Metrica, формирование дашборда, Wordstat отчётные запросы (получение статистики/подсказок).

## Уровень G — Wordstat (сырые инструменты)

### 1) `wordstat.user_info`
- Назначение: проверка доступа/учётки Wordstat.
- Параметры: нет.
- Возврат: raw JSON ответа API.

### 2) `wordstat.get_regions_tree`
- Назначение: получить дерево регионов Wordstat.
- Параметры: нет.
- Возврат: raw JSON.

### 3) `wordstat.regions`
- Назначение: получить частотности по регионам.
- Параметры:
  - `phrase` (string, required)
  - `region_type` (string, optional) — `cities|regions|all` (как в API)
  - `devices` (string[], optional)
- Возврат: raw JSON.

### 4) `wordstat.dynamics`
- Назначение: получить динамику частотности по времени.
- Параметры:
  - `phrase` (string, required)
  - `from_date` (string, required) — `YYYY-MM` (как в API `fromDate`)
  - `to_date` (string, optional) — `YYYY-MM` (как в API `toDate`)
  - `period` (string, optional) — `monthly|weekly|daily` (как в API)
  - `regions` (int[], optional)
  - `devices` (string[], optional)
- Возврат: raw JSON.

### 5) `wordstat.top_requests`
- Назначение: топ запросов по фразе (включая связанные запросы).
- Параметры:
  - `phrase` (string) **или** `phrases` (string[], up to 128)
  - `regions` (int[], optional)
  - `num_phrases` (int, optional, max 2000)
  - `devices` (string[], optional)
- Возврат: raw JSON.

## Уровень H — Wordstat HF (public)

HF-инструменты работают без изменений Direct/Metrica и не требуют `apply=true`.

### 1) `wordstat.hf.suggest_keywords`
- Назначение: сгенерировать кандидаты ключевых фраз по seed-фразам.
- Вход:
  - `seed_phrases` (string[], required)
  - `regions` (int[], optional)
  - `num_phrases` (int, optional, default 50)
  - `max_seed_phrases_per_call` (int, optional, default 8)
  - `cursor` (string, optional) — для пошагового выполнения (base64 JSON)
  - `max_candidates` (int, optional, default 200)
- Выход:
  - `status`: `ok|pending|error`
  - `result.candidates[]`: `{phrase, score, sources[]}`
  - при `pending`: `preview.cursor` для продолжения (opaque base64 JSON)

### 2) `wordstat.hf.suggest_negative_keywords`
- Назначение: предложить кандидаты в минус-слова по списку фраз (из Wordstat/кампаний).
- Вход:
  - `phrases` (string[], required)
  - `language` (string, optional, default `ru`)
  - `max_candidates` (int, optional, default 100)
- Выход:
  - `status`: `ok|error`
  - `result.negatives[]`: `{token, reason, count}`

## Pro: применение рекомендаций (вне public-контракта)

В pro можно добавить `direct.hf.apply_wordstat_suggestions` / `direct.hf.apply_negative_suggestions` с привычными guardrails:
`MCP_WRITE_ENABLED=true`, `HF_WRITE_ENABLED=true`, sandbox-only и т.п.

## Public env-матрица (норма)

Wordstat через Yandex Search API:
- `YANDEX_SEARCH_API_FOLDER_ID`
- `YANDEX_SEARCH_API_API_KEY` **или** `YANDEX_SEARCH_API_IAM_TOKEN`

Ограничители:
- `MCP_WORDSTAT_RATE_LIMIT_RPS` (0=disabled)
- `MCP_WORDSTAT_ENABLED` (default true)

Игнорируются в public (всегда false/disabled):
- `MCP_WRITE_ENABLED`
- `HF_WRITE_ENABLED`
- `HF_DESTRUCTIVE_ENABLED`
- `MCP_ACCOUNTS_WRITE_ENABLED`
- любые `*.raw_call`
