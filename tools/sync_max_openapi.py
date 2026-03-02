#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import urlopen


DEFAULT_SOURCE_URL = (
    "https://raw.githubusercontent.com/max-messenger/max-bot-api-client-go/main/schemes/schema.yaml"
)
DEFAULT_OUTPUT_PATH = Path("vendor/max_bot_api/schema.yaml")


def download_schema(source_url: str) -> str:
    with urlopen(source_url) as response:  # nosec B310 - fixed trusted URL by default
        raw = response.read()
    return raw.decode("utf-8")


def write_schema(contents: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(contents, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync MAX OpenAPI schema into vendor directory")
    parser.add_argument("--source", default=DEFAULT_SOURCE_URL, help="Source URL for schema.yaml")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Output path for downloaded schema",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    contents = download_schema(args.source)
    if "openapi:" not in contents:
        raise RuntimeError("downloaded file does not look like OpenAPI schema")
    write_schema(contents, output_path)
    print("Schema synced to {0}".format(output_path))


if __name__ == "__main__":
    main()
