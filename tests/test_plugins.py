import importlib


def test_plugins_can_register_tools_via_env(monkeypatch, tmp_path):
    plugin = tmp_path / "dummy_plugin.py"
    plugin.write_text(
        "\n".join(
            [
                "from mcp.types import Tool",
                "",
                "def register(registry):",
                "    registry.add_tools([Tool(name='x.hello', description='dummy', inputSchema={'type':'object','properties':{}})])",
                "    registry.add_tool_handler('x.hello', lambda _ctx, _args: {'result': {'ok': True}})",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv("MCP_PLUGIN_MODULES", "dummy_plugin:register")

    import mcp_yandex_ad.plugins as plugins

    importlib.reload(plugins)

    from mcp_yandex_ad.tools import tool_definitions

    try:
        tools = tool_definitions(None)
        assert any(t.name == "x.hello" for t in tools)

        out = plugins.try_handle(None, "x.hello", {})
        assert out == {"result": {"ok": True}}
    finally:
        # Reset global registry state so other tests (snapshots) are stable.
        monkeypatch.delenv("MCP_PLUGIN_MODULES", raising=False)
        importlib.reload(plugins)
