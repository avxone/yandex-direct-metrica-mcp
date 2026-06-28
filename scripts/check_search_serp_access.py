"""Check live access to Yandex Search API SERP.

This script uses the same runtime config and Search API helpers as the MCP
server. It performs a bounded read-only smoke query and validates that at least
one normalized result bucket is returned.
"""

from __future__ import annotations

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


def _ctx() -> SimpleNamespace:
    config = load_config()
    return SimpleNamespace(
        config=config,
        cache=None,
        wordstat_rate_limiter=RateLimiter(getattr(config, "wordstat_rate_limit_rps", 0)),
    )


def _print_error(tool: str, exc: Exception) -> None:
    print(json.dumps(normalize_error(tool, exc), ensure_ascii=False))


def main() -> int:
    load_dotenv()
    query = os.environ.get("LIVE_TEST_SEARCH_QUERY", "яндекс директ")
    ctx = _ctx()
    config = ctx.config

    if not getattr(config, "search_api_enabled", True):
        print("Search API tools are disabled (MCP_SEARCH_API_ENABLED=false).")
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
        result = server._search_serp(
            ctx,
            {
                "query": query,
                "device": "desktop",
                "n_results": 5,
            },
        )
    except MissingClientError as exc:  # pragma: no cover - runtime safety
        _print_error("search_serp", exc)
        return 1
    except Exception as exc:  # pragma: no cover - runtime safety
        _print_error("search_serp", exc)
        return 2

    organic_count = len(result.get("organic") or [])
    ads_count = len(result.get("ads") or [])
    print(
        "Search SERP OK: "
        f"query={query!r} region={result.get('region')} "
        f"ads={ads_count} top_ads={result.get('ads_count_top')} organic={organic_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
