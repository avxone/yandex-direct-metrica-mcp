"""Create Linear issues from local Markdown drafts.

This script is intentionally small and dependency-free. It reads Linear auth
from LINEAR_API_KEY and project/team defaults from a local JSON config.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path("/Users/georgyagaev/Projects/Symphony_yaad/linear.yandexad.json")
LINEAR_ENDPOINT = "https://api.linear.app/graphql"


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Config not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON config {path}: {exc}") from None


def read_markdown(path: Path | None, text: str | None) -> str:
    if path and text:
        raise SystemExit("Use either --from or --body, not both")
    if path:
        return path.read_text(encoding="utf-8").strip()
    if text:
        return text.strip()
    data = sys.stdin.read().strip()
    if data:
        return data
    raise SystemExit("Provide issue body with --from, --body, or stdin")


def parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def graphql(api_key: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        LINEAR_ENDPOINT,
        data=payload,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Linear API HTTP {exc.code}: {details}") from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"Linear API request failed: {exc}") from None

    data = json.loads(body)
    if data.get("errors"):
        raise SystemExit(json.dumps(data["errors"], indent=2, ensure_ascii=False))
    return data


def team_labels(api_key: str, team_id: str) -> dict[str, str]:
    query = """
    query($teamId: String!) {
      team(id: $teamId) {
        labels(first: 100) {
          nodes { id name }
        }
      }
    }
    """
    data = graphql(api_key, query, {"teamId": team_id})
    nodes = data["data"]["team"]["labels"]["nodes"]
    return {node["name"].strip().lower(): node["id"] for node in nodes}


def team_states(api_key: str, team_id: str) -> dict[str, str]:
    query = """
    query($teamId: String!) {
      team(id: $teamId) {
        states(first: 100) {
          nodes { id name }
        }
      }
    }
    """
    data = graphql(api_key, query, {"teamId": team_id})
    nodes = data["data"]["team"]["states"]["nodes"]
    return {node["name"].strip().lower(): node["id"] for node in nodes}


def create_label(api_key: str, team_id: str, name: str) -> str:
    query = """
    mutation($teamId: String!, $name: String!) {
      issueLabelCreate(input: {teamId: $teamId, name: $name}) {
        success
        issueLabel { id name }
      }
    }
    """
    data = graphql(api_key, query, {"teamId": team_id, "name": name})
    return data["data"]["issueLabelCreate"]["issueLabel"]["id"]


def resolve_label_ids(api_key: str, team_id: str, labels: list[str], create_missing: bool) -> list[str]:
    existing = team_labels(api_key, team_id)
    label_ids: list[str] = []
    for label in labels:
        key = label.strip().lower()
        if key in existing:
            label_ids.append(existing[key])
            continue
        if not create_missing:
            raise SystemExit(f"Linear label not found: {label}")
        label_id = create_label(api_key, team_id, label)
        existing[key] = label_id
        label_ids.append(label_id)
    return label_ids


def resolve_state_id(api_key: str, team_id: str, state: str) -> str:
    states = team_states(api_key, team_id)
    key = state.strip().lower()
    if key not in states:
        names = ", ".join(sorted(states))
        raise SystemExit(f"Linear state not found: {state}. Available: {names}")
    return states[key]


def build_input(args: argparse.Namespace, config: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    team_id = args.team_id or config.get("teamId")
    project_id = args.project_id or config.get("projectId")
    if not team_id:
        raise SystemExit("Missing teamId in config or --team-id")
    if not project_id:
        raise SystemExit("Missing projectId in config or --project-id")

    body = read_markdown(args.body_file, args.body)
    labels = list(dict.fromkeys([*config.get("defaultLabels", []), *parse_csv(args.labels)]))
    state = args.state or config.get("defaultState") or "Backlog"

    result: dict[str, Any] = {
        "teamId": team_id,
        "projectId": project_id,
        "title": args.title,
        "description": body,
    }
    if api_key:
        result["stateId"] = resolve_state_id(api_key, team_id, state)
        result["labelIds"] = resolve_label_ids(api_key, team_id, labels, args.create_missing_labels)
    else:
        result["stateName"] = state
        result["labels"] = labels
    return result


def create_issue(api_key: str, input_payload: dict[str, Any]) -> dict[str, Any]:
    query = """
    mutation($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue {
          id
          identifier
          title
          url
          state { name }
          labels { nodes { name } }
        }
      }
    }
    """
    data = graphql(api_key, query, {"input": input_payload})
    return data["data"]["issueCreate"]["issue"]


def render_preview(input_payload: dict[str, Any]) -> str:
    visible = dict(input_payload)
    description = visible.get("description", "")
    if len(description) > 1_200:
        visible["description"] = description[:1_200] + "\n\n[truncated preview]"
    return json.dumps(visible, indent=2, ensure_ascii=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["preview", "create"])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--from", dest="body_file", type=Path)
    parser.add_argument("--body")
    parser.add_argument("--title", required=True)
    parser.add_argument("--labels", help="Comma-separated labels to add")
    parser.add_argument("--state", help="Linear state name; defaults to config defaultState or Backlog")
    parser.add_argument("--team-id")
    parser.add_argument("--project-id")
    parser.add_argument(
        "--create-missing-labels",
        action="store_true",
        help="Create missing team-level issue labels before creating the issue",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_json(args.config)

    api_key = os.environ.get("LINEAR_API_KEY")
    if args.command == "create" and not api_key:
        raise SystemExit("LINEAR_API_KEY is required for create")

    input_payload = build_input(args, config, api_key if args.command == "create" else None)
    if args.command == "preview":
        print(render_preview(input_payload))
        return 0

    issue = create_issue(api_key or "", input_payload)
    print(f"{issue['identifier']} {issue['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

