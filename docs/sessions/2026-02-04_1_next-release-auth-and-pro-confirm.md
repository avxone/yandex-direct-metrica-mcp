# 2026-02-04 — Next release: Auth UX tools + PRO two-phase confirm

## Context / Goals

We want to improve:
- **Auth UX**: make it possible to obtain OAuth tokens via MCP tools (in addition to CLI), without storing secrets in the server.
- **PRO write safety**: make “accidental writes” materially harder by enforcing a two-phase flow (**plan → confirm**) via a dedicated tool.

Non-goal (for this release):
- Adding a new network transport (Streamable HTTP / hosted) — defer to a separate SaaS/hosted release.

---

## Completed

- Confirmed scope for the next release:
  - Add MCP tools for Auth UX (pro-only, disabled by default).
  - Add PRO two-phase commit mechanism (plan → confirm) using a new tool (`write.confirm`).
- Agreed to defer Streamable HTTP transport changes to a separate hosted/SaaS release.

---

## Proposal A — Auth UX via MCP tools (pro-only, no storage)

### UX
1) Call `auth.start` → get `authorize_url` + `state` (+ echo `redirect_uri` and `scopes`).
2) User authorizes in browser and gets `code`.
3) Call `auth.exchange_code` → get tokens + a ready-to-paste `.env` block.

### Guardrails
- Pro-only and disabled by default (`MCP_AUTH_TOOLS_ENABLED=true` to enable).
- Never write tokens to disk.
- Never log tokens (even at debug).
- Explicit docs warning: tokens returned by tools are secrets; chat clients may store transcripts.

### Tool list impact
- New tools: `auth.start`, `auth.exchange_code` (and optionally `auth.scopes.suggest` later).

---

## Proposal B — PRO two-phase write via `write.confirm` (B2)

### UX
1) Any write-capable tool call returns:
   - `status=planned`
   - `confirm_token` (opaque, single-use, TTL)
   - `plan` (human + machine summary)
2) Only after user approval:
   - Call `write.confirm(confirm_token)` → server performs the write and returns the real result.

### Guardrails
- Pro-only and enabled by default in pro (configurable).
- Tokens are single-use and expire quickly (TTL).
- Confirm re-checks all existing write guardrails (`MCP_WRITE_ENABLED`, sandbox-only, HF flags, destructive flags).
- No persistence: pending plans are stored only in-memory for TTL.

### Compatibility strategy
- Phase 1 (next release): ship mechanism behind a feature flag (`MCP_TWO_PHASE_WRITES=true`), document and recommend it for PRO.
- Phase 2: consider making it default-on in PRO after migration window.

---

## To Do

- Draft and publish the official tool list changes:
  - Add new tools to `docs/tools-proposal-YYYY-MM-DD.md` (auth + write.confirm).
- Implement Auth tools:
  - Add `auth.start` + `auth.exchange_code`.
  - Add `MCP_AUTH_TOOLS_ENABLED` guard.
  - Add tests for tool schemas and “no storage / no logging” rules.
- Implement two-phase write confirm:
  - Add `write.confirm` tool and a minimal in-memory pending store (TTL, single-use).
  - Add `MCP_TWO_PHASE_WRITES` flag and wire into write-capable tools.
  - Update tests for write guard + confirm path.
- Update docs:
  - `README.md` and `docs/quickstart.md` (auth UX warning + flows).
  - `docs/public-vs-pro.md` (PRO write safety model).
- Update release artifacts:
  - Ensure public tools snapshot remains unchanged.
  - Add new pro tools to any pro snapshot/contract (if we maintain one).

