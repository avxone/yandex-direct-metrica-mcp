"""Prepare a deterministic branch name and PR body for Symphony workspaces."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue-id", required=True, help="Linear shorthand identifier, for example GEO-7")
    parser.add_argument("--title", required=True, help="Issue title")
    parser.add_argument(
        "--work-result",
        type=Path,
        default=Path("SYMPHONY_WORK_RESULT.md"),
        help="Path to the workspace handoff file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the PR body markdown. When omitted, prints JSON only.",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-")[:48] or "change"


def build_pr_body(issue_id: str, title: str, handoff: str) -> str:
    return "\n".join(
        [
            f"## Summary",
            f"- {issue_id}: {title}",
            "",
            "## Symphony Handoff",
            "",
            handoff.strip(),
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    handoff = args.work_result.read_text(encoding="utf-8").strip()
    branch = f"issue/{args.issue_id.lower()}-{slugify(args.title)}"
    commit_title = f"{args.issue_id}: {args.title}"
    pr_body = build_pr_body(args.issue_id, args.title, handoff)

    if args.output:
        args.output.write_text(pr_body, encoding="utf-8")

    payload = {
        "branch": branch,
        "commit_title": commit_title,
        "pr_title": commit_title,
        "pr_body_path": str(args.output) if args.output else None,
        "pr_body_preview": pr_body[:800],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
