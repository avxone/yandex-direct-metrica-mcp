"""Check live access to Yandex Search API Wordstat.

This script uses the same runtime config and payload builders as the MCP server.
It performs a bounded read-only smoke:
- getRegionsTree
- topRequests
- regions
- dynamics (monthly)
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mcp_yandex_ad import server  # noqa: E402
from mcp_yandex_ad.config import load_config  # noqa: E402
from mcp_yandex_ad.errors import MissingClientError, normalize_error  # noqa: E402
from mcp_yandex_ad.ratelimit import RateLimiter  # noqa: E402


def _monthly_window(today: dt.date) -> tuple[str, str]:
    current_month_start = today.replace(day=1)
    prev_month_end = current_month_start - dt.timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)
    return prev_month_start.strftime("%Y-%m"), prev_month_end.strftime("%Y-%m-%d")


def _ctx() -> SimpleNamespace:
    config = load_config()
    return SimpleNamespace(
        config=config,
        cache=None,
        wordstat_rate_limiter=RateLimiter(getattr(config, "wordstat_rate_limit_rps", 0)),
    )


def _print_error(tool: str, exc: Exception) -> None:
    print(json.dumps(normalize_error(tool, exc), ensure_ascii=False))


def _items_count(payload: dict[str, object], *keys: str) -> int:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
    return 0


def main() -> int:
    load_dotenv()
    phrase = os.environ.get("LIVE_TEST_WORDSTAT_PHRASE", "яндекс директ")
    ctx = _ctx()
    config = ctx.config

    if not getattr(config, "wordstat_enabled", False):
        print("Wordstat is disabled (MCP_WORDSTAT_ENABLED=false).")
        return 1
    if not getattr(config, "wordstat_search_api_folder_id", None):
        print("Missing YANDEX_SEARCH_API_FOLDER_ID.")
        return 1
    if not (
        getattr(config, "wordstat_search_api_api_key", None)
        or getattr(config, "wordstat_search_api_iam_token", None)
    ):
        print("Missing YANDEX_SEARCH_API_API_KEY or YANDEX_SEARCH_API_IAM_TOKEN.")
        return 1

    try:
        regions_tree = server._wordstat_post(ctx, "getRegionsTree")
        print(f"Wordstat getRegionsTree OK: {max(1, _items_count(regions_tree, 'regions', 'items'))} top-level items")
    except Exception as exc:  # pragma: no cover - runtime safety
        _print_error("wordstat.get_regions_tree", exc)
        return 2

    try:
        top_payload = server._build_wordstat_top_requests_payload({"phrase": phrase, "num_phrases": 5})
        top_requests = server._wordstat_top_requests_with_fallback(ctx, top_payload)
        result_count = _items_count(top_requests, "topRequests", "results")
        assoc_count = _items_count(top_requests, "associations")
        print(f"Wordstat topRequests OK: phrase={phrase!r} results={result_count} associations={assoc_count}")
    except Exception as exc:  # pragma: no cover - runtime safety
        _print_error("wordstat.top_requests", exc)
        return 2

    try:
        regions_payload = server._build_wordstat_regions_payload({"phrase": phrase, "region_type": "regions"})
        regions = server._wordstat_post(ctx, "regions", regions_payload)
        print(f"Wordstat regions OK: buckets={max(1, _items_count(regions, 'regions', 'items', 'results'))}")
    except Exception as exc:  # pragma: no cover - runtime safety
        _print_error("wordstat.regions", exc)
        return 2

    try:
        from_month, to_month_end = _monthly_window(dt.date.today())
        dynamics_payload = server._build_wordstat_dynamics_payload(
            {
                "phrase": phrase,
                "from_date": from_month,
                "to_date": to_month_end,
                "period": "monthly",
            }
        )
        dynamics = server._wordstat_post(ctx, "dynamics", dynamics_payload)
        print(f"Wordstat dynamics OK: points={max(1, _items_count(dynamics, 'dynamics', 'items', 'results'))}")
    except MissingClientError as exc:  # pragma: no cover - runtime safety
        _print_error("wordstat.dynamics", exc)
        return 1
    except Exception as exc:  # pragma: no cover - runtime safety
        _print_error("wordstat.dynamics", exc)
        return 2

    print("Wordstat live validation OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
