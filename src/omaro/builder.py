"""Deterministic exports, quality reports, and release packaging."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import platform
import re
import shutil
import sqlite3
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from pyshacl import validate as shacl_validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCAT, DCTERMS, OWL, RDF, RDFS, SKOS, VOID, XSD

from .knowledge_exports import build_okf, build_rag_jsonl
from .model import (
    BROADER,
    ENDORSED_POLICY,
    EXACT_MATCH,
    HS_SCHEME,
    INSTRUMENT_SCHEME,
    OMARO,
    NARROWER,
    DATASET_BASE_URI,
    REPOSITORY_URI,
    Dataset,
    ValidationError,
    canonical_json,
    assertion_uri,
    controlled_value_uri,
)
from .ro_crate import RO_CRATE_METADATA_NAME, write_ro_crate_metadata

REPO_URI = URIRef(REPOSITORY_URI)
LICENSE_URI = URIRef("https://creativecommons.org/publicdomain/zero/1.0/")
CREATOR_URI = URIRef("https://orcid.org/0000-0002-7904-3892")
SCHEMA = Namespace("https://schema.org/")
PROV = Namespace("http://www.w3.org/ns/prov#")
DQV = Namespace("http://www.w3.org/ns/dqv#")
DCAT_NS = Namespace("http://www.w3.org/ns/dcat#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SPDX = Namespace("http://spdx.org/rdf/terms#")
SKOSXL = Namespace("http://www.w3.org/2008/05/skos-xl#")
VANN = Namespace("http://purl.org/vocab/vann/")
SOSA = Namespace("http://www.w3.org/ns/sosa/")
QUDT = Namespace("http://qudt.org/schema/qudt/")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
CRMSCI = Namespace("http://www.cidoc-crm.org/extensions/crmsci/")
TIME = Namespace("http://www.w3.org/2006/time#")
OMARO_NS = Namespace(OMARO)
ZIP_TIMESTAMP = (2026, 9, 11, 0, 0, 0)
RELEASES_BASE = "https://github.com/modavis-project/omaro/releases/download"
DCAT_3_SPECIFICATION = URIRef("https://www.w3.org/TR/vocab-dcat-3/")
IANA_ZIP_MEDIA_TYPE = URIRef(
    "https://www.iana.org/assignments/media-types/application/zip"
)
VAO_RELEASE_IRI = URIRef("https://w3id.org/modavis/vao/0.4.0/")
MODAVIS_RELEASE_IRI = URIRef("https://w3id.org/modavis/ontology/0.1.0")

CONTROLLED_CODES: dict[str, tuple[str, ...]] = {
    "target-type": (
        "instrument-concept",
        "physical-object",
        "instrument-component",
        "functional-module",
        "instrument-aggregate",
        "instrument-configuration",
        "condition-state",
        "sounding-realization",
        "performance-event",
        "ensemble-medium",
    ),
    "stance": (
        "source-asserted",
        "asserted",
        "proposed",
        "endorsed",
        "disputed",
        "rejected",
        "superseded",
    ),
    "classification-method": ("source-mapping-projection",),
    "mapping-purpose": (
        "query-expansion",
        "display-navigation",
        "data-transformation",
        "scholarly-comparison",
    ),
    "evidence-type": (
        "source-record",
        "fieldwork",
        "community-decision",
        "linguistic-analysis",
        "scholarly-publication",
        "rights-protocol",
        "observation",
        "reasoning",
    ),
    "evidence-role": ("supports", "opposes", "qualifies", "documents"),
    "perspective-type": (
        "source",
        "institutional",
        "scholarly",
        "community",
        "curatorial",
        "historical",
        "technical",
    ),
    "scope-mode": (
        "specified",
        "context-independent",
        "source-silent",
        "not-yet-investigated",
        "known-unknown",
        "intentionally-unscoped",
        "not-applicable",
    ),
    "review-outcome": (
        "accepted",
        "correction",
        "disputed",
        "rejected",
        "unverifiable",
        "withdrawn",
    ),
    "review-dimension": (
        "referential",
        "linguistic",
        "community",
        "historical",
        "scholarly",
        "ethical",
        "rights",
    ),
    "review-method": ("human", "community"),
    "reviewer-authority": (
        "community",
        "language",
        "organology",
        "history",
        "rights",
        "technical",
        "ethical",
    ),
    "authority-role": (
        "community-reviewer",
        "cultural-authority",
        "language-authority",
        "rights-authority",
        "delegated-representative",
        "organology-reviewer",
        "historical-reviewer",
        "technical-reviewer",
        "ethical-reviewer",
    ),
    "decision-status": ("active", "withdrawn", "superseded"),
    "assessment-status": (
        "detected",
        "not-detected",
        "indeterminate",
        "not-observed",
        "not-applicable",
    ),
    "result-kind": ("resource", "literal", "quantity", "range"),
    "criterion-type": (
        "primary-vibrator",
        "excitation-mechanism",
        "active-sound-source",
        "resonator",
        "sympathetic-vibrator",
        "sound-propagation",
        "construction",
        "material",
        "bore-profile",
        "pitch-control",
        "tuning-range",
        "controller-interface",
        "timbre-modifier",
        "signal-generator",
        "signal-processor",
        "amplifier",
        "transducer",
        "radiator",
        "physical-configuration",
        "actual-technique",
        "performer-instrument-relation",
        "acoustic-property",
        "manufacture",
        "visual-design",
        "ensemble-or-repertoire-role",
        "historical-provenance",
        "geographic-distribution",
        "social-or-ritual-function",
        "symbolic-meaning",
        "intended-function",
        "actual-use",
        "community-category",
        "other",
    ),
    "combination-operator": (
        "joint",
        "alternative",
        "broader-plus-refinement",
        "source-unspecified",
    ),
    "expression-parse-status": (
        "tokenized-uninterpreted",
        "expert-interpreted",
    ),
    "protocol-enforcement": (
        "advisory",
        "human-decision-required",
        "machine-enforceable",
    ),
    "protocol-resolution": ("verified", "unverified", "unavailable"),
    "protocol-integrity-method": (
        "local-sha256",
        "external-attestation",
        "none",
    ),
    "criterion-status": ("draft", "active", "deprecated", "withdrawn"),
    "protocol-status": ("active", "withdrawn", "superseded", "expired"),
    "use-decision-status": ("active", "superseded", "expired"),
    "use-decision": ("granted", "refused", "withheld", "withdrawn"),
    "use-action": (
        "collect",
        "retain",
        "discover",
        "display",
        "index",
        "export",
        "reuse",
        "derive",
        "train",
        "commercialize",
    ),
    "use-purpose": ("public-reference-release",),
    "use-audience": ("general-public",),
    "legal-basis-status": ("documented", "not-required", "unknown", "blocked"),
    "consent-status": (
        "documented",
        "not-required",
        "unknown",
        "withheld",
        "withdrawn",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def _csv_json_rows(
    rows: list[dict[str, Any]], json_fields: tuple[str, ...]
) -> list[dict[str, Any]]:
    return [
        {
            **row,
            **{f"{field}_json": canonical_json(row[field]) for field in json_fields},
        }
        for row in sorted(rows, key=lambda item: item["uri"])
    ]


def _add_creator(graph: Graph, dataset_uri: URIRef, dataset: Dataset) -> None:
    creator = dataset.metadata["creators"][0]
    graph.add((dataset_uri, DCTERMS.creator, CREATOR_URI))
    graph.add((CREATOR_URI, RDF.type, SCHEMA.Person))
    graph.add((CREATOR_URI, SCHEMA.name, Literal(creator["name"])))
    for affiliation in creator["affiliations"]:
        graph.add((CREATOR_URI, SCHEMA.affiliation, Literal(affiliation)))


def _bind_namespaces(graph: Graph) -> None:
    graph.bind("skos", SKOS)
    graph.bind("skosxl", SKOSXL)
    graph.bind("dcterms", DCTERMS)
    graph.bind("dcat", DCAT)
    graph.bind("omaro", OMARO_NS)
    graph.bind("prov", PROV)
    graph.bind("schema", SCHEMA)
    graph.bind("sosa", SOSA)
    graph.bind("qudt", QUDT)
    graph.bind("crm", CRM)
    graph.bind("crmsci", CRMSCI)
    graph.bind("time", TIME)


def _code(category: str, value: str) -> URIRef:
    return URIRef(controlled_value_uri(category, value))


def _add_evidence(
    graph: Graph,
    owner: URIRef,
    owner_uri: str,
    evidence_rows: list[dict[str, Any]],
    *,
    usage_activity: URIRef | None = None,
) -> None:
    """Project structured evidence with stable, occurrence-scoped identifiers."""
    for evidence in evidence_rows:
        evidence_uri = URIRef(
            assertion_uri(
                "evidence",
                owner_uri,
                evidence["citation"],
                evidence["evidence_type"],
                evidence["relation"],
                evidence.get("resource_uri") or "",
                evidence.get("note") or "",
            )
        )
        graph.add((owner, OMARO_NS.hasEvidence, evidence_uri))
        graph.add((evidence_uri, RDF.type, OMARO_NS.Evidence))
        graph.add(
            (evidence_uri, DCTERMS.bibliographicCitation, Literal(evidence["citation"]))
        )
        graph.add(
            (
                evidence_uri,
                OMARO_NS.evidenceType,
                _code("evidence-type", evidence["evidence_type"]),
            )
        )
        graph.add(
            (
                evidence_uri,
                OMARO_NS.evidenceRelation,
                _code("evidence-role", evidence["relation"]),
            )
        )
        if evidence.get("resource_uri"):
            graph.add((evidence_uri, DCTERMS.source, URIRef(evidence["resource_uri"])))
        if evidence.get("note"):
            graph.add((evidence_uri, RDFS.comment, Literal(evidence["note"])))
        if usage_activity is not None:
            usage_uri = URIRef(
                assertion_uri("evidence-use", owner_uri, str(evidence_uri))
            )
            graph.add((usage_activity, PROV.qualifiedUsage, usage_uri))
            graph.add((usage_uri, RDF.type, PROV.Usage))
            graph.add((usage_uri, PROV.entity, evidence_uri))
            graph.add(
                (
                    usage_uri,
                    PROV.hadRole,
                    _code("evidence-role", evidence["relation"]),
                )
            )


def _add_policy_and_scope_links(
    graph: Graph, node: URIRef, row: dict[str, Any]
) -> None:
    for scope_uri in row.get("applicability_scope_uris", []):
        graph.add((node, OMARO_NS.hasApplicabilityScope, URIRef(scope_uri)))
    for policy_uri in row.get("projection_policy_uris", []):
        graph.add((node, OMARO_NS.underProjectionPolicy, URIRef(policy_uri)))


def _add_source_vocabulary(
    graph: Graph,
    dataset: Dataset,
    *,
    include_exact_matches: bool,
    include_source_labels: bool,
    scheme_uris: set[str] | None = None,
) -> None:
    """Add source concepts, labels, and selected MIMO relations to an RDF graph."""
    concepts_by_uri = dataset.concepts_by_uri
    for scheme in dataset.concept_schemes:
        if scheme_uris is not None and scheme["uri"] not in scheme_uris:
            continue
        node = URIRef(scheme["uri"])
        graph.add((node, RDF.type, SKOS.ConceptScheme))
        graph.add((node, SKOS.prefLabel, Literal(scheme["label"], lang="en")))

    for concept in dataset.concepts:
        if scheme_uris is not None and concept["scheme_uri"] not in scheme_uris:
            continue
        node = URIRef(concept["uri"])
        graph.add((node, RDF.type, SKOS.Concept))
        graph.add((node, SKOS.inScheme, URIRef(concept["scheme_uri"])))
        if concept.get("notation"):
            graph.add((node, SKOS.notation, Literal(concept["notation"])))
        if concept.get("definition"):
            graph.add(
                (node, SKOS.definition, Literal(concept["definition"], lang="en"))
            )
        if concept.get("created"):
            graph.add(
                (node, DCTERMS.created, Literal(concept["created"], datatype=XSD.date))
            )
    if include_source_labels:
        for label in dataset.labels:
            if (
                scheme_uris is not None
                and concepts_by_uri[label["concept_uri"]]["scheme_uri"]
                not in scheme_uris
            ):
                continue
            predicate = {
                "preferred": SKOS.prefLabel,
                "alternative": SKOS.altLabel,
                "hidden": SKOS.hiddenLabel,
            }[label["label_type"]]
            graph.add(
                (
                    URIRef(label["concept_uri"]),
                    predicate,
                    Literal(label["label"], lang=label["language"]),
                )
            )
    for relation in dataset.source_relations:
        if scheme_uris is not None and (
            concepts_by_uri[relation["subject_uri"]]["scheme_uri"] not in scheme_uris
            or concepts_by_uri[relation["object_uri"]]["scheme_uri"] not in scheme_uris
        ):
            continue
        if relation["predicate_uri"] == EXACT_MATCH and not include_exact_matches:
            continue
        subject = URIRef(relation["subject_uri"])
        obj = URIRef(relation["object_uri"])
        predicate = URIRef(relation["predicate_uri"])
        graph.add((subject, predicate, obj))
        if relation["predicate_uri"] == BROADER:
            graph.add((obj, URIRef(NARROWER), subject))


def source_snapshot_graph(dataset: Dataset) -> Graph:
    """Return the preserved MIMO source graph, including its exact-match predicates."""
    graph = Graph()
    _bind_namespaces(graph)
    bundle = URIRef(f"{dataset.metadata['dataset_uri']}#mimo-source-snapshot")
    graph.add((bundle, RDF.type, PROV.Bundle))
    graph.add(
        (
            bundle,
            DCTERMS.title,
            Literal("Preserved MIMO source vocabulary snapshot", lang="en"),
        )
    )
    graph.add(
        (
            bundle,
            PROV.generatedAtTime,
            Literal(dataset.metadata["source_retrieved_at"], datatype=XSD.dateTime),
        )
    )
    graph.add((bundle, DCTERMS.license, LICENSE_URI))
    for source in dataset.metadata["sources"]:
        graph.add((bundle, DCTERMS.source, URIRef(source)))
    _add_source_vocabulary(
        graph,
        dataset,
        include_exact_matches=True,
        include_source_labels=True,
        scheme_uris={HS_SCHEME, INSTRUMENT_SCHEME},
    )
    return graph


def dataset_graph(dataset: Dataset) -> Graph:
    """Return the project graph with qualified classification semantics."""
    graph = Graph()
    _bind_namespaces(graph)

    ontology_uri = URIRef(dataset.metadata["ontology_uri"])
    ontology_version_uri = URIRef(dataset.metadata["ontology_version_iri"])
    dataset_base_uri = URIRef(DATASET_BASE_URI)
    dataset_uri = URIRef(dataset.metadata["dataset_uri"])
    graph.add((ontology_uri, RDF.type, OWL.Ontology))
    graph.add(
        (ontology_uri, OWL.versionInfo, Literal(dataset.metadata["schema_version"]))
    )
    graph.add((ontology_uri, OWL.versionIRI, ontology_version_uri))
    graph.add((ontology_uri, DCTERMS.license, LICENSE_URI))
    graph.add((ontology_uri, DCTERMS.creator, CREATOR_URI))
    graph.add((ontology_uri, DCTERMS.publisher, Literal("MODAVIS Project")))
    graph.add((ontology_uri, VANN.preferredNamespacePrefix, Literal("omaro")))
    graph.add((ontology_uri, VANN.preferredNamespaceUri, URIRef(OMARO)))
    graph.add((ontology_uri, DCTERMS.relation, VAO_RELEASE_IRI))
    graph.add((ontology_uri, DCTERMS.relation, MODAVIS_RELEASE_IRI))
    graph.add(
        (
            ontology_uri,
            DCTERMS.title,
            Literal(
                "OMARO: Ontology for Multiperspectivity, Assertions, and Review in Organology",
                lang="en",
            ),
        )
    )
    graph.add(
        (
            ontology_uri,
            DCTERMS.description,
            Literal(
                "An ontology for representing contextualized organological assertions, "
                "their perspectives and applicability, supporting evidence, authority, "
                "review decisions, and governed projections without collapsing disagreement.",
                lang="en",
            ),
        )
    )
    graph.add((ontology_version_uri, RDF.type, OWL.Ontology))
    graph.add((ontology_version_uri, DCTERMS.isVersionOf, ontology_uri))
    graph.add(
        (
            ontology_version_uri,
            OWL.versionInfo,
            Literal(dataset.metadata["schema_version"]),
        )
    )
    graph.add((dataset_base_uri, RDF.type, DCAT.Dataset))
    graph.add((dataset_base_uri, DCAT_NS.hasVersion, dataset_uri))
    graph.add((dataset_base_uri, DCAT_NS.hasCurrentVersion, dataset_uri))
    graph.add((dataset_uri, RDF.type, DCAT.Dataset))
    graph.add((dataset_uri, DCAT_NS.isVersionOf, dataset_base_uri))
    graph.add(
        (dataset_uri, DCAT_NS.version, Literal(dataset.metadata["dataset_version"]))
    )
    graph.add(
        (dataset_uri, DCTERMS.title, Literal(dataset.metadata["title"], lang="en"))
    )
    graph.add((dataset_uri, DCTERMS.identifier, Literal(dataset.metadata["doi"])))
    graph.add((dataset_uri, DCTERMS.license, LICENSE_URI))
    graph.add((dataset_uri, DCTERMS.conformsTo, ontology_version_uri))
    graph.add((dataset_uri, DCTERMS.relation, VAO_RELEASE_IRI))
    graph.add((dataset_uri, DCTERMS.relation, MODAVIS_RELEASE_IRI))
    graph.add((dataset_uri, DCAT.landingPage, REPO_URI))
    graph.add(
        (
            dataset_uri,
            DCTERMS.issued,
            Literal(dataset.metadata["generated_at"], datatype=XSD.dateTime),
        )
    )
    _add_creator(graph, dataset_uri, dataset)
    for source in dataset.metadata["sources"]:
        graph.add((dataset_uri, DCTERMS.source, URIRef(source)))

    _add_source_vocabulary(
        graph,
        dataset,
        include_exact_matches=False,
        include_source_labels=False,
    )
    class_terms = {
        "LabelAssertion": (
            "label assertion",
            "A contextualized assertion that assigns a lexical label to a concept.",
        ),
        "NoteAssertion": (
            "note assertion",
            "A contextualized assertion that assigns a definition or other SKOS note to a concept.",
        ),
        "ClassificationAssertion": (
            "classification assertion",
            "An occurrence-level claim that a named target is classified by a concept under a recorded perspective, scope, method, and provenance.",
        ),
        "ClassificationAssignment": (
            "classification assignment",
            "The provenance-bearing activity that applies a named classification to a target and generates a distinct classification assertion entity.",
        ),
        "ReviewStatus": (
            "review status",
            "A controlled lifecycle status used for assertions without collapsing separate review decisions.",
        ),
        "QualityRule": (
            "quality rule",
            "A deterministic validation or review-signal rule that has no human review effect by itself.",
        ),
        "QualityFinding": (
            "quality finding",
            "An occurrence of a quality rule against a target assertion, retained as a review signal.",
        ),
        "ReviewEvent": (
            "review event",
            "A provenance-bearing review activity that evaluates an assertion and generates a distinct review decision.",
        ),
        "ReviewDecision": (
            "review decision",
            "The durable outcome entity generated by a review event; lifecycle links apply to decisions rather than to the activities that created them.",
        ),
        "OrganologicalTarget": (
            "organological target",
            "A target whose physical identity, component structure, configuration, state, sounding realization, or performance role may be described independently.",
        ),
        "InstrumentConfiguration": (
            "instrument configuration",
            "A time-bounded arrangement of an object, components, modules, accessories, or signal path that may receive its own classification.",
        ),
        "ConditionState": (
            "condition state",
            "A time-bounded condition of an object or component, kept distinct from the configuration it was intended to have.",
        ),
        "InstrumentComponent": (
            "instrument component",
            "A physical component that can be observed or classified without propagating its class to the whole object.",
        ),
        "FunctionalModule": (
            "functional module",
            "A functional subsystem or configurable module participating in sound production or control.",
        ),
        "SoundingRealization": (
            "sounding realization",
            "A particular occurrence or configuration of sounding, distinct from a physical artefact realization in other music ontologies.",
        ),
        "ObservationAssessment": (
            "observation assessment",
            "A record of whether an organological property was observed or applicable; it is not itself an observation activity when the status is non-observation or non-applicability.",
        ),
        "OrganologicalObservation": (
            "organological observation",
            "An observation or measurement of a target or part, recording property, result, procedure, observer, and time before classification inference.",
        ),
        "ObservationResult": (
            "observation result",
            "A categorical, literal, quantity, or range result of an organological observation.",
        ),
        "ClassificationCriterion": (
            "classification criterion",
            "A governed description of an observable organological basis and any documented inference logic used by an assignment.",
        ),
        "ClassificationExpression": (
            "classification expression",
            "An ordered compound classification expression whose component targets and suffix scope are explicit or explicitly unresolved.",
        ),
        "ClassificationExpressionMember": (
            "classification expression member",
            "One ordered member of a compound classification expression.",
        ),
        "ProtocolApplication": (
            "protocol application",
            "The application of an authoritative cultural or community protocol to specified resources, separate from legal rights and epistemic review.",
        ),
        "UseDecision": (
            "use decision",
            "An action-, purpose-, audience-, and time-specific authorization decision governing publication or reuse.",
        ),
        "LabelProfile": (
            "label linguistic profile",
            "A conservative linguistic and display profile attached to one assertion-scoped label resource.",
        ),
        "Perspective": (
            "named perspective",
            "An explicit source, institutional, scholarly, community, curatorial, historical, or technical standpoint from which an assertion is made or evaluated.",
        ),
        "ApplicabilityScope": (
            "applicability scope",
            "A resource stating whether and under which communities, places, periods, uses, techniques, configurations, languages, or times an assertion applies.",
        ),
        "AuthorityAssignment": (
            "authority assignment",
            "A time-bounded mandate connecting an agent to roles, subject matter, communities, and validation dimensions.",
        ),
        "ProjectionPolicy": (
            "projection policy",
            "A versioned rule set governing which qualified assertions may appear in a named graph or simplified direct view.",
        ),
        "ConceptRelationAssertion": (
            "concept relation assertion",
            "A qualified structural relation or purpose-specific mapping claim between two concepts.",
        ),
        "Evidence": (
            "evidence record",
            "A structured citation, resource, or note directionally related to an assertion, observation, criterion, or review decision.",
        ),
        "ReviewRequirement": (
            "review requirement",
            "A minimum reviewer-authority, validation-dimension, outcome, and independence condition used by a projection policy.",
        ),
        "VetoRule": (
            "review veto rule",
            "A policy rule identifying active review decisions that prevent an assertion from entering a projection.",
        ),
    }
    for class_name, (label, definition) in class_terms.items():
        class_uri = OMARO_NS[class_name]
        graph.add((class_uri, RDF.type, OWL.Class))
        graph.add((class_uri, RDF.type, RDFS.Class))
        graph.add((class_uri, RDFS.label, Literal(label, lang="en")))
        graph.add((class_uri, RDFS.comment, Literal(definition, lang="en")))
        graph.add((class_uri, RDFS.isDefinedBy, ontology_uri))
    for class_name in (
        "ClassificationAssertion",
        "ConceptRelationAssertion",
        "LabelAssertion",
        "NoteAssertion",
    ):
        graph.add((OMARO_NS[class_name], RDFS.subClassOf, RDF.Statement))
        graph.add((OMARO_NS[class_name], RDFS.subClassOf, PROV.Entity))
    for class_name in (
        "ApplicabilityScope",
        "AuthorityAssignment",
        "Evidence",
        "LabelProfile",
        "Perspective",
        "ProjectionPolicy",
        "QualityFinding",
        "ReviewDecision",
        "ObservationResult",
        "ClassificationExpression",
        "ClassificationExpressionMember",
        "ProtocolApplication",
        "UseDecision",
    ):
        graph.add((OMARO_NS[class_name], RDFS.subClassOf, PROV.Entity))
    graph.add((OMARO_NS.ReviewEvent, RDFS.subClassOf, PROV.Activity))
    graph.add((OMARO_NS.ClassificationAssignment, RDFS.subClassOf, PROV.Activity))
    # State the local identity contract even without importing PROV-O. These
    # disjointness axioms do not make every target kind mutually exclusive:
    # a physical component may also have a functional-module role.
    for activity in ("ClassificationAssignment", "ReviewEvent"):
        for entity in (
            "ClassificationAssertion",
            "ConceptRelationAssertion",
            "LabelAssertion",
            "NoteAssertion",
            "ReviewDecision",
        ):
            graph.add((OMARO_NS[activity], OWL.disjointWith, OMARO_NS[entity]))
    graph.add(
        (OMARO_NS.ClassificationAssignment, RDFS.subClassOf, CRM.E17_Type_Assignment)
    )
    graph.add((OMARO_NS.OrganologicalObservation, RDFS.subClassOf, SOSA.Observation))
    graph.add(
        (
            OMARO_NS.OrganologicalObservation,
            RDFS.subClassOf,
            OMARO_NS.ObservationAssessment,
        )
    )
    graph.add(
        (OMARO_NS.OrganologicalObservation, RDFS.subClassOf, CRMSCI.S27_Observation)
    )
    graph.add((OMARO_NS.ClassificationCriterion, RDFS.subClassOf, PROV.Plan))
    for target_class in (
        "InstrumentConfiguration",
        "ConditionState",
        "InstrumentComponent",
        "FunctionalModule",
        "SoundingRealization",
    ):
        graph.add(
            (OMARO_NS[target_class], RDFS.subClassOf, OMARO_NS.OrganologicalTarget)
        )
    graph.add((OMARO_NS.classifiedAs, RDF.type, RDF.Property))
    graph.add(
        (
            OMARO_NS.classifiedAs,
            RDFS.label,
            Literal("classified as", lang="en"),
        )
    )
    graph.add((OMARO_NS.sourcePredicate, RDF.type, RDF.Property))
    graph.add((OMARO_NS.sourceRecord, RDF.type, RDF.Property))
    graph.add((OMARO_NS.assertionOrigin, RDF.type, RDF.Property))
    graph.add((OMARO_NS.reviewStatus, RDF.type, RDF.Property))
    graph.add((OMARO_NS.reviewStatusResource, RDF.type, RDF.Property))
    graph.add((OMARO_NS.normalizedForm, RDF.type, RDF.Property))
    graph.add((OMARO_NS.sourceLayer, RDF.type, RDF.Property))
    graph.add((OMARO_NS.qualityRule, RDF.type, RDF.Property))
    graph.add((OMARO_NS.targetAssertion, RDF.type, RDF.Property))
    graph.add((OMARO_NS.reviewEffect, RDF.type, RDF.Property))
    graph.add((OMARO_NS.validationDimension, RDF.type, RDF.Property))
    graph.add((OMARO_NS.submittedLanguageTag, RDF.type, RDF.Property))
    graph.add((OMARO_NS.languageTagStatus, RDF.type, RDF.Property))
    graph.add((OMARO_NS.languageRegistry, RDF.type, RDF.Property))
    graph.add((OMARO_NS.labelResource, RDF.type, RDF.Property))
    graph.add((OMARO_NS.skosProjectionStatus, RDF.type, RDF.Property))
    property_names = {
        "labelProfile",
        "sourceLabelAssertion",
        "primaryLanguageSubtag",
        "explicitScriptSubtag",
        "defaultScriptSubtag",
        "regionSubtag",
        "variantSubtag",
        "extensionSubtag",
        "privateUseSubtag",
        "languageVariety",
        "writingSystem",
        "observedScript",
        "hasCommonOrInheritedCharacters",
        "scriptObservationMethod",
        "scriptRegistry",
        "transliterationSystem",
        "transcriptionSystem",
        "pronunciation",
        "audio",
        "termRole",
        "translationStatus",
        "appliesToCommunity",
        "appliesToPlace",
        "appliesToPeriod",
        "appliesToUsageDomain",
        "displayPolicy",
        "searchPolicy",
        "schemeType",
        "schemeStatus",
        "schemePerspective",
        "perspective",
        "governance",
        "perspectiveType",
        "heldBy",
        "representsCommunity",
        "authorityAssignment",
        "scopeMode",
        "hasApplicabilityScope",
        "appliesToPlayingTechnique",
        "appliesToInstrumentConfiguration",
        "appliesToLanguageVariety",
        "temporalStart",
        "temporalEnd",
        "authorityRole",
        "authorityBasis",
        "conferredBy",
        "subjectMatter",
        "delegationPermitted",
        "assignmentStatus",
        "revocationEvent",
        "revocationEffect",
        "coveredValidationDimension",
        "coveredAction",
        "graphRole",
        "directAssertion",
        "eligibleStance",
        "requiredReviewOutcome",
        "eligibleReviewerAuthority",
        "reviewRequirement",
        "minimumIndependentReviewers",
        "vetoRule",
        "vetoOutcome",
        "contextMatchRequired",
        "unknownScopeBehavior",
        "includesSourceLayer",
        "policyVersion",
        "underProjectionPolicy",
        "assignedBy",
        "classificationAssignment",
        "generatedAssertion",
        "classificationScheme",
        "schemeVersion",
        "classificationMethod",
        "mappingPurpose",
        "classificationCriterion",
        "criterionType",
        "observableProperty",
        "usedProcedure",
        "supportsClassification",
        "usedAssessment",
        "usedObservation",
        "inferenceLogic",
        "classificationExpression",
        "stance",
        "targetType",
        "targetKind",
        "validFrom",
        "validUntil",
        "reviewerAuthority",
        "reviewMethod",
        "reviewOutcome",
        "decisionStatus",
        "supersedesDecision",
        "suspendsDecision",
        "reinstatesDecision",
        "rationale",
        "hasEvidence",
        "evidenceType",
        "evidenceRelation",
        "reviewDecision",
        "assessmentFeatureOfInterest",
        "assessmentProperty",
        "assessmentProcedure",
        "assessmentAgent",
        "assessmentSensor",
        "assessmentResult",
        "assessmentTime",
        "assessmentPart",
        "assessmentStatus",
        "resultKind",
        "categoricalValue",
        "numericValue",
        "minimumValue",
        "maximumValue",
        "unit",
        "uncertainty",
        "tolerance",
        "hasComponent",
        "componentOf",
        "componentRole",
        "hasFunctionalModule",
        "realizesInstrumentConcept",
        "configurationOf",
        "conditionStateOf",
        "actualPlayingTechnique",
        "intendedPlayingTechnique",
        "performanceEvent",
        "hasExpressionMember",
        "memberClassification",
        "memberAssertion",
        "memberTarget",
        "sequenceIndex",
        "memberNotation",
        "notationLiteral",
        "localSuffixNotation",
        "sharedSuffixNotation",
        "notationGrammar",
        "combinationOperator",
        "parseStatus",
        "protocol",
        "protocolType",
        "protocolApplication",
        "targetResource",
        "useAction",
        "usePurpose",
        "useAudience",
        "useDecision",
        "decisionMethod",
        "enforcementMode",
        "issuedBy",
        "appliedBy",
        "decidedBy",
        "criterionStatus",
        "protocolStatus",
        "useDecisionStatus",
        "protocolResolutionStatus",
        "protocolIntegritySha256",
        "integrityVerificationMethod",
        "integrityAttestation",
        "protocolArtifactPath",
        "legalBasis",
        "legalBasisStatus",
        "legalBasisAssessedBy",
        "consentRecord",
        "consentStatus",
        "consentAssessedBy",
        "supersedesProtocolApplication",
        "supersedesUseDecision",
    }
    for property_name in property_names:
        graph.add((OMARO_NS[property_name], RDF.type, RDF.Property))

    # Publish the operational vocabulary as an OWL ontology, not merely as a
    # collection of predicates encountered in instance data.  The conservative
    # ranges below are stable across all supported assertion targets.
    object_properties = {
        "classifiedAs": SKOS.Concept,
        "sourcePredicate": RDF.Property,
        "sourceRecord": PROV.Entity,
        "reviewStatusResource": OMARO_NS.ReviewStatus,
        "targetAssertion": None,
        "qualityRule": OMARO_NS.QualityRule,
        "languageRegistry": PROV.Entity,
        "labelResource": SKOSXL.Label,
        "labelProfile": OMARO_NS.LabelProfile,
        "sourceLabelAssertion": OMARO_NS.LabelAssertion,
        "languageVariety": None,
        "writingSystem": None,
        "scriptRegistry": PROV.Entity,
        "transliterationSystem": None,
        "transcriptionSystem": None,
        "audio": None,
        "appliesToCommunity": None,
        "appliesToPlace": None,
        "appliesToPeriod": None,
        "appliesToUsageDomain": None,
        "appliesToPlayingTechnique": None,
        "appliesToInstrumentConfiguration": None,
        "appliesToLanguageVariety": None,
        "schemePerspective": OMARO_NS.Perspective,
        "governance": None,
        "perspective": OMARO_NS.Perspective,
        "heldBy": PROV.Agent,
        "representsCommunity": PROV.Agent,
        "authorityAssignment": OMARO_NS.AuthorityAssignment,
        "hasApplicabilityScope": OMARO_NS.ApplicabilityScope,
        "authorityBasis": None,
        "conferredBy": PROV.Agent,
        "subjectMatter": None,
        "revocationEvent": None,
        "reviewRequirement": OMARO_NS.ReviewRequirement,
        "vetoRule": OMARO_NS.VetoRule,
        "underProjectionPolicy": OMARO_NS.ProjectionPolicy,
        "assignedBy": PROV.Agent,
        "classificationAssignment": OMARO_NS.ClassificationAssignment,
        "generatedAssertion": OMARO_NS.ClassificationAssertion,
        "classificationScheme": SKOS.ConceptScheme,
        "schemeVersion": None,
        "classificationMethod": SKOS.Concept,
        "mappingPurpose": SKOS.Concept,
        "classificationCriterion": OMARO_NS.ClassificationCriterion,
        "criterionType": SKOS.Concept,
        "observableProperty": None,
        "usedProcedure": None,
        "supportsClassification": SKOS.Concept,
        "usedAssessment": OMARO_NS.ObservationAssessment,
        "usedObservation": OMARO_NS.OrganologicalObservation,
        "inferenceLogic": None,
        "classificationExpression": OMARO_NS.ClassificationExpression,
        "targetType": SKOS.Concept,
        "targetKind": SKOS.Concept,
        "stance": SKOS.Concept,
        "perspectiveType": SKOS.Concept,
        "scopeMode": SKOS.Concept,
        "validationDimension": SKOS.Concept,
        "authorityRole": SKOS.Concept,
        "coveredValidationDimension": SKOS.Concept,
        "coveredAction": SKOS.Concept,
        "eligibleStance": SKOS.Concept,
        "requiredReviewOutcome": SKOS.Concept,
        "eligibleReviewerAuthority": SKOS.Concept,
        "vetoOutcome": SKOS.Concept,
        "reviewerAuthority": SKOS.Concept,
        "reviewMethod": SKOS.Concept,
        "reviewOutcome": SKOS.Concept,
        "decisionStatus": SKOS.Concept,
        "supersedesDecision": OMARO_NS.ReviewDecision,
        "suspendsDecision": OMARO_NS.ReviewDecision,
        "reinstatesDecision": OMARO_NS.ReviewDecision,
        "hasEvidence": OMARO_NS.Evidence,
        "evidenceType": SKOS.Concept,
        "evidenceRelation": SKOS.Concept,
        "reviewDecision": OMARO_NS.ReviewDecision,
        "assessmentFeatureOfInterest": None,
        "assessmentProperty": None,
        "assessmentProcedure": None,
        "assessmentAgent": PROV.Agent,
        "assessmentSensor": None,
        "assessmentResult": OMARO_NS.ObservationResult,
        "assessmentPart": OMARO_NS.OrganologicalTarget,
        "assessmentStatus": SKOS.Concept,
        "resultKind": SKOS.Concept,
        "categoricalValue": None,
        "unit": None,
        "hasComponent": OMARO_NS.OrganologicalTarget,
        "componentOf": OMARO_NS.OrganologicalTarget,
        "componentRole": None,
        "hasFunctionalModule": OMARO_NS.FunctionalModule,
        "realizesInstrumentConcept": SKOS.Concept,
        "configurationOf": OMARO_NS.OrganologicalTarget,
        "conditionStateOf": OMARO_NS.OrganologicalTarget,
        "actualPlayingTechnique": None,
        "intendedPlayingTechnique": None,
        "performanceEvent": OMARO_NS.OrganologicalTarget,
        "hasExpressionMember": OMARO_NS.ClassificationExpressionMember,
        "memberClassification": SKOS.Concept,
        "memberAssertion": OMARO_NS.ClassificationAssertion,
        "memberTarget": OMARO_NS.OrganologicalTarget,
        "notationGrammar": None,
        "combinationOperator": SKOS.Concept,
        "parseStatus": SKOS.Concept,
        "protocol": None,
        "protocolType": None,
        "protocolApplication": OMARO_NS.ProtocolApplication,
        "targetResource": None,
        "useAction": SKOS.Concept,
        "usePurpose": None,
        "useAudience": None,
        "useDecision": SKOS.Concept,
        "decisionMethod": None,
        "enforcementMode": SKOS.Concept,
        "issuedBy": PROV.Agent,
        "appliedBy": PROV.Agent,
        "decidedBy": PROV.Agent,
        "criterionStatus": SKOS.Concept,
        "protocolStatus": SKOS.Concept,
        "useDecisionStatus": SKOS.Concept,
        "protocolResolutionStatus": SKOS.Concept,
        "integrityVerificationMethod": SKOS.Concept,
        "integrityAttestation": None,
        "legalBasis": None,
        "legalBasisStatus": SKOS.Concept,
        "legalBasisAssessedBy": PROV.Agent,
        "consentRecord": None,
        "consentStatus": SKOS.Concept,
        "consentAssessedBy": PROV.Agent,
        "supersedesProtocolApplication": OMARO_NS.ProtocolApplication,
        "supersedesUseDecision": OMARO_NS.UseDecision,
    }
    for property_name, range_class in object_properties.items():
        property_uri = OMARO_NS[property_name]
        graph.add((property_uri, RDF.type, OWL.ObjectProperty))
        if range_class is not None:
            graph.add((property_uri, RDFS.range, range_class))

    datatype_properties = {
        "assertionOrigin",
        "reviewStatus",
        "normalizedForm",
        "sourceLayer",
        "reviewEffect",
        "submittedLanguageTag",
        "languageTagStatus",
        "skosProjectionStatus",
        "primaryLanguageSubtag",
        "explicitScriptSubtag",
        "defaultScriptSubtag",
        "regionSubtag",
        "variantSubtag",
        "extensionSubtag",
        "privateUseSubtag",
        "observedScript",
        "hasCommonOrInheritedCharacters",
        "scriptObservationMethod",
        "pronunciation",
        "termRole",
        "translationStatus",
        "displayPolicy",
        "searchPolicy",
        "schemeType",
        "schemeStatus",
        "temporalStart",
        "temporalEnd",
        "delegationPermitted",
        "assignmentStatus",
        "revocationEffect",
        "graphRole",
        "directAssertion",
        "minimumIndependentReviewers",
        "contextMatchRequired",
        "unknownScopeBehavior",
        "includesSourceLayer",
        "policyVersion",
        "validFrom",
        "validUntil",
        "rationale",
        "numericValue",
        "minimumValue",
        "maximumValue",
        "uncertainty",
        "tolerance",
        "sequenceIndex",
        "memberNotation",
        "notationLiteral",
        "localSuffixNotation",
        "sharedSuffixNotation",
        "protocolIntegritySha256",
        "protocolArtifactPath",
        "assessmentTime",
    }
    for property_name in datatype_properties:
        property_uri = OMARO_NS[property_name]
        graph.add((property_uri, RDF.type, OWL.DatatypeProperty))
        datatype = {
            "delegationPermitted": XSD.boolean,
            "directAssertion": XSD.boolean,
            "hasCommonOrInheritedCharacters": XSD.boolean,
            "contextMatchRequired": XSD.boolean,
            "includesSourceLayer": XSD.boolean,
            "minimumIndependentReviewers": XSD.integer,
            "temporalStart": XSD.dateTime,
            "temporalEnd": XSD.dateTime,
            "assessmentTime": XSD.dateTime,
            "validFrom": XSD.dateTime,
            "validUntil": XSD.dateTime,
        }.get(property_name, XSD.string)
        graph.add((property_uri, RDFS.range, datatype))

    base_property_names = {
        "classifiedAs",
        "sourcePredicate",
        "sourceRecord",
        "assertionOrigin",
        "reviewStatus",
        "reviewStatusResource",
        "normalizedForm",
        "sourceLayer",
        "qualityRule",
        "targetAssertion",
        "reviewEffect",
        "validationDimension",
        "submittedLanguageTag",
        "languageTagStatus",
        "languageRegistry",
        "labelResource",
        "skosProjectionStatus",
    }
    assert object_properties.keys().isdisjoint(datatype_properties)
    assert set(property_names) | base_property_names == (
        object_properties.keys() | datatype_properties
    )
    property_definitions: dict[str, str] = {}
    property_definitions.update(
        {
            "assertionOrigin": "States whether a record is source-asserted, source-derived, or locally authored.",
            "assignedBy": "Identifies the agent responsible for making an assignment occurrence.",
            "classificationCriterion": "Identifies a governed criterion applied when producing a classification assertion.",
            "classificationMethod": "Records the method used to produce a classification or concept-relation assertion.",
            "mappingPurpose": "Identifies an operation for which a qualified SKOS mapping is stated to be suitable; it does not grant permission or establish cultural authorization.",
            "classificationScheme": "Identifies the concept scheme used by a classification assertion.",
            "classifiedAs": "Links a classification assertion target to the classification concept asserted for it.",
            "evidenceType": "Records the controlled category of an evidence resource.",
            "hasEvidence": "Links an assertion or review decision to a structured evidence record.",
            "reviewStatus": "Records a compatibility code for the lifecycle status of an assertion.",
            "reviewStatusResource": "Links an assertion to its controlled review-status resource.",
            "schemeStatus": "Records the lifecycle status of a registered concept scheme.",
            "schemeType": "Records the controlled category of a registered concept scheme.",
            "schemeVersion": "Identifies the version of a concept scheme used by an assertion.",
            "sourceLayer": "Records the named provenance layer to which a source record belongs.",
            "sourcePredicate": "Records the predicate used by a preserved source statement before qualified projection.",
            "sourceRecord": "Links a project record to the versioned source snapshot from which it was asserted or derived.",
            "stance": "Records the asserted, proposed, disputed, rejected, or superseded position of a claim.",
            "targetType": "Records the ontological level of the target described by a classification assertion.",
            "validFrom": "Records the start instant of a claim, perspective, mandate, or decision lifecycle.",
            "validUntil": "Records the end instant of a claim, perspective, mandate, or decision lifecycle.",
        }
    )
    property_definitions.update(
        {
            "appliesToCommunity": "Identifies a community for which the described scope or label profile applies.",
            "appliesToInstrumentConfiguration": "Identifies an instrument configuration for which an assertion applies.",
            "appliesToLanguageVariety": "Identifies a language variety for which an assertion applies.",
            "appliesToPeriod": "Identifies a historical or cultural period for which the described scope applies.",
            "appliesToPlace": "Identifies a place for which the described scope or label profile applies.",
            "appliesToPlayingTechnique": "Identifies a playing technique for which an assertion applies.",
            "appliesToUsageDomain": "Identifies a usage domain for which the described scope or label profile applies.",
            "assignmentStatus": "Records the lifecycle status of an authority assignment or perspective.",
            "authorityAssignment": "Links a perspective, assertion, or review decision to the mandate that authorizes it.",
            "authorityBasis": "Links an authority assignment to the resource documenting its mandate.",
            "authorityRole": "Records the controlled authority role granted by a mandate.",
            "conferredBy": "Identifies the agent that granted an authority assignment.",
            "coveredValidationDimension": "Records a validation dimension covered by an authority assignment.",
            "delegationPermitted": "States whether an authority assignment permits the authorized agent to delegate its mandate.",
            "governance": "Links a concept scheme or perspective to its governance resource.",
            "hasApplicabilityScope": "Links a qualified assertion, mandate, or review decision to an applicability scope.",
            "heldBy": "Identifies the agent responsible for a named perspective.",
            "perspective": "Links an assertion, scope, or review decision to the perspective under which it is expressed.",
            "perspectiveType": "Records the controlled category of a named perspective.",
            "representsCommunity": "Identifies a community explicitly represented by a perspective, mandate, or review decision.",
            "revocationEffect": "Records whether revocation of a mandate is prospective or retroactive.",
            "revocationEvent": "Links an authority assignment to the resource documenting its revocation.",
            "schemePerspective": "Links a concept scheme to the perspective under which it is maintained or presented.",
            "scopeMode": "States the epistemic mode of an applicability scope, including explicit applicability and documented uncertainty.",
            "subjectMatter": "Identifies exact subject matter covered by an authority assignment.",
            "temporalEnd": "Records the end of subject-matter applicability as an instant.",
            "temporalStart": "Records the start of subject-matter applicability as an instant.",
        }
    )
    property_definitions.update(
        {
            "actualPlayingTechnique": "Identifies a playing technique observed in an actual sounding realization or performance.",
            "categoricalValue": "Links an observation result to a controlled categorical value.",
            "classificationAssignment": "Links an assertion to the distinct assignment activity that generated it.",
            "classificationExpression": "Links an assertion or source concept to an ordered compound classification expression.",
            "criterionType": "Identifies the organological facet addressed by a classification criterion.",
            "criterionStatus": "Identifies the controlled lifecycle status of a classification criterion.",
            "combinationOperator": "Identifies the controlled operator joining the members of a classification expression.",
            "componentOf": "Links a component to the target of which it is a physical or functional part.",
            "componentRole": "Identifies the evidenced role of a component in a configuration.",
            "conditionStateOf": "Links a condition state to the target whose condition it records.",
            "coveredAction": "Identifies a use action that an authority mandate explicitly empowers its holder to decide.",
            "configurationOf": "Links a configuration to the persistent target configured in that state.",
            "decisionMethod": "Identifies the community- or authority-defined procedure by which a use decision was reached.",
            "decidedBy": "Identifies the authorized agent responsible for a use decision.",
            "enforcementMode": "Identifies whether a protocol is advisory, requires human decision, or has an authorized machine-enforceable rule.",
            "evidenceRelation": "Identifies whether evidence supports, opposes, qualifies, or documents a claim or decision.",
            "generatedAssertion": "Links an assignment activity to the assertion entity it generated.",
            "hasComponent": "Links a target or configuration to one of its physical components.",
            "hasExpressionMember": "Links a compound classification expression to one ordered member.",
            "hasFunctionalModule": "Links a target or configuration to a functional subsystem or module.",
            "inferenceLogic": "Identifies the documented inference logic applied by a classification assignment.",
            "intendedPlayingTechnique": "Identifies an intended or prescribed technique without claiming that it occurred.",
            "issuedBy": "Identifies the authority or community agent that issued an applied protocol.",
            "appliedBy": "Identifies the agent that recorded or applied a protocol to the target resources.",
            "localSuffixNotation": "Preserves suffix notation explicitly scoped to one expression member.",
            "maximumValue": "Records the maximum numeric value of a range observation result.",
            "memberAssertion": "Links an expression member to the qualified assertion it groups.",
            "memberClassification": "Links an expression member to its classification concept.",
            "memberNotation": "Preserves the source notation of one expression member.",
            "memberTarget": "Links an expression member to the component, configuration, or event it classifies.",
            "minimumValue": "Records the minimum numeric value of a range observation result.",
            "notationGrammar": "Identifies the versioned grammar used to parse a classification expression.",
            "notationLiteral": "Preserves a complete classification expression exactly as supplied by its source.",
            "numericValue": "Records the numeric value of a quantity observation result.",
            "assessmentStatus": "Distinguishes detection, non-detection, indeterminacy, non-observation, and non-applicability.",
            "assessmentFeatureOfInterest": "Identifies the target considered by an observation assessment without claiming that an observation occurred.",
            "assessmentProperty": "Identifies the property considered by an observation assessment.",
            "assessmentProcedure": "Identifies the procedure attempted, planned, or assessed for applicability.",
            "assessmentAgent": "Identifies the agent responsible for an observation assessment record.",
            "assessmentSensor": "Identifies the sensor used or considered by an observation assessment.",
            "assessmentResult": "Links an observation assessment to its structured result when one exists.",
            "assessmentTime": "Records when the observation result or non-observation assessment was produced.",
            "observableProperty": "Identifies a property that a classification criterion expects to be observed.",
            "assessmentPart": "Identifies the part or component considered by an assessment without claiming that an observation occurred.",
            "parseStatus": "Identifies whether expression structure is merely tokenized or expert interpreted.",
            "performanceEvent": "Links a sounding realization or configured target to its performance event.",
            "protocol": "Links a protocol application to the authoritative external or community protocol resource.",
            "protocolApplication": "Links a governed resource or use decision to an applicable protocol record.",
            "protocolType": "Identifies the externally governed type of a cultural protocol without locally imitating it.",
            "protocolStatus": "Identifies the controlled lifecycle status of a protocol application.",
            "protocolResolutionStatus": "Records whether the referenced protocol was resolved and integrity-verified for this application.",
            "protocolIntegritySha256": "Records the lowercase SHA-256 digest used to verify the resolved protocol representation.",
            "integrityVerificationMethod": "Distinguishes locally recomputed SHA-256 verification from an identified external attestation or no verification.",
            "integrityAttestation": "Links to a public-safe external attestation when protocol integrity was not recomputed from a bundled artifact.",
            "protocolArtifactPath": "Records the safe dataset-relative path of a bundled protocol representation whose SHA-256 digest was recomputed.",
            "realizesInstrumentConcept": "Links a physical or configured target to an instrument concept it realizes in context.",
            "resultKind": "Records whether an observation result is categorical, literal, quantitative, or a range.",
            "reviewDecision": "Links a review event to the durable decision entity it generated.",
            "sequenceIndex": "Records the one-based order of a member in a classification expression.",
            "sharedSuffixNotation": "Preserves suffix notation explicitly documented as applying to several expression members.",
            "supportsClassification": "Links a criterion to a classification concept that it can support under its documented inference logic.",
            "targetKind": "Identifies the controlled kind of an organological target.",
            "targetResource": "Identifies a resource governed by a protocol application or use decision.",
            "tolerance": "Records the stated tolerance associated with a quantitative result.",
            "uncertainty": "Records measurement or observational uncertainty without treating it as epistemic or cultural authority.",
            "unit": "Links a quantitative result to a unit resource, normally from QUDT.",
            "useAction": "Identifies an action such as display, index, export, train, or commercialize governed by a use decision.",
            "useAudience": "Identifies an audience to which a use decision applies.",
            "useDecision": "Identifies the granted, refused, withheld, or withdrawn state of a use decision.",
            "useDecisionStatus": "Identifies the controlled lifecycle status of a use decision record.",
            "legalBasis": "Links a use decision to a public-safe reference documenting the independently assessed legal basis.",
            "legalBasisStatus": "Records whether the legal basis is documented, not required, unknown, or blocking publication.",
            "legalBasisAssessedBy": "Identifies the agent responsible for the separately recorded legal-basis determination; it does not itself prove legal compliance.",
            "consentRecord": "Links a use decision to a public-safe authorization reference for any required individual consent.",
            "consentStatus": "Records whether required individual consent is documented, not required, unknown, withheld, or withdrawn.",
            "consentAssessedBy": "Identifies the agent responsible for the separately recorded consent determination; it does not itself prove valid consent.",
            "supersedesProtocolApplication": "Links a protocol application to the earlier application that it replaces.",
            "supersedesUseDecision": "Links a use decision to the earlier use decision that it replaces.",
            "usePurpose": "Identifies a purpose to which a use decision applies.",
            "usedAssessment": "Links a classification assignment to an observation assessment used as a premise, including an explicit non-observation or non-applicability assessment.",
            "usedObservation": "Links a classification assignment to an observation used as a premise.",
            "usedProcedure": "Identifies the procedure used by an observation or prescribed by a criterion.",
        }
    )
    property_definitions.update(
        {
            "contextMatchRequired": "States whether a projection policy requires supplied context to match every applicable scope constraint.",
            "decisionStatus": "Records whether a review decision is active, suspended, superseded, or otherwise lifecycle-limited.",
            "directAssertion": "States whether a projection policy may emit simplified direct RDF assertions.",
            "eligibleReviewerAuthority": "Records a reviewer-authority code eligible to satisfy a requirement or veto rule.",
            "eligibleStance": "Records a claim stance eligible for a projection policy.",
            "graphRole": "Records the intended role of the graph produced by a projection policy.",
            "includesSourceLayer": "States whether a projection policy includes preserved source statements.",
            "minimumIndependentReviewers": "States the minimum number of independent authorized reviewers required by a policy or review requirement.",
            "policyVersion": "Records the semantic version of a projection policy.",
            "qualityRule": "Links a quality finding to the deterministic rule that produced it.",
            "rationale": "Records the explanatory rationale supplied with a review decision.",
            "reinstatesDecision": "Links a review event to a suspended decision it explicitly restores.",
            "requiredReviewOutcome": "Records an outcome that can satisfy a projection-policy review requirement.",
            "reviewEffect": "Records whether a quality signal changes review state; automated OMARO findings use none.",
            "reviewMethod": "Records the method used to reach one review decision.",
            "reviewOutcome": "Records the non-collapsed outcome of one review event.",
            "reviewRequirement": "Links a projection policy to a declarative review requirement.",
            "reviewerAuthority": "Records the authority role under which a reviewer made a decision.",
            "supersedesDecision": "Links a review event to a decision it permanently supersedes.",
            "suspendsDecision": "Links a review event to a decision it temporarily suspends.",
            "targetAssertion": "Identifies the assertion evaluated by a finding or review event.",
            "underProjectionPolicy": "Links an assertion to a projection policy in which it may be evaluated.",
            "unknownScopeBehavior": "States whether a projection includes, excludes, or warns about assertions whose applicability is unresolved.",
            "validationDimension": "Records the referential, linguistic, community, historical, scholarly, ethical, or rights dimension addressed.",
            "vetoOutcome": "Records a review outcome that triggers a projection-policy veto rule.",
            "vetoRule": "Links a projection policy to a declarative veto rule.",
        }
    )
    property_definitions.update(
        {
            "audio": "Links a label profile to an evidenced audio resource.",
            "defaultScriptSubtag": "Records a registry-supported default script subtag without treating it as an observed script.",
            "displayPolicy": "Records how a contextualized label may be displayed.",
            "explicitScriptSubtag": "Records the explicit BCP 47 script subtag supplied with a label.",
            "extensionSubtag": "Records one BCP 47 extension subtag supplied with a label.",
            "hasCommonOrInheritedCharacters": "States whether a label contains Unicode Common or Inherited script characters.",
            "labelProfile": "Links an assertion-scoped lexical resource to its conservative linguistic profile.",
            "labelResource": "Links a label assertion or profile to its assertion-scoped SKOS-XL label resource.",
            "languageRegistry": "Identifies the versioned language registry used to validate a label tag.",
            "languageTagStatus": "Records the validation and canonicalization status of a submitted language tag.",
            "languageVariety": "Identifies an evidenced language variety associated with a label profile.",
            "normalizedForm": "Records the project-normalized lexical form while preserving the submitted form separately.",
            "observedScript": "Records a Unicode Script code observed in the characters of a label.",
            "primaryLanguageSubtag": "Records the primary language subtag parsed from a submitted language tag.",
            "privateUseSubtag": "Records one BCP 47 private-use subtag supplied with a label.",
            "pronunciation": "Records an evidenced textual pronunciation associated with a label profile.",
            "regionSubtag": "Records the region subtag parsed from a submitted language tag.",
            "scriptObservationMethod": "Records the versioned method used to observe Unicode Script values.",
            "scriptRegistry": "Identifies the versioned Unicode Script registry used by a label profile.",
            "searchPolicy": "Records whether and with what warning a contextualized label may be indexed.",
            "skosProjectionStatus": "Records whether a label assertion is projected to direct SKOS and SKOS-XL links.",
            "sourceLabelAssertion": "Links a label profile to the source-qualified label assertion from which it was derived.",
            "submittedLanguageTag": "Records the language tag exactly as supplied by the source.",
            "termRole": "Records an evidenced controlled lexical role such as endonym, exonym, or historical name.",
            "transcriptionSystem": "Identifies an evidenced transcription system used for a label.",
            "translationStatus": "Records the evidence status of a label as a translation or translingual form.",
            "transliterationSystem": "Identifies an evidenced transliteration system used for a label.",
            "variantSubtag": "Records one BCP 47 variant subtag supplied with a label.",
            "writingSystem": "Identifies an evidenced writing-system resource associated with a label profile.",
        }
    )
    all_property_names = base_property_names | set(property_names)
    assert property_definitions.keys() == all_property_names
    for property_name in sorted(all_property_names):
        property_uri = OMARO_NS[property_name]
        label = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", property_name).lower()
        definition = property_definitions[property_name]
        graph.add((property_uri, RDFS.label, Literal(label, lang="en")))
        graph.add((property_uri, RDFS.comment, Literal(definition, lang="en")))
        graph.add((property_uri, RDFS.isDefinedBy, ontology_uri))

    for category, codes in CONTROLLED_CODES.items():
        scheme = URIRef(f"{OMARO}vocabulary-{category}")
        graph.add((scheme, RDF.type, SKOS.ConceptScheme))
        graph.add(
            (
                scheme,
                SKOS.prefLabel,
                Literal(category.replace("-", " ") + " vocabulary", lang="en"),
            )
        )
        graph.add((scheme, RDFS.isDefinedBy, ontology_uri))
        for code in codes:
            term = _code(category, code)
            graph.add((term, RDF.type, SKOS.Concept))
            graph.add((term, SKOS.inScheme, scheme))
            graph.add((term, SKOS.notation, Literal(code)))
            graph.add(
                (term, SKOS.prefLabel, Literal(code.replace("-", " "), lang="en"))
            )
            graph.add((term, RDFS.isDefinedBy, ontology_uri))

    mapping_purpose_definitions = {
        "query-expansion": (
            "Suitability for expanding a retrieval query across the mapped "
            "concepts under the assertion's stated qualifications."
        ),
        "display-navigation": (
            "Suitability for presenting a human-readable navigation link between "
            "the mapped concepts under the assertion's stated qualifications."
        ),
        "data-transformation": (
            "Suitability as an input to an explicitly reviewed data transformation; "
            "the declaration does not guarantee a lossless conversion."
        ),
        "scholarly-comparison": (
            "Suitability for comparative research across the mapped concepts or "
            "classification systems under the assertion's stated qualifications."
        ),
    }
    mapping_purpose_scope_note = Literal(
        "A mapping-purpose declaration states intended operational suitability. "
        "It is not a licence, permission, cultural authorization, or substitute "
        "for an applicable OMARO use decision and protocol.",
        lang="en",
    )
    for code, definition in mapping_purpose_definitions.items():
        term = _code("mapping-purpose", code)
        graph.add((term, SKOS.definition, Literal(definition, lang="en")))
        graph.add((term, SKOS.scopeNote, mapping_purpose_scope_note))

    for resource in dataset.label_resources:
        node = URIRef(resource["uri"])
        graph.add((node, RDF.type, SKOSXL.Label))
        graph.add(
            (
                node,
                SKOSXL.literalForm,
                Literal(resource["literal_form"], lang=resource["language_tag"]),
            )
        )
        graph.add((node, OMARO_NS.normalizedForm, Literal(resource["normalized_form"])))
        graph.add(
            (
                node,
                OMARO_NS.languageRegistry,
                URIRef(resource["language_registry_uri"]),
            )
        )

    agent_types = {
        "person": PROV.Person,
        "organization": PROV.Organization,
        "software": PROV.SoftwareAgent,
        "community": PROV.Organization,
    }
    for agent in dataset.agents:
        node = URIRef(agent["uri"])
        graph.add((node, RDF.type, PROV.Agent))
        graph.add((node, RDF.type, agent_types[agent["agent_type"]]))
        graph.add((node, RDFS.label, Literal(agent["name"])))
        graph.add((node, SCHEMA.url, URIRef(agent["resource_uri"])))
    for source in dataset.source_records:
        node = URIRef(source["uri"])
        graph.add((node, RDF.type, PROV.Entity))
        graph.add((node, DCTERMS.title, Literal(source["title"], lang="en")))
        graph.add((node, DCTERMS.source, URIRef(source["resource_uri"])))
        graph.add((node, DCTERMS.license, URIRef(source["rights_uri"])))
        graph.add((node, PROV.wasAttributedTo, URIRef(source["publisher_agent_uri"])))
        graph.add(
            (
                node,
                PROV.generatedAtTime,
                Literal(source["retrieved_at"], datatype=XSD.dateTime),
            )
        )
        graph.add((node, OMARO_NS.sourceLayer, Literal(source["layer"])))
        graph.add((node, SKOS.inScheme, URIRef(source["scheme_uri"])))
    for scheme in dataset.concept_schemes:
        node = URIRef(scheme["uri"])
        graph.add((node, OMARO_NS.schemeType, Literal(scheme["scheme_type"])))
        graph.add((node, OMARO_NS.schemeStatus, Literal(scheme["status"])))
        graph.add((node, OMARO_NS.schemePerspective, URIRef(scheme["perspective_uri"])))
        graph.add((node, DCTERMS.description, Literal(scheme["scope_note"], lang="en")))
        graph.add((node, PROV.wasAttributedTo, URIRef(scheme["publisher_agent_uri"])))
        graph.add((node, DCTERMS.license, URIRef(scheme["rights_uri"])))
        if scheme["version"] is not None:
            graph.add((node, DCTERMS.hasVersion, Literal(scheme["version"])))
        if scheme["version_uri"] is not None:
            graph.add((node, DCTERMS.hasVersion, URIRef(scheme["version_uri"])))
        if scheme["source_record_uri"] is not None:
            graph.add((node, PROV.wasDerivedFrom, URIRef(scheme["source_record_uri"])))
        if scheme["governance_uri"] is not None:
            graph.add((node, OMARO_NS.governance, URIRef(scheme["governance_uri"])))
    for perspective in dataset.perspectives:
        node = URIRef(perspective["uri"])
        graph.add((node, RDF.type, OMARO_NS.Perspective))
        graph.add((node, RDFS.label, Literal(perspective["label"], lang="en")))
        graph.add(
            (node, DCTERMS.description, Literal(perspective["description"], lang="en"))
        )
        graph.add(
            (
                node,
                OMARO_NS.perspectiveType,
                _code("perspective-type", perspective["perspective_type"]),
            )
        )
        graph.add((node, OMARO_NS.heldBy, URIRef(perspective["holder_agent_uri"])))
        graph.add((node, OMARO_NS.assignmentStatus, Literal(perspective["status"])))
        for community_uri in perspective["represented_community_uris"]:
            graph.add((node, OMARO_NS.representsCommunity, URIRef(community_uri)))
        for authority_uri in perspective["authority_assignment_uris"]:
            graph.add((node, OMARO_NS.authorityAssignment, URIRef(authority_uri)))
        if perspective["valid_from"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.validFrom,
                    Literal(perspective["valid_from"], datatype=XSD.dateTime),
                )
            )
        if perspective["valid_until"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.validUntil,
                    Literal(perspective["valid_until"], datatype=XSD.dateTime),
                )
            )
    for scope in dataset.applicability_scopes:
        node = URIRef(scope["uri"])
        graph.add((node, RDF.type, OMARO_NS.ApplicabilityScope))
        graph.add((node, RDFS.label, Literal(scope["label"], lang="en")))
        graph.add((node, DCTERMS.description, Literal(scope["description"], lang="en")))
        graph.add((node, OMARO_NS.scopeMode, _code("scope-mode", scope["scope_mode"])))
        for field, predicate in (
            ("community_uris", OMARO_NS.appliesToCommunity),
            ("place_uris", OMARO_NS.appliesToPlace),
            ("period_uris", OMARO_NS.appliesToPeriod),
            ("usage_domain_uris", OMARO_NS.appliesToUsageDomain),
            ("playing_technique_uris", OMARO_NS.appliesToPlayingTechnique),
            (
                "instrument_configuration_uris",
                OMARO_NS.appliesToInstrumentConfiguration,
            ),
            ("language_variety_uris", OMARO_NS.appliesToLanguageVariety),
        ):
            for value in scope[field]:
                graph.add((node, predicate, URIRef(value)))
        if scope["temporal_start"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.temporalStart,
                    Literal(scope["temporal_start"], datatype=XSD.dateTime),
                )
            )
        if scope["temporal_end"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.temporalEnd,
                    Literal(scope["temporal_end"], datatype=XSD.dateTime),
                )
            )
        graph.add((node, PROV.wasAttributedTo, URIRef(scope["asserted_by_uri"])))
        if scope["perspective_uri"] is not None:
            graph.add((node, OMARO_NS.perspective, URIRef(scope["perspective_uri"])))
        if scope["source_record_uri"] is not None:
            graph.add((node, PROV.wasDerivedFrom, URIRef(scope["source_record_uri"])))
    for authority in dataset.authority_assignments:
        node = URIRef(authority["uri"])
        graph.add((node, RDF.type, OMARO_NS.AuthorityAssignment))
        graph.add((node, OMARO_NS.assignedBy, URIRef(authority["agent_uri"])))
        if authority["represented_community_uri"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.representsCommunity,
                    URIRef(authority["represented_community_uri"]),
                )
            )
        graph.add(
            (
                node,
                OMARO_NS.authorityRole,
                _code("authority-role", authority["authority_role"]),
            )
        )
        graph.add(
            (node, OMARO_NS.authorityBasis, URIRef(authority["authority_basis_uri"]))
        )
        graph.add(
            (
                node,
                OMARO_NS.validFrom,
                Literal(authority["valid_from"], datatype=XSD.dateTime),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.delegationPermitted,
                Literal(authority["delegation_permitted"]),
            )
        )
        graph.add((node, OMARO_NS.assignmentStatus, Literal(authority["status"])))
        graph.add((node, DCTERMS.rights, URIRef(authority["rights_uri"])))
        graph.add(
            (node, OMARO_NS.conferredBy, URIRef(authority["conferred_by_agent_uri"]))
        )
        if authority["valid_until"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.validUntil,
                    Literal(authority["valid_until"], datatype=XSD.dateTime),
                )
            )
        if authority["revocation_event_uri"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.revocationEvent,
                    URIRef(authority["revocation_event_uri"]),
                )
            )
            graph.add(
                (
                    node,
                    OMARO_NS.revocationEffect,
                    Literal(authority["revocation_effect"]),
                )
            )
        for subject_uri in authority["subject_matter_uris"]:
            graph.add((node, OMARO_NS.subjectMatter, URIRef(subject_uri)))
        for dimension in authority["covered_validation_dimensions"]:
            graph.add(
                (
                    node,
                    OMARO_NS.coveredValidationDimension,
                    _code("review-dimension", dimension),
                )
            )
        for action_uri in authority["covered_action_uris"]:
            graph.add((node, OMARO_NS.coveredAction, URIRef(action_uri)))
        _add_policy_and_scope_links(graph, node, authority)
        _add_evidence(graph, node, authority["uri"], authority["evidence"])
    for policy in dataset.projection_policies:
        node = URIRef(policy["uri"])
        graph.add((node, RDF.type, OMARO_NS.ProjectionPolicy))
        graph.add((node, RDFS.label, Literal(policy["label"], lang="en")))
        graph.add(
            (node, DCTERMS.description, Literal(policy["description"], lang="en"))
        )
        graph.add((node, OMARO_NS.graphRole, Literal(policy["graph_role"])))
        graph.add((node, OMARO_NS.directAssertion, Literal(policy["direct_assertion"])))
        graph.add(
            (
                node,
                OMARO_NS.contextMatchRequired,
                Literal(policy["context_match_required"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.unknownScopeBehavior,
                Literal(policy["unknown_scope_behavior"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.includesSourceLayer,
                Literal(policy["includes_source_layer"]),
            )
        )
        graph.add((node, OMARO_NS.policyVersion, Literal(policy["policy_version"])))
        for stance in policy["eligible_stances"]:
            graph.add((node, OMARO_NS.eligibleStance, _code("stance", stance)))
        graph.add(
            (
                node,
                OMARO_NS.minimumIndependentReviewers,
                Literal(policy["minimum_independent_reviewers"]),
            )
        )
        for requirement in policy["review_requirements"]:
            requirement_uri = URIRef(
                assertion_uri(
                    "review-requirement", node.toPython(), canonical_json(requirement)
                )
            )
            graph.add((node, OMARO_NS.reviewRequirement, requirement_uri))
            graph.add((requirement_uri, RDF.type, OMARO_NS.ReviewRequirement))
            graph.add(
                (
                    requirement_uri,
                    OMARO_NS.validationDimension,
                    _code("review-dimension", requirement["validation_dimension"]),
                )
            )
            graph.add(
                (
                    requirement_uri,
                    OMARO_NS.minimumIndependentReviewers,
                    Literal(requirement["minimum_independent_reviewers"]),
                )
            )
            for authority in requirement["reviewer_authorities"]:
                graph.add(
                    (
                        requirement_uri,
                        OMARO_NS.eligibleReviewerAuthority,
                        _code("reviewer-authority", authority),
                    )
                )
            for outcome in requirement["outcomes"]:
                graph.add(
                    (
                        requirement_uri,
                        OMARO_NS.requiredReviewOutcome,
                        _code("review-outcome", outcome),
                    )
                )
        for rule in policy["veto_rules"]:
            rule_uri = URIRef(
                assertion_uri("veto-rule", node.toPython(), canonical_json(rule))
            )
            graph.add((node, OMARO_NS.vetoRule, rule_uri))
            graph.add((rule_uri, RDF.type, OMARO_NS.VetoRule))
            for dimension in rule["validation_dimensions"]:
                graph.add(
                    (
                        rule_uri,
                        OMARO_NS.validationDimension,
                        _code("review-dimension", dimension),
                    )
                )
            for authority in rule["reviewer_authorities"]:
                graph.add(
                    (
                        rule_uri,
                        OMARO_NS.eligibleReviewerAuthority,
                        _code("reviewer-authority", authority),
                    )
                )
            for outcome in rule["outcomes"]:
                graph.add(
                    (rule_uri, OMARO_NS.vetoOutcome, _code("review-outcome", outcome))
                )
    for status in dataset.review_statuses:
        node = URIRef(status["uri"])
        graph.add((node, RDF.type, OMARO_NS.ReviewStatus))
        graph.add((node, SKOS.notation, Literal(status["code"])))
        graph.add((node, SKOS.prefLabel, Literal(status["label"], lang="en")))
        graph.add((node, SKOS.definition, Literal(status["description"], lang="en")))
    for registry in dataset.language_registries:
        node = URIRef(registry["uri"])
        graph.add((node, RDF.type, PROV.Entity))
        graph.add((node, DCTERMS.title, Literal(registry["registry_type"], lang="en")))
        graph.add((node, DCTERMS.source, URIRef(registry["source_uri"])))
        graph.add(
            (node, DCTERMS.issued, Literal(registry["file_date"], datatype=XSD.date))
        )
        graph.add((node, DCTERMS.conformsTo, URIRef(registry["profile_uri"])))
    for registry in dataset.script_registries:
        node = URIRef(registry["uri"])
        graph.add((node, RDF.type, PROV.Entity))
        graph.add((node, DCTERMS.title, Literal(registry["registry_type"], lang="en")))
        graph.add((node, DCTERMS.hasVersion, Literal(registry["unicode_version"])))
        for source_uri in registry["source_uris"]:
            graph.add((node, DCTERMS.source, URIRef(source_uri)))
        graph.add((node, DCTERMS.conformsTo, URIRef(registry["profile_uri"])))
    for profile in dataset.label_profiles:
        node = URIRef(profile["uri"])
        resource = URIRef(profile["label_resource_uri"])
        graph.add((node, RDF.type, OMARO_NS.LabelProfile))
        graph.add((resource, OMARO_NS.labelProfile, node))
        graph.add((node, OMARO_NS.labelResource, resource))
        graph.add(
            (
                node,
                OMARO_NS.sourceLabelAssertion,
                URIRef(profile["source_label_assertion_uri"]),
            )
        )
        graph.add((node, DCTERMS.language, Literal(profile["language_tag"])))
        for field, predicate in (
            ("primary_language_subtag", OMARO_NS.primaryLanguageSubtag),
            ("explicit_script_subtag", OMARO_NS.explicitScriptSubtag),
            ("default_script_subtag", OMARO_NS.defaultScriptSubtag),
            ("region_subtag", OMARO_NS.regionSubtag),
            ("language_variety_uri", OMARO_NS.languageVariety),
            ("writing_system_uri", OMARO_NS.writingSystem),
            ("transliteration_system_uri", OMARO_NS.transliterationSystem),
            ("transcription_system_uri", OMARO_NS.transcriptionSystem),
        ):
            value = profile[field]
            if value is not None:
                obj = URIRef(value) if field.endswith("_uri") else Literal(value)
                graph.add((node, predicate, obj))
        for field, predicate in (
            ("variant_subtags", OMARO_NS.variantSubtag),
            ("extension_subtags", OMARO_NS.extensionSubtag),
            ("private_use_subtags", OMARO_NS.privateUseSubtag),
            ("observed_script_codes", OMARO_NS.observedScript),
            ("pronunciations", OMARO_NS.pronunciation),
            ("term_roles", OMARO_NS.termRole),
        ):
            for value in profile[field]:
                graph.add((node, predicate, Literal(value)))
        for value in profile["audio_uris"]:
            graph.add((node, OMARO_NS.audio, URIRef(value)))
        graph.add(
            (
                node,
                OMARO_NS.hasCommonOrInheritedCharacters,
                Literal(profile["has_common_or_inherited_characters"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.scriptObservationMethod,
                Literal(profile["script_observation_method"]),
            )
        )
        graph.add(
            (node, OMARO_NS.scriptRegistry, URIRef(profile["script_registry_uri"]))
        )
        graph.add(
            (node, OMARO_NS.translationStatus, Literal(profile["translation_status"]))
        )
        graph.add((node, OMARO_NS.displayPolicy, Literal(profile["display_policy"])))
        graph.add((node, OMARO_NS.searchPolicy, Literal(profile["search_policy"])))
        for context_key, predicate in (
            ("community_uris", OMARO_NS.appliesToCommunity),
            ("place_uris", OMARO_NS.appliesToPlace),
            ("period_uris", OMARO_NS.appliesToPeriod),
            ("usage_domain_uris", OMARO_NS.appliesToUsageDomain),
        ):
            for value in profile["applies_to"][context_key]:
                graph.add((node, predicate, URIRef(value)))
        graph.add((node, PROV.wasAttributedTo, URIRef(profile["asserted_by_uri"])))
        graph.add(
            (node, PROV.wasDerivedFrom, URIRef(profile["source_label_assertion_uri"]))
        )
        graph.add((node, OMARO_NS.sourceRecord, URIRef(profile["source_record_uri"])))
        graph.add(
            (node, OMARO_NS.assertionOrigin, Literal(profile["assertion_origin"]))
        )
        graph.add((node, OMARO_NS.reviewStatus, Literal(profile["review_status"])))
        graph.add(
            (
                node,
                OMARO_NS.reviewStatusResource,
                URIRef(profile["review_status_uri"]),
            )
        )
    for rule in dataset.quality_rules:
        node = URIRef(rule["uri"])
        graph.add((node, RDF.type, OMARO_NS.QualityRule))
        graph.add((node, SKOS.notation, Literal(rule["code"])))
        graph.add((node, DCTERMS.title, Literal(rule["title"], lang="en")))
        graph.add((node, DCTERMS.description, Literal(rule["description"], lang="en")))
        graph.add(
            (node, OMARO_NS.validationDimension, Literal(rule["validation_dimension"]))
        )
        graph.add((node, OMARO_NS.reviewEffect, Literal("none")))
    for finding in dataset.quality_findings:
        node = URIRef(finding["uri"])
        graph.add((node, RDF.type, OMARO_NS.QualityFinding))
        graph.add((node, OMARO_NS.qualityRule, URIRef(finding["rule_uri"])))
        graph.add(
            (node, OMARO_NS.targetAssertion, URIRef(finding["target_assertion_uri"]))
        )
        graph.add((node, DCTERMS.subject, URIRef(finding["concept_uri"])))
        graph.add((node, PROV.wasAssociatedWith, URIRef(finding["detected_by_uri"])))
        graph.add(
            (
                node,
                PROV.generatedAtTime,
                Literal(finding["detected_at"], datatype=XSD.dateTime),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.validationDimension,
                Literal(finding["validation_dimension"]),
            )
        )
        graph.add((node, OMARO_NS.reviewEffect, Literal("none")))

    target_classes = {
        "instrument-configuration": OMARO_NS.InstrumentConfiguration,
        "condition-state": OMARO_NS.ConditionState,
        "instrument-component": OMARO_NS.InstrumentComponent,
        "functional-module": OMARO_NS.FunctionalModule,
        "sounding-realization": OMARO_NS.SoundingRealization,
    }
    for target in dataset.organological_targets:
        node = URIRef(target["uri"])
        graph.add((node, RDF.type, OMARO_NS.OrganologicalTarget))
        if target["target_kind"] in target_classes:
            graph.add((node, RDF.type, target_classes[target["target_kind"]]))
        graph.add((node, RDFS.label, Literal(target["label"], lang="en")))
        graph.add(
            (node, OMARO_NS.targetKind, _code("target-type", target["target_kind"]))
        )
        for concept_uri in target["realizes_instrument_concept_uris"]:
            graph.add((node, OMARO_NS.realizesInstrumentConcept, URIRef(concept_uri)))
        for field, predicate in (
            ("configuration_of_uri", OMARO_NS.configurationOf),
            ("component_of_uri", OMARO_NS.componentOf),
            ("component_role_uri", OMARO_NS.componentRole),
            ("condition_state_of_uri", OMARO_NS.conditionStateOf),
            ("performance_event_uri", OMARO_NS.performanceEvent),
        ):
            if target[field] is not None:
                graph.add((node, predicate, URIRef(target[field])))
        for field, predicate in (
            ("has_component_uris", OMARO_NS.hasComponent),
            ("has_functional_module_uris", OMARO_NS.hasFunctionalModule),
            ("actual_playing_technique_uris", OMARO_NS.actualPlayingTechnique),
            ("intended_playing_technique_uris", OMARO_NS.intendedPlayingTechnique),
            ("protocol_application_uris", OMARO_NS.protocolApplication),
        ):
            for value in target[field]:
                graph.add((node, predicate, URIRef(value)))
        if target["valid_from"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.validFrom,
                    Literal(target["valid_from"], datatype=XSD.dateTime),
                )
            )
        if target["valid_until"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.validUntil,
                    Literal(target["valid_until"], datatype=XSD.dateTime),
                )
            )
        if target["source_record_uri"] is not None:
            graph.add((node, PROV.wasDerivedFrom, URIRef(target["source_record_uri"])))
        if target["generated_by_event_uri"] is not None:
            graph.add(
                (node, PROV.wasGeneratedBy, URIRef(target["generated_by_event_uri"]))
            )
        if target["ended_by_event_uri"] is not None:
            graph.add(
                (node, PROV.wasInvalidatedBy, URIRef(target["ended_by_event_uri"]))
            )
        if target["perspective_uri"] is not None:
            graph.add((node, OMARO_NS.perspective, URIRef(target["perspective_uri"])))
        graph.add((node, DCTERMS.rights, URIRef(target["rights_uri"])))
        for authority_uri in target["authority_assignment_uris"]:
            graph.add((node, OMARO_NS.authorityAssignment, URIRef(authority_uri)))
        _add_policy_and_scope_links(graph, node, target)

    for criterion in dataset.classification_criteria:
        node = URIRef(criterion["uri"])
        graph.add((node, RDF.type, OMARO_NS.ClassificationCriterion))
        graph.add((node, RDFS.label, Literal(criterion["label"], lang="en")))
        graph.add(
            (node, DCTERMS.description, Literal(criterion["description"], lang="en"))
        )
        graph.add(
            (
                node,
                OMARO_NS.criterionType,
                _code("criterion-type", criterion["criterion_type"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.classificationScheme,
                URIRef(criterion["classification_scheme_uri"]),
            )
        )
        for value in criterion["observable_property_uris"]:
            graph.add((node, OMARO_NS.observableProperty, URIRef(value)))
        for value in criterion["procedure_uris"]:
            graph.add((node, OMARO_NS.usedProcedure, URIRef(value)))
        for value in criterion["conclusion_classification_uris"]:
            graph.add((node, OMARO_NS.supportsClassification, URIRef(value)))
        if criterion["inference_logic_uri"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.inferenceLogic,
                    URIRef(criterion["inference_logic_uri"]),
                )
            )
        if criterion["scheme_version_uri"] is not None:
            graph.add(
                (node, OMARO_NS.schemeVersion, URIRef(criterion["scheme_version_uri"]))
            )
        if criterion["source_record_uri"] is not None:
            graph.add(
                (node, PROV.wasDerivedFrom, URIRef(criterion["source_record_uri"]))
            )
        graph.add((node, PROV.wasAttributedTo, URIRef(criterion["asserted_by_uri"])))
        graph.add((node, OMARO_NS.perspective, URIRef(criterion["perspective_uri"])))
        graph.add(
            (
                node,
                OMARO_NS.criterionStatus,
                _code("criterion-status", criterion["status"]),
            )
        )
        graph.add((node, DCTERMS.rights, URIRef(criterion["rights_uri"])))
        for authority_uri in criterion["authority_assignment_uris"]:
            graph.add((node, OMARO_NS.authorityAssignment, URIRef(authority_uri)))
        for protocol_uri in criterion["protocol_application_uris"]:
            graph.add((node, OMARO_NS.protocolApplication, URIRef(protocol_uri)))
        _add_policy_and_scope_links(graph, node, criterion)
        _add_evidence(graph, node, criterion["uri"], criterion["evidence"])

    for assessment in dataset.observation_assessments:
        node = URIRef(assessment["uri"])
        result_node = URIRef(assertion_uri("observation-result", assessment["uri"]))
        actual_observation = assessment["assessment_status"] in {
            "detected",
            "not-detected",
            "indeterminate",
        }
        graph.add((node, RDF.type, OMARO_NS.ObservationAssessment))
        graph.add(
            (
                node,
                OMARO_NS.assessmentFeatureOfInterest,
                URIRef(assessment["feature_of_interest_uri"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.assessmentProperty,
                URIRef(assessment["assessed_property_uri"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.assessmentProcedure,
                URIRef(assessment["assessment_procedure_uri"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.assessmentAgent,
                URIRef(assessment["assessment_agent_uri"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.assessmentStatus,
                _code("assessment-status", assessment["assessment_status"]),
            )
        )
        if assessment["assessed_part_uri"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.assessmentPart,
                    URIRef(assessment["assessed_part_uri"]),
                )
            )
        if assessment["assessment_sensor_uri"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.assessmentSensor,
                    URIRef(assessment["assessment_sensor_uri"]),
                )
            )
        graph.add(
            (
                node,
                OMARO_NS.assessmentTime,
                Literal(assessment["assessment_time"], datatype=XSD.dateTime),
            )
        )
        if actual_observation:
            graph.add((node, RDF.type, OMARO_NS.OrganologicalObservation))
            graph.add((node, RDF.type, SOSA.Observation))
            graph.add((node, RDF.type, CRMSCI.S27_Observation))
            graph.add(
                (
                    node,
                    SOSA.hasFeatureOfInterest,
                    URIRef(assessment["feature_of_interest_uri"]),
                )
            )
            graph.add(
                (
                    node,
                    SOSA.observedProperty,
                    URIRef(assessment["assessed_property_uri"]),
                )
            )
            graph.add(
                (
                    node,
                    SOSA.usedProcedure,
                    URIRef(assessment["assessment_procedure_uri"]),
                )
            )
            graph.add(
                (
                    node,
                    PROV.wasAssociatedWith,
                    URIRef(assessment["assessment_agent_uri"]),
                )
            )
            if assessment["assessment_sensor_uri"] is not None:
                graph.add(
                    (
                        node,
                        SOSA.madeBySensor,
                        URIRef(assessment["assessment_sensor_uri"]),
                    )
                )
            graph.add(
                (
                    node,
                    SOSA.resultTime,
                    Literal(assessment["assessment_time"], datatype=XSD.dateTime),
                )
            )
        if assessment["phenomenon_start"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.temporalStart,
                    Literal(assessment["phenomenon_start"], datatype=XSD.dateTime),
                )
            )
        if assessment["phenomenon_end"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.temporalEnd,
                    Literal(assessment["phenomenon_end"], datatype=XSD.dateTime),
                )
            )
        result = assessment["result"]
        if result is not None:
            graph.add((node, OMARO_NS.assessmentResult, result_node))
            if actual_observation:
                graph.add((node, SOSA.hasResult, result_node))
            graph.add((result_node, RDF.type, OMARO_NS.ObservationResult))
            graph.add(
                (
                    result_node,
                    OMARO_NS.resultKind,
                    _code("result-kind", result["kind"]),
                )
            )
            if result["kind"] == "resource":
                graph.add(
                    (
                        result_node,
                        OMARO_NS.categoricalValue,
                        URIRef(result["value_uri"]),
                    )
                )
            elif result["kind"] == "literal":
                value = Literal(
                    result["value"],
                    lang=result["language_tag"],
                    datatype=URIRef(result["datatype_uri"])
                    if result["datatype_uri"]
                    else None,
                )
                graph.add((result_node, RDF.value, value))
            elif result["kind"] == "quantity":
                graph.add(
                    (
                        result_node,
                        OMARO_NS.numericValue,
                        Literal(result["numeric_value"]),
                    )
                )
                graph.add((result_node, OMARO_NS.unit, URIRef(result["unit_uri"])))
                graph.add(
                    (result_node, QUDT.numericValue, Literal(result["numeric_value"]))
                )
                graph.add((result_node, QUDT.unit, URIRef(result["unit_uri"])))
                if result["uncertainty"] is not None:
                    graph.add(
                        (
                            result_node,
                            OMARO_NS.uncertainty,
                            Literal(result["uncertainty"]),
                        )
                    )
                if result["tolerance"] is not None:
                    graph.add(
                        (result_node, OMARO_NS.tolerance, Literal(result["tolerance"]))
                    )
            elif result["kind"] == "range":
                graph.add(
                    (
                        result_node,
                        OMARO_NS.minimumValue,
                        Literal(result["minimum_value"]),
                    )
                )
                graph.add(
                    (
                        result_node,
                        OMARO_NS.maximumValue,
                        Literal(result["maximum_value"]),
                    )
                )
                graph.add((result_node, OMARO_NS.unit, URIRef(result["unit_uri"])))
                if result["uncertainty"] is not None:
                    graph.add(
                        (
                            result_node,
                            OMARO_NS.uncertainty,
                            Literal(result["uncertainty"]),
                        )
                    )
        graph.add((node, OMARO_NS.perspective, URIRef(assessment["perspective_uri"])))
        graph.add(
            (
                node,
                OMARO_NS.reviewStatusResource,
                URIRef(assessment["review_status_uri"]),
            )
        )
        if assessment["source_record_uri"] is not None:
            graph.add(
                (node, PROV.wasDerivedFrom, URIRef(assessment["source_record_uri"]))
            )
        graph.add((node, DCTERMS.rights, URIRef(assessment["rights_uri"])))
        for authority_uri in assessment["authority_assignment_uris"]:
            graph.add((node, OMARO_NS.authorityAssignment, URIRef(authority_uri)))
        for protocol_uri in assessment["protocol_application_uris"]:
            graph.add((node, OMARO_NS.protocolApplication, URIRef(protocol_uri)))
        _add_policy_and_scope_links(graph, node, assessment)
        _add_evidence(
            graph,
            node,
            assessment["uri"],
            assessment["evidence"],
            usage_activity=node,
        )

    for expression in dataset.classification_expressions:
        node = URIRef(expression["uri"])
        graph.add((node, RDF.type, OMARO_NS.ClassificationExpression))
        graph.add(
            (node, OMARO_NS.notationLiteral, Literal(expression["notation_literal"]))
        )
        graph.add(
            (node, OMARO_NS.notationGrammar, URIRef(expression["notation_grammar_uri"]))
        )
        graph.add(
            (
                node,
                OMARO_NS.combinationOperator,
                _code("combination-operator", expression["combination_operator"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.parseStatus,
                _code("expression-parse-status", expression["parse_status"]),
            )
        )
        if expression["source_concept_uri"] is not None:
            graph.add(
                (
                    URIRef(expression["source_concept_uri"]),
                    OMARO_NS.classificationExpression,
                    node,
                )
            )
        if expression["expression_scheme_version_uri"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.schemeVersion,
                    URIRef(expression["expression_scheme_version_uri"]),
                )
            )
        if expression["shared_suffix_notation"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.sharedSuffixNotation,
                    Literal(expression["shared_suffix_notation"]),
                )
            )
        for member in expression["members"]:
            member_node = URIRef(
                assertion_uri(
                    "classification-expression-member",
                    expression["uri"],
                    str(member["sequence_index"]),
                )
            )
            graph.add((node, OMARO_NS.hasExpressionMember, member_node))
            graph.add((member_node, RDF.type, OMARO_NS.ClassificationExpressionMember))
            graph.add(
                (member_node, OMARO_NS.sequenceIndex, Literal(member["sequence_index"]))
            )
            graph.add(
                (
                    member_node,
                    OMARO_NS.memberNotation,
                    Literal(member["member_notation"]),
                )
            )
            for field, predicate in (
                ("classification_uri", OMARO_NS.memberClassification),
                ("member_assertion_uri", OMARO_NS.memberAssertion),
                ("member_target_uri", OMARO_NS.memberTarget),
                ("component_role_uri", OMARO_NS.componentRole),
            ):
                if member[field] is not None:
                    graph.add((member_node, predicate, URIRef(member[field])))
            if member["local_suffix_notation"] is not None:
                graph.add(
                    (
                        member_node,
                        OMARO_NS.localSuffixNotation,
                        Literal(member["local_suffix_notation"]),
                    )
                )
        graph.add((node, OMARO_NS.perspective, URIRef(expression["perspective_uri"])))
        graph.add((node, PROV.wasDerivedFrom, URIRef(expression["source_record_uri"])))
        graph.add((node, DCTERMS.rights, URIRef(expression["rights_uri"])))
        for authority_uri in expression["authority_assignment_uris"]:
            graph.add((node, OMARO_NS.authorityAssignment, URIRef(authority_uri)))
        for protocol_uri in expression["protocol_application_uris"]:
            graph.add((node, OMARO_NS.protocolApplication, URIRef(protocol_uri)))
        _add_policy_and_scope_links(graph, node, expression)
        _add_evidence(graph, node, expression["uri"], expression["evidence"])

    for protocol in dataset.protocol_applications:
        node = URIRef(protocol["uri"])
        graph.add((node, RDF.type, OMARO_NS.ProtocolApplication))
        graph.add((node, OMARO_NS.protocol, URIRef(protocol["protocol_uri"])))
        graph.add((node, OMARO_NS.protocolType, URIRef(protocol["protocol_type_uri"])))
        graph.add((node, OMARO_NS.issuedBy, URIRef(protocol["issued_by_agent_uri"])))
        graph.add((node, OMARO_NS.appliedBy, URIRef(protocol["applied_by_agent_uri"])))
        graph.add(
            (
                node,
                OMARO_NS.enforcementMode,
                _code("protocol-enforcement", protocol["enforcement_mode"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.protocolStatus,
                _code("protocol-status", protocol["status"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.protocolResolutionStatus,
                _code("protocol-resolution", protocol["resolution_status"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.integrityVerificationMethod,
                _code(
                    "protocol-integrity-method",
                    protocol["integrity_verification_method"],
                ),
            )
        )
        if protocol["protocol_artifact_path"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.protocolArtifactPath,
                    Literal(protocol["protocol_artifact_path"]),
                )
            )
        if protocol["integrity_attestation_uri"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.integrityAttestation,
                    URIRef(protocol["integrity_attestation_uri"]),
                )
            )
        if protocol["protocol_integrity_sha256"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.protocolIntegritySha256,
                    Literal(protocol["protocol_integrity_sha256"]),
                )
            )
        for value in protocol["target_resource_uris"]:
            graph.add((node, OMARO_NS.targetResource, URIRef(value)))
        for value in protocol["represented_community_uris"]:
            graph.add((node, OMARO_NS.representsCommunity, URIRef(value)))
        for value in protocol["authority_assignment_uris"]:
            graph.add((node, OMARO_NS.authorityAssignment, URIRef(value)))
        if protocol["source_record_uri"] is not None:
            graph.add(
                (node, PROV.wasDerivedFrom, URIRef(protocol["source_record_uri"]))
            )
        graph.add(
            (
                node,
                OMARO_NS.validFrom,
                Literal(protocol["valid_from"], datatype=XSD.dateTime),
            )
        )
        if protocol["valid_until"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.validUntil,
                    Literal(protocol["valid_until"], datatype=XSD.dateTime),
                )
            )
        if protocol["supersedes_uri"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.supersedesProtocolApplication,
                    URIRef(protocol["supersedes_uri"]),
                )
            )
        graph.add(
            (
                node,
                PROV.generatedAtTime,
                Literal(protocol["retrieved_at"], datatype=XSD.dateTime),
            )
        )
        _add_policy_and_scope_links(graph, node, protocol)

    for decision in dataset.use_decisions:
        node = URIRef(decision["uri"])
        graph.add((node, RDF.type, OMARO_NS.UseDecision))
        graph.add(
            (node, OMARO_NS.useDecision, _code("use-decision", decision["decision"]))
        )
        graph.add(
            (
                node,
                OMARO_NS.useDecisionStatus,
                _code("use-decision-status", decision["status"]),
            )
        )
        graph.add((node, OMARO_NS.decidedBy, URIRef(decision["decided_by_agent_uri"])))
        graph.add(
            (node, OMARO_NS.decisionMethod, URIRef(decision["decision_method_uri"]))
        )
        graph.add(
            (
                node,
                PROV.generatedAtTime,
                Literal(decision["decided_at"], datatype=XSD.dateTime),
            )
        )
        for field, predicate in (
            ("target_resource_uris", OMARO_NS.targetResource),
            ("action_uris", OMARO_NS.useAction),
            ("purpose_uris", OMARO_NS.usePurpose),
            ("audience_uris", OMARO_NS.useAudience),
            ("represented_community_uris", OMARO_NS.representsCommunity),
            ("authority_assignment_uris", OMARO_NS.authorityAssignment),
            ("protocol_application_uris", OMARO_NS.protocolApplication),
            ("legal_basis_uris", OMARO_NS.legalBasis),
            ("consent_record_uris", OMARO_NS.consentRecord),
        ):
            for value in decision[field]:
                graph.add((node, predicate, URIRef(value)))
        graph.add(
            (
                node,
                OMARO_NS.legalBasisStatus,
                _code("legal-basis-status", decision["legal_basis_status"]),
            )
        )
        graph.add(
            (
                node,
                OMARO_NS.consentStatus,
                _code("consent-status", decision["consent_status"]),
            )
        )
        if decision["legal_basis_assessed_by_agent_uri"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.legalBasisAssessedBy,
                    URIRef(decision["legal_basis_assessed_by_agent_uri"]),
                )
            )
        if decision["consent_assessed_by_agent_uri"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.consentAssessedBy,
                    URIRef(decision["consent_assessed_by_agent_uri"]),
                )
            )
        if decision["valid_until"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.validUntil,
                    Literal(decision["valid_until"], datatype=XSD.dateTime),
                )
            )
        if decision["supersedes_decision_uri"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.supersedesUseDecision,
                    URIRef(decision["supersedes_decision_uri"]),
                )
            )
        if decision["public_evidence_uri"] is not None:
            graph.add((node, DCTERMS.source, URIRef(decision["public_evidence_uri"])))
        if decision["public_summary"] is not None:
            graph.add((node, RDFS.comment, Literal(decision["public_summary"])))
        _add_policy_and_scope_links(graph, node, decision)

    for event in dataset.review_events:
        event_node = URIRef(event["uri"])
        decision_node = URIRef(event["decision_uri"])
        graph.add((event_node, RDF.type, OMARO_NS.ReviewEvent))
        graph.add((decision_node, RDF.type, OMARO_NS.ReviewDecision))
        graph.add((event_node, PROV.generated, decision_node))
        graph.add((decision_node, PROV.wasGeneratedBy, event_node))
        graph.add((event_node, OMARO_NS.reviewDecision, decision_node))
        graph.add((event_node, PROV.used, URIRef(event["target_assertion_uri"])))
        graph.add(
            (
                decision_node,
                OMARO_NS.targetAssertion,
                URIRef(event["target_assertion_uri"]),
            )
        )
        graph.add(
            (event_node, PROV.wasAssociatedWith, URIRef(event["reviewer_agent_uri"]))
        )
        graph.add(
            (
                event_node,
                PROV.endedAtTime,
                Literal(event["reviewed_at"], datatype=XSD.dateTime),
            )
        )
        graph.add(
            (
                event_node,
                OMARO_NS.reviewerAuthority,
                _code("reviewer-authority", event["reviewer_authority"]),
            )
        )
        graph.add(
            (
                event_node,
                OMARO_NS.reviewMethod,
                _code("review-method", event["review_method"]),
            )
        )
        graph.add(
            (
                decision_node,
                OMARO_NS.validationDimension,
                _code("review-dimension", event["validation_dimension"]),
            )
        )
        graph.add(
            (
                decision_node,
                OMARO_NS.reviewOutcome,
                _code("review-outcome", event["outcome"]),
            )
        )
        graph.add(
            (decision_node, OMARO_NS.perspective, URIRef(event["perspective_uri"]))
        )
        graph.add((decision_node, OMARO_NS.rationale, Literal(event["rationale"])))
        graph.add((decision_node, DCTERMS.rights, URIRef(event["rights_uri"])))
        graph.add(
            (
                decision_node,
                OMARO_NS.decisionStatus,
                _code("decision-status", event["decision_status"]),
            )
        )
        for authority_uri in event["authority_assignment_uris"]:
            graph.add((event_node, OMARO_NS.authorityAssignment, URIRef(authority_uri)))
        if event["valid_until"] is not None:
            graph.add(
                (
                    decision_node,
                    OMARO_NS.validUntil,
                    Literal(event["valid_until"], datatype=XSD.dateTime),
                )
            )
        if event["supersedes_decision_uri"] is not None:
            graph.add(
                (
                    decision_node,
                    OMARO_NS.supersedesDecision,
                    URIRef(event["supersedes_decision_uri"]),
                )
            )
        if event["suspends_decision_uri"] is not None:
            graph.add(
                (
                    decision_node,
                    OMARO_NS.suspendsDecision,
                    URIRef(event["suspends_decision_uri"]),
                )
            )
        if event["reinstates_decision_uri"] is not None:
            graph.add(
                (
                    decision_node,
                    OMARO_NS.reinstatesDecision,
                    URIRef(event["reinstates_decision_uri"]),
                )
            )
        for community_uri in event["represented_community_uris"]:
            graph.add(
                (decision_node, OMARO_NS.representsCommunity, URIRef(community_uri))
            )
        _add_policy_and_scope_links(graph, decision_node, event)
        _add_evidence(
            graph,
            decision_node,
            event["decision_uri"],
            event["evidence"],
            usage_activity=event_node,
        )

    for assertion_type, assertions in (
        (OMARO_NS.LabelAssertion, dataset.label_assertions),
        (OMARO_NS.NoteAssertion, dataset.note_assertions),
    ):
        for assertion in assertions:
            node = URIRef(assertion["uri"])
            literal = Literal(assertion["literal_form"], lang=assertion["language_tag"])
            graph.add((node, RDF.type, assertion_type))
            graph.add((node, RDF.subject, URIRef(assertion["concept_uri"])))
            graph.add((node, RDF.predicate, URIRef(assertion["predicate_uri"])))
            graph.add((node, RDF.object, literal))
            graph.add(
                (node, OMARO_NS.normalizedForm, Literal(assertion["normalized_form"]))
            )
            graph.add(
                (
                    node,
                    OMARO_NS.submittedLanguageTag,
                    Literal(assertion["submitted_language_tag"]),
                )
            )
            graph.add(
                (
                    node,
                    OMARO_NS.languageTagStatus,
                    Literal(assertion["language_tag_status"]),
                )
            )
            graph.add(
                (
                    node,
                    OMARO_NS.languageRegistry,
                    URIRef(assertion["language_registry_uri"]),
                )
            )
            graph.add(
                (node, PROV.wasAttributedTo, URIRef(assertion["asserted_by_uri"]))
            )
            graph.add(
                (node, OMARO_NS.sourceRecord, URIRef(assertion["source_record_uri"]))
            )
            graph.add((node, DCTERMS.source, URIRef(assertion["source_uri"])))
            graph.add(
                (
                    node,
                    PROV.wasDerivedFrom,
                    URIRef(assertion["source_record_uri"]),
                )
            )
            graph.add(
                (
                    node,
                    OMARO_NS.assertionOrigin,
                    Literal(assertion["assertion_origin"]),
                )
            )
            graph.add(
                (node, OMARO_NS.reviewStatus, Literal(assertion["review_status"]))
            )
            graph.add(
                (
                    node,
                    OMARO_NS.reviewStatusResource,
                    URIRef(assertion["review_status_uri"]),
                )
            )
            if assertion_type == OMARO_NS.LabelAssertion:
                label_resource = URIRef(assertion["label_resource_uri"])
                graph.add((node, OMARO_NS.labelResource, label_resource))
                graph.add(
                    (
                        node,
                        OMARO_NS.skosProjectionStatus,
                        Literal(assertion["skos_projection_status"]),
                    )
                )
                if assertion["skos_projection_status"] == "projected":
                    simple_predicate = URIRef(assertion["predicate_uri"])
                    xl_predicate = {
                        SKOS.prefLabel: SKOSXL.prefLabel,
                        SKOS.altLabel: SKOSXL.altLabel,
                        SKOS.hiddenLabel: SKOSXL.hiddenLabel,
                    }[simple_predicate]
                    concept = URIRef(assertion["concept_uri"])
                    graph.add((concept, simple_predicate, literal))
                    graph.add((concept, xl_predicate, label_resource))
    actual_assessment_uris = {
        assessment["uri"]
        for assessment in dataset.observation_assessments
        if assessment["assessment_status"]
        in {"detected", "not-detected", "indeterminate"}
    }
    for assertion in dataset.classification_assertions:
        node = URIRef(assertion["uri"])
        assignment = URIRef(assertion["assignment_uri"])
        target = URIRef(assertion["target_uri"])
        classification = URIRef(assertion["classification_uri"])
        predicate = URIRef(assertion["predicate_uri"])
        if dataset.is_directly_endorsed(assertion, ENDORSED_POLICY):
            graph.add((target, predicate, classification))
        graph.add((node, RDF.type, OMARO_NS.ClassificationAssertion))
        graph.add((node, RDF.subject, target))
        graph.add((node, RDF.predicate, predicate))
        graph.add((node, RDF.object, classification))
        graph.add((node, PROV.wasGeneratedBy, assignment))
        graph.add((node, OMARO_NS.classificationAssignment, assignment))
        graph.add((assignment, RDF.type, OMARO_NS.ClassificationAssignment))
        graph.add((assignment, PROV.generated, node))
        graph.add((assignment, OMARO_NS.generatedAssertion, node))
        graph.add((assignment, CRM.P41_classified, target))
        graph.add((assignment, CRM.P42_assigned, classification))
        graph.add(
            (assignment, CRM.P14_carried_out_by, URIRef(assertion["assigned_by_uri"]))
        )
        graph.add(
            (assignment, PROV.wasAssociatedWith, URIRef(assertion["assigned_by_uri"]))
        )
        graph.add(
            (assignment, OMARO_NS.assignedBy, URIRef(assertion["assigned_by_uri"]))
        )
        method = URIRef(assertion["classification_method_uri"])
        graph.add((assignment, OMARO_NS.classificationMethod, method))
        graph.add((node, DCTERMS.source, URIRef(assertion["source_uri"])))
        if assertion["generated_by_uri"] is not None:
            graph.add(
                (
                    assignment,
                    PROV.wasAssociatedWith,
                    URIRef(assertion["generated_by_uri"]),
                )
            )
        graph.add((node, OMARO_NS.sourceRecord, URIRef(assertion["source_record_uri"])))
        graph.add((node, PROV.wasDerivedFrom, URIRef(assertion["source_record_uri"])))
        graph.add((assignment, PROV.used, URIRef(assertion["source_record_uri"])))
        graph.add(
            (node, OMARO_NS.targetType, _code("target-type", assertion["target_type"]))
        )
        graph.add(
            (
                node,
                OMARO_NS.classificationScheme,
                URIRef(assertion["classification_scheme_uri"]),
            )
        )
        graph.add((node, OMARO_NS.perspective, URIRef(assertion["perspective_uri"])))
        graph.add((node, OMARO_NS.stance, _code("stance", assertion["stance"])))
        if assertion["scheme_version_uri"] is not None:
            graph.add(
                (node, OMARO_NS.schemeVersion, URIRef(assertion["scheme_version_uri"]))
            )
        if assertion["source_predicate_uri"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.sourcePredicate,
                    URIRef(assertion["source_predicate_uri"]),
                )
            )
        for authority_uri in assertion["authority_assignment_uris"]:
            graph.add((node, OMARO_NS.authorityAssignment, URIRef(authority_uri)))
        if assertion["valid_from"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.validFrom,
                    Literal(assertion["valid_from"], datatype=XSD.dateTime),
                )
            )
        if assertion["valid_until"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.validUntil,
                    Literal(assertion["valid_until"], datatype=XSD.dateTime),
                )
            )
        for criterion_uri in assertion["criteria_uris"]:
            graph.add(
                (assignment, OMARO_NS.classificationCriterion, URIRef(criterion_uri))
            )
            graph.add((assignment, PROV.hadPlan, URIRef(criterion_uri)))
        for assessment_uri in assertion["assessment_uris"]:
            graph.add((assignment, OMARO_NS.usedAssessment, URIRef(assessment_uri)))
            if assessment_uri in actual_assessment_uris:
                graph.add(
                    (assignment, OMARO_NS.usedObservation, URIRef(assessment_uri))
                )
            graph.add((assignment, PROV.used, URIRef(assessment_uri)))
        if assertion["inference_logic_uri"] is not None:
            graph.add(
                (
                    assignment,
                    OMARO_NS.inferenceLogic,
                    URIRef(assertion["inference_logic_uri"]),
                )
            )
        if assertion["classification_expression_uri"] is not None:
            graph.add(
                (
                    assignment,
                    OMARO_NS.classificationExpression,
                    URIRef(assertion["classification_expression_uri"]),
                )
            )
        _add_policy_and_scope_links(graph, node, assertion)
        _add_evidence(
            graph,
            node,
            assertion["uri"],
            assertion["evidence"],
            usage_activity=assignment,
        )
        graph.add(
            (
                node,
                OMARO_NS.assertionOrigin,
                Literal(assertion["assertion_origin"]),
            )
        )
    for assertion in dataset.concept_relation_assertions:
        node = URIRef(assertion["uri"])
        subject = URIRef(assertion["subject_concept_uri"])
        predicate = URIRef(assertion["predicate_uri"])
        obj = URIRef(assertion["object_concept_uri"])
        if dataset.is_directly_endorsed(assertion, ENDORSED_POLICY):
            graph.add((subject, predicate, obj))
        graph.add((node, RDF.type, OMARO_NS.ConceptRelationAssertion))
        graph.add((node, RDF.subject, subject))
        graph.add((node, RDF.predicate, predicate))
        graph.add((node, RDF.object, obj))
        graph.add((node, PROV.wasAttributedTo, URIRef(assertion["assigned_by_uri"])))
        graph.add((node, OMARO_NS.assignedBy, URIRef(assertion["assigned_by_uri"])))
        graph.add((node, OMARO_NS.perspective, URIRef(assertion["perspective_uri"])))
        graph.add(
            (
                node,
                OMARO_NS.classificationMethod,
                URIRef(assertion["relation_method_uri"]),
            )
        )
        for purpose_uri in assertion["mapping_purpose_uris"]:
            graph.add((node, OMARO_NS.mappingPurpose, URIRef(purpose_uri)))
        graph.add((node, OMARO_NS.stance, _code("stance", assertion["stance"])))
        graph.add((node, OMARO_NS.sourceRecord, URIRef(assertion["source_record_uri"])))
        graph.add((node, PROV.wasDerivedFrom, URIRef(assertion["source_record_uri"])))
        graph.add(
            (node, OMARO_NS.assertionOrigin, Literal(assertion["assertion_origin"]))
        )
        if assertion["generated_by_uri"] is not None:
            graph.add(
                (node, PROV.wasAttributedTo, URIRef(assertion["generated_by_uri"]))
            )
        for authority_uri in assertion["authority_assignment_uris"]:
            graph.add((node, OMARO_NS.authorityAssignment, URIRef(authority_uri)))
        if assertion["valid_from"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.validFrom,
                    Literal(assertion["valid_from"], datatype=XSD.dateTime),
                )
            )
        if assertion["valid_until"] is not None:
            graph.add(
                (
                    node,
                    OMARO_NS.validUntil,
                    Literal(assertion["valid_until"], datatype=XSD.dateTime),
                )
            )
        _add_policy_and_scope_links(graph, node, assertion)
        _add_evidence(graph, node, assertion["uri"], assertion["evidence"])
    return graph


def ontology_schema_graph(dataset: Dataset, project_graph: Graph) -> Graph:
    """Return the compact ontology vocabulary without reference-dataset instances."""
    graph = Graph()
    _bind_namespaces(graph)
    ontology_uri = URIRef(dataset.metadata["ontology_uri"])
    ontology_version_uri = URIRef(dataset.metadata["ontology_version_iri"])
    subjects = {ontology_uri, ontology_version_uri, CREATOR_URI}
    for ontology_type in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty):
        subjects.update(
            subject
            for subject in project_graph.subjects(RDF.type, ontology_type)
            if str(subject).startswith(OMARO)
        )
    mapping_purpose_scheme = URIRef(f"{OMARO}vocabulary-mapping-purpose")
    subjects.add(mapping_purpose_scheme)
    subjects.update(project_graph.subjects(SKOS.inScheme, mapping_purpose_scheme))
    for subject in subjects:
        for triple in project_graph.triples((subject, None, None)):
            graph.add(triple)
    return graph


def _jsonld_sorted(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _jsonld_sorted(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        normalized = [_jsonld_sorted(item) for item in value]
        return sorted(normalized, key=lambda item: canonical_json(item))
    return value


def _xml_element_key(element: ET.Element) -> tuple[Any, ...]:
    """Return a stable ordering key for an RDF/XML element."""
    return (
        element.tag,
        tuple(sorted(element.attrib.items())),
        (element.text or "").strip(),
    )


def _deterministic_rdf_xml(serialized: str) -> str:
    """Normalize RDF/XML subject and predicate ordering across processes."""
    namespaces = list(ET.iterparse(io.StringIO(serialized), events=("start-ns",)))
    for _, (prefix, uri) in namespaces:
        ET.register_namespace(prefix, uri)
    root = ET.fromstring(serialized)
    root.text = None
    for description in root:
        description.text = None
        description.tail = None
        for predicate in description:
            predicate.tail = None
        description[:] = sorted(description, key=_xml_element_key)
    root[:] = sorted(root, key=_xml_element_key)
    normalized = ET.tostring(root, encoding="unicode")
    return ET.canonicalize(normalized) + "\n"


def _build_rdf(dataset: Dataset, output: Path, schema_dir: Path) -> dict[str, int]:
    rdf_dir = output / "rdf"
    rdf_dir.mkdir(parents=True, exist_ok=True)
    graph = dataset_graph(dataset)
    turtle = graph.serialize(format="turtle")
    (rdf_dir / "omaro.ttl").write_text(turtle, encoding="utf-8", newline="\n")
    rdf_xml = _deterministic_rdf_xml(graph.serialize(format="xml"))
    (rdf_dir / "omaro.rdf").write_text(rdf_xml, encoding="utf-8", newline="\n")
    raw_jsonld = graph.serialize(format="json-ld", auto_compact=True)
    normalized_jsonld = _jsonld_sorted(json.loads(raw_jsonld))
    (rdf_dir / "omaro.jsonld").write_text(
        canonical_json(normalized_jsonld, indent=2), encoding="utf-8", newline="\n"
    )
    ontology_graph = ontology_schema_graph(dataset, graph)
    ontology_dir = output / "ontology" / dataset.metadata["schema_version"]
    ontology_dir.mkdir(parents=True)
    (ontology_dir / "omaro.ttl").write_text(
        ontology_graph.serialize(format="turtle"), encoding="utf-8", newline="\n"
    )
    (ontology_dir / "omaro.rdf").write_text(
        _deterministic_rdf_xml(ontology_graph.serialize(format="xml")),
        encoding="utf-8",
        newline="\n",
    )
    ontology_jsonld = _jsonld_sorted(
        json.loads(ontology_graph.serialize(format="json-ld", auto_compact=True))
    )
    (ontology_dir / "omaro.jsonld").write_text(
        canonical_json(ontology_jsonld, indent=2), encoding="utf-8", newline="\n"
    )
    source_graph = source_snapshot_graph(dataset)
    (rdf_dir / "mimo-source-snapshot.ttl").write_text(
        source_graph.serialize(format="turtle"), encoding="utf-8", newline="\n"
    )
    if any(graph.triples((None, URIRef(EXACT_MATCH), None))):
        raise ValidationError(
            "project RDF graph must not expose MIMO exactMatch as an unqualified assertion"
        )
    conforms, _, report = shacl_validate(
        graph,
        shacl_graph=str(schema_dir / "dataset.shacl.ttl"),
        inference="none",
        abort_on_first=False,
    )
    if not conforms:
        raise ValidationError(f"SHACL validation failed:\n{report}")
    return {
        "triples": len(graph),
        "ontology_triples": len(ontology_graph),
        "source_snapshot_triples": len(source_graph),
    }


def _classification_instrument_rows(dataset: Dataset) -> list[dict[str, Any]]:
    concepts = dataset.concepts_by_uri
    preferred_en = {
        row["concept_uri"]: row["label"]
        for row in dataset.labels
        if row["language"] == "en" and row["label_type"] == "preferred"
    }
    return [
        {
            "assertion_uri": assertion["uri"],
            "assignment_uri": assertion["assignment_uri"],
            "classification_uri": assertion["classification_uri"],
            "classification_notation": concepts[assertion["classification_uri"]].get(
                "notation", ""
            ),
            "classification_label_en": preferred_en.get(
                assertion["classification_uri"], ""
            ),
            "target_uri": assertion["target_uri"],
            "target_label_en": preferred_en.get(assertion["target_uri"], ""),
            "target_resolution_status": (
                concepts[assertion["target_uri"]]["resolution_status"]
                if assertion["target_uri"] in concepts
                else "external-target"
            ),
            "target_type": assertion["target_type"],
            "classification_scheme_uri": assertion["classification_scheme_uri"],
            "scheme_version_uri": assertion["scheme_version_uri"],
            "assertion_origin": assertion["assertion_origin"],
            "stance": assertion["stance"],
            "assigned_by_uri": assertion["assigned_by_uri"],
            "generated_by_uri": assertion["generated_by_uri"],
            "perspective_uri": assertion["perspective_uri"],
            "classification_method_uri": assertion["classification_method_uri"],
            "criteria_uris_json": json.dumps(
                assertion["criteria_uris"], sort_keys=True
            ),
            "assessment_uris_json": json.dumps(
                assertion["assessment_uris"], sort_keys=True
            ),
            "inference_logic_uri": assertion["inference_logic_uri"],
            "classification_expression_uri": assertion["classification_expression_uri"],
            "applicability_scope_uris_json": json.dumps(
                assertion["applicability_scope_uris"], sort_keys=True
            ),
            "evidence_json": json.dumps(
                assertion["evidence"], ensure_ascii=False, sort_keys=True
            ),
            "authority_assignment_uris_json": json.dumps(
                assertion["authority_assignment_uris"], sort_keys=True
            ),
            "valid_from": assertion["valid_from"],
            "valid_until": assertion["valid_until"],
            "projection_policy_uris_json": json.dumps(
                assertion["projection_policy_uris"], sort_keys=True
            ),
            "source_record_uri": assertion["source_record_uri"],
            "source_predicate_uri": assertion["source_predicate_uri"],
            "source_uri": assertion["source_uri"],
        }
        for assertion in sorted(
            dataset.classification_assertions,
            key=lambda row: (row["classification_uri"], row["target_uri"]),
        )
    ]


def _ancestor_rows(dataset: Dataset) -> list[tuple[str, str, int]]:
    parents: dict[str, list[str]] = defaultdict(list)
    for relation in dataset.source_relations:
        if relation["predicate_uri"] == BROADER:
            parents[relation["subject_uri"]].append(relation["object_uri"])

    memo: dict[str, dict[str, int]] = {}

    def ancestors(uri: str) -> dict[str, int]:
        if uri in memo:
            return memo[uri]
        result: dict[str, int] = {}
        for parent in sorted(parents[uri]):
            result[parent] = 1
            for ancestor, depth in ancestors(parent).items():
                candidate = depth + 1
                result[ancestor] = min(result.get(ancestor, candidate), candidate)
        memo[uri] = result
        return result

    return [
        (concept["uri"], ancestor, depth)
        for concept in sorted(dataset.concepts, key=lambda row: row["uri"])
        for ancestor, depth in sorted(ancestors(concept["uri"]).items())
    ]


def _build_sqlite(dataset: Dataset, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            PRAGMA user_version = 20200;
            CREATE TABLE schemes (
                uri TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                scheme_type TEXT NOT NULL,
                version TEXT,
                version_uri TEXT,
                publisher_agent_uri TEXT NOT NULL,
                perspective_uri TEXT NOT NULL,
                source_record_uri TEXT,
                governance_uri TEXT,
                rights_uri TEXT NOT NULL,
                status TEXT NOT NULL,
                scope_note TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE agents (
                uri TEXT PRIMARY KEY,
                agent_type TEXT NOT NULL CHECK(
                    agent_type IN ('person', 'organization', 'software', 'community')
                ),
                name TEXT NOT NULL,
                resource_uri TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE perspectives (
                uri TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                perspective_type TEXT NOT NULL,
                holder_agent_uri TEXT NOT NULL REFERENCES agents(uri),
                represented_community_uris_json TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                valid_from TEXT,
                valid_until TEXT,
                authority_assignment_uris_json TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE applicability_scopes (
                uri TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                scope_mode TEXT NOT NULL CHECK(scope_mode IN (
                    'source-silent', 'not-yet-investigated', 'known-unknown',
                    'intentionally-unscoped', 'not-applicable', 'specified',
                    'context-independent'
                )),
                description TEXT NOT NULL,
                community_uris_json TEXT NOT NULL,
                place_uris_json TEXT NOT NULL,
                period_uris_json TEXT NOT NULL,
                usage_domain_uris_json TEXT NOT NULL,
                playing_technique_uris_json TEXT NOT NULL,
                instrument_configuration_uris_json TEXT NOT NULL,
                language_variety_uris_json TEXT NOT NULL,
                temporal_start TEXT,
                temporal_end TEXT,
                asserted_by_uri TEXT NOT NULL REFERENCES agents(uri),
                perspective_uri TEXT REFERENCES perspectives(uri),
                source_record_uri TEXT
            ) WITHOUT ROWID;
            CREATE TABLE projection_policies (
                uri TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                description TEXT NOT NULL,
                graph_role TEXT NOT NULL,
                direct_assertion INTEGER NOT NULL,
                eligible_stances_json TEXT NOT NULL,
                review_requirements_json TEXT NOT NULL,
                minimum_independent_reviewers INTEGER NOT NULL,
                veto_rules_json TEXT NOT NULL,
                context_match_required INTEGER NOT NULL,
                unknown_scope_behavior TEXT NOT NULL,
                includes_source_layer INTEGER NOT NULL,
                policy_version TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE review_statuses (
                uri TEXT PRIMARY KEY,
                code TEXT NOT NULL UNIQUE CHECK(
                    code IN ('unreviewed', 'accepted', 'disputed', 'rejected', 'superseded')
                ),
                label TEXT NOT NULL,
                description TEXT NOT NULL,
                UNIQUE(code, uri)
            ) WITHOUT ROWID;
            CREATE TABLE language_registries (
                uri TEXT PRIMARY KEY,
                registry_type TEXT NOT NULL,
                file_date TEXT NOT NULL,
                source_uri TEXT NOT NULL,
                artifact_path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                profile_uri TEXT NOT NULL,
                normalization_overrides_json TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE script_registries (
                uri TEXT PRIMARY KEY,
                registry_type TEXT NOT NULL,
                unicode_version TEXT NOT NULL,
                source_uris_json TEXT NOT NULL,
                artifact_path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                profile_uri TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE quality_rules (
                uri TEXT PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                validation_dimension TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                assessment_method TEXT NOT NULL,
                review_effect TEXT NOT NULL CHECK(review_effect = 'none')
            ) WITHOUT ROWID;
            CREATE TABLE source_records (
                uri TEXT PRIMARY KEY,
                resource_uri TEXT NOT NULL,
                title TEXT NOT NULL,
                source_type TEXT NOT NULL,
                scheme_uri TEXT NOT NULL REFERENCES schemes(uri),
                publisher_agent_uri TEXT NOT NULL REFERENCES agents(uri),
                layer TEXT NOT NULL,
                rights_uri TEXT NOT NULL,
                retrieved_at TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE concepts (
                uri TEXT PRIMARY KEY,
                scheme_uri TEXT NOT NULL REFERENCES schemes(uri),
                kind TEXT NOT NULL CHECK(kind IN (
                    'classification', 'instrument', 'facet', 'community-category'
                )),
                local_id TEXT NOT NULL,
                mimo_id TEXT,
                notation TEXT,
                definition TEXT,
                created TEXT,
                resolution_status TEXT NOT NULL CHECK(resolution_status IN ('resolved', 'unresolved')),
                UNIQUE(scheme_uri, local_id),
                UNIQUE(scheme_uri, notation)
            ) WITHOUT ROWID;
            CREATE TABLE labels (
                concept_uri TEXT NOT NULL REFERENCES concepts(uri),
                language TEXT NOT NULL,
                submitted_language TEXT NOT NULL,
                label_type TEXT NOT NULL CHECK(label_type IN ('preferred', 'alternative', 'hidden')),
                label TEXT NOT NULL,
                PRIMARY KEY(concept_uri, language, label_type, label)
            ) WITHOUT ROWID;
            CREATE TABLE label_resources (
                uri TEXT PRIMARY KEY,
                literal_form TEXT NOT NULL,
                normalized_form TEXT NOT NULL,
                language_tag TEXT NOT NULL,
                language_registry_uri TEXT NOT NULL REFERENCES language_registries(uri)
            ) WITHOUT ROWID;
            CREATE TABLE label_assertions (
                uri TEXT PRIMARY KEY,
                concept_uri TEXT NOT NULL REFERENCES concepts(uri),
                predicate_uri TEXT NOT NULL,
                literal_form TEXT NOT NULL,
                normalized_form TEXT NOT NULL,
                language_tag TEXT NOT NULL,
                submitted_language_tag TEXT NOT NULL,
                language_tag_status TEXT NOT NULL,
                language_registry_uri TEXT NOT NULL REFERENCES language_registries(uri),
                label_resource_uri TEXT NOT NULL REFERENCES label_resources(uri),
                label_role TEXT NOT NULL CHECK(
                    label_role IN ('preferred', 'alternative', 'hidden')
                ),
                skos_projection_status TEXT NOT NULL CHECK(
                    skos_projection_status IN ('projected', 'suppressed-role-conflict')
                ),
                asserted_by_uri TEXT NOT NULL REFERENCES agents(uri),
                source_record_uri TEXT NOT NULL REFERENCES source_records(uri),
                source_uri TEXT NOT NULL,
                assertion_origin TEXT NOT NULL CHECK(assertion_origin = 'source-asserted'),
                review_status TEXT NOT NULL,
                review_status_uri TEXT NOT NULL,
                FOREIGN KEY(review_status, review_status_uri)
                    REFERENCES review_statuses(code, uri),
                UNIQUE(concept_uri, language_tag, label_role, literal_form)
            ) WITHOUT ROWID;
            CREATE TABLE label_profiles (
                uri TEXT PRIMARY KEY,
                label_resource_uri TEXT NOT NULL UNIQUE REFERENCES label_resources(uri),
                source_label_assertion_uri TEXT NOT NULL UNIQUE REFERENCES label_assertions(uri),
                language_tag TEXT NOT NULL,
                primary_language_subtag TEXT NOT NULL,
                explicit_script_subtag TEXT,
                default_script_subtag TEXT,
                region_subtag TEXT,
                variant_subtags_json TEXT NOT NULL,
                extension_subtags_json TEXT NOT NULL,
                private_use_subtags_json TEXT NOT NULL,
                language_variety_uri TEXT,
                writing_system_uri TEXT,
                observed_script_codes_json TEXT NOT NULL,
                has_common_or_inherited_characters INTEGER NOT NULL,
                script_observation_method TEXT NOT NULL,
                script_registry_uri TEXT NOT NULL REFERENCES script_registries(uri),
                transliteration_system_uri TEXT,
                transcription_system_uri TEXT,
                pronunciations_json TEXT NOT NULL,
                audio_uris_json TEXT NOT NULL,
                term_roles_json TEXT NOT NULL,
                translation_status TEXT NOT NULL,
                applies_to_json TEXT NOT NULL,
                display_policy TEXT NOT NULL,
                search_policy TEXT NOT NULL,
                asserted_by_uri TEXT NOT NULL REFERENCES agents(uri),
                source_record_uri TEXT NOT NULL REFERENCES source_records(uri),
                assertion_origin TEXT NOT NULL CHECK(assertion_origin = 'source-derived'),
                review_status TEXT NOT NULL,
                review_status_uri TEXT NOT NULL,
                FOREIGN KEY(review_status, review_status_uri)
                    REFERENCES review_statuses(code, uri)
            ) WITHOUT ROWID;
            CREATE TABLE note_assertions (
                uri TEXT PRIMARY KEY,
                concept_uri TEXT NOT NULL REFERENCES concepts(uri),
                predicate_uri TEXT NOT NULL,
                literal_form TEXT NOT NULL,
                normalized_form TEXT NOT NULL,
                language_tag TEXT NOT NULL,
                submitted_language_tag TEXT NOT NULL,
                language_tag_status TEXT NOT NULL,
                language_registry_uri TEXT NOT NULL REFERENCES language_registries(uri),
                asserted_by_uri TEXT NOT NULL REFERENCES agents(uri),
                source_record_uri TEXT NOT NULL REFERENCES source_records(uri),
                source_uri TEXT NOT NULL,
                assertion_origin TEXT NOT NULL CHECK(assertion_origin = 'source-asserted'),
                review_status TEXT NOT NULL,
                review_status_uri TEXT NOT NULL,
                FOREIGN KEY(review_status, review_status_uri)
                    REFERENCES review_statuses(code, uri),
                UNIQUE(concept_uri, predicate_uri, language_tag, literal_form)
            ) WITHOUT ROWID;
            CREATE TABLE source_relations (
                subject_uri TEXT NOT NULL REFERENCES concepts(uri),
                predicate_uri TEXT NOT NULL,
                object_uri TEXT NOT NULL REFERENCES concepts(uri),
                source_uri TEXT NOT NULL,
                PRIMARY KEY(subject_uri, predicate_uri, object_uri)
            ) WITHOUT ROWID;
            CREATE TABLE classification_assertions (
                uri TEXT PRIMARY KEY,
                target_uri TEXT NOT NULL,
                target_type TEXT NOT NULL,
                predicate_uri TEXT NOT NULL,
                classification_uri TEXT NOT NULL REFERENCES concepts(uri),
                classification_scheme_uri TEXT NOT NULL REFERENCES schemes(uri),
                scheme_version_uri TEXT,
                perspective_uri TEXT NOT NULL REFERENCES perspectives(uri),
                stance TEXT NOT NULL,
                applicability_scope_uris_json TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                authority_assignment_uris_json TEXT NOT NULL,
                valid_from TEXT,
                valid_until TEXT,
                projection_policy_uris_json TEXT NOT NULL,
                source_predicate_uri TEXT,
                source_uri TEXT NOT NULL,
                source_record_uri TEXT NOT NULL REFERENCES source_records(uri),
                assertion_origin TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE classification_assignments (
                uri TEXT PRIMARY KEY,
                assertion_uri TEXT NOT NULL UNIQUE
                    REFERENCES classification_assertions(uri),
                assigned_by_uri TEXT NOT NULL REFERENCES agents(uri),
                generated_by_uri TEXT REFERENCES agents(uri),
                classification_method_uri TEXT NOT NULL,
                criteria_uris_json TEXT NOT NULL,
                assessment_uris_json TEXT NOT NULL,
                inference_logic_uri TEXT,
                classification_expression_uri TEXT
            ) WITHOUT ROWID;
            CREATE TABLE concept_relation_assertions (
                uri TEXT PRIMARY KEY,
                subject_concept_uri TEXT NOT NULL REFERENCES concepts(uri),
                predicate_uri TEXT NOT NULL,
                object_concept_uri TEXT NOT NULL REFERENCES concepts(uri),
                assigned_by_uri TEXT NOT NULL REFERENCES agents(uri),
                generated_by_uri TEXT REFERENCES agents(uri),
                perspective_uri TEXT NOT NULL REFERENCES perspectives(uri),
                relation_method_uri TEXT NOT NULL,
                mapping_purpose_uris_json TEXT NOT NULL,
                stance TEXT NOT NULL,
                applicability_scope_uris_json TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                authority_assignment_uris_json TEXT NOT NULL,
                valid_from TEXT,
                valid_until TEXT,
                projection_policy_uris_json TEXT NOT NULL,
                source_record_uri TEXT NOT NULL REFERENCES source_records(uri),
                assertion_origin TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE quality_findings (
                uri TEXT PRIMARY KEY,
                rule_uri TEXT NOT NULL REFERENCES quality_rules(uri),
                rule_code TEXT NOT NULL,
                target_assertion_uri TEXT NOT NULL,
                concept_uri TEXT NOT NULL REFERENCES concepts(uri),
                detected_by_uri TEXT NOT NULL REFERENCES agents(uri),
                detected_at TEXT NOT NULL,
                assessment_method TEXT NOT NULL,
                validation_dimension TEXT NOT NULL,
                severity TEXT NOT NULL,
                review_effect TEXT NOT NULL CHECK(review_effect = 'none'),
                human_review_required INTEGER NOT NULL CHECK(human_review_required = 1),
                applies_to_json TEXT NOT NULL,
                evidence_json TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE review_events (
                uri TEXT PRIMARY KEY,
                reviewer_agent_uri TEXT NOT NULL REFERENCES agents(uri),
                reviewer_authority TEXT NOT NULL,
                authority_assignment_uris_json TEXT NOT NULL,
                review_method TEXT NOT NULL CHECK(review_method IN ('human', 'community')),
                reviewed_at TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE review_decisions (
                uri TEXT PRIMARY KEY,
                event_uri TEXT NOT NULL UNIQUE REFERENCES review_events(uri),
                target_assertion_uri TEXT NOT NULL,
                validation_dimension TEXT NOT NULL,
                outcome TEXT NOT NULL,
                valid_until TEXT,
                perspective_uri TEXT NOT NULL,
                represented_community_uris_json TEXT NOT NULL,
                applicability_scope_uris_json TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                rationale TEXT NOT NULL,
                rights_uri TEXT NOT NULL,
                supersedes_decision_uri TEXT,
                suspends_decision_uri TEXT,
                reinstates_decision_uri TEXT,
                decision_status TEXT NOT NULL,
                projection_policy_uris_json TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE organological_targets (
                uri TEXT PRIMARY KEY,
                target_kind TEXT NOT NULL,
                label TEXT NOT NULL,
                record_json TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE classification_criteria (
                uri TEXT PRIMARY KEY,
                criterion_type TEXT NOT NULL,
                label TEXT NOT NULL,
                status TEXT NOT NULL,
                record_json TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE observation_assessments (
                uri TEXT PRIMARY KEY,
                feature_of_interest_uri TEXT NOT NULL,
                assessed_property_uri TEXT NOT NULL,
                assessment_status TEXT NOT NULL,
                result_json TEXT,
                record_json TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE classification_expressions (
                uri TEXT PRIMARY KEY,
                source_concept_uri TEXT REFERENCES concepts(uri),
                notation_literal TEXT NOT NULL,
                combination_operator TEXT NOT NULL,
                parse_status TEXT NOT NULL,
                members_json TEXT NOT NULL,
                record_json TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE protocol_applications (
                uri TEXT PRIMARY KEY,
                protocol_uri TEXT NOT NULL,
                enforcement_mode TEXT NOT NULL,
                status TEXT NOT NULL,
                record_json TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE use_decisions (
                uri TEXT PRIMARY KEY,
                decision TEXT NOT NULL,
                decided_at TEXT NOT NULL,
                status TEXT NOT NULL,
                record_json TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE authority_assignments (
                uri TEXT PRIMARY KEY,
                agent_uri TEXT NOT NULL REFERENCES agents(uri),
                represented_community_uri TEXT,
                authority_role TEXT NOT NULL,
                authority_basis_uri TEXT NOT NULL,
                conferred_by_agent_uri TEXT NOT NULL REFERENCES agents(uri),
                subject_matter_uris_json TEXT NOT NULL,
                covered_validation_dimensions_json TEXT NOT NULL,
                covered_action_uris_json TEXT NOT NULL,
                applicability_scope_uris_json TEXT NOT NULL,
                valid_from TEXT NOT NULL,
                valid_until TEXT,
                delegation_permitted INTEGER NOT NULL,
                status TEXT NOT NULL,
                revocation_event_uri TEXT,
                revocation_effect TEXT,
                rights_uri TEXT NOT NULL,
                evidence_json TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE concept_ancestors (
                concept_uri TEXT NOT NULL REFERENCES concepts(uri),
                ancestor_uri TEXT NOT NULL REFERENCES concepts(uri),
                depth INTEGER NOT NULL CHECK(depth > 0),
                PRIMARY KEY(concept_uri, ancestor_uri)
            ) WITHOUT ROWID;
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE INDEX concepts_kind_idx ON concepts(kind);
            CREATE INDEX concepts_notation_idx ON concepts(notation);
            CREATE INDEX labels_language_label_idx ON labels(language, label);
            CREATE INDEX label_assertions_lookup_idx
                ON label_assertions(language_tag, literal_form, review_status);
            CREATE INDEX label_profiles_script_idx
                ON label_profiles(language_tag, translation_status, search_policy);
            CREATE INDEX note_assertions_concept_idx
                ON note_assertions(concept_uri, predicate_uri, review_status);
            CREATE INDEX source_relations_object_idx
                ON source_relations(object_uri, predicate_uri);
            CREATE INDEX classification_assertions_class_idx
                ON classification_assertions(classification_uri, target_uri);
            CREATE INDEX classification_assignments_assertion_idx
                ON classification_assignments(assertion_uri);
            CREATE INDEX review_decisions_target_idx
                ON review_decisions(target_assertion_uri, decision_status);
            CREATE INDEX concept_ancestors_lookup_idx
                ON concept_ancestors(ancestor_uri, depth, concept_uri);
            CREATE VIEW preferred_labels AS
                SELECT concept_uri, language_tag AS language, literal_form AS label
                FROM label_assertions
                WHERE label_role = 'preferred'
                  AND review_status NOT IN ('rejected', 'superseded');
            CREATE VIEW labels_enriched AS
                SELECT
                    la.uri AS assertion_uri,
                    la.concept_uri,
                    la.language_tag AS language,
                    la.submitted_language_tag,
                    la.language_tag_status,
                    la.language_registry_uri,
                    la.label_resource_uri,
                    la.label_role,
                    la.skos_projection_status,
                    la.literal_form AS label,
                    la.normalized_form,
                    la.asserted_by_uri,
                    la.source_record_uri,
                    la.source_uri,
                    la.assertion_origin,
                    la.review_status,
                    la.review_status_uri
                FROM label_assertions la;
            CREATE VIEW skosxl_labels AS
                SELECT
                    la.concept_uri,
                    la.label_role,
                    la.label_resource_uri,
                    lr.literal_form,
                    lr.normalized_form,
                    lr.language_tag,
                    la.skos_projection_status
                FROM label_assertions la
                JOIN label_resources lr ON lr.uri = la.label_resource_uri;
            CREATE VIEW label_linguistic_profiles AS
                SELECT
                    la.concept_uri,
                    lp.*,
                    lr.literal_form,
                    lr.normalized_form
                FROM label_profiles lp
                JOIN label_resources lr ON lr.uri = lp.label_resource_uri
                JOIN label_assertions la ON la.uri = lp.source_label_assertion_uri;
            CREATE VIEW notes_enriched AS
                SELECT
                    na.uri AS assertion_uri,
                    na.concept_uri,
                    na.predicate_uri,
                    na.language_tag AS language,
                    na.submitted_language_tag,
                    na.language_tag_status,
                    na.language_registry_uri,
                    na.literal_form AS note,
                    na.normalized_form,
                    na.asserted_by_uri,
                    na.source_record_uri,
                    na.source_uri,
                    na.assertion_origin,
                    na.review_status,
                    na.review_status_uri
                FROM note_assertions na;
            CREATE VIEW assertions AS
                SELECT
                    ca.uri,
                    'classification' AS assertion_type,
                    ca.target_uri AS subject_uri,
                    ca.predicate_uri,
                    ca.classification_uri AS object_uri,
                    NULL AS object_literal,
                    NULL AS language_tag,
                    assignment.assigned_by_uri AS claimant_uri,
                    ca.source_record_uri,
                    ca.source_uri,
                    ca.assertion_origin,
                    ca.stance
                FROM classification_assertions ca
                JOIN classification_assignments assignment
                  ON assignment.assertion_uri = ca.uri
                UNION ALL
                SELECT
                    la.uri,
                    'label' AS assertion_type,
                    la.concept_uri AS subject_uri,
                    la.predicate_uri,
                    NULL AS object_uri,
                    la.literal_form AS object_literal,
                    la.language_tag,
                    la.asserted_by_uri AS claimant_uri,
                    la.source_record_uri,
                    la.source_uri,
                    la.assertion_origin,
                    'source-asserted' AS stance
                FROM label_assertions la
                UNION ALL
                SELECT
                    na.uri,
                    'note' AS assertion_type,
                    na.concept_uri AS subject_uri,
                    na.predicate_uri,
                    NULL AS object_uri,
                    na.literal_form AS object_literal,
                    na.language_tag,
                    na.asserted_by_uri AS claimant_uri,
                    na.source_record_uri,
                    na.source_uri,
                    na.assertion_origin,
                    'source-asserted' AS stance
                FROM note_assertions na;
            CREATE VIEW audit_queue AS
                SELECT
                    qf.uri AS finding_uri,
                    qf.rule_code,
                    qr.title,
                    qf.target_assertion_uri,
                    qf.concept_uri,
                    qf.validation_dimension,
                    qf.severity,
                    qf.applies_to_json,
                    qf.evidence_json
                FROM quality_findings qf
                JOIN quality_rules qr ON qr.uri = qf.rule_uri
                WHERE qf.human_review_required = 1
                  AND qf.review_effect = 'none';
            CREATE VIEW classification_claims AS
                SELECT ca.uri AS assertion_uri,
                       assignment.uri AS assignment_uri,
                       ca.classification_uri,
                       ca.target_uri
                FROM classification_assertions ca
                JOIN classification_assignments assignment
                  ON assignment.assertion_uri = ca.uri;
            CREATE TABLE endorsed_classification_assertions (
                assertion_uri TEXT PRIMARY KEY
                    REFERENCES classification_assertions(uri)
            ) WITHOUT ROWID;
            CREATE VIEW classification_targets AS
                SELECT DISTINCT
                    ca.classification_uri,
                    ca.target_uri,
                    target_label.label AS target_label_en,
                    target.resolution_status AS target_resolution_status
                FROM classification_assertions ca
                JOIN endorsed_classification_assertions endorsed
                  ON endorsed.assertion_uri = ca.uri
                LEFT JOIN concepts target ON target.uri = ca.target_uri
                LEFT JOIN preferred_labels target_label
                  ON target_label.concept_uri = ca.target_uri
                 AND target_label.language = 'en';
            CREATE VIEW mimo_source_exact_matches AS
                SELECT subject_uri AS classification_uri, object_uri AS target_uri,
                       source_uri
                FROM source_relations
                WHERE predicate_uri = 'http://www.w3.org/2004/02/skos/core#exactMatch';
            CREATE VIEW classification_claims_enriched AS
                SELECT
                    ca.uri AS assertion_uri,
                    assignment.uri AS assignment_uri,
                    ci.classification_uri,
                    c.notation AS classification_notation,
                    cl.label AS classification_label_en,
                    ci.target_uri,
                    il.label AS target_label_en,
                    i.resolution_status AS target_resolution_status,
                    ca.assertion_origin,
                    ca.target_type,
                    ca.classification_scheme_uri,
                    assignment.assigned_by_uri,
                    assignment.generated_by_uri,
                    ca.perspective_uri,
                    assignment.classification_method_uri,
                    assignment.criteria_uris_json,
                    assignment.assessment_uris_json,
                    assignment.inference_logic_uri,
                    assignment.classification_expression_uri,
                    ca.stance,
                    ca.applicability_scope_uris_json,
                    ca.evidence_json,
                    ca.source_record_uri,
                    ca.source_predicate_uri,
                    ca.source_uri
                FROM classification_claims ci
                JOIN classification_assertions ca
                    ON ca.uri = ci.assertion_uri
                JOIN classification_assignments assignment
                    ON assignment.uri = ci.assignment_uri
                JOIN concepts c ON c.uri = ci.classification_uri
                LEFT JOIN concepts i ON i.uri = ci.target_uri
                LEFT JOIN preferred_labels cl
                    ON cl.concept_uri = ci.classification_uri AND cl.language = 'en'
                LEFT JOIN preferred_labels il
                    ON il.concept_uri = ci.target_uri AND il.language = 'en';
            CREATE VIRTUAL TABLE label_search USING fts5(
                concept_uri UNINDEXED,
                language UNINDEXED,
                label,
                tokenize = 'unicode61'
            );
            """
        )
        connection.executemany(
            "INSERT INTO schemes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["label"],
                    row["scheme_type"],
                    row["version"],
                    row["version_uri"],
                    row["publisher_agent_uri"],
                    row["perspective_uri"],
                    row["source_record_uri"],
                    row["governance_uri"],
                    row["rights_uri"],
                    row["status"],
                    row["scope_note"],
                )
                for row in sorted(dataset.concept_schemes, key=lambda row: row["uri"])
            ],
        )
        connection.executemany(
            "INSERT INTO agents VALUES (?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["agent_type"],
                    row["name"],
                    row["resource_uri"],
                )
                for row in sorted(dataset.agents, key=lambda row: row["uri"])
            ],
        )
        connection.executemany(
            "INSERT INTO perspectives VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["label"],
                    row["perspective_type"],
                    row["holder_agent_uri"],
                    json.dumps(row["represented_community_uris"], sort_keys=True),
                    row["description"],
                    row["status"],
                    row["valid_from"],
                    row["valid_until"],
                    json.dumps(row["authority_assignment_uris"], sort_keys=True),
                )
                for row in sorted(dataset.perspectives, key=lambda row: row["uri"])
            ],
        )
        connection.executemany(
            "INSERT INTO applicability_scopes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["label"],
                    row["scope_mode"],
                    row["description"],
                    json.dumps(row["community_uris"], sort_keys=True),
                    json.dumps(row["place_uris"], sort_keys=True),
                    json.dumps(row["period_uris"], sort_keys=True),
                    json.dumps(row["usage_domain_uris"], sort_keys=True),
                    json.dumps(row["playing_technique_uris"], sort_keys=True),
                    json.dumps(row["instrument_configuration_uris"], sort_keys=True),
                    json.dumps(row["language_variety_uris"], sort_keys=True),
                    row["temporal_start"],
                    row["temporal_end"],
                    row["asserted_by_uri"],
                    row["perspective_uri"],
                    row["source_record_uri"],
                )
                for row in sorted(
                    dataset.applicability_scopes, key=lambda row: row["uri"]
                )
            ],
        )
        connection.executemany(
            "INSERT INTO projection_policies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["label"],
                    row["description"],
                    row["graph_role"],
                    int(row["direct_assertion"]),
                    json.dumps(row["eligible_stances"], sort_keys=True),
                    json.dumps(row["review_requirements"], sort_keys=True),
                    row["minimum_independent_reviewers"],
                    json.dumps(row["veto_rules"], sort_keys=True),
                    int(row["context_match_required"]),
                    row["unknown_scope_behavior"],
                    int(row["includes_source_layer"]),
                    row["policy_version"],
                )
                for row in sorted(
                    dataset.projection_policies, key=lambda row: row["uri"]
                )
            ],
        )
        connection.executemany(
            "INSERT INTO review_statuses VALUES (?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["code"],
                    row["label"],
                    row["description"],
                )
                for row in sorted(dataset.review_statuses, key=lambda row: row["uri"])
            ],
        )
        connection.executemany(
            "INSERT INTO language_registries VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["registry_type"],
                    row["file_date"],
                    row["source_uri"],
                    row["artifact_path"],
                    row["sha256"],
                    row["profile_uri"],
                    json.dumps(
                        row["normalization_overrides"],
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                )
                for row in dataset.language_registries
            ],
        )
        connection.executemany(
            "INSERT INTO script_registries VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["registry_type"],
                    row["unicode_version"],
                    json.dumps(row["source_uris"], sort_keys=True),
                    row["artifact_path"],
                    row["sha256"],
                    row["profile_uri"],
                )
                for row in dataset.script_registries
            ],
        )
        connection.executemany(
            "INSERT INTO quality_rules VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                tuple(
                    row[field]
                    for field in (
                        "uri",
                        "code",
                        "validation_dimension",
                        "severity",
                        "title",
                        "description",
                        "assessment_method",
                        "review_effect",
                    )
                )
                for row in sorted(dataset.quality_rules, key=lambda row: row["uri"])
            ],
        )
        connection.executemany(
            "INSERT INTO source_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["resource_uri"],
                    row["title"],
                    row["source_type"],
                    row["scheme_uri"],
                    row["publisher_agent_uri"],
                    row["layer"],
                    row["rights_uri"],
                    row["retrieved_at"],
                )
                for row in sorted(dataset.source_records, key=lambda row: row["uri"])
            ],
        )
        connection.executemany(
            "INSERT INTO concepts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["scheme_uri"],
                    row["kind"],
                    row["local_id"],
                    row.get("mimo_id"),
                    row.get("notation"),
                    row.get("definition"),
                    row.get("created"),
                    row["resolution_status"],
                )
                for row in sorted(dataset.concepts, key=lambda row: row["uri"])
            ],
        )
        label_rows = [
            (
                row["concept_uri"],
                row["language"],
                row["submitted_language"],
                row["label_type"],
                row["label"],
            )
            for row in sorted(
                dataset.labels,
                key=lambda row: (
                    row["concept_uri"],
                    row["language"],
                    row["label_type"],
                    row["label"],
                ),
            )
        ]
        connection.executemany("INSERT INTO labels VALUES (?, ?, ?, ?, ?)", label_rows)
        connection.executemany(
            "INSERT INTO label_resources VALUES (?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["literal_form"],
                    row["normalized_form"],
                    row["language_tag"],
                    row["language_registry_uri"],
                )
                for row in sorted(dataset.label_resources, key=lambda row: row["uri"])
            ],
        )
        label_assertion_rows = [
            (
                row["uri"],
                row["concept_uri"],
                row["predicate_uri"],
                row["literal_form"],
                row["normalized_form"],
                row["language_tag"],
                row["submitted_language_tag"],
                row["language_tag_status"],
                row["language_registry_uri"],
                row["label_resource_uri"],
                row["label_role"],
                row["skos_projection_status"],
                row["asserted_by_uri"],
                row["source_record_uri"],
                row["source_uri"],
                row["assertion_origin"],
                row["review_status"],
                row["review_status_uri"],
            )
            for row in sorted(dataset.label_assertions, key=lambda row: row["uri"])
        ]
        connection.executemany(
            "INSERT INTO label_assertions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            label_assertion_rows,
        )
        connection.executemany(
            "INSERT INTO label_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["label_resource_uri"],
                    row["source_label_assertion_uri"],
                    row["language_tag"],
                    row["primary_language_subtag"],
                    row["explicit_script_subtag"],
                    row["default_script_subtag"],
                    row["region_subtag"],
                    json.dumps(row["variant_subtags"], sort_keys=True),
                    json.dumps(row["extension_subtags"], sort_keys=True),
                    json.dumps(row["private_use_subtags"], sort_keys=True),
                    row["language_variety_uri"],
                    row["writing_system_uri"],
                    json.dumps(row["observed_script_codes"], sort_keys=True),
                    int(row["has_common_or_inherited_characters"]),
                    row["script_observation_method"],
                    row["script_registry_uri"],
                    row["transliteration_system_uri"],
                    row["transcription_system_uri"],
                    json.dumps(row["pronunciations"], ensure_ascii=False),
                    json.dumps(row["audio_uris"], sort_keys=True),
                    json.dumps(row["term_roles"], sort_keys=True),
                    row["translation_status"],
                    json.dumps(row["applies_to"], sort_keys=True),
                    row["display_policy"],
                    row["search_policy"],
                    row["asserted_by_uri"],
                    row["source_record_uri"],
                    row["assertion_origin"],
                    row["review_status"],
                    row["review_status_uri"],
                )
                for row in sorted(dataset.label_profiles, key=lambda row: row["uri"])
            ],
        )
        connection.executemany(
            "INSERT INTO note_assertions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["concept_uri"],
                    row["predicate_uri"],
                    row["literal_form"],
                    row["normalized_form"],
                    row["language_tag"],
                    row["submitted_language_tag"],
                    row["language_tag_status"],
                    row["language_registry_uri"],
                    row["asserted_by_uri"],
                    row["source_record_uri"],
                    row["source_uri"],
                    row["assertion_origin"],
                    row["review_status"],
                    row["review_status_uri"],
                )
                for row in sorted(dataset.note_assertions, key=lambda row: row["uri"])
            ],
        )
        connection.executemany(
            "INSERT INTO label_search(concept_uri, language, label) VALUES (?, ?, ?)",
            [
                (row[1], row[5], row[3])
                for row in label_assertion_rows
                if row[16] not in {"rejected", "superseded"}
            ],
        )
        connection.executemany(
            "INSERT INTO source_relations VALUES (?, ?, ?, ?)",
            [
                (
                    row["subject_uri"],
                    row["predicate_uri"],
                    row["object_uri"],
                    row["source_uri"],
                )
                for row in sorted(
                    dataset.source_relations,
                    key=lambda row: (
                        row["subject_uri"],
                        row["predicate_uri"],
                        row["object_uri"],
                    ),
                )
            ],
        )
        connection.executemany(
            "INSERT INTO organological_targets VALUES (?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["target_kind"],
                    row["label"],
                    canonical_json(row),
                )
                for row in sorted(
                    dataset.organological_targets, key=lambda row: row["uri"]
                )
            ],
        )
        connection.executemany(
            "INSERT INTO classification_criteria VALUES (?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["criterion_type"],
                    row["label"],
                    row["status"],
                    canonical_json(row),
                )
                for row in sorted(
                    dataset.classification_criteria, key=lambda row: row["uri"]
                )
            ],
        )
        connection.executemany(
            "INSERT INTO observation_assessments VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["feature_of_interest_uri"],
                    row["assessed_property_uri"],
                    row["assessment_status"],
                    canonical_json(row["result"])
                    if row["result"] is not None
                    else None,
                    canonical_json(row),
                )
                for row in sorted(
                    dataset.observation_assessments, key=lambda row: row["uri"]
                )
            ],
        )
        connection.executemany(
            "INSERT INTO classification_expressions VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["source_concept_uri"],
                    row["notation_literal"],
                    row["combination_operator"],
                    row["parse_status"],
                    canonical_json(row["members"]),
                    canonical_json(row),
                )
                for row in sorted(
                    dataset.classification_expressions, key=lambda row: row["uri"]
                )
            ],
        )
        connection.executemany(
            "INSERT INTO protocol_applications VALUES (?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["protocol_uri"],
                    row["enforcement_mode"],
                    row["status"],
                    canonical_json(row),
                )
                for row in sorted(
                    dataset.protocol_applications, key=lambda row: row["uri"]
                )
            ],
        )
        connection.executemany(
            "INSERT INTO use_decisions VALUES (?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["decision"],
                    row["decided_at"],
                    row["status"],
                    canonical_json(row),
                )
                for row in sorted(dataset.use_decisions, key=lambda row: row["uri"])
            ],
        )
        connection.executemany(
            "INSERT INTO classification_assertions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["target_uri"],
                    row["target_type"],
                    row["predicate_uri"],
                    row["classification_uri"],
                    row["classification_scheme_uri"],
                    row["scheme_version_uri"],
                    row["perspective_uri"],
                    row["stance"],
                    json.dumps(row["applicability_scope_uris"], sort_keys=True),
                    json.dumps(row["evidence"], ensure_ascii=False, sort_keys=True),
                    json.dumps(row["authority_assignment_uris"], sort_keys=True),
                    row["valid_from"],
                    row["valid_until"],
                    json.dumps(row["projection_policy_uris"], sort_keys=True),
                    row["source_predicate_uri"],
                    row["source_uri"],
                    row["source_record_uri"],
                    row["assertion_origin"],
                )
                for row in sorted(
                    dataset.classification_assertions, key=lambda row: row["uri"]
                )
            ],
        )
        connection.executemany(
            "INSERT INTO classification_assignments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["assignment_uri"],
                    row["uri"],
                    row["assigned_by_uri"],
                    row["generated_by_uri"],
                    row["classification_method_uri"],
                    json.dumps(row["criteria_uris"], sort_keys=True),
                    json.dumps(row["assessment_uris"], sort_keys=True),
                    row["inference_logic_uri"],
                    row["classification_expression_uri"],
                )
                for row in sorted(
                    dataset.classification_assertions,
                    key=lambda row: row["assignment_uri"],
                )
            ],
        )
        connection.executemany(
            "INSERT INTO concept_relation_assertions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["subject_concept_uri"],
                    row["predicate_uri"],
                    row["object_concept_uri"],
                    row["assigned_by_uri"],
                    row["generated_by_uri"],
                    row["perspective_uri"],
                    row["relation_method_uri"],
                    json.dumps(row["mapping_purpose_uris"], sort_keys=True),
                    row["stance"],
                    json.dumps(row["applicability_scope_uris"], sort_keys=True),
                    json.dumps(row["evidence"], ensure_ascii=False, sort_keys=True),
                    json.dumps(row["authority_assignment_uris"], sort_keys=True),
                    row["valid_from"],
                    row["valid_until"],
                    json.dumps(row["projection_policy_uris"], sort_keys=True),
                    row["source_record_uri"],
                    row["assertion_origin"],
                )
                for row in sorted(
                    dataset.concept_relation_assertions, key=lambda row: row["uri"]
                )
            ],
        )
        connection.executemany(
            "INSERT INTO quality_findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["rule_uri"],
                    row["rule_code"],
                    row["target_assertion_uri"],
                    row["concept_uri"],
                    row["detected_by_uri"],
                    row["detected_at"],
                    row["assessment_method"],
                    row["validation_dimension"],
                    row["severity"],
                    row["review_effect"],
                    int(row["human_review_required"]),
                    json.dumps(row["applies_to"], ensure_ascii=False, sort_keys=True),
                    json.dumps(row["evidence"], ensure_ascii=False, sort_keys=True),
                )
                for row in sorted(dataset.quality_findings, key=lambda row: row["uri"])
            ],
        )
        connection.executemany(
            "INSERT INTO authority_assignments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["agent_uri"],
                    row["represented_community_uri"],
                    row["authority_role"],
                    row["authority_basis_uri"],
                    row["conferred_by_agent_uri"],
                    json.dumps(row["subject_matter_uris"], sort_keys=True),
                    json.dumps(row["covered_validation_dimensions"], sort_keys=True),
                    json.dumps(row["covered_action_uris"], sort_keys=True),
                    json.dumps(row["applicability_scope_uris"], sort_keys=True),
                    row["valid_from"],
                    row["valid_until"],
                    int(row["delegation_permitted"]),
                    row["status"],
                    row["revocation_event_uri"],
                    row["revocation_effect"],
                    row["rights_uri"],
                    json.dumps(row["evidence"], ensure_ascii=False, sort_keys=True),
                )
                for row in sorted(
                    dataset.authority_assignments, key=lambda row: row["uri"]
                )
            ],
        )
        connection.executemany(
            "INSERT INTO review_events VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    row["uri"],
                    row["reviewer_agent_uri"],
                    row["reviewer_authority"],
                    json.dumps(row["authority_assignment_uris"], sort_keys=True),
                    row["review_method"],
                    row["reviewed_at"],
                )
                for row in sorted(dataset.review_events, key=lambda row: row["uri"])
            ],
        )
        connection.executemany(
            "INSERT INTO review_decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["decision_uri"],
                    row["uri"],
                    row["target_assertion_uri"],
                    row["validation_dimension"],
                    row["outcome"],
                    row["valid_until"],
                    row["perspective_uri"],
                    json.dumps(row["represented_community_uris"], sort_keys=True),
                    json.dumps(row["applicability_scope_uris"], sort_keys=True),
                    json.dumps(row["evidence"], ensure_ascii=False, sort_keys=True),
                    row["rationale"],
                    row["rights_uri"],
                    row["supersedes_decision_uri"],
                    row["suspends_decision_uri"],
                    row["reinstates_decision_uri"],
                    row["decision_status"],
                    json.dumps(row["projection_policy_uris"], sort_keys=True),
                )
                for row in sorted(
                    dataset.review_events, key=lambda row: row["decision_uri"]
                )
            ],
        )
        connection.executemany(
            "INSERT INTO endorsed_classification_assertions VALUES (?)",
            [
                (row["uri"],)
                for row in sorted(
                    dataset.classification_assertions, key=lambda row: row["uri"]
                )
                if dataset.is_directly_endorsed(row, ENDORSED_POLICY)
            ],
        )
        connection.executemany(
            "INSERT INTO concept_ancestors VALUES (?, ?, ?)",
            _ancestor_rows(dataset),
        )
        connection.executemany(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            [
                (key, json.dumps(value, ensure_ascii=False, sort_keys=True))
                for key, value in sorted(
                    {
                        **dataset.metadata,
                        "build_python_version": platform.python_version(),
                        "build_sqlite_version": sqlite3.sqlite_version,
                    }.items()
                )
            ],
        )
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        if integrity != "ok" or foreign_keys:
            raise ValidationError(
                f"SQLite validation failed: integrity={integrity}, foreign_keys={foreign_keys}"
            )
        connection.execute("VACUUM")
    finally:
        connection.close()


