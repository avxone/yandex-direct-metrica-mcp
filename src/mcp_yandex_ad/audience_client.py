"""Yandex Audience API client (raw HTTP wrapper)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


DEFAULT_AUDIENCE_BASE_URL = "https://api-audience.yandex.com/v1/management"


@dataclass
class AudienceError(RuntimeError):
    """Audience API error wrapper for normalized MCP errors."""

    response: requests.Response | None = None
    provider: str = "audience"


class AudienceClient:
    def __init__(
        self,
        *,
        access_token: str,
        base_url: str = DEFAULT_AUDIENCE_BASE_URL,
        timeout_seconds: int = 60,
    ) -> None:
        self._access_token = access_token
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", path, params=params)

    def post(
        self,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request("POST", path, payload=payload, params=params, files=files)

    def put(
        self,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request("PUT", path, payload=payload, params=params)

    def delete(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("DELETE", path, params=params)

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"OAuth {self._access_token}",
            "Accept": "application/json",
        }
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                json=None if files else (payload or None),
                files=files,
                timeout=self._timeout_seconds,
            )
        except requests.RequestException as exc:
            raise AudienceError(str(exc)) from exc

        if response.status_code >= 400:
            err = AudienceError(f"Audience API HTTP {response.status_code}")
            err.response = response
            raise err

        if not response.content:
            return {"ok": True}
        try:
            data = response.json()
        except ValueError as exc:
            err = AudienceError("Audience API returned invalid JSON")
            err.response = response
            raise err from exc
        if not isinstance(data, dict):
            return {"result": data}
        return data

