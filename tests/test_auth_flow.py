from __future__ import annotations

from mcp_yandex_ad.auth_flow import parse_oauth_callback_request


def test_parse_oauth_callback_request_not_found():
    status, res = parse_oauth_callback_request(
        "/other?code=abc&state=s",
        callback_path="/callback",
        expected_state="s",
    )
    assert status == 404
    assert res is None


def test_parse_oauth_callback_request_captures_code():
    status, res = parse_oauth_callback_request(
        "/callback?code=abc&state=state123",
        callback_path="/callback",
        expected_state="state123",
    )
    assert status == 200
    assert res is not None
    assert res.error is None
    assert res.code == "abc"


def test_parse_oauth_callback_request_rejects_state_mismatch():
    status, res = parse_oauth_callback_request(
        "/callback?code=abc&state=wrong",
        callback_path="/callback",
        expected_state="expected",
    )
    assert status == 200
    assert res is not None
    assert res.code is None
    assert res.error == "Invalid state"

