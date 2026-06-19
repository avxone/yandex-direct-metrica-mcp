# Unfinished Work Register

Date: 2026-06-18

This file records work that has been started or identified but is not yet logically complete. It is intended as input for future agent tasks.

## 1. PRO HTML Dashboard Generator

Status: started, not released.

Observed local changes:

- modified `src/mcp_yandex_ad/server.py`;
- modified `src/mcp_yandex_ad/tools.py`;
- modified `docs/templates/dashboard-template-option1-2026-02-17.html`;
- untracked `scripts/generate_dashboard_pro_html.py`;
- untracked `tests/test_dashboard_pro.py`;
- untracked `docs/dashboard-pro-html.md`;
- untracked `docs/ru/dashboard-pro-html.md`;
- untracked `docs/sessions/2026-05-12_1_pro-html-dashboard.md`.

Known issue:

- `scripts/generate_dashboard_pro_html.py` references old removed Wordstat OAuth config fields and must be adapted to the current Yandex Search API credentials or removed from the feature scope.

Next logical step:

- decide whether to finish this as a pro-only tool, split it into a separate PR, and update it for Search API credentials before tests/release.

## 2. Yandex Search API Web Search Tools

Status: researched/documented, not implemented.

Observed local docs:

- untracked `docs/yandex-search-api-web-search-2026-06-18.md`;
- untracked `docs/ru/yandex-search-api-web-search-2026-06-18.md`.

Goal:

- add MCP tools for Yandex Search API web search so Marketing2025 can reduce browser-based Yandex SERP parsing.

Candidate tools:

- `search_api.web_search`;
- `search_api.serp_parse`;
- `search_api.site_search`;
- `search_api.competitors`;
- `search_api.snippets`;
- `search_api.search_preflight`;
- optional cache tools if needed.

Next logical step:

- write a short feature spec, confirm exact Search API methods and response schema, then implement read-only MCP tools with tests and docs.

## 3. Marketing2025 Pipeline Migration

Status: MCP smoke checked, pipeline migration not done.

Completed context:

- Marketing2025 Claude config points `ydm-mcp-pro-dev` to local Docker image `yandex-direct-metrica-mcp-pro:dev`;
- local `pro:dev` image was retagged to the plugin-enabled 2.0.11 build;
- direct MCP stdio smoke showed key Wordstat and dashboard tools are present and responding.

Remaining work:

- restart Claude/MCP session so Marketing2025 uses the new image;
- inspect the Marketing2025 pipeline that currently parses Yandex SERP through a browser;
- replace eligible browser parsing with Search API MCP tools after those tools exist;
- add fallback behavior for cases not covered by Search API;
- add smoke tests or a handoff document for the new pipeline.

## 4. PRO Docker Image With BI Plugin in GHCR

Status: local image fixed, remote workflow incomplete.

Completed context:

- local `yandex-direct-metrica-mcp-pro:dev`;
- local `yandex-direct-metrica-mcp-pro:2.0.11-local`;
- local `yandex-direct-metrica-mcp-pro-bi:2.0.11-local`;
- all point to a plugin-enabled pro image with `yandex-direct-metrica-mcp-pro-bi 2.0.7`.

Remaining work:

- update the gated PRO Docker publish workflow so the BI plugin wheel can be installed during pro image builds where intended;
- verify GHCR private pro image access and manifest after publish;
- document whether the official pro tag is plain pro or pro+bi.

Risk:

- publishing private pro images must remain gated and must not expose private plugin code in the public image.

## 5. Release 2.0.11 Follow-Up Hygiene

Status: release completed, some follow-up checks remain useful.

Completed:

- public `v2.0.11` release exists;
- `pro-v2.0.11` tag exists;
- public Docker image verified;
- Wordstat migrated to Yandex Search API;
- old `YANDEX_WORDSTAT_*` configuration wording removed from current release docs and code paths.

Remaining useful checks:

- confirm any stale historical docs mentioning old Wordstat OAuth helpers are either explicitly historical or updated;
- verify GitHub UI, tags, and Docker manifests still agree after cache delays;
- ensure future release docs mention Search API credentials only.

## 6. Automation / Agent Operating Layer

Status: initial plan captured, not fully installed.

Started:

- `docs/automation/agent-development-operating-plan-2026-06-18.md`;
- `docs/automation/unfinished-work-2026-06-18.md`.

Remaining work:

- create `WORKFLOW.md`;
- create release gate docs;
- create GitHub issue templates;
- define the first agent-ready task for Search API Web tools;
- decide whether to use GitHub Issues, Symphony/Linear, or a small custom orchestrator.

## 7. Stale Marketing2025 Handoff Docs

Status: untracked and likely stale.

Observed local docs:

- untracked `docs/marketing2025-release-handoff-2026-05-08.md`;
- untracked `docs/ru/marketing2025-release-handoff-2026-05-08.md`;
- untracked `docs/sessions/2026-05-08_2_marketing-release-handoff.md`.

Next logical step:

- review whether these should be updated for the Search API migration or discarded before any future release documentation cleanup.

