"""Generate PRO HTML dashboard directly from local config.

This is a local convenience runner over the internal dashboard generator.
It reads `.env` / environment, builds the same runtime context as the MCP server,
and writes HTML + JSON artifacts into the requested directory.
"""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

import click
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mcp_yandex_ad.auth import TokenManager  # noqa: E402
from mcp_yandex_ad.cache import TTLCache  # noqa: E402
from mcp_yandex_ad.clients import build_clients  # noqa: E402
from mcp_yandex_ad.config import load_config  # noqa: E402
from mcp_yandex_ad.errors import normalize_error  # noqa: E402
from mcp_yandex_ad.ratelimit import RateLimiter  # noqa: E402
from mcp_yandex_ad.server import AppContext, _dashboard_generate_pro_html  # noqa: E402


def _build_context() -> AppContext:
    config = load_config()
    tokens = TokenManager(config)
    access_token = tokens.get_access_token()
    clients = build_clients(config, access_token)

    audience_tokens: TokenManager | None = None
    if getattr(config, "audience_enabled", False):
        audience_tokens = TokenManager(
            config,
            access_token=config.audience_access_token,
            refresh_token=config.audience_refresh_token,
            client_id=config.audience_client_id,
            client_secret=config.audience_client_secret,
            provider="audience",
        )

    wordstat_tokens: TokenManager | None = None
    if getattr(config, "wordstat_enabled", False):
        wordstat_tokens = TokenManager(
            config,
            access_token=config.wordstat_access_token,
            refresh_token=config.wordstat_refresh_token,
            client_id=config.wordstat_client_id,
            client_secret=config.wordstat_client_secret,
            provider="wordstat",
        )

    cache: TTLCache | None = None
    if config.cache_enabled and config.cache_ttl_seconds > 0:
        cache = TTLCache(config.cache_ttl_seconds)

    return AppContext(
        config=config,
        tokens=tokens,
        audience_tokens=audience_tokens,
        wordstat_tokens=wordstat_tokens,
        clients=clients,
        cache=cache,
        direct_rate_limiter=RateLimiter(config.direct_rate_limit_rps),
        metrica_rate_limiter=RateLimiter(config.metrica_rate_limit_rps),
        audience_rate_limiter=RateLimiter(getattr(config, "audience_rate_limit_rps", 0)),
        wordstat_rate_limiter=RateLimiter(getattr(config, "wordstat_rate_limit_rps", 0)),
        direct_clients_cache={},
        direct_clients_cache_lock=threading.Lock(),
    )


@click.command()
@click.option("--account-id", default=None, help="Profile id from accounts.json.")
@click.option("--all-accounts", is_flag=True, default=False, help="Generate one multi-account dashboard.")
@click.option("--direct-client-login", default=None, help="Optional Direct Client-Login override.")
@click.option("--counter-id", default=None, help="Optional Metrica counter id override.")
@click.option("--goal-id", "goal_ids", multiple=True, help="Repeatable Metrica goal id.")
@click.option("--date-from", required=True, help="YYYY-MM-DD current period start.")
@click.option("--date-to", required=True, help="YYYY-MM-DD current period end.")
@click.option("--output-dir", required=True, type=click.Path(path_type=Path), help="Where to write HTML + JSON.")
@click.option("--dashboard-slug", default=None, help="Optional suffix for file names.")
@click.option("--include-wordstat/--no-include-wordstat", default=False, show_default=True)
@click.option("--include-audience/--no-include-audience", default=False, show_default=True)
@click.option("--include-raw-reports/--no-include-raw-reports", default=False, show_default=True)
@click.option("--max-campaigns", default=12, show_default=True, type=int)
@click.option("--max-keywords", default=100, show_default=True, type=int)
@click.option("--max-search-phrases", default=200, show_default=True, type=int)
@click.option("--max-findings", default=24, show_default=True, type=int)
def main(
    account_id: str | None,
    all_accounts: bool,
    direct_client_login: str | None,
    counter_id: str | None,
    goal_ids: tuple[str, ...],
    date_from: str,
    date_to: str,
    output_dir: Path,
    dashboard_slug: str | None,
    include_wordstat: bool,
    include_audience: bool,
    include_raw_reports: bool,
    max_campaigns: int,
    max_keywords: int,
    max_search_phrases: int,
    max_findings: int,
) -> None:
    load_dotenv()
    ctx = _build_context()

    args: dict[str, object] = {
        "date_from": date_from,
        "date_to": date_to,
        "output_dir": str(output_dir),
        "dashboard_slug": dashboard_slug,
        "include_wordstat": include_wordstat,
        "include_audience": include_audience,
        "include_raw_reports": include_raw_reports,
        "return_data": False,
        "max_campaigns": max_campaigns,
        "max_keywords": max_keywords,
        "max_search_phrases": max_search_phrases,
        "max_findings": max_findings,
    }
    if account_id:
        args["account_id"] = account_id
    if all_accounts:
        args["all_accounts"] = True
    if direct_client_login:
        args["direct_client_login"] = direct_client_login
    if counter_id:
        args["counter_id"] = counter_id
    if goal_ids:
        args["goal_ids"] = [str(item).strip() for item in goal_ids if str(item).strip()]

    try:
        result = _dashboard_generate_pro_html(ctx, args)
    except Exception as exc:
        click.echo(json.dumps(normalize_error("dashboard.generate_pro_html", exc), ensure_ascii=False))
        raise SystemExit(2) from exc

    payload = result.get("result") or {}
    files = payload.get("files") or {}
    click.echo(f"html: {files.get('html_path')}")
    click.echo(f"json: {files.get('json_path')}")

    pro_summary = payload.get("pro_summary")
    if isinstance(pro_summary, dict):
        click.echo(f"findings_total: {pro_summary.get('findings_total')}")
    elif isinstance(payload.get("accounts"), list):
        click.echo(f"accounts: {len(payload['accounts'])}")


if __name__ == "__main__":
    main()
