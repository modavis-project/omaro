"""Intentional network refresh from MIMO's native SKOS API."""

from __future__ import annotations

import json
import hashlib
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from rdflib import Graph, URIRef
from rdflib.namespace import SKOS

from .model import (
    BROADER,
    EXACT_MATCH,
    HS_PREFIX,
    HS_SCHEME,
    INSTRUMENT_PREFIX,
    INSTRUMENT_SCHEME,
    MIMO_PERSPECTIVE,
    canonical_json,
    classification_assertions_from_source_relations,
    classification_expressions_from_concepts,
    default_applicability_scopes,
    default_agents,
    default_concept_schemes,
    default_perspectives,
    default_projection_policies,
    default_quality_rules,
    default_review_statuses,
    label_assertions_from_labels,
    label_profiles_from_assertions,
    label_resources_from_assertions,
    note_assertions_from_concepts,
    linguistic_quality_findings,
    language_registry_record,
    script_registry_record,
    read_jsonl,
    source_records_from_metadata,
    write_jsonl,
)
from .language_registry import LanguageSubtagRegistry
from .script_registry import UnicodeScriptRegistry

API_ROOT = "https://vocabulary.mimo-international.com/rest/v1"
RESERVED_DOI = "10.5281/zenodo.21442777"
DC_CREATED = URIRef("http://purl.org/dc/elements/1.1/created")


