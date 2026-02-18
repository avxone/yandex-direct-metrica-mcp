# PRO plug-in’ы (private)

В этом репозитории поддерживаются **приватные PRO plug-in’ы**, которые могут регистрировать дополнительные инструменты и handlers во время запуска (например, **BI Option 2**: датасеты + инкрементальный sync).

## Загрузка

Core обнаруживает plug-in’ы через Python entry points:
- group: `mcp_yandex_ad.plugins`

Docker-сборки могут устанавливать приватные plug-in’ы через:
- build arg `MCP_PLUGIN_PIP` в корневом `Dockerfile` (pip spec, например `package==1.2.3` или URL приватного индекса)

Пример (git URL, закреплено на тег):
```bash
docker build \
  --build-arg MCP_EDITION=pro \
  --build-arg MCP_PUBLIC_READONLY=false \
  --build-arg MCP_PLUGIN_PIP="git+https://github.com/<OWNER>/<PRIVATE_PLUGIN_REPO>.git@vX.Y.Z" \
  -t yandex-direct-metrica-mcp:pro .
```

Опционально, для локальной разработки без упаковки в пакет:
- `MCP_PLUGIN_MODULES=module[:attr],...`
  - если `:attr` не указан — используется `register`

## Plug-in API (минимальный контракт)

Plug-in может быть любым из:
- объект с `register(registry)`
- функция `register(registry)`
- factory-функция, возвращающая один из вариантов выше

`registry` предоставляет:
- `registry.add_tools(list[Tool])`
- `registry.add_tool_handler(name, handler)` где `handler(ctx, args) -> dict`
- `registry.add_prefix_handler(prefix, handler)` где `handler(ctx, name, args) -> dict`

Примечания:
- Доступность инструментов проверяется в runtime: если tool name отсутствует в `tools/list`, сервер отклоняет вызов.
- В public read-only режиме любые `dashboard.dataset.*` скрываются даже при наличии plug-in’а.

## BI Option 2 (примеры датасетов)

PRO BI plug-in может добавлять инструменты `dashboard.*`, например:
- `dashboard.schema`
- `dashboard.dataset.join_direct_vs_metrica_yclid_daily` (Metrica Logs API export + join по `yclid`/Direct click id; может вернуть `status=pending` и `request_id` для resume)
- `dashboard.sync.start` / `dashboard.sync.next` (NDJSON; при `pending` нужно повторить `sync.next`)
