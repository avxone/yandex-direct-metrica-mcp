from __future__ import annotations

from types import SimpleNamespace
import threading

import pytest

from mcp_yandex_ad.accounts import AccountProfile
from mcp_yandex_ad import server
from mcp_yandex_ad.hf_direct import handle as hf_direct_handle
from mcp_yandex_ad.hf_metrica import handle as hf_metrica_handle


def _ctx_for_overrides() -> SimpleNamespace:
    return SimpleNamespace(
        config=SimpleNamespace(
            accounts={"proj": AccountProfile(id="proj", direct_client_login="child-login", metrica_counter_ids=["1"])},
            accounts_file=None,
        ),
        accounts_registry_lock=threading.Lock(),
        accounts_registry_cache=None,
        accounts_registry_mtime=None,
    )


def test_build_report_params_uses_unique_default_report_names() -> None:
    params1 = server._build_report_params(
        {
            "report_type": "CAMPAIGN_PERFORMANCE_REPORT",
            "field_names": ["Date", "CampaignId"],
            "date_from": "2026-05-01",
            "date_to": "2026-05-02",
        }
    )
    params2 = server._build_report_params(
        {
            "report_type": "CAMPAIGN_PERFORMANCE_REPORT",
            "field_names": ["Date", "CampaignId"],
            "date_from": "2026-05-01",
            "date_to": "2026-05-02",
        }
    )

    assert params1["ReportName"] != params2["ReportName"]
    assert params1["ReportName"].startswith("MCP_CAMPAIGN_PERFORMANCE_REPORT_2026-05-01_2026-05-02__")


def test_build_report_params_rejects_keyword_for_custom_report() -> None:
    with pytest.raises(ValueError, match="Use Criterion instead"):
        server._build_report_params(
            {
                "report_type": "CUSTOM_REPORT",
                "field_names": ["Date", "CampaignId", "Keyword"],
            }
        )


def test_resolve_account_overrides_allows_read_only_login_override() -> None:
    ctx = _ctx_for_overrides()

    resolved = server._resolve_account_overrides(
        ctx,
        "direct.raw_call",
        {"account_id": "proj", "direct_client_login": "agency-master", "resource": "campaigns", "method": "get"},
    )

    assert resolved["direct_client_login"] == "agency-master"


def test_resolve_account_overrides_treats_unknown_read_only_account_as_login() -> None:
    ctx = _ctx_for_overrides()

    resolved = server._resolve_account_overrides(
        ctx,
        "direct.raw_call",
        {"account_id": "agency-master", "resource": "campaigns", "method": "get"},
    )

    assert resolved["direct_client_login"] == "agency-master"
    assert "account_id" not in resolved


