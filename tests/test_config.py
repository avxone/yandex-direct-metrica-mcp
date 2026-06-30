from mcp_yandex_ad.config import load_config


def test_load_config_write_flags(monkeypatch):
    monkeypatch.setenv("MCP_WRITE_ENABLED", "true")
    monkeypatch.setenv("MCP_WRITE_SANDBOX_ONLY", "false")
    config = load_config()
    assert config.write_enabled is True
    assert config.write_sandbox_only is False


def test_load_config_direct_api_version(monkeypatch):
    monkeypatch.delenv("YANDEX_DIRECT_API_VERSION", raising=False)
    config = load_config()
    assert config.direct_api_version == "v5"
    monkeypatch.setenv("YANDEX_DIRECT_API_VERSION", "v501")
    config = load_config()
    assert config.direct_api_version == "v501"


def test_load_config_wordstat_search_api(monkeypatch):
    monkeypatch.setenv("YANDEX_SEARCH_API_FOLDER_ID", "folder-1")
    monkeypatch.setenv("YANDEX_SEARCH_API_API_KEY", "api-key-1")
    monkeypatch.setenv("YANDEX_SEARCH_API_DEFAULT_REGION", "225")
    monkeypatch.setenv("YANDEX_SEARCH_API_WEB_BASE_URL", "https://example.test/web")

    config = load_config()

    assert config.wordstat_search_api_folder_id == "folder-1"
    assert config.wordstat_search_api_api_key == "api-key-1"
    assert config.search_api_enabled is True
    assert config.search_api_default_region == 225
    assert config.search_api_web_base_url == "https://example.test/web"
