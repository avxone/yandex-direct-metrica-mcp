# Cross-Repo RFCs

This folder is the canonical location for cross-repo contract RFCs shared between:

- `yandex.ad`
- `Marketing2025`

## Naming

Use:

- `RFC-NNNN-short-title.md`

Examples:

- `RFC-0001-hf-response-envelope.md`
- `RFC-0002-role-bundle-manifests.md`

## When an RFC is required

Write an RFC before implementation when a change affects:

- MCP output contracts
- cross-repo artifact contracts
- tool semantics consumed by `Marketing2025`
- role/bundle manifest format
- quality-gate semantics shared across repos

## Minimum RFC structure

Each RFC should include:

- purpose
- current pain
- proposed contract
- migration impact
- acceptance criteria

## Review rule

At minimum, each cross-repo RFC should be reviewed by:

- one `yandex.ad` owner
- one `Marketing2025` owner
