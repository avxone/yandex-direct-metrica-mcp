"""BI Option 2: datasets + incremental sync (cursor/NDJSON-friendly)."""

from __future__ import annotations

import base64
from datetime import date, datetime, timedelta
import json
from typing import Any

from .hf_audience import _build_direct_segment_proxy_series
from .hf_join import _extract_raw_and_columns, _metrica_filter_quote, _parse_delimited


def dashboard_option2_schema() -> dict[str, Any]:
    return {
        "result": {
            "version": 2,
            "datasets": [
                {
                    "name": "dashboard.dataset.audience_segments",
                    "primary_key": ["segment_id"],
                    "description": "Audience segments catalog (dimensions).",
                },
                {
                    "name": "dashboard.dataset.audience_overlap",
                    "primary_key": ["a", "b"],
                    "description": "Top overlap pairs between segments.",
                },
                {
                    "name": "dashboard.dataset.audience_segment_perf_daily",
                    "primary_key": ["segment_id", "date"],
                    "description": "Best-effort daily performance for a segment (proxy via Direct targeting).",
                },
                {
                    "name": "dashboard.dataset.direct_campaigns_dim",
                    "primary_key": ["account_id", "campaign_id"],
                    "description": "Direct campaigns catalog (dimensions).",
                },
                {
                    "name": "dashboard.dataset.direct_adgroups_dim",
                    "primary_key": ["account_id", "adgroup_id"],
                    "description": "Direct ad groups catalog (dimensions).",
                },
                {
                    "name": "dashboard.dataset.direct_keywords_dim",
                    "primary_key": ["account_id", "keyword_id"],
                    "description": "Direct keywords catalog (dimensions).",
                },
                {
                    "name": "dashboard.dataset.direct_campaign_daily",
                    "primary_key": ["account_id", "date", "campaign_id"],
                    "description": "Direct campaign daily performance (facts).",
                },
                {
                    "name": "dashboard.dataset.direct_keyword_daily",
                    "primary_key": ["account_id", "date", "keyword_id"],
                    "description": "Direct keyword daily performance (facts).",
                },
                {
                    "name": "dashboard.dataset.direct_ads_daily",
                    "primary_key": ["account_id", "date", "ad_id"],
                    "description": "Direct ads daily performance (facts).",
                },
                {
                    "name": "dashboard.dataset.direct_search_phrases_daily",
                    "primary_key": ["account_id", "date", "query", "adgroup_id"],
                    "description": "Direct search phrases daily performance (facts).",
                },
                {
                    "name": "dashboard.dataset.direct_bids_snapshot",
                    "primary_key": ["account_id", "keyword_id"],
                    "description": "Direct bids snapshot (dimensions-ish).",
                },
                {
                    "name": "dashboard.dataset.metrica_daily",
                    "primary_key": ["account_id", "date"],
                    "description": "Metrica daily summary (facts).",
                },
                {
                    "name": "dashboard.dataset.metrica_devices_daily",
                    "primary_key": ["account_id", "date", "device"],
                    "description": "Metrica daily visits by device category (facts).",
                },
                {
                    "name": "dashboard.dataset.metrica_geo_daily",
                    "primary_key": ["account_id", "date", "geo"],
                    "description": "Metrica daily visits by geo (country by default) (facts).",
                },
                {
                    "name": "dashboard.dataset.metrica_goals_daily",
                    "primary_key": ["account_id", "date", "goal_id"],
                    "description": "Metrica daily goal reaches by goal_id (facts).",
                },
                {
                    "name": "dashboard.dataset.metrica_utm_campaigns_daily",
                    "primary_key": ["account_id", "date", "utm_campaign", "utm_content"],
                    "description": "Metrica daily top UTM campaigns (facts, bounded).",
                },
                {
                    "name": "dashboard.dataset.metrica_landing_pages_daily",
                    "primary_key": ["account_id", "date", "landing_url"],
                    "description": "Metrica daily top landing pages (facts, bounded).",
                },
                {
                    "name": "dashboard.dataset.wordstat_top_requests",
                    "primary_key": ["seed_phrase", "phrase"],
                    "description": "Wordstat top requests for a seed phrase (bounded).",
                },
                {
                    "name": "dashboard.dataset.join_direct_vs_metrica_utm_daily",
                    "primary_key": ["account_id", "date", "campaign_id", "utm_campaign"],
                    "description": "Join: Direct daily spend/clicks with Metrica visits by UTMCampaign.",
                },
            ],
            "sync": {
                "tools": ["dashboard.sync.start", "dashboard.sync.next"],
                "cursor_format": "base64url(json)",
                "output": "NDJSON string (one JSON object per line).",
            },
        }
    }


