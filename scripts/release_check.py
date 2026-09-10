#!/usr/bin/env python3
"""Audit a locally built release candidate without contacting external services."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import tomllib
import zipfile
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.compare import IsomorphicGraph, to_isomorphic
from rdflib.namespace import DCAT, DCTERMS, OWL, RDF, RDFS, SKOS, VOID, XSD


PUBLIC_ARCHIVE_ROOT_FILES = {
    "AUTHORS.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "COMPETENCY_QUESTIONS.md",
    "CORRECTIONS.md",
    "CULTURAL_GOVERNANCE.md",
    "DATA_DICTIONARY.md",
    "DECOLONIAL_COMMITMENTS.md",
    "EXTERNAL_REVIEW_DECISIONS.md",
    "GOVERNANCE.md",
    "IMPLEMENTATION_VERIFICATION.md",
    "INTEROPERABILITY_PROFILES.md",
    "LICENSE",
    "MULTIPERSPECTIVITY.md",
    "MODAVIS_VAO_INTEROPERABILITY.md",
    "NAMING_AND_IDENTITY.md",
    "NOTICE",
    "ONTOLOGY_REFERENCE.md",
    "INFERENCE_AND_VALIDATION.md",
    "USE_CASES.md",
    "ORGANOLOGICAL_FOUNDATIONS.md",
    "ORGANOLOGICAL_MODEL.md",
    "PROVENANCE.md",
    "QUALITY_REPORT.md",
    "README.md",
    "RELEASE_NOTES.md",
    "RELATED_WORK.md",
    "REVIEW_PROTOCOL.md",
    "VERSION",
    "W3ID_REGISTRATION.md",
    "codemeta.json",
}
PUBLIC_ARCHIVE_GENERATED_ROOT_FILES = {"ro-crate-metadata.json"}
PUBLIC_ARCHIVE_EXAMPLES_DIR = Path("examples")
ILLUSTRATIVE_EXAMPLE_DIR = Path("examples/organological-assessment")
VERSIONED_INTERFACE_FILES = {
    ".zenodo.json",
    "schema/modavis-vao-relations.ttl",
    "site/dataset/index.html",
    "site/index.html",
    "site/ontology/index.html",
    "w3id/modavis/omaro/.htaccess",
    "w3id/modavis/omaro/README.md",
    "zenodo/metadata.json",
}
ONTOLOGY_VERSION = "0.1.0"
SCHEMA_VERSION = "0.1.0"
DATASET_VERSION = "0.1.0"
SQLITE_USER_VERSION = 20200
ONTOLOGY_CLASS_COUNT = 32
ONTOLOGY_PROPERTY_COUNT = 185
ONTOLEX_NAMESPACE = "http://www.w3.org/ns/lemon/ontolex#"
DATASET_BASE_URI = URIRef("https://w3id.org/modavis/omaro/dataset")
OMARO_NAMESPACE = Namespace("https://w3id.org/modavis/omaro#")
DCAT_NAMESPACE = Namespace("http://www.w3.org/ns/dcat#")
DQV = Namespace("http://www.w3.org/ns/dqv#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
PROV = Namespace("http://www.w3.org/ns/prov#")
SPDX = Namespace("http://spdx.org/rdf/terms#")
CC0_LICENSE = URIRef("https://creativecommons.org/publicdomain/zero/1.0/")
DCAT_3_SPECIFICATION = URIRef("https://www.w3.org/TR/vocab-dcat-3/")
IANA_ZIP_MEDIA_TYPE = URIRef(
    "https://www.iana.org/assignments/media-types/application/zip"
)
SQLITE_REQUIRED_TABLES = {
    "classification_assertions",
    "classification_assignments",
    "classification_criteria",
    "classification_expressions",
    "concept_relation_assertions",
    "endorsed_classification_assertions",
    "observation_assessments",
    "organological_targets",
    "protocol_applications",
    "review_decisions",
    "review_events",
    "use_decisions",
}
SQLITE_REQUIRED_VIEWS = {
    "classification_claims",
    "classification_claims_enriched",
    "classification_targets",
}
SQLITE_REQUIRED_COLUMNS = {
    "classification_assignments": {
        "uri",
        "assertion_uri",
        "classification_method_uri",
        "criteria_uris_json",
        "assessment_uris_json",
    },
    "classification_targets": {
        "classification_uri",
        "target_uri",
        "target_label_en",
        "target_resolution_status",
    },
    "concept_relation_assertions": {
        "uri",
        "predicate_uri",
        "mapping_purpose_uris_json",
    },
    "review_decisions": {"uri", "event_uri", "target_assertion_uri"},
    "review_events": {"uri", "reviewer_agent_uri", "reviewed_at"},
}
RELATED_WORK_REGISTRIES = {
    "classification_criteria.jsonl": "classification_criteria",
    "classification_expressions.jsonl": "classification_expressions",
    "observation_assessments.jsonl": "observation_assessments",
    "organological_targets.jsonl": "organological_targets",
    "protocol_applications.jsonl": "protocol_applications",
    "use_decisions.jsonl": "use_decisions",
}
SCHEMA_REQUIRED_FIELDS = {
    "classification_assertion.schema.json": {
        "classification_method_uri",
        "criteria_uris",
        "assessment_uris",
    },
    "classification_criterion.schema.json": {
        "applicability_scope_uris",
        "authority_assignment_uris",
        "protocol_application_uris",
    },
    "concept_relation_assertion.schema.json": {"mapping_purpose_uris"},
    "observation_assessment.schema.json": {
        "assessed_part_uri",
        "assessed_property_uri",
        "assessment_status",
        "assessment_time",
        "protocol_application_uris",
        "authority_assignment_uris",
    },
    "protocol_application.schema.json": {
        "resolution_status",
        "integrity_verification_method",
        "protocol_artifact_path",
        "integrity_attestation_uri",
        "protocol_integrity_sha256",
    },
    "use_decision.schema.json": {
        "legal_basis_uris",
        "legal_basis_status",
        "legal_basis_assessed_by_agent_uri",
        "consent_record_uris",
        "consent_status",
        "consent_assessed_by_agent_uri",
    },
}
CSV_REQUIRED_COLUMNS = {
    "classification-assignments.csv": {
        "classification_method_uri",
        "criteria_uris_json",
        "assessment_uris_json",
    },
    "classification-criteria.csv": {
        "applicability_scope_uris_json",
        "authority_assignment_uris_json",
        "protocol_application_uris_json",
    },
    "concept-relation-assertions.csv": {"mapping_purpose_uris_json"},
    "observation-assessments.csv": {
        "assessed_part_uri",
        "assessed_property_uri",
        "assessment_status",
        "assessment_time",
        "protocol_application_uris_json",
        "authority_assignment_uris_json",
    },
    "protocol-applications.csv": {
        "resolution_status",
        "integrity_verification_method",
        "protocol_artifact_path",
        "integrity_attestation_uri",
        "protocol_integrity_sha256",
    },
    "use-decisions.csv": {
        "legal_basis_uris_json",
        "legal_basis_status",
        "legal_basis_assessed_by_agent_uri",
        "consent_record_uris_json",
        "consent_status",
        "consent_assessed_by_agent_uri",
    },
}
STALE_INTERFACE_MARKERS = (b"2.1.0", b"20100")
PUBLIC_DIST_ROOTS = {
    "app.js",
    "csv",
    "data.json",
    "dataset",
    "favicon.svg",
    "index.html",
    "jsonl",
    "legacy",
    "manifest.json",
    "metadata",
    "okf",
    "ontology",
    "quality-report.json",
    "quality-report.md",
    "rdf",
    "schema",
    "sqlite",
    "styles.css",
}
PRIVATE_REPOSITORY_PATHS = {
    "DATA_PAPER_OUTLINE.md",
    "IMPACT.md",
    "RELEASE_CHECKLIST.md",
    "zenodo/README.md",
}
PRIVATE_REPOSITORY_PREFIXES = (".release-private/", "review/")
PRIVATE_FILENAMES = {
    ".env",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "secrets.json",
}
PRIVATE_SUFFIXES = {".bak", ".key", ".log", ".p12", ".pem", ".pfx", ".swp", ".tmp"}
TEXT_SUFFIXES = {
    ".cff",
    ".css",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".sql",
    ".sparql",
    ".rdf",
    ".svg",
    ".toml",
    ".ttl",
    ".txt",
    ".xml",
    ".yml",
    ".yaml",
}
SENSITIVE_PATTERNS = {
    "local macOS path": re.compile(bytes.fromhex("2f55736572732f") + rb"[^\s'\"<>]+"),
    "local Linux home path": re.compile(
        bytes.fromhex("2f686f6d652f") + rb"[^\s'\"<>]+"
    ),
    "local Windows path": re.compile(rb"[A-Za-z]:\\\\Users\\\\[^\s'\"<>]+"),
    "private key": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "GitHub token": re.compile(
        rb"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"
    ),
    "AWS access key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "bearer credential": re.compile(
        rb"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._~-]{12,}"
    ),
}
PROHIBITED_TEXT_MARKERS = {
    "legacy project slug": "6d75736963616c2d696e737472756d656e742d636c6173736573",
    "legacy Python package": "6d75736963616c5f696e737472756d656e745f636c6173736573",
    "legacy project title": "4d75736963616c20496e737472756d656e7420436c6173736573",
    "legacy project namespace": (
        "68747470733a2f2f773369642e6f72672f6d6f64617669732f6d75736963616c2d"
        "696e737472756d656e742d636c6173736573"
    ),
    "legacy RDF declaration": "40707265666978206d69633a",
    "legacy SPARQL prefix": "707265666978206d69633a",
    "prohibited authorship marker 1": "43686174475054",
    "prohibited authorship marker 2": "4f70656e4149",
    "prohibited authorship marker 3": "436c61756465",
    "prohibited authorship marker 4": "436f70696c6f74",
    "prohibited authorship marker 5": "47656d696e69",
    "prohibited authorship marker 6": "436f646578",
    "prohibited authorship phrase 1": "617320616e204149",
    "prohibited authorship phrase 2": "41492d67656e657261746564",
    "prohibited authorship phrase 3": "4c4c4d2d67656e657261746564",
    "prohibited authorship phrase 4": ("6c61726765206c616e6775616765206d6f64656c"),
    "prohibited authorship phrase 5": "41492d6173736973746564",
    "prohibited authorship phrase 6": "4c4c4d2d6173736973746564",
}
HISTORY_AUTHORSHIP_MARKERS = {
    label: encoded
    for label, encoded in PROHIBITED_TEXT_MARKERS.items()
    if "authorship" in label
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def cff_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(?:\"([^\"]*)\"|([^#\n]+))", text)
    if not match:
        return None
    return (match.group(1) or match.group(2)).strip()


def rdf_isomorphism_fingerprint(path: Path, rdf_format: str) -> tuple[int, int]:
    """Return the cardinality and canonical digest of one RDF serialization."""
    graph = IsomorphicGraph()
    graph.parse(path, format=rdf_format)
    return len(graph), graph.graph_digest()


def sensitive_findings(data: bytes) -> list[str]:
    findings = [
        label for label, pattern in SENSITIVE_PATTERNS.items() if pattern.search(data)
    ]
    folded = data.lower()
    findings.extend(
        label
        for label, encoded in PROHIBITED_TEXT_MARKERS.items()
        if bytes.fromhex(encoded).lower() in folded
    )
    return findings


def path_is_private(path: PurePosixPath) -> bool:
    return (
        any(
            part in PRIVATE_FILENAMES or part.startswith(".env.") for part in path.parts
        )
        or path.suffix.lower() in PRIVATE_SUFFIXES
    )


def audit_public_repository(root: Path, errors: list[str]) -> None:
    if not (root / ".git").exists():
        return
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    paths = [Path(value.decode()) for value in result.stdout.split(b"\0") if value]
    for relative in paths:
        name = relative.as_posix()
        require(
            name not in PRIVATE_REPOSITORY_PATHS
            and not name.startswith(PRIVATE_REPOSITORY_PREFIXES),
            f"maintainer-only file is part of the public repository surface: {name}",
            errors,
        )
        require(
            not path_is_private(PurePosixPath(name)),
            f"credential or private working-file path is public: {name}",
            errors,
        )
        path = root / relative
        if path.is_file():
            for finding in sensitive_findings(path.read_bytes()):
                errors.append(f"{finding} found in public repository file: {name}")


def audit_public_history(root: Path, errors: list[str]) -> None:
    if not (root / ".git").exists():
        return
    revisions = subprocess.run(
        ["git", "rev-list", "--all"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if not revisions:
        return
    command = ["git", "grep", "-a", "-l", "-i"]
    for encoded in HISTORY_AUTHORSHIP_MARKERS.values():
        command.extend(("-e", bytes.fromhex(encoded).decode("utf-8")))
    result = subprocess.run(
        [*command, *revisions, "--"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in {0, 1}:
        errors.append(f"commit-history text audit failed: {result.stderr.strip()}")
        return
    for location in result.stdout.splitlines():
        errors.append(
            f"prohibited authorship marker found in commit history: {location}"
        )

    metadata_commands = (
        ["git", "log", "--all", "--format=fuller"],
        [
            "git",
            "for-each-ref",
            "--format=%(refname)%00%(subject)%00%(contents)%00%(taggername)%00%(taggeremail)",
            "refs/heads",
            "refs/tags",
            "refs/remotes",
        ],
    )
    for command in metadata_commands:
        metadata = subprocess.run(
            command,
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout.lower()
        for label, encoded in HISTORY_AUTHORSHIP_MARKERS.items():
            if bytes.fromhex(encoded).lower() in metadata:
                errors.append(f"{label} found in commit, tag, or reference metadata")


def audit_illustrative_examples(root: Path, errors: list[str]) -> None:
    bundle = root / ILLUSTRATIVE_EXAMPLE_DIR
    manifest_path = bundle / "manifest.json"
    require(bundle.is_dir(), "missing illustrative example bundle", errors)
    require(
        (bundle / "README.md").is_file(),
        "illustrative example bundle omits README.md",
        errors,
    )
    require(
        manifest_path.is_file(),
        "illustrative example bundle omits manifest.json",
        errors,
    )
    if not manifest_path.is_file():
        return
    manifest = load_json(manifest_path)
    for field in ("canonical", "empirical_data", "community_authorization"):
        require(
            manifest.get(field) is False,
            f"illustrative example manifest must set {field} to false",
            errors,
        )

    declared_jsonl: set[str] = set()
    parsed_records: dict[str, list[dict[str, Any]]] = {}
    schema_root = (root / "schema").resolve()
    for entry in manifest.get("files", []):
        relative = PurePosixPath(entry.get("path", ""))
        require(
            len(relative.parts) == 1 and relative.suffix == ".jsonl",
            f"unsafe or non-JSONL illustrative example path: {relative}",
            errors,
        )
        if len(relative.parts) != 1 or relative.suffix != ".jsonl":
            continue
        name = relative.as_posix()
        require(
            name not in declared_jsonl,
            f"duplicate example manifest path: {name}",
            errors,
        )
        declared_jsonl.add(name)
        data_path = bundle / name
        schema_path = (bundle / entry.get("schema", "")).resolve()
        require(
            data_path.is_file(), f"missing illustrative example file: {name}", errors
        )
        require(
            schema_path.is_file() and schema_root in schema_path.parents,
            f"missing or out-of-tree example schema for {name}",
            errors,
        )
        if not data_path.is_file() or not schema_path.is_file():
            continue
        validator = Draft202012Validator(
            load_json(schema_path), format_checker=FormatChecker()
        )
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(
            data_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSON in {name}:{line_number}: {exc.msg}")
                continue
            records.append(record)
            for finding in validator.iter_errors(record):
                location = "/".join(str(value) for value in finding.absolute_path)
                errors.append(
                    f"example schema violation in {name}:{line_number}"
                    f"{f' at {location}' if location else ''}: {finding.message}"
                )
        parsed_records[name] = records

    actual_jsonl = {path.name for path in bundle.glob("*.jsonl") if path.is_file()}
    require(
        declared_jsonl == actual_jsonl,
        "illustrative example manifest JSONL inventory differs from the bundle",
        errors,
    )

    supporting_paths: set[str] = set()
    protocols = {
        record.get("protocol_uri"): record
        for record in parsed_records.get("protocol_applications.jsonl", [])
    }
    for entry in manifest.get("supporting_resources", []):
        relative = PurePosixPath(entry.get("path", ""))
        require(
            len(relative.parts) == 1,
            f"unsafe illustrative supporting-resource path: {relative}",
            errors,
        )
        if len(relative.parts) != 1:
            continue
        name = relative.as_posix()
        require(
            name not in supporting_paths,
            f"duplicate supporting-resource path: {name}",
            errors,
        )
        supporting_paths.add(name)
        resource_path = bundle / name
        require(
            resource_path.is_file(),
            f"missing illustrative supporting resource: {name}",
            errors,
        )
        if not resource_path.is_file():
            continue
        expected_digest = entry.get("sha256")
        require(
            expected_digest == sha256(resource_path),
            f"illustrative supporting-resource checksum differs: {name}",
            errors,
        )
        protocol = protocols.get(entry.get("protocol_uri"))
        require(
            protocol is not None
            and protocol.get("resolution_status") == "verified"
            and protocol.get("integrity_verification_method") == "local-sha256"
            and protocol.get("protocol_artifact_path") == name
            and protocol.get("protocol_integrity_sha256") == expected_digest,
            f"illustrative protocol integrity record differs: {name}",
            errors,
        )

    expected_files = {
        "README.md",
        "manifest.json",
        *declared_jsonl,
        *supporting_paths,
    }
    actual_files = {
        path.relative_to(bundle).as_posix()
        for path in bundle.rglob("*")
        if path.is_file()
    }
    require(
        expected_files == actual_files,
        "illustrative example bundle inventory differs from its manifest",
        errors,
    )


def require_dataset_versioning(
    graph: Graph,
    dataset_uri: URIRef,
    version: str,
    doi: str,
    label: str,
    errors: list[str],
) -> None:
    doi_uri = URIRef(f"https://doi.org/{doi}")
    require(
        (DATASET_BASE_URI, RDF.type, DCAT.Dataset) in graph
        and (dataset_uri, RDF.type, DCAT.Dataset) in graph,
        f"{label} omits the stable or versioned DCAT dataset",
        errors,
    )
    require(
        (DATASET_BASE_URI, DCAT_NAMESPACE.hasVersion, dataset_uri) in graph
        and (DATASET_BASE_URI, DCAT_NAMESPACE.hasCurrentVersion, dataset_uri) in graph
        and (dataset_uri, DCAT_NAMESPACE.isVersionOf, DATASET_BASE_URI) in graph
        and (dataset_uri, DCAT_NAMESPACE.version, Literal(version)) in graph,
        f"{label} has an inconsistent DCAT 3 version chain",
        errors,
    )
    require(
        not list(graph.subjects(RDF.type, DCAT_NAMESPACE.DatasetSeries)),
        f"{label} introduces an unsupported dcat:DatasetSeries identity",
        errors,
    )
    require(
        (doi_uri, RDF.type, DCAT.Dataset) not in graph
        and (doi_uri, RDF.type, VOID.Dataset) not in graph,
        f"{label} incorrectly types the DOI landing page as a second dataset",
        errors,
    )


def audit_exchange_metadata(
    root: Path,
    canonical: dict[str, Any],
    quality_report: dict[str, Any],
    version: str,
    errors: list[str],
) -> None:
    dataset_uri = URIRef(canonical["dataset_uri"])
    for relative, label in (
        ("dist/rdf/omaro.ttl", "full RDF export"),
        ("dist/metadata/dcat-void.ttl", "embedded DCAT/VoID metadata"),
    ):
        path = root / relative
        require(path.is_file(), f"missing {label}: {relative}", errors)
        if path.is_file():
            graph = Graph().parse(path, format="turtle")
            require_dataset_versioning(
                graph,
                dataset_uri,
                version,
                canonical["doi"],
                label,
                errors,
            )

    dqv_path = root / "dist/metadata/dqv.ttl"
    require(dqv_path.is_file(), "missing DQV quality metadata", errors)
    if dqv_path.is_file():
        dqv_graph = Graph().parse(dqv_path, format="turtle")
        software_agent = OMARO_NAMESPACE["release-builder"]
        generated_at = Literal(canonical["generated_at"], datatype=XSD.dateTime)
        require(
            (software_agent, RDF.type, PROV.SoftwareAgent) in dqv_graph,
            "DQV metadata omits release-builder software attribution",
            errors,
        )

        resolved = int(quality_report["instruments"])
        unresolved = int(quality_report["unresolved_stubs"])
        denominator = resolved + unresolved
        expected_rate = (Decimal(resolved) / Decimal(denominator)).quantize(
            Decimal("0.000000000001")
        )
        expected_measures: dict[str, tuple[URIRef, str]] = {
            "resolved-source-target-count": (XSD.integer, str(resolved)),
            "unresolved-source-target-count": (XSD.integer, str(unresolved)),
            "source-target-resolution-denominator": (
                XSD.integer,
                str(denominator),
            ),
            "source-target-resolution-rate": (
                XSD.decimal,
                format(expected_rate, "f"),
            ),
            "automated-finding-count-total": (
                XSD.integer,
                str(quality_report["quality_findings"]),
            ),
            "review-event-count": (
                XSD.integer,
                str(quality_report["review_events"]),
            ),
            "canonical-validation-passed": (XSD.boolean, "true"),
        }
        for rule_code, count in quality_report["quality_findings_by_rule"].items():
            expected_measures[f"automated-finding-count-{rule_code}"] = (
                XSD.integer,
                str(count),
            )

        actual_measurements = set(dqv_graph.subjects(RDF.type, DQV.QualityMeasurement))
        require(
            len(actual_measurements) == len(expected_measures),
            "DQV measurement inventory differs from the quality report",
            errors,
        )
        for code, (expected_datatype, expected_lexical) in expected_measures.items():
            metric_uri = OMARO_NAMESPACE[f"quality-metric-{code}"]
            expected_measurement_uri = URIRef(
                f"{dataset_uri}#quality-measurement-{code}"
            )
            measurements = list(dqv_graph.subjects(DQV.isMeasurementOf, metric_uri))
            require(
                measurements == [expected_measurement_uri],
                f"DQV measure is missing or duplicated: {code}",
                errors,
            )
            if measurements != [expected_measurement_uri]:
                continue
            measurement_uri = measurements[0]
            values = list(dqv_graph.objects(measurement_uri, DQV.value))
            require(
                len(values) == 1
                and isinstance(values[0], Literal)
                and values[0].datatype == expected_datatype
                and str(values[0]) == expected_lexical,
                f"DQV measure has an incorrect typed value: {code}",
                errors,
            )
            require(
                (measurement_uri, DQV.computedOn, dataset_uri) in dqv_graph
                and (measurement_uri, PROV.wasAttributedTo, software_agent) in dqv_graph
                and (measurement_uri, PROV.generatedAtTime, generated_at) in dqv_graph,
                f"DQV measure lacks dataset or generation provenance: {code}",
                errors,
            )
            require(
                (metric_uri, RDF.type, DQV.Metric) in dqv_graph
                and (metric_uri, DQV.expectedDataType, expected_datatype) in dqv_graph
                and len(list(dqv_graph.objects(metric_uri, SKOS.definition))) == 1,
                f"DQV metric is not fully defined: {code}",
                errors,
            )
            dimensions = list(dqv_graph.objects(metric_uri, DQV.inDimension))
            require(
                len(dimensions) == 1
                and (dimensions[0], RDF.type, DQV.Dimension) in dqv_graph,
                f"DQV metric lacks one defined dimension: {code}",
                errors,
            )

        require(
            sum(quality_report["quality_findings_by_rule"].values())
            == quality_report["quality_findings"],
            "quality-report per-rule findings do not sum to the total",
            errors,
        )
        canonical_metric = OMARO_NAMESPACE["quality-metric-canonical-validation-passed"]
        canonical_definition = " ".join(
            str(value) for value in dqv_graph.objects(canonical_metric, SKOS.definition)
        ).lower()
        require(
            "does not establish" in canonical_definition
            and "organological" in canonical_definition
            and "cultural validity" in canonical_definition,
            "canonical validation metric lacks its domain/cultural validity guard",
            errors,
        )
        dqv_nodes = {str(node) for node in dqv_graph.all_nodes()}
        finding_path = root / "dist/jsonl/quality_findings.jsonl"
        if finding_path.is_file():
            finding_uris = {
                json.loads(line)["uri"]
                for line in finding_path.read_text(encoding="utf-8").splitlines()
                if line
            }
            require(
                dqv_nodes.isdisjoint(finding_uris),
                "DQV metadata retypes or references OMARO quality findings",
                errors,
            )

    archive = root / f"omaro-v{version}.zip"
    sidecar = root / f"omaro-v{version}.dcat.ttl"
    require(sidecar.is_file(), f"missing external DCAT sidecar: {sidecar.name}", errors)
    if archive.is_file() and sidecar.is_file():
        graph = Graph().parse(sidecar, format="turtle")
        require_dataset_versioning(
            graph,
            dataset_uri,
            version,
            canonical["doi"],
            "external DCAT sidecar",
            errors,
        )
        distribution_uri = URIRef(f"{dataset_uri}#distribution-release-zip")
        archive_uri = URIRef(
            "https://github.com/modavis-project/omaro/releases/download/"
            f"v{version}/omaro-v{version}.zip"
        )
        require(
            (dataset_uri, DCAT.distribution, distribution_uri) in graph
            and (distribution_uri, RDF.type, DCAT.Distribution) in graph
            and (distribution_uri, DCAT.downloadURL, archive_uri) in graph,
            "external DCAT distribution identity or download URL differs",
            errors,
        )
        require(
            (distribution_uri, DCAT_NAMESPACE.packageFormat, IANA_ZIP_MEDIA_TYPE)
            in graph
            and (
                distribution_uri,
                DCAT.byteSize,
                Literal(archive.stat().st_size, datatype=XSD.nonNegativeInteger),
            )
            in graph
            and (distribution_uri, DCTERMS.license, CC0_LICENSE) in graph,
            "external DCAT distribution package metadata differs",
            errors,
        )
        checksum_nodes = list(graph.objects(distribution_uri, SPDX.checksum))
        require(
            len(checksum_nodes) == 1,
            "external DCAT distribution does not have exactly one checksum",
            errors,
        )
        if len(checksum_nodes) == 1:
            checksum = checksum_nodes[0]
            checksum_values = list(graph.objects(checksum, SPDX.checksumValue))
            require(
                (checksum, RDF.type, SPDX.Checksum) in graph
                and (checksum, SPDX.algorithm, SPDX.checksumAlgorithm_sha256) in graph
                and len(checksum_values) == 1
                and isinstance(checksum_values[0], Literal)
                and checksum_values[0].datatype == XSD.hexBinary
                and str(checksum_values[0]) == sha256(archive),
                "external DCAT distribution SHA-256 metadata differs",
                errors,
            )
        records = list(graph.subjects(RDF.type, DCAT.CatalogRecord))
        require(
            len(records) == 1
            and (records[0], FOAF.primaryTopic, dataset_uri) in graph
            and (records[0], DCTERMS.conformsTo, DCAT_3_SPECIFICATION) in graph,
            "external DCAT catalog record is missing DCAT 3 conformance",
            errors,
        )
        require(
            not any(sidecar.name in str(node) for node in graph.all_nodes()),
            "external DCAT sidecar makes a circular claim about itself",
            errors,
        )


def audit_ro_crate(
    handle: zipfile.ZipFile,
    prefix: str,
    canonical: dict[str, Any],
    publication_date: str,
    errors: list[str],
) -> None:
    member_name = prefix + "ro-crate-metadata.json"
    names = set(handle.namelist())
    if member_name not in names:
        errors.append("release archive omits ro-crate-metadata.json")
        return
    try:
        document = json.loads(handle.read(member_name))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        errors.append(f"RO-Crate metadata is not valid UTF-8 JSON: {error}")
        return

    require(
        document.get("@context") == "https://w3id.org/ro/crate/1.3/context",
        "RO-Crate does not use the official 1.3 context",
        errors,
    )
    graph = document.get("@graph")
    require(isinstance(graph, list), "RO-Crate @graph is not an array", errors)
    if not isinstance(graph, list):
        return
    entities = [row for row in graph if isinstance(row, dict)]
    require(
        len(entities) == len(graph),
        "RO-Crate graph contains a non-object entity",
        errors,
    )
    identifiers = [row.get("@id") for row in entities]
    require(
        all(isinstance(identifier, str) and identifier for identifier in identifiers),
        "RO-Crate entity omits a non-empty @id",
        errors,
    )
    if not all(
        isinstance(identifier, str) and identifier for identifier in identifiers
    ):
        return
    require(
        len(identifiers) == len(set(identifiers)),
        "RO-Crate entity identifiers are not unique",
        errors,
    )
    by_id = {row["@id"]: row for row in entities}
    descriptor = by_id.get("ro-crate-metadata.json", {})
    root_entity = by_id.get("./", {})
    require(
        descriptor.get("@type") == "CreativeWork"
        and descriptor.get("about") == {"@id": "./"}
        and descriptor.get("conformsTo") == {"@id": "https://w3id.org/ro/crate/1.3"},
        "RO-Crate descriptor identity or profile differs",
        errors,
    )
    dataset_uri = canonical["dataset_uri"]
    doi_uri = f"https://doi.org/{canonical['doi']}"
    root_types = root_entity.get("@type", [])
    if isinstance(root_types, str):
        root_types = [root_types]
    require("Dataset" in root_types, "RO-Crate root is not a Dataset", errors)
    root_identifiers = root_entity.get("identifier", [])
    if isinstance(root_identifiers, str):
        root_identifiers = [root_identifiers]
    require(
        {dataset_uri, doi_uri}.issubset(set(root_identifiers))
        and root_entity.get("url") == dataset_uri
        and root_entity.get("sameAs") == doi_uri
        and root_entity.get("version") == canonical["dataset_version"]
        and root_entity.get("datePublished") == publication_date
        and root_entity.get("license") == {"@id": "https://spdx.org/licenses/CC0-1.0"},
        "RO-Crate root release identity differs from canonical metadata",
        errors,
    )
    require(
        root_entity.get("codeRepository") == {"@id": canonical["repository_uri"]}
        and {
            row.get("@id")
            for row in root_entity.get("isBasedOn", [])
            if isinstance(row, dict)
        }
        == set(canonical["sources"]),
        "RO-Crate repository or source identity differs",
        errors,
    )
    require(
        bool(root_entity.get("creator"))
        and "cultural authorization"
        in str(root_entity.get("conditionsOfAccess", "")).lower(),
        "RO-Crate omits creator or cultural-authorization boundary",
        errors,
    )

    local_ids = {
        identifier
        for identifier in by_id
        if identifier not in {"./", "ro-crate-metadata.json"}
        and not identifier.startswith(("#", "http://", "https://"))
    }
    for identifier in sorted(local_ids):
        entity = by_id[identifier]
        if identifier.endswith("/"):
            require(
                entity.get("@type") == "Dataset"
                and any(name.startswith(prefix + identifier) for name in names),
                f"RO-Crate directory entity is absent from the archive: {identifier}",
                errors,
            )
            continue
        archive_name = prefix + identifier
        require(
            entity.get("@type") == "File" and archive_name in names,
            f"RO-Crate file entity is absent from the archive: {identifier}",
            errors,
        )
        if archive_name in names:
            require(
                entity.get("contentSize") == str(handle.getinfo(archive_name).file_size)
                and isinstance(entity.get("encodingFormat"), str),
                f"RO-Crate file metadata differs: {identifier}",
                errors,
            )

    reached: set[str] = set()
    pending = ["./"]
    while pending:
        parent = pending.pop()
        for reference in by_id.get(parent, {}).get("hasPart", []):
            child = reference.get("@id") if isinstance(reference, dict) else None
            require(
                isinstance(child, str) and child in by_id,
                f"RO-Crate hasPart reference is unresolved: {child}",
                errors,
            )
            if isinstance(child, str) and child in by_id and child not in reached:
                reached.add(child)
                pending.append(child)
    require(
        reached == local_ids,
        "RO-Crate local entities are not exactly reachable from the root hasPart graph",
        errors,
    )


def audit(root: Path) -> list[str]:
    errors: list[str] = []
    audit_public_repository(root, errors)
    audit_public_history(root, errors)
    audit_illustrative_examples(root, errors)
    for name in sorted(PUBLIC_ARCHIVE_ROOT_FILES):
        path = root / name
        require(path.is_file(), f"missing public release document: {name}", errors)
        if path.is_file():
            data = path.read_bytes()
            for marker in STALE_INTERFACE_MARKERS:
                require(
                    marker not in data,
                    f"stale interface marker {marker.decode()} in {name}",
                    errors,
                )
    for name in sorted(VERSIONED_INTERFACE_FILES):
        path = root / name
        require(path.is_file(), f"missing versioned interface file: {name}", errors)
        if path.is_file():
            data = path.read_bytes()
            for marker in STALE_INTERFACE_MARKERS:
                require(
                    marker not in data,
                    f"stale interface marker {marker.decode()} in {name}",
                    errors,
                )
    w3id_path = root / "w3id/modavis/omaro/.htaccess"
    if w3id_path.is_file():
        w3id_rules = w3id_path.read_text(encoding="utf-8")
        for target in (
            f"ontology/{ONTOLOGY_VERSION}/index.html",
            f"ontology/{ONTOLOGY_VERSION}/omaro.ttl",
            f"ontology/{ONTOLOGY_VERSION}/omaro.jsonld",
            f"ontology/{ONTOLOGY_VERSION}/omaro.rdf",
            f"dataset/{DATASET_VERSION}/index.html",
            f"dataset/{DATASET_VERSION}/omaro.ttl",
            f"dataset/{DATASET_VERSION}/omaro.jsonld",
            f"dataset/{DATASET_VERSION}/omaro.rdf",
            "schema/$1",
        ):
            require(
                target in w3id_rules,
                f"W3ID rules omit current publication target: {target}",
                errors,
            )
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    reuse = tomllib.loads((root / "REUSE.toml").read_text(encoding="utf-8"))
    version = project["project"]["version"]
    version_file = (root / "VERSION").read_text(encoding="utf-8").strip()
    canonical = load_json(root / "data/canonical/metadata.json")
    zenodo = load_json(root / "zenodo/metadata.json")
    github_zenodo = load_json(root / ".zenodo.json")
    codemeta = load_json(root / "codemeta.json")
    manifest = load_json(root / "dist/manifest.json")
    datacite = load_json(root / "dist/metadata/datacite.json")["data"]["attributes"]
    quality_report = load_json(root / "dist/quality-report.json")
    cff = (root / "CITATION.cff").read_text(encoding="utf-8")

    audit_exchange_metadata(
        root,
        canonical,
        quality_report,
        version,
        errors,
    )

    doi = canonical["doi"]
    publication_date = zenodo["api_payload"]["metadata"]["publication_date"]
    title = canonical["title"]
    expected_identity = {
        "name": "OMARO",
        "ontology_title": (
            "Ontology for Multiperspectivity, Assertions, and Review in Organology"
        ),
        "preferred_namespace_prefix": "omaro",
        "namespace_uri": "https://w3id.org/modavis/omaro#",
        "ontology_uri": "https://w3id.org/modavis/omaro/ontology",
        "ontology_version_iri": (
            f"https://w3id.org/modavis/omaro/ontology/{ONTOLOGY_VERSION}"
        ),
        "dataset_uri": f"https://w3id.org/modavis/omaro/dataset/{DATASET_VERSION}",
        "repository_uri": "https://github.com/modavis-project/omaro",
    }
    for key, expected in expected_identity.items():
        require(
            canonical.get(key) == expected,
            f"canonical OMARO identity differs for {key}",
            errors,
        )
    require(project["project"]["name"] == "omaro", "package name is not omaro", errors)
    require(
        version == DATASET_VERSION,
        f"dataset/tooling version is {version}, expected {DATASET_VERSION}",
        errors,
    )
    require(
        project["project"]["scripts"].get("omaro") == "omaro.cli:main",
        "OMARO command-line entry point is inconsistent",
        errors,
    )
    require(
        canonical["dataset_version"] == version,
        "canonical version differs from package version",
        errors,
    )
    require(
        canonical["schema_version"] == SCHEMA_VERSION,
        f"canonical schema version is not {SCHEMA_VERSION}",
        errors,
    )
    canonical_checksums = canonical.get("canonical_checksums", {})
    canonical_counts = canonical.get("counts", {})
    for filename, expected_checksum in canonical_checksums.items():
        path = root / "data/canonical" / filename
        require(
            path.is_file(), f"missing checksummed canonical file: {filename}", errors
        )
        if path.is_file():
            require(
                sha256(path) == expected_checksum,
                f"canonical checksum differs: {filename}",
                errors,
            )
    for filename, count_key in RELATED_WORK_REGISTRIES.items():
        require(
            (root / "data/canonical" / filename).is_file(),
            f"missing canonical related-work registry: {filename}",
            errors,
        )
        require(
            filename in canonical_checksums,
            f"canonical checksum inventory omits {filename}",
            errors,
        )
        require(
            count_key in canonical_counts,
            f"canonical count inventory omits {count_key}",
            errors,
        )
    for filename, required_fields in SCHEMA_REQUIRED_FIELDS.items():
        schema_path = root / "schema" / filename
        require(schema_path.is_file(), f"missing contract schema: {filename}", errors)
        if not schema_path.is_file():
            continue
        schema = load_json(schema_path)
        declared_required = set(schema.get("required", []))
        declared_properties = set(schema.get("properties", {}))
        require(
            required_fields.issubset(declared_required),
            f"schema required-field contract differs: {filename}",
            errors,
        )
        require(
            required_fields.issubset(declared_properties),
            f"schema property inventory differs: {filename}",
            errors,
        )
    classification_schema_path = root / "schema/classification_assertion.schema.json"
    if classification_schema_path.is_file():
        classification_method_schema = (
            load_json(classification_schema_path)
            .get("properties", {})
            .get("classification_method_uri", {})
        )
        require(
            classification_method_schema.get("type") == "string"
            and classification_method_schema.get("format") == "uri",
            "classification_method_uri is not constrained as an absolute URI",
            errors,
        )
    protocol_schema_path = root / "schema/protocol_application.schema.json"
    if protocol_schema_path.is_file():
        protocol_digest_schema = (
            load_json(protocol_schema_path)
            .get("properties", {})
            .get("protocol_integrity_sha256", {})
        )
        require(
            protocol_digest_schema.get("pattern") == "^[0-9a-f]{64}$",
            "protocol_integrity_sha256 is not constrained as a lowercase SHA-256",
            errors,
        )
    require(version_file == version, "VERSION differs from package version", errors)
    require(
        reuse.get("SPDX-PackageName") == "OMARO",
        "REUSE package name is inconsistent",
        errors,
    )
    require(
        (root / "LICENSES/CC0-1.0.txt").read_bytes() == (root / "LICENSE").read_bytes(),
        "REUSE CC0 license text differs from LICENSE",
        errors,
    )
    require(
        codemeta["version"] == version,
        "CodeMeta version differs from package version",
        errors,
    )
    require(
        manifest["dataset_version"] == version,
        "manifest version differs from package version",
        errors,
    )
    require(
        manifest["schema_version"] == SCHEMA_VERSION,
        f"manifest schema version is not {SCHEMA_VERSION}",
        errors,
    )
    for count_key in RELATED_WORK_REGISTRIES.values():
        require(
            manifest.get("counts", {}).get(count_key)
            == canonical_counts.get(count_key),
            f"manifest count differs for {count_key}",
            errors,
        )
    require(
        zenodo["api_payload"]["metadata"]["version"] == version,
        "Zenodo version differs from package version",
        errors,
    )
    require(
        github_zenodo["version"] == version,
        ".zenodo.json version differs from package version",
        errors,
    )
    require(
        cff_scalar(cff, "version") == version,
        "CITATION.cff version differs from package version",
        errors,
    )
    require(
        zenodo["record_status"] == "draft",
        "Zenodo metadata is not marked as a draft",
        errors,
    )
    require(
        "doi" not in zenodo["api_payload"]["metadata"],
        "Zenodo API payload must not resubmit its reserved DOI",
        errors,
    )
    require(
        zenodo["reserved_doi"] == doi == manifest["doi"] == datacite["doi"],
        "DOI metadata is inconsistent",
        errors,
    )
    require(
        codemeta["identifier"] == f"https://doi.org/{doi}",
        "CodeMeta DOI is inconsistent",
        errors,
    )
    require(cff_scalar(cff, "doi") == doi, "CITATION.cff DOI is inconsistent", errors)
    require(
        cff_scalar(cff, "date-released") == publication_date,
        "release dates are inconsistent",
        errors,
    )
    require(
        zenodo["api_payload"]["metadata"]["title"] == title,
        "Zenodo title differs from canonical title",
        errors,
    )
    require(
        github_zenodo["title"] == title,
        ".zenodo.json title differs from canonical title",
        errors,
    )
    require(
        codemeta["name"] == title,
        "CodeMeta title differs from canonical title",
        errors,
    )
    require(
        datacite["publicationYear"] == int(publication_date[:4]),
        "DataCite publication year is inconsistent",
        errors,
    )
    require(
        cff_scalar(cff, "url") == canonical["dataset_uri"],
        "CITATION.cff dataset identifier is inconsistent",
        errors,
    )
    require(
        codemeta["url"] == canonical["repository_uri"]
        and canonical["ontology_version_iri"] in codemeta["isRelatedTo"]
        and canonical["dataset_uri"] in codemeta["isRelatedTo"],
        "CodeMeta OMARO identifiers are inconsistent",
        errors,
    )
    zenodo_related = {
        row["identifier"]
        for row in zenodo["api_payload"]["metadata"]["related_identifiers"]
    }
    github_zenodo_related = {
        row["identifier"] for row in github_zenodo["related_identifiers"]
    }
    for expected in (
        canonical["ontology_version_iri"],
        canonical["dataset_uri"],
        canonical["repository_uri"],
    ):
        require(
            expected in zenodo_related and expected in github_zenodo_related,
            f"Zenodo related identifiers omit {expected}",
            errors,
        )

    source_schema_dir = root / "schema"
    dist_schema_dir = root / "dist/schema"
    require(dist_schema_dir.is_dir(), "dist/schema is missing", errors)
    if source_schema_dir.is_dir() and dist_schema_dir.is_dir():
        source_schema_files = {
            path.relative_to(source_schema_dir).as_posix(): path
            for path in source_schema_dir.rglob("*")
            if path.is_file()
        }
        dist_schema_files = {
            path.relative_to(dist_schema_dir).as_posix(): path
            for path in dist_schema_dir.rglob("*")
            if path.is_file()
        }
        require(
            set(source_schema_files) == set(dist_schema_files),
            "dist/schema file inventory differs from source schema/",
            errors,
        )
        for relative in sorted(set(source_schema_files) & set(dist_schema_files)):
            require(
                source_schema_files[relative].read_bytes()
                == dist_schema_files[relative].read_bytes(),
                f"distributed schema differs from source: {relative}",
                errors,
            )

    rdf_dir = root / "dist/rdf"
    ontology_root = root / "dist/ontology"
    ontology_version_dir = ontology_root / ONTOLOGY_VERSION
    ontology_version_directories = {
        path.name for path in ontology_root.iterdir() if path.is_dir()
    }
    require(
        ontology_version_directories == {ONTOLOGY_VERSION, "2.2.0"},
        "dist/ontology contains a stale or missing version directory",
        errors,
    )
    historical_source = root / "site/compatibility/ontology/2.2.0"
    historical_output = ontology_root / "2.2.0"
    for name in (
        "index.html",
        "manifest.json",
        "omaro.ttl",
        "omaro.rdf",
        "omaro.jsonld",
    ):
        original = historical_source / name
        distributed = historical_output / name
        require(
            original.is_file()
            and distributed.is_file()
            and original.read_bytes() == distributed.read_bytes(),
            f"historical ontology differs from preserved source: {name}",
            errors,
        )
    for name in ("omaro.ttl", "omaro.rdf", "omaro.jsonld"):
        require(
            (ontology_version_dir / name).is_file(),
            f"missing versioned ontology representation: {name}",
            errors,
        )
    if all(
        (ontology_version_dir / name).is_file()
        for name in ("omaro.ttl", "omaro.rdf", "omaro.jsonld")
    ):
        ontology_graphs = [
            Graph().parse(ontology_version_dir / "omaro.ttl", format="turtle"),
            Graph().parse(ontology_version_dir / "omaro.rdf"),
            Graph().parse(ontology_version_dir / "omaro.jsonld"),
        ]
        require(
            all(
                to_isomorphic(graph) == to_isomorphic(ontology_graphs[0])
                for graph in ontology_graphs[1:]
            ),
            "versioned ontology representations are not RDF-isomorphic",
            errors,
        )
        ontology_graph = ontology_graphs[0]
        for activity in ("ClassificationAssignment", "ReviewEvent"):
            for entity in (
                "ClassificationAssertion",
                "ConceptRelationAssertion",
                "LabelAssertion",
                "NoteAssertion",
                "ReviewDecision",
            ):
                require(
                    (
                        OMARO_NAMESPACE[activity],
                        OWL.disjointWith,
                        OMARO_NAMESPACE[entity],
                    )
                    in ontology_graph,
                    f"compact ontology lacks activity/entity disjointness: {activity}/{entity}",
                    errors,
                )
        ontology_uri = URIRef(canonical["ontology_uri"])
        version_uri = URIRef(canonical["ontology_version_iri"])
        require(
            (ontology_uri, RDF.type, OWL.Ontology) in ontology_graph
            and (ontology_uri, OWL.versionIRI, version_uri) in ontology_graph,
            "versioned ontology header is inconsistent",
            errors,
        )
        namespace = canonical["namespace_uri"]
        owned_classes = {
            term
            for term in ontology_graph.subjects(RDF.type, OWL.Class)
            if str(term).startswith(namespace)
        }
        owned_object_properties = {
            term
            for term in ontology_graph.subjects(RDF.type, OWL.ObjectProperty)
            if str(term).startswith(namespace)
        }
        owned_datatype_properties = {
            term
            for term in ontology_graph.subjects(RDF.type, OWL.DatatypeProperty)
            if str(term).startswith(namespace)
        }
        owned_properties = owned_object_properties | owned_datatype_properties
        require(
            owned_object_properties.isdisjoint(owned_datatype_properties),
            "ontology types an owned property as both object and datatype",
            errors,
        )
        require(
            owned_classes.isdisjoint(owned_properties),
            "ontology uses the same owned term as both class and property",
            errors,
        )
        require(
            len(owned_classes) == ONTOLOGY_CLASS_COUNT,
            "ontology class inventory differs",
            errors,
        )
        require(
            len(owned_properties) == ONTOLOGY_PROPERTY_COUNT,
            "ontology property inventory differs",
            errors,
        )
        mapping_purpose_property = URIRef(f"{namespace}mappingPurpose")
        mapping_purpose_scheme = URIRef(f"{namespace}vocabulary-mapping-purpose")
        mapping_purpose_terms = {
            URIRef(f"{namespace}mapping-purpose-{code}")
            for code in (
                "query-expansion",
                "display-navigation",
                "data-transformation",
                "scholarly-comparison",
            )
        }
        require(
            (mapping_purpose_property, RDFS.range, SKOS.Concept) in ontology_graph,
            "mappingPurpose does not have the required SKOS Concept range",
            errors,
        )
        require(
            (mapping_purpose_scheme, RDF.type, SKOS.ConceptScheme) in ontology_graph
            and all(
                (term, RDF.type, SKOS.Concept) in ontology_graph
                and (term, SKOS.inScheme, mapping_purpose_scheme) in ontology_graph
                for term in mapping_purpose_terms
            ),
            "ontology omits its controlled mapping-purpose concepts",
            errors,
        )
        for term in owned_classes | owned_properties:
            require(
                len(list(ontology_graph.objects(term, RDFS.label))) == 1
                and len(list(ontology_graph.objects(term, RDFS.comment))) == 1
                and (term, RDFS.isDefinedBy, ontology_uri) in ontology_graph,
                f"ontology term is not individually documented: {term}",
                errors,
            )
        for term in owned_properties:
            require(
                (term, RDF.type, RDF.Property) in ontology_graph,
                f"OWL property lacks an explicit rdf:Property declaration: {term}",
                errors,
            )
            require(
                len(list(ontology_graph.objects(term, RDFS.range))) <= 1,
                f"ontology property has conflicting ranges: {term}",
                errors,
            )
        for term in owned_datatype_properties:
            require(
                len(list(ontology_graph.objects(term, RDFS.range))) == 1,
                f"datatype property lacks one explicit range: {term}",
                errors,
            )
        require(
            not list(
                ontology_graph.subjects(
                    RDF.type, URIRef("http://www.w3.org/ns/dcat#Dataset")
                )
            ),
            "compact ontology contains dataset instances",
            errors,
        )
        require(
            not any(
                isinstance(term, URIRef) and str(term).startswith(ONTOLEX_NAMESPACE)
                for triple in ontology_graph
                for term in triple
            ),
            "compact ontology contains an unsupported OntoLex assertion",
            errors,
        )
        require(
            manifest.get("rdf", {}).get("ontology_triples") == len(ontology_graph),
            "manifest compact-ontology triple count differs",
            errors,
        )
    full_rdf_serializations = {
        "omaro.ttl": "turtle",
        "omaro.rdf": "xml",
        "omaro.jsonld": "json-ld",
    }
    full_rdf_fingerprints: dict[str, tuple[int, int]] = {}
    for filename, rdf_format in full_rdf_serializations.items():
        path = rdf_dir / filename
        require(
            path.is_file(), f"missing public RDF representation: {filename}", errors
        )
        if path.is_file():
            try:
                full_rdf_fingerprints[filename] = rdf_isomorphism_fingerprint(
                    path, rdf_format
                )
            except Exception as exc:  # pragma: no cover - parser diagnostics vary
                errors.append(
                    f"cannot parse public RDF representation {filename}: {exc}"
                )
    if len(full_rdf_fingerprints) == len(full_rdf_serializations):
        require(
            len(set(full_rdf_fingerprints.values())) == 1,
            "public RDF representations are not RDF-isomorphic",
            errors,
        )
        rdf_triples = next(iter(full_rdf_fingerprints.values()))[0]
        require(
            manifest.get("rdf", {}).get("triples") == rdf_triples,
            "manifest public-RDF triple count differs",
            errors,
        )
    dataset_root = root / "dist/dataset"
    dataset_version_directories = {
        path.name for path in dataset_root.iterdir() if path.is_dir()
    }
    require(
        dataset_version_directories == {DATASET_VERSION},
        "dist/dataset contains a stale or missing version directory",
        errors,
    )
    require(
        (dataset_root / DATASET_VERSION / "index.html").is_file(),
        "missing versioned dataset landing page",
        errors,
    )
    sqlite_path = root / "dist/sqlite/omaro.sqlite"
    require(sqlite_path.is_file(), "missing SQLite distribution", errors)
    if sqlite_path.is_file():
        try:
            with sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True) as connection:
                user_version = connection.execute("PRAGMA user_version").fetchone()[0]
                objects = {
                    name: kind
                    for name, kind in connection.execute(
                        "SELECT name, type FROM sqlite_master "
                        "WHERE type IN ('table', 'view')"
                    )
                }
                column_names = {
                    relation: {
                        row[1]
                        for row in connection.execute(
                            f'PRAGMA table_info("{relation}")'
                        )
                    }
                    for relation in SQLITE_REQUIRED_COLUMNS
                }
            require(
                user_version == SQLITE_USER_VERSION,
                f"SQLite user_version is {user_version}, expected {SQLITE_USER_VERSION}",
                errors,
            )
            for table in SQLITE_REQUIRED_TABLES:
                require(
                    objects.get(table) == "table",
                    f"SQLite distribution omits required table: {table}",
                    errors,
                )
            for view in SQLITE_REQUIRED_VIEWS:
                require(
                    objects.get(view) == "view",
                    f"SQLite distribution omits required view: {view}",
                    errors,
                )
            require(
                "classification_instruments" not in objects,
                "SQLite distribution retains superseded classification_instruments",
                errors,
            )
            for relation, required_columns in SQLITE_REQUIRED_COLUMNS.items():
                missing_columns = required_columns - column_names[relation]
                require(
                    not missing_columns,
                    f"SQLite {relation} omits columns: "
                    + ", ".join(sorted(missing_columns)),
                    errors,
                )
        except sqlite3.DatabaseError as error:
            errors.append(f"SQLite distribution cannot be audited: {error}")
    turtle = (rdf_dir / "omaro.ttl").read_text(encoding="utf-8")
    require(
        ONTOLEX_NAMESPACE not in turtle,
        "OMARO RDF contains an unsupported OntoLex assertion",
        errors,
    )
    for expected in (
        canonical["namespace_uri"],
        canonical["ontology_uri"],
        canonical["ontology_version_iri"],
        canonical["dataset_uri"],
    ):
        require(expected in turtle, f"OMARO RDF omits identity: {expected}", errors)

    csv_dir = root / "dist/csv"
    for filename, required_columns in CSV_REQUIRED_COLUMNS.items():
        path = csv_dir / filename
        require(path.is_file(), f"missing generated CSV contract: {filename}", errors)
        if not path.is_file():
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle), [])
        missing_columns = required_columns - set(header)
        require(
            not missing_columns,
            f"generated CSV {filename} omits columns: "
            + ", ".join(sorted(missing_columns)),
            errors,
        )

    manifest_file_rows = manifest["files"]
    expected_files = {row["path"]: row for row in manifest_file_rows}
    require(
        len(manifest_file_rows) == len(expected_files),
        "manifest contains duplicate file paths",
        errors,
    )
    for relative in expected_files:
        manifest_path = PurePosixPath(relative)
        require(
            not manifest_path.is_absolute() and ".." not in manifest_path.parts,
            f"manifest contains an unsafe file path: {relative}",
            errors,
        )
    actual_files = {
        path.relative_to(root / "dist").as_posix(): path
        for path in (root / "dist").rglob("*")
        if path.is_file() and path != root / "dist/manifest.json"
    }
    require(
        set(expected_files) == set(actual_files),
        "manifest file inventory differs from dist/",
        errors,
    )
    for relative, row in expected_files.items():
        path = actual_files.get(relative)
        if path is None:
            continue
        require(
            path.stat().st_size == row["bytes"],
            f"manifest byte count differs: {relative}",
            errors,
        )
        require(
            sha256(path) == row["sha256"],
            f"manifest checksum differs: {relative}",
            errors,
        )

    archive = root / f"omaro-v{version}.zip"
    dcat_sidecar = root / f"omaro-v{version}.dcat.ttl"
    sums_path = root / "SHA256SUMS"
    require(archive.is_file(), f"missing release archive: {archive.name}", errors)
    require(
        dcat_sidecar.is_file(),
        f"missing release metadata sidecar: {dcat_sidecar.name}",
        errors,
    )
    require(sums_path.is_file(), "missing SHA256SUMS", errors)
    if archive.is_file() and dcat_sidecar.is_file() and sums_path.is_file():
        checksum_artifacts = sorted((archive, dcat_sidecar), key=lambda path: path.name)
        expected_sum_lines = "".join(
            f"{sha256(path)}  {path.name}\n" for path in checksum_artifacts
        )
        require(
            sums_path.read_text(encoding="utf-8") == expected_sum_lines,
            "SHA256SUMS does not exactly identify the release archive and sidecar",
            errors,
        )

    if archive.is_file():
        prefix = f"omaro-v{version}/"
        example_files = {
            path.relative_to(root).as_posix(): path
            for path in (root / PUBLIC_ARCHIVE_EXAMPLES_DIR).rglob("*")
            if path.is_file()
        }
        required = {
            prefix + "README.md",
            prefix + "AUTHORS.md",
            prefix + "NOTICE",
            prefix + "VERSION",
            prefix + "codemeta.json",
            prefix + "RELEASE_NOTES.md",
            prefix + "CITATION.cff",
            prefix + "CULTURAL_GOVERNANCE.md",
            prefix + "INTEROPERABILITY_PROFILES.md",
            prefix + "MODAVIS_VAO_INTEROPERABILITY.md",
            prefix + "NAMING_AND_IDENTITY.md",
            prefix + "ONTOLOGY_REFERENCE.md",
            prefix + "ORGANOLOGICAL_FOUNDATIONS.md",
            prefix + "ORGANOLOGICAL_MODEL.md",
            prefix + "RELATED_WORK.md",
            prefix + "W3ID_REGISTRATION.md",
            prefix + "dist/manifest.json",
            prefix + "dist/quality-report.json",
            prefix + "dist/okf/index.md",
            prefix + "dist/jsonl/rag-concepts.jsonl",
            prefix + "dist/metadata/dqv.ttl",
            prefix + "dist/metadata/vao-classification-example.json",
            prefix + f"dist/ontology/{ONTOLOGY_VERSION}/index.html",
            prefix + f"dist/ontology/{ONTOLOGY_VERSION}/omaro.ttl",
            prefix + f"dist/dataset/{DATASET_VERSION}/index.html",
            prefix + "examples/organological-assessment/README.md",
            prefix + "examples/organological-assessment/manifest.json",
            prefix + "examples/multidimensional-analysis/README.md",
            prefix + "examples/multidimensional-analysis/scalogram.json",
            prefix + "ro-crate-metadata.json",
        }
        with zipfile.ZipFile(archive) as handle:
            bad_member = handle.testzip()
            member_info = handle.infolist()
            names = [info.filename for info in member_info]
            require(
                len(names) == len(set(names)),
                "release archive contains duplicate member names",
                errors,
            )
            for info in member_info:
                file_type = (info.external_attr >> 16) & 0o170000
                require(
                    not info.is_dir() and file_type in {0, 0o100000},
                    f"release archive contains a non-regular member: {info.filename}",
                    errors,
                )
                require(
                    not (info.flag_bits & 0x1),
                    f"release archive contains an encrypted member: {info.filename}",
                    errors,
                )
            expected_names = {
                *(prefix + name for name in PUBLIC_ARCHIVE_ROOT_FILES),
                *(prefix + name for name in PUBLIC_ARCHIVE_GENERATED_ROOT_FILES),
                *(prefix + name for name in example_files),
                *(
                    prefix + "dist/" + path.relative_to(root / "dist").as_posix()
                    for path in (root / "dist").rglob("*")
                    if path.is_file()
                ),
            }
            require(
                set(names) == expected_names,
                "release archive inventory differs from the approved public surface",
                errors,
            )
            for name in names:
                if not name.startswith(prefix):
                    continue
                relative = name.removeprefix(prefix)
                relative_path = PurePosixPath(relative)
                if relative_path.is_absolute() or ".." in relative_path.parts:
                    continue
                for finding in sensitive_findings(handle.read(name)):
                    errors.append(f"{finding} found in release archive member: {name}")
                if relative in PUBLIC_ARCHIVE_GENERATED_ROOT_FILES:
                    continue
                source = root / relative
                require(
                    source.is_file() and handle.read(name) == source.read_bytes(),
                    f"release archive member differs from source candidate: {name}",
                    errors,
                )
            audit_ro_crate(handle, prefix, canonical, publication_date, errors)
        require(bad_member is None, f"ZIP CRC failed: {bad_member}", errors)
        require(
            required.issubset(names),
            "release archive is missing required files",
            errors,
        )
        for name in names:
            parts = PurePosixPath(name).parts
            require(
                name.startswith(prefix),
                f"archive member has an unexpected prefix: {name}",
                errors,
            )
            require(
                not name.startswith("/") and ".." not in parts,
                f"unsafe archive path: {name}",
                errors,
            )
            relative = name.removeprefix(prefix)
            require(
                relative in PUBLIC_ARCHIVE_ROOT_FILES
                or relative in PUBLIC_ARCHIVE_GENERATED_ROOT_FILES
                or relative in example_files
                or relative.startswith("dist/"),
                f"non-distribution file is not allowed in the public archive: {name}",
                errors,
            )
            relative_path = PurePosixPath(relative)
            require(
                not path_is_private(relative_path),
                f"credential or private working-file path is in the archive: {name}",
                errors,
            )
            if relative.startswith("dist/"):
                require(
                    len(relative_path.parts) > 1
                    and relative_path.parts[1] in PUBLIC_DIST_ROOTS,
                    f"unexpected distribution area is in the archive: {name}",
                    errors,
                )
            require(
                ".egg-info" not in name
                and "__pycache__" not in parts
                and not name.endswith((".pyc", ".pyo", "/.DS_Store")),
                f"generated or platform-specific file in archive: {name}",
                errors,
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    errors = audit(args.repo_root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Release candidate audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
