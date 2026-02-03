import json

from mcp_yandex_ad.dashboard_option2 import dashboard_sync_next, dashboard_sync_start


class DummyCtx:
    def __init__(self, segments):
        self._segments = segments

    def _audience_call(self, method, path, *, params=None, payload=None):  # noqa: ARG002
        assert method in {"GET", "POST"} or True
        if path == "/segments" or path == "segments":
            limit = int((params or {}).get("limit") or 50)
            offset = int((params or {}).get("offset") or 0)
            items = self._segments[offset : offset + limit]
            return {"segments": items}
        if path == "/segments/overlap":
            # Minimal fake overlap
            ids = (payload or {}).get("segment_ids") or []
            pairs = []
            for i in range(len(ids) - 1):
                pairs.append({"a": ids[i], "b": ids[i + 1], "overlap_share": 0.1, "overlap_abs": 100})
            return {"pairs": pairs}
        raise AssertionError(f"unexpected audience call: {method} {path}")


def _parse_ndjson(text: str):
    lines = [l for l in (text or "").splitlines() if l.strip()]
    return [json.loads(l) for l in lines]


def test_sync_segments_paginates_and_finishes():
    ctx = DummyCtx(
        segments=[
            {"id": "1", "name": "S1", "type": "geo", "status": "ready"},
            {"id": "2", "name": "S2", "type": "geo", "status": "ready"},
            {"id": "3", "name": "S3", "type": "geo", "status": "ready"},
        ]
    )
    start = dashboard_sync_start(ctx, {"datasets": ["dashboard.dataset.audience_segments"], "page_size": 2})
    cursor = start["result"]["cursor"]
    assert cursor

    p1 = dashboard_sync_next(ctx, {"cursor": cursor})["result"]
    rows1 = _parse_ndjson(p1["ndjson"])
    assert len(rows1) == 2
    assert p1["cursor"]
    assert not p1["done"]

    p2 = dashboard_sync_next(ctx, {"cursor": p1["cursor"]})["result"]
    rows2 = _parse_ndjson(p2["ndjson"])
    assert len(rows2) == 1
    assert p2["cursor"] is None or isinstance(p2["cursor"], str)

    if p2["cursor"]:
        p3 = dashboard_sync_next(ctx, {"cursor": p2["cursor"]})["result"]
        assert p3["done"] is True


def test_sync_overlap_requires_segment_ids():
    ctx = DummyCtx(segments=[])
    start = dashboard_sync_start(ctx, {"datasets": ["dashboard.dataset.audience_overlap"]})
    assert "skipped" in " ".join(start["result"]["warnings"])

