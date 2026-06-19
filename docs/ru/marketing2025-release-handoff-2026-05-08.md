# Handoff для Marketing2025 после релиза - 2026-05-08

## Назначение

Этот handoff закрывает сторону `yandex.ad` по совместному разбору от 2026-05-07 и фиксирует, на что `Marketing2025` теперь может опираться после релиза `v2.0.10`.

Использовать этот документ как актуальную точку правды по:

- статусу релиза
- статусу MCP-образов
- инструментам и контрактам, важным для `Marketing2025`
- оставшемуся совместному шагу валидации

## Коротко

Релиз `yandex.ad` `v2.0.10` опубликован.

Исправления MCP-стороны, найденные в разборе 2026-05-07, уже shipped, public и PRO Docker publish workflow завершились успешно, а локальный путь `:dev`, который использует `Marketing2025`, выровнен на проверенный PRO-образ с установленным BI plug-in.

Состояние на 2026-05-08:

- `Marketing2025` не нужны дополнительные изменения кода, чтобы начать потреблять новые special-campaign diagnostics, уже подготовленные у них в campaign validity
- следующая живая MCP-сессия `Marketing2025`, которая резолвит `yandex-direct-metrica-mcp-pro:dev`, должна поднять новый локальный образ
- главный оставшийся cross-repo шаг это совместный replay / pipeline validation run

## Что вышло в `yandex.ad`

Релиз:

- `v2.0.10`

Основной артефакт:

- [Release notes](../releases/v2.0.10.md)

Изменения, которые важны для `Marketing2025`:

- diagnostics для special / no-structure campaigns в `direct.hf.get_campaign_summary`
- special-campaign substitution / warning поведение в `direct.list_campaigns`
- автоматическая пагинация в затронутых `metrica.hf.report_*`, если `limit` не передан
- warnings о truncation для Metrica HF report calls с явным `limit`
- fallback для `wordstat.top_requests`
- исправление совместимости `direct.hf.report_keywords`
- явная валидация `Keyword` vs `Criterion` в low-level `direct.report`
- read-only Direct login override для agency read сценариев
- исправленный contract metadata для `dashboard.generate_option1`, чтобы инструмент больше не публиковался как read-only, если `output_dir` вызывает запись в файловую систему

Связанный consumer note:

- [Contract update for Marketing2025 - 2026-05-08](marketing2025-path-a-contract-update-2026-05-08.md)

## Статус публикации

Выполнено 2026-05-08:

- push в `main`
- тег `v2.0.10`
- тег `pro-v2.0.10`
- создан GitHub release для `v2.0.10`
- успешно завершён public Docker publish workflow
- успешно завершён PRO Docker publish workflow

Результат:

- public release path опубликован
- PRO release path опубликован
- локальный PRO+BI validation image тоже был отдельно собран и проверен

## Статус валидации

Релиз был провалидирован на стороне `yandex.ad` до handoff.

Что проверено:

- `pytest -q` passed
- public Docker image прошёл smoke test с реальными credentials
- локальный PRO image с установленным BI plug-in показал ожидаемую dashboard schema / dataset / sync поверхность
- существующий `Marketing2025` Docker QA runner прошёл против:
  - локального public image
  - локального PRO+BI image

Наблюдаемый итог QA:

- нет P0 release blockers
- нет P1 warnings
- нет schema-lint violations

Важная оговорка по scope:

- quick QA matrix не прогоняет каждый PRO BI dataset tool
- подтверждённый результат здесь такой:
  - release surface корректный
  - core MCP workflows проходят
  - dashboard / join / Direct / Metrica / Wordstat / Audience проверки проходят

## Локальный путь для Marketing

Исторически `Marketing2025` ссылался на локальный MCP server как:

- `ydm-mcp-pro-dev`
- Docker image reference: `yandex-direct-metrica-mcp-pro:dev`

Чтобы не требовать немедленного переписывания конфигов, проверенный локальный PRO image с установленным BI plug-in был ретегнут в:

- `yandex-direct-metrica-mcp-pro:dev`

Это означает:

- существующее локальное имя dev-образа теперь указывает на проверенный `2.0.10` PRO+BI image
- если старый контейнер не запущен, следующая MCP-сессия может поднять его без смены имени образа

Состояние в момент handoff:

- ни один Yandex MCP container не был запущен

Практический вывод:

- следующая локальная сессия `Marketing2025` должна чисто поднять новый `:dev` image
- если какой-то клиент уже держит старый MCP process, перед replay стоит перезапустить эту сессию

## Что `Marketing2025` может использовать уже сейчас

### Campaign validity

`Marketing2025` теперь может опираться на выпущенные MCP-поля, описанные здесь:

- [Contract update for Marketing2025 - 2026-05-08](marketing2025-path-a-contract-update-2026-05-08.md)

Главные сигналы:

- `campaign_type = "SPECIAL_NO_STRUCTURE"`
- `counts_applicable = false`
- warning code `campaign_type_special_no_structure`
- special-candidate substitution данные из `direct.list_campaigns`

Это соответствует уже подготовленной логике `Marketing2025`, где live MCP diagnostics имеют приоритет над registry fallback, если новые поля присутствуют.

### Metrica collectors

`Marketing2025` теперь может считать, что:

- отсутствие `limit` в затронутых HF Metrica tools означает auto-pagination
- явная truncation от caller limit теперь surfaced как warning, а не остаётся silent

### Wordstat collectors

`Marketing2025` теперь может трактовать fallback-ответы `wordstat.top_requests` как успешный degraded result, а не как hard failure.

### Dashboard contract

`Marketing2025` не использует `dashboard.generate_option1` как read-only contract signal, но metadata теперь корректна и больше не вводит в заблуждение.

## Что ещё осталось между репозиториями

### 1. Совместный replay validation

Всё ещё требуется:

- заново прогнать целевой workflow / replay `Marketing2025` против выпущенного MCP image path
- подтвердить, что special-campaign validity path корректно работает end-to-end в реальном pipeline, а не только в unit tests и MCP-side QA

Это главный оставшийся cross-repo шаг из разбора 2026-05-07.

### 2. PR от Marketing в `yandex.ad/docs/`

От `Marketing2025` всё ещё ожидается:

- PR Path A input file в `yandex.ad/docs/` до `2026-05-18`

### 3. Необязательное усиление

Не блокирует этот релиз, но полезно:

- расширить PRO BI QA matrix так, чтобы она напрямую вызывала больше `dashboard.dataset.*` tools
- добавить replay-specific artifact bundle для совместного validation run

## Итог handoff

`yandex.ad` больше не является блокирующей стороной по MCP-дефектам из разбора 2026-05-07.

Текущее состояние:

- released
- published
- locally validated
- locally aligned с `Marketing2025` `:dev` image path

Дальше точка принятия решения переходит к совместному replay / validation step на стороне workflow `Marketing2025`.
