from pathlib import Path

from scripts.prepare_pr import build_pr_body, slugify


def test_slugify_normalizes_and_truncates() -> None:
    value = "PR: GEO-7 Add search_serp MCP tool and client handoff for Marketing2025"
    result = slugify(value)
    assert result.startswith("pr-geo-7-add-search-serp-mcp-tool-and-client")
    assert len(result) <= 48


def test_build_pr_body_embeds_handoff_text() -> None:
    handoff = "# SYMPHONY_WORK_RESULT\n\n- tests passed"
    body = build_pr_body("GEO-8", "PR stage", handoff)
    assert "## Summary" in body
    assert "- GEO-8: PR stage" in body
    assert "# SYMPHONY_WORK_RESULT" in body


def test_prepare_pr_writes_expected_markdown(tmp_path: Path) -> None:
    handoff = tmp_path / "SYMPHONY_WORK_RESULT.md"
    handoff.write_text("handoff content", encoding="utf-8")
    body = build_pr_body("GEO-8", "Example title", handoff.read_text(encoding="utf-8"))
    output = tmp_path / "PR_BODY.md"
    output.write_text(body, encoding="utf-8")
    assert output.read_text(encoding="utf-8").startswith("## Summary")
