import threading

import pytest

import mcp_yandex_ad.server as server
from mcp_yandex_ad.accounts import AccountProfile
from mcp_yandex_ad.auth import TokenManager
from mcp_yandex_ad.clients import YandexClients
from mcp_yandex_ad.config import AppConfig
from mcp_yandex_ad.ratelimit import RateLimiter
from mcp_yandex_ad.server import AppContext, _dashboard_generate_option1


def _config(**overrides):
    data = dict(
        access_token="token",
        refresh_token=None,
        client_id=None,
        client_secret=None,
        audience_access_token=None,
        audience_refresh_token=None,
        audience_client_id=None,
        audience_client_secret=None,
        wordstat_access_token=None,
        wordstat_refresh_token=None,
        wordstat_client_id=None,
        wordstat_client_secret=None,
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


def test_dashboard_multi_account_uses_unique_report_names(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config()
    config.accounts.update(
        {
            "a1": AccountProfile(id="a1", name="A1", direct_client_login="login1", metrica_counter_ids=["1"]),
            "a2": AccountProfile(id="a2", name="A2", direct_client_login="login2", metrica_counter_ids=["2"]),
        }
    )
    ctx = _ctx(config)

    seen: dict[str, str | None] = {}

    def fake_direct_report(_ctx, params, *, direct_client_login=None):
        report_name = str(params.get("ReportName") or "")
        if report_name in seen and seen[report_name] != direct_client_login:
            return {"error": {"message": "duplicate report name"}}
        seen[report_name] = direct_client_login
        date_to = ((params.get("SelectionCriteria") or {}).get("DateTo")) or "2026-01-02"
        cid = "101" if direct_client_login == "login1" else "202"
        raw = f"Date\tCampaignId\tImpressions\tClicks\tCost\n{date_to}\t{cid}\t10\t2\t100.0\n"
        return {"raw": raw}

    def fake_direct_get(_ctx, resource, params, *, direct_client_login=None):
        if resource != "campaigns":
            raise AssertionError(f"Unexpected Direct resource: {resource}")
        cid = 101 if direct_client_login == "login1" else 202
        return {"result": {"Campaigns": [{"Id": cid, "Name": f"Camp-{direct_client_login}"}]}}

    def fake_metrica_get_stats(_ctx, params):
        return {"data": []}

    monkeypatch.setattr(server, "_direct_report", fake_direct_report)
    monkeypatch.setattr(server, "_direct_get", fake_direct_get)
    monkeypatch.setattr(server, "_metrica_get_stats", fake_metrica_get_stats)

    res = _dashboard_generate_option1(
        ctx,
        {
            "date_from": "2026-01-01",
            "date_to": "2026-01-02",
            "all_accounts": True,
            "include_html": False,
            "return_data": True,
        },
    )
    data = res["result"]["data"]
    assert sorted(data["accounts"].keys()) == ["a1", "a2"]

    for account_id in ["a1", "a2"]:
        per = data["accounts"][account_id]
        assert per["direct"]["campaign_data"], f"Expected non-empty campaign_data for {account_id}"
        assert per["direct"]["current"]["totals"]["impressions"] > 0
        summaries = per["direct"].get("campaign_summaries") or {}
        assert summaries, f"Expected non-empty campaign_summaries for {account_id}"
        first = next(iter(summaries.values()))
        assert first["current"]["impressions"] > 0
