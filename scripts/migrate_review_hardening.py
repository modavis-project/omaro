#!/usr/bin/env python3
"""Migrate the unpublished canonical snapshot to schema 2.1 review semantics."""

from __future__ import annotations

import json
from pathlib import Path

from omaro.language_registry import LanguageSubtagRegistry
from omaro.model import (
    EXACT_MATCH,
    HS_SCHEME,
    MIMO_PERSPECTIVE,
    classification_assertions_from_source_relations,
    default_applicability_scopes,
    default_projection_policies,
    label_assertions_from_labels,
    label_profiles_from_assertions,
    label_resources_from_assertions,
    language_registry_record,
    linguistic_quality_findings,
    note_assertions_from_concepts,
    read_jsonl,
    script_registry_record,
    write_jsonl,
)
from omaro.refresh import finalize_metadata
from omaro.script_registry import UnicodeScriptRegistry


def migrate(repo_root: Path) -> None:
    canonical = repo_root / "data" / "canonical"
    registries = repo_root / "data" / "registries"
    metadata_path = canonical / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["schema_version"] = "2.1.0"

    concepts = read_jsonl(canonical / "concepts.jsonl")
    concepts_by_uri = {row["uri"]: row for row in concepts}
    labels = read_jsonl(canonical / "labels.jsonl")
    source_relations = read_jsonl(canonical / "source_relations.jsonl")
    language_registry_path = registries / "iana-language-subtag-registry.json"
    script_registry_path = registries / "unicode-script-registry.json"
    language_registry = LanguageSubtagRegistry.load(language_registry_path)
    script_registry = UnicodeScriptRegistry.load(script_registry_path)
    language_record = language_registry_record(language_registry_path)
    script_record = script_registry_record(script_registry_path)

    label_assertions = label_assertions_from_labels(
        labels,
        concepts_by_uri,
        metadata,
        language_registry,
        language_record["uri"],
    )
    label_resources = label_resources_from_assertions(label_assertions)
    label_profiles = label_profiles_from_assertions(
        label_assertions,
        language_registry,
        script_registry,
        script_record["uri"],
    )
    note_assertions = note_assertions_from_concepts(
        concepts, metadata, language_registry, language_record["uri"]
    )
    quality_findings = linguistic_quality_findings(
        label_assertions, note_assertions, concepts_by_uri, metadata["generated_at"]
    )

    existing_assignments = read_jsonl(canonical / "classification_assertions.jsonl")
    preserved_assignments = [
        row
        for row in existing_assignments
        if not (
            row.get("assertion_origin") == "source-derived"
            and row.get("classification_scheme_uri") == HS_SCHEME
            and row.get("perspective_uri") == MIMO_PERSPECTIVE
            and row.get("source_predicate_uri") == EXACT_MATCH
        )
    ]
    for row in preserved_assignments:
        singular = row.pop("authority_assignment_uri", None)
        row.setdefault("authority_assignment_uris", [singular] if singular else [])

    relation_assertions = read_jsonl(canonical / "concept_relation_assertions.jsonl")
    for row in relation_assertions:
        singular = row.pop("authority_assignment_uri", None)
        row.setdefault("authority_assignment_uris", [singular] if singular else [])
        row.setdefault("valid_from", None)
        row.setdefault("valid_until", None)

    review_events = read_jsonl(canonical / "review_events.jsonl")
    for row in review_events:
        singular = row.pop("authority_assignment_uri", None)
        row.setdefault("authority_assignment_uris", [singular] if singular else [])
        row.setdefault("suspends_event_uri", None)
        row.setdefault("reinstates_event_uri", None)

    write_jsonl(
        canonical / "applicability_scopes.jsonl",
        default_applicability_scopes(),
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "projection_policies.jsonl",
        default_projection_policies(),
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "label_assertions.jsonl",
        label_assertions,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "label_resources.jsonl",
        label_resources,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "label_profiles.jsonl",
        label_profiles,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "note_assertions.jsonl",
        note_assertions,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "quality_findings.jsonl",
        quality_findings,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "classification_assertions.jsonl",
        [
            *classification_assertions_from_source_relations(
                source_relations, metadata
            ),
            *preserved_assignments,
        ],
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "concept_relation_assertions.jsonl",
        relation_assertions,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "review_events.jsonl",
        review_events,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "language_registries.jsonl",
        [language_record],
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical / "script_registries.jsonl",
        [script_record],
        key=lambda row: row["uri"],
    )
    finalize_metadata(canonical, metadata)


if __name__ == "__main__":
    migrate(Path(__file__).resolve().parents[1])
