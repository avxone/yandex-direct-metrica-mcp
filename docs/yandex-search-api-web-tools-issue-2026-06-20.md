# Issue Draft: Add `search_serp` to yandex.ad and prepare Marketing2025 handoff

## Title

Add `search_serp` MCP tool and client handoff for Marketing2025 SERP migration

## Type

Feature / integration / documentation

## Release Required

yes

## Suggested Labels

- `symphony`
- `search-api`
- `web-search`
- `marketing2025`
- `feature`
- `release-required`
- `next-release`

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

## Background

`Marketing2025` currently has a SERP workflow that depends on Playwright against live Yandex result pages. The client has now clarified what information they need from `yandex.ad`:

- organic results;
- ad results;
- top ad slot count;
- ad titles/snippets;
- region/device control;
- stable, reviewable server-side normalization;
- clear compatibility guidance for the existing client workflow.

The client request is to implement the MCP-side capability first, then document how the client can adopt it. The MCP task should not silently expand into direct client-repo edits.

## Goal

Implement a bounded MCP-side `search_serp` capability in `yandex.ad`, validate that it exposes the data the client needs, and produce a handoff document for `Marketing2025`.

The first release must:

1. add one MCP tool contract centered on `search_serp`;
2. prove that the required client-facing data is available from the server;
3. preserve compatibility where possible and document incompatibilities where not;
4. produce a client handoff/release-note style document describing adoption steps.

## Decision Options

### Option A - Native Search API HTML plus MCP-side parsing

Use the official Yandex Search API in `html` mode, decode the returned page, and parse ads plus organic results on the MCP side.

Pros:

- stays on the first-party provider and existing billing path;
- removes CAPTCHA and browser scraping from the server-side solution;
- keeps parsing in one deterministic place instead of prompt space.

Cons:

- HTML parsing remains a maintenance point;
- ad extraction must be validated on real queries.

### Option B - Native Search API XML only

Implement only structured organic retrieval from XML.

Pros:

- smallest implementation surface.

Cons:

- does not satisfy the client need for ads, top ad count, or competitor ad copy.

### Option C - Third-party wrapper with structured ads

Use an external wrapper that already returns structured ads.

Pros:

- less local parsing work.

Cons:

- adds a third-party dependency and changes the trust/runtime model.

## Recommended Path

Use **Option A** for the first implementation.

## Proposed MCP Scope

Primary tool:

- `search_serp`

Optional supporting tool:

- `search_api.search_preflight`

Explicitly out of scope for this issue:

- direct `Marketing2025` repo edits;
- broad search toolkit expansion unrelated to the concrete client need;
- cache infrastructure;
- third-party search wrappers.

## Client Compatibility Target

The client currently expects data equivalent to:

- ads: domain, title, snippet, position;
- top ad slot count;
- organic: domain, title, url, position;
- region-specific response;
- deterministic server output suitable for downstream aggregation.

This issue must explicitly state:

1. which of those needs are fully covered by `search_serp`;
2. which are partially covered;
3. which require client-side adaptation;
4. whether the response format differs from the client’s current internal shape.

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

Allowed implementation shapes:

- move/adapt existing parsing logic into MCP;
- or create a new MCP-owned parser module and document any remaining fallback semantics.

### 3. Validate client data coverage

This issue must check that the MCP result exposes the fields the client actually needs.

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
- do not publish a release from this feature issue;
- do not add unrelated search helpers.

## Acceptance Criteria

- MCP exposes a bounded `search_serp` tool with normalized ads plus organic results;
- the public tool contract matches the runtime payload;
- the issue includes explicit client compatibility notes;
- the issue includes a client handoff document;
- docs clearly state what data is available and what the client must adapt if needed;
- no direct `Marketing2025` repo edits are required for this issue to be considered complete.

## Validation

Required validation for the implementation task:

- unit tests for request building and normalized parsing;
- local validation on 3 to 5 real project queries comparing API-derived results with manual browser inspection for ad extraction sanity;
- compile/test pass in this repo;
- docs review for MCP contract plus client handoff;
- explicit coverage table or equivalent reasoning proving that the client-requested information is available.

## Release Notes Draft

```markdown
Search API: added `search_serp` to yandex.ad with normalized ads and organic results, plus a client handoff for Marketing2025 SERP migration.
```

## Definition of Done

- approved tool-list change is documented if required;
- `search_serp` is implemented in MCP;
- runtime payload and published output schema match;
- real-query validation for data coverage passes;
- handoff doc for `Marketing2025` is written in this repo;
- tests and MCP-side docs are updated;
- the task passes through the feature-issue Symphony pipeline, then through release publication because the client needs a published image to consume the result.

## Handoff Notes

This issue ends at a server-side deliverable plus client adoption guidance.

If the client later wants direct prompt/script migration inside `Marketing2025`, create a separate client-side issue that consumes this server capability.
