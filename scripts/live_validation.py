"""Run bounded live validation checks against real configured providers."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = {
    "direct": ROOT / "scripts" / "check_direct_access.py",
    "metrica": ROOT / "scripts" / "check_metrica_access.py",
    "wordstat": ROOT / "scripts" / "check_wordstat_access.py",
    "search": ROOT / "scripts" / "check_search_serp_access.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        default="direct,metrica,wordstat",
        help="Comma-separated suites to run: direct,metrica,wordstat,search",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    requested = [name.strip().lower() for name in args.suite.split(",") if name.strip()]
    invalid = [name for name in requested if name not in SCRIPTS]
    if invalid:
        raise SystemExit(f"Unknown suites: {', '.join(invalid)}")

    failed: list[str] = []
    for name in requested:
        script = SCRIPTS[name]
        print(f"== {name} ==")
        result = subprocess.run([sys.executable, str(script)], cwd=ROOT)
        if result.returncode == 0:
            print(f"[OK] {name}")
            continue
        failed.append(name)
        print(f"[FAILED] {name} exit={result.returncode}")

    if failed:
        print(f"Live validation failed: {', '.join(failed)}")
        return 2

    print("Live validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
