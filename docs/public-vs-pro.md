# Public vs Pro (модель доступа к инструментам)

Цель: публиковать безопасную **public** сборку для **read‑only** аналитики и держать write‑операции (особенно Direct) в отдельной **Pro** дистрибуции.

## Public (read‑only)

Рекомендованная настройка:
- `MCP_PUBLIC_READONLY=true`

Эффект:
- Write‑инструменты скрыты/заблокированы (Direct create/update, escape‑hatch raw calls).
- Режим рассчитан на отчёты, join’ы и генерацию BI‑дашборда.
 - BI Option 2 (`dashboard.schema`, `dashboard.dataset.*`, `dashboard.sync.*`) **не** входит в public поверхность и поставляется отдельным PRO plug-in.

Рекомендованная модель артефактов (релиз 1.0.0):
- Public Docker image: `ghcr.io/<OWNER>/yandex-direct-metrica-mcp:<tag>` и `:latest`
  - Safe‑by‑default: public edition форсирует read‑only даже если env‑переменные настроены неверно.
- Pro Docker image: `ghcr.io/<OWNER>/yandex-direct-metrica-mcp-pro:<tag>` (отдельный артефакт)

См. также:
- `docs/public-mode.md` (спецификация public‑контракта)
- `docs/compatibility-semver.md` (политика совместимости)

## Pro (полный контур)

Рекомендованная настройка:
- `MCP_PUBLIC_READONLY=false`

Эффект:
- Доступен полный набор инструментов (всё ещё под guardrails: `MCP_WRITE_ENABLED`, sandbox‑only политики и т.д.).
 - Доступен BI Option 2 (датасеты + инкрементальный sync для BI/warehouse пайплайнов) **через PRO plug-in**.
- Доступны HF write инструменты (guarded `apply=true`) — например, Direct plan/apply и CRUD целей в Метрике.

## Зачем делить

- Меньше риск для public пользователей (нет “случайных” записей).
- Public поверхность меньше и проще сопровождать.
- Можно сделать платный/pro слой без изменения архитектуры ядра.