def _build_site(dataset: Dataset, output: Path, site_source: Path) -> None:
    concepts = dataset.concepts_by_uri
    labels = dataset.labels_by_concept
    label_assertions = dataset.label_assertions_by_concept
    label_profiles = dataset.label_profiles_by_resource_uri
    note_assertions = dataset.note_assertions_by_concept
    findings_by_concept: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in dataset.quality_findings:
        findings_by_concept[finding["concept_uri"]].append(finding)
    parents: dict[str, list[str]] = defaultdict(list)
    children: dict[str, list[str]] = defaultdict(list)
    classified_instruments: dict[str, list[str]] = defaultdict(list)
    instrument_classifications: dict[str, list[str]] = defaultdict(list)
    classification_claims_by_concept: dict[str, list[dict[str, Any]]] = defaultdict(
        list
    )
    for relation in dataset.source_relations:
        if relation["predicate_uri"] == BROADER:
            parents[relation["subject_uri"]].append(relation["object_uri"])
            children[relation["object_uri"]].append(relation["subject_uri"])
    for assertion in dataset.classification_assertions:
        if assertion["stance"] in {"rejected", "superseded"}:
            continue
        if assertion["target_type"] != "instrument-concept":
            continue
        classified_instruments[assertion["classification_uri"]].append(
            assertion["target_uri"]
        )
        instrument_classifications[assertion["target_uri"]].append(
            assertion["classification_uri"]
        )
        claim_summary = {
            "assertionUri": assertion["uri"],
            "assignmentUri": assertion["assignment_uri"],
            "targetUri": assertion["target_uri"],
            "classificationUri": assertion["classification_uri"],
            "classificationSchemeUri": assertion["classification_scheme_uri"],
            "perspectiveUri": assertion["perspective_uri"],
            "stance": assertion["stance"],
            "applicabilityScopeUris": assertion["applicability_scope_uris"],
            "authorityAssignmentUris": assertion["authority_assignment_uris"],
            "projectionPolicyUris": assertion["projection_policy_uris"],
            "activeReviewDecisions": dataset.active_review_decisions(assertion["uri"]),
        }
        classification_claims_by_concept[assertion["classification_uri"]].append(
            claim_summary
        )
        classification_claims_by_concept[assertion["target_uri"]].append(claim_summary)
    items: list[dict[str, Any]] = []
    for concept in dataset.concepts:
        preferred = {
            row["language"]: row["label"]
            for row in labels[concept["uri"]]
            if row["label_type"] == "preferred"
        }
        alternatives = sorted(
            {
                row["label"]
                for row in labels[concept["uri"]]
                if row["label_type"] != "preferred"
            }
        )
        searchable = "\n".join([*preferred.values(), *alternatives]).casefold()
        items.append(
            {
                "uri": concept["uri"],
                "kind": concept["kind"],
                "notation": concept.get("notation"),
                "definition": concept.get("definition"),
                "resolutionStatus": concept["resolution_status"],
                "labels": preferred,
                "alternativeLabels": alternatives,
                "labelAssertionReviewStatuses": sorted(
                    {row["review_status"] for row in label_assertions[concept["uri"]]}
                ),
                "languageTagStatuses": sorted(
                    {
                        row["language_tag_status"]
                        for row in label_assertions[concept["uri"]]
                    }
                ),
                "observedScripts": sorted(
                    {
                        script
                        for assertion in label_assertions[concept["uri"]]
                        for script in label_profiles[assertion["label_resource_uri"]][
                            "observed_script_codes"
                        ]
                    }
                ),
                "translationStatuses": sorted(
                    {
                        label_profiles[assertion["label_resource_uri"]][
                            "translation_status"
                        ]
                        for assertion in label_assertions[concept["uri"]]
                    }
                ),
                "noteAssertionReviewStatuses": sorted(
                    {row["review_status"] for row in note_assertions[concept["uri"]]}
                ),
                "qualityFindings": sorted(
                    {row["rule_code"] for row in findings_by_concept[concept["uri"]]}
                ),
                "parents": sorted(parents[concept["uri"]]),
                "children": sorted(
                    children[concept["uri"]],
                    key=lambda uri: concepts[uri].get("notation", uri),
                ),
                "instruments": sorted(classified_instruments[concept["uri"]]),
                "classifications": sorted(instrument_classifications[concept["uri"]]),
                "classificationAssignments": sorted(
                    classification_claims_by_concept[concept["uri"]],
                    key=lambda row: row["assignmentUri"],
                ),
                "search": searchable,
            }
        )
    roots = sorted(
        (
            row["uri"]
            for row in dataset.concepts
            if row["kind"] == "classification" and not parents[row["uri"]]
        ),
        key=lambda uri: concepts[uri].get("notation", uri),
    )
    payload = {
        "version": dataset.metadata["dataset_version"],
        "doi": dataset.metadata["doi"],
        "classificationCount": sum(
            row["kind"] == "classification" for row in dataset.concepts
        ),
        "instrumentCount": sum(
            row["kind"] == "instrument" and row["resolution_status"] == "resolved"
            for row in dataset.concepts
        ),
        "labelAssertionCount": len(dataset.label_assertions),
        "labelResourceCount": len(dataset.label_resources),
        "labelProfileCount": len(dataset.label_profiles),
        "noteAssertionCount": len(dataset.note_assertions),
        "qualityFindingCount": len(dataset.quality_findings),
        "languageRegistryDate": dataset.language_registries[0]["file_date"],
        "unicodeScriptVersion": dataset.script_registries[0]["unicode_version"],
        "classificationNotice": (
            "Instrument/classification relationships are qualified assignment "
            "occurrences. Source mappings use the MIMO perspective and a "
            "source-silent scope; source silence is not context-independent or "
            "culturally validated."
        ),
        "endorsedClassificationCount": sum(
            dataset.is_directly_endorsed(row)
            for row in dataset.classification_assertions
        ),
        "perspectives": dataset.perspectives,
        "applicabilityScopes": dataset.applicability_scopes,
        "projectionPolicies": dataset.projection_policies,
        "lexicalNotice": (
            "Labels and definitions are preserved source assertions with stable "
            "agent, source, and review-status links; unreviewed does not mean "
            "linguistically or culturally validated. Character scripts are "
            "observations, not inferred languages or cultural identities."
        ),
        "qualityNotice": (
            "Automated findings are warnings only, have no review effect, and "
            "may describe valid transliterations, loanwords, or historical forms."
        ),
        "roots": roots,
        "items": sorted(items, key=lambda row: row["uri"]),
    }
    for name in ("index.html", "styles.css", "app.js", "favicon.svg"):
        shutil.copy2(site_source / name, output / name)

    ontology_version_dir = output / "ontology" / dataset.metadata["schema_version"]
    ontology_version_dir.mkdir(parents=True, exist_ok=True)
    ontology_template = (site_source / "ontology/index.html").read_text()
    (ontology_version_dir / "index.html").write_text(
        ontology_template.replace("{{ROOT}}", "../../"), encoding="utf-8"
    )
    (output / "ontology/index.html").write_text(
        ontology_template.replace("{{ROOT}}", "../"), encoding="utf-8"
    )

    dataset_version_dir = output / "dataset" / dataset.metadata["dataset_version"]
    dataset_version_dir.mkdir(parents=True)
    for suffix in ("ttl", "jsonld", "rdf"):
        shutil.copy2(
            output / "rdf" / f"omaro.{suffix}",
            dataset_version_dir / f"omaro.{suffix}",
        )
    dataset_template = (site_source / "dataset/index.html").read_text()
    (dataset_version_dir / "index.html").write_text(
        dataset_template.replace("{{ROOT}}", "../../"), encoding="utf-8"
    )
    (output / "dataset/index.html").write_text(
        dataset_template.replace("{{ROOT}}", "../"), encoding="utf-8"
    )

    (output / "data.json").write_text(
        canonical_json(payload), encoding="utf-8", newline="\n"
    )


