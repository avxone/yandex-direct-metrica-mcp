# Development options for `yandex.ad` focused on `Marketing2025` — 2026-05-03

## Why this note exists

The question is no longer “how do we grow `yandex.ad` in general?”

The more useful question is:

> How should we continue developing `yandex.ad` so it becomes more useful for its main real user today: `Marketing2025`?

This note reassesses the advantages and disadvantages of the main directions and proposes several balanced paths.

## What `Marketing2025` actually needs from `yandex.ad`

From the project structure, role bundles, and QA runner, the demand pattern is clear:

### 1. The main load is read-heavy, multi-account analysis

The **Analyst** bundle is the clearest primary user:
- weekly dashboard refresh
- anomaly detection
- drilldowns by dimension
- Direct vs Metrica sanity checks
- portfolio-level reporting

Relevant bundle:
- `Marketing2025/dream-team/bundles/analyst-bundle.md`

### 2. A smaller but important write path exists

The **Ads Specialist** and **QA/Controller** bundles need:
- plan/apply writes
- pre-flight QA
- post-apply QA
- baseline and experiment logging

Relevant bundles:
- `Marketing2025/dream-team/bundles/ads-specialist-bundle.md`
- `Marketing2025/dream-team/bundles/qa-controller-bundle.md`

### 3. A second primary usage mode exists: pipeline analysis

`Marketing2025` is also building a full autonomous / semi-autonomous pipeline.

The pipeline docs and Voicexpert test runs show that `yandex.ad` is being used not only for weekly human-facing analysis, but also as a **machine-consumed data substrate** inside a multi-phase process:
- snapshot
- research
- synthesis
- quality gates
- preflight QA
- later execute/evaluate loops

This is visible in:
- `Marketing2025/docs/pipeline-architecture.md`
- `Marketing2025/docs/pipeline-quality-review.md`
- `Marketing2025/docs/pipeline-quality-improvements-2026-03-12.md`
- `Marketing2025/artifacts/pipeline_voicexpert_*`

Important implication:
- for the pipeline, the value of `yandex.ad` is not just “good tool UX for an LLM”
- it is also:
  - stable machine-readable outputs
  - deterministic data contracts
  - low-noise interoperability with Python quality gates and synthesizers

### 4. Context pressure is already a real constraint

`Marketing2025/PLAN.md` shows that:
- large agent fan-out caused context-limit failures
- the project moved to a hierarchical architecture specifically to stay within context budget
- the successful run still treated context as a first-class resource

This matters because `yandex.ad` should reduce orchestration/context waste, not increase it.

### 5. The project already uses a much smaller practical tool subset than the full server surface

In the `ydmcp-pro-qa-oneclick` skill, the practical working set is about:
- `33` distinct tools

This is much smaller than the full `143`-tool pro/core surface.

Implication:
- `Marketing2025` does not need “more tools everywhere” nearly as much as it needs:
  - better tool selection
  - better role-specific scoping
  - less orchestration overhead

### 6. Pipeline quality work pushes the backend toward stronger contracts

The Voicexpert pipeline quality reviews show recurring issues around:
- phantom campaigns
- absorbed/moot recommendation filtering
- budget traceability
- stable IDs across phases
- cross-step shared context
- deterministic validation between synthesis and preflight

Many of these issues are not caused by missing raw API coverage.
They are caused by weak or inconsistent contracts between:
- MCP outputs
- synthesis artifacts
- quality gates
- renderers/reviewers

Implication:
- `Marketing2025` needs `yandex.ad` to become a cleaner **contract provider**, not only a broader capability provider

### 7. Compatibility remains a hard requirement

The server should remain useful across:
- multiple model providers
- multiple MCP-capable hosts/clients

So any path that depends heavily on a single host or vendor is strategically weak for this project.

## What `yandex.ad` already does well for `Marketing2025`

### Advantage 1 — Broad domain coverage

The current server already covers the main surfaces `Marketing2025` needs:
- Direct
- Metrica
- Wordstat
- Audience
- dashboard generation
- Direct↔Metrica joins

This is a major strength. The project does not need a new backend category first.

### Advantage 2 — Strong public/pro safety split

This fits the real workflow:
- read-heavy analysis most of the time
- guarded writes only for approved execution

That matches `Marketing2025` well.

### Advantage 3 — Human-friendly tools already exist

The existence of HF tools is strategically correct for `Marketing2025`.
The main user is not trying to script raw APIs directly; it is trying to answer recurring operator questions.

At the same time, pipeline runs show that HF tools are also useful as upstream providers for deterministic downstream logic, as long as their outputs are stable enough.

