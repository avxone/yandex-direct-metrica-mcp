# Session 2026-05-04 (7) — `Path C` static bundle contract

## Completed
- Added backend-internal bundle manifest definitions in `src/mcp_yandex_ad/tool_bundles.py`.
- Added the explicit schema helper `bundle_manifest_schema()` with the currently agreed top-level fields:
  - `bundle_id`
  - `title`
  - `intended_for`
  - `recommended_tools`
  - `preferred_entrypoints`
  - `excluded_tools`
  - `notes`
- Added one provisional static manifest: `marketing2025.analyst_pipeline`.
- Kept the scope intentionally narrow:
  - no new MCP tool was added
  - no `tools/list` changes were introduced
  - no prompt-time or task-time dynamic discovery behavior was added
- Added tests for:
  - explicit manifest schema
  - static bundle definitions
  - copy-safe manifest retrieval
  - unknown bundle rejection
- Verified targeted regression suites still pass.

## To Do
- Wait for the real `Marketing2025` bundle inventory before exposing any runtime catalog/bundle MCP tool.
- Reconcile the provisional bundle contents with measured project usage once Marketing2025 provides the final inventory.
- Keep `Path D` limited to output-shape discipline until there is approval for app/resource work.
