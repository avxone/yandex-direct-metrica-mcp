"""Shared helpers for Yandex Search API Wordstat responses."""

from __future__ import annotations

from typing import Any


def wordstat_provider_items(resp: dict[str, Any]) -> list[dict[str, Any]]:
    """Return normalized Wordstat result/association items with source metadata."""
    out: list[dict[str, Any]] = []
    result_items = resp.get("topRequests")
    if not isinstance(result_items, list):
        result_items = resp.get("results")
    groups: tuple[tuple[Any, str], ...] = (
        (result_items, "result"),
        (resp.get("associations"), "association"),
    )
    for items, provider_source in groups:
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            phrase = str(item.get("phrase") or "").strip()
            if not phrase:
                continue
            try:
                score = float(item.get("count") or 0.0)
            except Exception:
                continue
            if score <= 0:
                continue
            out.append(
                {
                    "phrase": phrase,
                    "score": score,
                    "provider_source": provider_source,
                    "raw": item,
                }
            )
    return out


def merge_wordstat_candidate(
    acc: dict[str, dict[str, Any]],
    *,
    phrase: str,
    score: float,
    seed: str | None = None,
    provider_source: str,
) -> None:
    cur = acc.setdefault(phrase, {"score": 0.0, "sources": [], "provider_sources": []})
    cur["score"] = float(cur.get("score") or 0.0) + score
    if seed and seed not in cur["sources"]:
        cur["sources"].append(seed)
    if provider_source not in cur["provider_sources"]:
        cur["provider_sources"].append(provider_source)
