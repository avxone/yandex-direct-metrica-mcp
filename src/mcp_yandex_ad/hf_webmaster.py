"""Human-friendly Webmaster tools for Yandex Webmaster API v3."""

from __future__ import annotations

from typing import Any

from .hf_common import HFError
from .webmaster_client import WebmasterClient


def handle(name: str, client: WebmasterClient, args: dict[str, Any]) -> dict[str, Any] | None:
    """Dispatch Webmaster tools."""
    if name == "webmaster.hf.user_info":
        return _user_info(client)
    if name == "webmaster.hf.hosts_list":
        return _hosts_list(client, args)
    if name == "webmaster.hf.host_info":
        return _host_info(client, args)
    if name == "webmaster.hf.host_add":
        return _host_add(client, args)
    if name == "webmaster.hf.host_verification":
        return _host_verification(client, args)
    if name == "webmaster.hf.verification_uinna":
        return _verification_uinna(client, args)
    if name == "webmaster.hf.sitemaps_list":
        return _sitemaps_list(client, args)
    if name == "webmaster.hf.sitemap_add":
        return _sitemap_add(client, args)
    if name == "webmaster.hf.sitemap_remove":
        return _sitemap_remove(client, args)
    if name == "webmaster.hf.external_links":
        return _external_links(client, args)
    if name == "webmaster.hf.search_queries":
        return _search_queries(client, args)
    if name == "webmaster.hf.host_summary":
        return _host_summary(client, args)
    return None


def _ensure_user_id(client: WebmasterClient) -> str:
    """Get the current user's ID (cached in the client object or fetched)."""
    # Webmaster API requires user/{user_id} prefix for most operations.
    # We fetch it on demand.
    data = _user_info(client)
    user_id = data.get("user_id")
    if not user_id:
        raise HFError("Failed to get Webmaster user_id")
    return str(user_id)


# ── User info ───────────────────────────────────────────────────────────
def _user_info(client: WebmasterClient) -> dict[str, Any]:
    """Get current user info (user_id, login)."""
    data = client.get("user/")
    return {
        "user_id": data.get("user_id"),
        "login": data.get("login"),
    }


# ── Hosts ───────────────────────────────────────────────────────────────
def _hosts_list(client: WebmasterClient, args: dict[str, Any]) -> dict[str, Any]:
    """List all verified and unverified hosts for the user."""
    user_id = args.get("user_id") or _ensure_user_id(client)
    page = args.get("page", 0)
    per_page = args.get("per_page", 50)
    data = client.get(f"user/{user_id}/hosts/?page={page}&per_page={per_page}")
    return {
        "hosts": data.get("hosts", []),
        "count": data.get("count", 0),
    }


def _host_info(client: WebmasterClient, args: dict[str, Any]) -> dict[str, Any]:
    """Get host/site details from Webmaster."""
    host_id = args.get("host_id")
    if not host_id:
        raise HFError("host_id is required (e.g., 'example.com:https' or numeric id)")
    user_id = args.get("user_id") or _ensure_user_id(client)
    data = client.get(f"user/{user_id}/hosts/{host_id}/")
    return {"host": data}


def _host_add(client: WebmasterClient, args: dict[str, Any]) -> dict[str, Any]:
    """Add a new host/site to Webmaster."""
    host_url = args.get("host_url")
    if not host_url:
        raise HFError("host_url is required (e.g., 'https://example.com')")
    user_id = args.get("user_id") or _ensure_user_id(client)
    data = client.post(f"user/{user_id}/hosts/", {"host_url": host_url})
    return {"result": data}


# ── Verification ────────────────────────────────────────────────────────
def _host_verification(client: WebmasterClient, args: dict[str, Any]) -> dict[str, Any]:
    """Get verification status for a host."""
    host_id = args.get("host_id")
    if not host_id:
        raise HFError("host_id is required")
    user_id = args.get("user_id") or _ensure_user_id(client)
    data = client.get(f"user/{user_id}/hosts/{host_id}/verification/")
    return {"verification": data}


