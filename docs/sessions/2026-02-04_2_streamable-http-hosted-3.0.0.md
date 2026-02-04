# 2026-02-04 — Plan: Streamable HTTP transport + hosted/SaaS image (target 3.0.0)

## Completed

- Decided to ship Streamable HTTP transport in **3.0.0** (not in 2.0.0).
- Decided to ship a separate **hosted/SaaS Docker image** for our own deployments (not for public distribution).

## To Do

- Define transport requirements:
  - Which MCP transport(s) to support (Streamable HTTP vs SSE vs both).
  - TLS and auth strategy (reverse proxy vs built-in; per-tenant authn/authz).
  - Rate limits, quotas, and per-tenant isolation (tokens/state).
- Define packaging strategy:
  - Separate image name (internal) and build args/markers.
  - Ensure hosted image does not break public/pro images and keeps public safe-by-default.
- Add docs/runbooks (internal):
  - Deployment (compose/k8s), logging, monitoring, incident playbook.
- Add security checklist:
  - Secret handling, token storage policy, audit logging, data retention.

