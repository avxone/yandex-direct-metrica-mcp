"""Human-friendly (HF) tools for Yandex Metrica CDP (orders, contacts) + Analytics (funnels, cohorts, attribution, revenue, ROI, audit)."""

from __future__ import annotations

from typing import Any

from .cdp_client import CDPClient
from .hf_common import HFError, ensure_hf_enabled, ensure_hf_write_enabled, hf_payload, should_apply


def _require_counter_id(args: dict[str, Any]) -> str:
    cid = args.get("counter_id")
    if not cid:
        raise HFError("counter_id is required")
    return str(cid)


def _require_client(ctx: Any) -> CDPClient:
    if not hasattr(ctx, "_cdp_client") or ctx._cdp_client is None:
        raise HFError("CDP client not initialized (CDP access token missing?)")
    return ctx._cdp_client  # type: ignore[attr-defined]


def _counter_payload(counter_id: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"counter_id": counter_id}
    payload.update(extra)
    return payload


def handle(tool: str, ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    ensure_hf_enabled(ctx.config)

    # ------------------------------------------------------------------
    # CDP INGESTION
    # ------------------------------------------------------------------

    if tool == "metrica.cdp.upload_simple_orders":
        ensure_hf_write_enabled(ctx.config)
        counter_id = _require_counter_id(args)
        rows = args.get("rows", [])
        if not rows:
            raise HFError("rows (list of order dicts) is required")
        preview = {"tool": tool, "counter_id": counter_id, "row_count": len(rows)}
        if not should_apply(args):
            return hf_payload(tool=tool, status="dry_run", preview=preview)
        client = _require_client(ctx)
        result = client.upload_simple_orders(
            counter_id,
            rows,
            auto_create_statuses=args.get("auto_create_statuses", True),
        )
        return hf_payload(tool=tool, status="ok", preview=preview, result=result)

    if tool == "metrica.cdp.upload_contacts":
        ensure_hf_write_enabled(ctx.config)
        counter_id = _require_counter_id(args)
        rows = args.get("rows", [])
        if not rows:
            raise HFError("rows (list of contact dicts) is required")
        preview = {"tool": tool, "counter_id": counter_id, "row_count": len(rows)}
        if not should_apply(args):
            return hf_payload(tool=tool, status="dry_run", preview=preview)
        client = _require_client(ctx)
        result = client.upload_contacts(counter_id, rows)
        return hf_payload(tool=tool, status="ok", preview=preview, result=result)

    if tool == "metrica.cdp.get_uploading_status":
        counter_id = _require_counter_id(args)
        upload_id = args.get("upload_id")
        if not upload_id:
            raise HFError("upload_id is required")
        client = _require_client(ctx)
        result = client.get_uploading_status(counter_id, str(upload_id))
        return hf_payload(tool=tool, status="ok", result=_counter_payload(counter_id, upload_id=upload_id, status=result))

    if tool == "metrica.cdp.get_order_statuses":
        counter_id = _require_counter_id(args)
        client = _require_client(ctx)
        statuses = client.get_order_statuses(counter_id)
        return hf_payload(tool=tool, status="ok", result=_counter_payload(counter_id, statuses=statuses))

    if tool == "metrica.cdp.create_order_status":
        ensure_hf_write_enabled(ctx.config)
        counter_id = _require_counter_id(args)
        name = args.get("name")
        if not name:
            raise HFError("name is required for order status")
        is_closed = bool(args.get("is_closed", False))
        preview = {"tool": tool, "counter_id": counter_id, "name": name, "is_closed": is_closed}
        if not should_apply(args):
            return hf_payload(tool=tool, status="dry_run", preview=preview)
        client = _require_client(ctx)
        result = client.create_order_status(counter_id, name, is_closed=is_closed)
        return hf_payload(tool=tool, status="ok", preview=preview, result=result)

    if tool == "metrica.cdp.get_attributes":
        counter_id = _require_counter_id(args)
        client = _require_client(ctx)
        attributes = client.get_attributes(counter_id)
        return hf_payload(tool=tool, status="ok", result=_counter_payload(counter_id, attributes=attributes))

    if tool == "metrica.cdp.create_attribute":
        ensure_hf_write_enabled(ctx.config)
        counter_id = _require_counter_id(args)
        name = args.get("name")
        attr_type = args.get("type", "string")
        if not name:
            raise HFError("name is required")
        preview = {"tool": tool, "counter_id": counter_id, "name": name, "type": attr_type}
        if not should_apply(args):
            return hf_payload(tool=tool, status="dry_run", preview=preview)
        client = _require_client(ctx)
        result = client.create_attribute(counter_id, name, attr_type)
        return hf_payload(tool=tool, status="ok", preview=preview, result=result)

    # ------------------------------------------------------------------
    # CDP ANALYTICS (via Metrica Stats API)
    # ------------------------------------------------------------------

    if tool == "metrica.analytics.funnel_report":
        """Воронка конверсий: шаги (цели) → просадки на каждом шаге."""
        counter_id = _require_counter_id(args)
        date_from = args.get("date_from")
        date_to = args.get("date_to")
        if not date_from or not date_to:
            raise HFError("date_from and date_to are required")
        # goal_ids — ordered list of steps in funnel
        goal_ids = args.get("goal_ids")
        if not goal_ids:
            raise HFError("goal_ids (ordered list of goal IDs) is required")
        # Build Stats API params
        goals_dim = ",".join(f"ym:s:goal{id}id" for id in goal_ids)
        goals_metric = ",".join(f"ym:s:goal{id}reaches" for id in goal_ids)
        raw = ctx._metrica_get_stats({
            "ids": counter_id,
            "metrics": goals_metric,
            "dimensions": goals_dim,
            "date1": date_from,
            "date2": date_to,
            "limit": 100000,
        })
        # Build funnel from raw data
        rows = raw.get("data", [])
        funnel = _build_funnel(rows, goal_ids)
        return hf_payload(tool=tool, status="ok", result=_counter_payload(counter_id, funnel=funnel, raw=raw))

    if tool == "metrica.analytics.cohort_report":
        """Когортный анализ: удержание (retention) по периодам."""
        counter_id = _require_counter_id(args)
        date_from = args.get("date_from")
        date_to = args.get("date_to")
        if not date_from or not date_to:
            raise HFError("date_from and date_to are required")
        granularity = args.get("granularity", "week")
        raw = ctx._metrica_get_stats({
            "ids": counter_id,
            "metrics": "ym:s:visits,ym:s:users",
            "dimensions": f"ym:s:date,ym:s:cohort{granularity.capitalize()}Number",
            "date1": date_from,
            "date2": date_to,
            "limit": 100000,
            "sort": "ym:s:date",
        })
        return hf_payload(tool=tool, status="ok", result=_counter_payload(counter_id, granularity=granularity, raw=raw))

    if tool == "metrica.analytics.attribution_report":
        """Атрибуция конверсий по источникам трафика."""
        counter_id = _require_counter_id(args)
        date_from = args.get("date_from")
        date_to = args.get("date_to")
        if not date_from or not date_to:
            raise HFError("date_from and date_to are required")
        metrics = "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds"
        dimensions = "ym:s:lastTrafficSource,ym:s:lastSourceEngine,ym:s:lastAdvEngine"
        raw = ctx._metrica_get_stats({
            "ids": counter_id,
            "metrics": metrics,
            "dimensions": dimensions,
            "date1": date_from,
            "date2": date_to,
            "limit": 100000,
            "sort": "-ym:s:visits",
        })
        return hf_payload(tool=tool, status="ok", result=_counter_payload(counter_id, raw=raw))

    if tool == "metrica.analytics.revenue_report":
        """Выручка по CDP/ecommerce данным."""
        counter_id = _require_counter_id(args)
        date_from = args.get("date_from")
        date_to = args.get("date_to")
        if not date_from or not date_to:
            raise HFError("date_from and date_to are required")
        granularity = args.get("granularity", "day")
        dim = "ym:s:date"
        metrics = "ym:s:sumRevenue,ym:s:orderCount,ym:s:revenuePerOrder,ym:s:orderSumMargin"
        raw = ctx._metrica_get_stats({
            "ids": counter_id,
            "metrics": metrics,
            "dimensions": dim,
            "date1": date_from,
            "date2": date_to,
            "limit": 100000,
            "sort": "ym:s:date",
        })
        return hf_payload(tool=tool, status="ok", result=_counter_payload(counter_id, granularity=granularity, raw=raw))

    if tool == "metrica.analytics.roi_report":
        """ROI/ROMI + Profit по CDP/ecommerce."""
        counter_id = _require_counter_id(args)
        date_from = args.get("date_from")
        date_to = args.get("date_to")
        if not date_from or not date_to:
            raise HFError("date_from and date_to are required")
        granularity = args.get("granularity", "day")
        dim = "ym:s:date"
        metrics = (
            "ym:s:sumRevenue,ym:s:orderSumCost,ym:s:sumProfit,"
            "ym:s:orderSumROI,ym:s:orderSumMargin,ym:s:orderSumMarginPercent"
        )
        raw = ctx._metrica_get_stats({
            "ids": counter_id,
            "metrics": metrics,
            "dimensions": dim,
            "date1": date_from,
            "date2": date_to,
            "limit": 100000,
            "sort": "ym:s:date",
        })
        return hf_payload(tool=tool, status="ok", result=_counter_payload(counter_id, granularity=granularity, raw=raw))

    if tool == "metrica.analytics.crm_match_report":
        """Сверка CRM-заказов с данными Метрики: поиск нестыковок."""
        counter_id = _require_counter_id(args)
        date_from = args.get("date_from")
        date_to = args.get("date_to")
        if not date_from or not date_to:
            raise HFError("date_from and date_to are required")
        # Fetch ecommerce data from Metrica
        raw = ctx._metrica_get_stats({
            "ids": counter_id,
            "metrics": "ym:s:sumRevenue,ym:s:orderCount,ym:s:orderSumCost,ym:s:sumProfit",
            "dimensions": "ym:s:date,ym:s:lastTrafficSource",
            "date1": date_from,
            "date2": date_to,
            "limit": 100000,
            "sort": "ym:s:date",
        })
        return hf_payload(tool=tool, status="ok", result=_counter_payload(counter_id, raw=raw))

    if tool == "metrica.analytics.comprehensive_audit":
        """Комплексный аудит: воронка + LTV + атрибуция за 1 вызов."""
        counter_id = _require_counter_id(args)
        date_from = args.get("date_from")
        date_to = args.get("date_to")
        if not date_from or not date_to:
            raise HFError("date_from and date_to are required")
        goal_ids = args.get("goal_ids")
        if not goal_ids:
            raise HFError("goal_ids is required for comprehensive audit")
        # 1. Funnel
        goals_dim = ",".join(f"ym:s:goal{id}id" for id in goal_ids)
        goals_metric = ",".join(f"ym:s:goal{id}reaches" for id in goal_ids)
        funnel_raw = ctx._metrica_get_stats({
            "ids": counter_id,
            "metrics": goals_metric,
            "dimensions": goals_dim,
            "date1": date_from,
            "date2": date_to,
            "limit": 100000,
        })
        funnel = _build_funnel(funnel_raw.get("data", []), goal_ids)
        # 2. LTV/Revenue
        revenue_raw = ctx._metrica_get_stats({
            "ids": counter_id,
            "metrics": "ym:s:visits,ym:s:users,ym:s:sumRevenue,ym:s:orderCount,ym:s:revenuePerUser",
            "dimensions": "ym:s:date",
            "date1": date_from,
            "date2": date_to,
            "limit": 100000,
            "sort": "ym:s:date",
        })
        # 3. Attribution
        attr_raw = ctx._metrica_get_stats({
            "ids": counter_id,
            "metrics": "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:sumRevenue",
            "dimensions": "ym:s:lastTrafficSource",
            "date1": date_from,
            "date2": date_to,
            "limit": 1000,
            "sort": "-ym:s:visits",
        })
        return hf_payload(tool=tool, status="ok", result=_counter_payload(counter_id,
            funnel=funnel,
            revenue=revenue_raw,
            attribution=attr_raw,
        ))

    raise HFError(f"Unknown CDP/Analytics tool: {tool}")


def _build_funnel(rows: list[dict[str, Any]], goal_ids: list[str]) -> list[dict[str, Any]]:
    """Build funnel steps from Stats API rows.
    
    Each row has dimensions[0-N] as goal IDs and metrics[0-N] as reaches.
    We aggregate: for each step (goal), sum all reaches across rows.
    """
    if not rows:
        return [{"step": i, "goal_id": gid, "reaches": 0} for i, gid in enumerate(goal_ids)]
    totals = {gid: 0 for gid in goal_ids}
    for row in rows:
        metrics = row.get("metrics", [])
        for i, gid in enumerate(goal_ids):
            if i < len(metrics):
                try:
                    totals[gid] += float(metrics[i])
                except (ValueError, TypeError):
                    pass
    funnel = []
    prev = None
    for i, gid in enumerate(goal_ids):
        reaches = totals[gid]
        conversion_from_prev = None
        if prev is not None and prev > 0:
            conversion_from_prev = round((reaches / prev) * 100, 2) if prev else 0.0
        total_conversion = None
        if i == 0 and reaches > 0:
            total_conversion = 100.0
        elif i > 0 and totals[goal_ids[0]] > 0:
            total_conversion = round((reaches / totals[goal_ids[0]]) * 100, 2)
        funnel.append({
            "step": i + 1,
            "goal_id": gid,
            "reaches": int(reaches),
            "conversion_from_previous_pct": conversion_from_prev,
            "total_conversion_pct": total_conversion,
        })
        prev = reaches
    return funnel
