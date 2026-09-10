from __future__ import annotations

import csv
import gc
import hashlib
import importlib.util
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.compare import IsomorphicGraph, to_isomorphic
from rdflib.namespace import DCAT, DCTERMS, OWL, RDF, RDFS, SKOS, VOID, XSD

from omaro.builder import _legacy_exports, build, package
from omaro.knowledge_exports import _validate_okf
from omaro.model import (
    BROADER,
    CLASSIFIED_AS,
    EXACT_MATCH,
    NARROWER,
    Dataset,
    ValidationError,
)


RELEASE_CHECK_PATH = Path(__file__).resolve().parents[1] / "scripts/release_check.py"
RELEASE_CHECK_SPEC = importlib.util.spec_from_file_location(
    "release_check", RELEASE_CHECK_PATH
)
assert RELEASE_CHECK_SPEC is not None and RELEASE_CHECK_SPEC.loader is not None
RELEASE_CHECK_MODULE = importlib.util.module_from_spec(RELEASE_CHECK_SPEC)
RELEASE_CHECK_SPEC.loader.exec_module(RELEASE_CHECK_MODULE)
PUBLIC_ARCHIVE_ROOT_FILES = RELEASE_CHECK_MODULE.PUBLIC_ARCHIVE_ROOT_FILES
DATASET_BASE_URI = URIRef("https://w3id.org/modavis/omaro/dataset")
DCAT_NAMESPACE = Namespace("http://www.w3.org/ns/dcat#")
DQV = Namespace("http://www.w3.org/ns/dqv#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
PROV = Namespace("http://www.w3.org/ns/prov#")
SPDX = Namespace("http://spdx.org/rdf/terms#")


def _prepare(repo_root: Path, temporary_root: Path) -> None:
    shutil.copytree(repo_root / "data", temporary_root / "data")
    shutil.copytree(repo_root / "LICENSES", temporary_root / "LICENSES")
    shutil.copytree(repo_root / "schema", temporary_root / "schema")
    shutil.copytree(repo_root / "site", temporary_root / "site")
    required_root_files = PUBLIC_ARCHIVE_ROOT_FILES | {
        ".zenodo.json",
        "REUSE.toml",
        "pyproject.toml",
        "requirements.txt",
        "requirements-lock.txt",
        ".python-version",
        "CONTRIBUTING.md",
        "GOVERNANCE.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "CORRECTIONS.md",
    }
    for name in sorted(required_root_files):
        shutil.copy2(repo_root / name, temporary_root / name)
    shutil.copytree(repo_root / "examples", temporary_root / "examples")
    shutil.copytree(repo_root / "w3id", temporary_root / "w3id")
    shutil.copytree(
        repo_root / "src",
        temporary_root / "src",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copytree(
        repo_root / "scripts",
        temporary_root / "scripts",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copytree(
        repo_root / "tests",
        temporary_root / "tests",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    (temporary_root / "zenodo").mkdir()
    shutil.copy2(
        repo_root / "zenodo" / "metadata.json",
        temporary_root / "zenodo" / "metadata.json",
    )


def _hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def _okf_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    return yaml.safe_load(text.split("---\n", 2)[1])


def test_full_build_is_cross_format_and_deterministic(repo_root, tmp_path):
    roots = [tmp_path / "a", tmp_path / "b"]
    for root in roots:
        gc.collect()
        root.mkdir()
        _prepare(repo_root, root)
        summary = build(
            root, root / "data" / "canonical", root / "dist", root / "schema"
        )
        assert summary["classifications"] == 643
        assert summary["instruments"] == 2724
        assert summary["label_resources"] == 42662
        assert summary["label_profiles"] == 42662
        assert summary["label_assertions"] == 42662
        assert summary["note_assertions"] == 643
        assert summary["agents"] == 2
        assert summary["source_records"] == 2
        assert summary["concept_schemes"] == 2
        assert summary["perspectives"] == 1
        assert summary["applicability_scopes"] == 1
        assert summary["authority_assignments"] == 0
        assert summary["projection_policies"] == 3
        assert summary["concept_relation_assertions"] == 0
        assert summary["review_statuses"] == 5
        assert summary["language_registries"] == 1
        assert summary["script_registries"] == 1
        assert summary["quality_rules"] == 8
        assert summary["quality_findings"] == 9445
        assert summary["review_events"] == 0
        assert summary["okf_concept_pages"] == 3372
        assert summary["rag_records"] == 3372
        assert summary["triples"] > 56000
        assert 300 < summary["ontology_triples"] < 2000
        assert summary["source_snapshot_triples"] > 50000
    assert _hashes(roots[0] / "dist") == _hashes(roots[1] / "dist")

    csv_concepts = sum(1 for _ in (roots[0] / "dist/csv/concepts.csv").open()) - 1
    jsonl_concepts = sum(1 for _ in (roots[0] / "dist/jsonl/concepts.jsonl").open())
    assert csv_concepts == jsonl_concepts == 3372
    site_data = json.loads((roots[0] / "dist/data.json").read_text())
    assert site_data["doi"] == "10.5281/zenodo.21442777"
    assert site_data["classificationCount"] == 643
    assert site_data["labelProfileCount"] == 42662
    assert site_data["unicodeScriptVersion"] == "17.0.0"
    root_notations = {row["uri"]: row["notation"] for row in site_data["items"]}
    assert [root_notations[uri] for uri in site_data["roots"]] == [
        "1",
        "2",
        "3",
        "4",
        "5",
    ]
    assert (roots[0] / "dist/index.html").exists()
    assert (roots[0] / "dist/favicon.svg").exists()
    assert (roots[0] / "dist/ontology/0.1.0/index.html").exists()
    assert (roots[0] / "dist/dataset/0.1.0/index.html").exists()
    for suffix in ("ttl", "jsonld", "rdf"):
        assert (roots[0] / f"dist/dataset/0.1.0/omaro.{suffix}").read_bytes() == (
            roots[0] / f"dist/rdf/omaro.{suffix}"
        ).read_bytes()
    ontology_turtle = Graph().parse(
        roots[0] / "dist/ontology/0.1.0/omaro.ttl", format="turtle"
    )
    ontology_rdfxml = Graph().parse(roots[0] / "dist/ontology/0.1.0/omaro.rdf")
    ontology_jsonld = Graph().parse(roots[0] / "dist/ontology/0.1.0/omaro.jsonld")
    assert (
        to_isomorphic(ontology_turtle)
        == to_isomorphic(ontology_rdfxml)
        == to_isomorphic(ontology_jsonld)
    )
    assert 300 < len(ontology_turtle) < 2000
    assert not list(
        ontology_turtle.subjects(RDF.type, URIRef("http://www.w3.org/ns/dcat#Dataset"))
    )
    for name in (
        "ClassificationAssertion",
        "ConceptRelationAssertion",
        "LabelAssertion",
        "NoteAssertion",
    ):
        assert (
            URIRef(f"https://w3id.org/modavis/omaro#{name}"),
            RDFS.subClassOf,
            RDF.Statement,
        ) in ontology_turtle
    assert (
        URIRef("https://w3id.org/modavis/omaro#ReviewEvent"),
        RDFS.subClassOf,
        URIRef("http://www.w3.org/ns/prov#Activity"),
    ) in ontology_turtle
    omaro_namespace = "https://w3id.org/modavis/omaro#"
    mapping_purpose = URIRef(f"{omaro_namespace}mappingPurpose")
    mapping_purpose_scheme = URIRef(f"{omaro_namespace}vocabulary-mapping-purpose")
    assert (mapping_purpose, RDFS.range, SKOS.Concept) in ontology_turtle
    assert (
        mapping_purpose_scheme,
        RDF.type,
        SKOS.ConceptScheme,
    ) in ontology_turtle
    for code in (
        "query-expansion",
        "display-navigation",
        "data-transformation",
        "scholarly-comparison",
    ):
        term = URIRef(f"{omaro_namespace}mapping-purpose-{code}")
        assert (term, RDF.type, SKOS.Concept) in ontology_turtle
        assert (term, SKOS.inScheme, mapping_purpose_scheme) in ontology_turtle
        assert list(ontology_turtle.objects(term, SKOS.definition))
    assert (roots[0] / "dist/ontology/0.1.0/omaro.ttl").stat().st_size < (
        roots[0] / "dist/rdf/omaro.ttl"
    ).stat().st_size
    dcat = Graph().parse(roots[0] / "dist/metadata/dcat-void.ttl")
    creator = URIRef("https://orcid.org/0000-0002-7904-3892")
    assert set(dcat.objects(creator, URIRef("https://schema.org/affiliation"))) == {
        Literal("Research Group DIGITAL ORGANOLOGY, Leipzig University"),
        Literal(
            "Digital Humanities (Image/Object), Friedrich Schiller University Jena"
        ),
    }
    dataset_uri = URIRef("https://w3id.org/modavis/omaro/dataset/0.1.0")
    doi_uri = URIRef("https://doi.org/10.5281/zenodo.21442777")
    turtle = IsomorphicGraph().parse(roots[0] / "dist/rdf/omaro.ttl")
    for graph in (dcat, turtle):
        assert (DATASET_BASE_URI, RDF.type, DCAT.Dataset) in graph
        assert (dataset_uri, RDF.type, DCAT.Dataset) in graph
        assert (DATASET_BASE_URI, DCAT_NAMESPACE.hasVersion, dataset_uri) in graph
        assert (
            DATASET_BASE_URI,
            DCAT_NAMESPACE.hasCurrentVersion,
            dataset_uri,
        ) in graph
        assert (dataset_uri, DCAT_NAMESPACE.isVersionOf, DATASET_BASE_URI) in graph
        assert (dataset_uri, DCAT_NAMESPACE.version, Literal("0.1.0")) in graph
        assert not list(graph.subjects(RDF.type, DCAT_NAMESPACE.DatasetSeries))
        assert (doi_uri, RDF.type, DCAT.Dataset) not in graph
        assert (doi_uri, RDF.type, VOID.Dataset) not in graph

    quality_report = json.loads((roots[0] / "dist/quality-report.json").read_text())
    dqv = Graph().parse(roots[0] / "dist/metadata/dqv.ttl", format="turtle")
    omaro = Namespace("https://w3id.org/modavis/omaro#")
    resolved = quality_report["instruments"]
    unresolved = quality_report["unresolved_stubs"]
    denominator = resolved + unresolved
    resolution_rate = (Decimal(resolved) / Decimal(denominator)).quantize(
        Decimal("0.000000000001")
    )
    expected_measures = {
        "resolved-source-target-count": (XSD.integer, str(resolved)),
        "unresolved-source-target-count": (XSD.integer, str(unresolved)),
        "source-target-resolution-denominator": (XSD.integer, str(denominator)),
        "source-target-resolution-rate": (
            XSD.decimal,
            format(resolution_rate, "f"),
        ),
        "automated-finding-count-total": (
            XSD.integer,
            str(quality_report["quality_findings"]),
        ),
        "review-event-count": (XSD.integer, str(quality_report["review_events"])),
        "canonical-validation-passed": (XSD.boolean, "true"),
        **{
            f"automated-finding-count-{code}": (XSD.integer, str(count))
            for code, count in quality_report["quality_findings_by_rule"].items()
        },
    }
    software_agent = omaro["release-builder"]
    assert (software_agent, RDF.type, PROV.SoftwareAgent) in dqv
    assert len(set(dqv.subjects(RDF.type, DQV.QualityMeasurement))) == len(
        expected_measures
    )
    for code, (datatype, lexical_value) in expected_measures.items():
        metric = omaro[f"quality-metric-{code}"]
        measurement = URIRef(f"{dataset_uri}#quality-measurement-{code}")
        assert (metric, RDF.type, DQV.Metric) in dqv
        assert (metric, DQV.expectedDataType, datatype) in dqv
        assert list(dqv.subjects(DQV.isMeasurementOf, metric)) == [measurement]
        values = list(dqv.objects(measurement, DQV.value))
        assert len(values) == 1
        assert values[0].datatype == datatype
        assert str(values[0]) == lexical_value
        assert (measurement, DQV.computedOn, dataset_uri) in dqv
        assert (measurement, PROV.wasAttributedTo, software_agent) in dqv
        assert (
            measurement,
            PROV.generatedAtTime,
            Literal("2026-07-19T15:10:55Z", datatype=XSD.dateTime),
        ) in dqv
        dimensions = list(dqv.objects(metric, DQV.inDimension))
        assert len(dimensions) == 1
        assert (dimensions[0], RDF.type, DQV.Dimension) in dqv
        assert list(dqv.objects(metric, SKOS.definition))
        assert "/dataset/0.1.0" not in str(metric)
    canonical_definition = " ".join(
        str(value)
        for value in dqv.objects(
            omaro["quality-metric-canonical-validation-passed"],
            SKOS.definition,
        )
    ).lower()
    assert "does not establish" in canonical_definition
    assert "organological" in canonical_definition
    assert "cultural validity" in canonical_definition
    finding_uris = {
        json.loads(line)["uri"]
        for line in (roots[0] / "dist/jsonl/quality_findings.jsonl")
        .read_text()
        .splitlines()
    }
    assert {str(node) for node in dqv.all_nodes()}.isdisjoint(finding_uris)
    manifest = json.loads((roots[0] / "dist/manifest.json").read_text())
    assert "metadata/dqv.ttl" in {row["path"] for row in manifest["files"]}

    ontology = URIRef("https://w3id.org/modavis/omaro/ontology")
    ontology_version = URIRef("https://w3id.org/modavis/omaro/ontology/0.1.0")
    related_standards = {
        URIRef("https://w3id.org/modavis/vao/0.4.0/"),
        URIRef("https://w3id.org/modavis/ontology/0.1.0"),
    }
    assert (ontology, OWL.versionIRI, ontology_version) in turtle
    assert set(turtle.objects(ontology, DCTERMS.relation)) == related_standards
    owned_properties = {
        subject
        for subject in turtle.subjects(RDF.type, RDF.Property)
        if str(subject).startswith(omaro_namespace)
    }
    assert owned_properties
    for term in owned_properties:
        property_types = {
            type_
            for type_ in turtle.objects(term, RDF.type)
            if type_ in {OWL.ObjectProperty, OWL.DatatypeProperty}
        }
        assert len(property_types) == 1
        assert len(list(turtle.objects(term, RDFS.label))) == 1
        assert len(list(turtle.objects(term, RDFS.comment))) == 1
        assert (
            term,
            RDFS.isDefinedBy,
            URIRef("https://w3id.org/modavis/omaro/ontology"),
        ) in turtle
    vao_example = json.loads(
        (roots[0] / "dist/metadata/vao-classification-example.json").read_text()
    )
    assert vao_example == {
        "scheme": "http://www.mimo-db.eu/HornbostelAndSachs#",
        "code": "111.141",
        "label": {"en": "Castanets"},
        "version": "2026-07-19T15:10:55Z",
    }
    relation_graph = Graph().parse(
        roots[0] / "dist/schema/modavis-vao-relations.ttl", format="turtle"
    )
    assert not list(relation_graph.triples((None, OWL.imports, None)))
    assert not list(relation_graph.triples((None, OWL.equivalentClass, None)))
    assert not list(relation_graph.triples((None, OWL.equivalentProperty, None)))
    assert not list(relation_graph.triples((None, RDFS.subClassOf, None)))
    # Compare complete isomorphism digests one format at a time. Holding all
    # three corpus graphs plus their isomorphic copies can exhaust a CI runner.
    expected_digest = turtle.graph_digest()
    del turtle, graph
    gc.collect()
    for filename in ("omaro.jsonld", "omaro.rdf"):
        graph = IsomorphicGraph().parse(roots[0] / "dist/rdf" / filename)
        assert graph.graph_digest() == expected_digest
        del graph
        gc.collect()


def test_okf_and_rag_exports_are_complete_and_navigable(repo_root):
    dataset = Dataset.load(repo_root / "data/canonical")
    concepts = dataset.concepts_by_uri
    okf = repo_root / "dist/okf"

    assert (okf / "index.md").read_text().startswith('---\nokf_version: "0.2"\n---\n')
    assert (okf / "dataset.md").exists()
    assert (okf / "guides/choosing-identifiers.md").exists()
    assert (okf / "classifications/index.md").exists()
    assert (okf / "instruments/index.md").exists()

    classification_pages = list((okf / "classifications/concepts").glob("*.md"))
    instrument_pages = [
        path for path in (okf / "instruments").glob("*/*.md") if path.name != "index.md"
    ]
    assert len(classification_pages) == 643
    assert len(instrument_pages) == 2729
    assert len(classification_pages) + len(instrument_pages) == len(dataset.concepts)
    concept_documents = [
        path for path in okf.rglob("*.md") if path.name not in {"index.md", "log.md"}
    ]
    assert len(concept_documents) == 3380
    for path in concept_documents:
        frontmatter = _okf_frontmatter(path)
        assert frontmatter["type"]
        assert frontmatter["status"] == "stable"
        assert frontmatter["generated"]["by"] == "omaro/0.1.0"
        assert frontmatter["generated"]["at"] == "2026-07-29T12:45:28Z"
        assert frontmatter["sources"]
        assert "timestamp" not in frontmatter
        assert "# Citations" not in path.read_text(encoding="utf-8")

    castanets = next(
        row
        for row in dataset.concepts
        if row["kind"] == "classification" and row.get("notation") == "111.141"
    )
    castanets_page = okf / f"classifications/concepts/{castanets['mimo_id']}.md"
    castanets_text = castanets_page.read_text(encoding="utf-8")
    castanets_frontmatter = _okf_frontmatter(castanets_page)
    assert castanets_frontmatter["type"] == "Hornbostel-Sachs Classification"
    assert castanets_frontmatter["resource"] == castanets["uri"]
    assert castanets_frontmatter["verified"] == {
        "by": "process:okf-projection-validation",
        "at": "2026-07-29T12:45:28Z",
    }
    assert {row["id"] for row in castanets_frontmatter["sources"]} == {
        "concept-record",
        "classification-assertions",
        "label-assertions",
        "label-resources",
        "label-profiles",
        "note-assertions",
        "quality-findings",
    }
    assert "# Ancestor context" in castanets_text
    assert "# Instrument concepts appearing in classification claims" in castanets_text
    assert "perspective, scope, stance" in castanets_text
    guide_frontmatter = _okf_frontmatter(okf / "guides/choosing-identifiers.md")
    assert "verified" not in guide_frontmatter
    dataset_frontmatter = _okf_frontmatter(okf / "dataset.md")
    assert dataset_frontmatter["verified"]["by"] == (
        "process:okf-projection-validation"
    )
    assert {row["id"] for row in dataset_frontmatter["sources"]} == {
        "mimo-source-1",
        "mimo-source-2",
        "classification-assertions",
        "label-assertions",
        "label-resources",
        "label-profiles",
        "note-assertions",
        "quality-findings",
        "iana-language-subtag-registry",
        "unicode-script-registry",
    }
    assert "## 2026-07-29" in (okf / "log.md").read_text(encoding="utf-8")

    rag_rows = [
        json.loads(line)
        for line in (repo_root / "dist/jsonl/rag-concepts.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(rag_rows) == len(dataset.concepts) == 3372
    assert {row["uri"] for row in rag_rows} == set(concepts)
    assert all(row["uri"] in row["retrieval_text"] for row in rag_rows)
    assert all(
        row["provenance"]["dataset_version"] == dataset.metadata["dataset_version"]
        for row in rag_rows
    )
    assert sum(len(row["quality_findings"]) for row in rag_rows) == 9445
    assert sum(len(row["label_resources"]) for row in rag_rows) == 42662
    assert sum(len(row["label_profiles"]) for row in rag_rows) == 42662
    assert all(
        row["provenance"]["label_resource_layer"] == "label_resources.jsonl"
        for row in rag_rows
    )
    assert all(
        row["provenance"]["label_profile_layer"] == "label_profiles.jsonl"
        and row["provenance"]["script_registry"]["unicode_version"] == "17.0.0"
        for row in rag_rows
    )
    assert all(
        finding["review_effect"] == "none" and finding["human_review_required"] is True
        for row in rag_rows
        for finding in row["quality_findings"]
    )

    rag_by_uri = {row["uri"]: row for row in rag_rows}
    castanets_rag = rag_by_uri[castanets["uri"]]
    assert castanets_rag["assertions"]["labels"]
    assert castanets_rag["assertions"]["notes"]
    assert all(
        row["review_status"] == "unreviewed"
        and row["source_record_uri"]
        and row["asserted_by_uri"]
        for row in (
            castanets_rag["assertions"]["labels"] + castanets_rag["assertions"]["notes"]
        )
    )
    assert [row["notation"] for row in castanets_rag["relationships"]["ancestors"]] == [
        "1",
        "11",
        "111",
        "111.1",
        "111.14",
    ]
    classified = castanets_rag["relationships"]["classified_instruments"]
    assert classified
    assert all(
        all(
            assignment["predicate_uri"] == CLASSIFIED_AS
            and assignment["assertion_uri"] != assignment["assignment_uri"]
            and assignment["source_predicate_uri"] == EXACT_MATCH
            and assignment["stance"] == "source-asserted"
            and assignment["assigned_by_uri"].endswith("#agent-mimo")
            and assignment["perspective_uri"].endswith("#perspective-mimo-source")
            and assignment["source_record_uri"]
            for assignment in row["classification_assignments"]
        )
        for row in classified
    )
    assert any(
        row["uri"] == castanets["uri"]
        for row in rag_by_uri[classified[0]["uri"]]["relationships"][
            "instrument_classifications"
        ]
    )

    manifest = json.loads((repo_root / "dist/manifest.json").read_text())
    assert 300 < manifest["rdf"]["ontology_triples"] < 2000
    assert manifest["rdf"]["triples"] > 2_000_000
    assert manifest["rdf"]["source_snapshot_triples"] > 50_000
    assert manifest["knowledge_exports"] == {
        "okf_concept_pages": 3372,
        "okf_guide_pages": 8,
        "okf_index_pages": 19,
        "rag_records": 3372,
    }


def test_okf_v02_validator_enforces_migrated_profile(tmp_path):
    root = tmp_path / "okf"
    root.mkdir()
    (root / "index.md").write_text(
        '---\nokf_version: "0.2"\n---\n# Bundle\n\n- [Example](example.md)\n',
        encoding="utf-8",
    )
    (root / "log.md").write_text(
        "# Bundle update log\n\n## 2026-07-29\n- **Creation**: Added example.\n",
        encoding="utf-8",
    )
    valid = (
        "---\n"
        'type: "Reference"\n'
        'status: "stable"\n'
        'generated: {"by": "example/1.0", "at": "2026-07-29T00:00:00Z"}\n'
        'sources: [{"id": "source", "resource": "https://example.org"}]\n'
        "---\n"
        "# Example\n\nGrounded content.[^source]\n\n"
        "[^source]: Example source.\n"
    )
    concept = root / "example.md"
    concept.write_text(valid, encoding="utf-8")
    _validate_okf(root, 1)

    concept.write_text(
        valid.replace('status: "stable"\n', 'status: "stable"\ntimestamp: "legacy"\n'),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="superseded timestamp"):
        _validate_okf(root, 1)

    concept.write_text(
        valid.replace('type: "Reference"', 'type: "Attested Computation"'),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="requires runtime"):
        _validate_okf(root, 1)


def test_sqlite_views_search_and_hierarchy(repo_root):
    database = repo_root / "dist/sqlite/omaro.sqlite"
    connection = sqlite3.connect(database)
    try:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 20200
        assert (
            connection.execute(
                "SELECT value FROM metadata WHERE key = 'build_python_version'"
            ).fetchone()
            is not None
        )
        assert connection.execute("SELECT count(*) FROM concepts").fetchone()[0] == 3372
        assert (
            connection.execute("SELECT count(*) FROM label_resources").fetchone()[0]
            == 42662
        )
        assert (
            connection.execute("SELECT count(*) FROM label_profiles").fetchone()[0]
            == 42662
        )
        assert (
            connection.execute(
                "SELECT count(*) FROM label_linguistic_profiles"
            ).fetchone()[0]
            == 42662
        )
        assert (
            connection.execute("SELECT count(*) FROM label_assertions").fetchone()[0]
            == 42662
        )
        assert (
            connection.execute("SELECT count(*) FROM note_assertions").fetchone()[0]
            == 643
        )
        assert connection.execute("SELECT count(*) FROM agents").fetchone()[0] == 2
        assert (
            connection.execute("SELECT count(*) FROM source_records").fetchone()[0] == 2
        )
        assert (
            connection.execute("SELECT count(*) FROM review_statuses").fetchone()[0]
            == 5
        )
        assert connection.execute(
            "SELECT rule_code, count(*) FROM audit_queue "
            "GROUP BY rule_code ORDER BY rule_code"
        ).fetchall() == [
            ("definition-repeats-notation", 13),
            ("registry-invalid-language-tag", 3679),
            ("skos-label-role-conflict", 89),
            ("undetermined-language", 1445),
            ("zh-alternative-latin-script", 2387),
            ("zh-preferred-identical-to-en", 1779),
            ("zh-preferred-placeholder-or-uncertain", 53),
        ]
        assert (
            connection.execute(
                "SELECT count(*) FROM labels_enriched "
                "WHERE review_status = 'unreviewed' AND asserted_by_uri IS NOT NULL "
                "AND source_record_uri IS NOT NULL"
            ).fetchone()[0]
            == 42662
        )
        assert (
            connection.execute(
                "SELECT count(*) FROM notes_enriched WHERE review_status = 'unreviewed'"
            ).fetchone()[0]
            == 643
        )
        assert (
            connection.execute(
                "SELECT count(*) FROM classification_targets"
            ).fetchone()[0]
            == 0
        )
        assert (
            connection.execute(
                "SELECT count(*) FROM classification_claims_enriched"
            ).fetchone()[0]
            == 1872
        )
        assert (
            connection.execute(
                "SELECT count(*) FROM mimo_source_exact_matches"
            ).fetchone()[0]
            == 1872
        )
        assert (
            connection.execute(
                "SELECT count(*) FROM classification_assertions "
                "WHERE predicate_uri = ? AND stance = 'source-asserted'",
                (CLASSIFIED_AS,),
            ).fetchone()[0]
            == 1872
        )
        assert (
            connection.execute("SELECT count(*) FROM classification_claims").fetchone()[
                0
            ]
            == 1872
        )
        assert connection.execute(
            "SELECT assertion_type, count(*) FROM assertions "
            "GROUP BY assertion_type ORDER BY assertion_type"
        ).fetchall() == [
            ("classification", 1872),
            ("label", 42662),
            ("note", 643),
        ]
        broader_count = connection.execute(
            "SELECT count(*) FROM source_relations WHERE predicate_uri = ?",
            (BROADER,),
        ).fetchone()[0]
        assert (
            connection.execute(
                "SELECT count(*) FROM concept_ancestors WHERE depth = 1"
            ).fetchone()[0]
            == broader_count
        )
        assert (
            connection.execute("SELECT count(*) FROM concept_ancestors").fetchone()[0]
            > broader_count
        )
        ancestors = connection.execute(
            """
            SELECT a.depth, parent.notation
            FROM concept_ancestors a
            JOIN concepts child ON child.uri = a.concept_uri
            JOIN concepts parent ON parent.uri = a.ancestor_uri
            WHERE child.notation = '111.141'
            ORDER BY a.depth
            """
        ).fetchall()
        assert ancestors[0] == (1, "111.14")
        assert ancestors[-1] == (5, "1")
        assert (
            connection.execute(
                "SELECT count(*) FROM label_search WHERE label_search MATCH 'guitar'"
            ).fetchone()[0]
            > 0
        )
        descendants = connection.execute(
            """
            WITH RECURSIVE tree(uri) AS (
                SELECT uri FROM concepts WHERE notation = '4'
                UNION ALL
                SELECT r.subject_uri FROM source_relations r JOIN tree t ON r.object_uri = t.uri
                WHERE r.predicate_uri = 'http://www.w3.org/2004/02/skos/core#broader'
            ) SELECT count(*) FROM tree
            """
        ).fetchone()[0]
        assert descendants > 100
    finally:
        connection.close()


def test_canonical_csv_rdf_and_sqlite_sets_are_equivalent(repo_root):
    dataset = Dataset.load(repo_root / "data/canonical")
    canonical_concepts = {row["uri"] for row in dataset.concepts}
    canonical_quality_finding_uris = {row["uri"] for row in dataset.quality_findings}
    canonical_quality_rule_uris = {row["uri"] for row in dataset.quality_rules}
    canonical_language_registry_uris = {
        row["uri"] for row in dataset.language_registries
    }
    canonical_script_registry_uris = {row["uri"] for row in dataset.script_registries}
    canonical_label_profile_uris = {row["uri"] for row in dataset.label_profiles}
    agent_fields = ("uri", "agent_type", "name", "resource_uri")
    source_record_fields = (
        "uri",
        "resource_uri",
        "title",
        "source_type",
        "scheme_uri",
        "publisher_agent_uri",
        "layer",
        "rights_uri",
        "retrieved_at",
    )
    review_status_fields = ("uri", "code", "label", "description")
    canonical_agents = {
        tuple(row[field] for field in agent_fields) for row in dataset.agents
    }
    canonical_source_records = {
        tuple(row[field] for field in source_record_fields)
        for row in dataset.source_records
    }
    canonical_review_statuses = {
        tuple(row[field] for field in review_status_fields)
        for row in dataset.review_statuses
    }
    canonical_labels = {
        (
            row["concept_uri"],
            row["language"],
            row["submitted_language"],
            row["label_type"],
            row["label"],
        )
        for row in dataset.labels
    }
    canonical_rdf_labels = {
        (
            row["concept_uri"],
            row["language_tag"],
            row["label_role"],
            row["literal_form"],
        )
        for row in dataset.label_assertions
        if row["skos_projection_status"] == "projected"
    }
    canonical_label_resources = {
        (
            row["uri"],
            row["literal_form"],
            row["normalized_form"],
            row["language_tag"],
            row["language_registry_uri"],
        )
        for row in dataset.label_resources
    }
    assertion_context_fields = (
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
    )
    canonical_label_assertions = {
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
        for row in dataset.label_assertions
    }
    canonical_note_assertions = {
        tuple(row[field] for field in assertion_context_fields)
        for row in dataset.note_assertions
    }
    canonical_source_relations = {
        (row["subject_uri"], row["predicate_uri"], row["object_uri"])
        for row in dataset.source_relations
    }
    canonical_assertions = {row["uri"] for row in dataset.classification_assertions}

    with (repo_root / "dist/csv/concepts.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        assert {row["uri"] for row in csv.DictReader(handle)} == canonical_concepts
    with (repo_root / "dist/csv/quality-findings.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        assert {
            row["uri"] for row in csv.DictReader(handle)
        } == canonical_quality_finding_uris
    with (repo_root / "dist/csv/quality-rules.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        assert {
            row["uri"] for row in csv.DictReader(handle)
        } == canonical_quality_rule_uris
    with (repo_root / "dist/csv/language-registries.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        assert {
            row["uri"] for row in csv.DictReader(handle)
        } == canonical_language_registry_uris
    for filename, fields, canonical_rows in (
        ("agents.csv", agent_fields, canonical_agents),
        ("source-records.csv", source_record_fields, canonical_source_records),
        ("review-statuses.csv", review_status_fields, canonical_review_statuses),
    ):
        with (repo_root / "dist/csv" / filename).open(
            newline="", encoding="utf-8"
        ) as handle:
            assert {
                tuple(row[field] for field in fields) for row in csv.DictReader(handle)
            } == canonical_rows
    with (repo_root / "dist/csv/labels.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        assert {
            (
                row["concept_uri"],
                row["language"],
                row["submitted_language"],
                row["label_type"],
                row["label"],
            )
            for row in csv.DictReader(handle)
        } == canonical_labels
    with (repo_root / "dist/csv/source-relations.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        assert {
            (row["subject_uri"], row["predicate_uri"], row["object_uri"])
            for row in csv.DictReader(handle)
        } == canonical_source_relations
    with (repo_root / "dist/csv/label-assertions.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        assert {
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
            for row in csv.DictReader(handle)
        } == canonical_label_assertions
    with (repo_root / "dist/csv/label-resources.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        assert {
            (
                row["uri"],
                row["literal_form"],
                row["normalized_form"],
                row["language_tag"],
                row["language_registry_uri"],
            )
            for row in csv.DictReader(handle)
        } == canonical_label_resources
    with (repo_root / "dist/csv/note-assertions.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        assert {
            tuple(row[field] for field in assertion_context_fields)
            for row in csv.DictReader(handle)
        } == canonical_note_assertions
    with (repo_root / "dist/csv/classification-assignments.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        mapping_rows = list(csv.DictReader(handle))
    assert len(mapping_rows) == 1872
    assert {row["assertion_uri"] for row in mapping_rows} == canonical_assertions
    assert all(
        row["stance"] == "source-asserted"
        and row["assigned_by_uri"].endswith("#agent-mimo")
        and row["perspective_uri"].endswith("#perspective-mimo-source")
        and json.loads(row["applicability_scope_uris_json"])[0].endswith(
            "#scope-source-silent"
        )
        for row in mapping_rows
    )
    assert (
        sum(row["target_resolution_status"] == "unresolved" for row in mapping_rows)
        == 5
    )
    assert all(row["classification_notation"] for row in mapping_rows)

    connection = sqlite3.connect(repo_root / "dist/sqlite/omaro.sqlite")
    try:
        assert {
            row[0] for row in connection.execute("SELECT uri FROM concepts")
        } == canonical_concepts
        assert {
            row[0] for row in connection.execute("SELECT uri FROM quality_findings")
        } == canonical_quality_finding_uris
        assert {
            row[0] for row in connection.execute("SELECT uri FROM quality_rules")
        } == canonical_quality_rule_uris
        assert {
            row[0] for row in connection.execute("SELECT uri FROM language_registries")
        } == canonical_language_registry_uris
        assert {
            row[0] for row in connection.execute("SELECT uri FROM script_registries")
        } == canonical_script_registry_uris
        assert {
            row[0] for row in connection.execute("SELECT uri FROM label_profiles")
        } == canonical_label_profile_uris
        for table, fields, canonical_rows in (
            ("agents", agent_fields, canonical_agents),
            ("source_records", source_record_fields, canonical_source_records),
            ("review_statuses", review_status_fields, canonical_review_statuses),
        ):
            assert (
                set(connection.execute(f"SELECT {', '.join(fields)} FROM {table}"))
                == canonical_rows
            )
        assert (
            set(
                connection.execute(
                    "SELECT concept_uri, language, submitted_language, "
                    "label_type, label FROM labels"
                )
            )
            == canonical_labels
        )
        assert (
            set(
                connection.execute(
                    "SELECT uri, literal_form, normalized_form, language_tag, "
                    "language_registry_uri FROM label_resources"
                )
            )
            == canonical_label_resources
        )
        assert (
            set(
                connection.execute(
                    "SELECT uri, concept_uri, predicate_uri, literal_form, "
                    "normalized_form, language_tag, submitted_language_tag, "
                    "language_tag_status, language_registry_uri, label_resource_uri, "
                    "label_role, skos_projection_status, asserted_by_uri, "
                    "source_record_uri, source_uri, assertion_origin, review_status, "
                    "review_status_uri FROM label_assertions"
                )
            )
            == canonical_label_assertions
        )
        assert (
            set(
                connection.execute(
                    "SELECT uri, concept_uri, predicate_uri, literal_form, "
                    "normalized_form, language_tag, submitted_language_tag, "
                    "language_tag_status, language_registry_uri, asserted_by_uri, "
                    "source_record_uri, source_uri, assertion_origin, review_status, "
                    "review_status_uri FROM note_assertions"
                )
            )
            == canonical_note_assertions
        )
        assert (
            set(
                connection.execute(
                    "SELECT subject_uri, predicate_uri, object_uri FROM source_relations"
                )
            )
            == canonical_source_relations
        )
        assert {
            row[0]
            for row in connection.execute("SELECT uri FROM classification_assertions")
        } == canonical_assertions
    finally:
        connection.close()

    graph = Graph().parse(repo_root / "dist/rdf/omaro.ttl")
    label_predicates = {
        "preferred": SKOS.prefLabel,
        "alternative": SKOS.altLabel,
        "hidden": SKOS.hiddenLabel,
    }
    rdf_labels = {
        (str(subject), literal.language, label_type, str(literal))
        for label_type, predicate in label_predicates.items()
        for subject, _, literal in graph.triples((None, predicate, None))
        if str(subject) in canonical_concepts
    }
    assert rdf_labels == canonical_rdf_labels
    mic = "https://w3id.org/modavis/omaro#"
    label_assertion_nodes = set(
        graph.subjects(RDF.type, URIRef(f"{mic}LabelAssertion"))
    )
    note_assertion_nodes = set(graph.subjects(RDF.type, URIRef(f"{mic}NoteAssertion")))
    classification_assignment_nodes = set(
        graph.subjects(RDF.type, URIRef(f"{mic}ClassificationAssertion"))
    )
    quality_finding_nodes = set(
        graph.subjects(RDF.type, URIRef(f"{mic}QualityFinding"))
    )
    assert len(label_assertion_nodes) == len(dataset.label_assertions) == 42662
    skosxl = "http://www.w3.org/2008/05/skos-xl#"
    label_resource_nodes = set(graph.subjects(RDF.type, URIRef(f"{skosxl}Label")))
    assert {str(node) for node in label_resource_nodes} == {
        row["uri"] for row in dataset.label_resources
    }
    assert all(
        len(list(graph.objects(node, URIRef(f"{skosxl}literalForm")))) == 1
        for node in label_resource_nodes
    )
    label_profile_nodes = set(graph.subjects(RDF.type, URIRef(f"{mic}LabelProfile")))
    assert {str(node) for node in label_profile_nodes} == canonical_label_profile_uris
    ontolex = "http://www.w3.org/ns/lemon/ontolex#"
    assert not any(
        isinstance(term, URIRef) and str(term).startswith(ontolex)
        for triple in graph
        for term in triple
    )
    assert len(note_assertion_nodes) == len(dataset.note_assertions) == 643
    assert {str(node) for node in classification_assignment_nodes} == {
        row["uri"] for row in dataset.classification_assertions
    }
    assert all(
        (
            URIRef(row["uri"]),
            URIRef(f"{mic}perspective"),
            URIRef(row["perspective_uri"]),
        )
        in graph
        and any(
            graph.triples(
                (
                    URIRef(row["uri"]),
                    URIRef(f"{mic}hasApplicabilityScope"),
                    None,
                )
            )
        )
        and any(graph.triples((URIRef(row["uri"]), URIRef(f"{mic}hasEvidence"), None)))
        for row in dataset.classification_assertions
    )
    assert {str(node) for node in quality_finding_nodes} == (
        canonical_quality_finding_uris
    )
    assert {
        str(node)
        for node in graph.subjects(RDF.type, URIRef("http://www.w3.org/ns/prov#Entity"))
    } == {
        row["uri"]
        for row in [
            *dataset.source_records,
            *dataset.language_registries,
            *dataset.script_registries,
        ]
    }
    assert {
        str(node) for node in graph.subjects(RDF.type, URIRef(f"{mic}ReviewStatus"))
    } == {row["uri"] for row in dataset.review_statuses}
    sample_label = dataset.label_assertions[0]
    sample_node = URIRef(sample_label["uri"])
    assert (
        sample_node,
        RDF.subject,
        URIRef(sample_label["concept_uri"]),
    ) in graph
    assert (
        sample_node,
        URIRef(f"{mic}labelResource"),
        URIRef(sample_label["label_resource_uri"]),
    ) in graph
    for assertion in dataset.label_assertions:
        xl_predicate = URIRef(
            f"{skosxl}"
            + {
                "preferred": "prefLabel",
                "alternative": "altLabel",
                "hidden": "hiddenLabel",
            }[assertion["label_role"]]
        )
        triple = (
            URIRef(assertion["concept_uri"]),
            xl_predicate,
            URIRef(assertion["label_resource_uri"]),
        )
        assert (triple in graph) == (assertion["skos_projection_status"] == "projected")
    assert (
        sample_node,
        RDF.predicate,
        URIRef(sample_label["predicate_uri"]),
    ) in graph
    assert (
        sample_node,
        RDF.object,
        Literal(sample_label["literal_form"], lang=sample_label["language_tag"]),
    ) in graph
    assert (
        sample_node,
        URIRef("http://www.w3.org/ns/prov#wasAttributedTo"),
        URIRef(sample_label["asserted_by_uri"]),
    ) in graph
    assert (
        sample_node,
        URIRef(f"{mic}reviewStatusResource"),
        URIRef(sample_label["review_status_uri"]),
    ) in graph
    assert not set(graph.triples((None, URIRef(EXACT_MATCH), None)))
    assert {
        (str(subject), str(predicate), str(obj))
        for predicate in (URIRef(BROADER),)
        for subject, _, obj in graph.triples((None, predicate, None))
    } == {relation for relation in canonical_source_relations if relation[1] == BROADER}
    assert {
        (str(subject), str(obj))
        for subject, _, obj in graph.triples((None, URIRef(CLASSIFIED_AS), None))
    } == set()
    assert {
        (str(subject), str(obj))
        for subject, _, obj in graph.triples((None, URIRef(NARROWER), None))
    } == {
        (obj, subject)
        for subject, predicate, obj in canonical_source_relations
        if predicate == BROADER
    }
    source_graph = Graph().parse(repo_root / "dist/rdf/mimo-source-snapshot.ttl")
    assert {
        (str(subject), str(predicate), str(obj))
        for predicate in (URIRef(BROADER), URIRef(EXACT_MATCH))
        for subject, _, obj in source_graph.triples((None, predicate, None))
    } == canonical_source_relations


def test_legacy_exports_are_compatible_and_clean(repo_root):
    classifications = json.loads((repo_root / "hornbostelSachs.json").read_text())
    translations = json.loads((repo_root / "translations.json").read_text())
    expected_classifications, expected_translations = _legacy_exports(
        Dataset.load(repo_root / "data/canonical")
    )
    assert classifications == expected_classifications
    assert translations == expected_translations
    assert len(classifications) == 643
    assert len(translations) == 2724
    assert all(
        set(row) == {"Label", "Translations", "MIMOPage"} for row in translations
    )
    assert all("null" not in row["Translations"] for row in translations)
    assert all(isinstance(row["MIMOPage"], str) for row in translations)


def test_release_package_is_complete_and_reproducible(repo_root, tmp_path):
    root = tmp_path / "release"
    root.mkdir()
    _prepare(repo_root, root)
    build(root, root / "data/canonical", root / "dist", root / "schema")
    archive, checksums = package(root, root / "dist", "0.1.0")
    sidecar = root / "omaro-v0.1.0.dcat.ttl"
    first = archive.read_bytes()
    first_sidecar = sidecar.read_bytes()
    first_checksums = checksums.read_bytes()
    archive2, _ = package(root, root / "dist", "0.1.0")
    assert first == archive2.read_bytes()
    assert first_sidecar == sidecar.read_bytes()
    assert first_checksums == checksums.read_bytes()
    expected_checksum_lines = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
        for path in sorted((archive, sidecar), key=lambda path: path.name)
    )
    assert checksums.read_text() == expected_checksum_lines

    sidecar_graph = Graph().parse(sidecar, format="turtle")
    dataset_uri = URIRef("https://w3id.org/modavis/omaro/dataset/0.1.0")
    distribution = URIRef(f"{dataset_uri}#distribution-release-zip")
    release_url = URIRef(
        "https://github.com/modavis-project/omaro/releases/download/"
        "v0.1.0/omaro-v0.1.0.zip"
    )
    assert (DATASET_BASE_URI, DCAT_NAMESPACE.hasVersion, dataset_uri) in sidecar_graph
    assert (
        DATASET_BASE_URI,
        DCAT_NAMESPACE.hasCurrentVersion,
        dataset_uri,
    ) in sidecar_graph
    assert (
        dataset_uri,
        DCAT_NAMESPACE.isVersionOf,
        DATASET_BASE_URI,
    ) in sidecar_graph
    assert (dataset_uri, DCAT_NAMESPACE.version, Literal("0.1.0")) in sidecar_graph
    assert (distribution, DCAT.downloadURL, release_url) in sidecar_graph
    assert (
        distribution,
        DCAT_NAMESPACE.packageFormat,
        URIRef("https://www.iana.org/assignments/media-types/application/zip"),
    ) in sidecar_graph
    assert (
        distribution,
        DCAT.byteSize,
        Literal(archive.stat().st_size, datatype=XSD.nonNegativeInteger),
    ) in sidecar_graph
    assert (
        distribution,
        DCTERMS.license,
        URIRef("https://creativecommons.org/publicdomain/zero/1.0/"),
    ) in sidecar_graph
    checksum_nodes = list(sidecar_graph.objects(distribution, SPDX.checksum))
    assert len(checksum_nodes) == 1
    checksum_node = checksum_nodes[0]
    assert (checksum_node, RDF.type, SPDX.Checksum) in sidecar_graph
    assert (
        checksum_node,
        SPDX.algorithm,
        SPDX.checksumAlgorithm_sha256,
    ) in sidecar_graph
    assert (
        checksum_node,
        SPDX.checksumValue,
        Literal(
            hashlib.sha256(archive.read_bytes()).hexdigest(),
            datatype=XSD.hexBinary,
        ),
    ) in sidecar_graph
    records = list(sidecar_graph.subjects(RDF.type, DCAT.CatalogRecord))
    assert len(records) == 1
    assert (records[0], FOAF.primaryTopic, dataset_uri) in sidecar_graph
    assert (
        records[0],
        DCTERMS.conformsTo,
        URIRef("https://www.w3.org/TR/vocab-dcat-3/"),
    ) in sidecar_graph
    assert not any(sidecar.name in str(node) for node in sidecar_graph.all_nodes())
    with zipfile.ZipFile(archive) as handle:
        names = set(handle.namelist())
    prefix = "omaro-v0.1.0/"
    assert {prefix + name for name in PUBLIC_ARCHIVE_ROOT_FILES} <= names
    assert {
        prefix + path.relative_to(root).as_posix()
        for path in (root / "examples").rglob("*")
        if path.is_file()
    } <= names
    assert prefix + "ro-crate-metadata.json" in names
    assert prefix + "examples/multidimensional-analysis/README.md" in names
    assert prefix + "examples/multidimensional-analysis/scalogram.json" in names
    assert prefix + "dist/manifest.json" in names
    assert prefix + "AUTHORS.md" in names
    assert prefix + "NOTICE" in names
    assert prefix + "VERSION" in names
    assert prefix + "codemeta.json" in names
    assert prefix + "dist/okf/index.md" in names
    assert prefix + "dist/jsonl/rag-concepts.jsonl" in names
    assert prefix + "dist/jsonl/label_assertions.jsonl" in names
    assert prefix + "dist/jsonl/label_resources.jsonl" in names
    assert prefix + "dist/jsonl/label_profiles.jsonl" in names
    assert prefix + "dist/jsonl/note_assertions.jsonl" in names
    assert prefix + "dist/jsonl/agents.jsonl" in names
    assert prefix + "dist/jsonl/source_records.jsonl" in names
    assert prefix + "dist/jsonl/review_statuses.jsonl" in names
    assert prefix + "dist/jsonl/language_registries.jsonl" in names
    assert prefix + "dist/jsonl/script_registries.jsonl" in names
    assert prefix + "dist/jsonl/quality_rules.jsonl" in names
    assert prefix + "dist/jsonl/quality_findings.jsonl" in names
    assert prefix + "dist/jsonl/review_events.jsonl" in names
    assert prefix + "dist/jsonl/concept_schemes.jsonl" in names
    assert prefix + "dist/jsonl/perspectives.jsonl" in names
    assert prefix + "dist/jsonl/applicability_scopes.jsonl" in names
    assert prefix + "dist/jsonl/authority_assignments.jsonl" in names
    assert prefix + "dist/jsonl/projection_policies.jsonl" in names
    assert prefix + "dist/jsonl/concept_relation_assertions.jsonl" in names
    assert prefix + "dist/metadata/iana-language-subtag-registry.json" in names
    assert prefix + "dist/metadata/unicode-script-registry.json" in names
    assert prefix + "dist/metadata/dqv.ttl" in names
    assert not any(name.endswith(sidecar.name) for name in names)
    assert prefix + "dist/sqlite/omaro.sqlite" in names
    assert prefix + "RELEASE_NOTES.md" in names
    assert prefix + "PROVENANCE.md" in names
    assert prefix + "QUALITY_REPORT.md" in names
    assert prefix + "MULTIPERSPECTIVITY.md" in names
    assert prefix + "ONTOLOGY_REFERENCE.md" in names
    assert prefix + "NAMING_AND_IDENTITY.md" in names
    assert prefix + "W3ID_REGISTRATION.md" in names
    assert prefix + "COMPETENCY_QUESTIONS.md" in names
    assert prefix + "DECOLONIAL_COMMITMENTS.md" in names
    assert prefix + "MODAVIS_VAO_INTEROPERABILITY.md" in names
    assert prefix + "EXTERNAL_REVIEW_DECISIONS.md" in names
    assert prefix + "IMPLEMENTATION_VERIFICATION.md" in names
    assert prefix + "GOVERNANCE.md" in names
    assert prefix + "REVIEW_PROTOCOL.md" in names
    assert prefix + "dist/ontology/0.1.0/index.html" in names
    assert prefix + "dist/ontology/0.1.0/omaro.ttl" in names
    assert prefix + "dist/dataset/0.1.0/index.html" in names
    assert not any(
        name.startswith(prefix + directory)
        for name in names
        for directory in (
            "data/",
            "review/",
            "scripts/",
            "site/",
            "src/",
            "tests/",
            "w3id/",
            "zenodo/",
        )
    )
    assert not any(
        ".egg-info/" in name
        or "/__pycache__/" in name
        or name.endswith((".pyc", ".pyo", "/.DS_Store"))
        for name in names
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/release_check.py"),
            "--repo-root",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def test_build_is_reproducible_across_processes(repo_root, tmp_path):
    root = tmp_path / "cross-process"
    root.mkdir()
    _prepare(repo_root, root)
    command = [
        sys.executable,
        "-m",
        "omaro.cli",
        "--repo-root",
        str(root),
        "build",
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    first = _hashes(root / "dist")
    subprocess.run(command, check=True, capture_output=True, text=True)
    assert first == _hashes(root / "dist")


def test_doi_and_release_metadata_are_consistent(repo_root):
    expected = "10.5281/zenodo.21442777"
    canonical = json.loads((repo_root / "data/canonical/metadata.json").read_text())
    zenodo = json.loads((repo_root / "zenodo/metadata.json").read_text())
    github_zenodo = json.loads((repo_root / ".zenodo.json").read_text())
    datacite = json.loads((repo_root / "dist/metadata/datacite.json").read_text())
    citation = (repo_root / "CITATION.cff").read_text()
    site = (repo_root / "site/index.html").read_text()
    assert canonical["doi"] == expected
    assert zenodo["reserved_doi"] == expected
    assert zenodo["record_status"] == "draft"
    assert github_zenodo["version"] == "0.1.0"
    assert github_zenodo["title"] == canonical["title"]
    assert "doi" not in zenodo["api_payload"]["metadata"]
    assert datacite["data"]["attributes"]["doi"] == expected
    assert "event" not in datacite["data"]["attributes"]
    expected_affiliations = {
        "Research Group DIGITAL ORGANOLOGY, Leipzig University",
        "Digital Humanities (Image/Object), Friedrich Schiller University Jena",
    }
    assert set(canonical["creators"][0]["affiliations"]) == expected_affiliations
    assert {
        row["name"]
        for row in datacite["data"]["attributes"]["creators"][0]["affiliation"]
    } == expected_affiliations
    assert all(
        value in zenodo["api_payload"]["metadata"]["creators"][0]["affiliation"]
        for value in expected_affiliations
    )
    assert re.search(rf"^doi: {re.escape(expected)}$", citation, re.MULTILINE)
    assert all(value in citation for value in expected_affiliations)
    assert expected in site
