# Claude Code setup — MCP Yandex Ad (2026-01-27)

Goal: connect `yandex-direct-metrica-mcp` (legacy alias: `mcp-yandex-ad`) to Claude Code as an MCP server and quickly validate the UX (tools + dashboard).

## Option A (recommended): use `.mcp.json` in your Claude Code project folder

1) Add a new server entry to your project `.mcp.json`:

```json
{
  "mcpServers": {
    "yandexad": {
      "command": "/path/to/venv/bin/yandex-direct-metrica-mcp",
      "args": ["--env-file", "/path/to/your/.env"]
    }
  }
}
```

Notes:
- Default transport is `stdio`, which is what Claude Code expects for local MCP servers.
- Prefer pointing to an env file; do not inline secrets into JSON.

2) Enable the server in your Claude Code settings file:
- add `"yandexad"` to `enabledMcpjsonServers`.

3) Allow tool calls in your Claude Code settings file:
- add the minimal set first (and extend as needed):
  - `mcp__yandexad__direct.list_campaigns`
  - `mcp__yandexad__direct.report`
  - `mcp__yandexad__metrica.report`
  - `mcp__yandexad__join.hf.direct_vs_metrica_by_utm`
  - `mcp__yandexad__join.hf.direct_vs_metrica_by_yclid`
  - `mcp__yandexad__dashboard.generate_option1`

If Claude Code shows a “tool not allowed” name, copy that exact name into the allow-list.

4) Restart Claude Code.

## Option B: `claude mcp add ...`

If you prefer CLI-managed config:
```bash
claude mcp add yandex-direct-metrica-mcp -s user -- /path/to/venv/bin/yandex-direct-metrica-mcp --env-file /path/to/your/.env
claude mcp list
```
Then update your Claude Code settings allow-list similarly (path depends on your setup).

## Quick prompts to test UX

### 1) Discover tools
- “List available tools in yandexad and show me the main ones for reporting + joins.”

### 2) UTM join (works well)
- “Run a Direct vs Metrica join by UTM for the last 30 days for campaign `<campaign_id>` and counter `<counter_id>`. Use direct_client_login=`<direct_client_login>` and utm_campaign=`<utm_campaign>`.”

### 3) yclid join (best effort)
- “Try a yclid join for yesterday for counter `<counter_id>` (direct_client_login=`<direct_client_login>`). Explain join_mode and why unmatched rows can be high.”

## Dashboard generator (Option 1)

Generate HTML+JSON locally:
- Option A (local script): this is **not** an MCP tool; it calls MCP over SSE (`http://localhost:8000/sse` by default), so start the server with SSE transport first (e.g. via `docker-compose.yml`).
```bash
/path/to/venv/bin/python /path/to/project/scripts/generate_dashboard_option1.py \
  --account-id <account_id> \
  --date-from 2026-01-01 \
  --date-to 2026-01-31 \
  --output-dir /path/to/output/dashboard
```

Then open the HTML:
```bash
open /path/to/output/dashboard/yandexad_dashboard__account__2026-01-01_2026-01-31.html
```

Option B (MCP tool): call `dashboard.generate_option1` (no SSE needed; uses the same server runtime).
- Tip: when using `output_dir`, set `return_data=false` to avoid token-limit issues in Claude Code while still getting `files.html_path` / `files.json_path`.
