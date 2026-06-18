import json
from pathlib import Path
from typing import Any

from mcp_yandex_ad.config import AppConfig
from mcp_yandex_ad.tool_contracts import prioritized_contract_tools
from mcp_yandex_ad.tools import tool_definitions


def _config_public(**overrides: Any) -> AppConfig:
    data: dict[str, Any] = dict(
        access_token="token",
        refresh_token=None,
        client_id=None,
        client_secret=None,
        audience_access_token=None,
        audience_refresh_token=None,
        audience_client_id=None,
        audience_client_secret=None,
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


def _deep_sort(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _deep_sort(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [_deep_sort(x) for x in value]
    return value


def test_public_tool_contract_snapshot_is_stable():
    tools = {tool.name: tool for tool in tool_definitions(_config_public())}
    snapshot = []
    for name in sorted(prioritized_contract_tools()):
        tool = tools[name]
        snapshot.append(
            {
                "name": tool.name,
                "annotations": _deep_sort(tool.annotations.model_dump(exclude_none=True) if tool.annotations else {}),
                "outputSchema": _deep_sort(tool.outputSchema or {}),
            }
        )

    snap_path = Path(__file__).resolve().parent / "snapshots" / "public_tool_contracts_v1.json"
    expected = json.loads(snap_path.read_text(encoding="utf-8"))

    assert snapshot == expected
