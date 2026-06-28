# Symphony Launch

Use **two** Symphony processes for this project:

- implementation lane
- review lane

PR and release are no longer separate Symphony lanes. They are handled as follow-up issues with `issue-type:pr` and `issue-type:release` inside the same two-lane state loop.

Recommended ports:

- implementation: `3321`
- review: `3322`

Before relaunching, stop any old `3323` / `3324` PR or release lane sessions. They belong to the deprecated state-based model.

## Implementation lane

```bash
cd /Users/georgyagaev/Projects/Symphony_yaad/symphony/elixir
mkdir -p /Users/georgyagaev/Projects/Symphony_yaad/logs
set -a
. /Users/georgyagaev/Projects/Symphony_yaad/.env
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
