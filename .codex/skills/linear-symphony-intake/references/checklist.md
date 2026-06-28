# Intake Checklist

Use this checklist before creating or updating a Symphony-managed issue.

## Mandatory fields

- `Issue Class: bug / feature / investigation / release`
- `Risk: low / medium / high`
- `Owned by: <repo>`
- `Out of scope without a separate issue: <repos/systems>`
- `Goal`
- `Scope`
- `Non-goals`
- `Acceptance Criteria`
- `Feature Validation`
- `PR Validation`
- `Release Validation`
- `Handoff` or `Notes`

## Mandatory decisions

- `Release Required: yes/no`
- client handoff required: yes/no
- `Compatibility task` or `Migration task`

## Label mapping

Normal feature issue:

- `symphony`
- `issue-type:feature`
- domain labels

Only add `release-required` when published images are required before the client can use the result.

## Scope guard

If the user describes both:

- a producer capability in `yandex.ad`
- a consumer workflow change in another repo

split them unless the user explicitly wants both repos in scope.

## Validation guard

Validation must be defined per stage:

- `Feature Validation`: what the feature-stage implementation and review must prove
- `PR Validation`: what the PR-stage implementation and review must prove
- `Release Validation`: what the release-stage implementation and review must prove

Only the current stage should execute its validation section.

Validation must remain executable from the owner repo:

- tests
- contract checks
- live bounded API validation
- docs / handoff review

Cross-repo adoption tests belong in a separate consumer issue unless explicitly in scope.
