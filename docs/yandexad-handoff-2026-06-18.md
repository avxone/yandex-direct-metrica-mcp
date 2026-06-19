# `yandex.ad` Handoff - 2026-06-18

## Purpose

This handoff captures the current state after the Wordstat migration to Yandex Search API, release 2.0.11 cleanup, Docker/pro-bi checks, Marketing2025 MCP smoke checks, and the new agent-development operating plan.

Use this document at the start of the next session to continue without rediscovering context.

## Executive Summary

The old Wordstat endpoint is no longer the right integration point. Wordstat API access now works through Yandex Search API credentials:

- `YANDEX_SEARCH_API_FOLDER_ID`
- `YANDEX_SEARCH_API_API_KEY` or `YANDEX_SEARCH_API_IAM_TOKEN`

Release `v2.0.11` is published and contains the Wordstat migration and cleanup from old `YANDEX_WORDSTAT_*` OAuth wording in current code/docs. Public Docker `v2.0.11` is verified. A local pro/pro-bi Docker image with the BI plugin is verified and tagged for Marketing2025 use, but the remote GHCR pro workflow still needs follow-up if official pro images must include the BI plugin.

The next strategic work should be to make the repo agent-ready and then use that process to implement Yandex Search API Web Search MCP tools, so Marketing2025 can stop relying on browser-based Yandex SERP parsing where API coverage is sufficient.

## Current Git / Release State

Known completed release state:

- `main`, `origin/main`, `v2.0.11`, and `pro-v2.0.11` point to the clean Wordstat Search API release commit from the previous work.
- GitHub Release exists for `v2.0.11`.
- Public Docker image was verified:
  - `ghcr.io/georgy-agaev/yandex-direct-metrica-mcp:v2.0.11`
  - `ghcr.io/georgy-agaev/yandex-direct-metrica-mcp:latest`
- Public image verification showed core `2.0.11` and no plugins.

Known current dirty / untracked worktree items before this handoff:

- modified `CHANGELOG.md`
- modified `docs/templates/dashboard-template-option1-2026-02-17.html`
- modified `src/mcp_yandex_ad/server.py`
- modified `src/mcp_yandex_ad/tools.py`
- untracked dashboard pro docs/tests/script files
- untracked Marketing2025 release handoff docs
- untracked Search API Web Search research docs
- new automation docs added in this session

Do not revert unrelated dirty work. Treat it as started-but-unfinished work unless the user explicitly asks to discard it.

## Important Credentials / Secrets Rule

Do not store or print secrets.

The user tested Yandex Search API successfully with a temporary API key and planned to rotate it. Do not repeat any key values in future notes, logs, or docs.

The configuration model should use:

- `YANDEX_SEARCH_API_FOLDER_ID`
- `YANDEX_SEARCH_API_API_KEY`
- optional `YANDEX_SEARCH_API_IAM_TOKEN`
- optional `YANDEX_SEARCH_API_WORDSTAT_BASE_URL`

Avoid reintroducing old Wordstat OAuth envs such as `YANDEX_WORDSTAT_ACCESS_TOKEN`, `YANDEX_WORDSTAT_CLIENT_ID`, or related refresh helper wording in current docs.

## Confirmed Wordstat / Search API Facts

Old endpoint:

- `https://api.wordstat.yandex.net/v1/` is obsolete or misrouted.
- TLS hostname verification fails because the certificate does not cover `api.wordstat.yandex.net`.
- Even with TLS verification bypassed, old paths such as `/v1/userInfo` and `/v1/topRequests` returned `404 Not found`.

New endpoint:

- `https://searchapi.api.cloud.yandex.net/v2/wordstat/...`
- verified TLS works.
- unauthenticated request returns expected auth error.
- authenticated `topRequests` request returned HTTP 200 with Wordstat data.

Current Wordstat paths:

- `/v2/wordstat/topRequests`
- `/v2/wordstat/dynamics`
- `/v2/wordstat/regions`
- `/v2/wordstat/getRegionsTree`

## Marketing2025 Context

The Marketing2025 Claude configuration points `ydm-mcp-pro-dev` at:

- Docker image: `yandex-direct-metrica-mcp-pro:dev`
- env file: `/path/to/yandex.ad/.env`
- state mount: `/path/to/yandex.ad:/data`
- accounts file: `/data/accounts.json`

Local pro image status:

- `yandex-direct-metrica-mcp-pro:dev` was retagged to a plugin-enabled 2.0.11 image.
- The local image includes `yandex-direct-metrica-mcp-pro-bi 2.0.7`.
- Direct MCP stdio smoke showed the server starts and exposes expected Wordstat/dashboard tools.

Remaining Marketing2025 work:

- restart Claude/MCP session so it uses the new local image;
- inspect the current Marketing2025 pipeline that parses Yandex SERP through browser automation;
- add MCP Search API Web tools in this repo;
- update Marketing2025 to call those tools instead of browser parsing where possible;
- keep browser fallback only for uncovered cases;
- add smoke tests or a handoff doc for the new pipeline contract.

## New Automation / Agent Plan Docs

Added in this session:

