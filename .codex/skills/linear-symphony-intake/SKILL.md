---
name: linear-symphony-intake
description: Use when the user wants to create, refine, split, or update Linear issues for yandex.ad so Symphony can execute them safely. Covers issue shaping, ownership boundaries, release-required routing, client handoff vs client-repo changes, and label selection for the feature -> PR -> release pipeline.
---

# Linear Symphony Intake

Use this skill for new `yandex.ad` work that should enter the `Linear + Symphony` pipeline.

Read these files before shaping the issue:

1. `docs/automation/issue-writing-rules.md`
2. `docs/automation/linear-intake.md`
3. `references/checklist.md`

Choose the smallest fitting template:

- feature: `docs/automation/templates/linear-feature.md`
- bug: `docs/automation/templates/linear-bug.md`
- investigation: `docs/automation/templates/linear-investigation.md`
- release: `docs/automation/templates/linear-release.md`
- client workflow / downstream dependency: `docs/automation/templates/linear-marketing2025-workflow.md`

## Required intake decisions

Before creating or updating an issue, capture or infer:

1. issue class: `bug` / `feature` / `investigation` / `release`
2. risk: `low` / `medium` / `high`
3. owner repo
4. out-of-scope repos
5. `Release Required: yes/no`
6. client handoff required: yes/no
7. compatibility task vs migration task
8. required capabilities:
   - browser mode
   - live-api yes/no
   - manual-check yes/no
   - operator step required yes/no
9. external inputs / secrets:
   - required env vars
   - source of truth
   - expected parent-process availability
10. blocked input policy
11. acceptance criteria
12. `Feature Validation`
13. `PR Validation`
14. `Release Validation`

If the task is ambiguous, default to the smaller producer-side issue and create a downstream follow-up issue later.

## Label rules

For a new Symphony feature issue, default to:

- `symphony`
- `issue-type:feature`

Add:

- domain labels such as `search-api`, `wordstat`, `dashboard`
- `release-required` only when the client cannot use the work before a published image exists

Do not create `issue-type:pr` or `issue-type:release` manually during normal intake. Those are generated as follow-up issues by the pipeline.

## Workflow

1. Draft or refine the Markdown issue body.
2. Check that repo ownership and handoff boundaries are explicit.
3. Ensure capability requirements and secret dependencies are explicit before the issue can move to `Todo`.
4. Ensure validation is defined per stage, not as one mixed checklist.
5. Ensure the issue does not require client-repo edits unless that repo is explicitly in scope.
6. Preview the Linear payload with `python scripts/linear_issue.py preview`.
7. Create or update the Linear issue only when the user asks for the actual Linear change.

## Commands

Preview:

```bash
python scripts/linear_issue.py preview \
  --config /Users/georgyagaev/Projects/Symphony_yaad/linear.yandexad.json \
  --from <draft.md> \
  --title "<issue title>" \
  --labels symphony,issue-type:feature,<domain-label>
```

Create:

```bash
python scripts/linear_issue.py create \
  --config /Users/georgyagaev/Projects/Symphony_yaad/linear.yandexad.json \
  --from <draft.md> \
  --title "<issue title>" \
  --labels symphony,issue-type:feature,<domain-label>
```

Update:

```bash
python scripts/linear_issue.py update \
  --config /Users/georgyagaev/Projects/Symphony_yaad/linear.yandexad.json \
  --issue-id GEO-7 \
  --from <draft.md> \
  --title "<issue title>"
```

## Output standard

The finished issue should be ready for a human to move from `Backlog` to `Todo` without extra copy-paste or manual rewriting.