def test_wordstat_top_requests_falls_back_to_single_phrase_loop() -> None:
    calls: list[dict[str, object]] = []

    def fake_wordstat_post(_ctx, path: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        assert path == "topRequests"
        calls.append(dict(payload or {}))
        phrase = str((payload or {}).get("phrase") or "")
        return {"topRequests": [{"phrase": phrase, "count": 10}]}

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(server, "_wordstat_post", fake_wordstat_post)
    try:
        data = server._wordstat_top_requests_with_fallback(SimpleNamespace(), {"phrases": ["a", "b"], "numPhrases": 50})
    finally:
        monkeypatch.undo()

    assert data["fallback"]["mode"] == "single_phrase_loop"
    assert [item["phrase"] for item in data["topRequestsByPhrase"]] == ["a", "b"]
    assert calls[0]["phrase"] == "a"
    assert calls[1]["phrase"] == "b"


class _Cfg:
    hf_enabled = True


class _MetricaCtx:
    config = _Cfg()

    def __init__(self, pages: dict[int, dict[str, object]]) -> None:
        self.pages = pages
        self.calls: list[dict[str, object]] = []

    def _metrica_get_stats(self, params: dict[str, object]) -> dict[str, object]:
        self.calls.append(dict(params))
        offset = int(params.get("offset") or 0)
        return dict(self.pages[offset])


def test_metrica_hf_report_utm_campaigns_auto_paginates() -> None:
    ctx = _MetricaCtx(
        {
            0: {"total_rows": 3, "data": [{"id": 1}, {"id": 2}]},
            2: {"total_rows": 3, "data": [{"id": 3}]},
        }
    )

    out = hf_metrica_handle("metrica.hf.report_utm_campaigns", ctx, {"counter_id": "42", "date_from": "2026-01-01", "date_to": "2026-01-31"})

    assert out["status"] == "ok"
    assert len(out["result"]["raw"]["data"]) == 3
    assert "warnings" not in out
    assert len(ctx.calls) == 2


def test_metrica_hf_report_utm_campaigns_warns_when_limit_truncates() -> None:
    ctx = _MetricaCtx(
        {
            0: {"total_rows": 3, "data": [{"id": 1}]},
        }
    )

    out = hf_metrica_handle(
        "metrica.hf.report_utm_campaigns",
        ctx,
        {"counter_id": "42", "date_from": "2026-01-01", "date_to": "2026-01-31", "limit": 1},
    )

    assert out["status"] == "ok"
    assert out["warnings"][0]["code"] == "metrica_rows_truncated"


class _DirectCtx:
    config = _Cfg()

    def __init__(self) -> None:
        self.report_params: list[dict[str, object]] = []
        self.adgroup_calls = 0
        self.ads_calls = 0
        self.keyword_calls = 0

    def _direct_get(self, resource: str, params: dict[str, object]) -> dict[str, object]:
        page = dict(params.get("Page") or {})
        offset = int(page.get("Offset") or 0)
        if resource == "ads":
            if "Status" in ((params.get("FieldNames") or [])):
                return {
                    "result": {
                        "Ads": [
                            {"Id": 1, "CampaignId": 10, "AdGroupId": 100, "Status": "ACCEPTED", "State": "ON", "Type": "TEXT_AD", "TextAd": {"Title": "Good", "Href": "https://a"}},
                            {"Id": 2, "CampaignId": 10, "AdGroupId": 100, "Status": "ACCEPTED", "State": "OFF", "Type": "TEXT_AD", "TextAd": {"Title": "Off", "Href": "https://b"}},
                            {"Id": 3, "CampaignId": 10, "AdGroupId": 100, "Status": "DRAFT", "State": "ON", "Type": "TEXT_AD", "TextAd": {"Title": "Draft", "Href": "https://c"}},
                        ]
                    }
                }
        if resource == "adgroups":
            self.adgroup_calls += 1
            if offset == 0:
                return {"result": {"AdGroups": [{"Id": i} for i in range(1000)]}}
            return {"result": {"AdGroups": [{"Id": 1001}, {"Id": 1002}]}}
        if resource == "ads":
            self.ads_calls += 1
            if offset == 0:
                return {"result": {"Ads": [{"Id": i} for i in range(1000)]}}
            return {"result": {"Ads": [{"Id": 1001}, {"Id": 1002}]}}
        if resource == "keywords":
            self.keyword_calls += 1
            if offset == 0:
                return {"result": {"Keywords": [{"Id": i} for i in range(1000)]}}
            return {"result": {"Keywords": [{"Id": 1001}, {"Id": 1002}]}}
        raise AssertionError(resource)

    def _direct_report(self, params: dict[str, object]) -> dict[str, object]:
        self.report_params.append(dict(params))
        return {"raw": "Date\tCampaignId\tImpressions\tClicks\tCost\n2026-05-01\t10\t100\t5\t55.0\n"}


def test_hf_find_ads_respects_states_filter() -> None:
    class _AdsCtx:
        config = _Cfg()

        def _direct_get(self, resource: str, params: dict[str, object]) -> dict[str, object]:
            assert resource == "ads"
            return {
                "result": {
                    "Ads": [
                        {"Id": 1, "CampaignId": 10, "AdGroupId": 100, "Status": "ACCEPTED", "State": "ON", "Type": "TEXT_AD", "TextAd": {"Title": "Good", "Href": "https://a"}},
                        {"Id": 2, "CampaignId": 10, "AdGroupId": 100, "Status": "ACCEPTED", "State": "OFF", "Type": "TEXT_AD", "TextAd": {"Title": "Off", "Href": "https://b"}},
                        {"Id": 3, "CampaignId": 10, "AdGroupId": 100, "Status": "DRAFT", "State": "ON", "Type": "TEXT_AD", "TextAd": {"Title": "Draft", "Href": "https://c"}},
                    ]
                }
            }

    out = hf_direct_handle(
        "direct.hf.find_ads",
        _AdsCtx(),
        {"campaign_id": 10, "statuses": ["ACCEPTED"], "states": ["ON"]},
    )

    assert [ad["Id"] for ad in out["result"]["ads"]] == [1]


def test_hf_get_campaign_summary_paginates_and_warns_on_special_type() -> None:
    ctx = _DirectCtx()

    out = hf_direct_handle("direct.hf.get_campaign_summary", ctx, {"campaign_id": 10})

    assert out["status"] == "ok"
    assert out["result"]["counts"] == {"adgroups": 1002, "ads": 1002, "keywords": 1002}


def test_hf_get_campaign_summary_marks_special_no_structure() -> None:
    class _SpecialCtx:
        config = _Cfg()

        def _direct_get(self, resource: str, params: dict[str, object]) -> dict[str, object]:
            if resource == "adgroups":
                return {"result": {"AdGroups": []}}
            if resource == "ads":
                return {"result": {"Ads": []}}
            if resource == "keywords":
                return {"result": {"Keywords": []}}
            raise AssertionError(resource)

        def _direct_report(self, params: dict[str, object]) -> dict[str, object]:
            return {"raw": "Date\tCampaignId\tImpressions\tClicks\tCost\n2026-05-01\t10\t100\t5\t55.0\n"}

    out = hf_direct_handle("direct.hf.get_campaign_summary", _SpecialCtx(), {"campaign_id": 10})

    assert out["result"]["campaign_type"] == "SPECIAL_NO_STRUCTURE"
    assert out["result"]["counts_applicable"] is False
    assert out["warnings"][0]["code"] == "campaign_type_special_no_structure"


def test_hf_report_keywords_uses_custom_report_fields() -> None:
    class _ReportCtx:
        config = _Cfg()

        def __init__(self) -> None:
            self.params: dict[str, object] | None = None

        def _direct_report(self, params: dict[str, object]) -> dict[str, object]:
            self.params = dict(params)
            return {"raw": "Date\tCampaignId\tAdGroupId\tCriterion\tCriterionId\tCriterionType\tImpressions\tClicks\tCost\tBounces\n"}

    ctx = _ReportCtx()
    out = hf_direct_handle("direct.hf.report_keywords", ctx, {"campaign_id": 10, "date_from": "2026-05-01", "date_to": "2026-05-02"})

    assert out["status"] == "ok"
    assert ctx.params is not None
    assert ctx.params["ReportType"] == "CUSTOM_REPORT"
    assert "Criterion" in ctx.params["FieldNames"]
    assert "Keyword" not in ctx.params["FieldNames"]
