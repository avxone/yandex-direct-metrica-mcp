# Предложение по списку MCP-инструментов — Competitors (A+D) + Read-only Pressure — 2026-02-03

Цель: сделать “рабочий инструмент” для SEO‑аналитиков/маркетологов без покупки сторонних баз:
- **D (Content → Semantics)**: строим семантику конкурентов из их сайтов (server-fetch).
- **A (Read-only Pressure)**: оцениваем “сложность/дороговизну входа” по **вашим** данным Direct/Metrica (без попыток узнать “ставки конкурентов”).

Важно:
- Мы **не** обещаем “ставки конкурентов”. Мы даём:
  - список конкурентов/страниц/тем/семантики,
  - регионально‑устройственную детализацию спроса (Wordstat),
  - давление рынка через фактические CPC/CTR/показы/расход (и качество из Metrica).
- В следующих релизах планируется **Bid Sweep** (эксперименты) — точнее, но это write (pro-only).

---

## Термины (public vs pro)

В public 1.x:
- Разрешено: чтение Direct/Metrica/Wordstat, server-fetch конкурентов **только при жёстких guardrails** (allowlist доменов), HF read-only.
- Запрещено: любые Direct write, любые “эксперименты” (bid sweep), любые escape hatches (`*.raw_call`).

В pro 1.x:
- Разрешены bid sweep инструменты и любые write только при `apply=true` + write guardrails.

---

## Уровень G — Competitors raw (public, read-only)

### 1) `competitors.discover_urls`
Назначение: получить список URL конкурента для анализа (через `sitemap.xml`, `robots.txt`, главную).
- Вход:
  - `domains` (string[], required)
  - `max_urls` (int, default 200)
  - `prefer_sitemap` (bool, default true)
  - `include_patterns?` / `exclude_patterns?` (string[])
- Выход: raw JSON `{domain, urls[], sitemaps[], warnings[]}`

### 2) `competitors.fetch_pages`
Назначение: server-fetch HTML страниц (без JS/рендера).
- Вход:
  - `urls` (string[], required)
  - `max_pages` (int, default 50)
  - `timeout_ms` (int, default 8000)
  - `max_bytes_per_page` (int, default 1_000_000)
  - `concurrency` (int, default 4)
  - `respect_robots` (bool, default true)
- Выход: raw JSON
  - `pages[]`: `{url, status, content_type, fetched_at, bytes, html? | text?}`
  - `failures[]`: `{url, error_code, message}`

### 3) `competitors.extract_signals`
Назначение: извлечь “сигналы” из HTML: title/h1/h2, категории, товары/услуги, цены (если есть), регионы, контакты, микроразметку.
- Вход:
  - `pages[]` (url + html/text, required)
  - `mode` (ecom|leads|mixed, default mixed)
  - `language` (string, default ru)
- Выход: raw JSON `{signals_by_url, extracted_entities, debug}`

Примечание: это raw/extraction output без кластеризации.

---

## Уровень H — Competitors HF (public, read-only)

HF‑принципы:
- small inputs
- быстрые результаты, без тяжёлой нормализации
- всегда возвращаем `raw_refs`/`debug` для трассировки

### 1) `competitors.hf.crawl_plan`
Назначение: составить “план обхода” (что и сколько качать) под ограничения.
- Вход:
  - `domains` (string[], required)
  - `mode` (ecom|leads|mixed, default mixed)
  - `max_pages` (int, default 100)
  - `prefer_sitemap` (bool, default true)
- Выход:
  - `plan.urls[]`
  - `plan.meta.sitemaps[]`
  - `warnings[]` (например: “нет sitemap”, “слишком много URL”, “заблокировано robots”)

### 2) `competitors.hf.extract_topics`
Назначение: преобразовать страницы в темы/категории/офферы.
- Вход:
  - `domains` (string[] | optional) — если задано, tool сам делает discover+fetch под лимитами
  - `urls` (string[] | optional) — если хотим явно контролировать
  - `mode` (ecom|leads|mixed, default mixed)
  - `max_pages` (int, default 50)
  - `max_topics` (int, default 200)
  - `include_evidence` (bool, default true)
- Выход:
  - `topics[]`: `{topic, type(category|product|service|brand|geo|offer), score, evidence_urls[]}`
  - `meta`: `{pages_fetched, pages_failed, domains}`
  - `raw_refs`

### 3) `competitors.hf.build_seeds`
Назначение: собрать семантические “seed” фразы для Wordstat.
- Вход:
  - `topics[]` (required)
  - `brand_terms?` (string[])
  - `stopwords?` (string[])
  - `max_seeds` (int, default 200)
- Выход:
  - `seeds[]`: `{phrase, intent(brand|nonbrand|commercial|info), sources[]}`
  - `negatives_candidates[]`: `{token, reason}`

### 4) `competitors.hf.wordstat_expand`
Назначение: развернуть seeds через Wordstat (регионы/устройства).
- Вход:
  - `seed_phrases` (string[], required)
  - `regions?` (int[])
  - `devices?` (string[])
  - `strategy` (top_requests|dynamics_then_top, default top_requests)
  - `num_phrases` (int, default 200)
- Выход:
  - `keywords[]`: `{phrase, sources[], wordstat:{...}}`
  - `raw_refs`: `{wordstat.top_requests, wordstat.dynamics, wordstat.regions}`