### Advantage 4 — Multi-account and dashboard orientation

This is directly aligned with portfolio monitoring and weekly operations in `Marketing2025`.

### Advantage 5 — Plan/apply + QA posture

The Ads + QA bundles already assume a careful write process.
The backend direction is compatible with that.

## What currently limits usefulness for `Marketing2025`

### Disadvantage 1 — The surface is too large relative to the active working set

The full pro/core surface is large, while the project usually needs a much smaller subset.

Effect:
- higher context cost
- worse first-step tool selection
- more host-side prompt engineering burden

### Disadvantage 2 — Tool metadata is not rich enough

Current tool definitions mostly expose:
- name
- description
- input schema

Missing or underused:
- output schemas
- annotations
- stronger task-oriented semantic signaling

Effect:
- weaker chaining
- weaker ranking/safety behavior in hosts
- more trial-and-error tool use
- less reliable downstream use in pipeline gates and artifact processors

### Disadvantage 3 — The server is tool-centric but not role-aware

`Marketing2025` is role-and-runbook driven.
`yandex.ad` is not yet expressing that role structure at the MCP protocol level.

Effect:
- every host or skill layer has to rebuild role scoping manually

### Disadvantage 4 — The Analyst workflow still pays orchestration tax

The most frequent user path is still built from many MCP calls plus client-side synthesis.

That is flexible, but expensive in:
- latency
- context
- failure surface

The pipeline architecture shows a related problem in a different form:
- too much cross-step glue logic is needed outside the MCP server
- the more glue exists, the more contract drift becomes possible

### Disadvantage 5 — UI is still artifact-based, not conversationally interactive

The current dashboard is useful, but it is still a generated artifact pattern.

That is fine, but it means:
- good reporting
- weaker inline exploration

### Disadvantage 6 — Plug-in and protocol extensibility are still narrow

The current plug-in contract is tool-only.
There is no first-class support for:
- resources
- prompts
- MCP Apps

So some promising directions are architecturally blocked until the core contract evolves.

## Balanced development paths

## Path A — “Backend Hygiene First”

### What it means

Keep `yandex.ad` as a portable MCP backend and improve its quality as a tool catalog.

Focus:
- better descriptions
- clearer HF entrypoints
- `outputSchema`
- MCP `annotations`
- documented role-specific recommended tool subsets
- more stable machine-readable outputs for downstream pipeline stages

### Advantages

- Lowest risk
- Fully compatible with multiple models and hosts
- Improves every client immediately
- Helps progressive discovery without changing the public contract much
- Best fit for `Marketing2025` context pressure problem in the short term
- Also best fit for the pipeline-quality problem in the short term

### Disadvantages

- Does not reduce orchestration count by itself
- Does not create new “big capability” moments
- Still leaves more workflow logic in the host/skill layer

### Best when

- The priority is making current weekly/monthly operations more reliable and cheaper

## Path B — “Marketing2025-Optimized Read Layer”

### What it means

Develop a more explicitly task-oriented read layer aimed at the actual recurring Analyst workflows.

Examples:
- richer portfolio/account snapshot helpers
- anomaly-oriented bundles of related metrics
- more compact summary tools for executive review
- better first-class outputs for cross-account rollups

This does **not** mean adding random tools.
It means selectively collapsing common multi-call analysis patterns into better read-only entrypoints.

Pipeline interpretation:
- these tools should not only be “easy for an LLM to call”
- they should also be “easy for downstream Python gates and synthesizers to consume”

### Advantages

- Highest practical ROI for the primary user
- Directly attacks orchestration tax
- Reduces context and latency for Analyst workflows
- Still compatible with the public/pro safety model if kept read-only
- Can reduce glue code and ambiguity inside the pipeline if outputs are compact and stable

### Disadvantages

- Risk of overfitting to one user/project
- Requires strong discipline to avoid tool sprawl
- Needs explicit approval for any new tool surface
- If done carelessly, can create hidden business logic in MCP tools that is hard to audit

### Best when

- The main objective is making `Marketing2025` weekly analysis faster, cheaper, and more stable

## Path C — “Role-Aware MCP Surface”

### What it means

Make the MCP surface more aware of role/bundle usage patterns without necessarily changing the core tools drastically.

Possible forms:
- prompts/resources describing recommended tool subsets by role
- bundle manifests
- host-facing discovery artifacts for Analyst / Ads / QA
- project-aware documentation and compatibility contracts

This is the path that best matches the actual Dream Team architecture.

### Advantages

- Aligns `yandex.ad` with how `Marketing2025` is actually used
- Improves portability better than vendor-specific host hacks
- Makes discovery and scoping much easier
- Can coexist with Path A and Path B
- Creates a cleaner bridge between Dream Team bundles and backend capabilities

