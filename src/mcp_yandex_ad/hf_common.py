"""Human-friendly (HF) helpers shared across Direct and Metrica."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Iterable
from uuid import uuid4


class HFError(RuntimeError):
    """Human-friendly layer error (actionable)."""


@dataclass(frozen=True)
class ResolveResult:
    ids: list[int]
    matches: list[dict[str, Any]]
    ambiguous: bool


def ensure_hf_enabled(config: Any) -> None:
    if not getattr(config, "hf_enabled", True):
        raise HFError("HF tools are disabled (HF_ENABLED=false).")


def ensure_hf_write_enabled(config: Any) -> None:
    if not getattr(config, "hf_write_enabled", False):
        raise HFError("HF write tools are disabled (HF_WRITE_ENABLED=false).")


def ensure_hf_destructive_enabled(config: Any) -> None:
    if not getattr(config, "hf_destructive_enabled", False):
        raise HFError("HF destructive tools are disabled (HF_DESTRUCTIVE_ENABLED=false).")


def should_apply(args: dict[str, Any]) -> bool:
    return bool(args.get("apply", False))


HF_ENVELOPE_VERSION = "1.0"


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _normalize_error(error: dict[str, Any] | None, *, default_message: str | None = None) -> dict[str, Any]:
    base = dict(error or {})
    err_type = str(base.get("type") or "validation")
    return {
        "code": str(base.get("code") or "hf_error"),
        "type": err_type,
        "retryable": bool(base.get("retryable", err_type in {"rate_limited", "upstream"})),
        "details": base.get("details") if isinstance(base.get("details"), dict) else ({"message": str(default_message)} if default_message else {}),
    }


def _normalize_choice(choice: Any, *, index: int) -> dict[str, Any]:
    if isinstance(choice, dict):
        choice_id = choice.get("id")
        if choice_id is None:
            for key in ("Id", "id", "CampaignId", "AdGroupId", "KeywordId", "Name", "name"):
                if choice.get(key) not in (None, ""):
                    choice_id = choice[key]
                    break
        label = choice.get("label")
        if label is None:
            for key in ("Name", "name", "Title", "title", "Id", "id"):
                if choice.get(key) not in (None, ""):
                    label = choice[key]
                    break
        return {
            "id": str(choice_id if choice_id not in (None, "") else f"choice-{index}"),
            "label": str(label if label not in (None, "") else choice_id if choice_id not in (None, "") else f"Choice {index}"),
            "type": str(choice.get("type") or "entity"),
            "context": choice,
        }
    return {
        "id": f"choice-{index}",
        "label": str(choice),
        "type": "value",
        "context": {"value": choice},
    }


def _normalize_warning(warning: Any) -> dict[str, Any]:
    if isinstance(warning, dict):
        return {
            "code": str(warning.get("code") or "warning"),
            "message": str(warning.get("message") or warning.get("code") or "warning"),
            **({"field": str(warning.get("field"))} if warning.get("field") else {}),
            "details": warning.get("details") if isinstance(warning.get("details"), dict) else {},
        }
    return {"code": "warning", "message": str(warning), "details": {}}


def validate_hf_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("HF payload must be an object")
    if not payload.get("tool"):
        raise ValueError("HF payload requires tool")
    if not payload.get("status"):
        raise ValueError("HF payload requires status")
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("HF payload requires meta")
    if not meta.get("envelope_version"):
        raise ValueError("HF payload requires meta.envelope_version")
    if not meta.get("request_id"):
        raise ValueError("HF payload requires meta.request_id")
    if not meta.get("timestamp"):
        raise ValueError("HF payload requires meta.timestamp")

    status = str(payload.get("status"))
    if status == "error" and not isinstance(payload.get("error"), dict):
        raise ValueError("HF payload with status=error requires error")
    if status == "needs_disambiguation":
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("HF payload with status=needs_disambiguation requires non-empty choices")
    if status == "dry_run" and not isinstance(payload.get("preview"), dict):
        raise ValueError("HF payload with status=dry_run requires preview")


def hf_payload(
    *,
    tool: str,
    status: str,
    preview: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
    message: str | None = None,
    choices: list[dict[str, Any]] | None = None,
    warnings: list[Any] | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "tool": tool,
        "status": status,
        "meta": {
            "envelope_version": HF_ENVELOPE_VERSION,
            "request_id": str(uuid4()),
            "timestamp": _now_iso(),
        },
    }
    if message:
        payload["message"] = message
    if preview is not None:
        payload["preview"] = preview
    if result is not None:
        payload["result"] = result
    if choices is not None:
        payload["choices"] = [_normalize_choice(choice, index=index) for index, choice in enumerate(choices, start=1)]
    if warnings:
        payload["warnings"] = [_normalize_warning(warning) for warning in warnings]
    if status == "error":
        payload["error"] = _normalize_error(error, default_message=message)
    validate_hf_payload(payload)
    return payload


def today_plus(days: int) -> str:
    return str(dt.date.today() + dt.timedelta(days=days))


def micros_from_rub(value: float | int) -> int:
    return int(round(float(value) * 1_000_000))


def dedupe_ints(values: Iterable[int]) -> list[int]:
    return list(dict.fromkeys(int(v) for v in values))
