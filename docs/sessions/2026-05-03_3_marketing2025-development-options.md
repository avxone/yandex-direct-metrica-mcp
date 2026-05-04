# Session 2026-05-03 (3) — Development options for `Marketing2025`

## Completed
- Reassessed `yandex.ad` development priorities against the real usage pattern in `Marketing2025`.
- Confirmed that the main user path is:
  - read-heavy, multi-account Analyst workflows
  - smaller guarded Ads + QA write workflows
  - strong sensitivity to context budget and orchestration cost
- Extended the assessment with the `Voicexpert` pipeline test runs:
  - `yandex.ad` is also a machine-consumed data substrate for snapshot/research/synthesis/QA phases
  - pipeline quality issues point to a need for cleaner contracts and more stable machine-readable outputs
- Added a focused options note:
  - `docs/marketing2025-development-options-2026-05-03.md`
- Recommended a balanced path:
  - Path A (backend hygiene) now
  - selective Path B (Analyst-oriented read-layer improvements) next
  - Path C (role-aware discovery artifacts) after that
  - Path D (MCP Apps / interactive UI) later

## To Do
- Decide which specific Phase 1 metadata improvements are worth doing first for the highest-usage tools.
- Decide whether to draft a formal tool proposal for a small number of Analyst-oriented read-only composite tools.
- Decide whether role-aware bundle manifests belong in:
  - backend MCP docs only
  - MCP prompts/resources
  - or the separate orchestrator layer
- Keep MCP Apps exploration limited to dashboard UX until the read path is more stable.
