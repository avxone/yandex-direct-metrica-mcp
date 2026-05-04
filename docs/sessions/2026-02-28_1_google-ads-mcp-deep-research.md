# Session 2026-02-28 (1) — Google Ads MCP deep research + project brief

## Completed
- Reviewed current Google Ads MCP landscape:
  - Read-only/minimal GAQL wrappers
  - Large write-capable open-source servers
  - Remote/SaaS cross-platform ad MCP products
- Extracted the main differentiator for our approach: compete on workflow safety and reproducibility (plan → apply → QA → post-check) rather than tool count.
- Drafted a SaaS-ready self-hosted project brief, including architecture, tool surface v0, and a repo split recommendation:
  - `docs/research-google-ads-mcp-2026-02-28.md`

## To Do
- Decide the target packaging:
  - single repo (core + optional plugin) vs split repos (core / pro / skills)
- Confirm auth approach for MVP (`google-ads.yaml` only vs add ADC support).
- Draft a `tools-proposal-YYYY-MM-DD.md` for the new Google Ads project (separate repo), including:
  - OSS core read-only tools
  - PRO plugin write workflows and their safety constraints
- Define the first 5–10 skills aligned with the “Dream Team” roles:
  - campaign structure planner
  - UTM audit + fix
  - negative keywords sweep
  - post-launch QA (24h)
  - weekly executive summary

