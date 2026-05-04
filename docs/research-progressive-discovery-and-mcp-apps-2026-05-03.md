# Research — Progressive Tool Discovery + MCP Apps for `yandex.ad` — 2026-05-03

## Scope

This note prepares a project discussion around two questions:

1. How can **Progressive tool discovery** be implemented for our MCP surface?
2. How can **MCP Apps / server-delivered UI** be implemented for our project?

The goal is not abstract protocol theory. The goal is to map the official direction of MCP onto the current architecture and constraints of `yandex.ad`.

## Non-negotiable compatibility constraint

For this project, any architecture decision should preserve the ability to work with:
- multiple model vendors:
  - OpenAI
  - Anthropic / Claude
  - Google / Gemini
- multiple MCP-capable hosts/clients:
  - Claude Code
  - Codex
  - OpenCode
  - Cursor / VS Code / other compatible clients

Implications:
- We should prefer **MCP-standard** mechanisms over vendor-specific affordances whenever possible.
- OpenAI Apps SDK patterns are useful as historical and practical input, but they are **not** the target architecture by themselves.
- If a feature only works in one host, it should be treated as:
  - an optional compatibility layer
  - a hosted/pro-specific enhancement
  - or a spike/prototype, not the core product direction
- The backend MCP surface should remain portable across hosts and model providers.

## External findings

### 1) Progressive tool discovery

Official MCP guidance places progressive discovery primarily at the **host/client layer**, not at the server layer.

Key points from the MCP docs:
- The official client guidance explicitly recommends avoiding the naive pattern where every connected tool definition is injected into model context up front.
- The recommended pattern is:
  1. **Catalog**: expose a lightweight search mechanism that returns names + short descriptions.
  2. **Inspect**: fetch the full schema/details only for selected tools.
  3. **Execute**: call the chosen tool after loading its full definition.
- The host should continue using `tools/list`, but defer putting full tool definitions into the model’s context until needed.
- The docs recommend:
  - threshold-based switching to discovery mode when tool definitions become too large
  - caching tool definitions host-side
  - re-indexing when `notifications/tools/list_changed` fires
  - optionally grouping tools by server
- The same guide also suggests that tool search may be implemented as:
  - keyword/BM25
  - embedding retrieval
  - a small subagent/tool-selection model
  - hybrid ranking

Important implication for us:
- “Progressive discovery” does **not** mean “the server itself hides tools from `tools/list` dynamically for each prompt.”
- It usually means the **host** sees the full surface, but the **model** sees a filtered/loaded-on-demand view.
- This is good for us because a host-side pattern is inherently more portable across Claude/OpenAI/Gemini stacks than a vendor-specific server hack.

Practical enablers from the MCP spec:
- `tools/list`
- `notifications/tools/list_changed`
- richer tool metadata:
  - `outputSchema`
  - `annotations.readOnlyHint`
  - `annotations.destructiveHint`
  - `annotations.idempotentHint`
  - `annotations.openWorldHint`

These do not implement discovery by themselves, but they make tool search/ranking much better.

### 2) MCP Apps / server-delivered UI

As of **January 26, 2026**, MCP Apps are an official MCP extension.

Key points from the official MCP Apps docs/spec:
- A tool can declare a UI resource via `_meta.ui.resourceUri`.
- The resource is served from the MCP server via the `ui://` scheme.
- The host fetches the UI resource and renders it inside a **sandboxed iframe**.
- The UI and host communicate via JSON-RPC over `postMessage`.
- The app can:
  - receive tool results
  - call tools through the host
  - update model context
  - request follow-up interaction patterns, depending on host support
- UI resource metadata can carry:
  - `_meta.ui.csp`
  - `_meta.ui.permissions`
  - `_meta.ui.prefersBorder`
- Tool visibility can be split between:
  - `["model", "app"]`
  - `["app"]` for app-only helper tools
- Hosts may prefetch and cache UI resources.
- UI-only resources do not have to be broadly listed in `resources/list`.

Important implication for us:
- MCP Apps are **not** the same thing as “generate HTML and save it to disk”.
- They require:
  - `resources/read`
  - `ui://` resources
  - tool metadata pointing to UI resources
  - host support for the Apps extension

