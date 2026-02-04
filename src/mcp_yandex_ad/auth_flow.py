"""OAuth flow helpers for CLI auth UX (manual + local callback + hybrid).

This module is intentionally CLI-oriented: it helps users obtain OAuth tokens
without storing them inside the MCP server runtime.
"""

from __future__ import annotations

import http.server
import threading
import time
from dataclasses import dataclass
from typing import Callable
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True)
class OAuthCallbackResult:
    code: str | None = None
    error: str | None = None


def parse_oauth_callback_request(
    request_path: str,
    *,
    callback_path: str,
    expected_state: str,
) -> tuple[int, OAuthCallbackResult | None]:
    """Parse an incoming callback request path into an OAuthCallbackResult.

    Returns (http_status, result). When the path doesn't match callback_path,
    returns (404, None).
    """
    callback_path = callback_path if callback_path.startswith("/") else f"/{callback_path}"
    parsed = urlparse(request_path)
    if parsed.path != callback_path:
        return 404, None

    qs = parse_qs(parsed.query)
    state = (qs.get("state") or [""])[0]
    code = (qs.get("code") or [""])[0]
    err = (qs.get("error") or [""])[0]

    if state and state != expected_state:
        return 200, OAuthCallbackResult(error="Invalid state")
    if err:
        return 200, OAuthCallbackResult(error=err)
    if code:
        return 200, OAuthCallbackResult(code=code)
    return 200, OAuthCallbackResult(error="Missing code")


def is_loopback_redirect_uri(redirect_uri: str) -> bool:
    """Return True when redirect_uri points to a local loopback HTTP endpoint."""
    parsed = urlparse(redirect_uri)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower()
    return host in {"127.0.0.1", "localhost"}


def parse_loopback_redirect_uri(redirect_uri: str) -> tuple[str, int, str]:
    """Parse loopback redirect URI into (host, port, path)."""
    parsed = urlparse(redirect_uri)
    host = parsed.hostname or "127.0.0.1"
    port = int(parsed.port or 0)
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    return host, port, path


class LocalOAuthCallbackServer:
    """Minimal local callback server to capture `code` for OAuth flows."""

    def __init__(self, *, host: str, port: int, callback_path: str, expected_state: str) -> None:
        self._host = host
        self._port = int(port)
        self._callback_path = callback_path if callback_path.startswith("/") else f"/{callback_path}"
        self._expected_state = expected_state
        self._event = threading.Event()
        self._result = OAuthCallbackResult()
        self._httpd: http.server.HTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def port(self) -> int:
        if self._httpd is None:
            return self._port
        return int(self._httpd.server_address[1])

    @property
    def redirect_uri(self) -> str:
        return f"http://{self._host}:{self.port}{self._callback_path}"

    def start(self) -> None:
        expected_state = self._expected_state
        callback_path = self._callback_path
        event = self._event

        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:  # noqa: A002
                # Silence default HTTP server logging (avoid leaking query params into logs).
                return None

            def do_GET(self) -> None:  # noqa: N802
                status, result = parse_oauth_callback_request(
                    self.path,
                    callback_path=callback_path,
                    expected_state=expected_state,
                )
                if status == 404:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Not found")
                    return

                outer._result = result or OAuthCallbackResult(error="Missing code")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    b"<!doctype html><html><body><h3>OAuth received.</h3><p>You can close this tab.</p></body></html>"
                )
                event.set()

        self._httpd = http.server.HTTPServer((self._host, self._port), Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, name="oauth-callback", daemon=True)
        self._thread.start()

    def wait(self, *, timeout_seconds: int) -> OAuthCallbackResult | None:
        if timeout_seconds <= 0:
            timeout_seconds = 1
        ok = self._event.wait(timeout_seconds)
        if not ok:
            return None
        return self._result

    def stop(self) -> None:
        if self._httpd is not None:
            try:
                self._httpd.shutdown()
            except Exception:
                pass
            try:
                self._httpd.server_close()
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=1.0)


def wait_for_code_via_loopback(
    *,
    redirect_uri: str,
    expected_state: str,
    timeout_seconds: int,
    now: Callable[[], float] | None = None,
) -> OAuthCallbackResult | None:
    """Start a loopback server based on redirect_uri and wait for callback."""
    host, port, path = parse_loopback_redirect_uri(redirect_uri)
    if port <= 0:
        raise ValueError("Loopback redirect_uri must include an explicit port (for example: http://127.0.0.1:8765/callback)")

    server = LocalOAuthCallbackServer(host=host, port=port, callback_path=path, expected_state=expected_state)
    server.start()
    start = (now or time.monotonic)()
    try:
        remaining = int(max(1, timeout_seconds))
        result = server.wait(timeout_seconds=remaining)
        return result
    finally:
        server.stop()
