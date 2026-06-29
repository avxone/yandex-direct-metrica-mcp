# Symphony Launch

Use **two** Symphony processes for this project:

- implementation lane
- review lane

PR and release are no longer separate Symphony lanes. They are handled as follow-up issues with `issue-type:pr` and `issue-type:release` inside the same two-lane state loop.

Recommended ports:

- implementation: `3321`
- review: `3322`

Before relaunching, stop any old `3323` / `3324` PR or release lane sessions. They belong to the deprecated state-based model.

## Secret Source

Do not copy provider credentials into the repo or into `Symphony_yaad/`.

For Yandex live validation, export them into the parent Symphony process directly from:

- `/Users/georgyagaev/mcp/state/yandex.ad/.env`

This keeps the credentials in one place while still making them available to the isolated Codex worker via inherited process environment.

If a live-validation command still reports missing Search API credentials, the implementation/review lane may source `/Users/georgyagaev/mcp/state/yandex.ad/.env` directly in that command. Do not print values and do not copy the file into the repo or workspace.

## Implementation lane

```bash
cd /Users/georgyagaev/Projects/Symphony_yaad/symphony/elixir
mkdir -p /Users/georgyagaev/Projects/Symphony_yaad/logs
set -a
. /Users/georgyagaev/Projects/Symphony_yaad/.env
. /Users/georgyagaev/mcp/state/yandex.ad/.env
set +a
/opt/homebrew/bin/mise exec -- ./bin/symphony \
  /Users/georgyagaev/Projects/Symphony_yaad/workflows/WORKFLOW.yandexad.implementation.md \
  --logs-root /Users/georgyagaev/Projects/Symphony_yaad/logs \
  --port 3321 \
  --i-understand-that-this-will-be-running-without-the-usual-guardrails
```

## Review lane

```bash
cd /Users/georgyagaev/Projects/Symphony_yaad/symphony/elixir
mkdir -p /Users/georgyagaev/Projects/Symphony_yaad/logs
set -a
. /Users/georgyagaev/Projects/Symphony_yaad/.env
. /Users/georgyagaev/mcp/state/yandex.ad/.env
set +a
/opt/homebrew/bin/mise exec -- ./bin/symphony \
  /Users/georgyagaev/Projects/Symphony_yaad/workflows/WORKFLOW.yandexad.review.md \
  --logs-root /Users/georgyagaev/Projects/Symphony_yaad/logs \
  --port 3322 \
  --i-understand-that-this-will-be-running-without-the-usual-guardrails
```

## Copy Updated Workflow Files

When the repo workflow files change, refresh the external Symphony copies:

```bash
cp docs/automation/workflows/WORKFLOW.yandexad.implementation.md \
  /Users/georgyagaev/Projects/Symphony_yaad/workflows/
cp docs/automation/workflows/WORKFLOW.yandexad.review.md \
  /Users/georgyagaev/Projects/Symphony_yaad/workflows/
```

## Expected Runtime Behavior

1. user or Codex creates a feature issue with `symphony` and `issue-type:feature`
2. user moves it to `Todo`
3. implementation lane picks it up
4. review lane either returns it to `Todo` or closes it and creates the PR follow-up issue
5. the same two lanes process the PR issue
6. if the chain carries `release-required`, review creates the release follow-up issue
7. the same two lanes process the release issue

## Blocked Input Policy

If the current stage cannot proceed because required external credentials, operator-provided inputs, or manual validation evidence are unavailable:

1. implementation or review leaves one concise blocker comment;
2. the issue moves to `Backlog`, not `Todo`;
3. the operator restores the missing input;
4. the operator moves the issue back to `Todo`.
