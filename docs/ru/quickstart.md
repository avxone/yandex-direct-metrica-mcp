# Быстрый старт (Docker + Claude Code)

Гайд предполагает, что вы используете **Docker** (рекомендуется) и подключаетесь через **Claude Code**.

## Требования

- Docker Desktop
- Claude Code CLI (`claude`)
- OAuth‑токен(ы) Яндекса с доступом к:
  - Direct API (для нужных `Client-Login`)
  - Metrica API (для нужных счётчиков)
  - (опционально) Audience API
  - (опционально) Wordstat API

## 1) Создайте state‑папку

Выберите папку на своей машине, где будет храниться состояние/конфиги:
- Пример: `/path/to/mcp-state/yandex-direct-metrica-mcp`

Внутри создайте `accounts.json`:
```json
{
  "accounts": [
    {
      "id": "example_project",
      "name": "Example project",
      "direct_client_login": "example-client-login",
      "metrica_counter_ids": ["12345678"]
    }
  ]
}
```

Примечания:
- `id` должен быть **уникальным**. Если один `direct_client_login` соответствует нескольким сайтам/счётчикам — заведите несколько профилей с разными `id`.
- `metrica_counter_ids` — allow‑list счётчиков для профиля (используется в dashboard + join’ах).

## 2) Создайте `.env`

Скопируйте `.env.example` и заполните:
- OAuth‑токены/refresh tokens
- дефолты Direct (например, `YANDEX_DIRECT_CLIENT_LOGIN`, опционально `YANDEX_DIRECT_CLIENT_LOGINS`)
- allow‑list счётчиков Метрики (`YANDEX_METRICA_COUNTER_IDS`)

Рекомендованные дефолты для public/read‑only:
- `MCP_WRITE_ENABLED=false`
- `HF_WRITE_ENABLED=false`
- `MCP_PUBLIC_READONLY=true`

## 3) Добавьте MCP в Claude Code

Соберите локально:
```bash
docker build -t yandex-direct-metrica-mcp:local .
```

Примечания:
- `docker build ...` по умолчанию собирает **public read‑only** образ.
- Если вам действительно нужен локальный PRO образ, собирайте так:
  - `docker build --build-arg MCP_EDITION=pro --build-arg MCP_PUBLIC_READONLY=false -t yandex-direct-metrica-mcp:pro .`
  - Если нужен BI Option 2 — установите приватный PRO plug-in на этапе сборки через `--build-arg MCP_PLUGIN_PIP="..."` (см. `docs/ru/pro-plugin.md`).

Добавьте в Claude Code:
```bash
claude mcp add yandex-direct-metrica-mcp -- \
  docker run --rm -i \
    --env-file /path/to/your/.env \
    -e MCP_ACCOUNTS_FILE=/data/accounts.json \
    -v /path/to/your/state:/data \
    yandex-direct-metrica-mcp:local
```

Проверьте:
```bash
claude mcp list
```

## 4) Первые проверки

В Claude Code попробуйте:
- «List accounts from the server.»
- «Сгенерируй `dashboard.generate_option1` по всем аккаунтам за последние 30 дней **до вчера**, сохрани в `/path/to/dashboards`, `all_accounts=true`, `return_data=false`, и верни путь к HTML.»
