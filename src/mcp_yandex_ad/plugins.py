"""Optional PRO plugins loader.

This module enables a closed-source "plugin" distribution to register additional tools
and tool handlers at runtime (e.g., BI Option 2 datasets/sync).

Core (public) builds ship without plugins; if a plugin is installed, it can expose
extra tools via entry points.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import importlib
import logging
import os
from typing import Any, Callable, Iterable

from mcp.types import Tool

logger = logging.getLogger("yandex-direct-metrica-mcp.plugins")

ENTRYPOINT_GROUP = "mcp_yandex_ad.plugins"

ToolHandler = Callable[[Any, dict[str, Any]], dict[str, Any]]
PrefixHandler = Callable[[Any, str, dict[str, Any]], dict[str, Any]]


@dataclass
class PluginRegistry:
    tools: list[Tool] = field(default_factory=list)
    _tool_handlers: dict[str, ToolHandler] = field(default_factory=dict)
    _prefix_handlers: list[tuple[str, PrefixHandler]] = field(default_factory=list)

    def add_tools(self, tools: Iterable[Tool]) -> None:
        for tool in tools:
            if isinstance(tool, Tool):
                self.tools.append(tool)

    def add_tool_handler(self, name: str, handler: ToolHandler) -> None:
        if not name or not callable(handler):
            raise ValueError("tool handler requires a non-empty name and a callable")
        self._tool_handlers[name] = handler

    def add_prefix_handler(self, prefix: str, handler: PrefixHandler) -> None:
        if not prefix or not callable(handler):
            raise ValueError("prefix handler requires a non-empty prefix and a callable")
        self._prefix_handlers.append((prefix, handler))
        self._prefix_handlers.sort(key=lambda x: len(x[0]), reverse=True)

    def try_handle(self, ctx: Any, name: str, args: dict[str, Any]) -> dict[str, Any] | None:
        handler = self._tool_handlers.get(name)
        if handler is not None:
            return handler(ctx, args)
        for prefix, ph in self._prefix_handlers:
            if name.startswith(prefix):
                return ph(ctx, name, args)
        return None


_REGISTRY: PluginRegistry | None = None
_LOADED: bool = False


def _load_entrypoint_objects() -> list[Any]:
    try:
        from importlib.metadata import entry_points
    except Exception:  # pragma: no cover - very old python
        return []

    try:
        eps = entry_points()
        selected = eps.select(group=ENTRYPOINT_GROUP) if hasattr(eps, "select") else eps.get(ENTRYPOINT_GROUP, [])
        return [ep.load() for ep in selected]
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to load plugin entry points: %s", exc)
        return []


def _load_env_objects() -> list[Any]:
    raw = (os.getenv("MCP_PLUGIN_MODULES") or "").strip()
    if not raw:
        return []
    out: list[Any] = []
    for item in [x.strip() for x in raw.split(",") if x.strip()]:
        module_name, _, attr = item.partition(":")
        try:
            mod = importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to import plugin module %r: %s", module_name, exc)
            continue
        if attr:
            out.append(getattr(mod, attr, None))
        else:
            out.append(getattr(mod, "register", None))
    return [x for x in out if x is not None]


def _apply_plugin(registry: PluginRegistry, plugin_obj: Any) -> None:
    # Accepted forms:
    # - object with .register(registry)
    # - callable register(registry)
    # - callable that returns a plugin (factory)
    try:
        register = getattr(plugin_obj, "register", None)
        if callable(register):
            register(registry)
            return
        if callable(plugin_obj):
            # First, treat it as register(registry).
            try:
                plugin_obj(registry)
                return
            except TypeError:
                # Otherwise, treat it as a factory.
                maybe = plugin_obj()
                register2 = getattr(maybe, "register", None)
                if callable(register2):
                    register2(registry)
                    return
                if callable(maybe):
                    maybe(registry)
                    return
        logger.warning("Ignoring plugin object without register(): %r", plugin_obj)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Plugin registration failed for %r: %s", plugin_obj, exc)


def get_registry() -> PluginRegistry:
    global _REGISTRY, _LOADED
    if _REGISTRY is None:
        _REGISTRY = PluginRegistry()
    if _LOADED:
        return _REGISTRY
    _LOADED = True

    plugins: list[Any] = []
    plugins.extend(_load_entrypoint_objects())
    plugins.extend(_load_env_objects())
    for plugin_obj in plugins:
        _apply_plugin(_REGISTRY, plugin_obj)
    return _REGISTRY


def plugin_tools() -> list[Tool]:
    return list(get_registry().tools)


def try_handle(ctx: Any, name: str, args: dict[str, Any]) -> dict[str, Any] | None:
    return get_registry().try_handle(ctx, name, args)
