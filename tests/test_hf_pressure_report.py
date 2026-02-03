from mcp_yandex_ad.hf_direct import handle as hf_direct_handle


class DummyConfig:
    hf_enabled = True


class DummyCtx:
    def __init__(self, tsv: str):
        self.config = DummyConfig()
        self._tsv = tsv
        self.last_params = None

    def _direct_report(self, params):  # noqa: ANN001
        self.last_params = params
        return {"raw": self._tsv}


def _tsv(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def test_pressure_report_maps_clusters_and_computes_metrics():
    raw = _tsv(
        "Date\tCampaignId\tAdGroupId\tQuery\tMatchedKeyword\tMatchType\tImpressions\tClicks\tCost",
        "2026-02-01\t1\t10\tкупить велосипед\tкупить велосипед\tPHRASE\t100\t10\t100",
        "2026-02-01\t1\t10\tвелосипед цена\tвелосипед\tPHRASE\t50\t5\t50",
        "2026-02-01\t1\t10\tремонт велосипеда\tремонт велосипеда\tPHRASE\t10\t1\t20",
    )
    ctx = DummyCtx(raw)
    out = hf_direct_handle(
        "direct.hf.pressure_report",
        ctx,
        {
            "date_from": "2026-02-01",
            "date_to": "2026-02-01",
            "clusters": [
                {"cluster_id": "buy", "phrases": ["купить велосипед", "велосипед цена"]},
                {"cluster_id": "repair", "phrases": ["ремонт велосипеда"]},
            ],
        },
    )

    assert out["status"] == "ok"
    result = out["result"]
    by_cluster = {r["cluster_id"]: r for r in result["by_cluster"]}
    assert by_cluster["buy"]["impressions"] == 150.0
    assert by_cluster["buy"]["clicks"] == 15.0
    assert by_cluster["buy"]["cost_rub"] == 150.0
    assert by_cluster["buy"]["coverage"] == 1.0
    assert by_cluster["repair"]["impressions"] == 10.0
    assert by_cluster["repair"]["clicks"] == 1.0
    assert by_cluster["repair"]["cost_rub"] == 20.0

    notes = result["coverage_notes"]
    assert notes["rows_total"] == 3
    assert notes["rows_mapped"] == 3
    assert notes["rows_unmapped"] == 0
    assert notes["rows_ambiguous"] == 0


def test_pressure_report_partial_when_unmapped_or_ambiguous():
    raw = _tsv(
        "Date\tCampaignId\tAdGroupId\tQuery\tMatchedKeyword\tMatchType\tImpressions\tClicks\tCost",
        "2026-02-01\t1\t10\tкупить велосипед\tкупить велосипед\tPHRASE\t100\t10\t100",
        "2026-02-01\t1\t10\tнеизвестный запрос\tнеизвестный запрос\tPHRASE\t10\t0\t0",
    )
    ctx = DummyCtx(raw)
    out = hf_direct_handle(
        "direct.hf.pressure_report",
        ctx,
        {
            "date_from": "2026-02-01",
            "date_to": "2026-02-01",
            "clusters": [
                {"cluster_id": "a", "phrases": ["купить велосипед"]},
                {"cluster_id": "b", "phrases": ["купить велосипед"]},
            ],
        },
    )

    assert out["status"] == "partial"
    notes = out["result"]["coverage_notes"]
    assert notes["rows_total"] == 2
    assert notes["rows_mapped"] == 1
    assert notes["rows_unmapped"] == 1
    assert notes["rows_ambiguous"] == 1

