"""Helpers for future app-safe payload contracts."""

from __future__ import annotations

from typing import Any


_DROPPED_KEYS = {
    "raw",
    "raw_report",
    "sources_raw_report",
    "direct_raw_report",
    "direct_split_raw_report",
}

_MAX_STRING_LENGTH = 10_000


def compact_sections(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a UI-neutral payload by removing known bulky raw sections."""

    def _compact(value: Any) -> Any:
        if isinstance(value, dict):
            out: dict[str, Any] = {}
            for key, item in value.items():
                if key in _DROPPED_KEYS:
                    continue
                out[key] = _compact(item)
            return out
        if isinstance(value, list):
            return [_compact(item) for item in value]
        return value

    return _compact(payload)


def is_app_safe_payload(payload: dict[str, Any]) -> bool:
    """Check whether a payload is compact enough for future richer app surfaces."""

    if not isinstance(payload, dict):
        return False
    if compact_sections(payload) != payload:
        return False

    def _is_safe(value: Any) -> bool:
        if isinstance(value, dict):
            return all(_is_safe(item) for item in value.values())
        if isinstance(value, list):
            return all(_is_safe(item) for item in value)
        if isinstance(value, str):
            return len(value) <= _MAX_STRING_LENGTH
        return True

    return _is_safe(payload)
