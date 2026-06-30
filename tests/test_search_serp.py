from __future__ import annotations

import base64
from types import SimpleNamespace

from mcp_yandex_ad import server
from mcp_yandex_ad.ratelimit import RateLimiter
from mcp_yandex_ad.search_client import (
    build_search_serp_payload,
    normalize_search_serp,
    parse_search_xml,
)


def test_build_search_serp_payload_maps_region_device_and_html_limit() -> None:
    payload, meta = build_search_serp_payload(
        {
            "query": "гарнитура для колл центра купить",
            "region": 213,
            "device": "desktop",
            "format": "html",
            "mode": "sync",
            "n_results": 10,
        },
        folder_id="folder-1",
        default_region=225,
    )

    assert payload["folderId"] == "folder-1"
    assert payload["query"]["searchType"] == "SEARCH_TYPE_RU"
    assert payload["query"]["queryText"] == "гарнитура для колл центра купить"
    assert payload["groupSpec"]["groupsOnPage"] == "10"
    assert payload["region"] == "213"
    assert payload["responseFormat"] == "FORMAT_HTML"
    assert "Macintosh" in payload["userAgent"]
    assert meta["device"] == "DEVICE_DESKTOP"
    assert meta["region"] == 213


def test_normalize_search_html_extracts_top_ads_and_organic() -> None:
    raw_html = """
    <html><body>
      <li class="serp-item serp-adv" data-cid="ad-1">
        <span>Реклама</span>
        <a href="https://ads.example.ru/page"><h2>Ad title</h2></a>
        <div>Ad snippet text</div>
      </li>
      <li class="serp-item" data-cid="org-1">
        <a class="OrganicTitle-Link" href="https://organic.example.ru/a"><h2>Organic title</h2></a>
        <div>Organic snippet text</div>
      </li>
    </body></html>
    """

    out = normalize_search_serp(raw_html, response_format="FORMAT_HTML")

    assert out["captcha"] is False
    assert out["ads_count_top"] == 1
    assert out["ads"] == [
        {
            "domain": "ads.example.ru",
            "title": "Ad title",
            "url": "https://ads.example.ru/page",
            "snippet": "Реклама Ad title Ad snippet text",
            "position": 1,
        }
    ]
    assert out["organic"][0]["domain"] == "organic.example.ru"
    assert out["organic"][0]["title"] == "Organic title"
    assert out["organic"][0]["position"] == 1


def test_parse_search_xml_extracts_organic_results() -> None:
    raw_xml = """
    <yandexsearch>
      <request><reqid>req-1</reqid></request>
      <response>
        <found-docs-human>Нашлось 10 млн результатов</found-docs-human>
        <results><grouping><group><doc>
          <url>https://organic.example.ru/a</url>
          <domain>organic.example.ru</domain>
          <title>Organic XML title</title>
          <passages><passage>XML snippet</passage></passages>
        </doc></group></grouping></results>
      </response>
    </yandexsearch>
    """

    out = parse_search_xml(raw_xml)

    assert out["request_id"] == "req-1"
    assert out["found_docs_human"] == "Нашлось 10 млн результатов"
    assert out["organic"] == [
        {
            "domain": "organic.example.ru",
            "title": "Organic XML title",
            "url": "https://organic.example.ru/a",
            "snippet": "XML snippet",
            "position": 1,
        }
    ]
    assert out["ads"] == []


def test_search_serp_server_helper_omits_raw_by_default(monkeypatch) -> None:
    raw_html = """
    <li class="serp-item" data-cid="org-1">
      <a href="https://example.ru"><h2>Title</h2></a>
      <div>Snippet</div>
    </li>
    """
    encoded = base64.b64encode(raw_html.encode("utf-8")).decode("ascii")
    captured: dict[str, object] = {}

    class FakeSearchApiClient:
        def __init__(self, **kwargs) -> None:
            captured["client_kwargs"] = kwargs

        def search(self, payload):
            captured["payload"] = payload
            return {"rawData": encoded}

    monkeypatch.setattr(server, "SearchApiClient", FakeSearchApiClient)
    ctx = SimpleNamespace(
        config=SimpleNamespace(
            search_api_enabled=True,
            wordstat_search_api_folder_id="folder-1",
            wordstat_search_api_api_key="key-1",
            wordstat_search_api_iam_token=None,
            search_api_default_region=213,
            search_api_web_base_url=None,
            retry_max_attempts=1,
            retry_base_delay_seconds=0,
            retry_max_delay_seconds=0,
        ),
        wordstat_rate_limiter=RateLimiter(0),
    )

    out = server._search_serp(ctx, {"query": "x", "n_results": 5})

    assert out["query"] == "x"
    assert out["region"] == 213
    assert out["device"] == "DEVICE_DESKTOP"
    assert out["organic"][0]["domain"] == "example.ru"
    assert "raw_html" not in out
    assert captured["payload"]["responseFormat"] == "FORMAT_HTML"
