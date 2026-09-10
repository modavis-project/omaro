"""Migrate canonical OMARO data to the organology and governance profile."""

from __future__ import annotations

import json
from pathlib import Path

from omaro.model import (
    MAPPING_RELATION_PREDICATES,
    STRUCTURAL_RELATION_PREDICATES,
    classification_assertions_from_source_relations,
    classification_expressions_from_concepts,
    controlled_value_uri,
    review_decision_uri,
    write_jsonl,
)
from omaro.refresh import finalize_metadata


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def _evidence_relation(rows: list[dict], default: str) -> None:
    for row in rows:
        for evidence in row.get("evidence", []):
            evidence.setdefault("relation", default)


def migrate(root: Path) -> None:
    canonical = root / "data" / "canonical"
    metadata_path = canonical / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["schema_version"] = "0.1.0"
    metadata["ontology_version_iri"] = "https://w3id.org/modavis/omaro/ontology/0.1.0"

    concepts = _rows(canonical / "concepts.jsonl")
    expressions = classification_expressions_from_concepts(concepts, metadata)
    expression_by_concept = {
        row["source_concept_uri"]: row["uri"] for row in expressions
    }
    write_jsonl(
        canonical / "classification_expressions.jsonl",
        expressions,
        key=lambda row: row["uri"],
    )

    existing_classifications = _rows(canonical / "classification_assertions.jsonl")
    classifications = classification_assertions_from_source_relations(
        _rows(canonical / "source_relations.jsonl"), metadata, expressions
    )
    classifications.extend(
        row
        for row in existing_classifications
        if row.get("assertion_origin") != "source-derived"
    )
    target_type_migrations = {
        "physical-instrument": "physical-object",
        "instrument-realization": "sounding-realization",
    }
    for row in classifications:
        if "instrument_uri" in row:
            row["target_uri"] = row.pop("instrument_uri")
        row["target_type"] = target_type_migrations.get(
            row["target_type"], row["target_type"]
        )
        old_method = row.pop("classification_method", None)
        if "classification_method_uri" not in row and old_method is not None:
            row["classification_method_uri"] = (
                old_method
                if "://" in old_method
                else controlled_value_uri("classification-method", old_method)
            )
        row.setdefault("assessment_uris", [])
        row.setdefault("inference_logic_uri", None)
        row["classification_expression_uri"] = expression_by_concept.get(
            row["classification_uri"]
        )
    _evidence_relation(classifications, "documents")
    write_jsonl(
        canonical / "classification_assertions.jsonl",
        classifications,
        key=lambda row: row["uri"],
    )

    reviews = _rows(canonical / "review_events.jsonl")
    for row in reviews:
        row["decision_uri"] = review_decision_uri(row["uri"])
        for old, new in (
            ("supersedes_event_uri", "supersedes_decision_uri"),
            ("suspends_event_uri", "suspends_decision_uri"),
            ("reinstates_event_uri", "reinstates_decision_uri"),
        ):
            predecessor = row.pop(old, None)
            row[new] = review_decision_uri(predecessor) if predecessor else row.get(new)
    _evidence_relation(reviews, "supports")
    write_jsonl(canonical / "review_events.jsonl", reviews, key=lambda row: row["uri"])

    for filename, relation in (
        ("authority_assignments.jsonl", "supports"),
        ("concept_relation_assertions.jsonl", "supports"),
    ):
        rows = _rows(canonical / filename)
        _evidence_relation(rows, relation)
        if filename == "authority_assignments.jsonl":
            for row in rows:
                row.setdefault("covered_action_uris", [])
        else:
            for row in rows:
                predicate_uri = row.get("predicate_uri")
                if predicate_uri in STRUCTURAL_RELATION_PREDICATES:
                    if row.get("mapping_purpose_uris"):
                        raise ValueError(
                            "structural relation migration cannot retain mapping "
                            f"purposes: {row.get('uri')}"
                        )
                    row["mapping_purpose_uris"] = []
                elif predicate_uri in MAPPING_RELATION_PREDICATES and not row.get(
                    "mapping_purpose_uris"
                ):
                    raise ValueError(
                        "mapping relation migration requires an explicit, "
                        f"evidence-backed mapping purpose: {row.get('uri')}"
                    )
        write_jsonl(canonical / filename, rows, key=lambda row: row["uri"])

    policies = _rows(canonical / "projection_policies.jsonl")
    for policy in policies:
        policy["policy_version"] = "2.2.0"
    write_jsonl(
        canonical / "projection_policies.jsonl",
        policies,
        key=lambda row: row["uri"],
    )

    protocol_path = canonical / "protocol_applications.jsonl"
    protocols = _rows(protocol_path)
    for row in protocols:
        if "integrity_verification_method" not in row:
            row["integrity_verification_method"] = "none"
            row["protocol_artifact_path"] = None
            row["integrity_attestation_uri"] = None
            if row.get("resolution_status") == "verified":
                row["resolution_status"] = "unverified"
                row["protocol_integrity_sha256"] = None
        else:
            row.setdefault("protocol_artifact_path", None)
            row.setdefault("integrity_attestation_uri", None)
    write_jsonl(protocol_path, protocols, key=lambda row: row["uri"])

    use_decision_path = canonical / "use_decisions.jsonl"
    use_decisions = _rows(use_decision_path)
    for row in use_decisions:
        row.setdefault("legal_basis_assessed_by_agent_uri", None)
        row.setdefault("consent_assessed_by_agent_uri", None)
    write_jsonl(use_decision_path, use_decisions, key=lambda row: row["uri"])

    for filename in (
        "organological_targets.jsonl",
        "classification_criteria.jsonl",
        "observation_assessments.jsonl",
    ):
        path = canonical / filename
        if not path.exists():
            path.touch()

    finalize_metadata(canonical, metadata)


if __name__ == "__main__":
    migrate(Path(__file__).resolve().parents[1])