def finalize_metadata(canonical_dir: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    """Add canonical counts, coverage, unresolved URIs, and content checksums."""
    concepts = read_jsonl(canonical_dir / "concepts.jsonl")
    labels = read_jsonl(canonical_dir / "labels.jsonl")
    label_resources = read_jsonl(canonical_dir / "label_resources.jsonl")
    label_profiles = read_jsonl(canonical_dir / "label_profiles.jsonl")
    agents = read_jsonl(canonical_dir / "agents.jsonl")
    source_records = read_jsonl(canonical_dir / "source_records.jsonl")
    concept_schemes = read_jsonl(canonical_dir / "concept_schemes.jsonl")
    perspectives = read_jsonl(canonical_dir / "perspectives.jsonl")
    applicability_scopes = read_jsonl(canonical_dir / "applicability_scopes.jsonl")
    authority_assignments = read_jsonl(canonical_dir / "authority_assignments.jsonl")
    projection_policies = read_jsonl(canonical_dir / "projection_policies.jsonl")
    review_statuses = read_jsonl(canonical_dir / "review_statuses.jsonl")
    language_registries = read_jsonl(canonical_dir / "language_registries.jsonl")
    script_registries = read_jsonl(canonical_dir / "script_registries.jsonl")
    quality_rules = read_jsonl(canonical_dir / "quality_rules.jsonl")
    quality_findings = read_jsonl(canonical_dir / "quality_findings.jsonl")
    review_events = read_jsonl(canonical_dir / "review_events.jsonl")
    protocol_applications = read_jsonl(canonical_dir / "protocol_applications.jsonl")
    use_decisions = read_jsonl(canonical_dir / "use_decisions.jsonl")
    organological_targets = read_jsonl(canonical_dir / "organological_targets.jsonl")
    classification_criteria = read_jsonl(
        canonical_dir / "classification_criteria.jsonl"
    )
    observation_assessments = read_jsonl(
        canonical_dir / "observation_assessments.jsonl"
    )
    classification_expressions = read_jsonl(
        canonical_dir / "classification_expressions.jsonl"
    )
    label_assertions = read_jsonl(canonical_dir / "label_assertions.jsonl")
    note_assertions = read_jsonl(canonical_dir / "note_assertions.jsonl")
    source_relations = read_jsonl(canonical_dir / "source_relations.jsonl")
    concept_relation_assertions = read_jsonl(
        canonical_dir / "concept_relation_assertions.jsonl"
    )
    classification_assertions = read_jsonl(
        canonical_dir / "classification_assertions.jsonl"
    )
    metadata = dict(metadata)
    metadata["counts"] = {
        "concepts": len(concepts),
        "classifications": sum(row["kind"] == "classification" for row in concepts),
        "resolved_instruments": sum(
            row["kind"] == "instrument" and row["resolution_status"] == "resolved"
            for row in concepts
        ),
        "unresolved_stubs": sum(
            row["resolution_status"] == "unresolved" for row in concepts
        ),
        "labels": len(labels),
        "label_resources": len(label_resources),
        "label_profiles": len(label_profiles),
        "agents": len(agents),
        "source_records": len(source_records),
        "concept_schemes": len(concept_schemes),
        "perspectives": len(perspectives),
        "applicability_scopes": len(applicability_scopes),
        "authority_assignments": len(authority_assignments),
        "projection_policies": len(projection_policies),
        "review_statuses": len(review_statuses),
        "language_registries": len(language_registries),
        "script_registries": len(script_registries),
        "quality_rules": len(quality_rules),
        "quality_findings": len(quality_findings),
        "review_events": len(review_events),
        "protocol_applications": len(protocol_applications),
        "use_decisions": len(use_decisions),
        "organological_targets": len(organological_targets),
        "classification_criteria": len(classification_criteria),
        "observation_assessments": len(observation_assessments),
        "classification_expressions": len(classification_expressions),
        "label_assertions": len(label_assertions),
        "note_assertions": len(note_assertions),
        "source_relations": len(source_relations),
        "concept_relation_assertions": len(concept_relation_assertions),
        "classification_assertions": len(classification_assertions),
    }
    metadata["language_coverage"] = dict(
        sorted(
            Counter(
                row["language"] for row in labels if row["label_type"] == "preferred"
            ).items()
        )
    )
    metadata["label_type_counts"] = dict(
        sorted(Counter(row["label_type"] for row in labels).items())
    )
    metadata["unresolved_references"] = sorted(
        row["uri"] for row in concepts if row["resolution_status"] == "unresolved"
    )
    metadata["canonical_checksums"] = {
        name: hashlib.sha256((canonical_dir / name).read_bytes()).hexdigest()
        for name in (
            "agents.jsonl",
            "source_records.jsonl",
            "concept_schemes.jsonl",
            "perspectives.jsonl",
            "applicability_scopes.jsonl",
            "authority_assignments.jsonl",
            "projection_policies.jsonl",
            "review_statuses.jsonl",
            "language_registries.jsonl",
            "script_registries.jsonl",
            "quality_rules.jsonl",
            "quality_findings.jsonl",
            "review_events.jsonl",
            "protocol_applications.jsonl",
            "use_decisions.jsonl",
            "organological_targets.jsonl",
            "classification_criteria.jsonl",
            "observation_assessments.jsonl",
            "classification_expressions.jsonl",
            "concepts.jsonl",
            "labels.jsonl",
            "label_resources.jsonl",
            "label_profiles.jsonl",
            "label_assertions.jsonl",
            "note_assertions.jsonl",
            "source_relations.jsonl",
            "concept_relation_assertions.jsonl",
            "classification_assertions.jsonl",
        )
    }
    (canonical_dir / "metadata.json").write_text(
        canonical_json(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def _get(url: str, params: dict[str, str], attempts: int = 4) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=(10, 45),
                headers={
                    "User-Agent": "omaro/1.0 (+https://github.com/modavis-project/omaro)"
                },
            )
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    raise RuntimeError(f"MIMO request failed: {url} {params}") from last_error


def _language(value: Any) -> str:
    language = str(value.language or "und")
    return "da" if language == "dk" else language


def _submitted_language(value: Any) -> str:
    return str(value.language or "und")


def _labels_from_graph(graph: Graph, node: URIRef) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for predicate, label_type in (
        (SKOS.prefLabel, "preferred"),
        (SKOS.altLabel, "alternative"),
        (SKOS.hiddenLabel, "hidden"),
    ):
        for value in graph.objects(node, predicate):
            if str(value).strip():
                result.append(
                    {
                        "language": _language(value),
                        "submitted_language": _submitted_language(value),
                        "label_type": label_type,
                        "label": str(value).strip(),
                    }
                )
    return result


def _fetch_class(
    source: dict[str, Any],
) -> tuple[dict[str, Any], list[str], list[dict[str, str]], list[str]]:
    uri = f"{HS_PREFIX}{source['MIMOPage']}"
    data_response = _get(
        f"{API_ROOT}/HornbostelAndSachs/data",
        {"uri": uri, "format": "text/turtle"},
    )
    graph = Graph().parse(data=data_response.text, format="turtle")
    node = URIRef(uri)
    broader = sorted(str(value) for value in graph.objects(node, SKOS.broader))
    definitions = sorted(str(value) for value in graph.objects(node, SKOS.definition))
    labels = _labels_from_graph(graph, node)
    mappings_response = _get(
        f"{API_ROOT}/HornbostelAndSachs/mappings",
        {"uri": uri, "lang": "en", "clang": "en"},
    )
    targets: list[str] = []
    for mapping in mappings_response.json().get("mappings") or []:
        if "skos:exactMatch" not in mapping.get("type", []):
            continue
        for member in mapping.get("to", {}).get("memberSet", []):
            target_uri = member.get("uri")
            if target_uri and target_uri.startswith(INSTRUMENT_PREFIX):
                targets.append(target_uri)
    concept = {
        "uri": uri,
        "scheme_uri": HS_SCHEME,
        "kind": "classification",
        "local_id": str(source["MIMOPage"]),
        "mimo_id": str(source["MIMOPage"]),
        "notation": next(
            (str(value) for value in graph.objects(node, SKOS.notation)),
            source.get("Notation"),
        ),
        "definition": definitions[0] if definitions else source.get("Description", ""),
        "resolution_status": "resolved",
    }
    created = next((str(value) for value in graph.objects(node, DC_CREATED)), None)
    if created:
        concept["created"] = created
    return (
        concept,
        broader,
        labels
        or [
            {
                "language": "en",
                "submitted_language": "en",
                "label_type": "preferred",
                "label": source["Label"],
            }
        ],
        sorted(set(targets)),
    )


def _fetch_instrument(
    item: dict[str, Any],
) -> tuple[dict[str, Any], list[str], list[dict[str, str]]]:
    uri = f"{INSTRUMENT_PREFIX}{item['MIMOPage']}"
    response = _get(
        f"{API_ROOT}/InstrumentsKeywords/data",
        {"uri": uri, "format": "text/turtle"},
    )
    graph = Graph().parse(data=response.text, format="turtle")
    node = URIRef(uri)
    labels = _labels_from_graph(graph, node)
    if not any(row["label_type"] == "preferred" for row in labels):
        labels.extend(
            {
                "language": "da" if language == "dk" else language,
                "submitted_language": language,
                "label_type": "preferred",
                "label": label.strip(),
            }
            for language, label in (item.get("Translations") or {}).items()
            if language
            and language != "null"
            and isinstance(label, str)
            and label.strip()
        )
    concept = {
        "uri": uri,
        "scheme_uri": INSTRUMENT_SCHEME,
        "kind": "instrument",
        "local_id": str(item["MIMOPage"]),
        "mimo_id": str(item["MIMOPage"]),
        "resolution_status": "resolved",
    }
    created = next((str(value) for value in graph.objects(node, DC_CREATED)), None)
    if created:
        concept["created"] = created
    broader = sorted(str(value) for value in graph.objects(node, SKOS.broader))
    return concept, broader, labels


def refresh_from_legacy(
    repo_root: Path, canonical_dir: Path, workers: int = 4
) -> dict[str, int]:
    def existing_rows(name: str) -> list[dict[str, Any]]:
        path = canonical_dir / name
        return read_jsonl(path) if path.exists() else []

    mimo_scheme_uris = {HS_SCHEME, INSTRUMENT_SCHEME}
    existing_concepts = existing_rows("concepts.jsonl")
    preserved_concepts = {
        row["uri"]: row
        for row in existing_concepts
        if row["scheme_uri"] not in mimo_scheme_uris
    }
    preserved_concept_uris = set(preserved_concepts)
    preserved_labels = [
        row
        for row in existing_rows("labels.jsonl")
        if row["concept_uri"] in preserved_concept_uris
    ]
    preserved_label_assertions = [
        row
        for row in existing_rows("label_assertions.jsonl")
        if row["concept_uri"] in preserved_concept_uris
    ]
    preserved_note_assertions = [
        row
        for row in existing_rows("note_assertions.jsonl")
        if row["concept_uri"] in preserved_concept_uris
    ]
    existing_classification_assertions = existing_rows(
        "classification_assertions.jsonl"
    )
    classifications_raw = json.loads(
        (repo_root / "hornbostelSachs.json").read_text(encoding="utf-8")
    )
    translations_raw = json.loads(
        (repo_root / "translations.json").read_text(encoding="utf-8")
    )

    concepts: dict[str, dict[str, Any]] = dict(preserved_concepts)
    labels: list[dict[str, str]] = list(preserved_labels)
    relations: set[tuple[str, str, str, str]] = set()

    source_rows = []
    for notation, item in classifications_raw.items():
        source_rows.append({**item, "Notation": notation})

    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_fetch_class, item): item for item in source_rows}
        for index, future in enumerate(as_completed(futures), 1):
            item = futures[future]
            try:
                concept, broader, class_labels, targets = future.result()
            except Exception as exc:
                failures.append(f"{item['MIMOPage']}: {exc}")
                continue
            concepts[concept["uri"]] = concept
            for label in class_labels:
                labels.append(
                    {
                        "concept_uri": concept["uri"],
                        "language": label["language"],
                        "submitted_language": label["submitted_language"],
                        "label_type": label["label_type"],
                        "label": label["label"],
                    }
                )
            for parent in broader:
                relations.add((concept["uri"], BROADER, parent, concept["uri"]))
            for target in targets:
                relations.add((concept["uri"], EXACT_MATCH, target, concept["uri"]))
            if index % 50 == 0:
                print(f"Fetched {index}/{len(source_rows)} classifications")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_fetch_instrument, item): item for item in translations_raw
        }
        for index, future in enumerate(as_completed(futures), 1):
            item = futures[future]
            try:
                concept, broader, instrument_labels = future.result()
            except Exception as exc:
                failures.append(f"instrument {item['MIMOPage']}: {exc}")
                continue
            concepts[concept["uri"]] = concept
            for label in instrument_labels:
                labels.append(
                    {
                        "concept_uri": concept["uri"],
                        "language": label["language"],
                        "submitted_language": label["submitted_language"],
                        "label_type": label["label_type"],
                        "label": label["label"],
                    }
                )
            for parent in broader:
                relations.add((concept["uri"], BROADER, parent, concept["uri"]))
            if index % 100 == 0:
                print(f"Fetched {index}/{len(translations_raw)} instruments")

    if failures:
        raise RuntimeError(
            "Refresh was incomplete; canonical data was not written:\n"
            + "\n".join(failures)
        )

    relation_targets = {row[2] for row in relations}
    for uri in sorted(relation_targets - concepts.keys()):
        if not uri.startswith(INSTRUMENT_PREFIX):
            raise RuntimeError(f"Unknown non-instrument relation target: {uri}")
        concepts[uri] = {
            "uri": uri,
            "scheme_uri": INSTRUMENT_SCHEME,
            "kind": "instrument",
            "local_id": uri.rsplit("/", 1)[-1],
            "mimo_id": uri.rsplit("/", 1)[-1],
            "resolution_status": "unresolved",
        }

    unique_labels = {
        (
            row["concept_uri"],
            row["language"],
            row["label_type"],
            row["label"],
        ): row
        for row in labels
    }
    source_relation_rows = [
        {
            "subject_uri": subject,
            "predicate_uri": predicate,
            "object_uri": obj,
            "source_uri": source,
        }
        for subject, predicate, obj, source in relations
    ]
    timestamp = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    metadata = {
        "name": "OMARO",
        "ontology_title": (
            "Ontology for Multiperspectivity, Assertions, and Review in Organology"
        ),
        "preferred_namespace_prefix": "omaro",
        "namespace_uri": "https://w3id.org/modavis/omaro#",
        "ontology_uri": "https://w3id.org/modavis/omaro/ontology",
        "ontology_version_iri": "https://w3id.org/modavis/omaro/ontology/0.1.0",
        "dataset_uri": "https://w3id.org/modavis/omaro/dataset/0.1.0",
        "repository_uri": "https://github.com/modavis-project/omaro",
        "dataset_version": "0.1.0",
        "schema_version": "0.1.0",
        "title": (
            "OMARO Reference Dataset: Hornbostel–Sachs Classifications and "
            "Multilingual Musical Instrument Names"
        ),
        "generated_at": timestamp,
        "source_retrieved_at": timestamp,
        "license": "CC0-1.0",
        "doi": RESERVED_DOI,
        "creators": [
            {
                "name": "Dominik Ukolov",
                "affiliations": [
                    "Research Group DIGITAL ORGANOLOGY, Leipzig University",
                    "Digital Humanities (Image/Object), Friedrich Schiller University Jena",
                ],
            }
        ],
        "contributors": [{"name": "MODAVIS Project", "role": "DataCurator"}],
        "sources": [
            "https://vocabulary.mimo-international.com/rest/v1/HornbostelAndSachs",
            "https://vocabulary.mimo-international.com/rest/v1/InstrumentsKeywords",
        ],
        "schemes": [
            {"uri": HS_SCHEME, "label": "Hornbostel-Sachs classification"},
            {
                "uri": INSTRUMENT_SCHEME,
                "label": "Thesaurus of musical instrument names",
            },
        ],
    }
    canonical_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(
        canonical_dir / "concepts.jsonl", concepts.values(), key=lambda row: row["uri"]
    )
    write_jsonl(
        canonical_dir / "labels.jsonl",
        unique_labels.values(),
        key=lambda row: (
            row["concept_uri"],
            row["language"],
            row["label_type"],
            row["label"],
        ),
    )

    def merge_registry(
        generated: list[dict[str, Any]], existing: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        rows = {row["uri"]: row for row in existing}
        rows.update({row["uri"]: row for row in generated})
        return list(rows.values())

    agent_rows = merge_registry(default_agents(), existing_rows("agents.jsonl"))
    source_record_rows = [
        *source_records_from_metadata(metadata),
        *[
            row
            for row in existing_rows("source_records.jsonl")
            if row["scheme_uri"] not in mimo_scheme_uris
        ],
    ]
    concept_scheme_rows = merge_registry(
        default_concept_schemes(metadata),
        [
            row
            for row in existing_rows("concept_schemes.jsonl")
            if row["uri"] not in mimo_scheme_uris
        ],
    )
    perspective_rows = merge_registry(
        default_perspectives(), existing_rows("perspectives.jsonl")
    )
    applicability_scope_rows = merge_registry(
        default_applicability_scopes(),
        existing_rows("applicability_scopes.jsonl"),
    )
    projection_policy_rows = merge_registry(
        default_projection_policies(), existing_rows("projection_policies.jsonl")
    )
    authority_assignment_path = canonical_dir / "authority_assignments.jsonl"
    authority_assignment_rows = (
        read_jsonl(authority_assignment_path)
        if authority_assignment_path.exists()
        else []
    )
    concept_relation_path = canonical_dir / "concept_relation_assertions.jsonl"
    concept_relation_rows = (
        read_jsonl(concept_relation_path) if concept_relation_path.exists() else []
    )
    review_status_rows = default_review_statuses()
    registry_path = (
        canonical_dir.parent / "registries/iana-language-subtag-registry.json"
    )
    registry = LanguageSubtagRegistry.load(registry_path)
    language_registry_rows = [language_registry_record(registry_path)]
    registry_uri = language_registry_rows[0]["uri"]
    script_registry_path = (
        canonical_dir.parent / "registries/unicode-script-registry.json"
    )
    script_registry = UnicodeScriptRegistry.load(script_registry_path)
    script_registry_rows = [script_registry_record(script_registry_path)]
    source_concepts = {
        uri: row
        for uri, row in concepts.items()
        if row["scheme_uri"] in mimo_scheme_uris
    }
    source_labels = [
        row for row in unique_labels.values() if row["concept_uri"] in source_concepts
    ]
    label_assertion_rows = [
        *label_assertions_from_labels(
            source_labels, source_concepts, metadata, registry, registry_uri
        ),
        *preserved_label_assertions,
    ]
    label_resource_rows = label_resources_from_assertions(label_assertion_rows)
    label_profile_rows = label_profiles_from_assertions(
        label_assertion_rows,
        registry,
        script_registry,
        script_registry_rows[0]["uri"],
    )
    note_assertion_rows = [
        *note_assertions_from_concepts(
            source_concepts.values(), metadata, registry, registry_uri
        ),
        *preserved_note_assertions,
    ]
    quality_rule_rows = default_quality_rules()
    quality_finding_rows = linguistic_quality_findings(
        label_assertion_rows, note_assertion_rows, concepts, metadata["generated_at"]
    )
    review_event_path = canonical_dir / "review_events.jsonl"
    review_event_rows = (
        read_jsonl(review_event_path) if review_event_path.exists() else []
    )
    preserved_registries = {
        name: existing_rows(name)
        for name in (
            "protocol_applications.jsonl",
            "use_decisions.jsonl",
            "organological_targets.jsonl",
            "classification_criteria.jsonl",
            "observation_assessments.jsonl",
        )
    }
    expression_rows = classification_expressions_from_concepts(
        concepts.values(), metadata
    )
    write_jsonl(
        canonical_dir / "agents.jsonl",
        agent_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "source_records.jsonl",
        source_record_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "concept_schemes.jsonl",
        concept_scheme_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "perspectives.jsonl",
        perspective_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "applicability_scopes.jsonl",
        applicability_scope_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        authority_assignment_path,
        authority_assignment_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "projection_policies.jsonl",
        projection_policy_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "review_statuses.jsonl",
        review_status_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "language_registries.jsonl",
        language_registry_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "script_registries.jsonl",
        script_registry_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "quality_rules.jsonl",
        quality_rule_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "quality_findings.jsonl",
        quality_finding_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        review_event_path,
        review_event_rows,
        key=lambda row: row["uri"],
    )
    for name, rows in preserved_registries.items():
        write_jsonl(canonical_dir / name, rows, key=lambda row: row["uri"])
    write_jsonl(
        canonical_dir / "classification_expressions.jsonl",
        expression_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "label_resources.jsonl",
        label_resource_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "label_profiles.jsonl",
        label_profile_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "label_assertions.jsonl",
        label_assertion_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "note_assertions.jsonl",
        note_assertion_rows,
        key=lambda row: row["uri"],
    )
    write_jsonl(
        canonical_dir / "source_relations.jsonl",
        source_relation_rows,
        key=lambda row: (row["subject_uri"], row["predicate_uri"], row["object_uri"]),
    )
    write_jsonl(
        concept_relation_path,
        concept_relation_rows,
        key=lambda row: row["uri"],
    )
    preserved_classification_assertions = [
        row
        for row in existing_classification_assertions
        if not (
            row.get("assertion_origin") == "source-derived"
            and row.get("classification_scheme_uri") == HS_SCHEME
            and row.get("perspective_uri") == MIMO_PERSPECTIVE
            and row.get("source_predicate_uri") == EXACT_MATCH
        )
    ]
    classification_assertions = [
        *classification_assertions_from_source_relations(
            source_relation_rows, metadata, expression_rows
        ),
        *preserved_classification_assertions,
    ]
    write_jsonl(
        canonical_dir / "classification_assertions.jsonl",
        classification_assertions,
        key=lambda row: row["uri"],
    )
    finalize_metadata(canonical_dir, metadata)
    return {
        "concepts": len(concepts),
        "labels": len(unique_labels),
        "source_relations": len(source_relation_rows),
        "classification_assertions": len(classification_assertions),
        "label_assertions": len(label_assertion_rows),
        "label_resources": len(label_resource_rows),
        "label_profiles": len(label_profile_rows),
        "note_assertions": len(note_assertion_rows),
        "agents": len(agent_rows),
        "source_records": len(source_record_rows),
        "review_statuses": len(review_status_rows),
        "language_registries": len(language_registry_rows),
        "script_registries": len(script_registry_rows),
        "quality_rules": len(quality_rule_rows),
        "quality_findings": len(quality_finding_rows),
        "review_events": len(review_event_rows),
        "protocol_applications": len(
            preserved_registries["protocol_applications.jsonl"]
        ),
        "use_decisions": len(preserved_registries["use_decisions.jsonl"]),
        "organological_targets": len(
            preserved_registries["organological_targets.jsonl"]
        ),
        "classification_criteria": len(
            preserved_registries["classification_criteria.jsonl"]
        ),
        "observation_assessments": len(
            preserved_registries["observation_assessments.jsonl"]
        ),
        "classification_expressions": len(expression_rows),
        "concept_schemes": len(concept_scheme_rows),
        "perspectives": len(perspective_rows),
        "applicability_scopes": len(applicability_scope_rows),
        "authority_assignments": len(authority_assignment_rows),
        "projection_policies": len(projection_policy_rows),
        "concept_relation_assertions": len(concept_relation_rows),
    }
