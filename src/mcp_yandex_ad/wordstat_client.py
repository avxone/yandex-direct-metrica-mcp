"""Minimal Wordstat API client (HTTP JSON).

This MCP keeps dependencies lightweight and uses requests directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


WORDSTAT_API_BASE = "https://api.wordstat.yandex.net/v1/"


class WordstatError(RuntimeError):
    def __init__(self, message: str, *, response: requests.Response | None = None) -> None:
        super().__init__(message)
        self.provider = "wordstat"
        self.response = response


@dataclass(frozen=True)
class WordstatClient:
    access_token: str
    base_url: str = WORDSTAT_API_BASE
    timeout_seconds: int = 30

    def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json;charset=utf-8",
        }
        try:
            resp = requests.post(url, headers=headers, json=(payload or {}), timeout=self.timeout_seconds)
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