def _release_archive_uri(version: str) -> URIRef:
    return URIRef(f"{RELEASES_BASE}/v{version}/omaro-v{version}.zip")


def _build_fair_metadata(dataset: Dataset, output: Path, triple_count: int) -> None:
    metadata_dir = output / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    dataset_base_uri = URIRef(DATASET_BASE_URI)
    dataset_uri = URIRef(dataset.metadata["dataset_uri"])
    doi_uri = URIRef(f"https://doi.org/{dataset.metadata['doi']}")
    archive_uri = _release_archive_uri(dataset.metadata["dataset_version"])
    graph = Graph()
    graph.bind("dcat", DCAT)
    graph.bind("dcterms", DCTERMS)
    graph.bind("void", VOID)
    graph.bind("schema", SCHEMA)
    graph.add((dataset_base_uri, RDF.type, DCAT.Dataset))
    graph.add((dataset_base_uri, DCAT_NS.hasVersion, dataset_uri))
    graph.add((dataset_base_uri, DCAT_NS.hasCurrentVersion, dataset_uri))
    graph.add((dataset_uri, RDF.type, DCAT.Dataset))
    graph.add((dataset_uri, RDF.type, VOID.Dataset))
    graph.add((dataset_uri, DCAT_NS.isVersionOf, dataset_base_uri))
    graph.add(
        (dataset_uri, DCAT_NS.version, Literal(dataset.metadata["dataset_version"]))
    )
    graph.add((dataset_uri, DCTERMS.identifier, Literal(dataset.metadata["doi"])))
    graph.add(
        (dataset_uri, DCTERMS.title, Literal(dataset.metadata["title"], lang="en"))
    )
    graph.add(
        (
            dataset_uri,
            DCTERMS.description,
            Literal(
                "The OMARO ontology and a versioned MIMO-derived reference "
                "dataset for contextualized, evidenced, and reviewable "
                "organological assertions, with preserved source statements "
                "and conservative linguistic profiles.",
                lang="en",
            ),
        )
    )
    graph.add((dataset_uri, DCTERMS.license, LICENSE_URI))
    graph.add(
        (
            dataset_uri,
            DCTERMS.issued,
            Literal(dataset.metadata["generated_at"], datatype=XSD.dateTime),
        )
    )
    graph.add(
        (
            dataset_uri,
            DCTERMS.conformsTo,
            URIRef(dataset.metadata["ontology_version_iri"]),
        )
    )
    graph.add((dataset_uri, DCTERMS.relation, VAO_RELEASE_IRI))
    graph.add((dataset_uri, DCTERMS.relation, MODAVIS_RELEASE_IRI))
    _add_creator(graph, dataset_uri, dataset)
    graph.add((dataset_uri, DCTERMS.publisher, Literal("Zenodo")))
    graph.add((dataset_uri, VOID.triples, Literal(triple_count)))
    graph.add((dataset_uri, VOID.vocabulary, URIRef(str(SKOS))))
    graph.add((dataset_uri, VOID.dataDump, archive_uri))
    for source in dataset.metadata["sources"]:
        graph.add((dataset_uri, DCTERMS.source, URIRef(source)))
    distribution = URIRef(f"{dataset_uri}#distribution-zip")
    graph.add((dataset_uri, DCAT.distribution, distribution))
    graph.add((distribution, RDF.type, DCAT.Distribution))
    graph.add((distribution, DCAT.downloadURL, archive_uri))
    graph.add((distribution, DCAT_NS.packageFormat, IANA_ZIP_MEDIA_TYPE))
    graph.add((distribution, DCTERMS.license, LICENSE_URI))
    graph.add((dataset_uri, DCAT.landingPage, doi_uri))
    serialized = graph.serialize(format="turtle")
    (metadata_dir / "dcat-void.ttl").write_text(
        serialized, encoding="utf-8", newline="\n"
    )

    datacite = {
        "data": {
            "type": "dois",
            "id": dataset.metadata["doi"],
            "attributes": {
                "doi": dataset.metadata["doi"],
                "creators": [
                    {
                        "name": "Ukolov, Dominik",
                        "givenName": "Dominik",
                        "familyName": "Ukolov",
                        "affiliation": [
                            {"name": affiliation}
                            for affiliation in dataset.metadata["creators"][0][
                                "affiliations"
                            ]
                        ],
                    }
                ],
                "titles": [{"title": dataset.metadata["title"]}],
                "publisher": "Zenodo",
                "publicationYear": 2026,
                "types": {"resourceTypeGeneral": "Dataset"},
                "schemaVersion": "http://datacite.org/schema/kernel-4",
                "version": dataset.metadata["dataset_version"],
                "language": "en",
                "rightsList": [
                    {
                        "rights": "Creative Commons Zero v1.0 Universal",
                        "rightsUri": str(LICENSE_URI),
                        "rightsIdentifier": "CC0-1.0",
                        "rightsIdentifierScheme": "SPDX",
                    }
                ],
                "subjects": [
                    {"subject": value}
                    for value in (
                        "Hornbostel-Sachs",
                        "musical instruments",
                        "multilingual vocabulary",
                        "SKOS",
                        "SKOS-XL",
                        "linked data",
                        "digital organology",
                        "multiperspectivity",
                        "ontology",
                        "Open Knowledge Format",
                        "retrieval-augmented generation",
                    )
                ],
                "descriptions": [
                    {
                        "description": (
                            "The OMARO ontology and a versioned MIMO-derived "
                            "reference dataset for contextualized, evidenced, "
                            "and reviewable organological assertions, with "
                            "preserved source statements and conservative "
                            "linguistic profiles."
                        ),
                        "descriptionType": "Abstract",
                    }
                ],
                "relatedIdentifiers": [
                    {
                        "relatedIdentifier": dataset.metadata["ontology_version_iri"],
                        "relatedIdentifierType": "URL",
                        "relationType": "IsDocumentedBy",
                    },
                    {
                        "relatedIdentifier": dataset.metadata["dataset_uri"],
                        "relatedIdentifierType": "URL",
                        "relationType": "IsIdenticalTo",
                    },
                    {
                        "relatedIdentifier": REPOSITORY_URI,
                        "relatedIdentifierType": "URL",
                        "relationType": "IsSupplementedBy",
                    },
                    {
                        "relatedIdentifier": "https://vocabulary.mimo-international.com/",
                        "relatedIdentifierType": "URL",
                        "relationType": "IsDerivedFrom",
                    },
                    {
                        "relatedIdentifier": "10.5281/zenodo.22122774",
                        "relatedIdentifierType": "DOI",
                        "relationType": "References",
                    },
                    {
                        "relatedIdentifier": "10.5281/zenodo.22126086",
                        "relatedIdentifierType": "DOI",
                        "relationType": "References",
                    },
                ],
                "formats": [
                    "application/zip",
                    "application/x-ndjson",
                    "text/csv",
                    "text/markdown",
                    "application/ld+json",
                    "text/turtle",
                    "application/vnd.sqlite3",
                ],
            },
        }
    }
    (metadata_dir / "datacite.json").write_text(
        canonical_json(datacite, indent=2), encoding="utf-8", newline="\n"
    )

    classification = next(
        row
        for row in dataset.concepts
        if row.get("notation") == "111.141" and row["scheme_uri"] == HS_SCHEME
    )
    scheme = next(row for row in dataset.concept_schemes if row["uri"] == HS_SCHEME)
    label = next(
        row["label"]
        for row in dataset.labels
        if row["concept_uri"] == classification["uri"]
        and row["label_type"] == "preferred"
        and row["language"] == "en"
    )
    vao_example = {
        "scheme": classification["scheme_uri"],
        "code": classification["notation"],
        "label": {"en": label},
        "version": scheme["version"],
    }
    (metadata_dir / "vao-classification-example.json").write_text(
        canonical_json(vao_example, indent=2), encoding="utf-8", newline="\n"
    )


