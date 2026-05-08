# Marketing2025 Handoff - 2026-05-07

## Purpose

This handoff converts the May 7 review and follow-up code inspection into an execution-ready backlog for the `Marketing2025` repo.

Use this document when assigning implementation work to the workflow / pipeline side. It assumes the MCP-side fixes are being handled separately in `yandex.ad`.

## Executive Summary

The current `Marketing2025` pipeline still has workflow-layer failure modes even after the MCP fixes:

- `campaign-audit` can produce false positives for DRAFT autotargeting
- preflight campaign validity still trusts `landing_map` more than live campaign state
- `gap-overlay-report` still depends on `Task()` with no degraded path
- the synthesis quality gate still lacks deterministic product/model existence validation
- provenance backfilling is still too weak for a pipeline that claims deterministic validation

The pipeline entrypoint that uses these components is:

- [`scripts/run_pipeline.sh`](../scripts/run_pipeline.sh)
- [`/.claude/skills/pipeline/SKILL.md`](../.claude/skills/pipeline/SKILL.md)

## Confirmed Problem Areas

### 1. False positive `draft_autotargeting`

Primary file:

- [`/Users/georgyagaev/Projects/Marketing2025/scripts/audit/build_campaign_audit.py`](</Users/georgyagaev/Projects/Marketing2025/scripts/audit/build_campaign_audit.py:253>)

Current behavior:

- raises on `DRAFT` + `autotargeting_enabled`
- upgrades to `CRITICAL` if the parent campaign has spend
- does not verify whether the flagged adgroup has live ads or an active serving path

Impact:

- dormant draft structures can be presented as urgent waste
- downstream synthesis and review inherit incorrect severity

### 2. Preflight `CAMPAIGN_VALID` still tied to `landing_map`

Primary files:

- [`/Users/georgyagaev/Projects/Marketing2025/scripts/preflight/run_preflight_checks.py`](</Users/georgyagaev/Projects/Marketing2025/scripts/preflight/run_preflight_checks.py:99>)
- [`/Users/georgyagaev/Projects/Marketing2025/.claude/skills/preflight-qa/SKILL.md`](</Users/georgyagaev/Projects/Marketing2025/.claude/skills/preflight-qa/SKILL.md:21>)

Current behavior:

- campaign existence and status are inferred from `landing_map`
- `"(not in snapshot)"` and empty-account placeholders can become hard failures
- special / Telegram campaigns still risk rejection before render

Impact:

- valid recommendations can be escalated or rejected for campaigns that are real but poorly represented in local mapping artifacts

### 3. `gap-overlay-report` has no `Task()` fallback

Primary file:

- [`/Users/georgyagaev/Projects/Marketing2025/.claude/skills/gap-overlay-report/SKILL.md`](</Users/georgyagaev/Projects/Marketing2025/.claude/skills/gap-overlay-report/SKILL.md:116>)

Current behavior:

- launches three parallel `Task()` subagents for collection
- launches another `Task()` for strategy
- does not define a sequential degraded path

Impact:

- unattended runs are brittle when agent features are unavailable, rate-limited, or degraded

### 4. Missing deterministic `MODEL_EXISTS`-style gate

Primary files:

- [`/Users/georgyagaev/Projects/Marketing2025/scripts/pipeline/synthesis_quality_gate.py`](</Users/georgyagaev/Projects/Marketing2025/scripts/pipeline/synthesis_quality_gate.py:1>)
- [`/Users/georgyagaev/Projects/Marketing2025/.claude/skills/pipeline/SKILL.md`](</Users/georgyagaev/Projects/Marketing2025/.claude/skills/pipeline/SKILL.md:245>)

Current behavior:

- validates trust, confidence, budget evidence, IDs, and review consistency
- does not load offerings to validate whether a proposed product/model actually exists

Impact:

- hallucinated or stale product references can survive to B2B review or render

### 5. Weak provenance repair in `populate_source_records.py`

Primary file:

- [`/Users/georgyagaev/Projects/Marketing2025/scripts/pipeline/populate_source_records.py`](</Users/georgyagaev/Projects/Marketing2025/scripts/pipeline/populate_source_records.py:1>)

Current behavior:

