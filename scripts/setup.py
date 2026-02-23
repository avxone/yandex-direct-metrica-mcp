#!/usr/bin/env python3
"""Interactive setup wizard for yandex-direct-metrica-mcp.

Pure stdlib Python 3.10+ — no third-party dependencies required.
Run:  python3 scripts/setup.py
"""

from __future__ import annotations

import json
import os
import platform
import stat
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOCKER_IMAGE = "ghcr.io/georgy-agaev/yandex-direct-metrica-mcp:latest"
SERVER_NAME = "yandex-direct-metrica-mcp"

CLIENTS = [
    ("claude-code", "Claude Code"),
    ("claude-desktop", "Claude Desktop"),
    ("cursor", "Cursor"),
    ("codex", "Codex CLI"),
    ("opencode", "OpenCode"),
    ("gemini", "Gemini CLI"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bold(text: str) -> str:
    if sys.stdout.isatty():
        return f"\033[1m{text}\033[0m"
    return text


def _dim(text: str) -> str:
    if sys.stdout.isatty():
        return f"\033[2m{text}\033[0m"
    return text


def _green(text: str) -> str:
    if sys.stdout.isatty():
        return f"\033[32m{text}\033[0m"
    return text


def _yellow(text: str) -> str:
    if sys.stdout.isatty():
        return f"\033[33m{text}\033[0m"
    return text


def _red(text: str) -> str:
    if sys.stdout.isatty():
        return f"\033[31m{text}\033[0m"
    return text


def ask(prompt: str, *, default: str | None = None, required: bool = True) -> str:
    """Prompt the user for a value. Returns stripped string."""
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{prompt}{suffix}: ").strip()
        if not value and default is not None:
            return default
        if value or not required:
            return value
        print(_red("  This field is required."))


def ask_choice(prompt: str, options: list[tuple[str, str]]) -> str:
    """Prompt the user to pick from numbered options. Returns the key."""
    print(f"\n{_bold(prompt)}")
    for i, (key, label) in enumerate(options, 1):
        print(f"  {i}) {label}")
    while True:
        raw = input("Choice: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            chosen = options[int(raw) - 1]
            print(f"  -> {chosen[1]}")
            return chosen[0]
        print(_red(f"  Enter a number 1–{len(options)}."))


def ask_yn(prompt: str, *, default: bool = True) -> bool:
    """Yes/no prompt."""
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{prompt} [{hint}]: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print(_red("  Enter y or n."))


def banner() -> None:
    print()
    print(_bold("=" * 56))
    print(_bold("  yandex-direct-metrica-mcp — Setup Wizard"))
    print(_bold("=" * 56))
    print()
    print("This wizard will:")
    print("  1. Collect your Yandex OAuth credentials")
    print("  2. Configure Direct / Metrica / Wordstat / Audience")
    print("  3. Write .env (and optionally accounts.json)")
    print("  4. Register the MCP server for your client")
    print()


# ---------------------------------------------------------------------------
# Step functions
# ---------------------------------------------------------------------------

def ask_client() -> str:
    return ask_choice("Which MCP client will you use?", CLIENTS)


def ask_state_dir() -> Path:
    print(f"\n{_bold('State directory')}")
    print("This is where .env and accounts.json will live.")
    print(_dim("Example: ~/mcp-state/yandex-direct-metrica-mcp"))
    raw = ask("Path", default=str(Path.home() / "mcp-state" / SERVER_NAME))
    state_dir = Path(raw).expanduser().resolve()
    if state_dir.exists() and not state_dir.is_dir():
        print(_red(f"  {state_dir} exists but is not a directory. Aborting."))
        sys.exit(1)
    state_dir.mkdir(parents=True, exist_ok=True)
    print(_green(f"  Using {state_dir}"))
    return state_dir


def ask_install() -> str:
    return ask_choice(
        "Install method?",
        [("docker", "Docker (recommended)"), ("local", "Local Python (pip)")],
    )


def ask_oauth() -> dict:
    print(f"\n{_bold('OAuth credentials')}")
    print("You need a Yandex OAuth app. See: https://oauth.yandex.ru/")
    client_id = ask("YANDEX_CLIENT_ID")
    client_secret = ask("YANDEX_CLIENT_SECRET")

    print()
    token_mode = ask_choice(
        "Token type?",
        [
            ("refresh", "Refresh token (recommended — auto-renews)"),
            ("access", "Access token (static, expires)"),
        ],
    )
    if token_mode == "refresh":
        refresh_token = ask("YANDEX_REFRESH_TOKEN")
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }
    access_token = ask("YANDEX_ACCESS_TOKEN")
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": access_token,
    }


def ask_direct() -> dict:
    print(f"\n{_bold('Yandex Direct')}")
    client_login = ask("YANDEX_DIRECT_CLIENT_LOGIN (agency client login)", required=False)
    client_logins = ask(
        "YANDEX_DIRECT_CLIENT_LOGINS (comma-separated, optional)",
        required=False,
    )
    api_version = ask_choice(
        "Direct API version?",
        [("v501", "v501 (latest)"), ("v5", "v5 (legacy)")],
    )
    sandbox = ask_yn("Use sandbox?", default=False)
    return {
        "client_login": client_login,
        "client_logins": client_logins,
        "api_version": api_version,
        "sandbox": sandbox,
    }


def ask_metrica() -> dict:
    print(f"\n{_bold('Yandex Metrica')}")
    counter_ids = ask("YANDEX_METRICA_COUNTER_IDS (comma-separated)", required=False)
    return {"counter_ids": counter_ids}


def ask_wordstat() -> dict:
    print(f"\n{_bold('Wordstat')}")
    enabled = ask_yn("Enable Wordstat tools?", default=True)
    result: dict = {"enabled": enabled}
    if enabled and ask_yn("Use separate OAuth for Wordstat?", default=False):
        result["client_id"] = ask("YANDEX_WORDSTAT_CLIENT_ID")
        result["client_secret"] = ask("YANDEX_WORDSTAT_CLIENT_SECRET")
        token_mode = ask_choice(
            "Wordstat token type?",
            [("refresh", "Refresh token"), ("access", "Access token")],
        )
        if token_mode == "refresh":
            result["refresh_token"] = ask("YANDEX_WORDSTAT_REFRESH_TOKEN")
        else:
            result["access_token"] = ask("YANDEX_WORDSTAT_ACCESS_TOKEN")
    return result


def ask_audience() -> dict:
    print(f"\n{_bold('Audience')}")
    enabled = ask_yn("Enable Audience tools?", default=True)
    result: dict = {"enabled": enabled}
    if enabled and ask_yn("Use separate OAuth for Audience?", default=False):
        result["client_id"] = ask("YANDEX_AUDIENCE_CLIENT_ID")
        result["client_secret"] = ask("YANDEX_AUDIENCE_CLIENT_SECRET")
        token_mode = ask_choice(
            "Audience token type?",
            [("refresh", "Refresh token"), ("access", "Access token")],
        )
        if token_mode == "refresh":
            result["refresh_token"] = ask("YANDEX_AUDIENCE_REFRESH_TOKEN")
        else:
            result["access_token"] = ask("YANDEX_AUDIENCE_ACCESS_TOKEN")
    return result


def ask_accounts() -> list | None:
    print(f"\n{_bold('Multi-account setup')}")
    if not ask_yn("Set up accounts.json (multi-project profiles)?", default=False):
        return None

    accounts: list[dict] = []
    while True:
        print(f"\n  {_bold(f'Account #{len(accounts) + 1}')}")
        acc_id = ask("  Account id (unique slug)")
        acc_name = ask("  Display name")
        acc_login = ask("  Direct client login")
        acc_counters = ask("  Metrica counter IDs (comma-separated)", required=False)
        accounts.append({
            "id": acc_id,
            "name": acc_name,
            "direct_client_login": acc_login,
            "metrica_counter_ids": [
                c.strip() for c in acc_counters.split(",") if c.strip()
            ] if acc_counters else [],
        })
        if not ask_yn("  Add another account?", default=False):
            break
    return accounts


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _env_line(key: str, value: str) -> str:
    return f"{key}={value}"


def write_env(
    state_dir: Path,
    oauth: dict,
    direct: dict,
    metrica: dict,
    wordstat: dict,
    audience: dict,
) -> Path:
    env_path = state_dir / ".env"
    if env_path.exists():
        if not ask_yn(
            _yellow(f"\n{env_path} already exists. Overwrite?"), default=False
        ):
            print("  Keeping existing .env")
            return env_path

    lines: list[str] = [
        "# Generated by setup.py",
        "# Yandex OAuth",
        _env_line("YANDEX_CLIENT_ID", oauth["client_id"]),
        _env_line("YANDEX_CLIENT_SECRET", oauth["client_secret"]),
    ]
    if "refresh_token" in oauth:
        lines.append(_env_line("YANDEX_REFRESH_TOKEN", oauth["refresh_token"]))
    if "access_token" in oauth:
        lines.append(_env_line("YANDEX_ACCESS_TOKEN", oauth["access_token"]))

    # Wordstat OAuth
    lines.append("")
    lines.append("# Wordstat OAuth")
    if "client_id" in wordstat:
        lines.append(_env_line("YANDEX_WORDSTAT_CLIENT_ID", wordstat["client_id"]))
        lines.append(_env_line("YANDEX_WORDSTAT_CLIENT_SECRET", wordstat["client_secret"]))
        if "refresh_token" in wordstat:
            lines.append(_env_line("YANDEX_WORDSTAT_REFRESH_TOKEN", wordstat["refresh_token"]))
        if "access_token" in wordstat:
            lines.append(_env_line("YANDEX_WORDSTAT_ACCESS_TOKEN", wordstat["access_token"]))

    # Audience OAuth
    lines.append("")
    lines.append("# Audience OAuth")
    if "client_id" in audience:
        lines.append(_env_line("YANDEX_AUDIENCE_CLIENT_ID", audience["client_id"]))
        lines.append(_env_line("YANDEX_AUDIENCE_CLIENT_SECRET", audience["client_secret"]))
        if "refresh_token" in audience:
            lines.append(_env_line("YANDEX_AUDIENCE_REFRESH_TOKEN", audience["refresh_token"]))
        if "access_token" in audience:
            lines.append(_env_line("YANDEX_AUDIENCE_ACCESS_TOKEN", audience["access_token"]))

    # Direct
    lines.append("")
    lines.append("# Direct API")
    lines.append(_env_line("YANDEX_DIRECT_CLIENT_LOGIN", direct["client_login"]))
    if direct["client_logins"]:
        lines.append(_env_line("YANDEX_DIRECT_CLIENT_LOGINS", direct["client_logins"]))
    lines.append(_env_line("YANDEX_DIRECT_SANDBOX", str(direct["sandbox"]).lower()))
    lines.append(_env_line("YANDEX_DIRECT_API_VERSION", direct["api_version"]))

    # Write guardrails — safe defaults
    lines.append("")
    lines.append("# Write guardrails")
    lines.append(_env_line("MCP_WRITE_ENABLED", "false"))
    lines.append(_env_line("MCP_WRITE_SANDBOX_ONLY", "true"))

    # Accounts
    lines.append("")
    lines.append("# Accounts registry")
    lines.append(_env_line("MCP_ACCOUNTS_FILE", "/data/accounts.json"))

    # HF layer
    lines.append("")
    lines.append("# Human-friendly tools")
    lines.append(_env_line("HF_ENABLED", "true"))
    lines.append(_env_line("HF_WRITE_ENABLED", "false"))

    # Metrica
    lines.append("")
    lines.append("# Metrica")
    lines.append(_env_line("YANDEX_METRICA_COUNTER_IDS", metrica["counter_ids"]))

    # Wordstat / Audience toggles
    lines.append("")
    lines.append("# Wordstat")
    lines.append(_env_line("MCP_WORDSTAT_ENABLED", str(wordstat["enabled"]).lower()))

    lines.append("")
    lines.append("# Audience")
    lines.append(_env_line("MCP_AUDIENCE_ENABLED", str(audience["enabled"]).lower()))

    # Cache / rate limits — sensible defaults
    lines.append("")
    lines.append("# Runtime")
    lines.append(_env_line("MCP_CONTENT_MODE", "json"))
    lines.append(_env_line("MCP_CACHE_ENABLED", "true"))
    lines.append(_env_line("MCP_CACHE_TTL_SECONDS", "300"))
    lines.append("")

    env_path.write_text("\n".join(lines), encoding="utf-8")
    # chmod 600 — owner-only read/write
    env_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    print(_green(f"  Wrote {env_path}  (chmod 600)"))
    return env_path


def write_accounts(state_dir: Path, accounts: list[dict]) -> Path:
    accounts_path = state_dir / "accounts.json"
    if accounts_path.exists():
        if not ask_yn(
            _yellow(f"\n{accounts_path} already exists. Overwrite?"), default=False
        ):
            print("  Keeping existing accounts.json")
            return accounts_path

    data = {"accounts": accounts}
    accounts_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(_green(f"  Wrote {accounts_path}"))
    return accounts_path


# ---------------------------------------------------------------------------
# Client registration
# ---------------------------------------------------------------------------

def _docker_args(state_dir: Path) -> list[str]:
    return [
        "docker", "run", "--rm", "-i",
        "--env-file", str(state_dir / ".env"),
        "-e", "MCP_ACCOUNTS_FILE=/data/accounts.json",
        "-v", f"{state_dir}:/data",
        DOCKER_IMAGE,
    ]


def _local_args() -> list[str]:
    return ["mcp-yandex-ad"]


def _get_command_and_args(install: str, state_dir: Path) -> tuple[str, list[str]]:
    if install == "docker":
        args = _docker_args(state_dir)
        return args[0], args[1:]
    args = _local_args()
    return args[0], args[1:]


def _claude_desktop_config_path() -> Path:
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"


def _print_json_snippet(label: str, config_path: str, snippet: dict) -> None:
    print(f"\n{_bold(label)}")
    print(f"Add the following to {_dim(config_path)}:\n")
    print(json.dumps(snippet, indent=2))
    print()


def register_mcp(client: str, state_dir: Path, install: str) -> None:
    print(f"\n{_bold('Registering MCP server')}")
    command, args = _get_command_and_args(install, state_dir)

    if client == "claude-code":
        _register_claude_code(command, args, install, state_dir)
    elif client == "claude-desktop":
        _register_claude_desktop(command, args)
    elif client == "cursor":
        _register_cursor(command, args)
    elif client == "codex":
        _register_codex(command, args)
    elif client == "opencode":
        _register_opencode(command, args)
    elif client == "gemini":
        _register_gemini(command, args)


def _register_claude_code(
    command: str, args: list[str], install: str, state_dir: Path
) -> None:
    cmd = ["claude", "mcp", "add", SERVER_NAME, "--", command, *args]
    readable = (
        f"claude mcp add {SERVER_NAME} -- \\\n"
        f"  {command} \\\n"
        + " \\\n".join(f"    {a}" for a in args)
    )
    print(f"Running:\n{_dim(readable)}\n")
    if not ask_yn("Execute now?", default=True):
        print("Skipped. You can run it manually:")
        print(f"  {readable}")
        return
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(_green("  Registered successfully."))
        else:
            stderr = result.stderr.strip()
            print(_red(f"  Command failed (exit {result.returncode})."))
            if stderr:
                print(f"  {stderr}")
            print(f"\nYou can run it manually:\n  {readable}")
    except FileNotFoundError:
        print(_red("  'claude' CLI not found in PATH."))
        print(f"Run manually:\n  {readable}")
    except subprocess.TimeoutExpired:
        print(_red("  Command timed out."))


def _register_claude_desktop(command: str, args: list[str]) -> None:
    config_path = _claude_desktop_config_path()
    snippet = {
        "mcpServers": {
            SERVER_NAME: {
                "command": command,
                "args": args,
            }
        }
    }
    _print_json_snippet("Claude Desktop", str(config_path), snippet)
    print(_dim("Merge the mcpServers entry into your existing config file."))


def _register_cursor(command: str, args: list[str]) -> None:
    snippet = {
        "mcpServers": {
            SERVER_NAME: {
                "command": command,
                "args": args,
            }
        }
    }
    _print_json_snippet("Cursor", ".cursor/mcp.json (in project root)", snippet)


def _register_codex(command: str, args: list[str]) -> None:
    toml_lines = [
        "[[mcp]]",
        f'name = "{SERVER_NAME}"',
        f'command = "{command}"',
        "args = " + json.dumps(args),
    ]
    print(f"\n{_bold('Codex CLI')}")
    print(f"Add the following to {_dim('~/.codex/config.toml')}:\n")
    print("\n".join(toml_lines))
    print()


def _register_opencode(command: str, args: list[str]) -> None:
    snippet = {
        "mcp": {
            "servers": {
                SERVER_NAME: {
                    "command": command,
                    "args": args,
                    "enabled": True,
                }
            }
        }
    }
    _print_json_snippet("OpenCode", "opencode.json (in project root)", snippet)


def _register_gemini(command: str, args: list[str]) -> None:
    snippet = {
        "mcpServers": {
            SERVER_NAME: {
                "command": command,
                "args": args,
            }
        }
    }
    _print_json_snippet("Gemini CLI", "~/.gemini/settings.json", snippet)
    print(_dim("Merge the mcpServers entry into your existing settings file."))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(state_dir: Path) -> bool:
    print(f"\n{_bold('Validating configuration')}")
    env_path = state_dir / ".env"
    ok = True

    if not env_path.exists():
        print(_red(f"  Missing {env_path}"))
        return False

    content = env_path.read_text(encoding="utf-8")
    required_keys = ["YANDEX_CLIENT_ID", "YANDEX_CLIENT_SECRET"]
    token_keys = ["YANDEX_REFRESH_TOKEN", "YANDEX_ACCESS_TOKEN"]

    for key in required_keys:
        if f"{key}=" not in content or content.split(f"{key}=")[1].split("\n")[0].strip() == "":
            print(_red(f"  Missing value for {key}"))
            ok = False

    has_token = any(
        f"{k}=" in content and content.split(f"{k}=")[1].split("\n")[0].strip()
        for k in token_keys
    )
    if not has_token:
        print(_red("  Missing YANDEX_REFRESH_TOKEN or YANDEX_ACCESS_TOKEN"))
        ok = False

    accounts_path = state_dir / "accounts.json"
    if accounts_path.exists():
        try:
            data = json.loads(accounts_path.read_text(encoding="utf-8"))
            if "accounts" not in data or not isinstance(data["accounts"], list):
                print(_red("  accounts.json: missing 'accounts' array"))
                ok = False
            else:
                for i, acc in enumerate(data["accounts"]):
                    for field in ("id", "name", "direct_client_login"):
                        if field not in acc:
                            print(_red(f"  accounts.json: account #{i + 1} missing '{field}'"))
                            ok = False
                print(_green(f"  accounts.json: {len(data['accounts'])} account(s) OK"))
        except json.JSONDecodeError as exc:
            print(_red(f"  accounts.json: invalid JSON — {exc}"))
            ok = False

    if ok:
        print(_green("  .env looks valid"))
    return ok


# ---------------------------------------------------------------------------
# Next steps
# ---------------------------------------------------------------------------

def print_next_steps(client: str) -> None:
    print(f"\n{_bold('Next steps')}")
    print()
    if client == "claude-code":
        print("  1. Verify:  claude mcp list")
        print('  2. Test:    ask Claude "List accounts from the server."')
    elif client == "claude-desktop":
        config_path = _claude_desktop_config_path()
        print(f"  1. Merge the snippet into {config_path}")
        print("  2. Restart Claude Desktop")
        print('  3. Test:  ask Claude "List accounts from the server."')
    elif client == "cursor":
        print("  1. Place .cursor/mcp.json in your project root")
        print("  2. Restart Cursor")
    elif client == "codex":
        print("  1. Add the snippet to ~/.codex/config.toml")
        print("  2. Run:  codex")
    elif client == "opencode":
        print("  1. Place opencode.json in your project root")
        print("  2. Run:  opencode")
    elif client == "gemini":
        print("  1. Merge the snippet into ~/.gemini/settings.json")
        print("  2. Run:  gemini")
    print()
    print("Docs: https://github.com/georgy-agaev/yandex-direct-metrica-mcp")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        banner()
        client = ask_client()
        state_dir = ask_state_dir()
        install = ask_install()
        oauth = ask_oauth()
        direct = ask_direct()
        metrica = ask_metrica()
        wordstat = ask_wordstat()
        audience = ask_audience()
        accounts = ask_accounts()

        print(f"\n{_bold('Writing configuration files')}")
        write_env(state_dir, oauth, direct, metrica, wordstat, audience)
        if accounts:
            write_accounts(state_dir, accounts)

        register_mcp(client, state_dir, install)
        validate(state_dir)
        print_next_steps(client)
        print(_green("Setup complete!"))
    except KeyboardInterrupt:
        print("\n\nAborted.")
        sys.exit(130)
    except EOFError:
        print("\n\nNo input. Aborting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
