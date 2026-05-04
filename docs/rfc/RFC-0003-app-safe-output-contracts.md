# RFC-0003 — app-safe output contracts

## Purpose

Define the minimal backend-side contract discipline needed to keep selected outputs usable by future MCP App / richer UI surfaces without introducing any app runtime now.

## Scope

This RFC does **not** introduce:

- `resources`
- `ui://`
- app-specific metadata
- client-specific widget contracts
- runtime behavior changes for existing MCP tools

This RFC only defines what counts as an app-safe payload shape for future use.

## Current pain

Some outputs already have compact, UI-neutral forms, especially:

- `dashboard.generate_option1` compact result
- prioritized HF envelope responses

But the repo does not yet have one explicit rule for distinguishing:

- compact, sectioned, app-safe payloads
- bulky raw/debug payloads that should not become future app surface contracts

## Proposed contract

An app-safe payload should:

- be structured as a JSON object
- remain machine-readable without HTML
- avoid embedded raw report blobs by default
- avoid large opaque strings
- expose stable sections such as `summary`, `meta`, `warnings`, `coverage`, `result`, `preview`, `message`
- keep warnings and partial-quality signals explicit at the top level

Known bulky keys that are not app-safe by default:

- `raw`
- `raw_report`
- `sources_raw_report`
- `direct_raw_report`
- `direct_split_raw_report`

`raw_refs` is allowed when it remains compact and points to source context rather than embedding the full source dataset.

## Initial helper seam

The repo may use small internal helpers to enforce this discipline:

- `compact_sections(payload)`
  Removes known bulky raw sections while preserving compact structured sections.
- `is_app_safe_payload(payload)`
  Returns `true` only when the payload is already compact and does not contain oversized strings.

These helpers are internal only and do not change runtime MCP contracts.

## Acceptance criteria

- one explicit RFC exists for app-safe output discipline
- one internal helper module exists to encode the rule
- compact dashboard-style outputs satisfy the helper
- raw-heavy payloads fail the helper
- no MCP Apps runtime is introduced

## Deferred items

Out of scope for this RFC:

- app transport/runtime
- app resources
- interactive actions
- richer section taxonomies per tool family
- host-specific rendering metadata
