import json
import threading
from pathlib import Path

import pytest

import mcp_yandex_ad.server as server
from mcp_yandex_ad.auth import TokenManager
from mcp_yandex_ad.clients import YandexClients
from mcp_yandex_ad.config import AppConfig
from mcp_yandex_ad.ratelimit import RateLimiter
from mcp_yandex_ad.server import AppContext, _dashboard_generate_pro_html
from mcp_yandex_ad.tools import tool_definitions


def _config(**overrides) -> AppConfig:
    data = dict(
        access_token="token",
        refresh_token=None,
        client_id=None,
        client_secret=None,
        audience_access_token=None,
        audience_refresh_token=None,
        audience_client_id=None,
        audience_client_secret=None,
        direct_client_login="default-login",
        direct_client_logins=["default-login"],
        direct_api_version="v5",
        metrica_counter_ids=[],
        audience_enabled=True,
        wordstat_enabled=True,
        use_sandbox=False,
        write_enabled=False,
        write_sandbox_only=True,
        hf_enabled=True,
        hf_write_enabled=False,
        hf_destructive_enabled=False,
        cache_enabled=True,
        cache_ttl_seconds=300,
        direct_rate_limit_rps=0,
        metrica_rate_limit_rps=0,
        audience_rate_limit_rps=0,
        wordstat_rate_limit_rps=0,
        retry_max_attempts=3,
        retry_base_delay_seconds=0.5,
        retry_max_delay_seconds=8.0,
        content_mode="json",
        public_readonly=False,
        accounts_write_enabled=False,
        accounts_file=None,
        accounts={},
    )
    data.update(overrides)
    return AppConfig(**data)


def _ctx(config: AppConfig) -> AppContext:
    return AppContext(
        config=config,
        tokens=TokenManager(config, access_token="token"),
        audience_tokens=None,
        wordstat_tokens=None,
        clients=YandexClients(direct=None, metrica_management=None, metrica_stats=None, metrica_logs=None),
        cache=None,
        direct_rate_limiter=RateLimiter(0),
        metrica_rate_limiter=RateLimiter(0),
        audience_rate_limiter=RateLimiter(0),
        wordstat_rate_limiter=RateLimiter(0),
        direct_clients_cache={},
        direct_clients_cache_lock=threading.Lock(),
    )


def test_dashboard_generate_pro_html_hidden_in_public_readonly() -> None:
    tools = {tool.name for tool in tool_definitions(_config(public_readonly=True))}
    assert "dashboard.generate_pro_html" not in tools


def test_dashboard_generate_pro_html_visible_in_pro() -> None:
    tools = {tool.name for tool in tool_definitions(_config(public_readonly=False))}
    assert "dashboard.generate_pro_html" in tools


