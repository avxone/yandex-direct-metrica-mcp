from __future__ import annotations

from mcp_yandex_ad.tool_bundles import bundle_definitions, bundle_manifest_schema, get_bundle_manifest


def test_bundle_manifest_schema_is_explicit() -> None:
    schema = bundle_manifest_schema()

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == [
        "bundle_id",
        "title",
        "intended_for",
        "recommended_tools",
        "preferred_entrypoints",
        "excluded_tools",
        "notes",
    ]


def test_bundle_definitions_are_static() -> None:
    bundles = bundle_definitions()

    assert list(bundles.keys()) == ["marketing2025.analyst_pipeline"]
    manifest = bundles["marketing2025.analyst_pipeline"]
    assert manifest["preferred_entrypoints"][0] == "accounts.list"
    assert "dashboard.generate_option1" in manifest["recommended_tools"]
    assert "join.hf.direct_vs_metrica_by_yclid" in manifest["excluded_tools"]


def test_get_bundle_manifest_returns_copy() -> None:
    manifest = get_bundle_manifest("marketing2025.analyst_pipeline")
    manifest["notes"].append("mutated")

    fresh = get_bundle_manifest("marketing2025.analyst_pipeline")
    assert "mutated" not in fresh["notes"]


def test_get_bundle_manifest_rejects_unknown_bundle_id() -> None:
    try:
        get_bundle_manifest("unknown.bundle")
    except ValueError as exc:
        assert str(exc) == "Unknown bundle_id: unknown.bundle"
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected ValueError for unknown bundle id")