def _build_dqv_metadata(
    dataset: Dataset,
    output: Path,
    quality_report: dict[str, Any],
    *,
    canonical_validation_passed: bool,
) -> None:
    """Write machine-readable measures derived from the build quality report."""
    dataset_uri = URIRef(dataset.metadata["dataset_uri"])
    ontology_uri = URIRef(dataset.metadata["ontology_uri"])
    software_agent = OMARO_NS["release-builder"]
    generated_at = Literal(dataset.metadata["generated_at"], datatype=XSD.dateTime)
    resolved_targets = int(quality_report["instruments"])
    unresolved_targets = int(quality_report["unresolved_stubs"])
    target_denominator = resolved_targets + unresolved_targets
    if target_denominator <= 0:
        raise ValidationError(
            "DQV source-target resolution rate requires a positive denominator"
        )
    resolution_rate = (
        Decimal(resolved_targets) / Decimal(target_denominator)
    ).quantize(Decimal("0.000000000001"))

    graph = Graph()
    graph.bind("dcat", DCAT)
    graph.bind("dcterms", DCTERMS)
    graph.bind("dqv", DQV)
    graph.bind("omaro", OMARO_NS)
    graph.bind("prov", PROV)
    graph.bind("skos", SKOS)
    graph.bind("xsd", XSD)
    graph.add((dataset_uri, RDF.type, DCAT.Dataset))
    graph.add((software_agent, RDF.type, PROV.SoftwareAgent))
    graph.add(
        (
            software_agent,
            RDFS.label,
            Literal("OMARO deterministic release builder", lang="en"),
        )
    )
    graph.add((software_agent, DCTERMS.identifier, Literal("omaro.builder")))
    graph.add(
        (
            software_agent,
            SCHEMA.softwareVersion,
            Literal(dataset.metadata["dataset_version"]),
        )
    )

    dimensions = {
        "source-resolution": (
            "source target resolution",
            "Completeness of source instrument targets resolved to public OMARO identifiers.",
        ),
        "automated-quality-control": (
            "automated quality control",
            "Counts and outcomes produced by deterministic machine checks; these are review signals, not domain or cultural validation.",
        ),
        "review-activity": (
            "review activity",
            "Recorded human or community review events in the canonical release dataset.",
        ),
    }
    dimension_uris: dict[str, URIRef] = {}
    for code, (label, definition) in dimensions.items():
        dimension_uri = OMARO_NS[f"quality-dimension-{code}"]
        dimension_uris[code] = dimension_uri
        graph.add((dimension_uri, RDF.type, DQV.Dimension))
        graph.add((dimension_uri, SKOS.prefLabel, Literal(label, lang="en")))
        graph.add((dimension_uri, SKOS.definition, Literal(definition, lang="en")))
        graph.add((dimension_uri, RDFS.isDefinedBy, ontology_uri))

    measurements: dict[str, URIRef] = {}

    def add_measurement(
        code: str,
        label: str,
        definition: str,
        expected_datatype: URIRef,
        value: Literal,
        dimension_code: str,
    ) -> URIRef:
        metric_uri = OMARO_NS[f"quality-metric-{code}"]
        measurement_uri = URIRef(f"{dataset_uri}#quality-measurement-{code}")
        measurements[code] = measurement_uri
        graph.add((metric_uri, RDF.type, DQV.Metric))
        graph.add((metric_uri, SKOS.prefLabel, Literal(label, lang="en")))
        graph.add((metric_uri, SKOS.definition, Literal(definition, lang="en")))
        graph.add((metric_uri, DQV.expectedDataType, expected_datatype))
        graph.add((metric_uri, DQV.inDimension, dimension_uris[dimension_code]))
        graph.add((metric_uri, RDFS.isDefinedBy, ontology_uri))
        graph.add((measurement_uri, RDF.type, DQV.QualityMeasurement))
        graph.add((measurement_uri, DQV.computedOn, dataset_uri))
        graph.add((measurement_uri, DQV.isMeasurementOf, metric_uri))
        graph.add((measurement_uri, DQV.value, value))
        graph.add((measurement_uri, PROV.wasAttributedTo, software_agent))
        graph.add((measurement_uri, PROV.generatedAtTime, generated_at))
        graph.add((dataset_uri, DQV.hasQualityMeasurement, measurement_uri))
        return measurement_uri

    add_measurement(
        "resolved-source-target-count",
        "resolved source target count",
        "Number of source instrument targets resolved to public OMARO identifiers in this release.",
        XSD.integer,
        Literal(resolved_targets, datatype=XSD.integer),
        "source-resolution",
    )
    add_measurement(
        "unresolved-source-target-count",
        "unresolved source target count",
        "Number of source instrument targets retained as unresolved stubs in this release.",
        XSD.integer,
        Literal(unresolved_targets, datatype=XSD.integer),
        "source-resolution",
    )
    add_measurement(
        "source-target-resolution-denominator",
        "source target resolution denominator",
        "Total known source instrument targets in this release: resolved targets plus unresolved stubs.",
        XSD.integer,
        Literal(target_denominator, datatype=XSD.integer),
        "source-resolution",
    )
    rate_measurement = add_measurement(
        "source-target-resolution-rate",
        "source target resolution rate",
        "Resolved source instrument targets divided by the source target resolution denominator, rounded to twelve decimal places.",
        XSD.decimal,
        Literal(format(resolution_rate, "f"), datatype=XSD.decimal),
        "source-resolution",
    )
    graph.add(
        (
            rate_measurement,
            PROV.wasDerivedFrom,
            measurements["resolved-source-target-count"],
        )
    )
    graph.add(
        (
            rate_measurement,
            PROV.wasDerivedFrom,
            measurements["source-target-resolution-denominator"],
        )
    )

    findings_total_measurement = add_measurement(
        "automated-finding-count-total",
        "automated finding count, total",
        "Total deterministic quality-rule findings recorded as review signals; the count is not a validation decision.",
        XSD.integer,
        Literal(int(quality_report["quality_findings"]), datatype=XSD.integer),
        "automated-quality-control",
    )
    for rule_code, count in sorted(quality_report["quality_findings_by_rule"].items()):
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", rule_code):
            raise ValidationError(
                f"quality rule code is not suitable for a stable metric URI: {rule_code}"
            )
        rule_measurement = add_measurement(
            f"automated-finding-count-{rule_code}",
            f"automated finding count for {rule_code}",
            f"Number of deterministic review-signal findings emitted by quality rule {rule_code}; this is not a validation decision.",
            XSD.integer,
            Literal(int(count), datatype=XSD.integer),
            "automated-quality-control",
        )
        graph.add((findings_total_measurement, PROV.wasDerivedFrom, rule_measurement))

    add_measurement(
        "review-event-count",
        "review event count",
        "Number of recorded human or community review events in this release; zero means none are recorded, not that review is unnecessary.",
        XSD.integer,
        Literal(int(quality_report["review_events"]), datatype=XSD.integer),
        "review-activity",
    )
    add_measurement(
        "canonical-validation-passed",
        "canonical validation passed",
        "Whether canonical input, cross-record integrity, generated RDF, and machine validation gates passed for this build. This does not establish organological, linguistic, community, or cultural validity.",
        XSD.boolean,
        Literal(canonical_validation_passed, datatype=XSD.boolean),
        "automated-quality-control",
    )

    (output / "metadata" / "dqv.ttl").write_text(
        graph.serialize(format="turtle"), encoding="utf-8", newline="\n"
    )


