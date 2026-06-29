# Capability Matrix

Use this matrix when writing or reviewing a Symphony-managed issue.

The issue must state which capabilities are required before it can move from `Backlog` to `Todo`.

## Capability Fields

Every issue should explicitly define:

- `browser`
- `live-api`
- `manual-check`
- `operator step required`
- `required env`
- `source of truth`

## Browser Modes

### `none`

Use when the stage can be completed with:

- unit/integration tests
- contract checks
- fixture validation
- docs/handoff review

### `playwright`

Use when the agent must automate a deterministic browser workflow itself.

Good fit:

- stable page traversal
- DOM extraction
- repeatable checks
- screenshot or artifact capture

### `chrome-devtools`

Use when the stage must inspect a real Chrome target rather than a fresh automated browser context.

Good fit:

- validating what an operator actually sees
- checking session/cookie/captcha behavior
- inspecting an already-open page

### `operator-browser`

Use when the comparison must be performed by a human operator in a visible browser and the agent can only describe or record the required checklist.

Good fit:

- manual SERP comparison
- subjective UI sanity
- cases where the agent cannot reliably bypass captcha or anti-bot gating

## Live API

### `live-api: no`

The stage must be completable from:

- local tests
- fixtures
- static artifacts
- docs

### `live-api: yes`

The issue must also define:

- required env vars
- source of truth for secrets
- whether the parent Symphony process must export them before `Todo`

## Manual Check

### `manual-check: no`

The stage must be agent-completable.

### `manual-check: yes`

The issue must also define:

- what exactly must be checked
- who owns the check: agent or operator
- what artifact proves completion

## Blocked Input Policy

Use `Backlog` when the stage is blocked by:

- missing external credentials
- missing browser capability
- missing operator-provided evidence
- missing manual approval

Use `Todo` only when another implementation pass can fix the issue directly:

- code defect
- test failure
- snapshot drift
- docs drift
- missing stage artifact that the agent can create

## Release Chain Implication

If a feature issue requires:

- `operator-browser`
- or manual browser-visible comparison

that requirement must be satisfied before the feature can move to `Done`, unless the issue explicitly delegates that check to a later stage.