Also important:
- The official MCP Apps effort explicitly builds on patterns pioneered by OpenAI’s Apps SDK and MCP-UI.
- OpenAI’s official examples show a similar pattern:
  - tools return structured content
  - widget/UI resources are served separately
  - host/widget state can be synchronized

Compatibility implication for us:
- If we pursue server-delivered UI, the reference direction should be **official MCP Apps / ext-apps**, not a ChatGPT-only widget model.
- OpenAI-specific metadata/patterns are useful only insofar as they map cleanly to standard MCP Apps concepts.

## Relevant official sources

- MCP client best practices:
  - <https://modelcontextprotocol.io/docs/develop/clients/client-best-practices>
- MCP tools spec (2025-06-18):
  - <https://modelcontextprotocol.io/specification/2025-06-18/server/tools>
- MCP resources spec (2025-06-18):
  - <https://modelcontextprotocol.io/specification/2025-06-18/server/resources>
- MCP Apps overview:
  - <https://modelcontextprotocol.io/extensions/apps/overview>
- MCP Apps launch post:
  - <https://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/>
- MCP Apps spec / ext-apps:
  - <https://github.com/modelcontextprotocol/ext-apps>
  - <https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx>
- OpenAI Apps SDK official examples:
  - <https://github.com/openai/openai-apps-sdk-examples>

## What we already have in `yandex.ad`

### A. Strong tool-centric MCP surface

Today the server is centered around tools:
- raw tools
- HF tools
- dashboard tool
- optional Pro tools / private plug-ins

This is reflected in the public docs and LLM guides:
- `README.md`
- `docs/llm-usage-guide-2026-02-03.md`
- `docs/llm-usage-guide-pro-2026-02-03.md`

### B. `tools/list` is already the source of truth

This is already a strong foundation for discovery-oriented thinking:
- the docs explicitly treat `tools/list` as the contract surface
- runtime rejects calls to tools that are not available for the current build/config
- public/pro visibility is already enforced through the tool surface

This is good because progressive discovery relies on a stable catalog source.

### C. Dynamic tool surface by build/config already exists

We already have runtime filtering by:
- public vs pro
- feature flags
- plug-in presence

That means we already support one important prerequisite:
- the **catalog** can change by deployment mode

### D. We already have a UI-like artifact pattern

`dashboard.generate_option1` already gives us:
- generated `HTML + JSON`
- multi-account UI behavior inside the generated dashboard
- a strong user-facing analysis artifact

This matters because the project already has a clear “something visual” use case. We do **not** need to invent a use case for MCP Apps; the dashboard is the obvious candidate.

### E. We already have a plug-in boundary

The project already separates:
- OSS public core
- Pro image
- private PRO plug-ins

That is useful because both discovery helpers and UI capabilities may fit better in:
- a Pro contour
- a hosted contour
- a separate extension/plugin

## What is already planned

### 1. Streamable HTTP / hosted direction

We already recorded a plan to add:
- Streamable HTTP transport
- a separate hosted/SaaS image

See:
- `docs/sessions/2026-02-04_2_streamable-http-hosted-3.0.0.md`

This is directly relevant to MCP Apps and more advanced client integrations.

### 2. Agent ergonomics as the recommended direction

We already captured a roadmap recommendation:
- **Option B now**: improve agent ergonomics without changing the core public/pro contract

See:
- `docs/mcp-ecosystem-roadmap-2026-05-03.md`

This supports incremental work such as:
- better tool semantics
- clearer grouping
- controlled expansion of HF workflows

### 3. Orchestrator separation

We already have a separate orchestrator proposal:
- workflow runner / control plane in a separate repo

See:
- `docs/dream-team-orchestrator-proposal-2026-03-01.md`

This matters because part of “progressive discovery” may be better implemented in the host/orchestrator, not in this MCP server itself.

It also matters because an orchestrator/host-side layer is the natural place to normalize behavior across:
- different models
- different tool-selection heuristics
- different MCP-capable clients

## What blocks or constrains us today

### 1. The server currently implements tools, not resources/prompts/apps

In code, the MCP server exposes:
- `@app.list_tools()`
- `@app.call_tool()`

There are no server handlers for:
- resources
- prompts
- MCP Apps / `ui://` resources

Implication:
- a real MCP Apps implementation is **not** a metadata-only patch
- it requires new protocol capabilities and server plumbing

### 2. Plug-in API is tool-only

