# PRO HTML Dashboard

Инструмент: `dashboard.generate_pro_html`

Назначение:
- генерировать самодостаточный `HTML + JSON` дашборд без отдельной БД
- переиспользовать существующий визуальный каркас Option 1
- добавить поверх него PRO-диагностику

Выходы:
- `*.html`
- `*.json`

## Что добавляется по сравнению с Option 1

PRO dashboard сохраняет текущую оболочку Option 1 и добавляет новые блоки на основе live MCP data:

- PRO summary counters
- campaign watchlist
- top search terms
- top keywords
- findings с severity и рекомендациями

В JSON эти данные лежат в `data.pro`.

## Типовые аргументы

Один аккаунт:
- `date_from`
- `date_to`
- `output_dir`
- `direct_client_login` или `account_id`
- `counter_id`, если он не резолвится автоматически

Настройки PRO-блоков:
- `max_campaigns`
- `max_keywords`
- `max_search_phrases`
- `max_findings`
- `include_wordstat`
- `include_audience`

## Текущие эвристики

Первая версия сфокусирована на прозрачной операционной диагностике:

- дорогие search phrases с низким качеством клика
- дорогие keywords с высоким bounce rate
- кампании со spend и без attributed leads
- кампании с ростом spend без роста leads
- UTMCampaign classification gaps

Это диагностические эвристики, а не автоматическое применение изменений.

## Локальный runner

Для локальной генерации из `.env` используйте helper script:

```bash
.venv/bin/python scripts/generate_dashboard_pro_html.py \
  --direct-client-login elama-16161182 \
  --counter-id 91450749 \
  --date-from 2026-04-12 \
  --date-to 2026-05-11 \
  --output-dir /private/tmp/yandexad-pro-dashboard-2026-05-12
```

## Примечания

- Инструмент PRO-only и скрыт из public read-only surface.
- Если передан `output_dir`, инструмент пишет локальные файлы и therefore side-effecting относительно файловой системы.
- Отдельный historical warehouse не нужен; дашборд строится из live reads за текущий и предыдущий периоды.
