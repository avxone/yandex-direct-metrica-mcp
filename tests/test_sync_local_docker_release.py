from scripts.sync_local_docker_release import specs


def test_specs_public_only() -> None:
    items = specs("georgy-agaev", "2.0.13", include_pro=False)
    assert len(items) == 1
    assert items[0].remote == "ghcr.io/georgy-agaev/yandex-direct-metrica-mcp:v2.0.13"
    assert "yandex-direct-metrica-mcp:latest" in items[0].local_aliases


def test_specs_include_pro() -> None:
    items = specs("georgy-agaev", "2.0.13", include_pro=True)
    assert len(items) == 2
    assert items[1].remote == "ghcr.io/georgy-agaev/yandex-direct-metrica-mcp-pro:pro-v2.0.13"
    assert "yandex-direct-metrica-mcp-pro:latest" in items[1].local_aliases
