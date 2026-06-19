"""Release gate checks for public/pro Yandex AD MCP artifacts."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"
DOCKERFILE = ROOT / "Dockerfile"
DOCS_DIR = ROOT / "docs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release version, for example 2.0.12")
    parser.add_argument(
        "--require-release-notes",
        action="store_true",
        help="Require docs/releases/vX.Y.Z.md to exist.",
    )
    return parser.parse_args()


def _fail(message: str) -> None:
    raise SystemExit(message)


def _check_version(version: str) -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    actual = data["project"]["version"]
    if actual != version:
        _fail(f"pyproject version mismatch: expected {version}, found {actual}")


def _check_changelog(version: str) -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    heading = f"## {version} - "
    if heading not in text:
        _fail(f"CHANGELOG missing release heading for {version}")


def _check_release_notes(version: str) -> None:
    release_note = DOCS_DIR / "releases" / f"v{version}.md"
    if not release_note.exists():
        _fail(f"Missing release note: {release_note}")


def _check_docker_defaults() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    required = [
        "ARG MCP_EDITION=public",
        "ARG MCP_PUBLIC_READONLY=true",
    ]
    for marker in required:
        if marker not in text:
            _fail(f"Dockerfile missing required default: {marker}")


def _check_docs_paths() -> None:
    forbidden = ("/Users/", "~/")
    for path in DOCS_DIR.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for marker in forbidden:
            if marker in text:
                _fail(f"Docs contain machine-specific path {marker}: {path}")


def main() -> int:
    args = parse_args()
    _check_version(args.version)
    _check_changelog(args.version)
    if args.require_release_notes:
        _check_release_notes(args.version)
    _check_docker_defaults()
    _check_docs_paths()
    print(f"Release guard OK for {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
