# Генератор дашборда (Option 1)

Инструмент: `dashboard.generate_option1`

Выходы:
- `*.html` (самодостаточный дашборд)
- `*.json` (те же данные; удобно для diff/проверок)

## Типовые сценарии

### Один аккаунт

Аргументы (пример):
- `account_id`: profile id из `accounts.json`
- `date_from`: `YYYY-MM-DD`
- `date_to`: `YYYY-MM-DD` (рекомендуется: **вчера**)
- `output_dir`: куда писать файлы
- `dashboard_slug`: опционально, для более читаемых имён файлов
- `return_data=false`: чтобы не упираться в лимиты ответа в Claude Code

### Несколько аккаунтов

Используйте:
- `all_accounts=true`
или
- `account_ids=[...]`

Сгенерированный HTML содержит селектор аккаунта и переключает контент на стороне клиента.

## Примечания

- Если передан `output_dir`, инструмент пишет локальные `*.html` / `*.json` файлы. Если нужны нулевые side effects на файловую систему, не передавайте `output_dir`.
- Данные за “сегодня” в Direct/Metrica часто неполные; для ежедневного использования ставьте `date_to` = вчера.
- Leads/CPL на уровне кампаний могут считаться **best-effort** и иногда “гейтятся”, если фильтры атрибуции Metrica не проходят проверку (чтобы не показывать вводящие в заблуждение числа).

## Wordstat (опционально)

Можно включить подсказки ключевых фраз на основе Wordstat:
- `include_wordstat=true`
- Дополнительные настройки:
  - `wordstat_max_campaigns`
  - `wordstat_max_seed_phrases_per_campaign`
  - `wordstat_num_phrases`
  - `wordstat_max_candidates_per_campaign`
  - `wordstat_max_negatives_per_campaign`
  - `wordstat_language`
  - `wordstat_regions`, `wordstat_devices`

В multi-account режиме (`all_accounts=true` / `account_ids=[...]`) подсказки Wordstat считаются для выбранного аккаунта и переключаются вместе с селектором.

Dashboard Wordstat expansion cleans Direct keyword syntax (`!`, `+`, brackets, quotes) before calling Search API Wordstat. Candidate JSON can include phrases from both provider `results` and `associations`; `provider_sources` indicates the source type.

## Audience (опционально)

Можно включить блоки с сегментами и пересечениями Audience:
- `include_audience=true`

В multi-account режиме (`all_accounts=true` / `account_ids=[...]`) данные Audience считаются для выбранного аккаунта и переключаются вместе с селектором.