### Disadvantages

- Some variants require protocol expansion beyond tools
- Benefits depend on host support if expressed through MCP features like prompts/resources
- More design work than simple metadata cleanup

### Best when

- The priority is medium-term architecture quality and better role-based ergonomics

## Path D — “Interactive UI / MCP Apps”

### What it means

Move part of the reporting and exploration experience toward MCP Apps / server-delivered UI.

Best first candidate:
- dashboard explorer

Not a good first candidate:
- write-heavy management workflows

### Advantages

- Strongest user-facing leap
- Good fit for dashboard exploration
- Could reduce repeated prompt loops for filtering/drilldown

### Disadvantages

- Highest architecture cost
- Requires resources/UI protocol work
- Host support varies
- Less urgent than read-layer and metadata improvements for `Marketing2025`

### Best when

- The baseline analysis workflow is already stable and you want a better inline UX

## Which path is best for `Marketing2025`?

No single path is sufficient.

The best balanced answer is:

### Recommended combination

1. **Path A now**
2. **Path B selectively, for Analyst-heavy read workflows**
3. **Path C in parallel, but minimally at first**
4. **Path D later, only after the read layer is cleaner**

## Why this combination is balanced

### Why not Path A only?

Because metadata cleanup alone will help, but it will not remove enough orchestration overhead from the Analyst workflow.
It also will not, by itself, reduce the amount of glue logic in the pipeline.

### Why not Path B only?

Because without Path A discipline, Path B can devolve into more tool sprawl.
It can also hide too much interpretation inside MCP tools, making the pipeline harder to debug.

### Why not Path C first?

Because role-aware protocol design is valuable, but the fastest value still comes from better metadata and better read-path ergonomics.

### Why not Path D first?

Because `Marketing2025`’s biggest pain today is not “lack of fancy UI.”
It is:
- context budget
- orchestration cost
- repeatable weekly reliability

## Concrete phased proposal

## Phase 1 — Improve the current backend for the main user

Targets:
- improve tool descriptions and HF positioning
- add `outputSchema` to the most used tools
- add tool annotations
- document role-specific recommended subsets:
  - Analyst
  - Ads Specialist
  - QA
- identify which current outputs are consumed by pipeline gates and make those contracts explicit/stable

Expected outcome for `Marketing2025`:
- better tool selection
- less prompt waste
- easier host-side bundling
- fewer downstream parsing/contract issues in pipeline analysis

## Phase 2 — Add a small number of high-leverage Analyst-oriented read tools

Targets:
- reduce common multi-call analysis sequences
- focus on recurring `Marketing2025` use cases only
- keep these tools read-only and compact
- prefer outputs that are useful both to LLMs and to deterministic downstream scripts

Examples of good candidates:
- weekly account health summary
- anomaly drilldown summary
- portfolio rollup summary
- structured campaign audit snapshot / anomaly pack inputs for pipeline synthesis

Expected outcome:
- lower latency
- fewer context-expensive agent pipelines
- better weekly cadence reliability

## Phase 3 — Add role-aware discovery artifacts

Targets:
- make the backend easier to consume by bundles/hosts
- avoid vendor lock-in

Possible outputs:
- role manifests
- prompts/resources for recommended entrypoints
- clearer project-facing docs for curated working sets

Expected outcome:
- easier integration with `Marketing2025`
- better cross-client portability

## Phase 4 — Explore one MCP App

Target:
- dashboard explorer only

Expected outcome:
- stronger interactive UX without destabilizing the core backend

## What we should explicitly avoid

- Expanding tools one-to-one from API surface for the sake of completeness
- Solving discovery primarily with vendor-specific behavior
- Starting with UI before stabilizing the read path
- Putting too much workflow/orchestrator logic into the backend MCP server
- Optimizing writes before the Analyst path is cheaper and more reliable

## Final recommendation

If the main user is `Marketing2025`, then `yandex.ad` should evolve primarily as:

1. a **better-described, better-typed, portable MCP backend**
2. a **more efficient read-heavy analysis backend for the Analyst bundle**
3. a **clean contract provider for pipeline analysis and quality gates**
4. a **role-aware backend that is easier for host/orchestrator layers to scope**
5. only later, an **interactive dashboard/app backend**

In plain terms:
- do not chase breadth first
- do not chase UI first
- optimize the real weekly user first
- and optimize the pipeline contracts second, before chasing richer UI

That means:
- Path A + selective Path B is the highest-ROI next step
- Path C is the right architectural follow-up
- Path D is valuable, but later