def test_dashboard_generate_pro_html_writes_enriched_payload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ctx = _ctx(_config())

    def fake_option1(_ctx, _args):
        return {
            "result": {
                "data": {
                    "meta": {
                        "generated_at": "2026-05-12T00:00:00Z",
                        "date_from": "2026-05-01",
                        "date_to": "2026-05-10",
                        "requested_date_to": "2026-05-10",
                        "prev_date_from": "2026-04-21",
                        "prev_date_to": "2026-04-30",
                        "account_id": "vx",
                        "project_name": "Voice Expert",
                        "direct_client_login": "login-vx",
                        "counter_id": "123",
                        "tool": "dashboard.generate_option1",
                    },
                    "coverage": {},
                    "warnings": [],
                    "direct": {
                        "current": {"totals": {"impressions": 100, "clicks": 10, "cost_rub": 1000.0}},
                        "prev": {"totals": {"impressions": 80, "clicks": 8, "cost_rub": 750.0}},
                        "campaign_data": {},
                        "campaign_summaries": {},
                    },
                    "metrica": {
                        "current": {"totals": {"visits": 11, "engaged": 7, "leads": 1}},
                        "prev": {"totals": {"visits": 9, "engaged": 6, "leads": 1}},
                        "direct_by_campaign": {"campaigns": {}},
                    },
                    "recommendations": {},
                }
            }
        }

    def fake_pro(_ctx, *, args, base_data):
        assert args["date_from"] == "2026-05-01"
        assert base_data["meta"]["account_id"] == "vx"
        return {
            "available": True,
            "warnings": ["wordstat fallback used"],
            "summary": {
                "findings_total": 2,
                "findings_by_severity": {"high": 1, "medium": 1, "low": 0, "info": 0},
                "search_terms_rows": 12,
                "keywords_rows": 9,
                "watchlist_rows": 4,
                "bids_campaigns": 2,
            },
            "blocks": {
                "top_search_terms": [
                    {"query": "voice ai", "clicks": 10, "cost_rub": 2500.0, "ctr": 1.8, "matched_keyword": "voice ai"}
                ],
                "top_keywords": [
                    {
                        "keyword": "voice analytics",
                        "clicks": 9,
                        "cost_rub": 1800.0,
                        "bounce_rate": 72.0,
                        "criterion_type": "KEYWORD",
                    }
                ],
                "campaign_watchlist": [
                    {
                        "short_name": "Brand Search",
                        "type": "TEXT_CAMPAIGN",
                        "cost_rub": 5000.0,
                        "clicks": 44,
                        "visits": 35,
                        "leads": 0,
                        "cpl": None,
                        "cost_delta_pct": 24.0,
                        "leads_delta_pct": -100.0,
                        "avg_bid_rub": 42.0,
                    }
                ],
                "tracking_gaps": {"available": True, "classified_share_pct": 82.0},
                "bid_summary": {"available": True, "campaigns": [{"campaign_id": "1", "avg_rub": 42.0}]},
            },
            "findings": {
                "items": [
                    {
                        "severity": "high",
                        "category": "campaigns",
                        "title": "Campaign spends with no leads",
                        "entity_label": "Brand Search",
                        "metrics": {"cost_rub": 5000.0, "clicks": 44, "leads": 0},
                        "recommendation": "Review search terms and negatives.",
                    },
                    {
                        "severity": "medium",
                        "category": "tracking",
                        "title": "Tracking coverage is incomplete",
                        "entity_label": "UTMCampaign",
                        "metrics": {"classified_share_pct": 82.0},
                        "recommendation": "Normalize campaign markup.",
                    },
                ],
                "counts": {"high": 1, "medium": 1, "low": 0, "info": 0},
            },
            "by_campaign": {
                "1": {
                    "available": True,
                    "watchlist": {"campaign_id": "1", "short_name": "Brand Search", "leads": 0, "cpl": None},
                    "search_terms": [{"query": "voice ai", "matched_keyword": "voice ai", "clicks": 10, "ctr": 1.8, "cost_rub": 2500.0}],
                    "keywords": [{"keyword": "voice analytics", "criterion_type": "KEYWORD", "clicks": 9, "bounce_rate": 72.0, "cost_rub": 1800.0}],
                    "findings": [{"severity": "high", "category": "campaigns", "title": "Campaign spends with no leads", "entity_label": "Brand Search", "metrics": {"cost_rub": 5000.0}, "recommendation": "Review search terms and negatives."}],
                    "bid_summary": {"campaign_id": "1", "avg_rub": 42.0},
                    "tracking_notes": ["Check UTM mapping."],
                    "today_actions": ["Review search terms and negatives."],
                }
            },
            "recommendations": {"today_actions": ["Review search terms and negatives."]},
        }

    monkeypatch.setattr(server, "_dashboard_generate_option1", fake_option1)
    monkeypatch.setattr(server, "_dashboard_build_pro_account_data", fake_pro)

    res = _dashboard_generate_pro_html(
        ctx,
        {
            "date_from": "2026-05-01",
            "date_to": "2026-05-10",
            "output_dir": str(tmp_path),
            "return_data": False,
        },
    )

    files = res["result"]["files"]
    html_path = Path(files["html_path"])
    json_path = Path(files["json_path"])

    assert html_path.exists()
    assert json_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["meta"]["tool"] == "dashboard.generate_pro_html"
    assert payload["pro"]["summary"]["findings_total"] == 2
    assert payload["pro"]["blocks"]["campaign_watchlist"][0]["short_name"] == "Brand Search"
    assert payload["pro"]["by_campaign"]["1"]["bid_summary"]["avg_rub"] == 42.0

    html = html_path.read_text(encoding="utf-8")
    assert "Campaign spends with no leads" in html
    assert "wordstat fallback used" in html
    assert "modalProCard" in html
    assert "modalProFindingsList" in html
    assert "proPriorityList" in html


