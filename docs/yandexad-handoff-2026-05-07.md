# `yandex.ad` Handoff - 2026-05-07

## Purpose

This handoff captures the MCP-side work that has already been implemented locally, plus the remaining release, contract, and downstream-integration work needed for `Marketing2025` to consume it safely.

## Executive Summary

The core May 7 MCP issues have already been fixed in local code:

- unique Direct `ReportName` generation
- valid `direct.hf.report_keywords` field set
- actionable `CUSTOM_REPORT` validation
- Metrica HF auto-pagination
- Wordstat batch fallback
- special/no-structure campaign diagnostics
- read-only Direct login override improvements
- HF discovery pagination and filter corrections

What remains is not feature invention. It is release discipline, contract clarity, and downstream validation.

## Confirmed Implemented Fixes

Primary implementation files:

- [`src/mcp_yandex_ad/server.py`](../src/mcp_yandex_ad/server.py)
- [`src/mcp_yandex_ad/hf_direct.py`](../src/mcp_yandex_ad/hf_direct.py)
- [`src/mcp_yandex_ad/hf_metrica.py`](../src/mcp_yandex_ad/hf_metrica.py)
- [`src/mcp_yandex_ad/report_names.py`](../src/mcp_yandex_ad/report_names.py)
- [`src/mcp_yandex_ad/campaign_diagnostics.py`](../src/mcp_yandex_ad/campaign_diagnostics.py)
- [`tests/test_review_regressions.py`](../tests/test_review_regressions.py)

Validated locally:

- `pytest -q` -> `125 passed`

## Detailed Task List

### Track A - Ship the reviewed fixes

#### A1. Review and merge the local MCP fixes

Owner:

- `yandex.ad` maintainer

Files:

- [`src/mcp_yandex_ad/server.py`](../src/mcp_yandex_ad/server.py)
- [`src/mcp_yandex_ad/hf_direct.py`](../src/mcp_yandex_ad/hf_direct.py)
- [`src/mcp_yandex_ad/hf_metrica.py`](../src/mcp_yandex_ad/hf_metrica.py)
- [`src/mcp_yandex_ad/report_names.py`](../src/mcp_yandex_ad/report_names.py)
- [`src/mcp_yandex_ad/campaign_diagnostics.py`](../src/mcp_yandex_ad/campaign_diagnostics.py)
- [`tests/test_review_regressions.py`](../tests/test_review_regressions.py)

Required changes:

- complete code review against branch policy
- merge without dropping regression tests
- preserve the new campaign diagnostic fields and warning semantics

Acceptance criteria:

- fixes exist on the main release path
- full test suite stays green

#### A2. Release the MCP changes with versioning and notes

Owner:

- `yandex.ad` maintainer

Files:

- [`CHANGELOG.md`](../CHANGELOG.md)
- `pyproject.toml`
- release notes under `docs/releases/` if needed

Required changes:

- bump version
- finalize changelog entry
- publish release notes that call out payload / warning changes relevant to downstream consumers

Acceptance criteria:

- a tagged release exists for the reviewed fixes
- downstream repos can target a specific version

### Track B - Contract and docs cleanup

#### B1. Document new response semantics for downstream clients

Owner:

- `yandex.ad` maintainer

Required changes:

- document special-campaign diagnostic fields:
  - `campaign_type`
  - `campaign_type_hint`
  - `counts_applicable`
  - `performance_signal`
- document Metrica truncation warnings
- document Wordstat fallback payload shape
- document read-only `account_id` -> `direct_client_login` fallback behavior

Acceptance criteria:

- `Marketing2025` can update parsers from docs, not from reverse-engineering runtime output

#### B2. Resolve the `dashboard.generate_option1` contract mismatch

Owner:

- `yandex.ad` maintainer

Files:

- [`src/mcp_yandex_ad/tool_contracts.py`](../src/mcp_yandex_ad/tool_contracts.py)
- [`src/mcp_yandex_ad/server.py`](../src/mcp_yandex_ad/server.py)

Problem:

- the reviewed branch marked `dashboard.generate_option1` as read-only while it could still write files

Required changes:

- either remove side effects from the read-only contract path
- or reclassify the tool contract to reflect real behavior

Acceptance criteria:

- metadata and runtime side effects match

### Track C - Downstream validation with Marketing2025

#### C1. Validate the fixed MCP responses against the actual pipeline consumers

Owner:

- joint `yandex.ad` + `Marketing2025` validation

Required checks:

- `direct.hf.report_search_phrases`
- `direct.hf.report_keywords`
- `direct.hf.get_campaign_summary`
- `direct.list_campaigns`
- `metrica.hf.report_utm_campaigns`
- `wordstat.top_requests`

Required changes:

- replay or live-run the exact MCP calls used by the marketing workflow
- verify that returned warning fields and result structures are parsed correctly
- identify any downstream parser assumptions that still rely on broken historical behavior

Acceptance criteria:

- `Marketing2025` can consume the fixed responses without ad hoc workarounds

#### C2. Normalize special-campaign diagnostics across related tools

Owner:

- `yandex.ad` maintainer

Required changes:

- ensure list/summary/discovery tools expose compatible diagnostic fields for special/no-structure campaigns
- avoid forcing downstream code to maintain tool-specific heuristics

Acceptance criteria:

- downstream code can branch on one stable diagnostic contract

### Track D - Test depth and safety

#### D1. Expand integration-style regression coverage

Owner:

- `yandex.ad` maintainer

Files:

- [`tests/test_review_regressions.py`](../tests/test_review_regressions.py)

Required additions:

- realistic special/Telegram campaign fixtures
- pagination edge cases beyond 1000 rows
- Metrica explicit `limit` truncation warnings
- Wordstat fallback with mixed phrase batches
- read-only login overrides vs write-tool rejection paths

Acceptance criteria:

- reviewed failure classes are covered by tests closer to production payloads

#### D2. Re-audit read-only override safety

Owner:

- `yandex.ad` maintainer

Files:

- [`src/mcp_yandex_ad/server.py`](../src/mcp_yandex_ad/server.py)

Required changes:

- verify that relaxed read-only login handling cannot leak into write flows
- ensure write tools still reject conflicting or unsafe overrides

Acceptance criteria:

- there is no mutation path that benefits from the read-only relaxation

## Recommended Execution Order

1. Merge and release implemented fixes (`A1`, `A2`)
2. Document contract changes and resolve the dashboard contract mismatch (`B1`, `B2`)
3. Validate against real `Marketing2025` consumers (`C1`, `C2`)
4. Expand integration coverage and re-audit override safety (`D1`, `D2`)

## Cross-Repo Dependency On Marketing2025

These MCP fixes only remove backend-side defects. `Marketing2025` still needs its own pipeline changes for:

- DRAFT autotargeting false positives
- preflight campaign validity logic
- `Task()` degraded execution
- deterministic product existence checks
- stronger provenance handling

## Done Means

The handoff is complete when:

- a released `yandex.ad` version contains the May 7 MCP fixes
- response semantics are documented for downstream clients
- `Marketing2025` consumes the new warnings and diagnostics correctly
- the outstanding contract mismatch for `dashboard.generate_option1` is resolved

