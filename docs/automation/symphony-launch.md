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

- `<state-root>/yandex.ad/.env`

This keeps the credentials in one place while still making them available to the isolated Codex worker via inherited process environment.

If a live-validation command still reports missing Search API credentials, the implementation/review lane may source `<state-root>/yandex.ad/.env` directly in that command. Do not print values and do not copy the file into the repo or workspace.

## Codex runtime

Use the app-bundled Codex binary for Symphony lanes:

- `/Applications/Codex.app/Contents/Resources/codex`

Reason:

- the global Codex config (for example `$CODEX_HOME/config.toml`) already carries the enabled browser/plugin configuration;
- using the app-bundled binary keeps Symphony closer to the same runtime that already exposes `browser@openai-bundled`, `chrome-devtools`, and `playwrigh` in the interactive desktop setup.

## Implementation lane

```bash
cd <symphony-root>/symphony/elixir
mkdir -p <symphony-root>/logs
set -a
. <symphony-root>/.env
. <state-root>/yandex.ad/.env
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
set +a
/opt/homebrew/bin/mise exec -- ./bin/symphony \
  <symphony-root>/workflows/WORKFLOW.yandexad.implementation.md \
  --logs-root <symphony-root>/logs \
  --port 3321 \
  --i-understand-that-this-will-be-running-without-the-usual-guardrails
```

## Review lane

```bash
cd <symphony-root>/symphony/elixir
mkdir -p <symphony-root>/logs
set -a
. <symphony-root>/.env
. <state-root>/yandex.ad/.env
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
set +a
/opt/homebrew/bin/mise exec -- ./bin/symphony \
  <symphony-root>/workflows/WORKFLOW.yandexad.review.md \
  --logs-root <symphony-root>/logs \
  --port 3322 \
  --i-understand-that-this-will-be-running-without-the-usual-guardrails
```

## Copy Updated Workflow Files

When the repo workflow files change, refresh the external Symphony copies:

```bash
cp docs/automation/workflows/WORKFLOW.yandexad.implementation.md \
  <symphony-root>/workflows/
cp docs/automation/workflows/WORKFLOW.yandexad.review.md \
  <symphony-root>/workflows/
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

If the restored input is operator/browser evidence, the next retry may consume it from either:

- a Linear issue comment with explicit validation summary, or
- a repo-local note under `docs/` or `docs/sessions/`.
