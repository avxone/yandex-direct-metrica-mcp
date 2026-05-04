# Session 2026-05-03 (2) — Research: Progressive discovery + MCP Apps

## Completed
- Researched official MCP guidance for **Progressive tool discovery**.
- Researched official MCP guidance for **MCP Apps / server-delivered UI**.
- Compared those patterns against the current `yandex.ad` implementation, roadmap, and public/pro constraints.
- Added the research note: `docs/research-progressive-discovery-and-mcp-apps-2026-05-03.md`.
- Explicitly captured a non-negotiable architecture constraint: preserve compatibility across multiple model vendors and multiple MCP-capable hosts/clients.
- Identified the main project conclusion:
  - progressive discovery is primarily a **host/client/orchestrator** concern for this project
  - MCP Apps are viable, but would require new server capabilities (`resources`, `ui://`, app metadata), so they should be treated as a deliberate product/architecture expansion

## To Do
- Decide whether the first discovery improvement is:
  - metadata quality (`description`, `outputSchema`, `annotations`)
  - a host/orchestrator-side search layer
  - or a new MCP discovery tool proposal
- Decide whether Streamable HTTP should move forward before any serious hosted/UI work.
- Decide whether a first MCP App spike should be:
  - dashboard explorer
  - campaign drill-down
  - or deferred entirely
- If UI work proceeds, decide whether it belongs in:
  - OSS core
  - Pro image
  - private Pro plug-in
  - or a separate companion service
