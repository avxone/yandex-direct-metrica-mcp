# Session: Symphony external secrets and backlog blocker policy

Date: 2026-06-29

## Completed

- Confirmed that Yandex Search API credentials exist in the external state store:
  - external state file, for example `<state-root>/yandex.ad/.env`
- Updated Symphony launch guidance to source that state `.env` directly into the parent Symphony process instead of copying credentials into the repo or `Symphony_yaad/`.
- Updated implementation/review workflow prompts so missing external credentials, missing operator inputs, or impossible manual validation move an issue to `Backlog` instead of sending it around a `Todo` retry loop.
- Documented the same blocker policy in the pipeline and issue-writing guidance.

## To Do

- Sync the updated workflow files into `<symphony-root>/workflows/`.
- Relaunch Symphony with both `<symphony-root>/.env` and `<state-root>/yandex.ad/.env` sourced into the parent process.
- Re-run `GEO-9` and confirm live Search API validation either completes or produces a single `Backlog` blocker instead of a loop.
