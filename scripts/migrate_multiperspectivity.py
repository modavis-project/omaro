#!/usr/bin/env python3
"""Migrate the unpublished canonical snapshot to multiperspectival schema 2.1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from omaro.model import (
    EXACT_MATCH,
    HS_SCHEME,
    MIMO_PERSPECTIVE,
    classification_assertions_from_source_relations,
    default_applicability_scopes,
    default_concept_schemes,
    default_perspectives,
    default_projection_policies,
    read_jsonl,
    write_jsonl,
)
from omaro.refresh import finalize_metadata


def migrate(repo_root: Path) -> None:
    canonical = repo_root / "data" / "canonical"
    metadata_path = canonical / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["schema_version"] = "2.1.0"

    concepts = read_jsonl(canonical / "concepts.jsonl")
    for concept in concepts:
        concept["local_id"] = concept.get("local_id") or concept.get("mimo_id")
        concept.setdefault("mimo_id", None)
    write_jsonl(canonical / "concepts.jsonl", concepts, key=lambda row: row["uri"])

    def existing(name: str) -> list[dict]:
        path = canonical / name
        return read_jsonl(path) if path.exists() else []

    def merge_defaults(name: str, defaults: list[dict]) -> list[dict]:
        rows = {row["uri"]: row for row in existing(name)}
        rows.update({row["uri"]: row for row in defaults})
        return list(rows.values())

    write_jsonl(
        canonical / "concept_schemes.jsonl",
        merge_defaults("concept_schemes.jsonl", default_concept_schemes(metadata)),
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "perspectives.jsonl",
        merge_defaults("perspectives.jsonl", default_perspectives()),
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "applicability_scopes.jsonl",
        merge_defaults("applicability_scopes.jsonl", default_applicability_scopes()),
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "projection_policies.jsonl",
        merge_defaults("projection_policies.jsonl", default_projection_policies()),
        key=lambda row: row["uri"],
    )
    for name in ("authority_assignments.jsonl", "concept_relation_assertions.jsonl"):
        path = canonical / name
        if not path.exists():
            path.write_text("", encoding="utf-8")

    source_relations = read_jsonl(canonical / "source_relations.jsonl")
    preserved_assignments = [
        row
        for row in existing("classification_assertions.jsonl")
        if not (
            row.get("assertion_origin") == "source-derived"
            and row.get("classification_scheme_uri") == HS_SCHEME
            and row.get("perspective_uri") == MIMO_PERSPECTIVE
            and row.get("source_predicate_uri") == EXACT_MATCH
        )
    ]
    assignments = [
        *classification_assertions_from_source_relations(source_relations, metadata),
        *preserved_assignments,
    ]
    write_jsonl(
        canonical / "classification_assertions.jsonl",
        assignments,
        key=lambda row: row["uri"],
    )
    finalize_metadata(canonical, metadata)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    migrate(args.repo_root.resolve())


if __name__ == "__main__":
    main()
