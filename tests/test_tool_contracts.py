from __future__ import annotations

from typing import Any

from mcp_yandex_ad.config import AppConfig
from mcp_yandex_ad.tool_contracts import prioritized_contract_tools
from mcp_yandex_ad.tools import tool_definitions


def _config(**overrides: Any) -> AppConfig:
    data = dict(
        access_token="token",
        refresh_token=None,
        client_id=None,
        client_secret=None,
        audience_access_token=None,
        audience_refresh_token=None,
        audience_client_id=None,
        audience_client_secret=None,
        wordstat_access_token=None,
        wordstat_refresh_token=None,
        wordstat_client_id=None,
        wordstat_client_secret=None,
        direct_client_login=None,
        direct_client_logins=[],
        direct_api_version="v5",
        metrica_counter_ids=[],
        audience_enabled=True,
        wordstat_enabled=True,
        use_sandbox=False,
        write_enabled=False,
        write_sandbox_only=True,
        hf_enabled=True,
        hf_write_enabled=False,
        hf_destructive_enabled=False,
        cache_enabled=True,
        cache_ttl_seconds=300,
        direct_rate_limit_rps=0,
        metrica_rate_limit_rps=0,
        audience_rate_limit_rps=0,
        wordstat_rate_limit_rps=0,
        retry_max_attempts=3,
        retry_base_delay_seconds=0.5,
        retry_max_delay_seconds=8.0,
        content_mode="json",
        public_readonly=True,
        accounts_write_enabled=False,
        accounts_file=None,
        accounts={},
    )
    data.update(overrides)
    return AppConfig(**data)


def test_tool_contracts_expose_output_schema_for_prioritized_tools() -> None:
    tools = {tool.name: tool for tool in tool_definitions(_config())}

    for tool_name in prioritized_contract_tools():
        assert tools[tool_name].outputSchema is not None, tool_name


def test_tool_contracts_mark_read_only_intent() -> None:
    tools = {tool.name: tool for tool in tool_definitions(_config())}

    assert tools["accounts.list"].annotations is not None
    assert tools["accounts.list"].annotations.readOnlyHint is True
    assert tools["dashboard.generate_option1"].annotations is not None
    assert tools["dashboard.generate_option1"].annotations.readOnlyHint is False
    assert tools["direct.hf.find_campaigns"].annotations is not None
    assert tools["direct.hf.find_campaigns"].annotations.readOnlyHint is True
    assert tools["join.hf.direct_vs_metrica_by_utm"].annotations is not None
    assert tools["join.hf.direct_vs_metrica_by_utm"].annotations.readOnlyHint is True


def test_tool_contracts_include_hf_error_shape() -> None:
    tools = {tool.name: tool for tool in tool_definitions(_config())}

    schema = tools["direct.hf.find_campaigns"].outputSchema
    assert schema is not None
    error_props = schema["properties"]["error"]["properties"]
    assert error_props["code"]["type"] == "string"
    assert error_props["retryable"]["type"] == "boolean"


def test_tool_contracts_do_not_expand_unscoped_tools() -> None:
    tools = {tool.name: tool for tool in tool_definitions(_config())}

    assert tools["direct.list_campaigns"].outputSchema is None
    assert tools["metrica.logs_export"].outputSchema is None
