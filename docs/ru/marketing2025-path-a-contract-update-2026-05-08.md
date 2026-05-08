# Обновление контрактов `yandex.ad` для потребителей из `Marketing2025` - 2026-05-08

## Назначение

Эта заметка описывает backend-изменения ответов, которые `Marketing2025` может начать использовать после релиза `yandex.ad` от 8 мая.

Фокус намеренно узкий:

- только поля и warning'и, важные для `Marketing2025`
- без обзора всего каталога инструментов
- без описания orchestration-логики

## 1. Диагностика special / no-structure кампаний

### Затронутые инструменты

- `direct.hf.get_campaign_summary`
- `direct.list_campaigns`

### `direct.hf.get_campaign_summary`

Когда у кампании нулевые структурные счётчики, но при этом есть живая доставка/перформанс, HF-ответ может включать:

- `result.campaign_type = "SPECIAL_NO_STRUCTURE"`
- `result.campaign_type_hint`
- `result.counts_applicable = false`
- `result.performance_signal`

HF envelope также может содержать:

- `warnings[].code = "campaign_type_special_no_structure"`

Как интерпретировать:

- не считайте `0/0/0` доказательством того, что кампания phantom или moot
- используйте `counts_applicable=false` как основной машинный сигнал, что структурные счётчики для этой кампании неавторитетны
- используйте `performance_signal` как доказательство, что живая доставка всё ещё есть

### `direct.list_campaigns`

Когда lookup по `Ids` не возвращает строк, `direct.list_campaigns` может подставить special campaign candidates на основе живого перформанса. В этом случае:

- `result.Campaigns[]` может содержать объекты с полями:
  - `Id`
  - `CampaignType`
  - `CountsApplicable`
  - `PerformanceSignal`
  - `Note`
- `result.Warnings[]` объяснит, что была сделана подстановка

Как интерпретировать:

- не считайте пустой исходный `campaigns.get` финальным результатом, если присутствуют substituted special candidates
- предпочитайте live MCP diagnostics вместо placeholder'ов `landing_map` вроде `"(not in snapshot)"`

## 2. Пагинация HF-отчётов Metrica и warning'и о truncation

### Затронутые инструменты

- `metrica.hf.report_landing_pages`
- `metrica.hf.report_utm_campaigns`
- `metrica.hf.report_geo`
- `metrica.hf.report_devices`

### Новое поведение

- если `limit` не передан, эти инструменты теперь автоматически пагинируют ответ и возвращают полный bounded result set
- если передан явный `limit` и он обрезает строки, HF envelope включает:
  - `warnings[].code = "metrica_rows_truncated"`

Как интерпретировать:

- отсутствие warning означает, что строки не были обрезаны явным лимитом вызывающей стороны
- если warning присутствует, downstream checks должны считать датасет частичным

## 3. Метаданные fallback для Wordstat batch mode

### Затронутый инструмент

- `wordstat.top_requests`

### Новое поведение

Если upstream Wordstat batch mode возвращает неожиданный тип ответа, сервер делает retry по одной фразе и возвращает:

- `fallback.mode = "single_phrase_loop"`
- `fallback.reason`
- `fallback.requested_phrases`
- `topRequestsByPhrase[]`

Как интерпретировать:

- downstream callers могут использовать ответ дальше вместо падения всего workflow
- если `fallback` присутствует, считайте ответ успешным, но деградированным

## 4. Совместимость `direct.report` / `direct.hf.report_keywords`

### Затронутые инструменты

- `direct.report`
- `direct.hf.report_keywords`

### Новое поведение

- `direct.hf.report_keywords` теперь использует корректный `CUSTOM_REPORT` field set на базе `Criterion`
- low-level `direct.report` теперь сразу валится, если `CUSTOM_REPORT` запрошен с `Keyword`

Как интерпретировать:

- для `CUSTOM_REPORT` используйте `Criterion`, при необходимости вместе с `CriterionId` и `CriterionType`
- не полагайтесь на старые предположения о custom-report пресетах на базе `Keyword`

## 5. Семантика read-only override для Direct login

### Затронутые инструменты

- read-only вызовы `direct.*`, включая raw read helpers

### Новое поведение

- для read-only Direct вызовов неизвестный `account_id` может интерпретироваться как `direct_client_login`
- read-only вызовы также могут override'ить login из профиля через явный `direct_client_login`

Как интерпретировать:

- это предназначено только для agency/multi-login read-сценариев
- write flows должны по-прежнему использовать явный валидированный account/profile resolution

## 6. Side-effect контракт `dashboard.generate_option1`

### Новое поведение

- контракт инструмента больше не помечает `dashboard.generate_option1` как read-only, если используется `output_dir`

Как интерпретировать:

- если задан `output_dir`, инструмент пишет локальные HTML/JSON артефакты
- если вызывающей стороне нужны нулевые локальные filesystem side effects, не передавайте `output_dir`

## Migration Checklist для `Marketing2025`

1. В campaign validity предпочитайте live MCP diagnostics вместо placeholder'ов из `landing_map`.
2. Используйте `counts_applicable=false` как сигнал первого класса.
3. Считайте `metrica_rows_truncated` признаком partial coverage.
4. Принимайте fallback-ответы `wordstat.top_requests` вместо жёсткого падения на batch degradation.
5. Уберите предположение о совместимости `CUSTOM_REPORT` с `Keyword`.
