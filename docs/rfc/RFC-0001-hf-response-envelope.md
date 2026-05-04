# RFC-0001 — HF response envelope

## Purpose

Define one small, stable response envelope for the human-friendly read layer in `yandex.ad`.

The contract should be:

- easy for LLMs to inspect
- easy for deterministic Python code to parse
- stable enough for reuse across multiple HF tools

## Current pain

`Marketing2025` currently maintains many tool-specific parsers for MCP outputs.

This creates:

- duplicated parsing logic
- defensive checks against ambiguous shapes
- extra glue code in gates, synthesis, and render stages

The primary goal of this RFC is stronger than “similar outer shape”.

The goal is:

- one shared loader on the `Marketing2025` side
- no regex/keyword parsing of error messages
- no per-tool parsers for `choices[]` or `warnings[]`
- no separate dry-run parser when a tool already has a normal result parser

## Proposed contract

The canonical HF envelope is:

```json
{
  "tool": "string",
  "status": "ok | error | dry_run | needs_disambiguation",
  "message": "optional human-readable string",
  "meta": {
    "envelope_version": "1.0",
    "tool_version": "string",
    "request_id": "string",
    "timestamp": "ISO8601"
  },
  "preview": {},
  "result": {},
  "error": {
    "code": "string",
    "type": "validation | not_found | rate_limited | upstream | auth | internal",
    "retryable": true,
    "details": {}
  },
  "choices": [
    {
      "id": "string",
      "label": "string",
      "type": "string",
      "context": {}
    }
  ],
  "warnings": [
    {
      "code": "string",
      "message": "string",
      "field": "string",
      "details": {}
    }
  ]
}
```

### Field rules

- `tool`: required
- `status`: required
- `meta`: required
- `meta.envelope_version`: required, current value is `1.0`
- `meta.tool_version`: optional, recommended when tool-internal output contracts may evolve
- `meta.request_id`: required, for correlation across server logs, pipeline logs, and reviews
- `meta.timestamp`: required, ISO 8601 UTC string
- `message`: optional, human-readable, never the only carrier of machine-critical state
- `preview`: optional, used for dry-run or pre-apply style outputs
- `result`: optional, primary structured payload for machine use
- `error`: required when `status == "error"`, omitted otherwise
- `error.code`: required, stable machine-readable identifier
- `error.type`: required closed enum for coarse error handling
- `error.retryable`: required boolean for retry vs hard-fail decisions
- `error.details`: optional structured payload, never prose-only
- `choices`: required and non-empty when `status == "needs_disambiguation"`
- `choices[].id`: machine-readable identifier passed back by the caller
- `choices[].label`: human-readable label, not a substitute for `id`
- `choices[].type`: machine-readable choice category
- `choices[].context`: optional structured helper context
- `warnings`: optional non-fatal machine-readable warnings
- `warnings[].code`: required stable machine-readable identifier
- `warnings[].message`: required short human-readable summary
- `warnings[].field`: optional dotted path into `result` or `preview`
- `warnings[].details`: optional structured helper context

### Required-field matrix by status

| Status | Required | Optional |
|---|---|---|
| `ok` | `tool`, `status`, `meta` | `message`, `result`, `warnings` |
| `error` | `tool`, `status`, `meta`, `error` | `message`, `warnings` |
| `dry_run` | `tool`, `status`, `meta`, `preview` | `message`, `warnings` |
| `needs_disambiguation` | `tool`, `status`, `meta`, `choices` | `message`, `warnings` |

### Preview/result relationship

`preview` SHOULD use the same schema family as `result` for the same tool whenever that is practical.

The intention is:

- one parser can often read both `result` and `preview`
- dry-run does not automatically force a second tool-specific parser

If a tool genuinely needs a different preview shape, that divergence must be made explicit in the tool-level `outputSchema` and justified there.

### Shape rules

- top-level keys must remain shallow and stable
- structured machine data belongs in `result`
- structured machine error state belongs in `error`
- `message` must not be the only place where critical state is expressed
- handlers should not invent additional top-level keys casually
- consumers must be able to parse `error`, `choices[]`, and `warnings[]` without tool-specific heuristics

## Migration impact

Short term:

- existing HF handlers should be normalized to this envelope
- `Marketing2025` can begin implementing one shared envelope loader

Medium term:

- new fixed read workflows should reuse the same outer contract
- envelope migrations become detectable through `meta.envelope_version`

## Explicit deferrals

The following topics are useful, but do not block locking this RFC:

- envelope-level pagination metadata
- `partial` status for multi-account / mixed-success calls
- cost or quota hints in `meta`

They should land in follow-up RFCs if needed rather than delaying the current contract lock.

## Acceptance criteria

- prioritized HF read tools use the canonical top-level envelope
- error handling does not require parsing `message` for machine-critical decisions
- `choices[]` and `warnings[]` have stable element shapes
- dry-run outputs do not force a second parser by default
- `Marketing2025` can replace multiple ad hoc parsers with one shared loader
- contract changes become reviewable via tests and future RFCs
