from __future__ import annotations

from mcp_yandex_ad.hf_common import HF_ENVELOPE_VERSION, hf_payload


def test_hf_payload_emits_canonical_minimal_shape() -> None:
    payload = hf_payload(tool="direct.hf.find_campaigns", status="ok", result={"campaigns": []})

    assert payload["tool"] == "direct.hf.find_campaigns"
    assert payload["status"] == "ok"
    assert payload["meta"]["envelope_version"] == HF_ENVELOPE_VERSION
    assert payload["meta"]["request_id"]
    assert payload["meta"]["timestamp"]
    assert payload["result"] == {"campaigns": []}


def test_hf_payload_emits_structured_error_by_default() -> None:
    payload = hf_payload(tool="direct.hf.find_campaigns", status="error", message="campaign not found")

    assert payload["status"] == "error"
    assert payload["error"]["code"] == "hf_error"
    assert payload["error"]["type"] == "validation"
    assert payload["error"]["retryable"] is False


def test_hf_payload_normalizes_choices_and_warnings() -> None:
    payload = hf_payload(
        tool="direct.hf.find_campaigns",
        status="needs_disambiguation",
        choices=[{"Id": 123, "Name": "Campaign A"}],
        warnings=["best effort"],
    )

    assert payload["choices"] == [
        {
            "id": "123",
            "label": "Campaign A",
            "type": "entity",
            "context": {"Id": 123, "Name": "Campaign A"},
        }
    ]
    assert payload["warnings"] == [{"code": "warning", "message": "best effort", "details": {}}]
