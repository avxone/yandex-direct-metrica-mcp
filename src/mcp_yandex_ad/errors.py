"""Error normalization for Yandex Direct + Metrica."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlsplit, urlunsplit

try:
    from tapi_yandex_direct import exceptions as direct_exceptions
except ImportError:  # pragma: no cover - optional dependency (tests/dev)
    class _DirectExceptions:
        class YandexDirectClientError(Exception):
            error_code: str | None = None
            request_id: str | None = None
            error_string: str | None = None
            error_detail: str | None = None

        class YandexDirectTokenError(YandexDirectClientError):
            pass

        class YandexDirectRequestsLimitError(YandexDirectClientError):
            pass

        class YandexDirectNotEnoughUnitsError(YandexDirectClientError):
            pass

        class YandexDirectApiError(Exception):
            data: Any | None = None

    direct_exceptions = _DirectExceptions()

try:
    from tapi_yandex_metrika import exceptions as metrica_exceptions
except ImportError:  # pragma: no cover - optional dependency (tests/dev)
    class _MetricaExceptions:
        class YandexMetrikaClientError(Exception):
            code: str | None = None
            message: str | None = None
            errors: Any | None = None

        class YandexMetrikaTokenError(YandexMetrikaClientError):
            pass

        class YandexMetrikaLimitError(YandexMetrikaClientError):
            pass

        class YandexMetrikaDownloadReportError(YandexMetrikaClientError):
            pass

        class YandexMetrikaApiError(Exception):
            data: Any | None = None

    metrica_exceptions = _MetricaExceptions()

from .wordstat_client import WordstatError
from .audience_client import AudienceError

HINT_RATE_LIMIT = "Rate limit exceeded; retry with backoff."
HINT_TOKEN = "Check access/refresh token and API permissions."
HINT_UNITS = "Not enough units; retry later or reduce scope."
HINT_REPORT = "Report not ready; retry later."
HINT_PARAMS = "Check required parameters."
HINT_WORDSTAT_ACCESS = (
    "Check Yandex Search API Wordstat setup: service account in the target folder, "
    "search-api.webSearch.user role, API key scope yc.search-api.execute if scopes are configured, "
    "and matching YANDEX_SEARCH_API_FOLDER_ID."
)
HINT_WORDSTAT_FOLDER = "Set YANDEX_SEARCH_API_FOLDER_ID to the Yandex Cloud folder that owns the Search API credentials."
HINT_WORDSTAT_PERIOD = "Use period monthly/weekly/daily or PERIOD_MONTHLY/PERIOD_WEEKLY/PERIOD_DAILY."
HINT_WORDSTAT_MONTH = "For monthly Wordstat dynamics, pass to_date as YYYY-MM or the last day of the month."
HINT_WORDSTAT_WEEK = "For weekly Wordstat dynamics, pass a provider-valid week-end toDate via params or use daily/monthly."


class MissingClientError(RuntimeError):
    def __init__(self, provider: str, message: str) -> None:
        super().__init__(message)
        self.provider = provider


class WriteGuardError(RuntimeError):
    def __init__(self, provider: str, message: str, hint: str) -> None:
        super().__init__(message)
        self.provider = provider
        self.hint = hint


class NotSupportedError(RuntimeError):
    def __init__(self, provider: str, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.provider = provider
        self.hint = hint or "Operation is not supported by the upstream API."


class ToolNotAvailableError(RuntimeError):
    def __init__(self, tool: str, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.tool = tool
        self.hint = hint or "Call tools/list to see the available tools for this build."


def _safe_message(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True)
    return str(value)


def _sanitize_url(url: str | None) -> str | None:
    if not url:
        return None
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        return url
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _extract_http_info(exc: Exception) -> dict[str, Any]:
    response = getattr(exc, "response", None)
    if response is None:
        return {}

    info: dict[str, Any] = {}
    status_code = getattr(response, "status_code", None)
    reason = getattr(response, "reason", None)
    endpoint = _sanitize_url(getattr(response, "url", None))

    if status_code is not None:
        info["http_status"] = status_code
    if reason:
        info["http_reason"] = reason
    if endpoint:
        info["endpoint"] = endpoint

    headers = getattr(response, "headers", None)
    if headers:
        request_id = headers.get("X-Request-Id") or headers.get("X-Request-ID")
        if request_id:
            info["request_id"] = request_id

    return info


def _extract_response_text(response: Any) -> str:
    try:
        data = response.json()
    except Exception:
        text = getattr(response, "text", "") or ""
        return str(text)[:1000]
    if isinstance(data, dict):
        parts: list[str] = []
        for key in ("message", "error", "error_description", "details"):
            value = data.get(key)
            if value:
                parts.append(_safe_message(value) or "")
        return " ".join(parts)[:1000]
    return _safe_message(data)[:1000] if data is not None else ""


def _wordstat_hint(exc: WordstatError, *, http_status: Any) -> str | None:
    response = getattr(exc, "response", None)
    text = _extract_response_text(response).lower() if response is not None else str(exc).lower()
    if "folderid" in text or "folder id" in text or "folder_id" in text:
        return HINT_WORDSTAT_FOLDER
    if "period_" in text or ("period" in text and "enum" in text):
        return HINT_WORDSTAT_PERIOD
    if "last day of the month" in text or ("month" in text and "todate" in text):
        return HINT_WORDSTAT_MONTH
    if "last day of the week" in text or ("week" in text and "todate" in text):
        return HINT_WORDSTAT_WEEK
    access_markers = ("permission", "access", "iam", "role", "scope", "unauthorized", "forbidden")
    if http_status in {401, 403} or any(marker in text for marker in access_markers):
        return HINT_WORDSTAT_ACCESS
    return None


def normalize_error(tool: str, exc: Exception) -> dict[str, Any]:
    payload: dict[str, Any] = {"tool": tool, "type": exc.__class__.__name__}
    payload.update(_extract_http_info(exc))

    if isinstance(exc, MissingClientError):
        payload["provider"] = exc.provider
        payload["message"] = str(exc)
        payload["hint"] = HINT_TOKEN
    elif isinstance(exc, ToolNotAvailableError):
        payload["provider"] = "mcp"
        payload["message"] = str(exc)
        payload["hint"] = exc.hint
    elif isinstance(exc, WriteGuardError):
        payload["provider"] = exc.provider
        payload["message"] = str(exc)
        payload["hint"] = exc.hint
    elif isinstance(exc, NotSupportedError):
        payload["provider"] = exc.provider
        payload["message"] = str(exc)
        payload["hint"] = exc.hint
    elif isinstance(exc, direct_exceptions.YandexDirectClientError):
        payload["provider"] = "direct"
        payload["error_code"] = exc.error_code
        payload["request_id"] = exc.request_id
        payload["message"] = exc.error_string
        payload["detail"] = exc.error_detail
        if isinstance(exc, direct_exceptions.YandexDirectTokenError):
            payload["hint"] = HINT_TOKEN
        elif isinstance(exc, direct_exceptions.YandexDirectRequestsLimitError):
            payload["hint"] = HINT_RATE_LIMIT
        elif isinstance(exc, direct_exceptions.YandexDirectNotEnoughUnitsError):
            payload["hint"] = HINT_UNITS
    elif isinstance(exc, direct_exceptions.YandexDirectApiError):
        payload["provider"] = "direct"
        payload["message"] = _safe_message(getattr(exc, "data", None)) or "Direct API error"
    elif isinstance(exc, metrica_exceptions.YandexMetrikaClientError):
        payload["provider"] = "metrica"
        payload["error_code"] = exc.code
        payload["message"] = exc.message or "Metrica API error"
        if exc.errors:
            payload["details"] = exc.errors
        if isinstance(exc, metrica_exceptions.YandexMetrikaTokenError):
            payload["hint"] = HINT_TOKEN
        elif isinstance(exc, metrica_exceptions.YandexMetrikaLimitError):
            payload["hint"] = HINT_RATE_LIMIT
        elif isinstance(exc, metrica_exceptions.YandexMetrikaDownloadReportError):
            payload["hint"] = HINT_REPORT
    elif isinstance(exc, metrica_exceptions.YandexMetrikaApiError):
        payload["provider"] = "metrica"
        payload["message"] = exc.message or "Metrica API error"
    elif isinstance(exc, WordstatError):
        payload["provider"] = "wordstat"
        payload["message"] = str(exc) or "Wordstat API error"
        http_status = payload.get("http_status")
        hint = _wordstat_hint(exc, http_status=http_status)
        if hint:
            payload["hint"] = hint
        elif http_status == 401 or http_status == 403:
            payload["hint"] = HINT_WORDSTAT_ACCESS
        elif http_status == 429:
            payload["hint"] = HINT_RATE_LIMIT
        elif isinstance(http_status, int) and 500 <= http_status <= 599:
            payload["hint"] = HINT_RATE_LIMIT
    elif isinstance(exc, AudienceError):
        payload["provider"] = "audience"
        payload["message"] = str(exc) or "Audience API error"
        http_status = payload.get("http_status")
        if http_status == 401 or http_status == 403:
            payload["hint"] = HINT_TOKEN
        elif http_status == 429:
            payload["hint"] = HINT_RATE_LIMIT
        elif isinstance(http_status, int) and 500 <= http_status <= 599:
            payload["hint"] = HINT_RATE_LIMIT
    elif isinstance(exc, ValueError):
        payload["message"] = str(exc)
        payload["hint"] = HINT_PARAMS
    else:
        payload["message"] = str(exc)

    return {"error": payload}
