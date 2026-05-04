"""Static role/bundle manifest definitions for backend-side discovery contracts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def bundle_manifest_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": [
            "bundle_id",
            "title",
            "intended_for",
            "recommended_tools",
            "preferred_entrypoints",
            "excluded_tools",
            "notes",
        ],
        "properties": {
            "bundle_id": {"type": "string"},
            "title": {"type": "string"},
            "intended_for": {"type": "array", "items": {"type": "string"}},
            "recommended_tools": {"type": "array", "items": {"type": "string"}},
            "preferred_entrypoints": {"type": "array", "items": {"type": "string"}},
            "excluded_tools": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": False,
    }


def bundle_definitions() -> dict[str, dict[str, Any]]:
    return {
        "marketing2025.analyst_pipeline": {
            "bundle_id": "marketing2025.analyst_pipeline",
            "title": "Marketing2025 Analyst + Pipeline",
            "intended_for": [
                "Marketing2025",
                "Analyst",
                "Pipeline evaluation",
            ],
            "recommended_tools": [
                "accounts.list",
                "dashboard.generate_option1",
                "direct.hf.find_campaigns",
                "direct.hf.find_adgroups",
                "direct.hf.find_ads",
                "direct.hf.find_keywords",
                "direct.hf.get_campaign_summary",
                "direct.hf.get_bids_summary",
                "direct.hf.pressure_report",
                "direct.hf.report_performance",
                "direct.hf.report_keywords",
                "direct.hf.report_ads",
                "direct.hf.report_adgroups",
                "direct.hf.report_search_phrases",
                "metrica.hf.list_accessible_counters",
                "metrica.hf.counter_summary",
                "metrica.hf.report_time_series",
                "metrica.hf.report_landing_pages",
                "metrica.hf.report_utm_campaigns",
                "metrica.hf.report_geo",
                "metrica.hf.report_devices",
                "join.hf.direct_vs_metrica_by_utm",
            ],
            "preferred_entrypoints": [
                "accounts.list",
                "dashboard.generate_option1",
                "direct.hf.get_campaign_summary",
                "direct.hf.report_performance",
                "metrica.hf.report_time_series",
                "join.hf.direct_vs_metrica_by_utm",
            ],
            "excluded_tools": [
                "direct.raw_call",
                "metrica.raw_call",
                "join.hf.direct_vs_metrica_by_yclid",
                "direct.create_campaigns",
                "direct.update_campaigns",
                "metrica.goals.create",
                "metrica.goals.update",
                "metrica.goals.delete",
            ],
            "notes": [
                "Provisional backend bundle until Marketing2025 ships measured inventory input.",
                "Read-heavy scope only; excludes write paths and logs-export-dependent joins.",
                "Keeps runtime MCP surface unchanged for now; this manifest is backend-internal contract preparation.",
            ],
        }
    }


def get_bundle_manifest(bundle_id: str) -> dict[str, Any]:
    manifests = bundle_definitions()
    if bundle_id not in manifests:
        raise ValueError(f"Unknown bundle_id: {bundle_id}")
    return deepcopy(manifests[bundle_id])
