from requests import Response

from mcp_yandex_ad import errors as errors_mod
from mcp_yandex_ad.errors import MissingClientError, WriteGuardError, normalize_error

direct_exceptions = errors_mod.direct_exceptions
metrica_exceptions = errors_mod.metrica_exceptions


def _response(url: str = "https://api.direct.yandex.com/json/v5/campaigns") -> Response:
    response = Response()
    response.status_code = 400
    response.reason = "Bad Request"
    response.url = url
    response.headers["X-Request-Id"] = "req-123"
    return response


def test_normalize_direct_token_error():
    message = {
        "error": {
            "error_code": 53,
            "request_id": "req-123",
            "error_string": "Invalid",
            "error_detail": "OAuth token is missing",
        }
    }
    cls = direct_exceptions.YandexDirectTokenError
    try:
        exc = cls(_response(), message, client=object())
    except TypeError:
        exc = cls()
        exc.response = _response()
        exc.error_code = message["error"]["error_code"]
        exc.request_id = message["error"]["request_id"]
        exc.error_string = message["error"]["error_string"]
        exc.error_detail = message["error"]["error_detail"]
    payload = normalize_error("direct.list_campaigns", exc)["error"]
    assert payload["provider"] == "direct"
    assert payload["error_code"] == 53
    assert payload["request_id"] == "req-123"
    assert payload["hint"] == "Check access/refresh token and API permissions."


def test_normalize_metrica_limit_error():
    cls = metrica_exceptions.YandexMetrikaLimitError
    try:
        exc = cls(
            _response("https://api-metrika.yandex.net/stat/v1/data"),
            message="Rate limit",
            code=429,
            errors=[{"error_type": "quota"}],
        )
    except TypeError:
        exc = cls()
        exc.response = _response("https://api-metrika.yandex.net/stat/v1/data")
        exc.message = "Rate limit"
        exc.code = 429
        exc.errors = [{"error_type": "quota"}]
    payload = normalize_error("metrica.report", exc)["error"]
    assert payload["provider"] == "metrica"
    assert payload["error_code"] == 429
    assert payload["hint"] == "Rate limit exceeded; retry with backoff."


def test_normalize_missing_client():
    exc = MissingClientError("direct", "Direct client not configured.")
    payload = normalize_error("direct.list_campaigns", exc)["error"]
    assert payload["provider"] == "direct"
    assert payload["hint"] == "Check access/refresh token and API permissions."


def test_normalize_write_guard():
    exc = WriteGuardError("direct", "Write operations are disabled.", "Enable write mode")
    payload = normalize_error("direct.create_campaigns", exc)["error"]
    assert payload["provider"] == "direct"
    assert payload["hint"] == "Enable write mode"
