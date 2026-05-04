# MCP ecosystem roadmap signals for `yandex.ad` — 2026-05-03

## Context

This note extracts the parts of the NotebookLM notebook **"Будущее MCP: Экосистема связности и агенты нового поколения"** that are useful for this repo.

Current repo priorities already include:
- raw, traceable analytics access
- a practical dashboard UX
- a safe-by-default public build
- a separate Pro path with private plug-ins

See:
- `README.md`
- `docs/public-vs-pro.md`

## What is actually useful for this repo

Useful signals from the notebook:
- **Progressive tool discovery**: important because this repo already has a broad surface across `direct.*`, `metrica.*`, `wordstat.*`, `audience.*`, HF tools, and dashboard tools.
- **Task-oriented abstractions over raw APIs**: aligns with the repo split between raw tools and human-friendly tools; this is a good direction for future expansion.
- **Server-delivered UI / MCP applications**: relevant to the dashboard direction, especially if the project later wants client-native views instead of only generated `HTML + JSON`.
- **Skills/domain knowledge near the tool layer**: relevant for packaging higher-level operating patterns without turning the public surface into a large REST mirror.
- **Enterprise auth / cross-app access**: relevant only for a later enterprise-grade Pro track.

Less useful signals from the notebook:
- It does **not** help with Yandex API coverage, payload shapes, retries, or low-level auth flows.
- It does **not** justify adding risky execution features to the public build.
- It is based on a narrow source set, so it should be treated as roadmap input, not as protocol authority.

## Three options

### Option A — Stay conservative

Keep the repo focused on:
- raw data access
- current HF helpers
- Option 1 dashboard
- existing public vs Pro split

Pros:
- lowest execution risk
- preserves the current read-only/public contract
- no new protocol complexity

Cons:
- tool surface may become harder for agents to navigate as coverage grows
- misses the chance to improve agent usability at the protocol layer

Best fit:
- if the next priority is Yandex API coverage and release hardening only

### Option B — Add agent-oriented ergonomics without changing the core contract

Focus on near-term improvements that make the MCP easier for agents to use, while preserving the current public/pro boundaries.

Scope:
- improve tool descriptions, grouping, and discovery hints
- keep adding high-level HF workflows instead of mirroring raw endpoints one-for-one
- define a clearer contract for Pro plug-ins and domain guidance around workflows
- keep dashboard evolution on the current path, but design it so it can later map into MCP-delivered UI

Pros:
- directly improves agent usability
- fits the existing architecture
- keeps the public build safe-by-default
- helps control context bloat without introducing major runtime risk

Cons:
- requires careful curation of tool naming and descriptions
- some benefits depend on client support for richer discovery patterns

Best fit:
- if the goal is to make `yandex.ad` more effective in real agent workflows this quarter

### Option C — Push toward a platform-forward MCP product

Use the notebook as a signal to invest in advanced MCP-native capabilities.

Scope:
- add explicit progressive discovery patterns at the server layer
- evolve dashboard UX toward MCP-delivered UI / app patterns
- prepare for enterprise auth and cross-app access in the Pro contour
- explore packaged “skills over MCP” for complex ad operations

Pros:
- strongest long-term strategic alignment with the broader MCP direction
- differentiates the project beyond raw API access

Cons:
- highest design and maintenance cost
- depends on evolving client/spec support
- easy to overbuild ahead of actual user demand

Best fit:
- only after the current public/pro product line is stable and well-adopted

## Recommendation

Recommended path: **Option B now**, while keeping selected Option C ideas on the later roadmap.

Reasoning:
- It matches the repo’s current product shape.
- It improves usefulness for agent clients without weakening the public safety model.
- It avoids premature work on speculative UI/auth features.
- It leaves room for a future MCP-application model without forcing a redesign now.

## Proposed priority order

### Near-term

1. **Strengthen tool semantics before adding more tools**
   - Improve descriptions and usage framing for existing tools.
   - Prefer task language over REST language where possible.
   - Keep the public surface compact.

2. **Expand HF workflows selectively**
   - Add only the highest-value workflows that reduce multi-step agent orchestration pain.
   - Avoid exposing low-signal endpoint wrappers unless they are clearly needed.

3. **Formalize the Pro plug-in contract**
   - Document what belongs in OSS core vs private Pro plug-ins.
   - Keep BI Option 2 and similar advanced workflows as plug-in territory.

### Later

1. **Tool discovery as an approved feature**
   - Only add a dedicated discovery helper/tool after explicit approval.
   - Keep it aligned with the approved tool-list process.

2. **MCP-delivered dashboard UI**
   - Treat this as an evolution of the dashboard track, not as a replacement for current `HTML + JSON` generation.

3. **Enterprise auth / cross-app access**
   - Revisit only when there is a concrete enterprise distribution need.

## What not to prioritize yet

- Embedding a general code-execution/runtime layer inside this MCP server.
- Adding speculative enterprise auth features before there is a real customer path.
- Reworking the current dashboard around experimental UI patterns before the existing path is fully mature.

## Practical takeaway

For `yandex.ad`, the notebook is most useful as a reminder to:
- design for agent usability, not just API completeness
- keep the public contract small and safe
- use the Pro/plugin boundary intentionally
- treat richer UI and enterprise auth as later-stage capabilities