### 5) `competitors.hf.cluster_keywords`
Назначение: кластеризовать семантику (для поиска и ecom/лидов).
- Вход:
  - `keywords` (string[] | required) **или** `keywords[]` (objects)
  - `cluster_mode` (intent|topic|landing, default intent)
  - `max_clusters` (int, default 100)
- Выход:
  - `clusters[]`: `{cluster_id, label, intent, phrases[], priority_score, notes?}`

---

## Уровень H — Direct HF: Read-only Pressure (public)

### 1) `direct.hf.pressure_report`
Назначение: оценить “давление/дороговизну” по вашим данным Direct, в разрезе:
- поиск/РСЯ,
- регионы/устройства,
- кластеры (семантика).

Вход:
- `account_id?` (string) — резолв `direct_client_login` и дефолтных counters
- `direct_client_login?` (string)
- `date_from` (YYYY-MM-DD, required)
- `date_to` (YYYY-MM-DD, required)
- `grain` (day|week|month, default day)
- `placement` (search|rsya|all, default all)
- `regions?` (int[])
- `devices?` (string[])
- `clusters?` (array, optional): `[{cluster_id, phrases[]}]`
- `campaign_ids?` / `adgroup_ids?` (optional) — если хотим “pressure” только по текущей структуре

Выход:
- `status`: `ok|partial|error`
- `result.by_cluster[]`:
  - `{cluster_id, impressions, clicks, cost_rub, ctr, cpc_rub, cpm_rub?, coverage}`
- `result.by_cluster_region_device[]` (optional):
  - `{cluster_id, region_id?, device?, placement?, impressions, clicks, cost_rub, cpc_rub, ctr}`
- `meta.coverage_notes`:
  - как именно кластеры сопоставлены с Direct (по keyword text / по UTM / по структуре)
  - что не попало в покрытие
- `raw_refs`: параметры вызовов `direct.report` и/или `direct.list_keywords` (best-effort)

### 2) `join.hf.cluster_quality_metrica` (optional, public)
Назначение: добавить “качество” из Metrica по тем же кластерам (чтобы не оптимизировать “дорого, но мусор”).

Вход:
- `counter_id` (int, required)
- `goal_ids?` (int[])
- `date_from`, `date_to`
- `clusters[]` (required)
- `regions?`, `devices?`
- `scope` (direct_attributed|all, default direct_attributed)

Выход:
- `status`: `ok|partial|error`
- `result.by_cluster[]`: `{cluster_id, visits, users, bounce_rate, depth, avg_visit_duration_seconds, goal_reaches?}`
- `meta.coverage_notes`
- `raw_refs`: `metrica.report` params

---

## Уровень F — Dashboard integration (рекомендовано)

Цель: дать BI/дашборду стабильные датасеты и инкрементальный sync.

### Датасеты (public)
- `dashboard.dataset.competitor_topics`
  - `{domain, url?, topic, type, score, evidence_url?}`
- `dashboard.dataset.competitor_seeds`
  - `{domain, seed_phrase, intent, sources[]}`
- `dashboard.dataset.wordstat_keywords`
  - `{seed_phrase|cluster_id, phrase, region_id?, device?, freq?, dynamics?}`
- `dashboard.dataset.market_pressure`
  - `{cluster_id, date, region_id?, device?, placement?, impressions, clicks, cost_rub, cpc_rub, ctr, coverage}`
- `dashboard.dataset.cluster_quality`
  - `{cluster_id, date?, visits, users, bounce_rate, depth, avg_visit_duration_seconds, goal_reaches?}`

### Инкрементальный sync (public)
- `dashboard.sync.start` / `dashboard.sync.next`
  - cursor/watermark, NDJSON-friendly, bounded batch size

---

## Pro roadmap: Bid Sweep (следующие релизы)

Планируемые pro-only инструменты (write, apply=true, sandbox-only по умолчанию):
- `direct.hf.bid_sweep_plan` (preview-only)
- `direct.hf.bid_sweep_run` (apply=true)
- `direct.hf.bid_sweep_analyze` (read-only)

Guardrails:
- `MCP_WRITE_ENABLED=true`
- `MCP_WRITE_SANDBOX_ONLY=true` + `YANDEX_DIRECT_SANDBOX=true`
- `HF_ENABLED=true` + `HF_WRITE_ENABLED=true`
- бюджетные лимиты (`budget_cap_rub`, `max_steps`, `max_days`)

---

## Guardrails для server-fetch (обязательные)

Чтобы server-fetch не превратился в “сканер интернета”, вводим явные ограничения:
- `MCP_COMPETITORS_FETCH_ENABLED` (default false)
- `MCP_COMPETITORS_ALLOWED_DOMAINS` (CSV allowlist, required when enabled)
- `MCP_COMPETITORS_RATE_LIMIT_RPS` (0=disabled)
- `MCP_COMPETITORS_MAX_PAGES_PER_CALL`
- `MCP_COMPETITORS_MAX_BYTES_PER_PAGE`
- `MCP_COMPETITORS_RESPECT_ROBOTS` (default true)
- `MCP_COMPETITORS_CACHE_TTL_SECONDS` (опционально)

Логи:
- логируем только URL/статусы/тайминги, без хранения содержимого страниц
- не логируем случайно извлечённые персональные данные (если встречаются на страницах)

---

## Согласование (explicit approval)
Документ — черновик. Добавление новых инструментов `competitors.*`, `competitors.hf.*`, `direct.hf.pressure_report`, `dashboard.dataset.*` — только после явного утверждения списка (политика `AGENTS.md`).

