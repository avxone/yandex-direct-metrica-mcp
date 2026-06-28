# Handoff: Linear + Symphony orchestration model for yandex.ad

Date: 2026-06-25

## Purpose

This note summarizes the current state of the `Linear + Symphony` setup for `yandex.ad`, the failure mode we hit, and the realistic options for moving to a full multi-stage agent pipeline.

The goal is to decide how to model:

- feature implementation;
- review;
- PR publication;
- release publication.

## Executive Summary

We tested a lane-per-state Symphony model and found that it does not cleanly fit the current Linear workflow states in the `Georgy Agaev` team.

Current available Linear states are:

- `Backlog`
- `Todo`
- `In Progress`
- `In Review`
- `Done`
- `Canceled`
- `Duplicate`

Missing states we previously assumed:

- `Approved`
- `Releasing`

Because those states do not exist, the current PR/release lane configuration cannot route work correctly.

## What happened

We first modeled the pipeline like this:

- implementation lane: `Todo` / `In Progress`
- review lane: `In Review`
- PR lane: `Approved`
- release lane: `Releasing`

That model is internally coherent, but it depends on two extra Linear states that the current team does not have.

Result:

- implementation lane worked;
- review lane worked;
- PR lane never started because no issue could enter `Approved`;
- release lane cannot be used as configured because no issue can enter `Releasing`.

We also considered routing PR/release from `Done`, but that is wrong for the current Symphony configuration because `Done` is a terminal state and terminal states are not dispatched.

## Core design problem

We need a process that supports all of these realities:

1. `Linear` currently has a simple state machine.
2. `Symphony` routes work by state and label.
3. Some feature issues are not really complete until a published Docker image exists.
4. We want clean auditability and retry behavior for each stage.
5. We do not want hidden orchestration logic spread across manual Linear UI actions.

## Options

## Option A: add new workflow states in Linear

Add:

- `Approved`
- `Releasing`

Then use:

- implementation lane -> `Todo` / `In Progress`
- review lane -> `In Review`
- PR lane -> `Approved`
- release lane -> `Releasing`

### Pros

- simplest mental model;
- clean visual state machine;
- one issue tracks the whole lifecycle;
- Symphony routing stays straightforward.

### Cons

- requires changing the team workflow in Linear;
- all colleagues must align on the new state semantics;
- one issue ends up representing multiple kinds of work:
  - feature implementation
  - publication
  - release

### Best use

Good if the team is comfortable evolving the Linear workflow itself.

## Option B: keep current states and route by labels inside `In Review`

Example:

- implementation lane -> `Todo` / `In Progress`
- review lane -> `In Review` + `review-ready`
- PR lane -> `In Review` + `pr-ready`
- release lane -> `In Review` + `release-ready`

### Pros

- no new Linear states needed;
- can be implemented quickly.

### Cons

- visually confusing;
- multiple very different meanings share the same `In Review` state;
- easier to misroute or deadlock issues;
- harder for humans to understand current phase at a glance.

### Best use

Only as a temporary workaround.

## Option C: create follow-up issues for PR and release

Model each stage as its own issue.

Flow:

1. `feature issue`
   - implementation
   - review
   - `Done`

2. `PR issue`
   - created automatically after successful feature completion
   - branch / commit / push / PR
   - review
   - `Done`

3. `release issue`
   - created automatically only when the feature is marked `release-required`
   - version bump / release notes / tags / GitHub Release / Docker publish / local docker sync
   - review
   - `Done`

### Pros

- works with the existing Linear states;
- each issue has one clear purpose;
- retries are cleaner;
- release work is explicit and auditable;
- no need to overload one issue with three different kinds of work;
- easiest way to preserve the standard `Todo -> In Progress -> In Review -> Done` loop for every stage.

### Cons

- more issues get created;
- we need API-driven orchestration to create and link follow-up issues;
- colleagues need to get used to a parent/child or chain-based flow.

### Best use

Best option if we want to keep the current Linear workflow unchanged.

## Recommendation

Recommended path: **Option C**.

Reason:

- it fits the current Linear setup without requiring state changes;
- it keeps each stage operationally clean;
- it is a better match for agent orchestration than overloading a single issue;
- it gives the best audit trail for “what exactly happened” at each stage.

## Recommended issue types

Use labels or a dedicated naming convention to distinguish issue roles:

