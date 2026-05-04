# Collaboration Proposal for `Marketing2025` + `yandex.ad` — 2026-05-04

## Why this document exists

We now have enough evidence to stop treating `Marketing2025` as “just another MCP client”.

From the weekly Analyst workflows and the `Voicexpert` pipeline runs, the real shape is:

- `yandex.ad` is the **backend capability layer**
- `Marketing2025` is the **workflow / orchestrator layer**
- LLM clients (`Claude`, `Codex`, `Gemini`, etc.) are **interchangeable frontends**

The purpose of this proposal is to define a joint working model that the product/marketing side can review and operate against.

## Target architecture

### `yandex.ad` responsibilities

`yandex.ad` should own:

- Yandex API integration and MCP transport
- stable MCP tool contracts
- auth, retries, rate limits, write guards
- compact domain read models
- a small number of fixed high-ROI read workflows when they materially reduce orchestration cost

`yandex.ad` should not own:

- project-specific workflow policy
- pipeline orchestration
- backlog lifecycle
- run history and artifact governance
- freeform planning logic inside the server

### `Marketing2025` responsibilities

`Marketing2025` should own:

- project profiles and account bundles
- workflow execution (`snapshot -> research -> synthesize -> decide -> QA -> execute`)
- artifact storage and run history
- stable ids for runs, recommendations, evidence, and approvals
- quality gates and workflow policy
- CLI / orchestrator surface

`Marketing2025` should not own:

- raw Yandex API transport logic
- duplicated retry/auth/rate-limit behavior
- duplicated platform wrappers already present in `yandex.ad`

### Client / agent responsibilities

LLM clients should own:

- user interaction
- ad hoc exploration
- human-in-the-loop reviews
- planning assistance when useful

They should not be the primary source of workflow state or artifact truth.

## Proposed joint operating model

### Working principle

The teams should collaborate through **explicit contracts**, not through prompt-only conventions.

The main contract surfaces should be:

1. MCP tool contracts from `yandex.ad`
2. Workflow/artifact contracts from `Marketing2025`
3. Review and acceptance criteria shared by both sides

### Collaboration boundary

Use this rule for deciding ownership:

- “How do we get or mutate Yandex data safely?” -> `yandex.ad`
- “What workflow should run, in what order, with which artifacts and gates?” -> `Marketing2025`
- “How should a human or agent interact with the workflow?” -> client / skill / UI layer

### What must not be duplicated

Avoid duplicating these rules across both repos:

- tool semantics
- campaign/account resolution rules
- write safety policy
- output schemas
- QA status semantics
- workflow routing logic

If a rule is duplicated in both places, one of the repos will drift and pipeline quality will degrade.

## Immediate shared goals

The next phase should optimize for the real current user, not for speculative platform breadth.

### Goal 1 — Make the read path cheaper and more stable

This is the highest-value area for:

- weekly Analyst work
- pipeline snapshot
- pipeline pre-synthesis data collection

The expected result:

- fewer MCP round-trips
- lower context cost
- fewer downstream parsing failures

### Goal 2 — Make pipeline contracts explicit

The pipeline already depends on machine-consumed outputs.

The expected result:

- stable JSON shapes
- explicit ids and status fields
- less glue code in downstream gates
- easier debugging of `Voicexpert`-like runs

### Goal 3 — Keep orchestration above the backend

Do not turn `yandex.ad` into a hidden workflow engine.

The expected result:

- stable MCP surface
- better debuggability
- better portability across hosts and models

## What we should build now

### In `yandex.ad`

#### Workstream A — Contract hardening

Deliverables:

- `outputSchema` for the highest-usage read tools
- explicit read/write intent annotations
- one stable HF response envelope for downstream machine use

Success criteria:

- downstream pipeline code no longer relies on ad hoc parsing per tool
- core read tools expose stable output contracts

#### Workstream B — Narrow read workflows

Only add new MCP functionality if it replaces a long multi-call chain.

The first acceptable candidates are:

- account snapshot
- structure snapshot
- attribution audit

Guardrail:

- no broad expansion of tool count
- no “dynamic tool generation” inside the server

Success criteria:

- each new workflow replaces a materially longer call chain
- each workflow returns a contract useful both to LLMs and to deterministic pipeline code

### In `Marketing2025`

#### Workstream C — CLI-first orchestrator

`Marketing2025` should move toward an operator-grade CLI/control plane.

Initial surface:

- `snapshot`
- `weekly-review`
- `pipeline run`
- `qa preflight`
- `qa review`

Success criteria:

- each run has a stable run id
- each run writes artifacts with predictable locations and schemas
- the same workflow can be run by human, cron, CI, or LLM-assisted operator

#### Workstream D — Artifact and quality contracts

Make these contracts explicit:

- run record
- recommendation record
- evidence record
- preflight report
- review report

Success criteria:

- downstream scripts do not infer state from prose
- QA gates operate on explicit statuses and ids

## Shared review process

### Change classes

#### Backend contract change

Examples:

- new MCP tool
- changed output shape
- changed safety behavior

Required review:

- `yandex.ad` owner
- `Marketing2025` workflow owner

#### Workflow contract change

Examples:

- new artifact schema
- new status semantics
- changed QA gate meaning

Required review:

- `Marketing2025` owner
- `yandex.ad` owner when MCP outputs are consumed differently

### RFC rule

Any change that affects cross-repo contracts should be written down before implementation:

- purpose
- current pain
- proposed contract
- migration impact
- acceptance criteria

## Recommended cadence

### Weekly

- review current Analyst pain points
- review one pipeline run deeply
- decide whether the next improvement belongs to backend or orchestrator

### Per implementation cycle

1. define contract change
2. implement in one repo
3. adapt consuming repo
4. validate on one real project run
5. keep or revert

## Decisions already taken

These are already effectively decided and should be treated as constraints:

- `yandex.ad` remains the backend capability layer
- `Marketing2025` becomes the workflow/control-plane layer
- portability across multiple model vendors and MCP clients must be preserved
- we optimize Analyst + Pipeline read paths before richer UI work
- we do not solve the current problem by simply adding many more tools

## Non-goals for this phase

Do not spend the next phase on:

- broad write-workflow expansion
- MCP Apps runtime implementation
- dynamic tool generation from freeform natural-language tasks
- host-specific hacks for one client
- project-specific business logic inside `yandex.ad`

## Proposed next step

Use this proposal to align the product/marketing side on one concrete delivery split:

1. `yandex.ad` improves **contracts + a very small number of read workflows**
2. `Marketing2025` improves **CLI orchestration + artifacts + QA gates**
3. both sides review one real `Voicexpert`-style run after each iteration

If this split is accepted, the next implementation note should define:

- the first backend contracts to harden
- the first orchestrator commands to standardize
- the first real workflow to validate end-to-end