def test_dashboard_generate_pro_html_enriches_multi_account_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(_config())

    def fake_option1(_ctx, _args):
        return {
            "result": {
                "data": {
                    "meta": {
                        "generated_at": "2026-05-12T00:00:00Z",
                        "date_from": "2026-05-01",
                        "date_to": "2026-05-10",
                        "multi": True,
                        "account_ids": ["a1", "a2"],
                        "default_account_id": "a1",
                        "tool": "dashboard.generate_option1",
                    },
                    "accounts": {
                        "a1": {
                            "meta": {
                                "account_id": "a1",
                                "project_name": "A1",
                                "direct_client_login": "login-a1",
                                "counter_id": "11",
                                "date_from": "2026-05-01",
                                "date_to": "2026-05-10",
                                "prev_date_from": "2026-04-21",
                                "prev_date_to": "2026-04-30",
                            },
                            "coverage": {},
                            "warnings": [],
                            "direct": {"current": {"totals": {}}, "prev": {"totals": {}}, "campaign_data": {}, "campaign_summaries": {}},
                            "metrica": {"current": {"totals": {}}, "prev": {"totals": {}}, "direct_by_campaign": {"campaigns": {}}},
                            "recommendations": {},
                        },
                        "a2": {
                            "meta": {
                                "account_id": "a2",
                                "project_name": "A2",
                                "direct_client_login": "login-a2",
                                "counter_id": "22",
                                "date_from": "2026-05-01",
                                "date_to": "2026-05-10",
                                "prev_date_from": "2026-04-21",
                                "prev_date_to": "2026-04-30",
                            },
                            "coverage": {},
                            "warnings": [],
                            "direct": {"current": {"totals": {}}, "prev": {"totals": {}}, "campaign_data": {}, "campaign_summaries": {}},
                            "metrica": {"current": {"totals": {}}, "prev": {"totals": {}}, "direct_by_campaign": {"campaigns": {}}},
                            "recommendations": {},
                        },
                    },
                    "warnings": [],
                }
            }
        }

    def fake_pro(_ctx, *, args, base_data):
        account_id = str((base_data.get("meta") or {}).get("account_id") or args.get("account_id"))
        return {
            "available": True,
            "warnings": [],
            "summary": {
                "findings_total": 1,
                "findings_by_severity": {"high": 0, "medium": 1, "low": 0, "info": 0},
                "search_terms_rows": 0,
                "keywords_rows": 0,
                "watchlist_rows": 0,
                "bids_campaigns": 0,
            },
            "blocks": {"top_search_terms": [], "top_keywords": [], "campaign_watchlist": [], "tracking_gaps": {"available": False}, "bid_summary": {"available": False, "campaigns": []}},
            "findings": {"items": [{"severity": "medium", "title": f"check {account_id}"}], "counts": {"high": 0, "medium": 1, "low": 0, "info": 0}},
            "by_campaign": {},
            "recommendations": {"today_actions": [f"check {account_id}"]},
        }

    monkeypatch.setattr(server, "_dashboard_generate_option1", fake_option1)
    monkeypatch.setattr(server, "_dashboard_build_pro_account_data", fake_pro)

    res = _dashboard_generate_pro_html(
        ctx,
        {
            "date_from": "2026-05-01",
            "date_to": "2026-05-10",
            "all_accounts": True,
            "include_html": False,
            "return_data": True,
        },
    )

    data = res["result"]["data"]
    assert data["meta"]["tool"] == "dashboard.generate_pro_html"
    assert data["accounts"]["a1"]["pro"]["findings"]["items"][0]["title"] == "check a1"
    assert data["accounts"]["a2"]["pro"]["findings"]["items"][0]["title"] == "check a2"
