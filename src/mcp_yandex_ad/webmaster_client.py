"""Minimal Yandex Webmaster API client (HTTP JSON).

API docs: https://yandex.ru/dev/webmaster/doc/dg/concepts/about.html
Base URL: https://api.webmaster.yandex.net/v3/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import requests


WEBMASTER_API_BASE = "https://api.webmaster.yandex.net/v3/"


class WebmasterError(RuntimeError):
    def __init__(self, message: str, *, response: requests.Response | None = None) -> None:
        super().__init__(message)
        self.provider = "webmaster"
        self.response = response


@dataclass(frozen=True)
class WebmasterClient:
    access_token: str
    base_url: str = WEBMASTER_API_BASE
    timeout_seconds: int = 30

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json;charset=utf-8",
        }

    def get(self, path: str) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self.timeout_seconds)
        except requests.RequestException as exc:
            raise WebmasterError(str(exc)) from exc
        if resp.status_code < 200 or resp.status_code >= 300:
            raise WebmasterError(f"Webmaster API error (HTTP {resp.status_code})", response=resp)
        try:
            data: Any = resp.json()
        except Exception as exc:
            raise WebmasterError("Failed to decode Webmaster JSON response", response=resp) from exc
        if not isinstance(data, dict):
            raise WebmasterError("Unexpected Webmaster response type", response=resp)
        return data

    def put(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        try:
            resp = requests.put(url, headers=self._headers(), json=(payload or {}), timeout=self.timeout_seconds)
        except requests.RequestException as exc:
            raise WebmasterError(str(exc)) from exc
        if resp.status_code < 200 or resp.status_code >= 300:
            raise WebmasterError(f"Webmaster API error (HTTP {resp.status_code})", response=resp)
        try:
            data: Any = resp.json()
        except Exception as exc:
            raise WebmasterError("Failed to decode Webmaster JSON response", response=resp) from exc
        return data if isinstance(data, dict) else {}

    def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        try:
            resp = requests.post(url, headers=self._headers(), json=(payload or {}), timeout=self.timeout_seconds)
        except requests.RequestException as exc:
            raise WebmasterError(str(exc)) from exc
        if resp.status_code < 200 or resp.status_code >= 300:
            raise WebmasterError(f"Webmaster API error (HTTP {resp.status_code})", response=resp)
        try:
            data: Any = resp.json()
        except Exception as exc:
            raise WebmasterError("Failed to decode Webmaster JSON response", response=resp) from exc
        return data if isinstance(data, dict) else {}

    def delete(self, path: str) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        try:
            resp = requests.delete(url, headers=self._headers(), timeout=self.timeout_seconds)
        except requests.RequestException as exc:
            raise WebmasterError(str(exc)) from exc
        if resp.status_code < 200 or resp.status_code >= 300:
            raise WebmasterError(f"Webmaster API error (HTTP {resp.status_code})", response=resp)
        if resp.status_code == 204:
            return {"deleted": True}
        try:
            data: Any = resp.json() if resp.text else {}
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}
