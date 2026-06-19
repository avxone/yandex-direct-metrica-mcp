from __future__ import annotations

from types import SimpleNamespace

import pytest
from requests import Response

from mcp_yandex_ad import server
from mcp_yandex_ad.errors import normalize_error
from mcp_yandex_ad.hf_wordstat import handle as hf_wordstat_handle
from mcp_yandex_ad.wordstat_client import WordstatError


class _HFConfig:
    hf_enabled = True


class _HFWordstatCtx:
    config = _HFConfig()

    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def _wordstat_post(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        self.calls.append((path, dict(payload)))
        return self.responses.pop(0)


def test_wordstat_regions_payload_maps_region_type_aliases() -> None:
    assert server._build_wordstat_regions_payload({"phrase": "x", "region_type": "regions"})["region"] == "REGION_REGIONS"
    assert server._build_wordstat_regions_payload({"phrase": "x", "region_type": "cities"})["region"] == "REGION_CITIES"
    assert server._build_wordstat_regions_payload({"phrase": "x", "region_type": "all"})["region"] == "REGION_ALL"
    assert server._build_wordstat_regions_payload({"phrase": "x", "region_type": "REGION_CITIES"})["region"] == "REGION_CITIES"
    assert "region" not in server._build_wordstat_regions_payload({"phrase": "x"})


def test_wordstat_regions_payload_preserves_raw_params() -> None:
    raw = {"phrase": "x", "region": "REGION_REGIONS"}
    assert server._build_wordstat_regions_payload({"params": raw, "region_type": "cities"}) is raw


def test_wordstat_dynamics_monthly_and_weekly_dates() -> None:
    monthly = server._build_wordstat_dynamics_payload(
        {"phrase": "x", "from_date": "2026-01", "to_date": "2026-02", "period": "monthly"}
    )
    assert monthly["toDate"] == "2026-02-28T23:59:59Z"

    month_end = server._build_wordstat_dynamics_payload(
        {"phrase": "x", "from_date": "2026-01", "to_date": "2026-02-28", "period": "PERIOD_MONTHLY"}
    )
    assert month_end["toDate"] == "2026-02-28T23:59:59Z"

    with pytest.raises(ValueError, match="last day of the month"):
        server._build_wordstat_dynamics_payload(
            {"phrase": "x", "from_date": "2026-01", "to_date": "2026-02-27", "period": "monthly"}
        )

    with pytest.raises(ValueError, match="week-end boundary"):
        server._build_wordstat_dynamics_payload(
            {"phrase": "x", "from_date": "2026-01-01", "to_date": "2026-01-07", "period": "weekly"}
        )


def test_wordstat_dynamics_preserves_raw_params() -> None:
    raw = {"phrase": "x", "fromDate": "2026-01-01T00:00:00Z", "toDate": "2026-01-07T23:59:59Z"}
    assert server._build_wordstat_dynamics_payload({"params": raw, "period": "weekly"}) is raw


def test_hf_suggest_keywords_includes_associations_and_merges_sources() -> None:
    ctx = _HFWordstatCtx(
        [
            {
                "results": [{"phrase": "чат бот", "count": "10"}],
                "associations": [{"phrase": "чатбот", "count": "7"}, {"phrase": "чат бот", "count": "3"}],
            }
        ]
    )

    out = hf_wordstat_handle(
        "wordstat.hf.suggest_keywords",
        ctx,
        {"seed_phrases": ["чат бот для бизнеса"], "max_seed_phrases_per_call": 1, "max_candidates": 10},
    )

    candidates = {item["phrase"]: item for item in out["result"]["candidates"]}
    assert candidates["чатбот"]["provider_sources"] == ["association"]
    assert candidates["чат бот"]["score"] == 13.0
    assert candidates["чат бот"]["provider_sources"] == ["result", "association"]


def test_hf_suggest_keywords_cursor_preserves_provider_sources() -> None:
    ctx = _HFWordstatCtx(
        [
            {"associations": [{"phrase": "first", "count": 5}]},
            {"results": [{"phrase": "second", "count": 3}]},
        ]
    )

    first = hf_wordstat_handle(
        "wordstat.hf.suggest_keywords",
        ctx,
        {"seed_phrases": ["a", "b"], "max_seed_phrases_per_call": 1, "max_candidates": 10},
    )
    second = hf_wordstat_handle(
        "wordstat.hf.suggest_keywords",
        ctx,
        {"cursor": first["preview"]["cursor"], "max_seed_phrases_per_call": 1, "max_candidates": 10},
    )

    candidates = {item["phrase"]: item for item in second["result"]["candidates"]}
    assert candidates["first"]["provider_sources"] == ["association"]
    assert candidates["second"]["provider_sources"] == ["result"]


def test_dashboard_wordstat_block_includes_association_only_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = SimpleNamespace(
        config=SimpleNamespace(
            wordstat_enabled=True,
            wordstat_search_api_folder_id="folder",
            wordstat_search_api_api_key="key",
            wordstat_search_api_iam_token=None,
        )
    )

    def fake_direct_get(_ctx, resource, params, *, direct_client_login=None):
        assert resource == "keywords"
        return {"result": {"Keywords": [{"CampaignId": 1, "Keyword": "seed"}]}}

    def fake_wordstat_post(_ctx, path, payload=None):
        assert path == "topRequests"
        return {"associations": [{"phrase": "association only", "count": "42"}]}

    monkeypatch.setattr(server, "_direct_get", fake_direct_get)
    monkeypatch.setattr(server, "_wordstat_post", fake_wordstat_post)

    block = server._dashboard_build_wordstat_block(
        ctx,
        args={"include_wordstat": True},
        campaign_data={"1": {"name": "Campaign", "daily": [{"date": "2026-06-01", "clicks": 1}]}},
        date_from="2026-06-01",
        date_to="2026-06-30",
        warnings=[],
    )

    candidate = block["campaigns"][0]["candidates"][0]
    assert candidate["phrase"] == "association only"
    assert candidate["provider_sources"] == ["association"]


def _wordstat_response(status: int, body: bytes) -> Response:
    response = Response()
    response.status_code = status
    response.reason = "Bad Request"
    response.url = "https://searchapi.api.cloud.yandex.net/v2/wordstat/dynamics"
    response._content = body
    response.headers["Content-Type"] = "application/json"
    return response


def test_wordstat_error_hints_for_monthly_boundary() -> None:
    exc = WordstatError(
        "Wordstat API error (HTTP 400)",
        response=_wordstat_response(400, b'{"message":"toDate must be the last day of the month"}'),
    )
    payload = normalize_error("wordstat.dynamics", exc)["error"]
    assert "YYYY-MM" in payload["hint"]


def test_wordstat_error_hints_for_permission() -> None:
    exc = WordstatError(
        "Wordstat API error (HTTP 403)",
        response=_wordstat_response(403, b'{"message":"permission denied"}'),
    )
    payload = normalize_error("wordstat.top_requests", exc)["error"]
    assert "search-api.webSearch.user" in payload["hint"]
