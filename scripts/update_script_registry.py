#!/usr/bin/env python3
"""Pin Unicode 17.0 Script-property data as a compact offline registry."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import requests

UNICODE_VERSION = "17.0.0"
BASE = f"https://www.unicode.org/Public/{UNICODE_VERSION}/ucd"
SCRIPTS_URL = f"{BASE}/Scripts.txt"
ALIASES_URL = f"{BASE}/PropertyValueAliases.txt"


def _get(url: str) -> bytes:
    response = requests.get(url, timeout=(10, 60))
    response.raise_for_status()
    return response.content


def _aliases(text: str) -> tuple[dict[str, str], dict[str, str]]:
    name_to_code: dict[str, str] = {
        "Common": "Zyyy",
        "Inherited": "Zinh",
        "Unknown": "Zzzz",
    }
    codes: dict[str, str] = {
        "Zyyy": "Common",
        "Zinh": "Inherited",
        "Zzzz": "Unknown",
    }
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(";")]
        if len(parts) >= 3 and parts[0] == "sc":
            code, name = parts[1], parts[2]
            name_to_code[name] = code
            codes[code] = name
    return name_to_code, codes


def _ranges(text: str, name_to_code: dict[str, str]) -> list[list[int | str]]:
    rows: list[list[int | str]] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        codepoints, script_name = [part.strip() for part in line.split(";")]
        if ".." in codepoints:
            start_text, end_text = codepoints.split("..")
        else:
            start_text = end_text = codepoints
        rows.append(
            [
                int(start_text, 16),
                int(end_text, 16),
                name_to_code[script_name],
            ]
        )
    return sorted(rows, key=lambda row: (row[0], row[1], row[2]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/registries/unicode-script-registry.json"),
    )
    args = parser.parse_args()
    scripts_bytes = _get(SCRIPTS_URL)
    aliases_bytes = _get(ALIASES_URL)
    name_to_code, codes = _aliases(aliases_bytes.decode("utf-8"))
    data = {
        "unicode_version": UNICODE_VERSION,
        "source_uris": [SCRIPTS_URL, ALIASES_URL],
        "source_sha256": {
            SCRIPTS_URL: hashlib.sha256(scripts_bytes).hexdigest(),
            ALIASES_URL: hashlib.sha256(aliases_bytes).hexdigest(),
        },
        "codes": dict(sorted(codes.items())),
        "ranges": _ranges(scripts_bytes.decode("utf-8"), name_to_code),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "unicode_version": UNICODE_VERSION,
                "codes": len(data["codes"]),
                "ranges": len(data["ranges"]),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