- attempts cluster-based backfill of empty `source_records`
- returns success even when some records remain unresolved
- is non-blocking in the pipeline

Impact:

- deterministic budget and traceability checks can run on partially provenance-free records

## Detailed Task List

### Track A - Audit correctness

#### A1. Fix `draft_autotargeting` classification

Owner:

- `Marketing2025` pipeline / audit maintainer

Files:

- [`/Users/georgyagaev/Projects/Marketing2025/scripts/audit/build_campaign_audit.py`](</Users/georgyagaev/Projects/Marketing2025/scripts/audit/build_campaign_audit.py:253>)

Required changes:

- require evidence that a flagged DRAFT adgroup can actually serve or is attached to active/non-archived ads
- stop inheriting campaign-level spend as direct proof against a dormant draft adgroup
- handle special/no-structure campaign layouts explicitly
- downgrade findings when the structure is ambiguous rather than clearly harmful

Acceptance criteria:

- the known false-positive case no longer emits a finding
- a real DRAFT autotargeting risk with live serving still emits a finding
- severity rules are based on adgroup-relevant evidence, not only parent campaign spend

Suggested tests:

- draft adgroup with autotargeting enabled but no active ads -> no finding
- draft adgroup with active ads and measurable spend path -> finding remains
- Telegram/special campaign fixture -> no false `CRITICAL`

#### A2. Add data completeness checks for audit snapshots

Owner:

- `Marketing2025` pipeline / collector maintainer

Files:

- [`/Users/georgyagaev/Projects/Marketing2025/.claude/skills/campaign-audit/SKILL.md`](</Users/georgyagaev/Projects/Marketing2025/.claude/skills/campaign-audit/SKILL.md:74>)
- collector prompt files used by that skill

Required changes:

- paginate or chunk MCP reads for large campaigns
- emit coverage counters for campaigns, adgroups, keywords, search phrases, and CriterionType rows
- refuse to run mismatch / waste analysis silently on partial datasets
- persist a completeness summary into audit artifacts

Acceptance criteria:

- large campaigns either analyze full data or clearly report partial coverage
- keyword mismatch is never silently skipped due to response size
- autotargeting waste only runs when CriterionType coverage is present or explicitly missing

### Track B - Preflight safety

#### B1. Replace `landing_map`-only campaign validity with live-aware validation

Owner:

- `Marketing2025` pipeline / QA maintainer

Files:

- [`/Users/georgyagaev/Projects/Marketing2025/scripts/preflight/run_preflight_checks.py`](</Users/georgyagaev/Projects/Marketing2025/scripts/preflight/run_preflight_checks.py:99>)
- [`/Users/georgyagaev/Projects/Marketing2025/.claude/skills/preflight-qa/SKILL.md`](</Users/georgyagaev/Projects/Marketing2025/.claude/skills/preflight-qa/SKILL.md:21>)

Dependencies:

- consume the new MCP warnings / diagnostic fields from `yandex.ad`

Required changes:

- add a live MCP lookup or a validated imported snapshot as the source of truth for campaign existence/state
- recognize special/no-structure campaigns from MCP diagnostics
- distinguish:
  - real phantom campaigns
  - archived / moot campaigns
  - live campaigns with non-standard structure
- change special campaign handling from hard failure to `WARN` or `ESCALATE` where appropriate

Acceptance criteria:

- Telegram/special campaigns are not rejected solely because they are absent from `landing_map`
- `"(not in snapshot)"` placeholders no longer overrule live MCP diagnostics
- preflight report explicitly states which source decided campaign validity

#### B2. Add explicit preflight provenance for campaign status decisions

Owner:

- `Marketing2025` pipeline / QA maintainer

Required changes:

- attach per-record evidence fields showing whether validity came from `landing_map`, live MCP, or both
- include conflict reporting when local mapping and MCP disagree

Acceptance criteria:

- a reviewer can explain every `CAMPAIGN_VALID` verdict from artifacts alone

### Track C - Gap workflow resilience

#### C1. Add degraded execution path for `gap-overlay-report`

Owner:

- `Marketing2025` workflow maintainer

Files:

- [`/Users/georgyagaev/Projects/Marketing2025/.claude/skills/gap-overlay-report/SKILL.md`](</Users/georgyagaev/Projects/Marketing2025/.claude/skills/gap-overlay-report/SKILL.md:116>)

