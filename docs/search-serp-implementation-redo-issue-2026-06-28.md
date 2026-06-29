# Issue Draft: Re-run `search_serp` implementation with publishable output

## Execution Profile

- Issue Class: feature
- Risk: high

## Title

Implement `search_serp` MCP tool and client handoff with a valid publishable branch

## Type

Feature / integration / documentation

## Release Required

yes

## Suggested Labels

- `symphony`
- `issue-type:feature`
- `search-api`
- `web-search`
- `marketing2025`
- `feature`
- `release-required`
- `next-release`

## Supersedes

This issue replaces the invalid execution chain around:

- `GEO-7`
- `GEO-8`

Reason:

- the prior feature/PR chain did not result in a recoverable implementation branch or commit;
- the PR follow-up had nothing publishable to publish;
- this replacement issue must produce real repo changes that can move through PR and release stages.

## Ownership Boundary

This issue is owned by the `yandex.ad` repository.

Allowed:

- MCP server changes in this repo;
- tests, docs, tool contracts, release notes, and handoff docs in this repo;
- live validation proving the server exposes the needed data.

Not part of this issue unless explicitly approved in a separate task:

- editing files in `Marketing2025/`;
- changing client prompts/scripts/workflows;
- changing client artifact formats in-place.

If client-side adaptation is needed, this issue must end with an explicit handoff that tells the client what to change.

## Required Capabilities

- browser: `operator-browser`
- live-api: yes
- manual-check: yes
- operator step required: yes

## External Inputs / Secrets

- required env:
  - `YANDEX_SEARCH_API_FOLDER_ID`
  - `YANDEX_SEARCH_API_API_KEY` or equivalent active Search API credential
- source of truth:
  - `/Users/georgyagaev/mcp/state/yandex.ad/.env`
- available to Symphony parent process before `Todo`: yes

## Blocked Input Policy

- move to `Backlog` if:
  - Search API credentials are unavailable in the Symphony parent process and cannot be sourced from the approved external state file
  - bounded live Search API validation cannot run
  - required manual browser-visible SERP comparison cannot be completed in the current environment
- return to `Todo` only for:
  - code defects
  - test failures
  - parser/contract/docs drift
  - missing artifacts that the agent can generate inside this repo

## Background

`Marketing2025` currently has a SERP workflow that depends on Playwright against live Yandex result pages.

The client needs server-side access to:

- organic results;
- ad results;
- top ad slot count;
- ad titles/snippets;
- region/device control;
- stable, reviewable normalization;
- explicit compatibility notes for current client expectations.

The implementation must live in `yandex.ad` first. Direct client-repo edits are out of scope for this feature issue.

## Goal

Implement a bounded MCP-side `search_serp` capability in `yandex.ad`, validate that it exposes the data the client needs, and produce a handoff document for `Marketing2025`.

This issue must produce actual repo changes that can be committed, reviewed, published as a PR, and later released.

## Scope

### 1. Add `search_serp` to MCP

Add a bounded MCP tool around Yandex Search API with this input shape:

```json
{
  "query": "гарнитура для колл центра купить",
  "region": 213,
  "device": "desktop",
  "format": "html",
  "mode": "sync",
  "n_results": 10
}
```

Expected normalized output:

```json
{
  "query": "...",
  "region": 213,
  "device": "DEVICE_DESKTOP",
  "ads": [
    {"domain": "...", "title": "...", "snippet": "...", "position": 1}
  ],
  "ads_count_top": 3,
  "organic": [
    {"domain": "...", "title": "...", "url": "...", "position": 1}
  ],
  "captcha": false
}
```

Required behaviors:

- support region as a parameter, defaulting to configured server default;
- support device as a parameter;
- support `html` mode for the first implementation because ads are required;
- normalize ads and organic results on the MCP side;
- keep raw HTML optional, not default;
- keep runtime payload and public output schema aligned.

### 2. Keep parsing responsibility inside MCP

The agent should not parse raw SERP HTML in prompt space.

### 3. Validate client data coverage

Required comparison:

- requested client fields;
- actual `search_serp` fields;
- compatibility notes;
- known gaps or caveats.

### 4. Write client handoff

Add a handoff doc in this repo that acts as the adoption note for `Marketing2025`.

It must include:

- what new MCP tool to call;
- request and response examples;
- which current client expectations are preserved;
- what differs from the current client path;
- what the client should change on their side;
- what can remain fallback.

### 5. Update MCP docs and release notes

Update:

- MCP docs for `search_serp`;
- tool proposal / contract docs;
- changelog or release-facing notes;
- session note for the work.

## Non-goals

- do not edit `Marketing2025` files in this issue;
- do not silently redefine client responsibilities;
- do not introduce writes;
- do not publish a release directly from this feature issue;
- do not add unrelated search helpers.

## Acceptance Criteria

- MCP exposes a bounded `search_serp` tool with normalized ads plus organic results;
- the public tool contract matches the runtime payload;
- the issue includes explicit client compatibility notes;
- the issue includes a client handoff document;
- docs clearly state what data is available and what the client must adapt if needed;
- the issue results in a real publishable repo diff, not only notes or comments.

## Feature Validation

- `python -m compileall -q src/mcp_yandex_ad`
- repo tests covering the touched surface, including parser/config/contract behavior
- changed-line lint via `python scripts/agent_lint.py`
- runtime payload, tool schema, snapshots, and docs remain aligned
- client handoff document exists in this repo
- bounded read-only live validation for `search` is required because this is a high-risk external API parsing feature
- 3 to 5 real project queries with a short manual sanity note comparing API-derived output to browser-visible SERP structure
- manual browser-visible SERP comparison is an `operator-browser` step; the agent must prepare the checklist and evidence note, but the operator owns the visible browser check when anti-bot gating prevents deterministic automation

## PR Validation

- branch can be created from the approved feature result
- commit is created from the approved feature result
- branch can be pushed
- GitHub PR can be created or updated
- PR body references the feature handoff/result accurately

## Release Validation

- `python scripts/live_validation.py --suite search`
- release notes and version metadata are updated
- release guard passes
- GitHub Release and image publication checks pass
