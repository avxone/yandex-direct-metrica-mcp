# Proposed MCP tools — Auth UX (pro) + Write Confirm (pro) — 2026-02-04

Цель: в следующем релизе добавить **pro-only** инструменты:
- для упрощения OAuth (получение токенов без хранения на стороне MCP),
- для безопасных write‑операций через обязательный **two‑phase** режим: “plan → confirm”.

Важно:
- Эти инструменты **не входят** в public read‑only контракт.
- Инструменты Auth возвращают секреты (токены). Использовать только в безопасной среде.

---

## Термины (public vs pro)

Public 1.x:
- Запрещено: любые write (Direct/Metrica/Audience), любые accounts write, любые “escape hatch” write вызовы.
- Разрешено: read-only аналитика, отчёты, дашборды, Wordstat отчётные запросы.

Pro 1.x:
- Разрешены write‑инструменты **только при включённых guardrails** и (в новом дизайне) только после явного подтверждения через `write.confirm`.

---

## PRO: Auth UX tools (no storage)

### 1) `auth.start` (pro-only)
Назначение: сформировать `authorize_url` для OAuth и вернуть `state` (CSRF).

Guardrails:
- Доступно только при `MCP_AUTH_TOOLS_ENABLED=true`.
- Не сохраняет токены/код на диск.
- Не логирует секреты.

Вход:
- `provider` (string, optional, default `yandex`) — на будущее, если появятся отдельные provider flows.
- `client_id` (string, optional) — иначе берём из env (`YANDEX_CLIENT_ID` / `YANDEX_AUDIENCE_CLIENT_ID`).
- `redirect_uri` (string, optional) — иначе env (`YANDEX_REDIRECT_URI` / …) или дефолт `https://oauth.yandex.ru/verification_code`.
- `scopes` (string[], optional) — иначе env (`YANDEX_SCOPES` / …).
- `purpose` (string, optional): `direct_metrica|audience` (чтобы выбирать env‑ключи и подсказки).

Выход:
- `status`: `ok|error`
- `result.authorize_url` (string)
- `result.state` (string) — opaque CSRF token
- `result.redirect_uri` (string)
- `result.scopes` (string[])
- `result.env_keys` (object) — какие env‑ключи ожидаются для данного `purpose`

### 2) `auth.exchange_code` (pro-only)
Назначение: обменять `code` на токены и вернуть результат + готовый `.env` блок.

Guardrails:
- Доступно только при `MCP_AUTH_TOOLS_ENABLED=true`.
- Не сохраняет токены/код на диск.
- Не логирует секреты.
- Возвращает секреты в ответе (caller должен понимать риск утечки в чате).

Вход:
- `purpose` (string, required): `direct_metrica|audience`
- `code` (string, required)
- `state` (string, optional) — если используем `auth.start` + state validation (внутри tool; no persistence)
- `client_id` / `client_secret` / `redirect_uri` (optional; default from env keys for given purpose)

Выход:
- `status`: `ok|error`
- `result.tokens`: `{access_token, refresh_token?, expires_in?, token_type?}`
- `result.env_block` (string) — ready-to-paste `.env` (includes client_id/client_secret/refresh/access/redirect_uri)
- `result.warnings[]` — например: “refresh_token empty”, “token_type missing”

Примечание: state‑валидация возможна только в рамках одной tool‑сессии без хранения. Если это сложно/ломает UX,
можно ограничиться тем, что `auth.start` возвращает state “для клиента”, а `auth.exchange_code` его не проверяет.

---

## PRO: Two-phase write confirm (B2)

### 1) `write.confirm` (pro-only)
Назначение: выполнить ранее “запланированную” write‑операцию по `confirm_token`.

Guardrails:
- Доступно только при `MCP_TWO_PHASE_WRITES=true` (или default-on в pro).
- Single-use token, short TTL (например 5 минут).
- Повторно проверяет все write guardrails:
  - public_readonly (must be false)
  - `MCP_WRITE_ENABLED=true`
  - sandbox-only (если включено)
  - `HF_WRITE_ENABLED=true` / `HF_DESTRUCTIVE_ENABLED=true` где применимо

Вход:
- `confirm_token` (string, required)

Выход:
- `status`: `ok|error`
- `result.executed_tool` (string)
- `result.executed_args` (object, optional, redacted)
- `result.output` (object) — реальный ответ исходного write‑tool

### Планирование (как появляется `confirm_token`)

Любой write‑tool в pro режиме при включённом `MCP_TWO_PHASE_WRITES` должен работать так:
- 1-й вызов: возвращает `status=planned`, `confirm_token`, `plan`, `raw_refs` (без выполнения write).
- 2-й вызов: `write.confirm(confirm_token)` выполняет write и возвращает `status=ok`.

---

## Public/Pro включение

Public:
- Эти инструменты скрыты из `tools/list` и заблокированы на runtime.

Pro:
- Показываются в `tools/list` только если включены соответствующие флаги:
  - `MCP_AUTH_TOOLS_ENABLED=true` (для auth.*)
  - `MCP_TWO_PHASE_WRITES=true` (для write.confirm и поведения “planned→confirm”)
