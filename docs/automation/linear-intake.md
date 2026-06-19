# Linear Intake Harness

This repo uses Linear as the work queue for Symphony-driven agent tasks. The intake harness lets Codex turn a local draft or prompt into a structured Linear issue without manual copy/paste.

## Safety Model

- `LINEAR_API_KEY` is read from the environment only.
- The default target state is `Backlog`, so Symphony will not run the task until a human moves it to `Todo`.
- The default dispatch label is `symphony`.
- The script never reads Yandex credentials.
- Use `--dry-run` before `create` when shaping a new task.

## Local Config

Keep local Linear routing outside this repo:

```json
{
  "teamId": "3460d8b7-42f7-498a-8917-784237f318ff",
  "projectId": "aadd4324-b828-4dd8-a0ca-eebd65b16683",
  "defaultState": "Backlog",
  "defaultLabels": ["symphony"]
}
```

Recommended path:

```bash
/path/to/Symphony_yaad/linear.yandexad.json
```

## Create From A Draft

```bash
set -a
. /path/to/Symphony_yaad/.env
set +a

python scripts/linear_issue.py preview \
  --config /path/to/Symphony_yaad/linear.yandexad.json \
  --from docs/wordstat-search-api-hardening-issue-2026-06-19.md \
  --title "Harden Wordstat Search API regions and associations handling" \
  --labels symphony,wordstat

python scripts/linear_issue.py create \
  --config /path/to/Symphony_yaad/linear.yandexad.json \
  --from docs/wordstat-search-api-hardening-issue-2026-06-19.md \
  --title "Harden Wordstat Search API regions and associations handling" \
  --labels symphony,wordstat
```

Move the issue to `Todo` only when it is approved for Symphony execution.
