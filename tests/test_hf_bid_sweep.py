import base64
import json

import pytest

from mcp_yandex_ad.hf_common import HFError
from mcp_yandex_ad.hf_direct import handle as hf_direct_handle


class DummyConfig:
    hf_enabled = True
    hf_write_enabled = True

    def __init__(self, *, use_sandbox: bool):
        self.use_sandbox = use_sandbox


class DummyCtx:
    def __init__(self, *, use_sandbox: bool, tsv: str | None = None):
        self.config = DummyConfig(use_sandbox=use_sandbox)
        self.direct_client_login = "login-a"
        self._tsv = tsv or ""
        self.calls: list[tuple[str, str, dict]] = []

    def _direct_get(self, resource, params):  # noqa: ANN001
        if resource == "keywords":
            return {
                "result": {
                    "Keywords": [
                        {"Id": 101, "Keyword": "a"},
                        {"Id": 102, "Keyword": "b"},
                        {"Id": 103, "Keyword": "---autotargeting"},
                    ]
                }
            }
        raise AssertionError(f"Unexpected _direct_get: {resource}")

    def _direct_call(self, resource, method, params):  # noqa: ANN001
        self.calls.append((resource, method, params))
        return {"result": {"ok": True}}

    def _direct_report(self, params):  # noqa: ANN001
        return {"raw": self._tsv}


def _decode_plan_id(plan_id: str) -> dict:
    padded = plan_id + "=" * (-len(plan_id) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    return json.loads(raw.decode("utf-8"))


def _tsv(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def test_bid_sweep_plan_builds_plan_id_and_steps():
    ctx = DummyCtx(use_sandbox=True)
    out = hf_direct_handle(
        "direct.hf.bid_sweep_plan",
        ctx,
        {"campaign_id": 1, "bid_steps_rub": [10, 20], "max_keywords": 2},
    )
    assert out["status"] == "ok"
    plan_id = out["result"]["plan_id"]
    plan = _decode_plan_id(plan_id)
    assert plan["kind"] == "bid_sweep"
    assert plan["campaign_id"] == 1
    assert plan["keyword_ids"] == [101, 102]
    assert len(plan["steps"]) == 2


def test_bid_sweep_run_requires_sandbox():
    ctx = DummyCtx(use_sandbox=False)
    plan_out = hf_direct_handle(
        "direct.hf.bid_sweep_plan",
        ctx,
        {"campaign_id": 1, "bid_steps_rub": [10]},
    )
    plan_id = plan_out["result"]["plan_id"]
    with pytest.raises(HFError):
        hf_direct_handle(
            "direct.hf.bid_sweep_run",
            ctx,
            {"plan_id": plan_id, "step_index": 0, "apply": True},
        )


def test_bid_sweep_analyze_aggregates_keyword_metrics():
    raw = _tsv(
        "Date\tCampaignId\tAdGroupId\tKeywordId\tImpressions\tClicks\tCost",
        "2026-02-01\t1\t10\t101\t100\t10\t100000000",
        "2026-02-01\t1\t10\t102\t50\t5\t50000000",
        "2026-02-01\t1\t10\t999\t100\t10\t100000000",
    )
    ctx = DummyCtx(use_sandbox=True, tsv=raw)
    plan_out = hf_direct_handle(
        "direct.hf.bid_sweep_plan",
        ctx,
        {"campaign_id": 1, "bid_steps_rub": [10]},
    )
    plan_id = plan_out["result"]["plan_id"]

    out = hf_direct_handle(
        "direct.hf.bid_sweep_analyze",
        ctx,
        {
            "plan_id": plan_id,
            "windows": [{"step_index": 0, "date_from": "2026-02-01", "date_to": "2026-02-01"}],
            "include_per_keyword": True,
        },
    )
    assert out["status"] == "ok"
    win = out["result"]["by_window"][0]
    assert win["matched_keywords"] == 2
    assert win["metrics"]["impressions"] == 150.0
    assert win["metrics"]["clicks"] == 15.0
    assert win["metrics"]["cost_rub"] == 150.0
