"""Best-effort diagnostics for atypical Direct campaign types."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .report_names import make_unique_report_name


def _parse_report_totals(report_payload: dict[str, Any]) -> dict[str, float]:
    raw = report_payload.get("raw")
    if not isinstance(raw, str) or not raw.strip():
        return {"impressions": 0.0, "clicks": 0.0, "cost": 0.0}

    lines = [line for line in raw.splitlines() if line.strip()]
    if len(lines) < 2:
        return {"impressions": 0.0, "clicks": 0.0, "cost": 0.0}

    header = [col.strip() for col in lines[0].split("\t")]
    index = {name: i for i, name in enumerate(header)}
    totals = {"impressions": 0.0, "clicks": 0.0, "cost": 0.0}
    for line in lines[1:]:
        cells = line.split("\t")
        for key, field in (("impressions", "Impressions"), ("clicks", "Clicks"), ("cost", "Cost")):
            idx = index.get(field)
            if idx is None or idx >= len(cells):
                continue
            try:
                totals[key] += float(cells[idx])
            except Exception:
                continue
    return totals


def detect_special_campaign(ctx: Any, *, campaign_id: int, counts: dict[str, int]) -> dict[str, Any] | None:
    """Detect campaigns with live delivery but no standard structure."""

    if any(int(counts.get(key) or 0) > 0 for key in ("adgroups", "ads", "keywords")):
        return None

    today_utc = date.today()
    date_to = today_utc - timedelta(days=1)
    date_from = date_to - timedelta(days=29)
    report = ctx._direct_report(  # type: ignore[attr-defined]
        {
            "SelectionCriteria": {
                "DateFrom": date_from.isoformat(),
                "DateTo": date_to.isoformat(),
                "Filter": [{"Field": "CampaignId", "Operator": "IN", "Values": [str(campaign_id)]}],
            },
            "FieldNames": ["Date", "CampaignId", "Impressions", "Clicks", "Cost"],
            "ReportName": make_unique_report_name(f"diagnose_campaign_{campaign_id}_{date_from.isoformat()}_{date_to.isoformat()}"),
            "ReportType": "CAMPAIGN_PERFORMANCE_REPORT",
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "YES",
            "IncludeDiscount": "NO",
        }
    )
    totals = _parse_report_totals(report if isinstance(report, dict) else {})
    if totals["impressions"] <= 0 and totals["clicks"] <= 0 and totals["cost"] <= 0:
        return None

    return {
        "campaign_type": "SPECIAL_NO_STRUCTURE",
        "counts_applicable": False,
        "counts": counts,
        "performance_signal": {
            "lookback_days": 30,
            "impressions": totals["impressions"],
            "clicks": totals["clicks"],
            "cost": totals["cost"],
        },
        "note": (
            "Campaign has live delivery but no traditional adgroups/ads/keywords structure. "
            "Treat it as a special Direct campaign type; Telegram Channels is a known example."
        ),
    }