def _extract_list(payload: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    result = payload.get("result")
    if isinstance(result, dict):
        for key in keys:
            value = result.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def _b64encode(obj: dict[str, Any]) -> str:
    raw = json.dumps(obj, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(text: str) -> dict[str, Any]:
    padded = text + "=" * (-len(text) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("cursor must decode to a JSON object")
    return data


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip().replace(",", "."))
    except Exception:
        return None


def _parse_ymd(value: Any) -> date:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Expected YYYY-MM-DD date string")
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except Exception as exc:
        raise ValueError(f"Invalid date: {text!r} (expected YYYY-MM-DD)") from exc


def _iter_date_chunks(date_from: str, date_to: str, *, chunk_days: int) -> list[tuple[str, str]]:
    start = _parse_ymd(date_from)
    end = _parse_ymd(date_to)
    if end < start:
        raise ValueError("date_to must be >= date_from")
    chunk_days = max(1, min(31, int(chunk_days)))

    chunks: list[tuple[str, str]] = []
    cur = start
    while cur <= end:
        nxt = min(end, cur + timedelta(days=chunk_days - 1))
        chunks.append((cur.isoformat(), nxt.isoformat()))
        cur = nxt + timedelta(days=1)
    return chunks


def _resolve_account_overrides_local(
    ctx: Any,
    *,
    account_id: str | None,
    direct_client_login: str | None,
    counter_id: str | None,
    needs_counter: bool,
) -> tuple[str | None, str | None]:
    if not account_id:
        return direct_client_login, counter_id
    profile = None
    try:
        profile = (getattr(getattr(ctx, "config", None), "accounts", None) or {}).get(account_id)
    except Exception:
        profile = None
    if profile is None:
        return direct_client_login, counter_id
    profile_login = (getattr(profile, "direct_client_login", None) or "").strip() or None
    if direct_client_login and profile_login and direct_client_login.strip() != profile_login:
        raise ValueError(
            f"direct_client_login={direct_client_login.strip()} conflicts with account_id={account_id} "
            f"(direct_client_login={profile_login})"
        )
    resolved_login = direct_client_login.strip() if isinstance(direct_client_login, str) and direct_client_login.strip() else profile_login

    resolved_counter = counter_id.strip() if isinstance(counter_id, str) and counter_id.strip() else None
    if needs_counter and not resolved_counter:
        counters = [str(x).strip() for x in (getattr(profile, "metrica_counter_ids", None) or []) if str(x).strip()]
        if len(counters) == 1:
            resolved_counter = counters[0]
        elif len(counters) > 1:
            raise ValueError(f"account_id={account_id} has multiple metrica_counter_ids; pass counter_id explicitly")
    return resolved_login, resolved_counter


def dataset_audience_segments(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for key in ("limit", "offset", "types", "statuses", "fields"):
        if args.get(key) is not None:
            params[key] = args.get(key)
    raw = ctx._audience_call("GET", "/segments", params=params or None)  # type: ignore[attr-defined]
    segments = _extract_list(raw, "segments", "items", "Segments")
    rows: list[dict[str, Any]] = []
    for s in segments:
        rows.append(
            {
                "segment_id": str(s.get("id") or s.get("segment_id") or ""),
                "name": s.get("name"),
                "type": s.get("type"),
                "status": s.get("status"),
                "updated_at": s.get("updated_at") or s.get("updated") or s.get("modified_at"),
                "size": s.get("size") or s.get("audience_size") or s.get("users"),
            }
        )
    return {"result": {"rows": rows, "raw_refs": [{"tool": "audience.segments.list", "params": params}]}}


def dataset_audience_overlap(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    seg_ids = args.get("segment_ids")
    if not isinstance(seg_ids, list) or not seg_ids:
        raise ValueError("segment_ids is required")
    payload: dict[str, Any] = {"segment_ids": [str(x) for x in seg_ids]}
    if args.get("mode") is not None:
        payload["mode"] = str(args.get("mode"))
    if args.get("limit") is not None:
        payload["limit"] = int(args.get("limit"))
    raw = ctx._audience_call("POST", "/segments/overlap", payload=payload)  # type: ignore[attr-defined]
    pairs = _extract_list(raw, "pairs", "items", "matrix")
    rows: list[dict[str, Any]] = []
    for p in pairs:
        a = p.get("a") or p.get("segment_a") or p.get("id_a")
        b = p.get("b") or p.get("segment_b") or p.get("id_b")
        if a is None or b is None:
            continue
        rows.append(
            {
                "a": str(a),
                "b": str(b),
                "overlap_share": p.get("overlap_share") or p.get("share"),
                "overlap_abs": p.get("overlap_abs") or p.get("count"),
            }
        )
    return {"result": {"rows": rows, "raw": raw, "raw_refs": [{"tool": "audience.segments.overlap", "payload": payload}]}}


def dataset_audience_segment_perf_daily(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    segment_id = str(args.get("segment_id") or "").strip()
    if not segment_id:
        raise ValueError("segment_id is required")
    date_from = str(args.get("date_from") or "").strip()
    date_to = str(args.get("date_to") or "").strip()
    if not date_from or not date_to:
        raise ValueError("date_from and date_to are required")
    max_targets = int(args.get("max_targets") or 200)
    max_targets = max(1, min(500, max_targets))
    series, coverage, raw_refs = _build_direct_segment_proxy_series(
        ctx,
        segment_id=segment_id,
        date_from=date_from,
        date_to=date_to,
        direct_client_login=str(args.get("direct_client_login")) if args.get("direct_client_login") else None,
        max_targets=max_targets,
    )
    rows: list[dict[str, Any]] = []
    for item in series:
        rows.append(
            {
                "segment_id": segment_id,
                "date": item.get("date"),
                "impressions": item.get("impressions"),
                "clicks": item.get("clicks"),
                "cost": item.get("cost"),
            }
        )
    return {"result": {"rows": rows, "coverage": coverage, "raw_refs": raw_refs}}


def dataset_direct_campaigns_dim(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    limit = int(args.get("limit") or 500)
    offset = int(args.get("offset") or 0)
    limit = max(1, min(10000, limit))
    offset = max(0, offset)
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    direct_client_login = (str(args.get("direct_client_login")).strip() if args.get("direct_client_login") else None) or None
    field_names = ["Id", "Name", "Type", "Status", "State"]
    params = {"SelectionCriteria": {}, "FieldNames": field_names, "Page": {"Limit": limit, "Offset": offset}}
    res = ctx._direct_get("campaigns", params, direct_client_login=direct_client_login)  # type: ignore[attr-defined]
    items = res.get("result", {}).get("Campaigns", []) if isinstance(res, dict) else []
    rows: list[dict[str, Any]] = []
    for c in items:
        if not isinstance(c, dict):
            continue
        cid = _safe_int(c.get("Id"))
        if cid is None:
            continue
        rows.append(
            {
                "account_id": account_id,
                "direct_client_login": direct_client_login,
                "campaign_id": cid,
                "name": c.get("Name"),
                "type": c.get("Type"),
                "status": c.get("Status"),
                "state": c.get("State"),
            }
        )
    return {"result": {"rows": rows, "raw_refs": [{"tool": "direct.campaigns.get", "params": params}]}}


def dataset_direct_adgroups_dim(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    limit = int(args.get("limit") or 500)
    offset = int(args.get("offset") or 0)
    limit = max(1, min(10000, limit))
    offset = max(0, offset)
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    direct_client_login = (str(args.get("direct_client_login")).strip() if args.get("direct_client_login") else None) or None
    field_names = ["Id", "Name", "CampaignId", "Status", "Type"]
    params = {"SelectionCriteria": {}, "FieldNames": field_names, "Page": {"Limit": limit, "Offset": offset}}
    res = ctx._direct_get("adgroups", params, direct_client_login=direct_client_login)  # type: ignore[attr-defined]
    items = res.get("result", {}).get("AdGroups", []) if isinstance(res, dict) else []
    rows: list[dict[str, Any]] = []
    for g in items:
        if not isinstance(g, dict):
            continue
        gid = _safe_int(g.get("Id"))
        if gid is None:
            continue
        rows.append(
            {
                "account_id": account_id,
                "direct_client_login": direct_client_login,
                "adgroup_id": gid,
                "campaign_id": _safe_int(g.get("CampaignId")),
                "name": g.get("Name"),
                "status": g.get("Status"),
                "type": g.get("Type"),
            }
        )
    return {"result": {"rows": rows, "raw_refs": [{"tool": "direct.adgroups.get", "params": params}]}}


def dataset_direct_keywords_dim(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    limit = int(args.get("limit") or 500)
    offset = int(args.get("offset") or 0)
    limit = max(1, min(10000, limit))
    offset = max(0, offset)
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    direct_client_login = (str(args.get("direct_client_login")).strip() if args.get("direct_client_login") else None) or None
    field_names = ["Id", "CampaignId", "AdGroupId", "Keyword", "State", "Status"]
    params = {"SelectionCriteria": {}, "FieldNames": field_names, "Page": {"Limit": limit, "Offset": offset}}
    res = ctx._direct_get("keywords", params, direct_client_login=direct_client_login)  # type: ignore[attr-defined]
    items = res.get("result", {}).get("Keywords", []) if isinstance(res, dict) else []
    rows: list[dict[str, Any]] = []
    for k in items:
        if not isinstance(k, dict):
            continue
        kid = _safe_int(k.get("Id"))
        if kid is None:
            continue
        rows.append(
            {
                "account_id": account_id,
                "direct_client_login": direct_client_login,
                "keyword_id": kid,
                "campaign_id": _safe_int(k.get("CampaignId")),
                "adgroup_id": _safe_int(k.get("AdGroupId")),
                "keyword": k.get("Keyword"),
                "state": k.get("State"),
                "status": k.get("Status"),
            }
        )
    return {"result": {"rows": rows, "raw_refs": [{"tool": "direct.keywords.get", "params": params}]}}


def _direct_report_rows(
    ctx: Any,
    *,
    report_type: str,
    field_names: list[str],
    args: dict[str, Any],
    report_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    date_from = str(args.get("date_from") or "").strip()
    date_to = str(args.get("date_to") or "").strip()
    if not date_from or not date_to:
        raise ValueError("date_from and date_to are required")

    direct_client_login = (str(args.get("direct_client_login")).strip() if args.get("direct_client_login") else None) or None
    selection: dict[str, Any] = {"DateFrom": date_from, "DateTo": date_to}

    campaign_ids = args.get("campaign_ids")
    if isinstance(campaign_ids, list) and campaign_ids:
        values = [str(int(x)) for x in campaign_ids if _safe_int(x) is not None]
        if values:
            selection["Filter"] = [{"Field": "CampaignId", "Operator": "IN", "Values": values}]

    params = {
        "SelectionCriteria": selection,
        "FieldNames": field_names,
        "ReportName": report_name[:255],
        "ReportType": report_type,
        "DateRangeType": "CUSTOM_DATE",
        "Format": "TSV",
        "IncludeVAT": "YES",
        "IncludeDiscount": "NO",
    }
    raw = ctx._direct_report(params, direct_client_login=direct_client_login)  # type: ignore[attr-defined]
    tsv, columns = _extract_raw_and_columns(raw if isinstance(raw, dict) else {})
    parsed, resolved_columns = _parse_delimited(tsv, delimiter="\t", columns=columns)
    refs = [{"tool": "direct.report", "params": params, "resolved_columns": resolved_columns}]
    return parsed, refs


def dataset_direct_campaign_daily(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    rows_raw, refs = _direct_report_rows(
        ctx,
        report_type="CAMPAIGN_PERFORMANCE_REPORT",
        field_names=["Date", "CampaignId", "Impressions", "Clicks", "Cost"],
        args=args,
        report_name=f"BI_direct_campaign_daily_{args.get('date_from')}_{args.get('date_to')}",
    )
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    out_rows: list[dict[str, Any]] = []
    for r in rows_raw:
        out_rows.append(
            {
                "account_id": account_id,
                "date": (r.get("Date") or "").strip(),
                "campaign_id": _safe_int(r.get("CampaignId")),
                "impressions": _safe_int(r.get("Impressions")),
                "clicks": _safe_int(r.get("Clicks")),
                "cost": _safe_float(r.get("Cost")),
            }
        )
    return {"result": {"rows": out_rows, "raw_refs": refs}}


def dataset_direct_keyword_daily(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    rows_raw, refs = _direct_report_rows(
        ctx,
        report_type="CRITERIA_PERFORMANCE_REPORT",
        field_names=["Date", "CampaignId", "AdGroupId", "KeywordId", "Impressions", "Clicks", "Cost"],
        args=args,
        report_name=f"BI_direct_keyword_daily_{args.get('date_from')}_{args.get('date_to')}",
    )
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    out_rows: list[dict[str, Any]] = []
    for r in rows_raw:
        out_rows.append(
            {
                "account_id": account_id,
                "date": (r.get("Date") or "").strip(),
                "campaign_id": _safe_int(r.get("CampaignId")),
                "adgroup_id": _safe_int(r.get("AdGroupId")),
                "keyword_id": _safe_int(r.get("KeywordId")),
                "impressions": _safe_int(r.get("Impressions")),
                "clicks": _safe_int(r.get("Clicks")),
                "cost": _safe_float(r.get("Cost")),
            }
        )
    return {"result": {"rows": out_rows, "raw_refs": refs}}


def dataset_direct_ads_daily(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    rows_raw, refs = _direct_report_rows(
        ctx,
        report_type="AD_PERFORMANCE_REPORT",
        field_names=["Date", "CampaignId", "AdGroupId", "AdId", "Impressions", "Clicks", "Cost"],
        args=args,
        report_name=f"BI_direct_ads_daily_{args.get('date_from')}_{args.get('date_to')}",
    )
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    out_rows: list[dict[str, Any]] = []
    for r in rows_raw:
        out_rows.append(
            {
                "account_id": account_id,
                "date": (r.get("Date") or "").strip(),
                "campaign_id": _safe_int(r.get("CampaignId")),
                "adgroup_id": _safe_int(r.get("AdGroupId")),
                "ad_id": _safe_int(r.get("AdId")),
                "impressions": _safe_int(r.get("Impressions")),
                "clicks": _safe_int(r.get("Clicks")),
                "cost": _safe_float(r.get("Cost")),
            }
        )
    return {"result": {"rows": out_rows, "raw_refs": refs}}


def dataset_direct_search_phrases_daily(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    rows_raw, refs = _direct_report_rows(
        ctx,
        report_type="SEARCH_QUERY_PERFORMANCE_REPORT",
        field_names=["Date", "CampaignId", "AdGroupId", "Query", "MatchedKeyword", "MatchType", "Impressions", "Clicks", "Cost"],
        args=args,
        report_name=f"BI_direct_search_phrases_daily_{args.get('date_from')}_{args.get('date_to')}",
    )
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    out_rows: list[dict[str, Any]] = []
    for r in rows_raw:
        out_rows.append(
            {
                "account_id": account_id,
                "date": (r.get("Date") or "").strip(),
                "campaign_id": _safe_int(r.get("CampaignId")),
                "adgroup_id": _safe_int(r.get("AdGroupId")),
                "query": (r.get("Query") or "").strip(),
                "matched_keyword": (r.get("MatchedKeyword") or "").strip(),
                "match_type": (r.get("MatchType") or "").strip(),
                "impressions": _safe_int(r.get("Impressions")),
                "clicks": _safe_int(r.get("Clicks")),
                "cost": _safe_float(r.get("Cost")),
            }
        )
    return {"result": {"rows": out_rows, "raw_refs": refs}}


def dataset_direct_bids_snapshot(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    limit = int(args.get("limit") or 1000)
    offset = int(args.get("offset") or 0)
    limit = max(1, min(10000, limit))
    offset = max(0, offset)
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    direct_client_login = (str(args.get("direct_client_login")).strip() if args.get("direct_client_login") else None) or None
    selection: dict[str, Any] = {}
    campaign_ids = args.get("campaign_ids")
    if isinstance(campaign_ids, list) and campaign_ids:
        ids = [int(x) for x in campaign_ids if _safe_int(x) is not None]
        if ids:
            selection["CampaignIds"] = ids
    res = ctx._direct_get(  # type: ignore[attr-defined]
        "bids",
        {"SelectionCriteria": selection, "FieldNames": ["Bid", "CampaignId", "KeywordId"], "Page": {"Limit": limit, "Offset": offset}},
        direct_client_login=direct_client_login,
    )
    bids = res.get("result", {}).get("Bids", []) if isinstance(res, dict) else []
    bids = [b for b in bids if isinstance(b, dict)]
    rows: list[dict[str, Any]] = []
    for b in bids:
        kid = _safe_int(b.get("KeywordId"))
        if kid is None:
            continue
        rows.append(
            {
                "account_id": account_id,
                "direct_client_login": direct_client_login,
                "keyword_id": kid,
                "campaign_id": _safe_int(b.get("CampaignId")),
                "bid": _safe_float(b.get("Bid")),
            }
        )
    return {"result": {"rows": rows, "raw_refs": [{"tool": "direct.bids.get", "params": {"SelectionCriteria": selection, "FieldNames": ["Bid", "CampaignId", "KeywordId"], "Page": {"Limit": limit, "Offset": offset}}}]}}


def _metrica_dim_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("id") or "").strip()
    return str(value or "").strip()


def _metrica_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, dict)]


def dataset_metrica_daily(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    counter_id = str(args.get("counter_id") or "").strip()
    date_from = str(args.get("date_from") or "").strip()
    date_to = str(args.get("date_to") or "").strip()
    if not counter_id or not date_from or not date_to:
        raise ValueError("counter_id, date_from, date_to are required")
    goal_ids = args.get("goal_ids") or []
    goal_ids_norm = [int(x) for x in goal_ids if _safe_int(x) is not None] if isinstance(goal_ids, list) else []
    metrics = ["ym:s:visits", "ym:s:users", "ym:s:bounceRate", "ym:s:avgVisitDurationSeconds"]
    for gid in goal_ids_norm:
        metrics.append(f"ym:s:goal{gid}reaches")

    raw = ctx._metrica_get_stats(  # type: ignore[attr-defined]
        {
            "ids": counter_id,
            "metrics": ",".join(metrics),
            "dimensions": "ym:s:date",
            "date1": date_from,
            "date2": date_to,
            "sort": "ym:s:date",
            "limit": 100000,
        }
    )
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    rows: list[dict[str, Any]] = []
    for row in _metrica_rows(raw):
        dims = row.get("dimensions")
        mets = row.get("metrics")
        if not isinstance(dims, list) or not isinstance(mets, list) or not dims or len(mets) < 4:
            continue
        date_value = _metrica_dim_name(dims[0])
        base = {
            "account_id": account_id,
            "counter_id": counter_id,
            "date": date_value,
            "visits": _safe_float(mets[0]),
            "users": _safe_float(mets[1]),
            "bounce_rate": _safe_float(mets[2]),
            "avg_visit_duration_seconds": _safe_float(mets[3]),
        }
        for idx, gid in enumerate(goal_ids_norm):
            if 4 + idx < len(mets):
                base[f"goal_{gid}_reaches"] = _safe_float(mets[4 + idx])
        rows.append(base)
    return {"result": {"rows": rows, "raw": raw, "raw_refs": [{"tool": "metrica.report", "params": {"ids": counter_id, "metrics": ",".join(metrics), "dimensions": "ym:s:date", "date1": date_from, "date2": date_to}}]}}


def dataset_metrica_devices_daily(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    counter_id = str(args.get("counter_id") or "").strip()
    date_from = str(args.get("date_from") or "").strip()
    date_to = str(args.get("date_to") or "").strip()
    if not counter_id or not date_from or not date_to:
        raise ValueError("counter_id, date_from, date_to are required")
    raw = ctx._metrica_get_stats(  # type: ignore[attr-defined]
        {
            "ids": counter_id,
            "metrics": "ym:s:visits",
            "dimensions": "ym:s:date,ym:s:deviceCategory",
            "date1": date_from,
            "date2": date_to,
            "sort": "ym:s:date",
            "limit": 100000,
        }
    )
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    rows: list[dict[str, Any]] = []
    for row in _metrica_rows(raw):
        dims = row.get("dimensions")
        mets = row.get("metrics")
        if not isinstance(dims, list) or len(dims) < 2 or not isinstance(mets, list) or not mets:
            continue
        rows.append(
            {
                "account_id": account_id,
                "counter_id": counter_id,
                "date": _metrica_dim_name(dims[0]),
                "device": _metrica_dim_name(dims[1]),
                "visits": _safe_float(mets[0]),
            }
        )
    return {"result": {"rows": rows, "raw": raw}}


def dataset_metrica_geo_daily(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    counter_id = str(args.get("counter_id") or "").strip()
    date_from = str(args.get("date_from") or "").strip()
    date_to = str(args.get("date_to") or "").strip()
    if not counter_id or not date_from or not date_to:
        raise ValueError("counter_id, date_from, date_to are required")
    level = (str(args.get("level") or "country")).strip().lower()
    dim = "ym:s:geoCountry" if level == "country" else "ym:s:geoCity"
    raw = ctx._metrica_get_stats(  # type: ignore[attr-defined]
        {
            "ids": counter_id,
            "metrics": "ym:s:visits",
            "dimensions": f"ym:s:date,{dim}",
            "date1": date_from,
            "date2": date_to,
            "sort": "ym:s:date",
            "limit": 100000,
        }
    )
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    rows: list[dict[str, Any]] = []
    for row in _metrica_rows(raw):
        dims = row.get("dimensions")
        mets = row.get("metrics")
        if not isinstance(dims, list) or len(dims) < 2 or not isinstance(mets, list) or not mets:
            continue
        rows.append(
            {
                "account_id": account_id,
                "counter_id": counter_id,
                "date": _metrica_dim_name(dims[0]),
                "geo": _metrica_dim_name(dims[1]),
                "geo_level": level,
                "visits": _safe_float(mets[0]),
            }
        )
    return {"result": {"rows": rows, "raw": raw}}


def dataset_metrica_goals_daily(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    counter_id = str(args.get("counter_id") or "").strip()
    date_from = str(args.get("date_from") or "").strip()
    date_to = str(args.get("date_to") or "").strip()
    if not counter_id or not date_from or not date_to:
        raise ValueError("counter_id, date_from, date_to are required")
    goal_ids = args.get("goal_ids")
    if not isinstance(goal_ids, list) or not goal_ids:
        raise ValueError("goal_ids is required")
    goal_ids_norm = [int(x) for x in goal_ids if _safe_int(x) is not None]
    if not goal_ids_norm:
        raise ValueError("goal_ids must contain integers")

    metrics = [f"ym:s:goal{gid}reaches" for gid in goal_ids_norm]
    raw = ctx._metrica_get_stats(  # type: ignore[attr-defined]
        {
            "ids": counter_id,
            "metrics": ",".join(metrics),
            "dimensions": "ym:s:date",
            "date1": date_from,
            "date2": date_to,
            "sort": "ym:s:date",
            "limit": 100000,
        }
    )
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    rows: list[dict[str, Any]] = []
    for row in _metrica_rows(raw):
        dims = row.get("dimensions")
        mets = row.get("metrics")
        if not isinstance(dims, list) or not dims or not isinstance(mets, list):
            continue
        d = _metrica_dim_name(dims[0])
        for idx, gid in enumerate(goal_ids_norm):
            if idx >= len(mets):
                continue
            rows.append(
                {
                    "account_id": account_id,
                    "counter_id": counter_id,
                    "date": d,
                    "goal_id": gid,
                    "goal_reaches": _safe_float(mets[idx]),
                }
            )
    return {"result": {"rows": rows, "raw": raw}}


def dataset_metrica_utm_campaigns_daily(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    counter_id = str(args.get("counter_id") or "").strip()
    date_from = str(args.get("date_from") or "").strip()
    date_to = str(args.get("date_to") or "").strip()
    if not counter_id or not date_from or not date_to:
        raise ValueError("counter_id, date_from, date_to are required")
    limit_per_day = int(args.get("limit_per_day") or 200)
    limit_per_day = max(1, min(5000, limit_per_day))
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None

    rows: list[dict[str, Any]] = []
    raw_refs: list[dict[str, Any]] = []
    for d1, d2 in _iter_date_chunks(date_from, date_to, chunk_days=1):
        raw = ctx._metrica_get_stats(  # type: ignore[attr-defined]
            {
                "ids": counter_id,
                "metrics": "ym:s:visits,ym:s:avgVisitDurationSeconds",
                "dimensions": "ym:s:UTMCampaign,ym:s:UTMContent",
                "date1": d1,
                "date2": d2,
                "sort": "-ym:s:visits",
                "limit": limit_per_day,
            }
        )
        raw_refs.append({"tool": "metrica.report", "date": d1, "limit": limit_per_day})
        for row in _metrica_rows(raw):
            dims = row.get("dimensions")
            mets = row.get("metrics")
            if not isinstance(dims, list) or len(dims) < 2 or not isinstance(mets, list) or len(mets) < 2:
                continue
            rows.append(
                {
                    "account_id": account_id,
                    "counter_id": counter_id,
                    "date": d1,
                    "utm_campaign": _metrica_dim_name(dims[0]),
                    "utm_content": _metrica_dim_name(dims[1]),
                    "visits": _safe_float(mets[0]),
                    "avg_visit_duration_seconds": _safe_float(mets[1]),
                }
            )
    return {"result": {"rows": rows, "raw_refs": raw_refs}}


def dataset_metrica_landing_pages_daily(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    counter_id = str(args.get("counter_id") or "").strip()
    date_from = str(args.get("date_from") or "").strip()
    date_to = str(args.get("date_to") or "").strip()
    if not counter_id or not date_from or not date_to:
        raise ValueError("counter_id, date_from, date_to are required")
    limit_per_day = int(args.get("limit_per_day") or 200)
    limit_per_day = max(1, min(5000, limit_per_day))
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None

    rows: list[dict[str, Any]] = []
    raw_refs: list[dict[str, Any]] = []
    for d1, d2 in _iter_date_chunks(date_from, date_to, chunk_days=1):
        raw = ctx._metrica_get_stats(  # type: ignore[attr-defined]
            {
                "ids": counter_id,
                "metrics": "ym:s:visits,ym:s:avgVisitDurationSeconds",
                "dimensions": "ym:s:startURL",
                "date1": d1,
                "date2": d2,
                "sort": "-ym:s:visits",
                "limit": limit_per_day,
            }
        )
        raw_refs.append({"tool": "metrica.report", "date": d1, "limit": limit_per_day})
        for row in _metrica_rows(raw):
            dims = row.get("dimensions")
            mets = row.get("metrics")
            if not isinstance(dims, list) or not dims or not isinstance(mets, list) or len(mets) < 2:
                continue
            rows.append(
                {
                    "account_id": account_id,
                    "counter_id": counter_id,
                    "date": d1,
                    "landing_url": _metrica_dim_name(dims[0]),
                    "visits": _safe_float(mets[0]),
                    "avg_visit_duration_seconds": _safe_float(mets[1]),
                }
            )
    return {"result": {"rows": rows, "raw_refs": raw_refs}}


def dataset_wordstat_top_requests(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    phrase = str(args.get("phrase") or "").strip()
    phrases = args.get("phrases")
    seeds: list[str] = []
    if phrase:
        seeds = [phrase]
    elif isinstance(phrases, list):
        seeds = [str(x).strip() for x in phrases if str(x).strip()]
    if not seeds:
        raise ValueError("phrase or phrases is required")
    num_phrases = int(args.get("num_phrases") or 50)
    num_phrases = max(1, min(2000, num_phrases))
    regions = args.get("regions")
    devices = args.get("devices")

    rows: list[dict[str, Any]] = []
    raw_refs: list[dict[str, Any]] = []
    for seed in seeds[:128]:
        payload: dict[str, Any] = {"phrase": seed, "numPhrases": num_phrases}
        if isinstance(regions, list) and regions:
            payload["regions"] = regions
        if isinstance(devices, list) and devices:
            payload["devices"] = devices
        raw = ctx._wordstat_post("topRequests", payload)  # type: ignore[attr-defined]
        raw_refs.append({"tool": "wordstat.top_requests", "payload": payload})
        items = raw.get("topRequests") if isinstance(raw, dict) else None
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            p = str(item.get("phrase") or "").strip()
            c = _safe_float(item.get("count"))
            if not p:
                continue
            rows.append({"seed_phrase": seed, "phrase": p, "count": c})
    return {"result": {"rows": rows, "raw_refs": raw_refs}}


def dataset_join_direct_vs_metrica_utm_daily(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    account_id = (str(args.get("account_id")).strip() if args.get("account_id") is not None else None) or None
    direct_client_login = (str(args.get("direct_client_login")).strip() if args.get("direct_client_login") else None) or None
    counter_id = str(args.get("counter_id") or "").strip()
    date_from = str(args.get("date_from") or "").strip()
    date_to = str(args.get("date_to") or "").strip()
    campaign_id = _safe_int(args.get("campaign_id"))
    if campaign_id is None or not counter_id or not date_from or not date_to:
        raise ValueError("campaign_id, counter_id, date_from, date_to are required")

    utm_campaign = str(args.get("utm_campaign") or "").strip() or None
    if utm_campaign is None:
        campaigns = ctx._direct_get(  # type: ignore[attr-defined]
            "campaigns",
            {"SelectionCriteria": {"Ids": [campaign_id]}, "FieldNames": ["Id", "Name"], "Page": {"Limit": 10, "Offset": 0}},
            direct_client_login=direct_client_login,
        )
        items = campaigns.get("result", {}).get("Campaigns", []) if isinstance(campaigns, dict) else []
        if isinstance(items, list) and items and isinstance(items[0], dict):
            utm_campaign = str(items[0].get("Name") or "").strip() or None
    if utm_campaign is None:
        raise ValueError("utm_campaign could not be resolved; pass utm_campaign explicitly")

    direct_report = ctx._direct_report(  # type: ignore[attr-defined]
        {
            "SelectionCriteria": {"DateFrom": date_from, "DateTo": date_to, "Filter": [{"Field": "CampaignId", "Operator": "IN", "Values": [str(campaign_id)]}]},
            "FieldNames": ["Date", "CampaignId", "Impressions", "Clicks", "Cost"],
            "ReportName": f"BI_join_direct_{campaign_id}_{date_from}_{date_to}",
            "ReportType": "CAMPAIGN_PERFORMANCE_REPORT",
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "YES",
            "IncludeDiscount": "NO",
        },
        direct_client_login=direct_client_login,
    )
    raw_direct, cols = _extract_raw_and_columns(direct_report if isinstance(direct_report, dict) else {})
    direct_rows, _ = _parse_delimited(raw_direct, delimiter="\t", columns=cols)
    direct_by_date: dict[str, dict[str, float]] = {}
    for r in direct_rows:
        d = (r.get("Date") or "").strip()
        if not d:
            continue
        direct_by_date[d] = {
            "impressions": float(_safe_float(r.get("Impressions")) or 0.0),
            "clicks": float(_safe_float(r.get("Clicks")) or 0.0),
            "cost": float(_safe_float(r.get("Cost")) or 0.0),
        }

    metrica = ctx._metrica_get_stats(  # type: ignore[attr-defined]
        {
            "ids": counter_id,
            "metrics": "ym:s:visits",
            "dimensions": "ym:s:date",
            "date1": date_from,
            "date2": date_to,
            "filters": f"ym:s:UTMCampaign=={_metrica_filter_quote(utm_campaign)}",
            "sort": "ym:s:date",
            "limit": 100000,
        }
    )
    visits_by_date: dict[str, float] = {}
    for row in _metrica_rows(metrica):
        dims = row.get("dimensions")
        mets = row.get("metrics")
        if not isinstance(dims, list) or not dims or not isinstance(mets, list) or not mets:
            continue
        d = _metrica_dim_name(dims[0])
        visits_by_date[d] = visits_by_date.get(d, 0.0) + float(_safe_float(mets[0]) or 0.0)

    all_dates = sorted(set(direct_by_date.keys()) | set(visits_by_date.keys()))
    rows: list[dict[str, Any]] = []
    for d in all_dates:
        dr = direct_by_date.get(d) or {"impressions": 0.0, "clicks": 0.0, "cost": 0.0}
        rows.append(
            {
                "account_id": account_id,
                "utm_campaign": utm_campaign,
                "campaign_id": campaign_id,
                "counter_id": counter_id,
                "date": d,
                "impressions": dr["impressions"],
                "clicks": dr["clicks"],
                "cost": dr["cost"],
                "visits": float(visits_by_date.get(d) or 0.0),
            }
        )
    return {"result": {"rows": rows, "raw_refs": [{"tool": "direct.report", "report": "CAMPAIGN_PERFORMANCE_REPORT"}, {"tool": "metrica.report", "dimensions": "ym:s:date"}]}}


_DATASET_HANDLERS: dict[str, Any] = {
    "dashboard.dataset.audience_segments": dataset_audience_segments,
    "dashboard.dataset.audience_overlap": dataset_audience_overlap,
    "dashboard.dataset.audience_segment_perf_daily": dataset_audience_segment_perf_daily,
    "dashboard.dataset.direct_campaigns_dim": dataset_direct_campaigns_dim,
    "dashboard.dataset.direct_adgroups_dim": dataset_direct_adgroups_dim,
    "dashboard.dataset.direct_keywords_dim": dataset_direct_keywords_dim,
    "dashboard.dataset.direct_campaign_daily": dataset_direct_campaign_daily,
    "dashboard.dataset.direct_keyword_daily": dataset_direct_keyword_daily,
    "dashboard.dataset.direct_ads_daily": dataset_direct_ads_daily,
    "dashboard.dataset.direct_search_phrases_daily": dataset_direct_search_phrases_daily,
    "dashboard.dataset.direct_bids_snapshot": dataset_direct_bids_snapshot,
    "dashboard.dataset.metrica_daily": dataset_metrica_daily,
    "dashboard.dataset.metrica_devices_daily": dataset_metrica_devices_daily,
    "dashboard.dataset.metrica_geo_daily": dataset_metrica_geo_daily,
    "dashboard.dataset.metrica_goals_daily": dataset_metrica_goals_daily,
    "dashboard.dataset.metrica_utm_campaigns_daily": dataset_metrica_utm_campaigns_daily,
    "dashboard.dataset.metrica_landing_pages_daily": dataset_metrica_landing_pages_daily,
    "dashboard.dataset.wordstat_top_requests": dataset_wordstat_top_requests,
    "dashboard.dataset.join_direct_vs_metrica_utm_daily": dataset_join_direct_vs_metrica_utm_daily,
}


def dashboard_dataset_handle(ctx: Any, name: str, args: dict[str, Any]) -> dict[str, Any]:
    handler = _DATASET_HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"Unknown dataset: {name}")
    return handler(ctx, args)


def dashboard_sync_start(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    datasets = args.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        datasets = [
            "dashboard.dataset.direct_campaigns_dim",
            "dashboard.dataset.direct_adgroups_dim",
            "dashboard.dataset.direct_keywords_dim",
            "dashboard.dataset.direct_campaign_daily",
            "dashboard.dataset.metrica_daily",
            "dashboard.dataset.audience_segments",
        ]
    datasets = [str(x).strip() for x in datasets if str(x).strip()]

    page_size = int(args.get("page_size") or 500)
    page_size = max(1, min(5000, page_size))
    chunk_days = int(args.get("chunk_days") or 7)
    chunk_days = max(1, min(31, chunk_days))

    date_from = str(args.get("date_from") or "").strip() or None
    date_to = str(args.get("date_to") or "").strip() or None
    goal_ids = args.get("goal_ids") if isinstance(args.get("goal_ids"), list) else None
    segment_ids = args.get("segment_ids") if isinstance(args.get("segment_ids"), list) else None

    # Determine which accounts to sync.
    account_ids = args.get("account_ids")
    if isinstance(account_ids, list):
        resolved_accounts = [str(x).strip() for x in account_ids if str(x).strip()]
    else:
        resolved_accounts = []
    if not resolved_accounts:
        try:
            resolved_accounts = sorted([str(k) for k in (getattr(getattr(ctx, "config", None), "accounts", None) or {}).keys()])
        except Exception:
            resolved_accounts = []
    if not resolved_accounts:
        resolved_accounts = [None]  # single default account context

    base_direct_login = str(args.get("direct_client_login") or "").strip() or None
    base_counter_id = str(args.get("counter_id") or "").strip() or None

    warnings: list[str] = []
    jobs: list[dict[str, Any]] = []

    for ds in datasets:
        # Audience datasets are global (not account-specific) by default.
        if ds in {"dashboard.dataset.audience_segments", "dashboard.dataset.audience_overlap", "dashboard.dataset.audience_segment_perf_daily"}:
            if ds == "dashboard.dataset.audience_segments":
                jobs.append({"dataset": ds, "account_id": None, "offset": 0, "page_size": page_size, "params": {}})
            elif ds == "dashboard.dataset.audience_overlap":
                if not segment_ids:
                    warnings.append("dataset audience_overlap skipped: provide segment_ids")
                    continue
                jobs.append({"dataset": ds, "account_id": None, "offset": 0, "page_size": page_size, "params": {"segment_ids": segment_ids, "mode": args.get("mode"), "limit": args.get("limit")}})
            elif ds == "dashboard.dataset.audience_segment_perf_daily":
                if not segment_ids:
                    warnings.append("dataset audience_segment_perf_daily skipped: provide segment_ids")
                    continue
                if not date_from or not date_to:
                    warnings.append("dataset audience_segment_perf_daily skipped: provide date_from/date_to")
                    continue
                for sid in [str(x).strip() for x in segment_ids if str(x).strip()]:
                    jobs.append({"dataset": ds, "account_id": None, "offset": 0, "page_size": page_size, "params": {"segment_id": sid, "date_from": date_from, "date_to": date_to}})
            continue

        # Account-specific datasets.
        for aid in resolved_accounts:
            account_id = str(aid).strip() if isinstance(aid, str) else None

            needs_counter = ds.startswith("dashboard.dataset.metrica_") or ds.startswith("dashboard.dataset.join_")
            try:
                resolved_login, resolved_counter = _resolve_account_overrides_local(
                    ctx,
                    account_id=account_id,
                    direct_client_login=base_direct_login,
                    counter_id=base_counter_id,
                    needs_counter=needs_counter,
                )
            except Exception as exc:
                warnings.append(
                    f"dataset {ds} skipped for account_id={account_id or '<default>'}: {exc}"
                )
                continue
            if needs_counter and not resolved_counter:
                warnings.append(
                    f"dataset {ds} skipped for account_id={account_id or '<default>'}: counter_id is required"
                )
                continue
            base_params: dict[str, Any] = {
                "account_id": account_id,
                "direct_client_login": resolved_login,
                "counter_id": resolved_counter,
            }

            if ds.endswith("_dim") or ds.endswith("_snapshot"):
                jobs.append({"dataset": ds, "account_id": account_id, "offset": 0, "page_size": page_size, "params": base_params})
                continue

            if ds.endswith("_daily") or ds.endswith("_perf_daily"):
                if not date_from or not date_to:
                    warnings.append(f"dataset {ds} skipped for account_id={account_id or '<default>'}: provide date_from/date_to")
                    continue

                if ds == "dashboard.dataset.metrica_goals_daily":
                    if not goal_ids:
                        warnings.append(f"dataset {ds} skipped for account_id={account_id or '<default>'}: provide goal_ids")
                        continue
                    base_params = dict(base_params)
                    base_params["goal_ids"] = goal_ids

                if ds in {"dashboard.dataset.metrica_utm_campaigns_daily", "dashboard.dataset.metrica_landing_pages_daily"}:
                    base_params = dict(base_params)
                    base_params["limit_per_day"] = int(args.get("limit_per_day") or 200)
                    jobs.extend(
                        [
                            {"dataset": ds, "account_id": account_id, "offset": 0, "page_size": page_size, "params": {**base_params, "date_from": d1, "date_to": d2}}
                            for d1, d2 in _iter_date_chunks(date_from, date_to, chunk_days=1)
                        ]
                    )
                    continue

                # For Direct heavy datasets, default to 1-day chunks for stability.
                ds_chunk_days = 1 if ds in {"dashboard.dataset.direct_keyword_daily", "dashboard.dataset.direct_ads_daily", "dashboard.dataset.direct_search_phrases_daily"} else chunk_days
                jobs.extend(
                    [
                        {"dataset": ds, "account_id": account_id, "offset": 0, "page_size": page_size, "params": {**base_params, "date_from": d1, "date_to": d2}}
                        for d1, d2 in _iter_date_chunks(date_from, date_to, chunk_days=ds_chunk_days)
                    ]
                )
                continue

            warnings.append(f"Unknown dataset ignored: {ds}")

    cursor = _b64encode({"v": 2, "job_index": 0, "jobs": jobs})
    return {"result": {"cursor": cursor, "jobs_count": len(jobs), "warnings": warnings}}


def dashboard_sync_next(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    cursor_text = str(args.get("cursor") or "").strip()
    if not cursor_text:
        raise ValueError("cursor is required")
    state = _b64decode(cursor_text)
    if int(state.get("v") or 1) not in {1, 2}:
        raise ValueError("Unsupported cursor version")
    jobs = state.get("jobs")
    if not isinstance(jobs, list):
        raise ValueError("cursor.jobs must be a list")
    job_index = int(state.get("job_index") or 0)
    if job_index >= len(jobs):
        return {"result": {"done": True, "dataset": None, "ndjson": "", "cursor": None}}
    job = jobs[job_index]
    if not isinstance(job, dict) or not job.get("dataset"):
        raise ValueError("Invalid cursor job")
    dataset = str(job["dataset"])
    account_id = job.get("account_id")
    offset = int(job.get("offset") or 0)
    page_size = int(job.get("page_size") or 500)
    params = job.get("params") or {}
    if not isinstance(params, dict):
        params = {}

    out = dashboard_dataset_handle(ctx, dataset, {"limit": page_size, "offset": offset, **params})
    rows = (out.get("result") or {}).get("rows") if isinstance(out, dict) else []
    if not isinstance(rows, list):
        rows = []

    is_paged = dataset in {
        "dashboard.dataset.audience_segments",
        "dashboard.dataset.direct_campaigns_dim",
        "dashboard.dataset.direct_adgroups_dim",
        "dashboard.dataset.direct_keywords_dim",
        "dashboard.dataset.direct_bids_snapshot",
    }
    if is_paged:
        next_offset = offset + len(rows)
        if len(rows) < page_size:
            job_index += 1
            offset = 0
        else:
            offset = next_offset
    else:
        job_index += 1
        offset = 0

    ndjson_lines: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        ndjson_lines.append(
            json.dumps({"dataset": dataset, "account_id": account_id, "row": row}, ensure_ascii=True, separators=(",", ":"))
        )
    ndjson = "\n".join(ndjson_lines) + ("\n" if ndjson_lines else "")

    # Update state.
    if job_index < len(jobs):
        jobs[job_index]["offset"] = offset
    state["job_index"] = job_index
    state["jobs"] = jobs
    next_cursor = None if job_index >= len(jobs) else _b64encode(state)
    return {"result": {"done": job_index >= len(jobs), "dataset": dataset, "ndjson": ndjson, "cursor": next_cursor}}