- `issue-type:feature`
- `issue-type:pr`
- `issue-type:release`

Additional routing labels:

- `symphony`
- `release-required`

Optional:

- `generated-followup`

## Recommended flow

### 1. Feature issue

Human or Codex creates a feature issue.

Required fields:

- ownership boundary;
- release required: yes/no;
- handoff required: yes/no;
- acceptance criteria;
- validation.

Standard path:

- `Backlog` -> `Todo` -> `In Progress` -> `In Review` -> `Done`

When `Done`:

- if not `release-required`, auto-create PR issue;
- if `release-required`, still auto-create PR issue first.

### 2. PR issue

Created automatically from the feature issue.

Contents:

- source issue link;
- workspace handoff summary;
- required gates before publication;
- branch naming and PR body requirements.

Standard path:

- `Todo` -> `In Progress` -> `In Review` -> `Done`

When `Done`:

- if source feature had `release-required`, auto-create release issue.

### 3. Release issue

Created automatically only when needed.

Contents:

- source feature issue link;
- source PR link;
- release version target;
- live validation requirements;
- publish checklist.

Standard path:

- `Todo` -> `In Progress` -> `In Review` -> `Done`

## What should be configured in Linear

Minimum required in Linear:

1. keep existing states as-is;
2. use labels:
   - `symphony`
   - `release-required`
   - `issue-type:feature`
   - `issue-type:pr`
   - `issue-type:release`
3. optionally create a project view filtered by each issue type.

Important:

The orchestration logic should live in our harness, not in manual Linear UI workflow rules.

Linear should remain:

- the queue;
- the visual board;
- the notification surface;
- the source of truth for issue status.

## What should be implemented on our side

The following logic should be implemented in the harness/API layer:

1. detect when a feature issue reaches `Done`;
2. create a PR issue automatically via Linear GraphQL `issueCreate`;
3. carry over:
   - title context;
   - source issue link;
   - key labels;
   - handoff summary;
4. detect when a PR issue reaches `Done`;
5. if `release-required` is present, create a release issue automatically;
6. comment cross-links into all related issues.

## Suggested issue chain format

### Feature issue title

`GEO-7 Add search_serp MCP tool and client handoff for Marketing2025 SERP migration`

### PR issue title

`PR for GEO-7: publish search_serp implementation`

### Release issue title

`Release for GEO-7: publish search_serp client-ready image`

## Suggested cross-links

Every generated issue should include:

- source issue URL;
- previous stage issue URL;
- expected next stage;
- definition of completion for this stage only.

## How `release-required` should work

`release-required` means:

- the client cannot practically validate or consume the feature until a published image exists;
- therefore the overall business outcome is not complete at PR creation time;
- but PR publication and release publication should still be separated as different issues.

This is important for `yandex.ad`, because a server feature often becomes usable only after the Docker image is published and pulled by client environments.

## Why not use one issue for everything

A single issue covering:

- implementation;
- review;
- PR publication;
- release publication

looks simpler at first, but in practice it blurs ownership and makes recovery harder.

Problems:

- stage boundaries are unclear;
- partial failures are messy;
- review comments mix code review with release ops;
- it is harder to restart only one failed stage.

## Proposed rollout

### Phase 1

Keep the current docs and lane files, but stop treating PR/release as state-based follow-up inside the same issue.

### Phase 2

Add follow-up issue creation to the harness:

- `feature Done` -> create PR issue
- `PR Done` + `release-required` -> create release issue

### Phase 3

Route Symphony lanes by issue type:

- implementation/review lanes can be reused;
- prompts differ by `issue-type`.

### Phase 4

Optionally add nicer Linear views or automations for visibility only.

## Open questions for team discussion

1. Do we want to keep the current Linear state machine unchanged?
2. Are colleagues comfortable with auto-generated follow-up issues?
3. Should PR and release issues live in the same project board as feature issues?
4. Do we want a lightweight parent/child relationship convention for chained issues?
5. Should release issues require explicit human approval before entering `Todo`?

## My recommendation

If the goal is operational clarity and a process that survives real failures, use:

- current Linear states unchanged;
- issue-type labels;
- automatic follow-up issue creation in our harness;
- `release-required` as the signal that a feature must continue into publication.

That gives the cleanest process without forcing immediate changes to the current Linear workflow.
