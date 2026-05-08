"""Helpers for unique Direct report names."""

from __future__ import annotations

from datetime import datetime, timezone
import secrets


def make_unique_report_name(prefix: str, *, max_length: int = 255) -> str:
    base = (prefix or "").strip() or "MCP_REPORT"
    suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + secrets.token_hex(4)
    reserved = len(suffix) + 2
    if max_length <= reserved:
        return suffix[:max_length]
    trimmed = base[: max_length - reserved].rstrip("_-:.") or "MCP_REPORT"
    return f"{trimmed}__{suffix}"
