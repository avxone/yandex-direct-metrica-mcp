from scripts import linear_issue


def _issue(labels: list[str]) -> dict:
    return {
        "id": "issue-id",
        "identifier": "GEO-7",
        "title": "Add search_serp MCP tool",
        "description": "Body",
        "url": "https://linear.app/example/GEO-7",
        "state": {"name": "Done"},
        "team": {"id": "team-id"},
        "project": {"id": "project-id", "name": "Yandex.AD"},
        "labels": {"nodes": [{"id": f"id-{idx}", "name": label} for idx, label in enumerate(labels)]},
    }


def test_classify_issue_type_defaults_to_feature() -> None:
    assert linear_issue.classify_issue_type(["symphony", "search-api"]) == "feature"


def test_classify_issue_type_uses_specific_labels() -> None:
    assert linear_issue.classify_issue_type(["issue-type:pr", "symphony"]) == "pr"
    assert linear_issue.classify_issue_type(["issue-type:release", "symphony"]) == "release"


def test_inherited_followup_labels_replace_issue_type_and_preserve_context() -> None:
    labels = linear_issue.inherited_followup_labels(
        ["symphony", "search-api", "issue-type:feature", "release-required"],
        "pr",
        ["extra"],
    )
    assert labels == [
        "symphony",
        "search-api",
        "release-required",
        "issue-type:pr",
        "generated-followup",
        "extra",
    ]


def test_followup_description_for_pr_contains_pr_contract() -> None:
    body = linear_issue.followup_description("pr", _issue(["symphony", "issue-type:feature"]))
    assert "## Goal" in body
    assert "GitHub PR" in body
    assert "No GitHub Release." in body


def test_followup_description_for_release_contains_release_contract() -> None:
    body = linear_issue.followup_description(
        "release",
        _issue(["symphony", "issue-type:pr", "release-required"]),
    )
    assert "GitHub Release exists." in body
    assert "scripts/live_validation.py" in body
    assert "No new feature work." in body
