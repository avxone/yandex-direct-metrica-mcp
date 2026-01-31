from mcp_yandex_ad.server import _dashboard_build_metrica_direct_split_by_utm


def test_dashboard_metrica_direct_split_by_utm_classifies_by_id_and_name():
    all_days = ["2026-01-01", "2026-01-02"]
    campaign_data = {
        "123456": {"name": "Camp Search", "shortName": "Camp Search", "type": "search"},
        "234567": {"name": "Camp RSYA", "shortName": "Camp RSYA", "type": "rsya"},
    }
    report = {
        "data": [
            # Classified by embedded id.
            {
                "dimensions": [
                    {"name": "2026-01-01"},
                    {"name": "utm-123456"},
                ],
                "metrics": [10, 50, 3],  # visits, bounceRate, sumGoalReachesAny
            },
            # Classified by exact campaign name.
            {
                "dimensions": [
                    {"name": "2026-01-01"},
                    {"name": "Camp RSYA"},
                ],
                "metrics": [20, 25, 2],
            },
            # Unclassified utm.
            {
                "dimensions": [
                    {"name": "2026-01-02"},
                    {"name": "unknown"},
                ],
                "metrics": [5, 0, 1],
            },
        ]
    }

    out = _dashboard_build_metrica_direct_split_by_utm(
        all_days=all_days,
        report=report,
        campaign_data=campaign_data,
        goals_mode="all",
        goal_ids_user=[],
        report_is_direct_only=False,
    )

    assert out["available"] is True
    assert out["method"] == "utm_campaign"
    assert out["search"]["totals"]["visits"] == 10
    assert out["rsya"]["totals"]["visits"] == 20
    assert out["meta"]["report_is_direct_only"] is False
    assert out["meta"]["classified_visits"] == 30
    assert out["meta"]["total_direct_visits"] is None
    assert out["meta"]["top_unclassified_utm"] == []


def test_dashboard_metrica_direct_split_selected_goals_sums_selected():
    all_days = ["2026-01-01"]
    campaign_data = {"123456": {"name": "Camp Search", "shortName": "Camp Search", "type": "search"}}
    report = {
        "data": [
            {
                "dimensions": [
                    {"name": "2026-01-01"},
                    {"name": "123456"},
                ],
                # visits, bounceRate, goal1, goal2
                "metrics": [10, 0, 2, 5],
            }
        ]
    }
    out = _dashboard_build_metrica_direct_split_by_utm(
        all_days=all_days,
        report=report,
        campaign_data=campaign_data,
        goals_mode="selected",
        goal_ids_user=["1", "2"],
        report_is_direct_only=True,
    )
    assert out["search"]["totals"]["leads"] == 7


def test_dashboard_metrica_direct_split_by_utm_filters_by_direct_click_order_allowlist():
    all_days = ["2026-01-01"]
    campaign_data = {
        "123456": {"name": "Camp Search", "shortName": "Camp Search", "type": "search"},
        "234567": {"name": "Camp RSYA", "shortName": "Camp RSYA", "type": "rsya"},
    }
    report = {
        "data": [
            {
                "dimensions": [{"name": "2026-01-01"}, {"name": "anything"}, {"direct_id": "N-123456", "name": "Camp Search"}],
                "metrics": [10, 0, 1],
            },
            # Should be ignored (not in allowlist).
            {
                "dimensions": [{"name": "2026-01-01"}, {"name": "anything"}, {"direct_id": "N-999999", "name": "Other"}],
                "metrics": [100, 0, 50],
            },
        ]
    }

    out = _dashboard_build_metrica_direct_split_by_utm(
        all_days=all_days,
        report=report,
        campaign_data=campaign_data,
        goals_mode="all",
        goal_ids_user=[],
        report_is_direct_only=True,
        direct_campaign_ids_allowlist={"123456"},
    )

    assert out["available"] is True
    assert out["search"]["totals"]["visits"] == 10
    assert out["search"]["totals"]["leads"] == 1
    assert out["rsya"]["totals"]["visits"] == 0
    assert out["meta"]["allowlist_rows_total"] == 2
    assert out["meta"]["allowlist_rows_matched"] == 1


def test_dashboard_metrica_direct_split_by_utm_allowlist_no_matches_returns_unavailable():
    all_days = ["2026-01-01"]
    campaign_data = {"123456": {"name": "Camp Search", "shortName": "Camp Search", "type": "search"}}
    report = {
        "data": [
            {
                "dimensions": [{"name": "2026-01-01"}, {"name": "anything"}, {"direct_id": "N-999999", "name": "Other"}],
                "metrics": [1, 0, 1],
            }
        ]
    }

    out = _dashboard_build_metrica_direct_split_by_utm(
        all_days=all_days,
        report=report,
        campaign_data=campaign_data,
        goals_mode="all",
        goal_ids_user=[],
        report_is_direct_only=True,
        direct_campaign_ids_allowlist={"123456"},
    )

    assert out["available"] is False
    assert out["reason"] == "allowlist_no_matches"