def _legacy_exports(dataset: Dataset) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    concepts = dataset.concepts_by_uri
    labels = dataset.labels_by_concept
    preferred: dict[tuple[str, str], str] = {}
    for rows in labels.values():
        for row in rows:
            if row["label_type"] == "preferred":
                preferred[(row["concept_uri"], row["language"])] = row["label"]
    mappings: dict[str, list[str]] = defaultdict(list)
    for assertion in dataset.classification_assertions:
        if assertion["assertion_origin"] != "source-derived":
            continue
        target = concepts[assertion["target_uri"]]
        label = preferred.get((target["uri"], "en"))
        mappings[assertion["classification_uri"]].append(
            label or f"instrumentskeywords:{target['mimo_id']}"
        )

    classifications: dict[str, Any] = {}
    for concept in sorted(
        (row for row in dataset.concepts if row["kind"] == "classification"),
        key=lambda row: row["notation"],
    ):
        classifications[concept["notation"]] = {
            "Label": preferred[(concept["uri"], "en")],
            "Instruments": sorted(set(mappings[concept["uri"]])),
            "Description": concept.get("definition", ""),
            "MIMOPage": concept["mimo_id"],
        }

    translations: list[dict[str, Any]] = []
    for concept in dataset.concepts:
        if (
            concept["kind"] != "instrument"
            or concept["resolution_status"] != "resolved"
        ):
            continue
        translations_map = {
            row["language"]: row["label"]
            for row in labels[concept["uri"]]
            if row["label_type"] == "preferred"
        }
        translations.append(
            {
                "Label": translations_map.get("en")
                or next(iter(sorted(translations_map.values()))),
                "Translations": dict(sorted(translations_map.items())),
                "MIMOPage": concept["mimo_id"],
            }
        )
    translations.sort(key=lambda row: (row["Label"], row["MIMOPage"]))
    return classifications, translations