Current plug-in registry can add:
- `Tool`s
- direct tool handlers
- prefix handlers

It cannot currently register:
- resources
- prompts
- UI resources
- app bridge behavior

Implication:
- a Pro plug-in cannot currently implement MCP Apps cleanly without first expanding the core plug-in contract

### 3. We do not currently use richer MCP tool metadata

Current tool definitions are mostly:
- `name`
- `description`
- `inputSchema`

We are not visibly using:
- `outputSchema`
- `annotations.*`

Implication:
- this weakens both discovery quality and future code-mode/programmatic calling quality
- the host has less machine-readable information for ranking and safety decisions

### 4. Transport support is behind the roadmap

Current `run_server()` supports:
- `stdio`
- `sse`

There is no Streamable HTTP implementation in the current code.

Implication:
- some modern remote/hosted integration paths remain awkward or postponed
- this does not block local/stdio experimentation, but it does affect productization

### 5. Public contract is intentionally strict

The project has already decided:
- public build is safe-by-default
- public contract is the exact `tools/list` surface
- BI Option 2 is out of public core
- write and risky surfaces stay gated

Implication:
- any new discovery helper added as a public MCP tool changes the public contract
- any UI/app expansion must be evaluated against the public/pro boundary

### 6. New tools require explicit approval

Project policy already says:
- add new tools only after explicit approval

Implication:
- “just add `search_tools`” is not a no-process change here
- even good discovery ideas must pass the tool-approval gate

### 7. We already decided not to prioritize embedded general code execution in this server

The roadmap note explicitly says not to prioritize:
- embedding a general code-execution/runtime layer inside this MCP server

Implication:
- if the discussion drifts from “progressive discovery” into “code mode inside the backend MCP,” that currently conflicts with the recommended direction

## What decisions already push us away from some options

### Decision: public surface is a stable contract

Effect:
- adding meta-discovery tools directly into the public server is not free
- descriptions and schemas are contract-sensitive

### Decision: BI Option 2 lives in a private PRO plug-in, not in OSS core

Effect:
- advanced UX/data workflows are already expected to live outside the core public build
- this makes a plugin/hosted route for UI work more consistent than putting everything into OSS core

### Decision: current dashboard is file/artifact-oriented

Effect:
- existing dashboard UX is based on generated HTML artifacts
- MCP Apps would be a new UX model, not a direct continuation of the current one

### Decision: orchestrator/workflow logic may live in a separate repo

Effect:
- host-side discovery/search/ranking may belong more naturally in the orchestrator than in `yandex.ad`

### Constraint: avoid single-vendor lock-in

Effect:
- we should avoid designing discovery around one vendor’s proprietary tool-search interface only
- we should avoid designing UI around one client’s custom widget contract if the same capability can be expressed through MCP Apps
- we should preserve text/tool fallbacks for clients that do not support Apps

## How Progressive tool discovery could be done for our project

## Option A — Host-side only, no MCP server surface change

Implementation:
- keep `yandex.ad` as the provider of the full tool catalog via `tools/list`
- implement discovery in the host/orchestrator/client layer:
  - build a searchable local catalog from `tools/list`
  - expose a lightweight search function to the model
  - fetch/show full schemas only for chosen tools

Good fit for us because:
- it matches official MCP guidance
- it avoids changing the public MCP contract
- it avoids adding new server tools just for discovery
- it is the most compatible with multi-model / multi-client usage

What we should improve in the server for this option:
- better descriptions
- consistent naming
- output schemas
- tool annotations

Recommendation:
- this is the **cleanest near-term path**

## Option B — Add server-assisted meta-tools

Implementation:
- add MCP tools such as:
  - `meta.search_tools`
  - `meta.get_tool_details`
  - maybe `meta.list_tool_groups`

Pros:
- server can inject domain-specific ranking logic
- can reflect build mode / account mode / plugin presence

Cons:
- changes the public/pro tool contract
- requires approval for new tools
- duplicates logic that the host may already be able to do from `tools/list`
- less aligned with official guidance, which is host-first

Recommendation:
- only consider this if we need domain-aware ranking the host cannot do well

## Option C — Put discovery logic in the separate orchestrator

Implementation:
- orchestrator maintains:
  - tool index
  - task-to-tool heuristics
  - maybe embeddings or a small selection model
- `yandex.ad` remains a clean backend MCP server

