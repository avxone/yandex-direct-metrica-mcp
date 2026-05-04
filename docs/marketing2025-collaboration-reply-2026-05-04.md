# `yandex.ad` reply to `Marketing2025` collaboration response — 2026-05-04

## Summary

We accept the `Marketing2025` response and treat the architectural split as settled:

- `yandex.ad` remains the backend capability layer
- `Marketing2025` remains the workflow / control-plane layer
- multi-vendor / multi-client portability remains mandatory

We will proceed with:

- `Path A` now
- `Path C` minimally and in parallel
- `Path D` as preparation only

We will not start `Path B` implementation until the promised `Marketing2025` usage data and candidate chains are delivered.

## Accepted decisions

We accept without further negotiation:

- ownership split
- “do not duplicate” list
- RFC-before-implementation rule for cross-repo contracts
- weekly joint review cadence
- `pipeline_voicexpert` as the first shared validation target

## Response to the open questions

### Q1. Format for the priority tool list

Recommended format:

- open a PR against this repo
- add one input file under `docs/`

Proposed filename:

- `docs/marketing2025-path-a-input-2026-05-18.md`

Minimum contents:

- tool name
- where it is consumed in `Marketing2025`
- why current output is insufficient
- required fields / invariants
- approximate usage frequency

Reason:

- it keeps the contract input reviewable
- it preserves history in one place
- it is easier to compare against implementation backlog and RFCs than an issue thread

### Q2. HF response envelope

We do not want this to remain implicit.

Decision:

- start from a backend-owned draft
- review it jointly before locking it as a stable contract

The first draft is created here:

- `docs/rfc/RFC-0001-hf-response-envelope.md`

This draft is intended to be:

- small
- machine-readable
- stable across the HF read layer

### Q3. RFC location

Agreed.

Cross-repo RFCs will live in:

- `docs/rfc/`

Naming:

- `RFC-NNNN-short-title.md`

The initial rules are documented here:

- `docs/rfc/README.md`

### Q4. First joint validation target

Agreed.

The first shared validation sequence will be:

1. `Marketing2025` completes the fresh `pipeline_voicexpert` run + `human-review`
2. `yandex.ad` ships the first `Path A` iteration
3. `Marketing2025` reruns the same target and compares:
   - contract failures removed
   - parser simplification achieved
   - error classes that remain on the orchestrator / synthesis side

## What `yandex.ad` will do now

### Path A — start immediately

Immediate scope:

- define the first stable HF response envelope draft
- add `outputSchema` for the highest-priority read-only tools
- add explicit safety annotations for the same tool set

Target outcome:

- `Marketing2025` can begin writing one shared loader instead of many tool-specific parsers

### Path C — minimal parallel work

Immediate scope:

- define the bundle / role-manifest contract shape
- wait for `Marketing2025` inventory before choosing runtime surface

Guardrail:

- no complex discovery runtime yet
- no dynamic tool surfacing by prompt/task

### Path D — preparation only

Immediate scope:

- keep new read contracts compact and app-safe
- avoid coupling new outputs to HTML or one client

Guardrail:

- no `resources`
- no `ui://`
- no MCP Apps runtime implementation in this phase

## What we are explicitly not doing now

- no `Path B` implementation before measured candidate chains arrive
- no dynamic tool generation inside the server
- no broad tool-count expansion
- no host-specific hacks
- no project-specific business logic in `yandex.ad`

## Next coordination point

The next useful cross-repo checkpoint is when `Marketing2025` delivers:

- the `Path A` priority tool list
- measured `Path B` candidate chains
- bundle inventory for `Path C`

Until then, `yandex.ad` should treat `Path A` as the active implementation track.
