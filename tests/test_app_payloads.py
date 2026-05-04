from __future__ import annotations

from mcp_yandex_ad.app_payloads import compact_sections, is_app_safe_payload
from mcp_yandex_ad.server import _dashboard_build_compact_result


def test_compact_sections_drops_known_raw_blocks() -> None:
    payload = {
        "summary": {"direct": {"current": {"total_impressions": 10}}},
        "direct": {"raw_report": {"raw": "big-tsv"}},
        "metrica": {"sources_raw_report": {"data": [1, 2, 3]}},
        "warnings": [],
    }

    compact = compact_sections(payload)

    assert "raw_report" not in compact["direct"]
    assert "sources_raw_report" not in compact["metrica"]
    assert compact["summary"]["direct"]["current"]["total_impressions"] == 10


def test_is_app_safe_payload_accepts_dashboard_compact_result() -> None:
    payload = _dashboard_build_compact_result(
        {
            "meta": {"date_from": "2026-01-01", "date_to": "2026-01-02"},
            "direct": {"current": {"totals": {"impressions": 10, "clicks": 2, "cost_rub": 100.0, "ctr": 20.0, "cpc": 50.0}}},
            "metrica": {"current": {"totals": {"visits": 5, "users": 4, "bounce_rate": 10.0, "avg_visit_duration_seconds": 42.0, "page_depth": 1.5, "engaged": 4.5, "leads": 1.0}}},
        },
        warnings=[],
        coverage={"ok": True},
    )

    assert is_app_safe_payload(payload) is True


def test_is_app_safe_payload_rejects_payload_with_raw_sections() -> None:
    payload = {"summary": {}, "raw": {"tsv": "x"}}

    assert is_app_safe_payload(payload) is False


def test_is_app_safe_payload_rejects_oversized_strings() -> None:
    payload = {"summary": {}, "message": "x" * 10001}

    assert is_app_safe_payload(payload) is False
