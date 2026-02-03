"""Human-friendly (HF) tools for Yandex Audience."""

from __future__ import annotations

import datetime as dt
from typing import Any

from .hf_common import HFError, ensure_hf_enabled, ensure_hf_write_enabled, hf_payload, should_apply


def _extract_list(payload: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    # Common nesting patterns
    result = payload.get("result")
    if isinstance(result, dict):
        for key in keys:
            value = result.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def _parse_iso_date(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    # Support "Z" suffix.
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(text)
    except Exception:
        return None


def _now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _segment_size(seg: dict[str, Any]) -> int | None:
    for k in ("size", "audience_size", "users", "count"):
        v = seg.get(k)
        if v is None:
            continue
        try:
            return int(v)
        except Exception:
            continue
    stats = seg.get("stats")
    if isinstance(stats, dict):
        for k in ("size", "audience_size", "users", "count"):
            v = stats.get(k)
            if v is None:
                continue
            try:
                return int(v)
            except Exception:
                continue
    return None


def _segment_updated_at(seg: dict[str, Any]) -> str | None:
    for k in ("updated_at", "updated", "modified", "modified_at", "created_at"):
        v = seg.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _tsv_rows(raw: str, *, columns: list[str] | None = None) -> list[dict[str, str]]:
    raw = raw or ""
    delim = "\t" if "\t" in raw else (";" if ";" in raw else ",")
    lines = [l for l in raw.splitlines() if l.strip()]
    if not lines:
        return []
    header = columns[:] if columns else []
    if not header:
        header = [c.strip() for c in lines[0].split(delim)]
        lines = lines[1:]
    out: list[dict[str, str]] = []
    for line in lines:
        if line.lower().startswith(("total", "итого", "всего")):
            continue
        parts = line.split(delim)
        if len(parts) != len(header):
            continue
        out.append({header[i]: parts[i] for i in range(len(header))})
    return out


def _build_direct_segment_proxy_series(
    ctx: Any,
    *,
    segment_id: str,
    date_from: str,
    date_to: str,
    direct_client_login: str | None,
    max_targets: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    """Best-effort: infer which campaigns use a segment by looking for retargeting lists with ExternalId=segment_id.

    Returns: (series_rows, coverage, raw_refs)
    """
    raw_refs: list[dict[str, Any]] = []
    seg_num = None
    try:
        seg_num = int(str(segment_id).strip())
    except Exception:
        seg_num = None

    retargeting_lists: list[dict[str, Any]] = []
    try:
        params = {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name", "Rules", "State"],
            "Page": {"Limit": 1000, "Offset": 0},
        }
        raw_refs.append({"tool": "direct.raw_call", "resource": "retargetinglists", "method": "get", "params": params})
        res = ctx._direct_get("retargetinglists", params, direct_client_login=direct_client_login)  # type: ignore[attr-defined]
        retargeting_lists = _extract_list(res.get("result", {}) if isinstance(res, dict) else {}, "RetargetingLists")
    except Exception:
        retargeting_lists = []

    matching_lists: list[dict[str, Any]] = []
    if seg_num is not None:
        for lst in retargeting_lists:
            rules = lst.get("Rules")
            if not isinstance(rules, list):
                continue
            found = False
            for rule in rules:
                if not isinstance(rule, dict):
                    continue
                args = rule.get("Arguments")
                if not isinstance(args, list):
                    continue
                for arg in args:
                    if not isinstance(arg, dict):
                        continue
                    ext = arg.get("ExternalId")
                    try:
                        if ext is not None and int(ext) == seg_num:
                            found = True
                            break
                    except Exception:
                        continue
                if found:
                    break
            if found:
                matching_lists.append(lst)

    list_ids = [int(x["Id"]) for x in matching_lists if isinstance(x, dict) and x.get("Id") is not None]
    list_ids = list(dict.fromkeys(list_ids))[: max_targets]

    audience_targets: list[dict[str, Any]] = []
    if list_ids:
        try:
            params = {
                "SelectionCriteria": {"RetargetingListIds": list_ids},
                "FieldNames": ["Id", "AdGroupId", "RetargetingListId", "State", "Status"],
                "Page": {"Limit": 1000, "Offset": 0},
            }
            raw_refs.append(
                {"tool": "direct.raw_call", "resource": "audiencetargets", "method": "get", "params": params}
            )
            res = ctx._direct_get("audiencetargets", params, direct_client_login=direct_client_login)  # type: ignore[attr-defined]
            audience_targets = _extract_list(res.get("result", {}) if isinstance(res, dict) else {}, "AudienceTargets")
        except Exception:
            audience_targets = []

    adgroup_ids = [int(x["AdGroupId"]) for x in audience_targets if isinstance(x, dict) and x.get("AdGroupId") is not None]
    adgroup_ids = list(dict.fromkeys(adgroup_ids))[: max_targets]

    campaign_ids: list[int] = []
    if adgroup_ids:
        try:
            params = {
                "SelectionCriteria": {"Ids": adgroup_ids},
                "FieldNames": ["Id", "CampaignId"],
                "Page": {"Limit": 1000, "Offset": 0},
            }
            raw_refs.append({"tool": "direct.raw_call", "resource": "adgroups", "method": "get", "params": params})
            res = ctx._direct_get("adgroups", params, direct_client_login=direct_client_login)  # type: ignore[attr-defined]
            groups = _extract_list(res.get("result", {}) if isinstance(res, dict) else {}, "AdGroups")
            campaign_ids = [
                int(g["CampaignId"]) for g in groups if isinstance(g, dict) and g.get("CampaignId") is not None
            ]
        except Exception:
            campaign_ids = []
    campaign_ids = list(dict.fromkeys(campaign_ids))[: max_targets]

    series: list[dict[str, Any]] = []
    if campaign_ids:
        report_params = {
            "ReportType": "CUSTOM_REPORT",
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "YES",
            "IncludeDiscount": "NO",
            "SelectionCriteria": {"DateFrom": date_from, "DateTo": date_to, "CampaignIds": campaign_ids},
            "FieldNames": ["Date", "Impressions", "Clicks", "Cost"],
        }
        raw_refs.append({"tool": "direct.report", "params": report_params})
        rep = ctx._direct_report(report_params, direct_client_login=direct_client_login)  # type: ignore[attr-defined]
        raw = rep.get("raw", "") if isinstance(rep, dict) else ""
        cols = rep.get("columns") if isinstance(rep, dict) else None
        rows = _tsv_rows(str(raw), columns=cols if isinstance(cols, list) else None)
        by_date: dict[str, dict[str, float]] = {}
        for row in rows:
            day = (row.get("Date") or "").strip()
            if not day:
                continue
            try:
                imp = float((row.get("Impressions") or "0").replace(",", "."))
            except Exception:
                imp = 0.0
            try:
                clk = float((row.get("Clicks") or "0").replace(",", "."))
            except Exception:
                clk = 0.0
            try:
                cost = float((row.get("Cost") or "0").replace(",", "."))
            except Exception:
                cost = 0.0
            by_date.setdefault(day, {"impressions": 0.0, "clicks": 0.0, "cost": 0.0})
            by_date[day]["impressions"] += imp
            by_date[day]["clicks"] += clk
            by_date[day]["cost"] += cost
        for day in sorted(by_date.keys()):
            series.append(
                {
                    "date": day,
                    "impressions": by_date[day]["impressions"],
                    "clicks": by_date[day]["clicks"],
                    "cost": by_date[day]["cost"],
                }
            )

    coverage = {
        "strategy": "direct_proxy_via_retargetinglists",
        "segment_id": segment_id,
        "retargeting_list_ids": list_ids,
        "audience_target_adgroup_ids": adgroup_ids,
        "campaign_ids": campaign_ids,
        "note": "Direct metrics are computed for campaigns whose adgroups have AudienceTargets referencing a retargeting list that includes the segment ExternalId.",
    }
    return series, coverage, raw_refs


def handle(tool: str, ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    ensure_hf_enabled(ctx.config)

    if tool == "audience.hf.find_segment":
        limit = int(args.get("limit") or 20)
        limit = max(1, min(200, limit))
        params: dict[str, Any] = {"limit": max(limit, 50), "offset": 0}
        if args.get("types") is not None:
            params["types"] = args.get("types")
        if args.get("statuses") is not None:
            params["statuses"] = args.get("statuses")
        res = ctx._audience_call("GET", "/segments", params=params)  # type: ignore[attr-defined]
        segments = _extract_list(res, "segments", "items", "Segments")
        name_contains = (args.get("name_contains") or "").strip()
        if name_contains:
            segments = [
                s
                for s in segments
                if isinstance(s.get("name"), str)
                and name_contains.lower() in s["name"].lower()
            ]
        out: list[dict[str, Any]] = []
        for s in segments[:limit]:
            out.append(
                {
                    "id": str(s.get("id") or s.get("segment_id") or ""),
                    "name": s.get("name"),
                    "type": s.get("type"),
                    "status": s.get("status"),
                    "updated_at": _segment_updated_at(s),
                    "size": _segment_size(s),
                }
            )
        result: dict[str, Any] = {"segments": out}
        if bool(args.get("include_raw")):
            result["raw"] = res
        return hf_payload(tool=tool, status="ok", result=result)

    if tool == "audience.hf.get_segment_summary":
        seg_id = str(args.get("segment_id") or "").strip()
        if not seg_id:
            raise HFError("segment_id is required")
        include_raw = args.get("include_raw")
        if include_raw is None:
            include_raw = True
        raw = ctx._audience_call("GET", f"/segments/{seg_id}")  # type: ignore[attr-defined]
        seg = raw.get("segment") if isinstance(raw.get("segment"), dict) else raw
        if not isinstance(seg, dict):
            seg = {}
        summary = {
            "id": str(seg.get("id") or seg_id),
            "name": seg.get("name"),
            "type": seg.get("type"),
            "status": seg.get("status"),
            "size": _segment_size(seg),
            "updated_at": _segment_updated_at(seg),
            "source": seg.get("source") or seg.get("source_type"),
            "notes": seg.get("description") or seg.get("notes"),
        }
        result: dict[str, Any] = {"summary": summary, "raw_refs": [{"tool": "audience.segments.get", "segment_id": seg_id}]}
        if include_raw:
            result["raw"] = raw
        return hf_payload(tool=tool, status="ok", result=result)

    if tool == "audience.hf.segment_health":
        seg_id = str(args.get("segment_id") or "").strip()
        if not seg_id:
            raise HFError("segment_id is required")
        min_size = int(args.get("min_size") or 1000)
        max_age_days = int(args.get("max_age_days") or 30)
        raw = ctx._audience_call("GET", f"/segments/{seg_id}")  # type: ignore[attr-defined]
        seg = raw.get("segment") if isinstance(raw.get("segment"), dict) else raw
        if not isinstance(seg, dict):
            seg = {}
        size = _segment_size(seg)
        updated_at = _segment_updated_at(seg)
        updated_dt = _parse_iso_date(updated_at) if updated_at else None

        hints: list[dict[str, Any]] = []
        status = "ok"
        if seg.get("status") and str(seg.get("status")).lower() not in {"ready", "active", "available", "ok"}:
            status = "warning"
            hints.append({"code": "status", "message": f"Segment status is {seg.get('status')}", "severity": "warning"})
        if size is not None and size < min_size:
            status = "warning"
            hints.append(
                {"code": "size", "message": f"Segment size {size} < min_size {min_size}", "severity": "warning"}
            )
        if updated_dt is not None:
            age_days = int((_now_utc() - updated_dt).total_seconds() // 86400)
            if age_days > max_age_days:
                status = "warning"
                hints.append(
                    {
                        "code": "stale",
                        "message": f"Segment updated {age_days} days ago (> {max_age_days})",
                        "severity": "warning",
                    }
                )
        if not hints and (size is None or updated_at is None):
            hints.append({"code": "unknown", "message": "Some health signals are unavailable (size/updated_at).", "severity": "info"})

        evidence = {"size": size, "updated_at": updated_at, "status": seg.get("status")}
        return hf_payload(
            tool=tool,
            status=status,
            result={"hints": hints, "evidence": evidence, "raw_refs": [{"tool": "audience.segments.get", "segment_id": seg_id}]},
        )

    if tool == "audience.hf.overlap_matrix":
        seg_ids = args.get("segment_ids")
        if not isinstance(seg_ids, list) or not seg_ids:
            raise HFError("segment_ids is required")
        top_k = int(args.get("top_k") or 50)
        top_k = max(1, min(200, top_k))
        raw = ctx._audience_call("POST", "/segments/overlap", payload={"segment_ids": [str(x) for x in seg_ids], "mode": "matrix", "limit": top_k})  # type: ignore[attr-defined]
        pairs = _extract_list(raw, "pairs", "matrix", "items")
        matrix: list[dict[str, Any]] = []
        for p in pairs[:top_k]:
            a = p.get("a") or p.get("segment_a") or p.get("id_a")
            b = p.get("b") or p.get("segment_b") or p.get("id_b")
            if a is None or b is None:
                continue
            matrix.append(
                {
                    "a": str(a),
                    "b": str(b),
                    "overlap_share": p.get("overlap_share") or p.get("share"),
                    "overlap_abs": p.get("overlap_abs") or p.get("count"),
                }
            )
        return hf_payload(
            tool=tool,
            status="ok",
            result={
                "matrix": matrix,
                "top_pairs": matrix[:top_k],
                "raw_refs": [{"tool": "audience.segments.overlap", "segment_ids": seg_ids, "mode": "matrix"}],
            },
        )

    if tool == "audience.hf.segment_perf":
        segment_id = str(args.get("segment_id") or "").strip()
        if not segment_id:
            raise HFError("segment_id is required")
        date_from = str(args.get("date_from") or "").strip()
        date_to = str(args.get("date_to") or "").strip()
        if not date_from or not date_to:
            raise HFError("date_from and date_to are required (YYYY-MM-DD)")
        grain = str(args.get("grain") or "day").strip().lower()
        if grain not in {"day", "week", "month"}:
            raise HFError("grain must be day|week|month")
        include_raw_refs = args.get("include_raw_refs")
        if include_raw_refs is None:
            include_raw_refs = True

        direct_login = args.get("direct_client_login")
        max_targets = int(args.get("max_targets") or 200) if args.get("max_targets") is not None else 200
        max_targets = max(1, min(500, max_targets))

        series, coverage, raw_refs = _build_direct_segment_proxy_series(
            ctx,
            segment_id=segment_id,
            date_from=date_from,
            date_to=date_to,
            direct_client_login=str(direct_login) if direct_login else None,
            max_targets=max_targets,
        )

        # Note: Metrica segment-level filters are not available; we keep it explicit.
        meta = {"coverage": coverage}
        result: dict[str, Any] = {"series": series, "meta": meta}
        if include_raw_refs:
            result["raw_refs"] = raw_refs
        status = "ok" if series else "partial"
        if not series:
            meta["coverage"]["note"] = (meta["coverage"].get("note") or "") + " No Direct targets found; series is empty."
        return hf_payload(tool=tool, status=status, result=result)

    if tool == "audience.hf.catalog":
        limit = int(args.get("limit") or 50)
        limit = max(1, min(500, limit))
        offset = int(args.get("offset") or 0)
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        res = ctx._audience_call("GET", "/segments", params=params)  # type: ignore[attr-defined]
        segments = _extract_list(res, "segments", "items", "Segments")
        include_health = bool(args.get("include_health") or False)
        out: list[dict[str, Any]] = []
        for s in segments[:limit]:
            item = {
                "id": str(s.get("id") or s.get("segment_id") or ""),
                "name": s.get("name"),
                "type": s.get("type"),
                "status": s.get("status"),
                "size": _segment_size(s),
                "updated_at": _segment_updated_at(s),
            }
            if include_health:
                # Lightweight health from the list payload (no extra per-segment API calls).
                hints: list[str] = []
                size = item.get("size")
                if isinstance(size, int) and size < 1000:
                    hints.append("small_size")
                if str(item.get("status") or "").lower() not in {"ready", "active", "available", "ok"}:
                    hints.append("status_not_ready")
                item["health"] = {"status": "ok" if not hints else "warning", "hints": hints}
            out.append(item)
        return hf_payload(
            tool=tool,
            status="ok",
            result={"segments": out, "raw_refs": [{"tool": "audience.segments.list", "limit": limit, "offset": offset}]},
        )

    if tool == "audience.hf.activation_plan":
        # Preview-only.
        if should_apply(args):
            raise HFError("activation_plan is preview-only; use audience.hf.apply_activation_plan with apply=true.")
        segment_id = str(args.get("segment_id") or "").strip()
        if not segment_id:
            raise HFError("segment_id is required")
        direct_login = args.get("direct_client_login")
        targets = args.get("targets")
        if not isinstance(targets, list) or not targets:
            raise HFError("targets is required")

        # Default: one retargeting list + one AudienceTarget per adgroup.
        ret_name = f"audience:{segment_id}"
        try:
            seg_num = int(segment_id)
        except Exception:
            seg_num = None

        ret_payload: dict[str, Any] = {
            "RetargetingLists": [
                {
                    "Name": ret_name,
                    "Description": f"Auto-created for Audience segment {segment_id} via MCP.",
                    "Rules": [
                        {
                            "Arguments": [{"ExternalId": seg_num if seg_num is not None else segment_id}],
                            "Operator": "ALL",
                        }
                    ],
                }
            ]
        }
        calls: list[dict[str, Any]] = [
            {"tool": "direct.raw_call", "resource": "retargetinglists", "method": "add", "params": ret_payload}
        ]
        for t in targets:
            if not isinstance(t, dict):
                continue
            t_type = str(t.get("type") or "").strip().lower()
            t_id = t.get("id")
            if t_type not in {"adgroup", "campaign"} or t_id is None:
                continue
            if t_type == "campaign":
                calls.append(
                    {
                        "note": "campaign targets require expanding to adgroups; apply tool will resolve adgroups via direct.adgroups.get",
                        "campaign_id": int(t_id),
                    }
                )
                continue
            calls.append(
                {
                    "tool": "direct.raw_call",
                    "resource": "audiencetargets",
                    "method": "add",
                    "params": {
                        "AudienceTargets": [
                            {"AdGroupId": int(t_id), "RetargetingListId": "<created_retargeting_list_id>"}
                        ]
                    },
                }
            )

        return hf_payload(
            tool=tool,
            status="ok",
            preview={"calls": calls, "warnings": ["This is a preview. To execute, use audience.hf.apply_activation_plan with apply=true."]},
            result={"segment_id": segment_id, "direct_client_login": direct_login},
        )

    if tool == "audience.hf.apply_activation_plan":
        ensure_hf_write_enabled(ctx.config)
        if not should_apply(args):
            raise HFError("apply_activation_plan requires apply=true")
        segment_id = str(args.get("segment_id") or "").strip()
        if not segment_id:
            raise HFError("segment_id is required")
        direct_login = args.get("direct_client_login")
        targets = args.get("targets")
        if not isinstance(targets, list) or not targets:
            raise HFError("targets is required")

        # 1) Create a retargeting list for the segment.
        ret_name = f"audience:{segment_id}"
        try:
            seg_num = int(segment_id)
        except Exception:
            seg_num = None
        ret_payload: dict[str, Any] = {
            "RetargetingLists": [
                {
                    "Name": ret_name,
                    "Description": f"Auto-created for Audience segment {segment_id} via MCP.",
                    "Rules": [
                        {
                            "Arguments": [{"ExternalId": seg_num if seg_num is not None else segment_id}],
                            "Operator": "ALL",
                        }
                    ],
                }
            ]
        }
        ret_res = ctx._direct_call("retargetinglists", "add", ret_payload, direct_client_login=str(direct_login) if direct_login else None)  # type: ignore[attr-defined]
        add_res = (ret_res.get("result") or {}).get("AddResults") if isinstance(ret_res, dict) else None
        ret_id: int | None = None
        if isinstance(add_res, list) and add_res and isinstance(add_res[0], dict):
            try:
                ret_id = int(add_res[0].get("Id"))
            except Exception:
                ret_id = None
        if ret_id is None:
            raise HFError("Failed to create retargeting list (no Id in response).")

        # 2) Expand campaign targets to adgroups (bounded).
        adgroup_ids: list[int] = []
        for t in targets:
            if not isinstance(t, dict):
                continue
            t_type = str(t.get("type") or "").strip().lower()
            t_id = t.get("id")
            if t_id is None:
                continue
            if t_type == "adgroup":
                adgroup_ids.append(int(t_id))
            elif t_type == "campaign":
                res = ctx._direct_get(
                    "adgroups",
                    {
                        "SelectionCriteria": {"CampaignIds": [int(t_id)]},
                        "FieldNames": ["Id"],
                        "Page": {"Limit": 1000, "Offset": 0},
                    },
                    direct_client_login=str(direct_login) if direct_login else None,
                )  # type: ignore[attr-defined]
                groups = _extract_list(res.get("result", {}) if isinstance(res, dict) else {}, "AdGroups")
                for g in groups:
                    if g.get("Id") is not None:
                        adgroup_ids.append(int(g["Id"]))
        adgroup_ids = list(dict.fromkeys(adgroup_ids))[:500]
        if not adgroup_ids:
            raise HFError("No adgroups resolved from targets.")

        # 3) Create AudienceTargets (chunked).
        created: list[dict[str, Any]] = []
        chunk = 100
        for i in range(0, len(adgroup_ids), chunk):
            part = adgroup_ids[i : i + chunk]
            payload = {"AudienceTargets": [{"AdGroupId": aid, "RetargetingListId": ret_id} for aid in part]}
            res = ctx._direct_call("audiencetargets", "add", payload, direct_client_login=str(direct_login) if direct_login else None)  # type: ignore[attr-defined]
            created.append({"adgroup_ids": part, "response": res})

        return hf_payload(
            tool=tool,
            status="ok",
            result={
                "retargeting_list_id": ret_id,
                "adgroups_count": len(adgroup_ids),
                "created": created,
                "notes": [
                    "Bid modifiers are not configured by this tool (optional; implement via bidmodifiers if needed).",
                ],
            },
        )

    raise HFError(f"Unknown HF tool: {tool}")

