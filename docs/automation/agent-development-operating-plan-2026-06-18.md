# Agent Development Operating Plan

Date: 2026-06-18

This document captures the target operating model for moving this project toward agent-driven development. The goal is not to study agent tooling for months, but to create a practical process where the user states goals and functions, and agents handle specification, implementation, verification, and release preparation.

## Objective

Create a development pipeline where human input is focused on:

- setting product goals;
- approving scope;
- providing or rotating credentials when required;
- approving merge and release gates;
- rejecting product mismatches.

Agents should handle the rest: task shaping, code changes, tests, documentation, PRs, release preparation, and follow-up tracking.

## Why This Follows Harness Engineering

OpenAI's harness engineering direction treats the repository, instructions, tests, and workflows as the "harness" that lets agents execute reliably. Symphony is one reference implementation of this idea: an orchestrator polls work items, creates isolated workspaces, starts an agent runner, and tracks progress.

For this project, the useful lesson is the operating model, not a requirement to adopt Symphony as production infrastructure immediately.

## Agent Roles

### Product / Spec Agent

Turns a user goal into a bounded task:

- problem statement;
- acceptance criteria;
- affected MCP tools and APIs;
- files and docs likely to change;
- test plan;
- risks and out-of-scope items.

### Implementation Agent

Implements the approved task:

- creates a focused branch;
- updates code, tests, and docs;
- follows existing repo patterns;
- does not mix unrelated dirty worktree changes into the task.

### Review Agent

Reviews the diff before merge:

- behavioral regressions;
- public/pro/pro-bi boundary violations;
- secrets exposure;
- missing tests;
- stale docs or release notes.

### QA Agent

Runs verification:

- unit tests;
- compile checks;
- Docker public/pro checks where relevant;
- MCP smoke tests;
- plugin checks for pro-bi work.

### Release Agent

Prepares releases, but does not perform dangerous final actions without approval:

- version bump;
- changelog;
- release notes;
- tags;
- GitHub Release draft;
- public Docker verification;
- pro/pro-bi local or gated workflow verification.

Manual approval is required for:

- pushing to `main`;
- creating or moving tags;
- publishing GitHub Releases;
- pushing Docker images;
- publishing private pro images;
- using or changing secrets.

### Ops / Memory Agent

Keeps the project state clean:

- tracks started but unfinished work;
- updates session notes;
- finds stale docs;
- proposes cleanup issues;
- checks that release state matches GitHub, Docker, and local images.

## Implementation Phases

### Phase 1: Agent-Ready Repository

Target duration: 1-2 days.

Deliverables:

- `WORKFLOW.md` for agent task execution;
- `docs/automation/agent-development-operating-plan-2026-06-18.md`;
- `docs/automation/unfinished-work-2026-06-18.md`;
- issue templates for feature, bug, release, investigation, and Marketing2025 workflow tasks;
- release gate documentation.

### Phase 2: Semi-Autopilot PR Flow

Target duration: 2-4 days.

Flow:

1. User creates or states a goal.
2. Spec Agent writes scope and acceptance criteria.
3. User approves or adjusts scope.
4. Implementation Agent creates a branch and implements.
5. Review Agent reviews.
6. QA Agent verifies.
7. PR is opened.
8. User merges or sends to rework.

Initial tasks should be safe and bounded: docs cleanup, tests, small features, and MCP read tools.

### Phase 3: Release Lane

Target duration: about 1 week after the PR flow works.

The Release Agent prepares release candidates end to end, but final release operations remain approval-gated.

Required checks:

- `pytest -q`;
- compile check for `src/mcp_yandex_ad`;
- no secrets in diff;
- changelog updated;
- public/pro boundaries preserved;
- public Docker image safe by default;
- pro image verified where relevant;
- pro-bi plugin wheel verified where relevant;
- GitHub Release and Docker image state verified after publish.

### Phase 4: Marketing2025 Integration Lane

Goal: reduce browser-based Yandex SERP parsing by adding Search API powered MCP tools.

Candidate MCP tools:

- `search_api.web_search`;
- `search_api.serp_parse`;
- `search_api.site_search`;
- `search_api.competitors`;
- `search_api.snippets`;
- `search_api.search_preflight`;
- `search_api.cache.*` if caching becomes necessary.

Expected Marketing2025 changes:

- replace browser scraping with MCP Search API calls where possible;
- keep browser parsing only as fallback;
- add smoke tests for real Search API credentials;
- document the pipeline contract.

### Phase 5: Full Orchestrator

After several successful PR tasks, choose an orchestrator:

- GitHub Issues plus a local Codex/Claude runner for the fastest start;
- Symphony plus Linear if queue management and isolated workspaces become more important;
- a small custom orchestrator if GitHub/Docker/MCP-specific release logic dominates.

Recommended path: start with GitHub Issues and local runners, use Symphony as a reference architecture, and build a custom hardened layer only after the workflow has proven useful.

## First 10-Day Plan

Day 1:

- create agent operating docs;
- define release gates;
- create issue templates.

Day 2:

- create first agent task for Yandex Search API Web tools;
- have the Spec Agent produce scope;
- approve scope.

Days 3-4:

- implement Search API Web tools;
- add tests and docs;
- open PR.

Day 5:

- review;
- QA;
- smoke test with real Search API credentials;
- merge when accepted.

Days 6-7:

- integrate Marketing2025 pipeline;
- replace browser parsing where Search API covers the need;
- document handoff.

Days 8-9:

- prepare release 2.0.12;
- verify public Docker;
- verify pro Docker;
- verify pro-bi plugin;
- publish only after approval.

Day 10:

- postmortem;
- update `WORKFLOW.md`;
- create the next task batch.

