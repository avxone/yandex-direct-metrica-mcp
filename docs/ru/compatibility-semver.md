# Совместимость / SemVer policy

Проект следует SemVer и фиксирует явный **tool contract**.

## Public contract (1.x)

Public‑контракт — это поверхность `tools/list` для public edition:
- `name`
- `description`
- `inputSchema` (включая дефолты)

Канонический снапшот:
- `tests/snapshots/public_tools_v1.json`

## Что считается breaking change (public)

Breaking (требует 2.0.0):
- Удаление public tool.
- Переименование public tool.
- Изменение `inputSchema` (типы, required‑поля, enums, defaults).
- Изменение `description` (так как оно входит в snapshot‑контракт).

Non‑breaking (допустимо в 1.x):
- Bugfix’ы без изменения tool‑контракта.
- Добавление **новых инструментов** (minor версия).
- Добавление **новых опциональных полей в output** (output не фиксируется контрактом в v1.0.0).

## Депрекации

Так как `description` фиксируется снапшотом, депрекации делаем так:
- Вводим новый инструмент (например, `..._v2`) и оставляем старый до конца ветки 1.x.
- Удаляем старый инструмент только в 2.0.0.

## Pro contract

Поверхность PRO‑инструментов по умолчанию не фиксируется снапшотом.
Если захотим гарантировать SemVer и для PRO, добавим отдельный snapshot и отдельную policy.