- [`docs/automation/agent-development-operating-plan-2026-06-18.md`](automation/agent-development-operating-plan-2026-06-18.md)
- [`docs/automation/unfinished-work-2026-06-18.md`](automation/unfinished-work-2026-06-18.md)
- [`docs/sessions/2026-06-18_2_agent-development-operating-plan.md`](sessions/2026-06-18_2_agent-development-operating-plan.md)

Core idea:

- move toward an agent-driven process where the user states goals and functions;
- agents handle spec, implementation, review, QA, PRs, and release preparation;
- final merge/release/publish operations remain human-approved.

Recommended agent roles:

- Product / Spec Agent
- Implementation Agent
- Review Agent
- QA Agent
- Release Agent
- Ops / Memory Agent

## Started But Unfinished Work

Use [`docs/automation/unfinished-work-2026-06-18.md`](automation/unfinished-work-2026-06-18.md) as the primary register.

Current items:

1. PRO HTML Dashboard Generator
   - started but not released;
   - has code/docs/tests/script changes;
   - script still references removed old Wordstat OAuth config and needs Search API adaptation or removal from scope.

2. Yandex Search API Web Search Tools
   - researched/documented but not implemented;
   - intended to reduce Marketing2025 browser SERP parsing.

3. Marketing2025 Pipeline Migration
   - MCP smoke checked;
   - actual pipeline migration not done.

4. PRO Docker Image With BI Plugin in GHCR
   - local pro/pro-bi image works;
   - remote gated pro workflow still needs update/verification if official pro images should include BI plugin.

5. Release 2.0.11 Follow-Up Hygiene
   - release is done;
   - future docs should not drift back to old Wordstat OAuth wording.

6. Automation / Agent Operating Layer
   - plan captured;
   - `WORKFLOW.md`, release gates, and issue templates not yet created.

7. Stale Marketing2025 Handoff Docs
   - untracked May 2026 handoff docs need review/update/discard decision.

## Recommended Next Session Path

### Step 1. Stabilize the agent operating layer

Create:

- `WORKFLOW.md`
- `docs/automation/release-gates.md`
- GitHub issue templates for:
  - feature;
  - bug;
  - release;
  - investigation;
  - Marketing2025 workflow.

Acceptance criteria:

- a future agent can pick up a GitHub issue and know how to plan, implement, verify, and stop for approval.

### Step 2. Turn Search API Web Search into the first agent-ready feature

Create a feature spec for read-only MCP tools:

- `search_api.web_search`
- `search_api.serp_parse`
- `search_api.site_search`
- `search_api.competitors`
- `search_api.snippets`
- `search_api.search_preflight`

Confirm exact Yandex Search API web-search request/response schema from official docs before implementation.

Acceptance criteria:

- no browser required for basic SERP collection;
- no write or paid destructive actions;
- clear errors for missing folder/API key/billing/permission issues;
- mocked unit tests;
- docs in EN and RU if added to public usage surface.

### Step 3. Integrate with Marketing2025

After MCP Search API tools exist:

- inspect Marketing2025 pipeline;
- replace eligible browser scraping calls;
- keep fallback path;
- smoke test with real credentials;
- document the pipeline contract.

### Step 4. Prepare the next release

Likely target:

- `v2.0.12`

Release should include:

- Search API Web tools if completed;
- automation docs if desired;
- any relevant docs cleanup.

Keep release gates approval-based:

- tests;
- compile;
- changelog;
- no secrets;
- public Docker safe-by-default;
- pro/pro-bi checks if relevant;
- GitHub release;
- Docker manifest verification.

## Commands Worth Reusing

Repo health:

```bash
git status --short
pytest -q
python -m compileall -q src/mcp_yandex_ad
```

Public Docker smoke:

```bash
docker run --rm ghcr.io/georgy-agaev/yandex-direct-metrica-mcp:v2.0.11 python -c "import importlib.metadata as m; print(m.version('yandex-direct-metrica-mcp'))"
```

Local pro plugin check:

```bash
docker run --rm yandex-direct-metrica-mcp-pro:dev python -c "import importlib.metadata as m; print(m.version('yandex-direct-metrica-mcp')); print(m.version('yandex-direct-metrica-mcp-pro-bi'))"
```

Search API Wordstat smoke shape:

```bash
curl -i -s -X POST 'https://searchapi.api.cloud.yandex.net/v2/wordstat/topRequests' \
  -H "Authorization: Api-Key ${YANDEX_SEARCH_API_API_KEY}" \
  -H 'Content-Type: application/json' \
  --data "{\"folderId\":\"${YANDEX_SEARCH_API_FOLDER_ID}\",\"phrase\":\"купить кондиционер\",\"numPhrases\":5}"
```

## Cautions

- Do not expose or commit API keys.
- Do not re-add old Wordstat OAuth helper flows.
- Do not mix the unfinished PRO HTML dashboard feature into unrelated Search API work.
- Do not publish pro/pro-bi images automatically.
- Do not assume GitHub UI cache reflects current Docker/tag state; verify manifests or workflow output.
- Do not rely on `claude mcp list` alone for MCP health because it previously failed for all servers, not only this one. Prefer direct stdio smoke tests.