def _verification_uinna(client: WebmasterClient, args: dict[str, Any]) -> dict[str, Any]:
    """Set verification uinna for a host."""
    host_id = args.get("host_id")
    uinna = args.get("uinna")
    if not host_id or not uinna:
        raise HFError("host_id and uinna are required")
    user_id = args.get("user_id") or _ensure_user_id(client)
    data = client.put(f"user/{user_id}/hosts/{host_id}/verification/", {"uinna": uinna})
    return {"result": data}


# ── Sitemaps ────────────────────────────────────────────────────────────
def _sitemaps_list(client: WebmasterClient, args: dict[str, Any]) -> dict[str, Any]:
    """List sitemaps for a host."""
    host_id = args.get("host_id")
    if not host_id:
        raise HFError("host_id is required")
    user_id = args.get("user_id") or _ensure_user_id(client)
    data = client.get(f"user/{user_id}/hosts/{host_id}/sitemaps/")
    return {"sitemaps": data.get("sitemaps", [])}


def _sitemap_add(client: WebmasterClient, args: dict[str, Any]) -> dict[str, Any]:
    """Add a sitemap URL for a host."""
    host_id = args.get("host_id")
    sitemap_url = args.get("sitemap_url")
    if not host_id or not sitemap_url:
        raise HFError("host_id and sitemap_url are required")
    user_id = args.get("user_id") or _ensure_user_id(client)
    data = client.post(f"user/{user_id}/hosts/{host_id}/sitemaps/", {"url": sitemap_url})
    return {"result": data}


def _sitemap_remove(client: WebmasterClient, args: dict[str, Any]) -> dict[str, Any]:
    """Remove a sitemap from a host."""
    host_id = args.get("host_id")
    sitemap_id = args.get("sitemap_id")
    if not host_id or not sitemap_id:
        raise HFError("host_id and sitemap_id are required")
    user_id = args.get("user_id") or _ensure_user_id(client)
    data = client.delete(f"user/{user_id}/hosts/{host_id}/sitemaps/{sitemap_id}/")
    return {"deleted": True}


# ── External links ──────────────────────────────────────────────────────
def _external_links(client: WebmasterClient, args: dict[str, Any]) -> dict[str, Any]:
    """Get external links for a host."""
    host_id = args.get("host_id")
    if not host_id:
        raise HFError("host_id is required")
    user_id = args.get("user_id") or _ensure_user_id(client)
    data = client.get(f"user/{user_id}/hosts/{host_id}/external-links/")
    return {"links": data.get("links", []), "count": data.get("count", 0)}


# ── Search queries ──────────────────────────────────────────────────────
def _search_queries(client: WebmasterClient, args: dict[str, Any]) -> dict[str, Any]:
    """Get popular search queries for a host."""
    host_id = args.get("host_id")
    if not host_id:
        raise HFError("host_id is required")
    user_id = args.get("user_id") or _ensure_user_id(client)
    query_id = args.get("query_id")
    if query_id:
        data = client.get(f"user/{user_id}/hosts/{host_id}/search-queries/{query_id}/")
        return {"query": data}
    data = client.get(f"user/{user_id}/hosts/{host_id}/search-queries/")
    return {"queries": data.get("queries", []), "count": data.get("count", 0)}


# ── Summary ─────────────────────────────────────────────────────────────
def _host_summary(client: WebmasterClient, args: dict[str, Any]) -> dict[str, Any]:
    """Get host summary (indexing stats, TIC, etc.)."""
    host_id = args.get("host_id")
    if not host_id:
        raise HFError("host_id is required")
    user_id = args.get("user_id") or _ensure_user_id(client)
    data = client.get(f"user/{user_id}/hosts/{host_id}/summary/")
    return {"summary": data}
