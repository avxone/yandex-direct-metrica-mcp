"""HTTP client for Yandex Metrica CDP API (api-metrika.yandex.net/cdp/api/v1)."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any
from urllib.parse import urljoin

import requests

logger = logging.getLogger("yandex-direct-metrica-mcp")


class CDPError(RuntimeError):
    """CDP API error."""

    def __init__(self, provider: str, message: str) -> None:
        super().__init__(message)
        self.provider = provider


_CDP_BASE = "https://api-metrika.yandex.net/cdp/api/v1/"


def _md5(val: str) -> str:
    return hashlib.md5(val.encode("utf-8")).hexdigest()


def _normalize_phone(raw: str) -> str:
    """Strip non-digits; keep last 10 digits."""
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) >= 10:
        return digits[-10:]
    return digits


def _normalize_email(raw: str) -> str:
    return raw.strip().lower()


class CDPClient:
    """Thin HTTP wrapper for Yandex Metrica CDP API.
    
    Endpoints:
      - https://api-metrika.yandex.net/cdp/api/v1/{counter_id}/...
    """

    def __init__(self, access_token: str) -> None:
        self._token = access_token
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"OAuth {access_token}",
            "Content-Type": "application/json",
        })

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------

    def _url(self, counter_id: str, path: str) -> str:
        return urljoin(_CDP_BASE, f"{counter_id}/{path.lstrip('/')}")

    def _get(self, counter_id: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self._url(counter_id, path)
        resp = self._session.get(url, params=params or {})
        if not resp.ok:
            raise CDPError("cdp_api", f"CDP GET {path} failed: {resp.status_code} {resp.text[:500]}")
        return resp.json()

    def _post(self, counter_id: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self._url(counter_id, path)
        resp = self._session.post(url, json=payload or {})
        if not resp.ok:
            raise CDPError("cdp_api", f"CDP POST {path} failed: {resp.status_code} {resp.text[:500]}")
        return resp.json()

    def _delete(self, counter_id: str, path: str) -> dict[str, Any]:
        url = self._url(counter_id, path)
        resp = self._session.delete(url)
        if not resp.ok:
            raise CDPError("cdp_api", f"CDP DELETE {path} failed: {resp.status_code} {resp.text[:500]}")
        return resp.json()

    # ------------------------------------------------------------------
    # CDP: Upload simple orders (CSV-style)
    # ------------------------------------------------------------------

    def upload_simple_orders(
        self,
        counter_id: str,
        rows: list[dict[str, Any]],
        *,
        auto_create_statuses: bool = True,
    ) -> dict[str, Any]:
        """Upload simple orders (ClientID, OrderID, Status, Revenue, Cost).
        
        `rows` should be list of dicts with keys matching CDP order schema.
        Returns upload result with upload_id for status tracking.
        """
        # Build CSV body from rows
        lines = [_serialize_order_row(r) for r in rows]
        csv_body = "\n".join(lines)
        payload = {
            "rows": csv_body,
            "autoCreateStatuses": auto_create_statuses,
        }
        return self._post(counter_id, "uploadings/simple_orders", payload)

    def upload_contacts(
        self,
        counter_id: str,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Upload contacts (email/phone → MD5).
        
        `rows` — list of dicts with keys: client_id, email, phone.
        email and phone are MD5-hashed before upload.
        """
        hashed_rows = []
        for r in rows:
            row: dict[str, Any] = {"client_id": r["client_id"]}
            if r.get("email"):
                row["email"] = _md5(_normalize_email(r["email"]))
            if r.get("phone"):
                row["phone"] = _md5(_normalize_phone(r["phone"]))
            hashed_rows.append(row)
        lines = [_serialize_order_row(r) for r in hashed_rows]
        csv_body = "\n".join(lines)
        return self._post(counter_id, "uploadings/contacts", {"rows": csv_body})

    def get_uploading_status(self, counter_id: str, upload_id: str) -> dict[str, Any]:
        """Check status of a previous upload."""
        return self._get(counter_id, f"uploadings/{upload_id}")

    # ------------------------------------------------------------------
    # CDP: Order statuses
    # ------------------------------------------------------------------

    def get_order_statuses(self, counter_id: str) -> list[dict[str, Any]]:
        """List all order statuses for counter."""
        data = self._get(counter_id, "order_statuses")
        return data.get("statuses", data.get("data", []))

    def create_order_status(self, counter_id: str, name: str, *,
                            is_closed: bool = False) -> dict[str, Any]:
        """Create a new order status.
        
        `is_closed=True` means order is final (e.g. completed/cancelled).
        """
        return self._post(counter_id, "order_statuses", {
            "name": name,
            "is_closed": is_closed,
        })

    def delete_order_status(self, counter_id: str, status_id: str) -> dict[str, Any]:
        return self._delete(counter_id, f"order_statuses/{status_id}")

    # ------------------------------------------------------------------
    # CDP: Attributes
    # ------------------------------------------------------------------

    def get_attributes(self, counter_id: str) -> list[dict[str, Any]]:
        data = self._get(counter_id, "attributes")
        return data.get("attributes", data.get("data", []))

    def create_attribute(self, counter_id: str, name: str, attr_type: str) -> dict[str, Any]:
        """Create a user attribute. attr_type: 'string'|'number'|'date'."""
        return self._post(counter_id, "attributes", {
            "name": name,
            "type": attr_type,
        })

    def delete_attribute(self, counter_id: str, attr_id: str) -> dict[str, Any]:
        return self._delete(counter_id, f"attributes/{attr_id}")


# ------------------------------------------------------------------
# Serialization helpers
# ------------------------------------------------------------------

def _serialize_order_row(row: dict[str, Any]) -> str:
    """Serialize a single order row dict → CSV line.
    
    Expected keys: client_id, order_id, status, revenue, cost, create_date, ...
    Extra keys are ignored.
    """
    fields = [
        str(row.get("client_id", "")),
        str(row.get("order_id", "")),
        str(row.get("status", "")),
        str(row.get("revenue", "0")),
        str(row.get("cost", "0")),
        str(row.get("create_date", "")),
        str(row.get("update_date", "")),
    ]
    return ",".join(fields)
