# RFC-0002 — role / bundle manifests

## Purpose

Define the minimal backend-side contract for role-aware bundle manifests without introducing dynamic discovery behavior.

## Current pain

`Marketing2025` already uses role bundles, but the backend has no explicit contract surface for:

- recommended tool subsets
- preferred entrypoints
- exclusions for a given role or workflow family

## Proposed contract

Each bundle manifest should include:

- `bundle_id`
- `title`
- `intended_for`
- `recommended_tools`
- `preferred_entrypoints`
- `excluded_tools`
- `notes`

The contract is initially documentation-first.

Runtime exposure is deferred until `Marketing2025` submits real inventory input.

## Migration impact

Short term:

- both repos can discuss role-aware scoping using one explicit schema

Medium term:

- the same schema may back a future static catalog/bundle MCP tool

## Acceptance criteria

- one documented schema exists for role/bundle manifests
- no prompt-time or task-time dynamic tool surfacing is introduced
