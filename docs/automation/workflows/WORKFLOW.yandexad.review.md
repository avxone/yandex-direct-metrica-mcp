---
tracker:
  kind: linear
  api_key: $LINEAR_API_KEY
  project_slug: "ca8365801feb"
  required_labels:
    - symphony
  active_states:
    - In Review
  terminal_states:
    - Done
    - Canceled
    - Cancelled
    - Duplicate
workspace:
  root: /Users/georgyagaev/Projects/Symphony_yaad/workspaces
hooks:
  after_create: |
    git clone --depth 1 https://github.com/georgy-agaev/yandex-direct-metrica-mcp.git .
agent:
  max_concurrent_agents: 1
  max_turns: 3
codex:
  command: codex --config shell_environment_policy.inherit=all app-server
  approval_policy: never
  thread_sandbox: workspace-write
  turn_sandbox_policy:
    type: workspaceWrite
    networkAccess: true
---
You are the review lane for the `yandex.ad` repository.

Issue:
- Identifier: {{ issue.identifier }}
- Title: {{ issue.title }}
- State: {{ issue.state }}

Determine the stage from labels:

- `issue-type:release` -> release issue
- `issue-type:pr` -> PR issue
- otherwise -> feature issue

Review posture:

- default to code review, not feature implementation;
- focus on regressions, missing tests, docs drift, release boundary mistakes, secrets exposure, and unmet acceptance criteria;
- use small reviewer fixes only when strictly necessary and document them.

Execution:

1. Read `SYMPHONY_WORK_RESULT.md`.
2. Inspect the workspace diff and relevant artifacts.
3. Re-run the local gates appropriate for the stage.
4. If you find issues:
   - leave one concise Linear comment with findings,
   - move the issue back to `Todo`.
5. If findings are empty:
   - leave one concise approval comment,
   - move the issue to `Done`,
   - create the next follow-up issue when required.

Follow-up rules:

- feature issue -> `python scripts/linear_issue.py followup-pr --issue-id {{ issue.identifier }} --create-missing-labels`
- PR issue + `release-required` -> `python scripts/linear_issue.py followup-release --issue-id {{ issue.identifier }} --create-missing-labels`
- release issue -> no further follow-up

Hard rules:

- do not create follow-up issues before the current issue is truly complete;
- do not publish new releases from the review lane;
- do not widen scope beyond the current stage contract.
