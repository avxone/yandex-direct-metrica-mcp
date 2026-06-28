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

1. owner repo
2. out-of-scope repos
3. feature vs bug vs investigation vs release
4. `Release Required: yes/no`
5. client handoff required: yes/no
6. compatibility task vs migration task
7. acceptance criteria
8. validation that the owner repo can execute directly

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
3. Ensure the issue does not require client-repo edits unless that repo is explicitly in scope.
4. Preview the Linear payload with `python scripts/linear_issue.py preview`.
5. Create or update the Linear issue only when the user asks for the actual Linear change.

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
