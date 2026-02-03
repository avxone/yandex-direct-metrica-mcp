# Compatibility / SemVer policy

This project follows SemVer with an explicit **tool contract**.

## Public contract (1.x)

The public contract is the `tools/list` surface for the public edition:
- tool `name`
- tool `description`
- tool `inputSchema` (including defaults)

Canonical snapshot:
- `tests/snapshots/public_tools_v1.json`

## What is a breaking change (public)

Breaking (requires 2.0.0):
- Removing a public tool.
- Renaming a public tool.
- Changing `inputSchema` (types, required fields, enums, defaults).
- Changing `description` (since it is part of the snapshot contract).

Non-breaking (allowed in 1.x):
- Bug fixes that do not change the tool contract.
- Adding **new tools** (minor version).
- Adding **new optional output fields** (outputs are not contract-frozen in v1.0.0).

## Deprecation approach

Because `description` is contract-frozen, deprecations should be handled by:
- Introducing a new tool name (e.g., `..._v2`) and keeping the old one through the rest of 1.x.
- Removing the old tool only in 2.0.0.

## Pro contract

The PRO tool surface is not contract-frozen by default.
If we decide to provide SemVer guarantees for PRO tools, we should add a separate snapshot and policy.

