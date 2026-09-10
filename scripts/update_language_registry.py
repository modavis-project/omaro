#!/usr/bin/env python3
"""Update the vendored, compact IANA Language Subtag Registry snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

REGISTRY_URL = (
    "https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry"
)


def parse_registry(text: str) -> dict:
    blocks = text.replace("\r\n", "\n").split("%%")
    header = blocks.pop(0).strip()
    file_date = header.removeprefix("File-Date:").strip()
    records: list[dict[str, object]] = []
    for block in blocks:
        fields: dict[str, object] = {}
        last_key: str | None = None
        for line in block.strip().splitlines():
            if line.startswith("  ") and last_key:
                value = fields[last_key]
                if isinstance(value, list):
                    value[-1] += " " + line.strip()
                else:
                    fields[last_key] = f"{value} {line.strip()}"
                continue
            key, separator, value = line.partition(":")
            if not separator:
                continue
            last_key = key
            value = value.strip()
            if key in fields:
                previous = fields[key]
                fields[key] = (
                    [*previous, value]
                    if isinstance(previous, list)
                    else [previous, value]
                )
            else:
                fields[key] = value
        if fields:
            records.append(fields)
    return {
        "file_date": file_date,
        "source_uri": REGISTRY_URL,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/registries/iana-language-subtag-registry.json"),
    )
    args = parser.parse_args()
    response = requests.get(REGISTRY_URL, timeout=(10, 60))
    response.raise_for_status()
    data = parse_registry(response.text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote IANA registry {data['file_date']} to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
