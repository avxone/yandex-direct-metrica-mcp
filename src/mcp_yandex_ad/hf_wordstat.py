"""Human-friendly (HF) tools for Yandex Wordstat."""

from __future__ import annotations

import base64
import json
import re
from typing import Any

from .hf_common import HFError, ensure_hf_enabled, hf_payload


def _b64encode_json(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _b64decode_json(value: str) -> dict[str, Any]:
    try:
        raw = base64.urlsafe_b64decode(value.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HFError("Invalid cursor (expected base64 JSON).") from exc
    if not isinstance(data, dict):
        raise HFError("Invalid cursor payload (expected object).")
    return data


def _normalize_phrase(value: Any) -> str:
    return str(value or "").strip()


def _top_requests_items(resp: dict[str, Any]) -> list[dict[str, Any]]:
    items = resp.get("topRequests")
    if isinstance(items, list):
        return [x for x in items if isinstance(x, dict)]
    return []


def _tokenize(phrase: str) -> list[str]:
    phrase = (phrase or "").lower()
    # Keep letters/digits and basic separators.
    phrase = re.sub(r"[^\w\s-]+", " ", phrase, flags=re.UNICODE)
    parts = [p.strip() for p in re.split(r"[\s-]+", phrase) if p.strip()]
    return parts


_NEGATIVE_LEXICON = {
    "ru": {
        "скачать": "noncommercial_intent",
        "бесплатно": "noncommercial_intent",
        "торрент": "noncommercial_intent",
        "вакансии": "jobs_intent",
        "работа": "jobs_intent",
        "резюме": "jobs_intent",
        "отзывы": "research_intent",
        "форум": "research_intent",
        "что": "question_intent",
        "как": "question_intent",
        "почему": "question_intent",
        "инструкция": "research_intent",
        "б/у": "secondhand_intent",
        "бу": "secondhand_intent",
        "avito": "marketplace_intent",
    },
    "en": {
        "free": "noncommercial_intent",
        "download": "noncommercial_intent",
        "torrent": "noncommercial_intent",
        "jobs": "jobs_intent",
        "vacancy": "jobs_intent",
        "resume": "jobs_intent",
        "review": "research_intent",
        "forum": "research_intent",
        "how": "question_intent",
        "what": "question_intent",
        "why": "question_intent",
        "used": "secondhand_intent",
        "avito": "marketplace_intent",
    },
}


def handle(tool: str, ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    ensure_hf_enabled(ctx.config)

    if tool == "wordstat.hf.suggest_keywords":
        cursor = args.get("cursor")
        if cursor:
            state = _b64decode_json(str(cursor))
            remaining = state.get("remaining_seeds") or []
            acc = state.get("acc") or {}
        else:
            remaining = args.get("seed_phrases") or []
            acc = {}

        if not isinstance(remaining, list) or not all(isinstance(x, (str, int, float)) for x in remaining):
            raise HFError("seed_phrases must be an array of strings")

        remaining_seeds = [_normalize_phrase(x) for x in remaining if _normalize_phrase(x)]
        if not remaining_seeds:
            return hf_payload(tool=tool, status="ok", result={"candidates": [], "seeds_processed": 0})

        max_per_call = int(args.get("max_seed_phrases_per_call") or 8)
        max_per_call = max(1, min(32, max_per_call))
        num_phrases = int(args.get("num_phrases") or 50)
        if num_phrases <= 0 or num_phrases > 2000:
            raise HFError("num_phrases must be between 1 and 2000")
        max_candidates = int(args.get("max_candidates") or 200)
        max_candidates = max(10, min(2000, max_candidates))

        regions = args.get("regions")
        devices = args.get("devices")

        chunk = remaining_seeds[:max_per_call]
        tail = remaining_seeds[max_per_call:]

        # Load accumulator.
        acc_map: dict[str, dict[str, Any]] = {}
        if isinstance(acc, dict):
            for k, v in acc.items():
                if isinstance(k, str) and isinstance(v, dict):
                    score = v.get("score")
                    sources = v.get("sources")
                    if isinstance(score, (int, float)) and isinstance(sources, list):
                        acc_map[k] = {"score": float(score), "sources": [str(x) for x in sources if str(x).strip()]}

        for seed in chunk:
            resp = ctx._wordstat_post(  # type: ignore[attr-defined]
                "topRequests",
                {
                    "phrase": seed,
                    **({"regions": regions} if isinstance(regions, list) and regions else {}),
                    **({"devices": devices} if isinstance(devices, list) and devices else {}),
                    "numPhrases": num_phrases,
                },
            )
            for item in _top_requests_items(resp):
                phrase = _normalize_phrase(item.get("phrase"))
                if not phrase:
                    continue
                try:
                    count = float(item.get("count") or 0)
                except Exception:
                    continue
                if count <= 0:
                    continue
                cur = acc_map.setdefault(phrase, {"score": 0.0, "sources": []})
                cur["score"] = float(cur.get("score") or 0.0) + count
                if seed not in cur["sources"]:
                    cur["sources"].append(seed)

        # Keep accumulator bounded (cursor size).
        sorted_items = sorted(acc_map.items(), key=lambda kv: float(kv[1].get("score") or 0.0), reverse=True)
        bounded = dict(sorted_items[: max_candidates * 2])

        candidates = [
            {"phrase": phrase, "score": float(meta.get("score") or 0.0), "sources": meta.get("sources") or []}
            for phrase, meta in sorted_items[:max_candidates]
        ]

        result = {
            "seeds_processed": len(chunk),
            "seeds_remaining": len(tail),
            "candidates": candidates,
        }

        if tail:
            next_cursor = _b64encode_json({"remaining_seeds": tail, "acc": bounded})
            return hf_payload(tool=tool, status="pending", result=result, preview={"cursor": next_cursor})

        return hf_payload(tool=tool, status="ok", result=result)

    if tool == "wordstat.hf.suggest_negative_keywords":
        phrases = args.get("phrases") or []
        if not isinstance(phrases, list):
            raise HFError("phrases must be an array of strings")
        normalized = [_normalize_phrase(x) for x in phrases if _normalize_phrase(x)]
        if not normalized:
            return hf_payload(tool=tool, status="ok", result={"negatives": []})

        language = str(args.get("language") or "ru").strip().lower()
        lex = _NEGATIVE_LEXICON.get(language) or _NEGATIVE_LEXICON["ru"]

        counts: dict[str, int] = {}
        for phrase in normalized:
            tokens = _tokenize(phrase)
            for token in tokens:
                if token in lex:
                    counts[token] = counts.get(token, 0) + 1

        max_candidates = int(args.get("max_candidates") or 100)
        max_candidates = max(10, min(500, max_candidates))

        out = []
        for token, cnt in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:max_candidates]:
            out.append({"token": token, "count": cnt, "reason": lex.get(token)})

        return hf_payload(tool=tool, status="ok", result={"negatives": out})

    raise HFError(f"Unknown HF Wordstat tool: {tool}")

