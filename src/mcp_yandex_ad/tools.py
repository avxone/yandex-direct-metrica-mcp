"""MCP tool definitions for Yandex Direct + Metrica."""

from mcp.types import Tool

from .config import AppConfig
from .plugins import plugin_tools
from .tool_contracts import decorate_tool

HF_DESTRUCTIVE_TOOLS = {
    "direct.hf.delete_ads",
    "direct.hf.delete_keywords",
}

ACCOUNT_ID_SCHEMA_BASE = {
    "description": "Project profile id (resolves to Direct Client-Login and optional Metrica counter defaults).",
}

DIRECT_CLIENT_LOGIN_SCHEMA_BASE = {
    "type": "string",
    "description": "Override Direct Client-Login for this call (agency multi-project support).",
}


def _hf_tools() -> list[Tool]:
    # Schemas are intentionally compact; HF layer does ID resolution + builds raw payloads.
    return [
        Tool(
            name="direct.hf.find_campaigns",
            description="Human-friendly: find campaigns by name/status/type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name_contains": {"type": "string"},
                    "states": {"type": "array", "items": {"type": "string"}},
                    "statuses": {"type": "array", "items": {"type": "string"}},
                    "types": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="direct.hf.find_adgroups",
            description="Human-friendly: find ad groups by campaign and name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "integer"},
                    "campaign_name": {"type": "string"},
                    "name_contains": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="direct.hf.find_ads",
            description="Human-friendly: find ads by campaign/adgroup and title/href filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "integer"},
                    "campaign_name": {"type": "string"},
                    "adgroup_id": {"type": "integer"},
                    "adgroup_name": {"type": "string"},
                    "title_contains": {"type": "string"},
                    "href_contains": {"type": "string"},
                    "statuses": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="direct.hf.find_keywords",
            description="Human-friendly: find keywords by campaign/adgroup and substring.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "integer"},
                    "campaign_name": {"type": "string"},
                    "adgroup_id": {"type": "integer"},
                    "adgroup_name": {"type": "string"},
                    "contains": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="direct.hf.get_campaign_summary",
            description="Human-friendly: summarize campaigns with counts (adgroups/ads/keywords).",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "integer"},
                    "campaign_name": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="direct.hf.get_campaign_assets",
            description="Human-friendly: show sitelinks/callouts/vcards attached in campaign.",
            inputSchema={
                "type": "object",
                "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}},
            },
        ),
        # Campaign lifecycle
        Tool(
            name="direct.hf.pause_campaigns",
            description="Human-friendly: suspend campaigns (by id or name).",
            inputSchema={"type": "object", "properties": {"campaign_ids": {"type": "array", "items": {"type": "integer"}}, "campaign_name": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.resume_campaigns",
            description="Human-friendly: resume campaigns (by id or name).",
            inputSchema={"type": "object", "properties": {"campaign_ids": {"type": "array", "items": {"type": "integer"}}, "campaign_name": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.archive_campaigns",
            description="Human-friendly: archive campaigns (by id or name).",
            inputSchema={"type": "object", "properties": {"campaign_ids": {"type": "array", "items": {"type": "integer"}}, "campaign_name": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.unarchive_campaigns",
            description="Human-friendly: unarchive campaigns (by id or name).",
            inputSchema={"type": "object", "properties": {"campaign_ids": {"type": "array", "items": {"type": "integer"}}, "campaign_name": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        # Ads lifecycle
        Tool(
            name="direct.hf.moderate_ads",
            description="Human-friendly: send ads for moderation (by ids or campaign).",
            inputSchema={"type": "object", "properties": {"ad_ids": {"type": "array", "items": {"type": "integer"}}, "campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.pause_ads",
            description="Human-friendly: suspend ads.",
            inputSchema={"type": "object", "properties": {"ad_ids": {"type": "array", "items": {"type": "integer"}}, "campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.resume_ads",
            description="Human-friendly: resume ads.",
            inputSchema={"type": "object", "properties": {"ad_ids": {"type": "array", "items": {"type": "integer"}}, "campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.archive_ads",
            description="Human-friendly: archive ads.",
            inputSchema={"type": "object", "properties": {"ad_ids": {"type": "array", "items": {"type": "integer"}}, "campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.unarchive_ads",
            description="Human-friendly: unarchive ads.",
            inputSchema={"type": "object", "properties": {"ad_ids": {"type": "array", "items": {"type": "integer"}}, "campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.delete_ads",
            description="Human-friendly: delete ads (destructive, gated).",
            inputSchema={"type": "object", "properties": {"ad_ids": {"type": "array", "items": {"type": "integer"}}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.delete_keywords",
            description="Human-friendly: delete keywords (destructive, gated).",
            inputSchema={"type": "object", "properties": {"keyword_ids": {"type": "array", "items": {"type": "integer"}}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        # Campaign config + UTM
        Tool(
            name="direct.hf.set_campaign_strategy_preset",
            description="Human-friendly: apply a strategy preset to a campaign.",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "preset": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_campaign_budget",
            description="Human-friendly: set campaign daily budget (rubles) if supported, else returns patch hint.",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "daily_budget_rub": {"type": "number"}, "mode": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_campaign_geo",
            description="Human-friendly: set geo (RegionIds) for all ad groups in a campaign.",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "region_ids": {"type": "array", "items": {"type": "integer"}}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_campaign_schedule",
            description="Human-friendly: set campaign schedule/time targeting (best effort).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "time_targeting": {"type": "object"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_campaign_negative_keywords",
            description="Human-friendly: set campaign negative keywords.",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "items": {"type": "array", "items": {"type": "string"}}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_campaign_tracking_params",
            description="Human-friendly: set TrackingParams for a campaign (best effort).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "tracking_params": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_campaign_utm_template",
            description="Human-friendly: apply UTM template to a campaign (utm_mode=auto).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "utm_template": {"type": "string"}, "overwrite": {"type": "boolean"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.clone_campaign",
            description="Human-friendly: clone campaign structure into a new draft campaign (best effort).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "new_name": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        # Adgroups
        Tool(
            name="direct.hf.create_adgroup_simple",
            description="Human-friendly: create a simple ad group under a campaign.",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "name": {"type": "string"}, "region_ids": {"type": "array", "items": {"type": "integer"}}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.update_adgroup_geo",
            description="Human-friendly: set RegionIds for an ad group.",
            inputSchema={"type": "object", "properties": {"adgroup_id": {"type": "integer"}, "adgroup_name": {"type": "string"}, "campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "region_ids": {"type": "array", "items": {"type": "integer"}}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_adgroup_negative_keywords",
            description="Human-friendly: set ad group negative keywords.",
            inputSchema={"type": "object", "properties": {"adgroup_id": {"type": "integer"}, "adgroup_name": {"type": "string"}, "campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "items": {"type": "array", "items": {"type": "string"}}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_adgroup_autotargeting",
            description="Human-friendly: enable/disable autotargeting (best effort, depends on campaign type).",
            inputSchema={"type": "object", "properties": {"adgroup_id": {"type": "integer"}, "campaign_id": {"type": "integer"}, "enabled": {"type": "boolean"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_adgroup_tracking_params",
            description="Human-friendly: set TrackingParams for an ad group.",
            inputSchema={"type": "object", "properties": {"adgroup_id": {"type": "integer"}, "tracking_params": {"type": "string"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        # Ads / assets
        Tool(
            name="direct.hf.create_text_ads_bulk",
            description="Human-friendly: create multiple TextAds in an ad group.",
            inputSchema={"type": "object", "properties": {"adgroup_id": {"type": "integer"}, "ads": {"type": "array", "items": {"type": "object"}}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.update_ads_text_bulk",
            description="Human-friendly: update multiple TextAds fields (title/text/href).",
            inputSchema={"type": "object", "properties": {"ad_ids": {"type": "array", "items": {"type": "integer"}}, "patch": {"type": "object"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.apply_utm_to_ads",
            description="Human-friendly: apply UTM template to ads in a campaign (utm_mode=auto).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "utm_template": {"type": "string"}, "overwrite": {"type": "boolean"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.attach_sitelinks_to_ads",
            description="Human-friendly: attach an existing sitelinks set to ads.",
            inputSchema={"type": "object", "properties": {"ad_ids": {"type": "array", "items": {"type": "integer"}}, "sitelink_set_id": {"type": "integer"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.attach_callouts_to_ads",
            description="Human-friendly: attach callouts (adextension ids) to ads.",
            inputSchema={"type": "object", "properties": {"ad_ids": {"type": "array", "items": {"type": "integer"}}, "callout_ids": {"type": "array", "items": {"type": "integer"}}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.attach_vcard_to_ads",
            description="Human-friendly: attach vcard id to ads (if supported).",
            inputSchema={"type": "object", "properties": {"ad_ids": {"type": "array", "items": {"type": "integer"}}, "vcard_id": {"type": "integer"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.create_sitelinks_set",
            description="Human-friendly: create a sitelinks set.",
            inputSchema={"type": "object", "properties": {"sitelinks": {"type": "array", "items": {"type": "object"}}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.create_callouts",
            description="Human-friendly: create callouts (AdExtensions CALLOUT).",
            inputSchema={"type": "object", "properties": {"texts": {"type": "array", "items": {"type": "string"}}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.ensure_assets_for_campaign",
            description="Human-friendly: ensure sitelinks+callouts exist and attach to ads in campaign.",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "sitelinks": {"type": "array", "items": {"type": "object"}}, "callouts": {"type": "array", "items": {"type": "string"}}, "overwrite": {"type": "boolean"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        # Bids/modifiers
        Tool(
            name="direct.hf.set_keyword_bid",
            description="Human-friendly: set a bid for a single keyword (rubles).",
            inputSchema={"type": "object", "properties": {"keyword_id": {"type": "integer"}, "bid_rub": {"type": "number"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_keyword_bids_bulk",
            description="Human-friendly: set a uniform bid (rubles) for all keywords in a campaign/adgroup.",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "adgroup_id": {"type": "integer"}, "bid_rub": {"type": "number"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_autotargeting_bid",
            description="Human-friendly: set bid for ---autotargeting pseudo-keywords (rubles).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "bid_rub": {"type": "number"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.get_bids_summary",
            description="Human-friendly: summarize bids in a campaign (min/avg/max).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}}},
        ),
        Tool(
            name="direct.hf.set_bid_modifier_mobile",
            description="Human-friendly: set mobile bid modifier (percent).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "value_percent": {"type": "integer"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_bid_modifier_desktop",
            description="Human-friendly: set desktop bid modifier (percent).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "value_percent": {"type": "integer"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_bid_modifier_demographics",
            description="Human-friendly: set demographics bid modifier (age+gender).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "age": {"type": "string"}, "gender": {"type": "string"}, "value_percent": {"type": "integer"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.set_bid_modifier_geo",
            description="Human-friendly: set geo bid modifier (best effort).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "region_id": {"type": "integer"}, "value_percent": {"type": "integer"}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        Tool(
            name="direct.hf.clear_bid_modifiers",
            description="Human-friendly: delete bid modifiers (by campaign/type).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "types": {"type": "array", "items": {"type": "string"}}, "dry_run": {"type": "boolean"}, "apply": {"type": "boolean"}}},
        ),
        # Reporting presets
        Tool(
            name="direct.hf.report_performance",
            description="Human-friendly: Direct performance report preset (day/week/month).",
            inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "campaign_name": {"type": "string"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}, "granularity": {"type": "string"}}},
        ),
        Tool(name="direct.hf.report_keywords", description="Human-friendly: Direct keyword report preset.", inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}}}),
        Tool(name="direct.hf.report_ads", description="Human-friendly: Direct ads report preset.", inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}}}),
        Tool(name="direct.hf.report_adgroups", description="Human-friendly: Direct adgroups report preset.", inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}}}),
        Tool(name="direct.hf.report_search_phrases", description="Human-friendly: Direct search phrases report preset (optional).", inputSchema={"type": "object", "properties": {"campaign_id": {"type": "integer"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}}}),
        Tool(
            name="direct.hf.pressure_report",
            description="Human-friendly: market pressure report by semantic clusters (best effort, read-only).",
            inputSchema={
                "type": "object",
                "required": ["date_from", "date_to"],
                "properties": {
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD."},
                    "grain": {"type": "string", "description": "day|week|month (default: day)."},
                    "placement": {"type": "string", "description": "search|rsya|all (default: all)."},
                    "regions": {"type": "array", "items": {"type": "integer"}, "description": "Optional Direct regions filter (best effort)."},
                    "devices": {"type": "array", "items": {"type": "string"}, "description": "Optional Direct devices filter (best effort)."},
                    "campaign_ids": {"type": "array", "items": {"type": "integer"}, "description": "Optional campaign filter."},
                    "adgroup_ids": {"type": "array", "items": {"type": "integer"}, "description": "Optional ad group filter."},
                    "clusters": {
                        "type": "array",
                        "description": "Optional semantic clusters input. When omitted, returns one __all__ cluster.",
                        "items": {
                            "type": "object",
                            "required": ["cluster_id"],
                            "properties": {
                                "cluster_id": {"type": "string"},
                                "phrases": {"type": "array", "items": {"type": "string"}},
                                "label": {"type": "string"},
                            },
                        },
                    },
                    "include_breakdown": {"type": "boolean", "description": "Try to include placement/device/region breakdown when supported."},
                    "max_rows": {"type": "integer", "description": "Parse at most N report rows (default: 50000)."},
                },
            },
        ),
        # Metrica HF (will error if no access; kept for discoverability)
        Tool(name="metrica.hf.list_accessible_counters", description="Human-friendly: list accessible counters.", inputSchema={"type": "object", "properties": {}}),
        Tool(name="metrica.hf.counter_summary", description="Human-friendly: counter summary.", inputSchema={"type": "object", "properties": {"counter_id": {"type": "string"}}}),
        Tool(name="metrica.hf.report_time_series", description="Human-friendly: time series report (day/week/month/quarter/year).", inputSchema={"type": "object", "properties": {"counter_id": {"type": "string"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}, "metric": {"type": "string"}, "granularity": {"type": "string"}}}),
        Tool(name="metrica.hf.report_landing_pages", description="Human-friendly: landing pages report.", inputSchema={"type": "object", "properties": {"counter_id": {"type": "string"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}, "limit": {"type": "integer"}}}),
        Tool(name="metrica.hf.report_utm_campaigns", description="Human-friendly: UTM campaigns report.", inputSchema={"type": "object", "properties": {"counter_id": {"type": "string"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}, "limit": {"type": "integer"}}}),
        Tool(name="metrica.hf.report_geo", description="Human-friendly: geo report (country/city).", inputSchema={"type": "object", "properties": {"counter_id": {"type": "string"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}, "level": {"type": "string"}, "limit": {"type": "integer"}}}),
        Tool(name="metrica.hf.report_devices", description="Human-friendly: device report.", inputSchema={"type": "object", "properties": {"counter_id": {"type": "string"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}, "limit": {"type": "integer"}}}),
        Tool(name="metrica.hf.logs_export_preset", description="Human-friendly: logs export preset (optional).", inputSchema={"type": "object", "properties": {"counter_id": {"type": "string"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}}}),
        # Metrica HF (pro write): goals CRUD
        Tool(
            name="metrica.hf.create_goal",
            description="Human-friendly: create a Metrica goal (pro-only, apply=true).",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "goal", "apply"],
                "properties": {
                    "counter_id": {"type": "string"},
                    "goal": {"type": "object", "description": "Raw goal object as per Metrica Management API."},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        Tool(
            name="metrica.hf.update_goal",
            description="Human-friendly: update a Metrica goal (pro-only, apply=true).",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "goal_id", "goal", "apply"],
                "properties": {
                    "counter_id": {"type": "string"},
                    "goal_id": {"type": "string"},
                    "goal": {"type": "object", "description": "Raw goal patch object as per Metrica Management API."},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        Tool(
            name="metrica.hf.delete_goal",
            description="Human-friendly: delete a Metrica goal (pro-only, apply=true).",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "goal_id", "apply"],
                "properties": {
                    "counter_id": {"type": "string"},
                    "goal_id": {"type": "string"},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # Direct HF (pro): plan/apply changes (Wordstat→Direct apply pattern)
        Tool(
            name="direct.hf.plan_changes",
            description="Human-friendly: build an opaque change plan for Direct (preview-only).",
            inputSchema={
                "type": "object",
                "required": ["operations"],
                "properties": {
                    "operations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["op"],
                            "properties": {
                                "op": {"type": "string", "description": "keywords.add | negatives.merge | bids.set"},
                                "adgroup_id": {"type": "integer"},
                                "campaign_id": {"type": "integer"},
                                "keyword_ids": {"type": "array", "items": {"type": "integer"}},
                                "phrases": {"type": "array", "items": {"type": "string"}},
                                "items": {"type": "array", "items": {"type": "string"}, "description": "Negatives items (tokens/phrases)."},
                                "bid_rub": {"type": "number"},
                                "max_phrases": {"type": "integer"},
                                "dedupe_mode": {"type": "string", "description": "normalize|strict (default: normalize)."},
                                "mode": {"type": "string", "description": "merge|replace for negatives (default: merge)."},
                            },
                        },
                    },
                },
            },
        ),
        Tool(
            name="direct.hf.apply_plan",
            description="Human-friendly: apply a previously planned Direct change plan (pro-only, apply=true).",
            inputSchema={
                "type": "object",
                "required": ["plan_id", "apply"],
                "properties": {
                    "plan_id": {"type": "string", "description": "Opaque plan id returned by direct.hf.plan_changes."},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # Direct HF (pro): bid sweep experiments (sandbox-only)
        Tool(
            name="direct.hf.bid_sweep_plan",
            description="Human-friendly: build a bid sweep experiment plan (pro-only; execution is sandbox-only).",
            inputSchema={
                "type": "object",
                "required": ["bid_steps_rub"],
                "properties": {
                    "account_id": {"type": "string"},
                    "campaign_id": {"type": "integer"},
                    "campaign_name": {"type": "string"},
                    "adgroup_id": {"type": "integer"},
                    "keyword_ids": {"type": "array", "items": {"type": "integer"}},
                    "include_autotargeting": {"type": "boolean", "description": "Include ---autotargeting pseudo-keywords (default: false)."},
                    "bid_steps_rub": {"type": "array", "items": {"type": "number"}, "description": "Bid sweep steps in rubles (ordered)."},
                    "restore_bid_rub": {"type": "number", "description": "Optional final restore bid in rubles."},
                    "max_keywords": {"type": "integer", "description": "Safety cap (default: 20, max: 200)."},
                    "max_steps": {"type": "integer", "description": "Safety cap (default: 6, max: 20)."},
                    "notes": {"type": "string"},
                },
            },
        ),
        Tool(
            name="direct.hf.bid_sweep_run",
            description="Human-friendly: apply one bid sweep step (pro-only, apply=true, sandbox-only).",
            inputSchema={
                "type": "object",
                "required": ["plan_id", "step_index", "apply"],
                "properties": {
                    "plan_id": {"type": "string", "description": "Opaque plan id returned by direct.hf.bid_sweep_plan."},
                    "step_index": {"type": "integer", "description": "0-based step index to apply."},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        Tool(
            name="direct.hf.bid_sweep_analyze",
            description="Human-friendly: analyze a bid sweep plan using Direct keyword performance report (read-only).",
            inputSchema={
                "type": "object",
                "required": ["plan_id", "windows"],
                "properties": {
                    "plan_id": {"type": "string"},
                    "windows": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["step_index", "date_from", "date_to"],
                            "properties": {
                                "step_index": {"type": "integer"},
                                "date_from": {"type": "string"},
                                "date_to": {"type": "string"},
                            },
                        },
                    },
                    "include_per_keyword": {"type": "boolean", "description": "Include per-keyword breakdown (default: false)."},
                    "max_rows": {"type": "integer", "description": "Parse at most N report rows (default: 50000)."},
                },
            },
        ),
        # Wordstat HF
        Tool(
            name="wordstat.hf.suggest_keywords",
            description="Human-friendly: suggest keyword candidates from seed phrases (resumable via cursor).",
            inputSchema={
                "type": "object",
                "properties": {
                    "seed_phrases": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Start a new run. Provide either seed_phrases or cursor (exactly one).",
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Resume a pending run. Provide either seed_phrases or cursor (exactly one).",
                    },
                    "regions": {"type": "array", "items": {"type": "integer"}},
                    "devices": {"type": "array", "items": {"type": "string"}},
                    "num_phrases": {"type": "integer", "description": "Per-seed numPhrases (default: 50, max: 2000)."},
                    "max_seed_phrases_per_call": {"type": "integer", "description": "How many seeds to process per call (default: 8)."},
                    "max_candidates": {"type": "integer", "description": "Max candidates to return (default: 200)."},
                },
            },
        ),
        Tool(
            name="wordstat.hf.suggest_negative_keywords",
            description="Human-friendly: suggest negative keyword tokens from phrases (lexicon-based).",
            inputSchema={
                "type": "object",
                "required": ["phrases"],
                "properties": {
                    "phrases": {"type": "array", "items": {"type": "string"}},
                    "language": {"type": "string", "description": "ru|en (default: ru)."},
                    "max_candidates": {"type": "integer", "description": "Max tokens to return (default: 100)."},
                },
            },
        ),
        # Audience HF (public read-only + pro activation)
        Tool(
            name="audience.hf.find_segment",
            description="Human-friendly: find Audience segments by name/type/status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name_contains": {"type": "string"},
                    "types": {"type": "array", "items": {"type": "string"}},
                    "statuses": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "integer", "description": "Default: 20."},
                    "include_raw": {"type": "boolean", "description": "Include raw response (default: false)."},
                },
            },
        ),
        Tool(
            name="audience.hf.get_segment_summary",
            description="Human-friendly: Audience segment summary card for UI/LLM.",
            inputSchema={
                "type": "object",
                "required": ["segment_id"],
                "properties": {
                    "segment_id": {"type": "string"},
                    "include_raw": {"type": "boolean", "description": "Include raw response (default: true)."},
                },
            },
        ),
        Tool(
            name="audience.hf.segment_health",
            description="Human-friendly: Audience segment health check.",
            inputSchema={
                "type": "object",
                "required": ["segment_id"],
                "properties": {
                    "segment_id": {"type": "string"},
                    "min_size": {"type": "integer", "description": "Default: 1000."},
                    "max_age_days": {"type": "integer", "description": "Default: 30."},
                },
            },
        ),
        Tool(
            name="audience.hf.overlap_matrix",
            description="Human-friendly: overlap matrix (sparse) for segment ids.",
            inputSchema={
                "type": "object",
                "required": ["segment_ids"],
                "properties": {
                    "segment_ids": {"type": "array", "items": {"type": "string"}},
                    "top_k": {"type": "integer", "description": "Default: 50."},
                },
            },
        ),
        Tool(
            name="audience.hf.segment_perf",
            description="Human-friendly: best-effort segment performance via Direct+Metrica.",
            inputSchema={
                "type": "object",
                "required": ["segment_id", "date_from", "date_to"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "counter_id": {"type": "integer"},
                    "segment_id": {"type": "string"},
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD."},
                    "grain": {"type": "string", "description": "day|week|month (default: day)."},
                    "goal_ids": {"type": "array", "items": {"type": "integer"}},
                    "include_raw_refs": {"type": "boolean", "description": "Include raw_refs (default: true)."},
                },
            },
        ),
        Tool(
            name="audience.hf.catalog",
            description="Human-friendly: audience segments catalog for dashboards.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"},
                    "include_health": {"type": "boolean", "description": "Default: false."},
                },
            },
        ),
        Tool(
            name="audience.hf.activation_plan",
            description="Human-friendly: preview Direct activation plan for an Audience segment (pro-only apply tool is separate).",
            inputSchema={
                "type": "object",
                "required": ["segment_id", "targets"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "segment_id": {"type": "string"},
                    "targets": {
                        "type": "array",
                        "description": "Activation targets (adgroup/campaign).",
                        "items": {
                            "type": "object",
                            "required": ["type", "id"],
                            "properties": {
                                "type": {"type": "string", "description": "adgroup|campaign"},
                                "id": {"type": "integer"},
                                "bid_modifier_percent": {"type": "integer", "description": "Optional bid modifier (percent)."},
                            },
                        },
                    },
                    "apply": {"type": "boolean", "description": "Must be false for preview tool."},
                },
            },
        ),
        Tool(
            name="audience.hf.apply_activation_plan",
            description="Human-friendly: apply activation plan for an Audience segment in Direct (pro-only, apply=true).",
            inputSchema={
                "type": "object",
                "required": ["segment_id", "targets", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "segment_id": {"type": "string"},
                    "targets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["type", "id"],
                            "properties": {
                                "type": {"type": "string", "description": "adgroup|campaign"},
                                "id": {"type": "integer"},
                                "bid_modifier_percent": {"type": "integer"},
                            },
                        },
                    },
                    "apply": {"type": "boolean", "description": "Must be true to execute."},
                    "dry_run": {"type": "boolean", "description": "Optional preview flag (default: true)."},
                },
            },
        ),
        # Joins
        Tool(
            name="join.hf.direct_vs_metrica_by_utm",
            description="Human-friendly: join Direct daily performance with Metrica daily visits using a stable UTMCampaign value.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "integer", "description": "Direct campaign id."},
                    "campaign_name": {"type": "string", "description": "Optional campaign name (used to infer utm_campaign)."},
                    "utm_campaign": {"type": "string", "description": "Explicit ym:s:UTMCampaign value to match in Metrica."},
                    "counter_id": {"type": "string", "description": "Metrica counter id."},
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD."},
                },
            },
        ),
        Tool(
            name="join.hf.direct_vs_metrica_by_yclid",
            description="Human-friendly: join Metrica visits (Logs API yclid) with Direct click identifiers (best effort).",
            inputSchema={
                "type": "object",
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter id."},
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD."},
                    "request_id": {"type": "string", "description": "Optional existing Logs API request id to resume."},
                    "max_wait_seconds": {"type": "number", "description": "Max time to wait for Logs export readiness (default: 60)."},
                    "poll_interval_seconds": {"type": "number", "description": "Polling interval for Logs export status (default: 2)."},
                    "max_rows": {"type": "integer", "description": "Max log rows to download/parse (default: 20000)."},
                    "cleanup": {"type": "boolean", "description": "Call logs clean after download (default: true)."},
                    "logs_source": {"type": "string", "description": "Logs API source (default: visits)."},
                    "logs_fields": {"type": "string", "description": "CSV fields list (default: ym:s:dateTime,ym:s:startURL,ym:s:lastDirectClickBanner)."},
                    "logs_delimiter": {"type": "string", "description": "Override delimiter for downloaded logs (default: autodetect)."},
                    "yclid_field": {"type": "string", "description": "Field name for yclid in logs (default: ym:s:yclid)."},
                    "start_url_field": {"type": "string", "description": "Field name for start URL in logs (default: ym:s:startURL)."},
                    "banner_field": {"type": "string", "description": "Field name for Direct banner/ad id in logs (default: ym:s:lastDirectClickBanner)."},
                    "direct_report_type": {"type": "string", "description": "Direct report type (default: CUSTOM_REPORT)."},
                    "direct_field_names": {"type": "array", "items": {"type": "string"}, "description": "Direct report field names (default: [Date, CampaignId, ClickId])."},
                    "direct_click_id_field": {"type": "string", "description": "Column name to use as click id in Direct report (default: ClickId)."},
                    "direct_campaign_id_field": {"type": "string", "description": "Column name to use as campaign id in Direct report (default: CampaignId)."},
                    "direct_max_rows": {"type": "integer", "description": "Max Direct report rows to parse (default: 200000)."},
                },
            },
        ),
        # ═══ Extra tools (hf_direct_extra.py) ════════════════════════
        Tool(
            name="direct.hf.video_list",
            description="List uploaded videos.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_ids": {"type": "array", "items": {"type": "integer"}},
                },
            },
        ),
        Tool(
            name="direct.hf.video_upload",
            description="Upload a video file to Yandex Direct.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to video file"},
                    "name": {"type": "string", "description": "Video name (optional)"},
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="direct.hf.feed_list",
            description="List product feeds.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_ids": {"type": "array", "items": {"type": "integer"}},
                },
            },
        ),
        Tool(
            name="direct.hf.feed_create",
            description="Create a product feed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Feed name"},
                    "business_type": {"type": "string", "enum": ["RETAIL", "HOTELS", "REALTY", "AUTOMOBILES", "FLIGHTS", "OTHER"]},
                    "url": {"type": "string", "description": "Feed YML URL"},
                    "login": {"type": "string", "description": "HTTP auth login (optional)"},
                    "password": {"type": "string", "description": "HTTP auth password (optional)"},
                    "remove_utm_tags": {"type": "string", "enum": ["YES", "NO"]},
                },
                "required": ["name", "business_type", "url"],
            },
        ),
        Tool(
            name="direct.hf.feed_delete",
            description="Delete feeds.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["feed_ids"],
            },
        ),
        Tool(
            name="direct.hf.feed_update",
            description="Update a feed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "url": {"type": "string"},
                    "login": {"type": "string"},
                    "password": {"type": "string"},
                },
                "required": ["feed_id"],
            },
        ),
        Tool(
            name="direct.hf.smart_target_list",
            description="List smart ad targets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_ids": {"type": "array", "items": {"type": "integer"}},
                    "adgroup_ids": {"type": "array", "items": {"type": "integer"}},
                    "target_ids": {"type": "array", "items": {"type": "integer"}},
                },
            },
        ),
        Tool(
            name="direct.hf.smart_target_create",
            description="Create a smart ad target.",
            inputSchema={
                "type": "object",
                "properties": {
                    "adgroup_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "available_items_only": {"type": "string", "enum": ["YES", "NO"]},
                    "conditions": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["adgroup_id", "name"],
            },
        ),
        Tool(
            name="direct.hf.smart_target_action",
            description="Suspend, resume, or delete smart ad targets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_ids": {"type": "array", "items": {"type": "integer"}},
                    "action": {"type": "string", "enum": ["suspend", "resume", "delete"]},
                },
                "required": ["target_ids", "action"],
            },
        ),
        Tool(
            name="direct.hf.businesses_get",
            description="Get organization profiles from Yandex Business.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["ids"],
            },
        ),
        Tool(
            name="direct.hf.creative_add",
            description="Create a video extension creative.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string"},
                },
                "required": ["video_id"],
            },
        ),
        Tool(
            name="direct.hf.creative_list",
            description="List creatives.",
            inputSchema={
                "type": "object",
                "properties": {
                    "creative_ids": {"type": "array", "items": {"type": "integer"}},
                    "types": {"type": "array", "items": {"type": "string"}},
                },
            },
        ),
        Tool(
            name="direct.hf.vcard_create",
            description="Create a VCard (business card) for a campaign.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "integer"},
                    "country": {"type": "string"},
                    "city": {"type": "string"},
                    "city_code": {"type": "string"},
                    "company": {"type": "string"},
                    "phone_number": {"type": "string"},
                    "street": {"type": "string"},
                    "house": {"type": "string"},
                    "work_time": {"type": "string"},
                    "extra_message": {"type": "string"},
                },
                "required": ["campaign_id", "company", "city_code", "phone_number", "city", "country"],
            },
        ),
        Tool(
            name="direct.hf.vcard_list",
            description="List VCards.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vcard_ids": {"type": "array", "items": {"type": "integer"}},
                },
            },
        ),
        Tool(
            name="direct.hf.vcard_delete",
            description="Delete VCards.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vcard_ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["vcard_ids"],
            },
        ),
        Tool(
            name="direct.hf.blocked_ips_update",
            description="Set blocked IPs for a campaign (max 25).",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "integer"},
                    "ips": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["campaign_id", "ips"],
            },
        ),
        Tool(
            name="direct.hf.excluded_sites_get",
            description="Get excluded sites (blocked placements) for a campaign.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "integer"},
                },
                "required": ["campaign_id"],
            },
        ),
        Tool(
            name="direct.hf.excluded_sites_update",
            description="Set excluded sites for a campaign.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "integer"},
                    "sites": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["campaign_id", "sites"],
            },
        ),
        Tool(
            name="direct.hf.neg_keyword_set_create",
            description="Create a shared negative keyword set.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "negative_keywords": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "negative_keywords"],
            },
        ),
        Tool(
            name="direct.hf.neg_keyword_set_list",
            description="List shared negative keyword sets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {"type": "array", "items": {"type": "integer"}},
                },
            },
        ),
        Tool(
            name="direct.hf.neg_keyword_set_update",
            description="Update a shared negative keyword set.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "negative_keywords": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="direct.hf.neg_keyword_set_delete",
            description="Delete shared negative keyword sets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["ids"],
            },
        ),
        Tool(
            name="direct.hf.keyword_bids_set_auto",
            description="Set automatic bidding for keywords by target position.",
            inputSchema={
                "type": "object",
                "properties": {
                    "bids": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "keyword_id": {"type": "integer"},
                                "position": {"type": "string", "enum": ["PREMIUMBLOCK", "FOOTERBLOCK", "P11", "P12", "P13", "P14", "P21", "P22", "P23", "P24"]},
                                "scope": {"type": "string", "enum": ["SEARCH", "NETWORK", "SEARCH_AND_NETWORK"]},
                                "max_bid": {"type": "number"},
                                "increase_percent": {"type": "integer"},
                            },
                            "required": ["keyword_id"],
                        },
                    },
                },
                "required": ["bids"],
            },
        ),
        Tool(
            name="direct.hf.keywords_has_volume",
            description="Check if keywords have search volume in regions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "region_ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["keywords", "region_ids"],
            },
        ),
        Tool(
            name="direct.hf.keywords_research",
            description="Deduplicate keywords: merge duplicates, eliminate overlapping.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "operations": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["MERGE_DUPLICATES", "ELIMINATE_OVERLAPPING"]},
                    },
                },
                "required": ["keywords"],
            },
        ),
        Tool(
            name="direct.hf.bid_modifiers_toggle",
            description="Enable or disable bid modifiers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "bid_modifier_ids": {"type": "array", "items": {"type": "integer"}},
                    "enabled": {"type": "boolean"},
                },
                "required": ["bid_modifier_ids", "enabled"],
            },
        ),
        Tool(
            name="direct.hf.callouts_link",
            description="Link callout extensions to an ad.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ad_id": {"type": "integer"},
                    "callout_ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["ad_id", "callout_ids"],
            },
        ),
        # ═══ Batch 2: dynamic/image/shopping ads ──────────���─────────────
        Tool(
            name="direct.hf.create_dynamic_ads",
            description="Create dynamic text ads.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ads": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ad_group_id": {"type": "integer"},
                                "title": {"type": "string"},
                                "text": {"type": "string"},
                                "href": {"type": "string"},
                                "sitelink_set_id": {"type": "integer"},
                            },
                            "required": ["ad_group_id", "text", "href"],
                        },
                    },
                },
                "required": ["ads"],
            },
        ),
        Tool(
            name="direct.hf.create_image_ads",
            description="Create image/text-image ads.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ads": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ad_group_id": {"type": "integer"},
                                "title": {"type": "string"},
                                "title2": {"type": "string"},
                                "text": {"type": "string"},
                                "href": {"type": "string"},
                                "ad_image_hash": {"type": "string"},
                            },
                            "required": ["ad_group_id"],
                        },
                    },
                },
                "required": ["ads"],
            },
        ),
        Tool(
            name="direct.hf.create_shopping_ads",
            description="Create shopping ads.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ads": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ad_group_id": {"type": "integer"},
                                "title": {"type": "string"},
                                "sitelink_set_id": {"type": "integer"},
                            },
                            "required": ["ad_group_id", "title"],
                        },
                    },
                },
                "required": ["ads"],
            },
        ),
        # ═══ Batch 2: ad images ─────────────────────────────────────────
        Tool(
            name="direct.hf.ad_images_add",
            description="Upload ad images (base64-encoded).",
            inputSchema={
                "type": "object",
                "properties": {
                    "images": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Image name"},
                                "image_data": {"type": "string", "description": "Base64-encoded image data"},
                            },
                            "required": ["name", "image_data"],
                        },
                    },
                },
                "required": ["images"],
            },
        ),
        Tool(
            name="direct.hf.ad_images_get",
            description="Get ad images by hashes or associated status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {"type": "array", "items": {"type": "string"}},
                    "associated": {"type": "boolean"},
                },
            },
        ),
        Tool(
            name="direct.hf.ad_images_delete",
            description="Delete ad images by hashes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["ids"],
            },
        ),
        # ═══ Batch 2: audience targets ─────────────────────────────────
        Tool(
            name="direct.hf.audience_targets_add",
            description="Add audience targeting conditions to ad groups.",
            inputSchema={
                "type": "object",
                "properties": {
                    "targets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ad_group_id": {"type": "integer"},
                                "retargeting_list_id": {"type": "integer"},
                                "interest_id": {"type": "integer"},
                                "context_bid": {"type": "number"},
                                "strategy_priority": {"type": "string", "enum": ["LOW", "NORMAL", "HIGH"]},
                            },
                            "required": ["ad_group_id"],
                        },
                    },
                },
                "required": ["targets"],
            },
        ),
        Tool(
            name="direct.hf.audience_targets_get",
            description="Get audience targets by campaign/ad group/target IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_ids": {"type": "array", "items": {"type": "integer"}},
                    "ad_group_ids": {"type": "array", "items": {"type": "integer"}},
                    "ids": {"type": "array", "items": {"type": "integer"}},
                },
            },
        ),
        Tool(
            name="direct.hf.audience_targets_delete",
            description="Delete audience targeting conditions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["ids"],
            },
        ),
        # ═══ Batch 2: retargeting lists ─────────────────────────────────
        Tool(
            name="direct.hf.retargeting_lists_add",
            description="Create retargeting/audience conditions based on Metrika goals.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "rules": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "operator": {"type": "string", "enum": ["ALL", "ANY", "NONE"]},
                                "goals": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "goal_id": {"type": "integer"},
                                            "membership_life_span": {"type": "integer"},
                                        },
                                        "required": ["goal_id"],
                                    },
                                },
                            },
                            "required": ["operator", "goals"],
                        },
                    },
                },
                "required": ["name", "rules"],
            },
        ),
        Tool(
            name="direct.hf.retargeting_lists_get",
            description="Get retargeting lists.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {"type": "array", "items": {"type": "integer"}},
                },
            },
        ),
        Tool(
            name="direct.hf.retargeting_lists_delete",
            description="Delete retargeting lists.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["ids"],
            },
        ),
        # ═══ Batch 2: sitelinks / extensions / interests ────────────────
        Tool(
            name="direct.hf.sitelinks_delete",
            description="Delete sitelinks sets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["ids"],
            },
        ),
        Tool(
            name="direct.hf.ad_extensions_get",
            description="Get ad extensions by IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["ids"],
            },
        ),
        Tool(
            name="direct.hf.ad_extensions_delete",
            description="Delete ad extensions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["ids"],
            },
        ),
        Tool(
            name="direct.hf.interests_get",
            description="Get interest categories (for mobile app targeting).",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # ═══════════════════════════════════════════════════════════════════
        # NEW TOOLS — Created from TZ (15.07.2026)
        # ═══════════════════════════════════════════════════════════════════
        # ─── Create campaign ───────────────────────────────────────────
        Tool(
            name="direct.hf.create_campaign",
            description="Create a campaign from scratch (TEXT/SMART/UNIFIED). Supports budget (rub), strategy, regions, schedule.",
            inputSchema={
                "type": "object",
                "required": ["name", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "name": {"type": "string", "description": "Campaign name"},
                    "type": {"type": "string", "enum": ["TEXT_CAMPAIGN", "SMART_CAMPAIGN", "UNIFIED_CAMPAIGN"], "description": "Campaign type (default TEXT_CAMPAIGN)"},
                    "daily_budget_rub": {"type": "number", "description": "Daily budget in rubles"},
                    "strategy": {
                        "type": "object",
                        "description": "Bidding strategy",
                        "properties": {
                            "type": {"type": "string", "description": "WB_MAXIMUM_CONVERSION_RATE, AVERAGE_CPC, etc."},
                            "weekly_spend_limit_rub": {"type": "number"},
                            "avg_cpc_rub": {"type": "number"},
                        },
                    },
                    "region_ids": {"type": "array", "items": {"type": "integer"}, "description": "Region IDs for targeting"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD campaign start date"},
                    "utm_template": {"type": "string", "description": "UTM template string"},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # ─── Combinator text ads ───────────────────────────────────────
        Tool(
            name="direct.hf.create_textads_combinator",
            description="Create text ads with ContentBlocks (combinator format). Supports TEXT/MEDIA/BUTTON blocks.",
            inputSchema={
                "type": "object",
                "required": ["ad_group_id", "blocks", "href", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "ad_group_id": {"type": "integer"},
                    "blocks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["type"],
                            "properties": {
                                "type": {"type": "string", "enum": ["TEXT", "MEDIA", "BUTTON"]},
                                "content": {"type": "string"},
                                "media_type": {"type": "string", "enum": ["IMAGE", "VIDEO"]},
                                "ad_image_hash": {"type": "string"},
                                "creative_id": {"type": "integer"},
                                "text": {"type": "string"},
                            },
                        },
                    },
                    "href": {"type": "string"},
                    "sitelink_set_id": {"type": "integer"},
                    "callout_ids": {"type": "array", "items": {"type": "integer"}},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # ─── Leads ────────────────────────────────────────────────────
        Tool(
            name="direct.hf.get_leads",
            description="Get leads from lead-based campaigns.",
            inputSchema={
                "type": "object",
                "required": ["campaign_id"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "campaign_id": {"type": "integer"},
                    "date_from": {"type": "string", "description": "YYYY-MM-DD"},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD"},
                    "limit": {"type": "integer", "description": "Page size (default: 50)"},
                    "offset": {"type": "integer", "description": "Page offset"},
                },
            },
        ),
        # ─── Creative update/delete ───────────────────────────────────
        Tool(
            name="direct.hf.creative_update",
            description="Update a creative (video extension).",
            inputSchema={
                "type": "object",
                "required": ["creative_id", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "creative_id": {"type": "integer"},
                    "video_id": {"type": "string"},
                    "name": {"type": "string"},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        Tool(
            name="direct.hf.creative_delete",
            description="Delete creatives.",
            inputSchema={
                "type": "object",
                "required": ["creative_ids", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "creative_ids": {"type": "array", "items": {"type": "integer"}},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # ─── Video delete ─────────────────────────────────────────────
        Tool(
            name="direct.hf.video_delete",
            description="Delete uploaded videos.",
            inputSchema={
                "type": "object",
                "required": ["video_ids", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "video_ids": {"type": "array", "items": {"type": "string"}},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # ─── Keywords resume/update ───────────────────────────────────
        Tool(
            name="direct.hf.keywords_resume",
            description="Resume auto-paused keywords.",
            inputSchema={
                "type": "object",
                "required": ["keyword_ids", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "keyword_ids": {"type": "array", "items": {"type": "integer"}},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        Tool(
            name="direct.hf.update_keywords",
            description="Update keyword properties (text, bid in rubles, strategy priority).",
            inputSchema={
                "type": "object",
                "required": ["keyword_id", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "keyword_id": {"type": "integer"},
                    "keyword": {"type": "string", "description": "New keyword text"},
                    "bid_rub": {"type": "number", "description": "Bid in rubles (converted to micros)"},
                    "strategy_priority": {"type": "string", "enum": ["LOW", "NORMAL", "HIGH"]},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # ─── Audience targets setBids ──────────────────────────────────
        Tool(
            name="direct.hf.audience_targets_set_bids",
            description="Set bids on audience targets.",
            inputSchema={
                "type": "object",
                "required": ["bids", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "bids": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["target_id"],
                            "properties": {
                                "target_id": {"type": "integer"},
                                "context_bid": {"type": "number", "description": "Bid in rubles"},
                            },
                        },
                    },
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # ─── VCard update ─────────────────────────────────────────────
        Tool(
            name="direct.hf.vcard_update",
            description="Update a VCard (business card).",
            inputSchema={
                "type": "object",
                "required": ["vcard_id", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "vcard_id": {"type": "integer"},
                    "company": {"type": "string"},
                    "phone_number": {"type": "string"},
                    "country_code": {"type": "string", "description": "Default: 7"},
                    "city_code": {"type": "string"},
                    "street": {"type": "string"},
                    "house": {"type": "string"},
                    "work_time": {"type": "string"},
                    "extra_message": {"type": "string"},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # ─── Sitelinks update ─────────────────────────────────────────
        Tool(
            name="direct.hf.sitelinks_update",
            description="Update a sitelinks set.",
            inputSchema={
                "type": "object",
                "required": ["sitelinks_set_id", "sitelinks", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "sitelinks_set_id": {"type": "integer"},
                    "sitelinks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["title", "href"],
                            "properties": {
                                "title": {"type": "string"},
                                "href": {"type": "string"},
                            },
                        },
                    },
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # ─── Video extension add ──────────────────────────────────────
        Tool(
            name="direct.hf.video_extension_add",
            description="Add a VIDEO_EXTENSION ad extension to a campaign.",
            inputSchema={
                "type": "object",
                "required": ["campaign_id", "creative_id", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "campaign_id": {"type": "integer"},
                    "creative_id": {"type": "integer"},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # ─── Card extensions ──────────────────────────────────────────
        Tool(
            name="direct.hf.card_extension_add",
            description="Add card extension (EXTENDED_TEXT) to a campaign.",
            inputSchema={
                "type": "object",
                "required": ["campaign_id", "cards", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "campaign_id": {"type": "integer"},
                    "cards": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["title", "href"],
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "href": {"type": "string"},
                                "price": {"type": "string"},
                            },
                        },
                    },
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        Tool(
            name="direct.hf.card_extension_delete",
            description="Delete card (EXTENDED_TEXT) extensions by IDs.",
            inputSchema={
                "type": "object",
                "required": ["extension_ids", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "extension_ids": {"type": "array", "items": {"type": "integer"}},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # ─── Client update (agency) ───────────────────────────────────
        Tool(
            name="direct.hf.client_update",
            description="Update client info (agency operation). Requires agency access.",
            inputSchema={
                "type": "object",
                "required": ["client_id", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "client_id": {"type": "integer"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # ─── Turbo pages ──────────────────────────────────────────────
        Tool(
            name="direct.hf.turbo_pages_list",
            description="List turbo landing pages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "campaign_id": {"type": "integer"},
                    "limit": {"type": "integer", "description": "Page size (default: 50)"},
                    "offset": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="direct.hf.turbo_page_get",
            description="Get a single turbo landing page by ID.",
            inputSchema={
                "type": "object",
                "required": ["page_id"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "page_id": {"type": "integer"},
                },
            },
        ),
        # ─── Video presets ────────────────────────────────────────────
        Tool(
            name="direct.hf.video_presets",
            description="Get video presets (supported formats, sizes).",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # ─── Retargeting lists update ─────────────────────────────────
        Tool(
            name="direct.hf.retargeting_lists_update",
            description="Update a retargeting/audience list.",
            inputSchema={
                "type": "object",
                "required": ["id", "apply"],
                "properties": {
                    "account_id": {"type": "string", **ACCOUNT_ID_SCHEMA_BASE},
                    "direct_client_login": DIRECT_CLIENT_LOGIN_SCHEMA_BASE,
                    "id": {"type": "integer", "description": "Retargeting list ID"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "rules": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["operator", "goals"],
                            "properties": {
                                "operator": {"type": "string", "enum": ["ALL", "ANY", "NONE"]},
                                "goals": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["goal_id"],
                                        "properties": {
                                            "goal_id": {"type": "integer"},
                                            "membership_life_span": {"type": "integer"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                    "dry_run": {"type": "boolean"},
                    "apply": {"type": "boolean"},
                },
            },
        ),
        # ═══ Webmaster tools ════════════════════════════════════════════
        Tool(
            name="webmaster.hf.user_info",
            description="Get current Yandex Webmaster user info (user_id, login).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="webmaster.hf.hosts_list",
            description="List all verified and unverified hosts/sites in Webmaster.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Webmaster user id (optional, auto-fetched)"},
                    "page": {"type": "integer", "description": "Page number (default: 0)"},
                    "per_page": {"type": "integer", "description": "Per page (default: 50)"},
                },
            },
        ),
        Tool(
            name="webmaster.hf.host_info",
            description="Get details about a specific host/site in Webmaster.",
            inputSchema={
                "type": "object",
                "required": ["host_id"],
                "properties": {
                    "user_id": {"type": "string"},
                    "host_id": {"type": "string", "description": "Host ID (e.g. 'example.com:https')"},
                },
            },
        ),
        Tool(
            name="webmaster.hf.host_add",
            description="Add a new host/site to Webmaster.",
            inputSchema={
                "type": "object",
                "required": ["host_url"],
                "properties": {
                    "user_id": {"type": "string"},
                    "host_url": {"type": "string", "description": "Full URL (e.g. 'https://example.com')"},
                },
            },
        ),
        Tool(
            name="webmaster.hf.host_verification",
            description="Get verification status for a host.",
            inputSchema={
                "type": "object",
                "required": ["host_id"],
                "properties": {
                    "user_id": {"type": "string"},
                    "host_id": {"type": "string"},
                },
            },
        ),
        Tool(
            name="webmaster.hf.verification_uinna",
            description="Set verification uinna for a host.",
            inputSchema={
                "type": "object",
                "required": ["host_id", "uinna"],
                "properties": {
                    "user_id": {"type": "string"},
                    "host_id": {"type": "string"},
                    "uinna": {"type": "string", "description": "Verification uinna hash"},
                },
            },
        ),
        Tool(
            name="webmaster.hf.sitemaps_list",
            description="List sitemaps for a host.",
            inputSchema={
                "type": "object",
                "required": ["host_id"],
                "properties": {
                    "user_id": {"type": "string"},
                    "host_id": {"type": "string"},
                },
            },
        ),
        Tool(
            name="webmaster.hf.sitemap_add",
            description="Add a sitemap URL for a host.",
            inputSchema={
                "type": "object",
                "required": ["host_id", "sitemap_url"],
                "properties": {
                    "user_id": {"type": "string"},
                    "host_id": {"type": "string"},
                    "sitemap_url": {"type": "string", "description": "Full sitemap URL"},
                },
            },
        ),
        Tool(
            name="webmaster.hf.sitemap_remove",
            description="Remove a sitemap from a host.",
            inputSchema={
                "type": "object",
                "required": ["host_id", "sitemap_id"],
                "properties": {
                    "user_id": {"type": "string"},
                    "host_id": {"type": "string"},
                    "sitemap_id": {"type": "string", "description": "Sitemap ID"},
                },
            },
        ),
        Tool(
            name="webmaster.hf.external_links",
            description="Get external links for a host.",
            inputSchema={
                "type": "object",
                "required": ["host_id"],
                "properties": {
                    "user_id": {"type": "string"},
                    "host_id": {"type": "string"},
                },
            },
        ),
        Tool(
            name="webmaster.hf.search_queries",
            description="Get popular search queries for a host (or specific query detail if query_id provided).",
            inputSchema={
                "type": "object",
                "required": ["host_id"],
                "properties": {
                    "user_id": {"type": "string"},
                    "host_id": {"type": "string"},
                    "query_id": {"type": "string", "description": "Optional: get detail for specific query"},
                },
            },
        ),
        Tool(
            name="webmaster.hf.host_summary",
            description="Get host summary (indexing stats, TIC, site quality).",
            inputSchema={
                "type": "object",
                "required": ["host_id"],
                "properties": {
                    "user_id": {"type": "string"},
                    "host_id": {"type": "string"},
                },
            },
        ),
    ]


def tool_definitions(config: AppConfig | None = None) -> list[Tool]:
    base = [
        Tool(
            name="dashboard.generate_option1",
            description="Generate a simple HTML+JSON dashboard from Direct+Metrica data (Option 1).",
            inputSchema={
                "type": "object",
                "required": ["date_from", "date_to"],
                "properties": {
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD."},
                    "all_accounts": {
                        "type": "boolean",
                        "description": "When true, generate one dashboard containing data for all configured account profiles (account switcher in UI).",
                    },
                    "account_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional explicit list of account profile ids to include in a multi-account dashboard.",
                    },
                    "counter_id": {"type": "string", "description": "Metrica counter id (optional if account profile has exactly one)."},
                    "goal_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional Metrica goal IDs. When set, dashboard will include leads based on goal{ID}reaches (best effort).",
                    },
                    "dashboard_slug": {"type": "string", "description": "Optional suffix for output file names."},
                    "output_dir": {"type": "string", "description": "When set, write HTML+JSON files to this directory."},
                    "include_raw_reports": {"type": "boolean", "description": "Include raw Direct/Metrica payloads in output data (default: true)."},
                    "include_wordstat": {"type": "boolean", "description": "Include Wordstat suggestions block (default: false)."},
                    "include_audience": {"type": "boolean", "description": "Include Audience segments blocks (default: false)."},
                    "wordstat_max_campaigns": {"type": "integer", "description": "Max campaigns to analyze with Wordstat (default: 5)."},
                    "wordstat_max_seed_phrases_per_campaign": {"type": "integer", "description": "Max seed phrases per campaign (default: 3)."},
                    "wordstat_num_phrases": {"type": "integer", "description": "Wordstat numPhrases (default: 50, max: 2000)."},
                    "wordstat_max_candidates_per_campaign": {"type": "integer", "description": "Max Wordstat candidates per campaign (default: 20)."},
                    "wordstat_max_negatives_per_campaign": {"type": "integer", "description": "Max negative tokens per campaign (default: 25)."},
                    "wordstat_language": {"type": "string", "description": "Negative lexicon language ru|en (default: ru)."},
                    "wordstat_regions": {"type": "array", "items": {"type": "integer"}, "description": "Optional Wordstat region ids."},
                    "wordstat_devices": {"type": "array", "items": {"type": "string"}, "description": "Optional Wordstat devices filter."},
                    "include_html": {"type": "boolean", "description": "Include HTML content in response (default: true if output_dir is not set)."},
                    "return_data": {
                        "type": "boolean",
                        "description": "Return the full data payload in response (default: false if output_dir is set, otherwise true).",
                    },
                },
            },
        ),
        Tool(
            name="accounts.list",
            description="List configured project profiles from the accounts registry file.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="accounts.reload",
            description="Reload accounts registry from disk (updates server cache).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="accounts.upsert",
            description="Create or update a project profile in the accounts registry file.",
            inputSchema={
                "type": "object",
                "required": ["account_id"],
                "properties": {
                    "account_id": {"type": "string", "description": "Profile id (stable, human-friendly)."},
                    "name": {"type": "string", "description": "Optional display name."},
                    "direct_client_login": {
                        "type": "string",
                        "description": "Direct Client-Login for this project (agency child account login).",
                    },
                    "metrica_counter_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional default Metrica counter ids for this project.",
                    },
                    "replace": {
                        "type": "boolean",
                        "description": "When true, replace the whole profile; when false, patch existing fields.",
                    },
                },
            },
        ),
        Tool(
            name="accounts.delete",
            description="Delete a project profile from the accounts registry file.",
            inputSchema={
                "type": "object",
                "required": ["account_id"],
                "properties": {"account_id": {"type": "string", "description": "Profile id to delete."}},
            },
        ),
        Tool(
            name="auth.start",
            description="Pro-only: build OAuth authorize URL (no token storage).",
            inputSchema={
                "type": "object",
                "properties": {
                    "purpose": {"type": "string", "description": "direct_metrica | audience | wordstat."},
                    "client_id": {"type": "string", "description": "Optional override; defaults to env for given purpose."},
                    "redirect_uri": {"type": "string", "description": "Optional override; defaults to env for given purpose."},
                    "scopes": {"type": "array", "items": {"type": "string"}, "description": "Optional override; defaults to env for given purpose."},
                },
            },
        ),
        Tool(
            name="auth.exchange_code",
            description="Pro-only: exchange OAuth code for tokens (returns secrets; no storage).",
            inputSchema={
                "type": "object",
                "required": ["purpose", "code"],
                "properties": {
                    "purpose": {"type": "string", "description": "direct_metrica | audience | wordstat."},
                    "code": {"type": "string"},
                    "client_id": {"type": "string"},
                    "client_secret": {"type": "string"},
                    "redirect_uri": {"type": "string"},
                },
            },
        ),
        Tool(
            name="write.confirm",
            description="Pro-only: confirm and execute a planned write operation (two-phase writes).",
            inputSchema={
                "type": "object",
                "required": ["confirm_token"],
                "properties": {"confirm_token": {"type": "string"}},
            },
        ),
        Tool(
            name="direct.list_campaigns",
            description="List campaigns from Yandex Direct.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selection_criteria": {
                        "type": "object",
                        "description": "Direct API SelectionCriteria object (optional).",
                    },
                    "field_names": {
                        "type": "array",
                        "description": "Campaign field names (default: Id, Name).",
                        "items": {"type": "string"},
                    },
                    "text_campaign_field_names": {
                        "type": "array",
                        "description": "TextCampaignFieldNames (optional).",
                        "items": {"type": "string"},
                    },
                    "mobile_app_campaign_field_names": {
                        "type": "array",
                        "description": "MobileAppCampaignFieldNames (optional).",
                        "items": {"type": "string"},
                    },
                    "dynamic_text_campaign_field_names": {
                        "type": "array",
                        "description": "DynamicTextCampaignFieldNames (optional).",
                        "items": {"type": "string"},
                    },
                    "cpm_banner_campaign_field_names": {
                        "type": "array",
                        "description": "CpmBannerCampaignFieldNames (optional).",
                        "items": {"type": "string"},
                    },
                    "smart_campaign_field_names": {
                        "type": "array",
                        "description": "SmartCampaignFieldNames (optional).",
                        "items": {"type": "string"},
                    },
                    "page": {
                        "type": "object",
                        "description": "Pagination: {\"limit\": int, \"offset\": int}.",
                        "properties": {
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                        },
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.list_adgroups",
            description="List ad groups from Yandex Direct.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selection_criteria": {
                        "type": "object",
                        "description": "Direct API SelectionCriteria object (optional).",
                    },
                    "field_names": {
                        "type": "array",
                        "description": "Ad group field names (default: Id, Name).",
                        "items": {"type": "string"},
                    },
                    "page": {
                        "type": "object",
                        "description": "Pagination: {\"limit\": int, \"offset\": int}.",
                        "properties": {
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                        },
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.list_ads",
            description="List ads from Yandex Direct.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selection_criteria": {
                        "type": "object",
                        "description": "Direct API SelectionCriteria object (optional).",
                    },
                    "field_names": {
                        "type": "array",
                        "description": "Ad field names (default: Id, AdGroupId).",
                        "items": {"type": "string"},
                    },
                    "page": {
                        "type": "object",
                        "description": "Pagination: {\"limit\": int, \"offset\": int}.",
                        "properties": {
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                        },
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.list_keywords",
            description="List keywords from Yandex Direct.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selection_criteria": {
                        "type": "object",
                        "description": "Direct API SelectionCriteria object (optional).",
                    },
                    "field_names": {
                        "type": "array",
                        "description": "Keyword field names (default: Id, Keyword).",
                        "items": {"type": "string"},
                    },
                    "page": {
                        "type": "object",
                        "description": "Pagination: {\"limit\": int, \"offset\": int}.",
                        "properties": {
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                        },
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.create_campaigns",
            description="Create campaigns in Yandex Direct.",
            inputSchema={
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Campaign objects to create.",
                        "items": {"type": "object"},
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.update_campaigns",
            description="Update campaigns in Yandex Direct.",
            inputSchema={
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Campaign objects to update (must include Id).",
                        "items": {"type": "object"},
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.create_adgroups",
            description="Create ad groups in Yandex Direct.",
            inputSchema={
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Ad group objects to create.",
                        "items": {"type": "object"},
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.update_adgroups",
            description="Update ad groups in Yandex Direct.",
            inputSchema={
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Ad group objects to update (must include Id).",
                        "items": {"type": "object"},
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.create_ads",
            description="Create ads in Yandex Direct.",
            inputSchema={
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Ad objects to create.",
                        "items": {"type": "object"},
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.update_ads",
            description="Update ads in Yandex Direct.",
            inputSchema={
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Ad objects to update (must include Id).",
                        "items": {"type": "object"},
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.create_keywords",
            description="Create keywords in Yandex Direct.",
            inputSchema={
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Keyword objects to create.",
                        "items": {"type": "object"},
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.update_keywords",
            description="Update keywords in Yandex Direct.",
            inputSchema={
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Keyword objects to update (must include Id).",
                        "items": {"type": "object"},
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.report",
            description="Run a Direct report (raw output).",
            inputSchema={
                "type": "object",
                "required": ["field_names", "report_type"],
                "properties": {
                    "selection_criteria": {
                        "type": "object",
                        "description": "Direct report SelectionCriteria (optional).",
                    },
                    "field_names": {
                        "type": "array",
                        "description": "Report fields (required by Direct API).",
                        "items": {"type": "string"},
                    },
                    "order_by": {
                        "type": "array",
                        "description": "OrderBy array for reports.",
                        "items": {"type": "object"},
                    },
                    "report_name": {"type": "string"},
                    "report_type": {"type": "string"},
                    "date_range_type": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "format": {"type": "string"},
                    "include_vat": {"type": "string"},
                    "include_discount": {"type": "string"},
                    "goals": {"type": "array", "items": {"type": "string"}},
                    "attribution_models": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct report params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.list_clients",
            description="List Direct clients (agency use).",
            inputSchema={
                "type": "object",
                "properties": {
                    "field_names": {
                        "type": "array",
                        "description": "Client field names (default: ClientId, Login).",
                        "items": {"type": "string"},
                    },
                    "page": {
                        "type": "object",
                        "description": "Pagination: {\"limit\": int, \"offset\": int}.",
                        "properties": {
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                        },
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.list_dictionaries",
            description="Get Direct dictionaries.",
            inputSchema={
                "type": "object",
                "required": ["dictionary_names"],
                "properties": {
                    "dictionary_names": {
                        "type": "array",
                        "description": "Dictionary names to fetch (required by API).",
                        "items": {"type": "string"},
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.get_changes",
            description="Get changes since a given timestamp.",
            inputSchema={
                "type": "object",
                "required": ["timestamp"],
                "properties": {
                    "timestamp": {
                        "type": "string",
                        "description": "Timestamp string as required by Direct Changes.checkCampaigns.",
                    },
                    "field_names": {
                        "type": "array",
                        "description": "Fields for changes response (optional).",
                        "items": {"type": "string"},
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.list_sitelinks",
            description="List sitelinks sets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "description": "Sitelinks set Ids (required unless using params override).",
                        "items": {"type": "integer"},
                    },
                    "selection_criteria": {
                        "type": "object",
                        "description": "Direct API SelectionCriteria object (optional).",
                    },
                    "field_names": {
                        "type": "array",
                        "description": "Sitelinks field names (default: Id, Sitelinks).",
                        "items": {"type": "string"},
                    },
                    "page": {
                        "type": "object",
                        "description": "Pagination: {\"limit\": int, \"offset\": int}.",
                        "properties": {
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                        },
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.list_vcards",
            description="List vCards.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "description": "vCard Ids (required unless using params override).",
                        "items": {"type": "integer"},
                    },
                    "selection_criteria": {
                        "type": "object",
                        "description": "Direct API SelectionCriteria object (optional).",
                    },
                    "field_names": {
                        "type": "array",
                        "description": "VCard field names (default: Id).",
                        "items": {"type": "string"},
                    },
                    "page": {
                        "type": "object",
                        "description": "Pagination: {\"limit\": int, \"offset\": int}.",
                        "properties": {
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                        },
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.list_adextensions",
            description="List ad extensions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selection_criteria": {
                        "type": "object",
                        "description": "Direct API SelectionCriteria object (optional).",
                    },
                    "field_names": {
                        "type": "array",
                        "description": "Ad extension field names (default: Id).",
                        "items": {"type": "string"},
                    },
                    "page": {
                        "type": "object",
                        "description": "Pagination: {\"limit\": int, \"offset\": int}.",
                        "properties": {
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                        },
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.list_bids",
            description="List bids.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selection_criteria": {
                        "type": "object",
                        "description": "Direct API SelectionCriteria object (optional).",
                    },
                    "field_names": {
                        "type": "array",
                        "description": "Bid field names (default: CampaignId, KeywordId).",
                        "items": {"type": "string"},
                    },
                    "page": {
                        "type": "object",
                        "description": "Pagination: {\"limit\": int, \"offset\": int}.",
                        "properties": {
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                        },
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.list_bidmodifiers",
            description="List bid modifiers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selection_criteria": {
                        "type": "object",
                        "description": "Direct API SelectionCriteria object (optional).",
                    },
                    "field_names": {
                        "type": "array",
                        "description": "Bid modifier field names (default: CampaignId).",
                        "items": {"type": "string"},
                    },
                    "page": {
                        "type": "object",
                        "description": "Pagination: {\"limit\": int, \"offset\": int}.",
                        "properties": {
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                        },
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Direct params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="direct.raw_call",
            description="Raw Direct API call (escape hatch).",
            inputSchema={
                "type": "object",
                "required": ["resource"],
                "properties": {
                    "resource": {
                        "type": "string",
                        "description": "Direct resource name, e.g. campaigns, ads.",
                    },
                    "method": {
                        "type": "string",
                        "description": "Direct API method, e.g. get, add, update.",
                    },
                    "params": {
                        "type": "object",
                        "description": "Direct API params payload.",
                    },
                },
            },
        ),
        Tool(
            name="metrica.list_counters",
            description="List available Metrica counters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "params": {
                        "type": "object",
                        "description": "Raw Metrica management params override (optional).",
                    }
                },
            },
        ),
        Tool(
            name="metrica.report",
            description="Run a Metrica report (raw output).",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "metrics"],
                "properties": {
                    "counter_id": {
                        "type": "string",
                        "description": "Metrica counter ID (required).",
                    },
                    "metrics": {
                        "type": "string",
                        "description": "Metrics string, e.g. ym:s:visits.",
                    },
                    "dimensions": {
                        "type": "string",
                        "description": "Dimensions string, e.g. ym:s:date.",
                    },
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "filters": {"type": "string"},
                    "sort": {"type": "string"},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"},
                    "accuracy": {"type": "string"},
                    "params": {
                        "type": "object",
                        "description": "Raw Metrica stats params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="metrica.counter_info",
            description="Get details of a Metrica counter.",
            inputSchema={
                "type": "object",
                "required": ["counter_id"],
                "properties": {
                    "counter_id": {
                        "type": "string",
                        "description": "Metrica counter ID (required).",
                    },
                    "params": {
                        "type": "object",
                        "description": "Raw Metrica management params override (optional).",
                    },
                },
            },
        ),
        Tool(
            name="metrica.logs_export",
            description="Logs API export (optional).",
            inputSchema={
                "type": "object",
                "required": ["counter_id"],
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Logs API action: allinfo, info, download, clean, cancel, create, evaluate.",
                    },
                    "counter_id": {"type": "string"},
                    "request_id": {"type": "string"},
                    "part_number": {"type": "integer"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "fields": {"type": "string"},
                    "source": {"type": "string"},
                    "params": {
                        "type": "object",
                        "description": "Raw Logs API params override (advanced).",
                    },
                },
            },
        ),
        Tool(
            name="metrica.raw_call",
            description="Raw Metrica API call (escape hatch).",
            inputSchema={
                "type": "object",
                "properties": {
                    "api": {
                        "type": "string",
                        "description": "Metrica API: stats, management, logs.",
                    },
                    "resource": {
                        "type": "string",
                        "description": "Management resource or logs action.",
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method: get, post, put, delete.",
                    },
                    "path_args": {
                        "type": "object",
                        "description": "Path args for resource (e.g., counterId).",
                    },
                    "params": {
                        "type": "object",
                        "description": "Query/body params for the request.",
                    },
                    "data": {
                        "type": "object",
                        "description": "Request body for management API (create/update).",
                    },
                },
            },
        ),
        # Metrica goals (raw)
        Tool(
            name="metrica.goals.list",
            description="Metrica: list goals for a counter.",
            inputSchema={
                "type": "object",
                "required": ["counter_id"],
                "properties": {"counter_id": {"type": "string"}, "params": {"type": "object"}},
            },
        ),
        Tool(
            name="metrica.goals.get",
            description="Metrica: get goal by id.",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "goal_id"],
                "properties": {"counter_id": {"type": "string"}, "goal_id": {"type": "string"}, "params": {"type": "object"}},
            },
        ),
        Tool(
            name="metrica.goals.create",
            description="Metrica: create goal (pro-only).",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "payload"],
                "properties": {"counter_id": {"type": "string"}, "payload": {"type": "object"}},
            },
        ),
        Tool(
            name="metrica.goals.update",
            description="Metrica: update goal (pro-only).",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "goal_id", "payload"],
                "properties": {"counter_id": {"type": "string"}, "goal_id": {"type": "string"}, "payload": {"type": "object"}},
            },
        ),
        Tool(
            name="metrica.goals.delete",
            description="Metrica: delete goal (pro-only).",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "goal_id"],
                "properties": {"counter_id": {"type": "string"}, "goal_id": {"type": "string"}},
            },
        ),
        # Audience (raw, read-only)
        Tool(
            name="audience.user_info",
            description="Audience: user info (validate access).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="audience.segments.list",
            description="Audience: list segments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"},
                    "types": {"type": "array", "items": {"type": "string"}},
                    "statuses": {"type": "array", "items": {"type": "string"}},
                    "fields": {"type": "array", "items": {"type": "string"}},
                },
            },
        ),
        Tool(
            name="audience.segments.get",
            description="Audience: get segment by id.",
            inputSchema={
                "type": "object",
                "required": ["segment_id"],
                "properties": {"segment_id": {"type": "string"}, "fields": {"type": "array", "items": {"type": "string"}}},
            },
        ),
        Tool(
            name="audience.segments.stats",
            description="Audience: segment stats (size/status) (best effort).",
            inputSchema={
                "type": "object",
                "required": ["segment_id"],
                "properties": {"segment_id": {"type": "string"}, "fields": {"type": "array", "items": {"type": "string"}}},
            },
        ),
        Tool(
            name="audience.segments.overlap",
            description="Audience: overlap between segments (best effort).",
            inputSchema={
                "type": "object",
                "required": ["segment_ids"],
                "properties": {
                    "segment_ids": {"type": "array", "items": {"type": "string"}},
                    "mode": {"type": "string", "description": "matrix|top_pairs (default: top_pairs)."},
                    "limit": {"type": "integer", "description": "Default: 50."},
                },
            },
        ),
        Tool(
            name="audience.pixels.list",
            description="Audience: list pixels.",
            inputSchema={"type": "object", "properties": {"limit": {"type": "integer"}, "offset": {"type": "integer"}, "fields": {"type": "array", "items": {"type": "string"}}}},
        ),
        Tool(
            name="audience.pixels.get",
            description="Audience: get pixel by id.",
            inputSchema={"type": "object", "required": ["pixel_id"], "properties": {"pixel_id": {"type": "string"}, "fields": {"type": "array", "items": {"type": "string"}}}},
        ),
        Tool(
            name="audience.lookalikes.list",
            description="Audience: list lookalikes (best effort).",
            inputSchema={"type": "object", "properties": {"limit": {"type": "integer"}, "offset": {"type": "integer"}, "fields": {"type": "array", "items": {"type": "string"}}}},
        ),
        Tool(
            name="audience.lookalikes.get",
            description="Audience: get lookalike by id.",
            inputSchema={"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}, "fields": {"type": "array", "items": {"type": "string"}}}},
        ),
        # Audience (pro-only write + escape hatch)
        Tool(
            name="audience.segments.create",
            description="Audience: create segment (pro-only).",
            inputSchema={"type": "object", "required": ["payload"], "properties": {"payload": {"type": "object"}}},
        ),
        Tool(
            name="audience.segments.update",
            description="Audience: update segment (pro-only).",
            inputSchema={"type": "object", "required": ["segment_id", "payload"], "properties": {"segment_id": {"type": "string"}, "payload": {"type": "object"}}},
        ),
        Tool(
            name="audience.segments.delete",
            description="Audience: delete segment (pro-only).",
            inputSchema={"type": "object", "required": ["segment_id"], "properties": {"segment_id": {"type": "string"}}},
        ),
        Tool(
            name="audience.upload.start",
            description="Audience: start upload job (pro-only, may include PII).",
            inputSchema={"type": "object", "required": ["segment_id", "payload"], "properties": {"segment_id": {"type": "string"}, "payload": {"type": "object"}}},
        ),
        Tool(
            name="audience.upload.status",
            description="Audience: upload job status (pro-only).",
            inputSchema={"type": "object", "required": ["upload_id"], "properties": {"upload_id": {"type": "string"}}},
        ),
        Tool(
            name="audience.upload.errors",
            description="Audience: upload job errors (pro-only).",
            inputSchema={"type": "object", "required": ["upload_id"], "properties": {"upload_id": {"type": "string"}}},
        ),
        Tool(
            name="audience.raw_call",
            description="Audience: raw API call (escape hatch, pro-only).",
            inputSchema={
                "type": "object",
                "required": ["method", "path"],
                "properties": {
                    "method": {"type": "string", "description": "GET|POST|PUT|DELETE."},
                    "path": {"type": "string", "description": "Path under /v1/management (e.g., /segments)."},
                    "params": {"type": "object"},
                    "payload": {"type": "object"},
                },
            },
        ),
        Tool(
            name="wordstat.user_info",
            description="Wordstat: userInfo (access check).",
            inputSchema={"type": "object", "properties": {"params": {"type": "object"}}},
        ),
        Tool(
            name="wordstat.get_regions_tree",
            description="Wordstat: getRegionsTree (regions dictionary).",
            inputSchema={"type": "object", "properties": {"params": {"type": "object"}}},
        ),
        Tool(
            name="wordstat.top_requests",
            description="Wordstat: topRequests (top queries by phrase).",
            inputSchema={
                "type": "object",
                "properties": {
                    "phrase": {
                        "type": "string",
                        "description": "Provide either phrase or phrases (exactly one).",
                    },
                    "phrases": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Up to 128 phrases. Provide either phrase or phrases (exactly one).",
                    },
                    "regions": {"type": "array", "items": {"type": "integer"}},
                    "devices": {"type": "array", "items": {"type": "string"}},
                    "num_phrases": {"type": "integer", "description": "Max: 2000."},
                    "params": {"type": "object", "description": "Raw Wordstat payload override (advanced)."},
                },
            },
        ),
        Tool(
            name="wordstat.dynamics",
            description="Wordstat: dynamics (frequency dynamics by period).",
            inputSchema={
                "type": "object",
                "required": ["phrase", "from_date"],
                "properties": {
                    "phrase": {"type": "string"},
                    "from_date": {"type": "string", "description": "YYYY-MM (inclusive)."},
                    "to_date": {"type": "string", "description": "YYYY-MM (inclusive). Optional."},
                    "period": {"type": "string", "description": "monthly | weekly | daily (API-defined)."},
                    "regions": {"type": "array", "items": {"type": "integer"}},
                    "devices": {"type": "array", "items": {"type": "string"}},
                    "params": {"type": "object", "description": "Raw Wordstat payload override (advanced)."},
                },
            },
        ),
        Tool(
            name="wordstat.regions",
            description="Wordstat: regions (frequency by region).",
            inputSchema={
                "type": "object",
                "required": ["phrase"],
                "properties": {
                    "phrase": {"type": "string"},
                    "region_type": {"type": "string", "description": "cities | regions | all (API-defined)."},
                    "devices": {"type": "array", "items": {"type": "string"}},
                    "params": {"type": "object", "description": "Raw Wordstat payload override (advanced)."},
                },
            },
        ),
        # ──────────────────────────────────────────────────────
        # CDP Ingestion (загрузка заказов/контактов в Метрику)
        # ──────────────────────────────────────────────────────
        Tool(
            name="metrica.cdp.upload_simple_orders",
            description="CDP: upload simple orders (ClientID, OrderID, Status, Revenue, Cost). Dry-run aware.",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "rows"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                    "rows": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of order dicts with keys: client_id, order_id, status, revenue, cost, create_date, update_date.",
                    },
                    "auto_create_statuses": {"type": "boolean", "description": "Auto-create missing statuses (default: true)."},
                    "apply": {"type": "boolean", "description": "Set true to execute; false (default) for dry-run preview."},
                },
            },
        ),
        Tool(
            name="metrica.cdp.upload_contacts",
            description="CDP: upload contacts (email/phone → MD5-hashed). Dry-run aware.",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "rows"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                    "rows": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of contact dicts with keys: client_id, email, phone.",
                    },
                    "apply": {"type": "boolean", "description": "Set true to execute; false (default) for dry-run preview."},
                },
            },
        ),
        Tool(
            name="metrica.cdp.get_uploading_status",
            description="CDP: check status of a previous upload.",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "upload_id"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                    "upload_id": {"type": "string", "description": "Upload ID from upload_simple_orders / upload_contacts."},
                },
            },
        ),
        Tool(
            name="metrica.cdp.get_order_statuses",
            description="CDP: list all order statuses for a counter.",
            inputSchema={
                "type": "object",
                "required": ["counter_id"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                },
            },
        ),
        Tool(
            name="metrica.cdp.create_order_status",
            description="CDP: create a new order status. Dry-run aware.",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "name"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                    "name": {"type": "string", "description": "Status name."},
                    "is_closed": {"type": "boolean", "description": "Final status (completed/cancelled)."},
                    "apply": {"type": "boolean", "description": "Set true to execute; false (default) for dry-run preview."},
                },
            },
        ),
        Tool(
            name="metrica.cdp.get_attributes",
            description="CDP: list all user attributes for a counter.",
            inputSchema={
                "type": "object",
                "required": ["counter_id"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                },
            },
        ),
        Tool(
            name="metrica.cdp.create_attribute",
            description="CDP: create a user attribute. Dry-run aware.",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "name"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                    "name": {"type": "string", "description": "Attribute name."},
                    "type": {"type": "string", "description": "Attribute type: string | number | date (default: string)."},
                    "apply": {"type": "boolean", "description": "Set true to execute; false (default) for dry-run preview."},
                },
            },
        ),
        # ──────────────────────────────────────────────────────
        # CDP Analytics (воронки, когорты, атрибуция, revenue, ROI, аудит)
        # ──────────────────────────────────────────────────────
        Tool(
            name="metrica.analytics.funnel_report",
            description="CDP Analytics: funnel report — conversion steps (goals) → drop-offs at each step.",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "date_from", "date_to", "goal_ids"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD."},
                    "goal_ids": {"type": "array", "items": {"type": "string"}, "description": "Ordered list of goal IDs (funnel steps)."},
                },
            },
        ),
        Tool(
            name="metrica.analytics.cohort_report",
            description="CDP Analytics: cohort analysis — retention by period.",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "date_from", "date_to"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD."},
                    "granularity": {"type": "string", "description": "week | month (default: week)."},
                },
            },
        ),
        Tool(
            name="metrica.analytics.attribution_report",
            description="CDP Analytics: attribution by traffic sources.",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "date_from", "date_to"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD."},
                    "attribution": {"type": "string", "description": "Attribution model: lastsign (default) | firstsign | lastyandexdirect | firstyandexdirect | lastclick | firstclick | lastimpression | firstimpression."},
                },
            },
        ),
        Tool(
            name="metrica.analytics.revenue_report",
            description="CDP Analytics: revenue report from CDP/ecommerce data.",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "date_from", "date_to"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD."},
                    "granularity": {"type": "string", "description": "day | week | month (default: day)."},
                },
            },
        ),
        Tool(
            name="metrica.analytics.roi_report",
            description="CDP Analytics: ROI/ROMI + Profit report.",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "date_from", "date_to"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD."},
                    "granularity": {"type": "string", "description": "day | week | month (default: day)."},
                },
            },
        ),
        Tool(
            name="metrica.analytics.crm_match_report",
            description="CDP Analytics: CRM match — reconcile CRM orders vs Metrica data (find discrepancies).",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "date_from", "date_to"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD."},
                },
            },
        ),
        Tool(
            name="metrica.analytics.comprehensive_audit",
            description="CDP Analytics: comprehensive audit — funnel + LTV + attribution in one call.",
            inputSchema={
                "type": "object",
                "required": ["counter_id", "date_from", "date_to", "goal_ids"],
                "properties": {
                    "counter_id": {"type": "string", "description": "Metrica counter ID."},
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD."},
                    "goal_ids": {"type": "array", "items": {"type": "string"}, "description": "Ordered list of goal IDs for funnel."},
                },
            },
        ),
    ]

    hf = _hf_tools()
    base.extend(plugin_tools())

    # Pro-only feature-flagged tools: hide unless enabled.
    if config is None:
        base = [t for t in base if t.name not in {"auth.start", "auth.exchange_code", "write.confirm"}]
    else:
        if getattr(config, "public_readonly", False):
            base = [t for t in base if t.name not in {"auth.start", "auth.exchange_code", "write.confirm"}]
        else:
            if not getattr(config, "auth_tools_enabled", False):
                base = [t for t in base if t.name not in {"auth.start", "auth.exchange_code"}]
            if not getattr(config, "two_phase_writes_enabled", False):
                base = [t for t in base if t.name != "write.confirm"]
    # Public read-only mode: expose only read-oriented tools (hide write + escape hatches by default).
    if config is not None and getattr(config, "public_readonly", False):
        # Hide write-capable tools from the published schema. Server-side guardrail still blocks any attempts.
        hide_prefixes = ("direct.create_", "direct.update_")
        hide_exact = {
            "direct.raw_call",
            "metrica.raw_call",
            "audience.raw_call",
            "join.hf.direct_vs_metrica_by_yclid",
            "dashboard.schema",
            "dashboard.sync.start",
            "dashboard.sync.next",
            "accounts.upsert",
            "accounts.delete",
            "audience.segments.create",
            "audience.segments.update",
            "audience.segments.delete",
            "audience.upload.start",
            "audience.upload.status",
            "audience.upload.errors",
            "metrica.goals.create",
            "metrica.goals.update",
            "metrica.goals.delete",
            "metrica.cdp.upload_simple_orders",
            "metrica.cdp.upload_contacts",
            "metrica.cdp.create_order_status",
            "metrica.cdp.create_attribute",
            "audience.lookalikes.list",
            "audience.lookalikes.get",
            "auth.start",
            "auth.exchange_code",
            "write.confirm",
        }
        base = [
            t
            for t in base
            if not t.name.startswith(hide_prefixes)
            and t.name not in hide_exact
            and not t.name.startswith("dashboard.dataset.")
        ]
        # Keep only read-oriented HF tools (find/get/report). Write HF tools remain available in pro builds.
        allowed_hf_prefixes = ("direct.hf.find_", "direct.hf.get_", "direct.hf.report_")
        allowed_hf_exact = {"direct.hf.get_bids_summary", "direct.hf.pressure_report"}
        hf = [
            t
            for t in hf
            if not t.name.startswith("direct.hf.")
            or t.name.startswith(allowed_hf_prefixes)
            or t.name in allowed_hf_exact
        ]
        # Join helpers: keep only pure read-only joins in public mode.
        hf = [t for t in hf if t.name != "join.hf.direct_vs_metrica_by_yclid"]
        hf = [t for t in hf if not t.name.startswith("audience.hf.apply_")]
        hf = [t for t in hf if not t.name.startswith("metrica.hf.") or t.name.startswith("metrica.hf.report_") or t.name in {"metrica.hf.list_accessible_counters", "metrica.hf.counter_summary", "metrica.hf.logs_export_preset"}]

    direct_client_logins: list[str] = []
    if config is not None:
        # Provide helpful hints, but never hard-restrict values via enum (agency setups may have many logins).
        if getattr(config, "direct_client_logins", None):
            direct_client_logins.extend([str(x) for x in (config.direct_client_logins or []) if str(x).strip()])
        if getattr(config, "accounts", None):
            for profile in (config.accounts or {}).values():
                login = getattr(profile, "direct_client_login", None)
                if login and str(login).strip():
                    direct_client_logins.append(str(login).strip())
    direct_client_logins = sorted({x for x in direct_client_logins if x})

    account_ids: list[str] = []
    if config is not None and getattr(config, "accounts", None):
        account_ids = sorted([str(x) for x in (config.accounts or {}).keys() if str(x).strip()])

    def _inject_account_and_overrides(tools: list[Tool]) -> list[Tool]:
        for tool in tools:
            is_direct_or_join = tool.name.startswith(("direct.", "join.hf."))
            is_metrica = tool.name.startswith("metrica.")
            is_dashboard = tool.name.startswith("dashboard.")
            is_audience_hf = tool.name.startswith("audience.hf.")
            if not (is_direct_or_join or is_metrica or is_dashboard or is_audience_hf):
                continue
            schema = tool.inputSchema or {"type": "object"}
            if not isinstance(schema, dict):
                continue
            props = schema.setdefault("properties", {})
            if isinstance(props, dict):
                # Allow any string, but provide an enum hint when we have known ids.
                if account_ids:
                    account_id_schema = {
                        "anyOf": [
                            {"type": "string", "enum": account_ids},
                            {"type": "string"},
                        ],
                        **ACCOUNT_ID_SCHEMA_BASE,
                    }
                else:
                    account_id_schema = {"type": "string", **ACCOUNT_ID_SCHEMA_BASE}
                props.setdefault("account_id", account_id_schema)
                if account_ids and isinstance(props.get("account_ids"), dict):
                    # Multi-account dashboards: suggest known ids, but don't enforce (users may have more).
                    items_schema = {
                        "anyOf": [
                            {"type": "string", "enum": account_ids},
                            {"type": "string"},
                        ],
                    }
                    try:
                        props["account_ids"].setdefault("items", items_schema)
                    except Exception:
                        pass

                if is_direct_or_join or is_dashboard or is_audience_hf:
                    direct_client_login_schema = dict(DIRECT_CLIENT_LOGIN_SCHEMA_BASE)
                    if direct_client_logins:
                        max_hint = 25
                        hinted = direct_client_logins[:max_hint]
                        suffix = ", …" if len(direct_client_logins) > max_hint else ""
                        hint = f" Known values: {', '.join(hinted)}{suffix}."
                        direct_client_login_schema["description"] = (direct_client_login_schema.get("description") or "").rstrip(".") + "." + hint
                    props.setdefault("direct_client_login", direct_client_login_schema)
            tool.inputSchema = schema
        return tools

    if config is None:
        tools = _inject_account_and_overrides(base + hf)
        return [decorate_tool(tool) for tool in tools]
    if not config.hf_enabled:
        tools = _inject_account_and_overrides(base)
        return [decorate_tool(tool) for tool in tools]
    if not config.hf_destructive_enabled:
        hf = [t for t in hf if t.name not in HF_DESTRUCTIVE_TOOLS]
    tools = _inject_account_and_overrides(base + hf)
    return [decorate_tool(tool) for tool in tools]
