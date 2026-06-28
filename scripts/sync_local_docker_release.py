"""Pull released images and refresh local Docker aliases."""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class ImageSpec:
    remote: str
    local_aliases: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release version, for example 2.0.13")
    parser.add_argument("--owner", default="georgy-agaev", help="GHCR/Docker owner")
    parser.add_argument(
        "--include-pro",
        action="store_true",
        help="Also sync the PRO image from ghcr.io/<owner>/yandex-direct-metrica-mcp-pro:pro-vX.Y.Z",
    )
    return parser.parse_args()


def run(*args: str) -> None:
    subprocess.run(list(args), check=True)


def specs(owner: str, version: str, include_pro: bool) -> list[ImageSpec]:
    items = [
        ImageSpec(
            remote=f"ghcr.io/{owner}/yandex-direct-metrica-mcp:v{version}",
            local_aliases=(
                "yandex-direct-metrica-mcp:latest",
                f"ghcr.io/{owner}/yandex-direct-metrica-mcp:latest",
                f"docker.io/{owner}/yandex-direct-metrica-mcp:latest",
            ),
        )
    ]
    if include_pro:
        items.append(
            ImageSpec(
                remote=f"ghcr.io/{owner}/yandex-direct-metrica-mcp-pro:pro-v{version}",
                local_aliases=(
                    "yandex-direct-metrica-mcp-pro:latest",
                    f"ghcr.io/{owner}/yandex-direct-metrica-mcp-pro:latest",
                    f"docker.io/{owner}/yandex-direct-metrica-mcp-pro:latest",
                ),
            )
        )
    return items


def main() -> int:
    args = parse_args()
    for item in specs(args.owner, args.version, args.include_pro):
        print(f"== pull {item.remote} ==")
        run("docker", "pull", item.remote)
        for alias in item.local_aliases:
            print(f"tag {item.remote} -> {alias}")
            run("docker", "tag", item.remote, alias)
    print("Local Docker aliases refreshed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
