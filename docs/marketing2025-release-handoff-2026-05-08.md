# Marketing2025 Release Handoff - 2026-05-08

## Purpose

This handoff closes the `yandex.ad` side of the May 7 cross-repo review and records what `Marketing2025` can now rely on after the `v2.0.10` release.

Use this document as the current source of truth for:

- release status
- MCP image status
- tool and contract status relevant to `Marketing2025`
- the remaining joint validation step

## Executive Summary

`yandex.ad` release `v2.0.10` is now published.

The MCP-side fixes identified during the May 7 review are shipped, the public and PRO Docker publish workflows completed successfully, and the local `:dev` path used by `Marketing2025` has been aligned to the verified PRO image with the BI plug-in installed.

As of 2026-05-08:

- `Marketing2025` does not need further code changes to pick up the new special-campaign diagnostics already pre-staged in its campaign validity logic
- the next live `Marketing2025` MCP session that resolves `yandex-direct-metrica-mcp-pro:dev` should pick up the new local image
- the main remaining cross-repo task is the joint replay / pipeline validation run

## Released On `yandex.ad`

Release:

- `v2.0.10`

Primary release artifact:

- [Release notes](releases/v2.0.10.md)

Included changes that matter to `Marketing2025`:

- special / no-structure campaign diagnostics in `direct.hf.get_campaign_summary`
- special-campaign substitution / warning behavior in `direct.list_campaigns`
- automatic pagination for the affected `metrica.hf.report_*` tools when `limit` is omitted
- truncation warnings for explicit-limited Metrica HF report calls
- Wordstat batch fallback behavior for `wordstat.top_requests`
- `direct.hf.report_keywords` compatibility fix
- explicit `Keyword` vs `Criterion` validation for low-level `direct.report`
- read-only Direct login override support for agency read scenarios
- corrected contract metadata for `dashboard.generate_option1` so it is no longer published as read-only when `output_dir` causes filesystem writes

Related consumer note:

- [Marketing2025 contract update - 2026-05-08](marketing2025-path-a-contract-update-2026-05-08.md)

## Publish Status

Completed on 2026-05-08:

- pushed `main`
- tagged `v2.0.10`
- tagged `pro-v2.0.10`
- created the GitHub release for `v2.0.10`
- completed public Docker publish workflow
- completed PRO Docker publish workflow

Result:

- public release path is published
- PRO release path is published
- local PRO+BI validation image was also built and verified separately

## Validation Status

The release was validated on the `yandex.ad` side before handoff.

Completed validation:

- `pytest -q` passed
- public Docker image passed a credential-backed smoke test
- local PRO image with the BI plug-in installed exposed the expected dashboard schema / dataset / sync surface
- the existing `Marketing2025` Docker QA runner passed against:
  - the local public image
  - the local PRO+BI image

Observed QA outcome:

- no P0 release blockers
- no P1 warnings
- no schema-lint violations

Important scope note:

- the quick QA matrix does not exercise every PRO BI dataset tool
- the verified result here is:
  - release surface is correct
  - core MCP workflows pass
  - dashboard / join / Direct / Metrica / Wordstat / Audience checks pass

## Local Marketing Path

`Marketing2025` has historically referred to the local MCP server as:

- `ydm-mcp-pro-dev`
- Docker image reference: `yandex-direct-metrica-mcp-pro:dev`

To avoid requiring an immediate config rewrite, the verified local PRO image with the BI plug-in installed was retagged onto:

- `yandex-direct-metrica-mcp-pro:dev`

Meaning:

- the existing local dev image name now points to the verified `2.0.10` PRO+BI image
- if no old container is still running, the next MCP session can pick it up without changing the image name

Observed state at handoff time:

- no Yandex MCP container was running

Operational implication:

- the next `Marketing2025` local session should resolve the new `:dev` image cleanly
- if an existing client session cached an older MCP process, restart that session before replay

## What `Marketing2025` Can Consume Now

### Campaign validity

`Marketing2025` can now rely on the released MCP fields documented in:

- [Marketing2025 contract update - 2026-05-08](marketing2025-path-a-contract-update-2026-05-08.md)

Most important signals:

- `campaign_type = "SPECIAL_NO_STRUCTURE"`
- `counts_applicable = false`
- warning code `campaign_type_special_no_structure`
- special-candidate substitution data from `direct.list_campaigns`

This matches the pre-staged `Marketing2025` logic that promotes live MCP diagnostics over registry fallback when those new fields are present.

### Metrica collectors

`Marketing2025` can now assume:

- omitted `limit` on the affected HF Metrica tools means auto-pagination
- explicit caller truncation is surfaced as a warning instead of remaining silent

### Wordstat collectors

`Marketing2025` can now treat `wordstat.top_requests` fallback responses as successful degraded results rather than hard failures.

### Dashboard contract

`Marketing2025` does not consume `dashboard.generate_option1` as a read-only contract signal, but the metadata is now accurate and no longer misleading.

## Remaining Cross-Repo Work

### 1. Joint replay validation

Still required:

- rerun the intended `Marketing2025` workflow / replay against the released MCP image path
- confirm that the special-campaign validity path behaves correctly end-to-end in the real pipeline, not only in unit tests and MCP-side QA

This is the main remaining cross-repo action from the May 7 review thread.

### 2. Marketing PR to `yandex.ad/docs/`

Still expected from `Marketing2025`:

- PR the Path A input file into `yandex.ad/docs/` by `2026-05-18`

### 3. Optional follow-up hardening

Not blocking this release, but still useful:

- expand the PRO BI QA matrix to exercise more `dashboard.dataset.*` tools directly
- add a replay-specific artifact bundle for the joint validation run

## Handoff Decision

`yandex.ad` is no longer the blocking side for the May 7 MCP defects.

The current state is:

- released
- published
- locally validated
- locally aligned with the `Marketing2025` `:dev` image path

The remaining decision point moves to the shared replay / validation step on the `Marketing2025` workflow side.