Required changes:

- detect whether `Task()` is available before launching parallel workers
- define a sequential fallback path for Analyst, SEO, SERP, and Strategist stages
- reuse cached artifacts where possible
- fail early with a single clear reason when neither parallel nor degraded execution is possible

Acceptance criteria:

- the skill can complete without `Task()`
- autonomous pipeline runs do not silently stall in this stage
- artifact logs show whether the normal or degraded path was used

#### C2. Add capability checks at `/pipeline` entry

Owner:

- `Marketing2025` orchestrator maintainer

Files:

- [`/Users/georgyagaev/Projects/Marketing2025/.claude/skills/pipeline/SKILL.md`](</Users/georgyagaev/Projects/Marketing2025/.claude/skills/pipeline/SKILL.md:13>)
- [`/Users/georgyagaev/Projects/Marketing2025/scripts/run_pipeline.sh`](</Users/georgyagaev/Projects/Marketing2025/scripts/run_pipeline.sh:17>)

Required changes:

- verify required agent capabilities before the unattended run begins
- stop early if the workflow configuration is incompatible with autonomous mode

Acceptance criteria:

- cron mode cannot enter an interactive or unsupported branch by accident

### Track D - Deterministic synthesis gates

#### D1. Add `MODEL_EXISTS` / product existence validation

Owner:

- `Marketing2025` synthesis maintainer

Files:

- [`/Users/georgyagaev/Projects/Marketing2025/scripts/pipeline/synthesis_quality_gate.py`](</Users/georgyagaev/Projects/Marketing2025/scripts/pipeline/synthesis_quality_gate.py:1>)

Required changes:

- load offerings as an input to the quality gate
- validate concrete product/model references against current offerings
- distinguish:
  - exact product match
  - alias / normalized match
  - unknown / hallucinated reference
- make unknown concrete products blocking for ads / ops recommendations

Acceptance criteria:

- invalid product/model references fail before B2B review or render
- reports show which offering entry matched each product-bearing recommendation

#### D2. Strengthen provenance requirements for deterministic budget logic

Owner:

- `Marketing2025` synthesis maintainer

Files:

- [`/Users/georgyagaev/Projects/Marketing2025/scripts/pipeline/populate_source_records.py`](</Users/georgyagaev/Projects/Marketing2025/scripts/pipeline/populate_source_records.py:1>)
- pipeline orchestration around `populate_source_records.py`

Required changes:

- return warning on any unresolved `source_records`
- emit unresolved IDs and counts into a machine-readable report
- allow the pipeline to block when budget-bearing or high-priority recs still lack provenance

Acceptance criteria:

- partial provenance no longer looks like a clean pass
- budget evidence checks can rely on source traceability

## Recommended Execution Order

1. Fix preflight campaign validity (`B1`, `B2`)
2. Fix audit false positives and completeness (`A1`, `A2`)
3. Add `Task()` degraded path (`C1`, `C2`)
4. Add deterministic product existence and provenance tightening (`D1`, `D2`)
5. Add regression tests for all reviewed cases

## Regression Test Matrix

Minimum scenarios to pin:

- DRAFT autotargeting false positive case from the May 7 review
- live DRAFT autotargeting case that should still fail
- Telegram/special campaign that is live but absent from `landing_map`
- large campaign whose keyword data exceeds a single MCP response page
- `gap-overlay-report` run without `Task()`
- recommendation referencing a non-existent product/model
- backlog item with empty `source_records` after post-processing

## Cross-Repo Dependency On `yandex.ad`

`Marketing2025` should consume these MCP-side improvements instead of preserving workarounds:

- special/no-structure campaign warnings and diagnostics
- paginated HF discovery results
- `metrica.hf.report_*` auto-pagination and truncation warnings
- Wordstat batch fallback metadata
- corrected `direct.hf.report_keywords`

## Done Means

The handoff is complete when a fresh autonomous `/pipeline` run:

- does not flag dormant DRAFT structures as urgent waste
- does not reject live special campaigns as phantom
- can proceed when `Task()` parallelism is unavailable
- blocks concrete product hallucinations before review/render
- exposes missing provenance explicitly instead of hiding it