def _quality_report(
    dataset: Dataset, summary: dict[str, Any]
) -> tuple[dict[str, Any], str]:
    labels = dataset.labels_by_concept
    english_labels = Counter(
        row["label"]
        for row in dataset.labels
        if row["label_type"] == "preferred" and row["language"] == "en"
    )
    mapped_classes = Counter(
        row["classification_uri"]
        for row in dataset.classification_assertions
        if row["stance"] not in {"rejected", "superseded"}
    )
    mappings_by_instrument = Counter(
        row["target_uri"]
        for row in dataset.classification_assertions
        if row["stance"] not in {"rejected", "superseded"}
    )
    unresolved = [
        row for row in dataset.concepts if row["resolution_status"] == "unresolved"
    ]
    label_types = Counter(row["label_type"] for row in dataset.labels)
    relation_types = Counter(row["predicate_uri"] for row in dataset.source_relations)
    classification_stances = Counter(
        row["stance"] for row in dataset.classification_assertions
    )
    label_assertion_review_statuses = Counter(
        row["review_status"] for row in dataset.label_assertions
    )
    note_assertion_review_statuses = Counter(
        row["review_status"] for row in dataset.note_assertions
    )
    quality_findings_by_rule = Counter(
        row["rule_code"] for row in dataset.quality_findings
    )
    language_tag_statuses = Counter(
        row["language_tag_status"] for row in dataset.label_assertions
    )
    translation_statuses = Counter(
        row["translation_status"] for row in dataset.label_profiles
    )
    observed_script_combinations = Counter(
        "+".join(row["observed_script_codes"]) or "none"
        for row in dataset.label_profiles
    )
    lexical_roles: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in dataset.labels:
        lexical_roles[(row["concept_uri"], row["language"], row["label"])].add(
            row["label_type"]
        )
    cross_type_lexical_collisions = sum(
        "preferred" in roles and bool(roles & {"alternative", "hidden"})
        for roles in lexical_roles.values()
    )
    missing_by_language: dict[str, int] = {}
    resolved_instruments = [
        row
        for row in dataset.concepts
        if row["kind"] == "instrument" and row["resolution_status"] == "resolved"
    ]
    languages = sorted(summary["languages"])
    for language in languages:
        missing_by_language[language] = sum(
            not any(
                label["language"] == language and label["label_type"] == "preferred"
                for label in labels[row["uri"]]
            )
            for row in resolved_instruments
        )
    report = {
        **summary,
        "baseline": {"classifications": 643, "resolved_instruments": 2724},
        "baseline_matches": {
            "classifications": summary["classifications"] == 643,
            "resolved_instruments": summary["instruments"] == 2724,
        },
        "classifications_without_instruments": sum(
            not mapped_classes[row["uri"]]
            for row in dataset.concepts
            if row["kind"] == "classification"
        ),
        "resolved_instruments_without_classifications": sum(
            not mappings_by_instrument[row["uri"]] for row in resolved_instruments
        ),
        "resolved_instruments_with_multiple_classifications": sum(
            mappings_by_instrument[row["uri"]] > 1 for row in resolved_instruments
        ),
        "maximum_classifications_per_resolved_instrument": max(
            (mappings_by_instrument[row["uri"]] for row in resolved_instruments),
            default=0,
        ),
        "duplicate_english_labels": sum(
            count - 1 for count in english_labels.values() if count > 1
        ),
        "preferred_nonpreferred_lexical_collisions": cross_type_lexical_collisions,
        "label_types": dict(sorted(label_types.items())),
        "relation_types": dict(sorted(relation_types.items())),
        "classification_stances": dict(sorted(classification_stances.items())),
        "label_assertion_review_statuses": dict(
            sorted(label_assertion_review_statuses.items())
        ),
        "note_assertion_review_statuses": dict(
            sorted(note_assertion_review_statuses.items())
        ),
        "quality_findings_by_rule": dict(sorted(quality_findings_by_rule.items())),
        "language_tag_statuses": dict(sorted(language_tag_statuses.items())),
        "translation_statuses": dict(sorted(translation_statuses.items())),
        "observed_script_combinations": dict(
            sorted(observed_script_combinations.items())
        ),
        "profiles_with_explicit_script": sum(
            row["explicit_script_subtag"] is not None for row in dataset.label_profiles
        ),
        "profiles_with_language_variety": sum(
            row["language_variety_uri"] is not None for row in dataset.label_profiles
        ),
        "profiles_with_transliteration_system": sum(
            row["transliteration_system_uri"] is not None
            for row in dataset.label_profiles
        ),
        "profiles_with_term_roles": sum(
            bool(row["term_roles"]) for row in dataset.label_profiles
        ),
        "concepts_with_created_date": sum(
            bool(row.get("created")) for row in dataset.concepts
        ),
        "missing_preferred_labels_by_language": missing_by_language,
        "unresolved_concepts": [row["uri"] for row in unresolved],
    }
    language_markdown = "\n".join(
        f"| `{language}` | {len(resolved_instruments) - missing} | {missing} |"
        for language, missing in missing_by_language.items()
    )
    audit_markdown = "\n".join(
        f"| `{code}` | {count} |"
        for code, count in report["quality_findings_by_rule"].items()
    )
    markdown = (
        f"""# Dataset quality report

Dataset version: `{dataset.metadata["dataset_version"]}`
Source retrieved: `{dataset.metadata["source_retrieved_at"]}`

| Metric | Value |
|---|---:|
| Classifications | {report["classifications"]} |
| Resolved instruments | {report["instruments"]} |
| Unresolved instrument stubs | {report["unresolved_stubs"]} |
| Preferred labels | {report["label_types"].get("preferred", 0)} |
| Alternative labels | {report["label_types"].get("alternative", 0)} |
| Assertion-scoped SKOS-XL label resources | {report["label_resources"]} |
| Conservative linguistic label profiles | {report["label_profiles"]} |
| Unicode Script registry snapshots | {report["script_registries"]} |
| Profiles with explicit BCP 47 script | {report["profiles_with_explicit_script"]} |
| Profiles with recorded language variety | {report["profiles_with_language_variety"]} |
| Profiles with recorded transliteration system | {report["profiles_with_transliteration_system"]} |
| Profiles with reviewed term roles | {report["profiles_with_term_roles"]} |
| Qualified label assertions | {report["label_assertions"]} |
| Unreviewed label assertions | {report["label_assertion_review_statuses"].get("unreviewed", 0)} |
| Qualified note assertions | {report["note_assertions"]} |
| Unreviewed note assertions | {report["note_assertion_review_statuses"].get("unreviewed", 0)} |
| Registered agents | {report["agents"]} |
| Versioned source records | {report["source_records"]} |
| Review statuses | {report["review_statuses"]} |
| Automated quality findings | {report["quality_findings"]} |
| Human/community review events | {report["review_events"]} |
| Registered perspectives | {report["perspectives"]} |
| Registered applicability scopes | {report["applicability_scopes"]} |
| Registered authority assignments | {report["authority_assignments"]} |
| Projection policies | {report["projection_policies"]} |
| IANA language-registry snapshots | {report["language_registries"]} |
| MIMO source relations | {report["source_relations"]} |
| Source-derived classification assertions | {report["classification_assertions"]} |
| Source-asserted classification assignments | {report["classification_stances"].get("source-asserted", 0)} |
| Qualified concept-relation assertions | {report["concept_relation_assertions"]} |
| Instrument hierarchy source relations | {sum(row["predicate_uri"] == BROADER and dataset.concepts_by_uri[row["subject_uri"]]["kind"] == "instrument" for row in dataset.source_relations)} |
| Concepts with source creation date | {report["concepts_with_created_date"]} |
| Classifications without classified instruments | {report["classifications_without_instruments"]} |
| Resolved instruments without classifications | {report["resolved_instruments_without_classifications"]} |
| Resolved instruments with multiple classifications | {report["resolved_instruments_with_multiple_classifications"]} |
| Maximum classifications on one resolved instrument | {report["maximum_classifications_per_resolved_instrument"]} |
| Duplicate English label occurrences | {report["duplicate_english_labels"]} |
| Source lexical forms asserted as both preferred and non-preferred | {report["preferred_nonpreferred_lexical_collisions"]} |

Both migration baselines match: **{all(report["baseline_matches"].values())}**.

MIMO's `skos:exactMatch` mappings are preserved only in the explicit source
layer. The project-facing classification assignments use `omaro:classifiedAs`,
retain their source predicate, source perspective, evidence, and an explicit
`source-silent` applicability scope. Source silence is not context-independent
validity. These source claims remain qualified occurrences and do not become
direct project assertions without explicit policy membership, an eligible
stance, a context-independent scope, independent authorized referential and
scholarly acceptances, and the absence of an active veto.

Every compatibility label and source definition now has a stable qualified
assertion linked to an agent, a versioned source record, and a review-status
resource. These records preserve source evidence; `unreviewed` does not imply
linguistic, community, or scholarly acceptance.

Every label resource also has a conservative linguistic profile. Declared BCP
47 components are kept distinct from Unicode Script observations made against
the pinned Unicode `{dataset.script_registries[0]["unicode_version"]}` data.
Missing variety, writing-system, transliteration, community, place, period,
usage-domain, pronunciation, audio, and term-role evidence remains explicitly
empty; the pipeline does not infer it.

## Automated linguistic and documentation audit

| Rule | Open findings |
|---|---:|
{audit_markdown}

All findings are deterministic review signals with `review_effect: none`.
They do not establish that a label is wrong and do not change assertion review
status. Script mismatch may indicate a valid transliteration, loanword, exonym,
or translingual form. Human or community review must record evidence,
perspective, authority, and contextual applicability in a review event.

The language-tag gate uses the vendored IANA registry dated
`{dataset.language_registries[0]["file_date"]}`. Submitted tags are retained
separately from canonical tags. The legacy MIMO `dk` value is explicitly
recorded as invalid source metadata normalized by the project to registered
language tag `da`; this technical normalization does not validate the label.

Cross-type lexical collisions are retained because they are present in MIMO's
native RDF. They are reported for review rather than silently discarded.

## Preferred-label coverage for resolved instruments

| Language | Present | Missing |
|---|---:|---:|
{language_markdown}

## Unresolved source targets

"""
        + ("\n".join(f"- `{uri}`" for uri in report["unresolved_concepts"]) or "None")
        + "\n"
    )
    return report, markdown


