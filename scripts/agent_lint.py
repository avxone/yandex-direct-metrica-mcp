"""Lint only changed Python lines for agent-generated work."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Files or directories to inspect")
    parser.add_argument(
        "--base-ref",
        help="Optional git base ref. When omitted, compare the working tree to HEAD.",
    )
    return parser.parse_args()


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _expand_paths(paths: list[str]) -> list[Path]:
    expanded: list[Path] = []
    for raw in paths:
        path = (ROOT / raw).resolve()
        if path.is_dir():
            expanded.extend(sorted(path.rglob("*.py")))
        elif path.suffix == ".py" and path.exists():
            expanded.append(path)
    if expanded:
        return sorted(dict.fromkeys(expanded))

    tracked = set(_git("ls-files", "*.py").splitlines())
    untracked = set(_git("ls-files", "--others", "--exclude-standard", "*.py").splitlines())
    candidates = sorted((tracked | untracked))
    return [(ROOT / item).resolve() for item in candidates]


def _diff_ranges(paths: list[Path], base_ref: str | None) -> dict[str, set[int]]:
    rel_paths = [str(path.relative_to(ROOT)) for path in paths]
    diff_args = ["diff", "--unified=0", "--no-color"]
    if base_ref:
        diff_args.append(f"{base_ref}...HEAD")
    else:
        diff_args.append("HEAD")
    diff_args.extend(["--", *rel_paths])
    diff = _git(*diff_args)

    ranges: dict[str, set[int]] = {}
    current = ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            ranges.setdefault(current, set())
            continue
        if not line.startswith("@@") or not current:
            continue
        try:
            hunk = line.split("+", 1)[1].split(" ", 1)[0]
            start_s, _, count_s = hunk.partition(",")
            start = int(start_s)
            count = int(count_s or "1")
        except Exception:
            continue
        if count <= 0:
            continue
        ranges[current].update(range(start, start + count))
    return ranges


def _ruff(paths: list[Path]) -> list[dict]:
    if not paths:
        return []
    result = subprocess.run(
        ["ruff", "check", "--output-format", "json", *[str(path.relative_to(ROOT)) for path in paths]],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if not result.stdout.strip():
        return []
    data = json.loads(result.stdout)
    if not isinstance(data, list):
        raise SystemExit("Unexpected ruff JSON output")
    return data


def main() -> int:
    args = parse_args()
    paths = _expand_paths(args.paths)
    ranges = _diff_ranges(paths, args.base_ref)
    changed_paths = {path for path in paths if ranges.get(str(path.relative_to(ROOT)))}
    if not changed_paths:
        print("No changed Python lines to lint.")
        return 0

    issues = []
    for item in _ruff(sorted(changed_paths)):
        rel_path = item.get("filename")
        row = ((item.get("location") or {}).get("row"))
        if not isinstance(rel_path, str) or not isinstance(row, int):
            continue
        if row not in ranges.get(rel_path, set()):
            continue
        issues.append(item)

    if not issues:
        print("Lint OK for changed Python lines.")
        return 0

    for item in issues:
        rel_path = item["filename"]
        location = item["location"]
        code = item["code"]
        message = item["message"]
        print(f"{rel_path}:{location['row']}:{location['column']}: {code} {message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
