# `yandex.ad` implementation backlog — `Path A -> C -> D` — 2026-05-04

## Summary

This backlog reflects the current agreed split with `Marketing2025`:

- implement `Path A` now
- prepare `Path C` minimally
- prepare `Path D` only at the contract level
- do not implement `Path B` until usage data arrives

The goal is to improve the backend as a stable, machine-consumable contract provider for:

- Analyst read-heavy workflows
- pipeline snapshot / research stages
- deterministic downstream parsers and quality gates

## Now — Path A

### A1. Create a single source of truth for tool contracts

Files:

- new: `src/mcp_yandex_ad/tool_contracts.py`
- update: `src/mcp_yandex_ad/tools.py`
- new: `tests/test_tool_contracts.py`

Functions:

- `tool_contracts()`
  Returns metadata for the prioritized read-only tool set: `outputSchema`, annotations, and optional internal tags.
- `decorate_tool(tool: Tool) -> Tool`
  Applies contract metadata to one existing MCP tool definition before it is returned from `tool_definitions()`.
- `prioritized_contract_tools()`
  Returns the exact set of tools covered in iteration 1 so the scope stays explicit and testable.

Initial tool scope:

- `accounts.list`
- `dashboard.generate_option1`
- `direct.hf.find_*`
- `direct.hf.get_campaign_summary`
- `direct.hf.get_bids_summary`
- `direct.hf.pressure_report`
- `direct.hf.report_*`
- `metrica.hf.list_accessible_counters`
- `metrica.hf.counter_summary`
- `metrica.hf.report_*`
- `join.hf.direct_vs_metrica_by_utm`

Tests:

- `test_tool_contracts_expose_output_schema_for_prioritized_tools`
  Prioritized tools publish explicit output schemas.
- `test_tool_contracts_mark_read_only_intent`
  Read-only tools expose safe-use annotations.
- `test_tool_contracts_do_not_expand_unscoped_tools`
  Non-priority tools remain untouched in iteration 1.

### A2. Formalize the HF response envelope

Files:

- update: `src/mcp_yandex_ad/hf_common.py`
- update: `src/mcp_yandex_ad/server.py`
- new: `docs/rfc/RFC-0001-hf-response-envelope.md`
- new: `tests/test_hf_envelope.py`

Functions:

- `hf_payload(...)`
  Remains the canonical builder for the stable HF payload envelope and should stop drifting across handlers.
- `validate_hf_payload(payload: dict[str, Any]) -> None`
  Defensive helper for tests and future composite workflows; fails when a payload breaks the canonical envelope.
- `extract_structured_payload(result: Any) -> dict[str, Any] | None`
  Small server-side helper to normalize structured return values during tests and future validation logic.

Target envelope shape:

- `tool`
- `status`
- `message?`
- `preview?`
- `result?`
- `choices?`
- `warnings?` when needed

Tests:

- `test_hf_payload_emits_canonical_minimal_shape`
  Minimal successful payload has stable keys.
- `test_hf_payload_preserves_preview_and_choices`
  Optional envelope fields survive helper usage.
- `test_hf_handlers_return_canonical_envelope`
  Existing HF handlers keep the same outer shape.

### A3. Add snapshot coverage for public contract changes

Files:

- update: `tests/test_public_tools_snapshot.py`
- update: `tests/snapshots/public_tools_v1.json`
- update: `CHANGELOG.md`

Functions:

- `_deep_sort(value: Any) -> Any`
  Keeps snapshot ordering stable when `outputSchema` and annotations are added.
- `test_public_tools_snapshot_is_stable`
  Extends the public contract snapshot so future metadata changes are explicit.

Tests:

- `test_public_tools_snapshot_is_stable`
  Public tools contract changes are intentional only.

## Next — Path C

### C1. Establish the role/bundle manifest contract

Files:

- new: `docs/rfc/README.md`
- new: `docs/rfc/RFC-0002-role-bundle-manifests.md`
- new: `src/mcp_yandex_ad/tool_bundles.py`
- new: `tests/test_tool_bundles.py`

Functions:

- `bundle_definitions()`
  Returns backend-side bundle metadata definitions without introducing dynamic discovery behavior.
- `bundle_manifest_schema()`
  Describes the minimal manifest shape expected by `Marketing2025`.
- `get_bundle_manifest(bundle_id: str) -> dict[str, Any]`
  Returns one static manifest by id once runtime exposure is approved.

Iteration rule:

- define contract now
- do not expose runtime bundle tools until `Marketing2025` sends inventory input

Tests:

- `test_bundle_manifest_schema_is_explicit`
  Bundle manifest contract has stable top-level fields.
- `test_bundle_definitions_are_static`
  Bundle definitions do not depend on prompt-time state.

### C2. Decide the minimal runtime surface after inventory arrives

Files:

- update later: `src/mcp_yandex_ad/tools.py`
- update later: `src/mcp_yandex_ad/server.py`

Candidate function:

- `handle_catalog_tool(name: str, args: dict[str, Any])`
  Small dispatcher for a future static catalog/bundle tool if runtime exposure is approved.

Not in scope now:

- prompt-dependent surfacing
- hidden server-side ranking logic
- dynamic “compose a tool for this task”

## Later — Path D

### D1. Keep new outputs compatible with future app surfaces

Files:

- update later if needed: `src/mcp_yandex_ad/server.py`
- update later if needed: `src/mcp_yandex_ad/tool_contracts.py`
- new later: `docs/rfc/RFC-0003-app-safe-output-contracts.md`

Functions:

- `is_app_safe_payload(payload: dict[str, Any]) -> bool`
  Future helper for checking whether a structured payload is compact and UI-neutral enough for richer clients.
- `compact_sections(payload: dict[str, Any]) -> dict[str, Any]`
  Future helper for trimming verbose data into stable sections usable by both LLMs and app surfaces.

Current rule:

- do not implement MCP Apps runtime
- do not add `resources`, `ui://`, or client-specific widget contracts
- only keep Path A outputs small, structured, and UI-neutral

Tests:

- `test_prioritized_outputs_remain_compact`
  New structured outputs avoid needless raw bulk.

## Coordination dependencies

Inputs expected from `Marketing2025` by `2026-05-18`:

- prioritized `Path A` tool list
- measured `Path B` candidate chains
- bundle inventory for `Path C`

Until those inputs arrive:

- `Path A` is the active delivery track
- `Path C` is contract definition only
- `Path D` is design discipline only

## Explicit non-goals

- no `Path B` implementation yet
- no dynamic tool generation
- no host-specific discovery hacks
- no project-specific business logic inside `yandex.ad`
- no MCP Apps runtime work in this phase