def build(
    repo_root: Path, canonical_dir: Path, output: Path, schema_dir: Path
) -> dict[str, Any]:
    dataset = Dataset.load(canonical_dir)
    summary = dataset.validate(schema_dir)
    dataset.assert_publication_authorized()
    if output.exists():
        shutil.rmtree(output)
    (output / "jsonl").mkdir(parents=True)
    for name in (
        "concept_schemes.jsonl",
        "agents.jsonl",
        "perspectives.jsonl",
        "applicability_scopes.jsonl",
        "authority_assignments.jsonl",
        "projection_policies.jsonl",
        "source_records.jsonl",
        "review_statuses.jsonl",
        "language_registries.jsonl",
        "script_registries.jsonl",
        "quality_rules.jsonl",
        "quality_findings.jsonl",
        "review_events.jsonl",
        "concepts.jsonl",
        "labels.jsonl",
        "label_resources.jsonl",
        "label_profiles.jsonl",
        "label_assertions.jsonl",
        "note_assertions.jsonl",
        "source_relations.jsonl",
        "classification_assertions.jsonl",
        "concept_relation_assertions.jsonl",
        "organological_targets.jsonl",
        "classification_criteria.jsonl",
        "observation_assessments.jsonl",
        "classification_expressions.jsonl",
        "protocol_applications.jsonl",
        "use_decisions.jsonl",
        "metadata.json",
    ):
        shutil.copy2(canonical_dir / name, output / "jsonl" / name)
    (output / "metadata").mkdir(parents=True, exist_ok=True)
    registry_artifact = (
        canonical_dir.parent / dataset.language_registries[0]["artifact_path"]
    )
    shutil.copy2(
        registry_artifact,
        output / "metadata" / "iana-language-subtag-registry.json",
    )
    script_registry_artifact = (
        canonical_dir.parent / dataset.script_registries[0]["artifact_path"]
    )
    shutil.copy2(
        script_registry_artifact,
        output / "metadata" / "unicode-script-registry.json",
    )
    rag_records = build_rag_jsonl(dataset, output / "jsonl" / "rag-concepts.jsonl")
    knowledge_summary = {
        "rag_records": rag_records,
        **build_okf(dataset, output),
    }

    _write_csv(
        output / "csv" / "agents.csv",
        ["uri", "agent_type", "name", "resource_uri"],
        sorted(dataset.agents, key=lambda row: row["uri"]),
    )
    _write_csv(
        output / "csv" / "concept-schemes.csv",
        [
            "uri",
            "label",
            "scheme_type",
            "version",
            "version_uri",
            "publisher_agent_uri",
            "perspective_uri",
            "applicability_scope_uris_json",
            "authority_assignment_uris_json",
            "protocol_application_uris_json",
            "source_record_uri",
            "governance_uri",
            "rights_uri",
            "status",
            "scope_note",
        ],
        sorted(dataset.concept_schemes, key=lambda row: row["uri"]),
    )
    _write_csv(
        output / "csv" / "perspectives.csv",
        [
            "uri",
            "label",
            "perspective_type",
            "holder_agent_uri",
            "represented_community_uris_json",
            "description",
            "status",
            "valid_from",
            "valid_until",
            "authority_assignment_uris_json",
        ],
        [
            {
                **row,
                "represented_community_uris_json": json.dumps(
                    row["represented_community_uris"], sort_keys=True
                ),
                "authority_assignment_uris_json": json.dumps(
                    row["authority_assignment_uris"], sort_keys=True
                ),
            }
            for row in sorted(dataset.perspectives, key=lambda row: row["uri"])
        ],
    )
    scope_array_fields = (
        "community_uris",
        "place_uris",
        "period_uris",
        "usage_domain_uris",
        "playing_technique_uris",
        "instrument_configuration_uris",
        "language_variety_uris",
    )
    _write_csv(
        output / "csv" / "applicability-scopes.csv",
        [
            "uri",
            "label",
            "scope_mode",
            "description",
            *(f"{field}_json" for field in scope_array_fields),
            "temporal_start",
            "temporal_end",
            "asserted_by_uri",
            "perspective_uri",
            "source_record_uri",
        ],
        [
            {
                **row,
                **{
                    f"{field}_json": json.dumps(row[field], sort_keys=True)
                    for field in scope_array_fields
                },
            }
            for row in sorted(dataset.applicability_scopes, key=lambda row: row["uri"])
        ],
    )
    _write_csv(
        output / "csv" / "projection-policies.csv",
        [
            "uri",
            "label",
            "description",
            "graph_role",
            "direct_assertion",
            "eligible_stances_json",
            "review_requirements_json",
            "minimum_independent_reviewers",
            "veto_rules_json",
            "context_match_required",
            "unknown_scope_behavior",
            "includes_source_layer",
            "policy_version",
        ],
        [
            {
                **row,
                "eligible_stances_json": json.dumps(
                    row["eligible_stances"], sort_keys=True
                ),
                "review_requirements_json": json.dumps(
                    row["review_requirements"], sort_keys=True
                ),
                "veto_rules_json": json.dumps(row["veto_rules"], sort_keys=True),
            }
            for row in sorted(dataset.projection_policies, key=lambda row: row["uri"])
        ],
    )
    _write_csv(
        output / "csv" / "authority-assignments.csv",
        [
            "uri",
            "agent_uri",
            "represented_community_uri",
            "authority_role",
            "authority_basis_uri",
            "conferred_by_agent_uri",
            "subject_matter_uris_json",
            "covered_validation_dimensions_json",
            "covered_action_uris_json",
            "applicability_scope_uris_json",
            "valid_from",
            "valid_until",
            "delegation_permitted",
            "status",
            "revocation_event_uri",
            "revocation_effect",
            "rights_uri",
            "evidence_json",
        ],
        [
            {
                **row,
                "subject_matter_uris_json": json.dumps(
                    row["subject_matter_uris"], sort_keys=True
                ),
                "covered_validation_dimensions_json": json.dumps(
                    row["covered_validation_dimensions"], sort_keys=True
                ),
                "covered_action_uris_json": json.dumps(
                    row["covered_action_uris"], sort_keys=True
                ),
                "applicability_scope_uris_json": json.dumps(
                    row["applicability_scope_uris"], sort_keys=True
                ),
                "evidence_json": json.dumps(
                    row["evidence"], ensure_ascii=False, sort_keys=True
                ),
            }
            for row in sorted(dataset.authority_assignments, key=lambda row: row["uri"])
        ],
    )
    _write_csv(
        output / "csv" / "source-records.csv",
        [
            "uri",
            "resource_uri",
            "title",
            "source_type",
            "scheme_uri",
            "publisher_agent_uri",
            "layer",
            "rights_uri",
            "retrieved_at",
        ],
        sorted(dataset.source_records, key=lambda row: row["uri"]),
    )
    _write_csv(
        output / "csv" / "review-statuses.csv",
        ["uri", "code", "label", "description"],
        sorted(dataset.review_statuses, key=lambda row: row["uri"]),
    )
    _write_csv(
        output / "csv" / "language-registries.csv",
        [
            "uri",
            "registry_type",
            "file_date",
            "source_uri",
            "artifact_path",
            "sha256",
            "profile_uri",
            "normalization_overrides",
        ],
        [
            {
                **row,
                "normalization_overrides": json.dumps(
                    row["normalization_overrides"], sort_keys=True
                ),
            }
            for row in dataset.language_registries
        ],
    )
    _write_csv(
        output / "csv" / "script-registries.csv",
        [
            "uri",
            "registry_type",
            "unicode_version",
            "source_uris_json",
            "artifact_path",
            "sha256",
            "profile_uri",
        ],
        [
            {
                **row,
                "source_uris_json": json.dumps(row["source_uris"], sort_keys=True),
            }
            for row in dataset.script_registries
        ],
    )
    _write_csv(
        output / "csv" / "quality-rules.csv",
        [
            "uri",
            "code",
            "validation_dimension",
            "severity",
            "title",
            "description",
            "assessment_method",
            "review_effect",
        ],
        sorted(dataset.quality_rules, key=lambda row: row["uri"]),
    )
    _write_csv(
        output / "csv" / "quality-findings.csv",
        [
            "uri",
            "rule_uri",
            "rule_code",
            "target_assertion_uri",
            "concept_uri",
            "detected_by_uri",
            "detected_at",
            "assessment_method",
            "validation_dimension",
            "severity",
            "review_effect",
            "human_review_required",
            "applies_to_json",
            "evidence_json",
        ],
        [
            {
                **row,
                "applies_to_json": json.dumps(
                    row["applies_to"], ensure_ascii=False, sort_keys=True
                ),
                "evidence_json": json.dumps(
                    row["evidence"], ensure_ascii=False, sort_keys=True
                ),
            }
            for row in sorted(dataset.quality_findings, key=lambda row: row["uri"])
        ],
    )
    _write_csv(
        output / "csv" / "review-events.csv",
        [
            "uri",
            "target_assertion_uri",
            "reviewer_agent_uri",
            "reviewer_authority",
            "authority_assignment_uris_json",
            "review_method",
            "validation_dimension",
            "outcome",
            "reviewed_at",
            "valid_until",
            "perspective_uri",
            "represented_community_uris_json",
            "applicability_scope_uris_json",
            "evidence_json",
            "rationale",
            "rights_uri",
            "supersedes_decision_uri",
            "suspends_decision_uri",
            "reinstates_decision_uri",
            "decision_status",
            "projection_policy_uris_json",
        ],
        [
            {
                **row,
                "represented_community_uris_json": json.dumps(
                    row["represented_community_uris"], sort_keys=True
                ),
                "authority_assignment_uris_json": json.dumps(
                    row["authority_assignment_uris"], sort_keys=True
                ),
                "applicability_scope_uris_json": json.dumps(
                    row["applicability_scope_uris"], sort_keys=True
                ),
                "evidence_json": json.dumps(
                    row["evidence"], ensure_ascii=False, sort_keys=True
                ),
                "projection_policy_uris_json": json.dumps(
                    row["projection_policy_uris"], sort_keys=True
                ),
            }
            for row in sorted(dataset.review_events, key=lambda row: row["uri"])
        ],
    )
    _write_csv(
        output / "csv" / "organological-targets.csv",
        [
            "uri",
            "label",
            "target_kind",
            "realizes_instrument_concept_uris_json",
            "configuration_of_uri",
            "component_of_uri",
            "component_role_uri",
            "has_component_uris_json",
            "has_functional_module_uris_json",
            "condition_state_of_uri",
            "valid_from",
            "valid_until",
            "generated_by_event_uri",
            "ended_by_event_uri",
            "performance_event_uri",
            "actual_playing_technique_uris_json",
            "intended_playing_technique_uris_json",
            "source_record_uri",
            "perspective_uri",
            "applicability_scope_uris_json",
            "rights_uri",
            "protocol_application_uris_json",
            "authority_assignment_uris_json",
        ],
        _csv_json_rows(
            dataset.organological_targets,
            (
                "realizes_instrument_concept_uris",
                "has_component_uris",
                "has_functional_module_uris",
                "actual_playing_technique_uris",
                "intended_playing_technique_uris",
                "applicability_scope_uris",
                "protocol_application_uris",
                "authority_assignment_uris",
            ),
        ),
    )
    _write_csv(
        output / "csv" / "classification-criteria.csv",
        [
            "uri",
            "label",
            "description",
            "criterion_type",
            "observable_property_uris_json",
            "procedure_uris_json",
            "classification_scheme_uri",
            "scheme_version_uri",
            "conclusion_classification_uris_json",
            "inference_logic_uri",
            "asserted_by_uri",
            "perspective_uri",
            "source_record_uri",
            "applicability_scope_uris_json",
            "authority_assignment_uris_json",
            "protocol_application_uris_json",
            "evidence_json",
            "rights_uri",
            "status",
        ],
        _csv_json_rows(
            dataset.classification_criteria,
            (
                "observable_property_uris",
                "procedure_uris",
                "conclusion_classification_uris",
                "evidence",
                "applicability_scope_uris",
                "authority_assignment_uris",
                "protocol_application_uris",
            ),
        ),
    )
    _write_csv(
        output / "csv" / "observation-assessments.csv",
        [
            "uri",
            "feature_of_interest_uri",
            "assessed_part_uri",
            "assessed_property_uri",
            "assessment_status",
            "result_json",
            "assessment_procedure_uri",
            "assessment_agent_uri",
            "assessment_sensor_uri",
            "phenomenon_start",
            "phenomenon_end",
            "assessment_time",
            "perspective_uri",
            "applicability_scope_uris_json",
            "source_record_uri",
            "evidence_json",
            "rights_uri",
            "protocol_application_uris_json",
            "authority_assignment_uris_json",
            "review_status",
            "review_status_uri",
        ],
        _csv_json_rows(
            dataset.observation_assessments,
            (
                "result",
                "applicability_scope_uris",
                "evidence",
                "protocol_application_uris",
                "authority_assignment_uris",
            ),
        ),
    )
    _write_csv(
        output / "csv" / "classification-expressions.csv",
        [
            "uri",
            "source_concept_uri",
            "notation_literal",
            "notation_grammar_uri",
            "expression_scheme_version_uri",
            "combination_operator",
            "members_json",
            "shared_suffix_notation",
            "parse_status",
            "perspective_uri",
            "applicability_scope_uris_json",
            "source_record_uri",
            "evidence_json",
            "authority_assignment_uris_json",
            "protocol_application_uris_json",
            "rights_uri",
        ],
        _csv_json_rows(
            dataset.classification_expressions,
            (
                "members",
                "applicability_scope_uris",
                "evidence",
                "authority_assignment_uris",
                "protocol_application_uris",
            ),
        ),
    )
    _write_csv(
        output / "csv" / "protocol-applications.csv",
        [
            "uri",
            "target_resource_uris_json",
            "protocol_uri",
            "protocol_type_uri",
            "issued_by_agent_uri",
            "applied_by_agent_uri",
            "represented_community_uris_json",
            "authority_assignment_uris_json",
            "source_record_uri",
            "applicability_scope_uris_json",
            "enforcement_mode",
            "status",
            "valid_from",
            "valid_until",
            "supersedes_uri",
            "retrieved_at",
            "resolution_status",
            "integrity_verification_method",
            "protocol_artifact_path",
            "integrity_attestation_uri",
            "protocol_integrity_sha256",
        ],
        _csv_json_rows(
            dataset.protocol_applications,
            (
                "target_resource_uris",
                "represented_community_uris",
                "authority_assignment_uris",
                "applicability_scope_uris",
            ),
        ),
    )
    _write_csv(
        output / "csv" / "use-decisions.csv",
        [
            "uri",
            "target_resource_uris_json",
            "action_uris_json",
            "purpose_uris_json",
            "audience_uris_json",
            "decision",
            "decided_by_agent_uri",
            "represented_community_uris_json",
            "authority_assignment_uris_json",
            "protocol_application_uris_json",
            "applicability_scope_uris_json",
            "decision_method_uri",
            "decided_at",
            "valid_until",
            "status",
            "supersedes_decision_uri",
            "public_evidence_uri",
            "public_summary",
            "legal_basis_uris_json",
            "legal_basis_status",
            "legal_basis_assessed_by_agent_uri",
            "consent_record_uris_json",
            "consent_status",
            "consent_assessed_by_agent_uri",
        ],
        _csv_json_rows(
            dataset.use_decisions,
            (
                "target_resource_uris",
                "action_uris",
                "purpose_uris",
                "audience_uris",
                "represented_community_uris",
                "authority_assignment_uris",
                "protocol_application_uris",
                "applicability_scope_uris",
                "legal_basis_uris",
                "consent_record_uris",
            ),
        ),
    )
    _write_csv(
        output / "csv" / "concepts.csv",
        [
            "uri",
            "scheme_uri",
            "kind",
            "local_id",
            "mimo_id",
            "notation",
            "definition",
            "created",
            "resolution_status",
        ],
        sorted(dataset.concepts, key=lambda row: row["uri"]),
    )
    _write_csv(
        output / "csv" / "labels.csv",
        ["concept_uri", "language", "submitted_language", "label_type", "label"],
        sorted(
            dataset.labels,
            key=lambda row: (
                row["concept_uri"],
                row["language"],
                row["label_type"],
                row["label"],
            ),
        ),
    )
    _write_csv(
        output / "csv" / "label-assertions.csv",
        [
            "uri",
            "concept_uri",
            "predicate_uri",
            "literal_form",
            "normalized_form",
            "language_tag",
            "submitted_language_tag",
            "language_tag_status",
            "language_registry_uri",
            "label_resource_uri",
            "label_role",
            "skos_projection_status",
            "asserted_by_uri",
            "source_record_uri",
            "source_uri",
            "assertion_origin",
            "review_status",
            "review_status_uri",
        ],
        sorted(dataset.label_assertions, key=lambda row: row["uri"]),
    )
    _write_csv(
        output / "csv" / "label-resources.csv",
        [
            "uri",
            "literal_form",
            "normalized_form",
            "language_tag",
            "language_registry_uri",
        ],
        sorted(dataset.label_resources, key=lambda row: row["uri"]),
    )
    _write_csv(
        output / "csv" / "label-profiles.csv",
        [
            "uri",
            "label_resource_uri",
            "source_label_assertion_uri",
            "language_tag",
            "primary_language_subtag",
            "explicit_script_subtag",
            "default_script_subtag",
            "region_subtag",
            "variant_subtags_json",
            "extension_subtags_json",
            "private_use_subtags_json",
            "language_variety_uri",
            "writing_system_uri",
            "observed_script_codes_json",
            "has_common_or_inherited_characters",
            "script_observation_method",
            "script_registry_uri",
            "transliteration_system_uri",
            "transcription_system_uri",
            "pronunciations_json",
            "audio_uris_json",
            "term_roles_json",
            "translation_status",
            "applies_to_json",
            "display_policy",
            "search_policy",
            "asserted_by_uri",
            "source_record_uri",
            "assertion_origin",
            "review_status",
            "review_status_uri",
        ],
        [
            {
                **row,
                **{
                    f"{field}_json": json.dumps(
                        row[field], ensure_ascii=False, sort_keys=True
                    )
                    for field in (
                        "variant_subtags",
                        "extension_subtags",
                        "private_use_subtags",
                        "observed_script_codes",
                        "pronunciations",
                        "audio_uris",
                        "term_roles",
                        "applies_to",
                    )
                },
            }
            for row in sorted(dataset.label_profiles, key=lambda row: row["uri"])
        ],
    )
    _write_csv(
        output / "csv" / "note-assertions.csv",
        [
            "uri",
            "concept_uri",
            "predicate_uri",
            "literal_form",
            "normalized_form",
            "language_tag",
            "submitted_language_tag",
            "language_tag_status",
            "language_registry_uri",
            "asserted_by_uri",
            "source_record_uri",
            "source_uri",
            "assertion_origin",
            "review_status",
            "review_status_uri",
        ],
        sorted(dataset.note_assertions, key=lambda row: row["uri"]),
    )
    _write_csv(
        output / "csv" / "source-relations.csv",
        ["subject_uri", "predicate_uri", "object_uri", "source_uri"],
        sorted(
            dataset.source_relations,
            key=lambda row: (
                row["subject_uri"],
                row["predicate_uri"],
                row["object_uri"],
            ),
        ),
    )
    _write_csv(
        output / "csv" / "concept-relation-assertions.csv",
        [
            "uri",
            "subject_concept_uri",
            "predicate_uri",
            "object_concept_uri",
            "assigned_by_uri",
            "generated_by_uri",
            "perspective_uri",
            "relation_method_uri",
            "mapping_purpose_uris_json",
            "stance",
            "applicability_scope_uris_json",
            "evidence_json",
            "authority_assignment_uris_json",
            "valid_from",
            "valid_until",
            "projection_policy_uris_json",
            "source_record_uri",
            "assertion_origin",
        ],
        [
            {
                **row,
                "applicability_scope_uris_json": json.dumps(
                    row["applicability_scope_uris"], sort_keys=True
                ),
                "authority_assignment_uris_json": json.dumps(
                    row["authority_assignment_uris"], sort_keys=True
                ),
                "mapping_purpose_uris_json": json.dumps(
                    row["mapping_purpose_uris"], sort_keys=True
                ),
                "evidence_json": json.dumps(
                    row["evidence"], ensure_ascii=False, sort_keys=True
                ),
                "projection_policy_uris_json": json.dumps(
                    row["projection_policy_uris"], sort_keys=True
                ),
            }
            for row in sorted(
                dataset.concept_relation_assertions, key=lambda row: row["uri"]
            )
        ],
    )
    _write_csv(
        output / "csv" / "classification-assignments.csv",
        [
            "assertion_uri",
            "assignment_uri",
            "classification_uri",
            "classification_notation",
            "classification_label_en",
            "target_uri",
            "target_label_en",
            "target_resolution_status",
            "target_type",
            "classification_scheme_uri",
            "scheme_version_uri",
            "assertion_origin",
            "stance",
            "assigned_by_uri",
            "generated_by_uri",
            "perspective_uri",
            "classification_method_uri",
            "criteria_uris_json",
            "assessment_uris_json",
            "inference_logic_uri",
            "classification_expression_uri",
            "applicability_scope_uris_json",
            "evidence_json",
            "authority_assignment_uris_json",
            "valid_from",
            "valid_until",
            "projection_policy_uris_json",
            "source_record_uri",
            "source_predicate_uri",
            "source_uri",
        ],
        _classification_instrument_rows(dataset),
    )
    rdf_summary = _build_rdf(dataset, output, schema_dir)
    _build_sqlite(dataset, output / "sqlite" / "omaro.sqlite")
    _build_site(dataset, output, repo_root / "site")
    from omaro.compatibility import copy_historical_ontologies

    copy_historical_ontologies(repo_root / "site" / "compatibility", output)

    legacy_hs, legacy_translations = _legacy_exports(dataset)
    legacy_dir = output / "legacy"
    legacy_dir.mkdir(parents=True)
    hs_text = json.dumps(legacy_hs, ensure_ascii=False, indent=4) + "\n"
    translation_text = (
        json.dumps(legacy_translations, ensure_ascii=False, indent=4) + "\n"
    )
    (legacy_dir / "hornbostelSachs.json").write_text(
        hs_text, encoding="utf-8", newline="\n"
    )
    (legacy_dir / "translations.json").write_text(
        translation_text, encoding="utf-8", newline="\n"
    )
    (repo_root / "hornbostelSachs.json").write_text(
        hs_text, encoding="utf-8", newline="\n"
    )
    (repo_root / "translations.json").write_text(
        translation_text, encoding="utf-8", newline="\n"
    )

    shutil.copytree(schema_dir, output / "schema")
    report, report_markdown = _quality_report(dataset, {**summary, **rdf_summary})
    (output / "quality-report.json").write_text(
        canonical_json(report, indent=2), encoding="utf-8"
    )
    (output / "quality-report.md").write_text(report_markdown, encoding="utf-8")
    (repo_root / "QUALITY_REPORT.md").write_text(
        report_markdown, encoding="utf-8", newline="\n"
    )
    _build_fair_metadata(dataset, output, rdf_summary["triples"])
    _build_dqv_metadata(
        dataset,
        output,
        report,
        canonical_validation_passed=True,
    )

    files = sorted(path for path in output.rglob("*") if path.is_file())
    manifest = {
        "dataset_version": dataset.metadata["dataset_version"],
        "schema_version": dataset.metadata["schema_version"],
        "doi": dataset.metadata["doi"],
        "build_environment": {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
        },
        "files": [
            {
                "path": path.relative_to(output).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in files
        ],
        "counts": summary,
        "rdf": rdf_summary,
        "knowledge_exports": knowledge_summary,
    }
    (output / "manifest.json").write_text(
        canonical_json(manifest, indent=2), encoding="utf-8"
    )
    return {
        **summary,
        **rdf_summary,
        **knowledge_summary,
        "files": len(files) + 1,
    }


def _build_release_dcat_sidecar(
    metadata: dict[str, Any], archive: Path, sidecar: Path, version: str
) -> None:
    dataset_base_uri = URIRef(DATASET_BASE_URI)
    dataset_uri = URIRef(metadata["dataset_uri"])
    doi_uri = URIRef(f"https://doi.org/{metadata['doi']}")
    archive_uri = _release_archive_uri(version)
    distribution_uri = URIRef(f"{dataset_uri}#distribution-release-zip")
    checksum_uri = URIRef(f"{distribution_uri}-checksum-sha256")
    record_uri = URIRef(f"{dataset_uri}#catalog-record")
    generated_at = Literal(metadata["generated_at"], datatype=XSD.dateTime)
    archive_digest = sha256(archive)

    graph = Graph()
    graph.bind("dcat", DCAT)
    graph.bind("dcterms", DCTERMS)
    graph.bind("foaf", FOAF)
    graph.bind("spdx", SPDX)
    graph.bind("xsd", XSD)
    graph.add((dataset_base_uri, RDF.type, DCAT.Dataset))
    graph.add((dataset_base_uri, DCAT_NS.hasVersion, dataset_uri))
    graph.add((dataset_base_uri, DCAT_NS.hasCurrentVersion, dataset_uri))
    graph.add((dataset_uri, RDF.type, DCAT.Dataset))
    graph.add((dataset_uri, DCAT_NS.isVersionOf, dataset_base_uri))
    graph.add((dataset_uri, DCAT_NS.version, Literal(version)))
    graph.add((dataset_uri, DCTERMS.identifier, Literal(metadata["doi"])))
    graph.add((dataset_uri, DCTERMS.title, Literal(metadata["title"], lang="en")))
    graph.add((dataset_uri, DCTERMS.license, LICENSE_URI))
    graph.add((dataset_uri, DCAT.landingPage, doi_uri))
    graph.add((dataset_uri, DCAT.distribution, distribution_uri))
    graph.add((distribution_uri, RDF.type, DCAT.Distribution))
    graph.add((distribution_uri, DCAT.downloadURL, archive_uri))
    graph.add((distribution_uri, DCAT_NS.packageFormat, IANA_ZIP_MEDIA_TYPE))
    graph.add(
        (
            distribution_uri,
            DCAT.byteSize,
            Literal(archive.stat().st_size, datatype=XSD.nonNegativeInteger),
        )
    )
    graph.add((distribution_uri, DCTERMS.license, LICENSE_URI))
    graph.add((distribution_uri, SPDX.checksum, checksum_uri))
    graph.add((checksum_uri, RDF.type, SPDX.Checksum))
    graph.add((checksum_uri, SPDX.algorithm, SPDX.checksumAlgorithm_sha256))
    graph.add(
        (
            checksum_uri,
            SPDX.checksumValue,
            Literal(archive_digest, datatype=XSD.hexBinary),
        )
    )
    graph.add((record_uri, RDF.type, DCAT.CatalogRecord))
    graph.add((record_uri, FOAF.primaryTopic, dataset_uri))
    graph.add((record_uri, DCTERMS.conformsTo, DCAT_3_SPECIFICATION))
    graph.add((record_uri, DCTERMS.issued, generated_at))
    graph.add((record_uri, DCTERMS.modified, generated_at))
    sidecar.write_text(graph.serialize(format="turtle"), encoding="utf-8", newline="\n")


def package(repo_root: Path, output: Path, version: str) -> tuple[Path, Path]:
    archive = repo_root / f"omaro-v{version}.zip"
    sidecar = repo_root / f"omaro-v{version}.dcat.ttl"
    checksums = repo_root / "SHA256SUMS"
    metadata = json.loads((output / "jsonl" / "metadata.json").read_text())
    if metadata["dataset_version"] != version:
        raise ValidationError(
            "package version differs from the canonical dataset version"
        )
    if archive.exists():
        archive.unlink()
    source_files: list[tuple[Path, str]] = []
    for path in sorted(output.rglob("*")):
        if path.is_file():
            source_files.append(
                (
                    path,
                    f"omaro-v{version}/dist/{path.relative_to(output).as_posix()}",
                )
            )
    for name in (
        "README.md",
        "AUTHORS.md",
        "NOTICE",
        "VERSION",
        "codemeta.json",
        "LICENSE",
        "CITATION.cff",
        "CHANGELOG.md",
        "RELEASE_NOTES.md",
        "DATA_DICTIONARY.md",
        "NAMING_AND_IDENTITY.md",
        "ONTOLOGY_REFERENCE.md",
        "INFERENCE_AND_VALIDATION.md",
        "USE_CASES.md",
        "MULTIPERSPECTIVITY.md",
        "COMPETENCY_QUESTIONS.md",
        "DECOLONIAL_COMMITMENTS.md",
        "MODAVIS_VAO_INTEROPERABILITY.md",
        "EXTERNAL_REVIEW_DECISIONS.md",
        "IMPLEMENTATION_VERIFICATION.md",
        "PROVENANCE.md",
        "QUALITY_REPORT.md",
        "CORRECTIONS.md",
        "GOVERNANCE.md",
        "REVIEW_PROTOCOL.md",
        "W3ID_REGISTRATION.md",
        "RELATED_WORK.md",
        "CULTURAL_GOVERNANCE.md",
        "ORGANOLOGICAL_FOUNDATIONS.md",
        "ORGANOLOGICAL_MODEL.md",
        "INTEROPERABILITY_PROFILES.md",
    ):
        path = repo_root / name
        source_files.append((path, f"omaro-v{version}/{name}"))
    examples_root = repo_root / "examples"
    for path in sorted(examples_root.rglob("*")):
        if path.is_file():
            source_files.append(
                (
                    path,
                    f"omaro-v{version}/examples/"
                    f"{path.relative_to(examples_root).as_posix()}",
                )
            )

    with tempfile.TemporaryDirectory(prefix="omaro-release-") as directory:
        staging = Path(directory)
        for source, name in source_files:
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        release_root = staging / f"omaro-v{version}"
        write_ro_crate_metadata(
            release_root,
            metadata,
            release_date=(
                f"{ZIP_TIMESTAMP[0]:04d}-{ZIP_TIMESTAMP[1]:02d}-{ZIP_TIMESTAMP[2]:02d}"
            ),
        )
        with zipfile.ZipFile(
            archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as handle:
            for source in sorted(
                path for path in release_root.rglob("*") if path.is_file()
            ):
                name = source.relative_to(staging).as_posix()
                info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                handle.writestr(
                    info,
                    source.read_bytes(),
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
        if not (release_root / RO_CRATE_METADATA_NAME).is_file():
            raise ValidationError("RO-Crate metadata was not generated")
    _build_release_dcat_sidecar(metadata, archive, sidecar, version)
    checksum_artifacts = sorted((archive, sidecar), key=lambda path: path.name)
    checksums.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in checksum_artifacts),
        encoding="utf-8",
        newline="\n",
    )
    return archive, checksums