Pros:
- strongest architectural separation
- aligns with the “backend repo vs orchestrator repo” split
- avoids polluting the MCP server with host behavior

Cons:
- requires orchestrator work to move first
- benefits are less visible to plain MCP clients that use the server directly

Recommendation:
- good medium-term path if the orchestrator becomes real

## How MCP Apps / server-delivered UI could be done for our project

## Option A — Stay with generated dashboard artifacts

Implementation:
- continue with `dashboard.generate_option1`
- optionally improve HTML delivery, preview, and hosted access later

Pros:
- no protocol expansion
- works today
- stable and low-risk

Cons:
- not an in-conversation UI
- not interactive through the host
- no app-to-tool feedback loop

Recommendation:
- keep as baseline regardless of other UI work

## Option B — Add a first MCP App for dashboard exploration

Implementation shape:
- add `resources` capability
- serve one `ui://` dashboard resource
- link a tool to it via `_meta.ui.resourceUri`
- keep tool text/structured fallback for non-supporting clients
- let the app call a small set of app-safe tools for drill-down

Best first candidate:
- a **dashboard explorer**
- not the whole ad-management surface

Why this is the best first candidate:
- the project already has dashboard logic and UX language
- it is naturally read-heavy
- it fits the public safe-by-default posture better than write flows
- it can still degrade to normal tool/text behavior in clients without Apps support

Required core changes:
- implement resource handlers in the MCP server
- choose resource MIME/content strategy
- expand plug-in/core contracts if UI should be pluggable
- decide whether UI tools should be model-visible, app-visible, or both

## Option C — Build MCP Apps only in a hosted/pro contour

Implementation:
- keep OSS/public core text/tool-first
- enable Apps only in:
  - a hosted image
  - a Pro image
  - or a separate companion server/plugin

Pros:
- preserves public OSS simplicity
- better match for richer auth, remote hosting, and asset serving
- lower contract risk for the public build

Cons:
- fragments the experience between editions
- more packaging/deployment complexity

Recommendation:
- this is the most realistic path if we decide to pursue MCP Apps soon

## Recommended discussion position

### Progressive discovery

Recommended position:
- **Do not start by adding discovery tools to the MCP server.**
- Start by making the existing server more discoverable:
  - better descriptions
  - add `outputSchema`
  - add tool annotations
  - keep `tools/list` high quality
- If needed, implement the actual progressive loading logic in the host/orchestrator.

Why:
- it is closer to the official MCP guidance
- it preserves the current public/pro contract
- it does not force protocol surface changes
- it keeps the backend portable across Claude/OpenAI/Gemini ecosystems and across different MCP hosts

### MCP Apps

Recommended position:
- **Do not try to convert the whole project to MCP Apps.**
- If we explore MCP Apps, do it through a narrow read-oriented vertical:
  - dashboard explorer
  - maybe campaign drill-down
  - no write workflows first

Why:
- we already have a natural dashboard use case
- it minimizes safety risk
- it gives us real learning about resource serving, app transport, and host compatibility
- it still allows us to keep a model/client-neutral fallback path for hosts without Apps support

## Practical next steps for discussion

### Near-term, low risk

1. Audit current tools for description quality and grouping.
2. Add `outputSchema` where the output is predictable.
3. Add MCP tool annotations for read/write semantics.
4. Decide whether tool discovery belongs in:
   - the MCP server
   - the host/orchestrator
   - both

### Medium-term

1. Decide whether to implement Streamable HTTP before any serious hosted/UI work.
2. Design a minimal resources API addition to the server.
3. Pick one dashboard-focused MCP App spike.
4. Decide whether UI belongs in:
   - OSS core
   - Pro plug-in
   - hosted image
   - separate companion service

## Bottom line

For `yandex.ad`:
- **Progressive discovery** should mostly be treated as a **host/orchestrator concern**, with server-side work focused on better metadata and cleaner tool semantics.
- **MCP Apps** are real and production-grade now, but in our project they would require real protocol and architecture work, not just a dashboard facelift.
- The cleanest path is:
  - improve discoverability of the existing tool surface first
  - keep dashboard HTML artifacts as the baseline
  - explore one narrow dashboard-oriented MCP App only after transport and capability decisions are clearer
- Throughout all of this, we should optimize for **vendor-neutral MCP portability**, not for any one model provider or host.
