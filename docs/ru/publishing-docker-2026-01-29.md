# Публикация (Docker + GHCR) — 2026-01-29 (обновлено для v1.0.0)

Проект публикует Docker образы в **GHCR** (GitHub Container Registry).

## Артефакты (Public vs Pro)

Public (read-only, safe-by-default):
- `ghcr.io/<OWNER>/yandex-direct-metrica-mcp:<tag>`
- `ghcr.io/<OWNER>/yandex-direct-metrica-mcp:latest` (stable public)

Pro (отдельный артефакт; планируется для платных подписчиков; пакет GHCR держим private):
- `ghcr.io/<OWNER>/yandex-direct-metrica-mcp-pro:<tag>`
- `ghcr.io/<OWNER>/yandex-direct-metrica-mcp-pro:latest` (только когда вы явно публикуете PRO)

## CI / Workflows

- Тесты: `.github/workflows/ci.yml` (pytest, blocking)
- Публикация Docker (public): `.github/workflows/docker-publish-public.yml`
  - триггеры: push в `main` и теги `v*`
  - `:latest` публикуется только при пуше тега
- Публикация Docker (pro): `.github/workflows/docker-publish-pro.yml`
  - триггеры: ручной `workflow_dispatch` или теги `pro-v*`

## Как релизить public

1) Убедитесь, что CI зелёный на `main`.
2) Создайте и запушьте тег:
   - `vX.Y.Z`
3) Public workflow соберёт и запушит:
   - `ghcr.io/<OWNER>/yandex-direct-metrica-mcp:vX.Y.Z`
   - `ghcr.io/<OWNER>/yandex-direct-metrica-mcp:latest`

## Как релизить PRO (ограниченный доступ)

Рекомендация:
- Держать package `yandex-direct-metrica-mcp-pro` в GHCR **private**.
- Публиковать PRO только по необходимости:
  - вручную (через `workflow_dispatch`), или
  - через тег `pro-vX.Y.Z`.

## Ручная публикация (опционально)

Если нужно запушить образ вручную с машины, используйте `docker buildx`.

Public:
```bash
export GHCR_OWNER="<OWNER>"
export VERSION="1.0.0"

echo "<GITHUB_PAT>" | docker login ghcr.io -u "$GHCR_OWNER" --password-stdin

docker buildx build --platform linux/amd64,linux/arm64 \
  --build-arg MCP_PUBLIC_READONLY=true \
  --build-arg MCP_EDITION=public \
  -t "ghcr.io/$GHCR_OWNER/yandex-direct-metrica-mcp:$VERSION" \
  -t "ghcr.io/$GHCR_OWNER/yandex-direct-metrica-mcp:latest" \
  --push .
```

Pro:
```bash
export GHCR_OWNER="<OWNER>"
export VERSION="1.0.0"

echo "<GITHUB_PAT>" | docker login ghcr.io -u "$GHCR_OWNER" --password-stdin

docker buildx build --platform linux/amd64,linux/arm64 \
  --build-arg MCP_PUBLIC_READONLY=false \
  --build-arg MCP_EDITION=pro \
  -t "ghcr.io/$GHCR_OWNER/yandex-direct-metrica-mcp-pro:$VERSION" \
  -t "ghcr.io/$GHCR_OWNER/yandex-direct-metrica-mcp-pro:latest" \
  --push .
```

## Подключение образов к Claude Code

Public:
```bash
claude mcp add yandex-direct-metrica-mcp -- \
  docker run --rm -i \
    --env-file /path/to/your/state/.env \
    -e MCP_ACCOUNTS_FILE=/data/accounts.json \
    -v /path/to/your/state:/data \
    ghcr.io/<OWNER>/yandex-direct-metrica-mcp:latest
```

Pro:
```bash
claude mcp add yandex-direct-metrica-mcp-pro -- \
  docker run --rm -i \
    --env-file /path/to/your/state/.env \
    -e MCP_ACCOUNTS_FILE=/data/accounts.json \
    -v /path/to/your/state:/data \
    ghcr.io/<OWNER>/yandex-direct-metrica-mcp-pro:<TAG>
```
