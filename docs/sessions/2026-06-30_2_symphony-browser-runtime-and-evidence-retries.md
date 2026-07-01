# Session: Symphony browser runtime and evidence retries

Date: 2026-06-30

## Completed

- Updated the `yandex.ad` Symphony implementation/review workflows to:
  - prefer the app-bundled Codex runtime (`/Applications/Codex.app/Contents/Resources/codex`);
  - inspect existing Linear comments and repo-local evidence artifacts before re-blocking on browser/manual validation;
  - allow previously supplied operator/browser evidence to satisfy a retry instead of forcing a fresh blocker loop.
- Updated capability/intake/issue-writing docs so browser validation now prefers:
  - `chrome-devtools` for human-visible Chrome inspection,
  - `playwright` for deterministic agent-owned browser runs,
  - `operator-browser` only when a human evidence step is intentionally accepted.
- Updated the local `GEO-9` draft so browser validation prefers `chrome-devtools` and explicitly accepts existing Linear/repo evidence when the backend is unavailable.

## To Do

- Sync the updated workflow files into `<symphony-root>/workflows/`.
- Update the live Linear issue body for `GEO-9`.
- Restart the Symphony implementation/review lanes so the new Codex runtime command and evidence-retry rules take effect.
- Re-run `GEO-9` and confirm it can progress past the former browser-evidence blocker.
