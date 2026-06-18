"""Minimal Yandex Search API Wordstat client (HTTP JSON).

This MCP keeps dependencies lightweight and uses requests directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


WORDSTAT_API_BASE = "https://searchapi.api.cloud.yandex.net/v2/wordstat/"


class WordstatError(RuntimeError):
    def __init__(self, message: str, *, response: requests.Response | None = None) -> None:
        super().__init__(message)
        self.provider = "wordstat"
        self.response = response


def _normalize_device(value: Any) -> str:
    normalized = str(value or "").strip().upper()
    aliases = {
        "ALL": "DEVICE_ALL",
        "DEVICE_ALL": "DEVICE_ALL",
        "DESKTOP": "DEVICE_DESKTOP",
        "DEVICE_DESKTOP": "DEVICE_DESKTOP",
        "PHONE": "DEVICE_PHONE",
        "PHONES": "DEVICE_PHONE",
        "MOBILE": "DEVICE_PHONE",
        "MOBILE_PHONE": "DEVICE_PHONE",
        "MOBILEPHONES": "DEVICE_PHONE",
        "DEVICE_PHONE": "DEVICE_PHONE",
        "TABLET": "DEVICE_TABLET",
        "TABLETS": "DEVICE_TABLET",
        "DEVICE_TABLET": "DEVICE_TABLET",
    }
    return aliases.get(normalized, normalized)


def _normalize_period(value: Any) -> str:
    normalized = str(value or "").strip().upper()
    aliases = {
        "MONTH": "PERIOD_MONTHLY",
        "MONTHLY": "PERIOD_MONTHLY",
        "PERIOD_MONTHLY": "PERIOD_MONTHLY",
        "WEEK": "PERIOD_WEEKLY",
        "WEEKLY": "PERIOD_WEEKLY",
        "PERIOD_WEEKLY": "PERIOD_WEEKLY",
        "DAY": "PERIOD_DAILY",
        "DAILY": "PERIOD_DAILY",
        "PERIOD_DAILY": "PERIOD_DAILY",
    }
    return aliases.get(normalized, normalized)


@dataclass(frozen=True)
class WordstatClient:
    folder_id: str
    api_key: str | None = None
    iam_token: str | None = None
    base_url: str = WORDSTAT_API_BASE
    timeout_seconds: int = 30

    def _payload(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        body = dict(payload or {})
        body.setdefault("folderId", self.folder_id)
        if isinstance(body.get("regions"), list):
            body["regions"] = [str(item) for item in body["regions"]]
        if isinstance(body.get("devices"), list):
            body["devices"] = [_normalize_device(item) for item in body["devices"]]
        if body.get("period") is not None:
            body["period"] = _normalize_period(body["period"])
        return body

    def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.folder_id:
            raise WordstatError("Yandex Search API folderId is not configured.")
        if not (self.api_key or self.iam_token):
            raise WordstatError("Yandex Search API API key or IAM token is not configured.")

        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        auth_value = f"Api-Key {self.api_key}" if self.api_key else f"Bearer {self.iam_token}"
        headers = {
            "Authorization": auth_value,
            "Content-Type": "application/json;charset=utf-8",
        }
        body = self._payload(payload)
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=self.timeout_seconds)
        except requests.RequestException as exc:
            raise WordstatError(str(exc)) from exc
        if resp.status_code < 200 or resp.status_code >= 300:
            # Keep response attached for error normalization (status, endpoint, request_id header).
            raise WordstatError(f"Wordstat API error (HTTP {resp.status_code})", response=resp)
        try:
            data: Any = resp.json()
        except Exception as exc:
            raise WordstatError("Failed to decode Wordstat JSON response", response=resp) from exc
        if not isinstance(data, dict):
            raise WordstatError("Unexpected Wordstat response type", response=resp)
        return data
