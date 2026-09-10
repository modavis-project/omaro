#!/usr/bin/env python3
"""Deterministically rebuild linguistic profiles inside canonical schema 2.1."""

from __future__ import annotations

import json
from pathlib import Path

from omaro.language_registry import LanguageSubtagRegistry
from omaro.model import (
    canonical_json,
    label_profiles_from_assertions,
    read_jsonl,
    script_registry_record,
    write_jsonl,
)
from omaro.refresh import finalize_metadata
from omaro.script_registry import UnicodeScriptRegistry


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    canonical = root / "data/canonical"
    registries = root / "data/registries"
    language_registry = LanguageSubtagRegistry.load(
        registries / "iana-language-subtag-registry.json"
    )
    script_path = registries / "unicode-script-registry.json"
    script_registry = UnicodeScriptRegistry.load(script_path)
    script_rows = [script_registry_record(script_path)]
    label_profiles = label_profiles_from_assertions(
        read_jsonl(canonical / "label_assertions.jsonl"),
        language_registry,
        script_registry,
        script_rows[0]["uri"],
    )
    write_jsonl(
        canonical / "script_registries.jsonl",
        script_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "label_profiles.jsonl",
        label_profiles,
        key=lambda row: row["uri"],
    )
    metadata = json.loads((canonical / "metadata.json").read_text(encoding="utf-8"))
    metadata["schema_version"] = "2.1.0"
    finalize_metadata(canonical, metadata)
    print(
        canonical_json(
            {
                "label_profiles": len(label_profiles),
                "script_registries": len(script_rows),
                "unicode_version": script_registry.unicode_version,
            },
            indent=2,
        ),
        end="",
    )


if __name__ == "__main__":
    main()
