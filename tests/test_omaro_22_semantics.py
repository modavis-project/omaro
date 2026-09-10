from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from pyshacl import validate as shacl_validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import PROV, RDF, SKOS

from omaro.builder import (
    CONTROLLED_CODES,
    OMARO_NS,
    _build_sqlite,
    dataset_graph,
)
from omaro.model import (
    CLAIMS_POLICY,
    MIMO_PERSPECTIVE,
    PROJECT_AGENT,
    PUBLICATION_AUDIENCE,
    PUBLICATION_PURPOSE,
    SOURCE_SILENT_SCOPE,
    Dataset,
    ValidationError,
    classification_assertion_uri,
    classification_assignment_uri,
    controlled_value_uri,
    review_decision_uri,
    review_status_uri,
)


ONTOLEX = "http://www.w3.org/ns/lemon/ontolex#"
CRMINF = Namespace("http://www.cidoc-crm.org/extensions/crminf/")
CRMSCI = Namespace("http://www.cidoc-crm.org/extensions/crmsci/")
SOSA = Namespace("http://www.w3.org/ns/sosa/")
AUTHORIZED_AGENT = "https://example.org/agent/authorized-body"
COMMUNITY_A = "https://example.org/community/a"
COMMUNITY_B = "https://example.org/community/b"
PROTOCOL_APPLICATION = "https://example.org/protocol/application-1"
PROTOCOL_RESOURCE = "https://example.org/protocol/cultural-care"


@pytest.fixture(scope="module")
def canonical_dataset(repo_root: Path) -> Dataset:
    return Dataset.load(repo_root / "data" / "canonical")


def _evidence(relation: str, suffix: str = "example") -> dict[str, str | None]:
    return {
        "citation": f"Evidence {suffix}",
        "evidence_type": "observation",
        "relation": relation,
        "resource_uri": f"https://example.org/evidence/{suffix}",
        "note": f"Evidence used to {relation} the assertion.",
    }


def _concept_relation_record(
    canonical_dataset: Dataset,
    *,
    predicate_uri: str = "http://www.w3.org/2004/02/skos/core#closeMatch",
    mapping_purpose_uris: list[str] | None = None,
) -> dict:
    subject = next(
        row for row in canonical_dataset.concepts if row["kind"] == "classification"
    )
    obj = next(row for row in canonical_dataset.concepts if row["kind"] == "instrument")
    return {
        "uri": "https://example.org/relation/purpose-qualified",
        "subject_concept_uri": subject["uri"],
        "predicate_uri": predicate_uri,
        "object_concept_uri": obj["uri"],
        "assigned_by_uri": PROJECT_AGENT,
        "generated_by_uri": None,
        "perspective_uri": MIMO_PERSPECTIVE,
        "relation_method_uri": "https://example.org/method/curated-crosswalk",
        "mapping_purpose_uris": (
            [controlled_value_uri("mapping-purpose", "scholarly-comparison")]
            if mapping_purpose_uris is None
            else mapping_purpose_uris
        ),
        "stance": "proposed",
        "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
        "evidence": [_evidence("supports", "mapping-purpose")],
        "authority_assignment_uris": [],
        "valid_from": None,
        "valid_until": None,
        "projection_policy_uris": [CLAIMS_POLICY],
        "source_record_uri": canonical_dataset.source_records[0]["uri"],
        "assertion_origin": "scholarly-asserted",
    }


def _review_event(target_assertion_uri: str) -> dict:
    event_uri = "https://example.org/review/activity-1"
    return {
        "uri": event_uri,
        "decision_uri": review_decision_uri(event_uri),
        "target_assertion_uri": target_assertion_uri,
        "reviewer_agent_uri": PROJECT_AGENT,
        "reviewer_authority": "organology",
        "authority_assignment_uris": ["https://example.org/authority/organology-1"],
        "review_method": "human",
        "validation_dimension": "scholarly",
        "outcome": "accepted",
        "reviewed_at": "2026-07-01T00:00:00Z",
        "valid_until": None,
        "perspective_uri": MIMO_PERSPECTIVE,
        "represented_community_uris": [],
        "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
        "evidence": [_evidence("supports", "review")],
        "rationale": "The documented assignment is consistent with the cited evidence.",
        "rights_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
        "supersedes_decision_uri": None,
        "suspends_decision_uri": None,
        "reinstates_decision_uri": None,
        "decision_status": "active",
        "projection_policy_uris": [
            "https://w3id.org/modavis/omaro#projection-policy-research-claims"
        ],
    }


@pytest.fixture(scope="module")
def semantic_projection(canonical_dataset: Dataset):
    dataset = copy.copy(canonical_dataset)
    assertion = copy.deepcopy(canonical_dataset.classification_assertions[0])
    assertion["classification_expression_uri"] = None
    assertion["criteria_uris"] = []
    assertion["assessment_uris"] = []
    assertion["evidence"] = [
        _evidence(relation, relation)
        for relation in ("supports", "opposes", "qualifies", "documents")
    ]
    retained_concept_uris = {assertion["classification_uri"], assertion["target_uri"]}

    dataset.concepts = [
        row for row in canonical_dataset.concepts if row["uri"] in retained_concept_uris
    ]
    dataset.labels = []
    dataset.label_resources = [canonical_dataset.label_resources[0]]
    dataset.label_profiles = []
    dataset.label_assertions = []
    dataset.note_assertions = []
    dataset.source_relations = []
    dataset.concept_relation_assertions = []
    dataset.quality_findings = []
    dataset.quality_rules = []
    dataset.organological_targets = []
    dataset.classification_criteria = []
    dataset.observation_assessments = []
    dataset.classification_expressions = []
    dataset.protocol_applications = []
    dataset.use_decisions = []
    dataset.classification_assertions = [assertion]
    dataset.review_events = [_review_event(assertion["uri"])]
    return dataset_graph(dataset), assertion, dataset.review_events[0]


def _assert_schema_valid(repo_root: Path, schema_name: str, row: dict) -> None:
    schema = json.loads(
        (repo_root / "schema" / schema_name).read_text(encoding="utf-8")
    )
    errors = list(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(row)
    )
    assert not errors, [error.message for error in errors]


@pytest.mark.parametrize(
    ("schema_name", "property_name", "controlled_category"),
    [
        ("perspective.schema.json", "perspective_type", "perspective-type"),
        (
            "classification_criterion.schema.json",
            "criterion_type",
            "criterion-type",
        ),
        (
            "observation_assessment.schema.json",
            "assessment_status",
            "assessment-status",
        ),
    ],
)
def test_schema_codes_match_rdf_controlled_vocabularies(
    repo_root: Path,
    schema_name: str,
    property_name: str,
    controlled_category: str,
):
    schema = json.loads(
        (repo_root / "schema" / schema_name).read_text(encoding="utf-8")
    )
    assert set(schema["properties"][property_name]["enum"]) == set(
        CONTROLLED_CODES[controlled_category]
    )


def test_assertion_and_assignment_identities_are_distinct_and_deterministic(
    canonical_dataset: Dataset,
):
    assertion_uris = {row["uri"] for row in canonical_dataset.classification_assertions}
    assignment_uris = {
        row["assignment_uri"] for row in canonical_dataset.classification_assertions
    }

    assert len(assertion_uris) == len(assignment_uris) == 1872
    assert assertion_uris.isdisjoint(assignment_uris)
    assert all(
        row["assignment_uri"] == classification_assignment_uri(row["uri"])
        for row in canonical_dataset.classification_assertions
    )


def test_assertion_and_review_identity_separation_is_explicit_in_rdf(
    semantic_projection,
):
    graph, assertion, event = semantic_projection
    assertion_node = URIRef(assertion["uri"])
    assignment_node = URIRef(assertion["assignment_uri"])
    event_node = URIRef(event["uri"])
    decision_node = URIRef(event["decision_uri"])

    assert assertion_node != assignment_node
    assert (assertion_node, RDF.type, OMARO_NS.ClassificationAssertion) in graph
    assert (assignment_node, RDF.type, OMARO_NS.ClassificationAssignment) in graph
    assert (assertion_node, PROV.wasGeneratedBy, assignment_node) in graph
    assert (assignment_node, PROV.generated, assertion_node) in graph
    assert not list(graph.objects(assertion_node, OMARO_NS.assignedBy))
    assert list(graph.objects(assignment_node, OMARO_NS.assignedBy))
    assert set(graph.objects(assignment_node, OMARO_NS.classificationMethod)) == {
        URIRef(assertion["classification_method_uri"])
    }

    assert event_node != decision_node
    assert event["decision_uri"] == review_decision_uri(event["uri"])
    assert (event_node, RDF.type, OMARO_NS.ReviewEvent) in graph
    assert (decision_node, RDF.type, OMARO_NS.ReviewDecision) in graph
    assert (event_node, PROV.generated, decision_node) in graph
    assert (decision_node, PROV.wasGeneratedBy, event_node) in graph
    assert list(graph.objects(event_node, OMARO_NS.reviewMethod))
    assert not list(graph.objects(decision_node, OMARO_NS.reviewMethod))
    assert list(graph.objects(decision_node, OMARO_NS.reviewOutcome))
    assert not list(graph.objects(event_node, OMARO_NS.reviewOutcome))


def test_json_envelopes_preserve_both_identities(
    repo_root: Path, canonical_dataset: Dataset
):
    assertion = canonical_dataset.classification_assertions[0]
    review = _review_event(assertion["uri"])

    _assert_schema_valid(repo_root, "classification_assertion.schema.json", assertion)
    _assert_schema_valid(repo_root, "review_event.schema.json", review)
    assert assertion["uri"] != assertion["assignment_uri"]
    assert review["uri"] != review["decision_uri"]
    assert "classification_method" not in assertion
    assert assertion["classification_method_uri"].startswith(("http://", "https://"))


def test_evidence_roles_are_directional_in_json_and_rdf(
    repo_root: Path, semantic_projection
):
    graph, assertion, _ = semantic_projection
    assertion_node = URIRef(assertion["uri"])
    assignment_node = URIRef(assertion["assignment_uri"])
    expected_roles = {
        URIRef(controlled_value_uri("evidence-role", relation))
        for relation in ("supports", "opposes", "qualifies", "documents")
    }

    evidence_nodes = set(graph.objects(assertion_node, OMARO_NS.hasEvidence))
    assert len(evidence_nodes) == 4
    assert {
        role
        for evidence_node in evidence_nodes
        for role in graph.objects(evidence_node, OMARO_NS.evidenceRelation)
    } == expected_roles
    usage_nodes = set(graph.objects(assignment_node, PROV.qualifiedUsage))
    assert len(usage_nodes) == 4
    assert {
        role for usage in usage_nodes for role in graph.objects(usage, PROV.hadRole)
    } == expected_roles

    invalid = copy.deepcopy(assertion)
    invalid["evidence"][0]["relation"] = "neutral"
    schema = json.loads(
        (repo_root / "schema/classification_assertion.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert list(Draft202012Validator(schema).iter_errors(invalid))


def test_all_source_compound_expressions_are_lossless_and_assignments_are_linked(
    canonical_dataset: Dataset,
):
    expressions = canonical_dataset.classification_expressions
    expression_by_uri = {row["uri"]: row for row in expressions}
    compound_concepts = {
        row["uri"]: row["notation"]
        for row in canonical_dataset.concepts
        if row["kind"] == "classification" and "+" in (row.get("notation") or "")
    }

    assert len(expressions) == len(compound_concepts) == 26
    assert {row["source_concept_uri"] for row in expressions} == set(compound_concepts)
    for expression in expressions:
        notation = compound_concepts[expression["source_concept_uri"]]
        assert expression["notation_literal"] == notation
        assert expression["parse_status"] == "tokenized-uninterpreted"
        assert expression["combination_operator"] == "joint"
        assert [member["sequence_index"] for member in expression["members"]] == list(
            range(1, len(expression["members"]) + 1)
        )
        assert [member["member_notation"] for member in expression["members"]] == (
            notation.split("+")
        )
        assert expression["shared_suffix_notation"] is None
        assert all(
            member["member_target_uri"] is None
            and member["component_role_uri"] is None
            and member["local_suffix_notation"] is None
            for member in expression["members"]
        )

    linked = [
        row
        for row in canonical_dataset.classification_assertions
        if row["classification_expression_uri"] is not None
    ]
    assert len(linked) == 15
    assert len({row["classification_expression_uri"] for row in linked}) == 8
    assert all(
        expression_by_uri[row["classification_expression_uri"]]["source_concept_uri"]
        == row["classification_uri"]
        for row in linked
    )


def _authority_uri(community_uri: str) -> str:
    return f"https://example.org/authority/{community_uri.rsplit('/', 1)[-1]}"


def _authority(
    target_uri: str,
    community_uri: str,
    *,
    status: str = "active",
    covered_dimensions: list[str] | None = None,
) -> dict:
    revoked = status == "revoked"
    return {
        "uri": _authority_uri(community_uri),
        "agent_uri": AUTHORIZED_AGENT,
        "represented_community_uri": community_uri,
        "authority_role": "cultural-authority",
        "authority_basis_uri": f"{community_uri}/mandate/rights",
        "conferred_by_agent_uri": community_uri,
        "subject_matter_uris": [target_uri, PROTOCOL_RESOURCE],
        "covered_validation_dimensions": covered_dimensions or ["rights"],
        "covered_action_uris": [
            controlled_value_uri("use-action", action)
            for action in ("display", "index", "export")
        ],
        "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_until": "2026-03-01T00:00:00Z" if revoked else None,
        "delegation_permitted": False,
        "status": status,
        "revocation_event_uri": (
            f"{community_uri}/mandate/revocation" if revoked else None
        ),
        "revocation_effect": "prospective" if revoked else None,
        "rights_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
        "evidence": [
            {
                "citation": f"Rights mandate from {community_uri}",
                "evidence_type": "rights-protocol",
                "relation": "documents",
                "resource_uri": f"{community_uri}/mandate/rights",
                "note": "Documents the represented community's rights mandate.",
            }
        ],
    }


def _authorities(target_uri: str) -> list[dict]:
    return [
        _authority(target_uri, COMMUNITY_A),
        _authority(target_uri, COMMUNITY_B),
    ]


def _protocol(
    target_uri: str,
    *,
    resolution_status: str = "verified",
    protocol_integrity_sha256: str | None = "a" * 64,
) -> dict:
    return {
        "uri": PROTOCOL_APPLICATION,
        "target_resource_uris": [target_uri],
        "protocol_uri": PROTOCOL_RESOURCE,
        "protocol_type_uri": "https://example.org/protocol/type/cultural",
        "issued_by_agent_uri": COMMUNITY_A,
        "applied_by_agent_uri": AUTHORIZED_AGENT,
        "represented_community_uris": [COMMUNITY_A, COMMUNITY_B],
        "authority_assignment_uris": [
            _authority_uri(COMMUNITY_A),
            _authority_uri(COMMUNITY_B),
        ],
        "source_record_uri": None,
        "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
        "enforcement_mode": "human-decision-required",
        "status": "active",
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_until": None,
        "supersedes_uri": None,
        "retrieved_at": "2026-01-01T00:00:00Z",
        "resolution_status": resolution_status,
        "integrity_verification_method": (
            "external-attestation" if resolution_status == "verified" else "none"
        ),
        "protocol_artifact_path": None,
        "integrity_attestation_uri": (
            "https://example.org/protocol/attestation/1"
            if resolution_status == "verified"
            else None
        ),
        "protocol_integrity_sha256": protocol_integrity_sha256,
    }


def _use_decision(
    suffix: str,
    target_uri: str,
    action: str,
    represented_communities: list[str],
    decision: str = "granted",
    *,
    purpose_uris: list[str] | None = None,
    audience_uris: list[str] | None = None,
    applicability_scope_uris: list[str] | None = None,
    legal_basis_status: str = "documented",
    legal_basis_uris: list[str] | None = None,
    consent_status: str = "documented",
    consent_record_uris: list[str] | None = None,
) -> dict:
    authority_uris = [
        _authority_uri(community_uri) for community_uri in represented_communities
    ]
    return {
        "uri": f"https://example.org/use-decision/{suffix}",
        "target_resource_uris": [target_uri],
        "action_uris": [controlled_value_uri("use-action", action)],
        "purpose_uris": purpose_uris or [PUBLICATION_PURPOSE],
        "audience_uris": audience_uris or [PUBLICATION_AUDIENCE],
        "decision": decision,
        "decided_by_agent_uri": AUTHORIZED_AGENT,
        "represented_community_uris": represented_communities,
        "authority_assignment_uris": authority_uris,
        "protocol_application_uris": [PROTOCOL_APPLICATION],
        "applicability_scope_uris": (applicability_scope_uris or [SOURCE_SILENT_SCOPE]),
        "decision_method_uri": "https://example.org/method/community-decision",
        "decided_at": "2026-02-01T00:00:00Z",
        "valid_until": None,
        "status": "active",
        "supersedes_decision_uri": None,
        "public_evidence_uri": None,
        "public_summary": None,
        "legal_basis_uris": (
            ["https://example.org/legal-basis/publication"]
            if legal_basis_uris is None
            else legal_basis_uris
        ),
        "legal_basis_status": legal_basis_status,
        "legal_basis_assessed_by_agent_uri": PROJECT_AGENT,
        "consent_record_uris": (
            ["https://example.org/consent/publication"]
            if consent_record_uris is None
            else consent_record_uris
        ),
        "consent_status": consent_status,
        "consent_assessed_by_agent_uri": PROJECT_AGENT,
    }


def _publication_authorization(
    dataset: Dataset,
    target_uri: str,
    action: str,
    *,
    purpose_uris: list[str] | None = None,
    audience_uris: list[str] | None = None,
    applicability_scope_uris: list[str] | None = None,
) -> dict:
    return dataset.publication_authorization(
        target_uri,
        controlled_value_uri("use-action", action),
        purpose_uris=purpose_uris or [PUBLICATION_PURPOSE],
        audience_uris=audience_uris or [PUBLICATION_AUDIENCE],
        applicability_scope_uris=(applicability_scope_uris or [SOURCE_SILENT_SCOPE]),
        requires_explicit_decision=True,
    )


def test_publication_authorization_fails_closed_by_action_and_community(
    canonical_dataset: Dataset,
):
    dataset = copy.copy(canonical_dataset)
    target = "https://example.org/resource/community-governed"
    dataset.authority_assignments = _authorities(target)
    dataset.protocol_applications = [_protocol(target)]
    dataset.use_decisions = []

    result = _publication_authorization(dataset, target, "export")
    assert result["authorized"] is False
    assert result["reason"] == "explicit-authorization-required"
    assert set(result["missing_community_uris"]) == {COMMUNITY_A, COMMUNITY_B}

    dataset.use_decisions = [_use_decision("export-a", target, "export", [COMMUNITY_A])]
    result = _publication_authorization(dataset, target, "export")
    assert result["authorized"] is False
    assert result["missing_community_uris"] == [COMMUNITY_B]

    dataset.use_decisions.append(
        _use_decision("export-b", target, "export", [COMMUNITY_B])
    )
    assert _publication_authorization(dataset, target, "export")["authorized"] is True
    assert _publication_authorization(dataset, target, "display")["authorized"] is False

    dataset.use_decisions.append(
        _use_decision("export-refusal", target, "export", [COMMUNITY_B], "refused")
    )
    result = _publication_authorization(dataset, target, "export")
    assert result["authorized"] is False
    assert result["reason"] == "active-denial"


def test_governance_records_satisfy_their_json_schemas(
    repo_root: Path, canonical_dataset: Dataset
):
    target = "https://example.org/resource/community-governed"
    for authority in _authorities(target):
        _assert_schema_valid(repo_root, "authority_assignment.schema.json", authority)
    _assert_schema_valid(
        repo_root, "protocol_application.schema.json", _protocol(target)
    )
    _assert_schema_valid(
        repo_root,
        "use_decision.schema.json",
        _use_decision("schema", target, "export", [COMMUNITY_A, COMMUNITY_B]),
    )


def test_publication_grants_do_not_leak_across_purpose_audience_or_scope(
    canonical_dataset: Dataset,
):
    dataset = copy.copy(canonical_dataset)
    target = "https://example.org/resource/community-governed"
    communities = [COMMUNITY_A, COMMUNITY_B]
    dataset.authority_assignments = _authorities(target)
    dataset.protocol_applications = [_protocol(target)]
    dataset.use_decisions = [_use_decision("export", target, "export", communities)]

    assert _publication_authorization(dataset, target, "export")["authorized"] is True
    mismatches = (
        {"purpose_uris": ["https://example.org/purpose/commercial"]},
        {"audience_uris": ["https://example.org/audience/private"]},
        {"applicability_scope_uris": ["https://example.org/scope/other"]},
    )
    for mismatch in mismatches:
        result = _publication_authorization(dataset, target, "export", **mismatch)
        assert result["authorized"] is False
        assert result["reason"] == "explicit-authorization-required"


@pytest.mark.parametrize(
    "authority_change",
    [
        {"status": "revoked"},
        {"covered_validation_dimensions": ["community"]},
    ],
    ids=["revoked-authority", "authority-without-rights-dimension"],
)
def test_publication_rejects_invalid_or_revoked_authority(
    canonical_dataset: Dataset, authority_change: dict
):
    dataset = copy.copy(canonical_dataset)
    target = "https://example.org/resource/community-governed"
    authorities = _authorities(target)
    authorities[0].update(authority_change)
    if authority_change.get("status") == "revoked":
        authorities[0].update(
            {
                "valid_until": "2026-03-01T00:00:00Z",
                "revocation_event_uri": (
                    "https://example.org/community/a/mandate/revocation"
                ),
                "revocation_effect": "prospective",
            }
        )
    dataset.authority_assignments = authorities
    dataset.protocol_applications = [_protocol(target)]
    dataset.use_decisions = [
        _use_decision("export", target, "export", [COMMUNITY_A, COMMUNITY_B])
    ]

    result = _publication_authorization(dataset, target, "export")
    assert result["authorized"] is False
    assert result["reason"] == "authorization-prerequisites-incomplete"


@pytest.mark.parametrize("resolution_status", ["unverified", "unavailable"])
def test_publication_rejects_unverified_protocol_resolution(
    canonical_dataset: Dataset, resolution_status: str
):
    dataset = copy.copy(canonical_dataset)
    target = "https://example.org/resource/community-governed"
    dataset.authority_assignments = _authorities(target)
    dataset.protocol_applications = [
        _protocol(
            target,
            resolution_status=resolution_status,
            protocol_integrity_sha256=None,
        )
    ]
    dataset.use_decisions = [
        _use_decision("export", target, "export", [COMMUNITY_A, COMMUNITY_B])
    ]

    result = _publication_authorization(dataset, target, "export")
    assert result["authorized"] is False
    assert result["reason"] == "protocol-integrity-unverified"


@pytest.mark.parametrize(
    "decision_change",
    [
        {"legal_basis_status": "unknown", "legal_basis_uris": []},
        {"legal_basis_status": "documented", "legal_basis_uris": []},
        {"consent_status": "unknown", "consent_record_uris": []},
        {"consent_status": "withheld", "consent_record_uris": []},
        {"consent_status": "documented", "consent_record_uris": []},
        {"legal_basis_status": "not-required", "legal_basis_uris": []},
        {
            "legal_basis_status": "not-required",
            "legal_basis_assessed_by_agent_uri": None,
        },
        {"consent_status": "not-required", "consent_record_uris": []},
        {
            "consent_status": "not-required",
            "consent_assessed_by_agent_uri": None,
        },
    ],
    ids=[
        "unknown-legal-basis",
        "missing-legal-record",
        "unknown-consent",
        "withheld-consent",
        "missing-consent-record",
        "not-required-legal-reference-missing",
        "not-required-legal-assessor-missing",
        "not-required-consent-reference-missing",
        "not-required-consent-assessor-missing",
    ],
)
def test_publication_rejects_incomplete_legal_or_consent_prerequisites(
    canonical_dataset: Dataset, decision_change: dict
):
    dataset = copy.copy(canonical_dataset)
    target = "https://example.org/resource/community-governed"
    dataset.authority_assignments = _authorities(target)
    dataset.protocol_applications = [_protocol(target)]
    decision = _use_decision("export", target, "export", [COMMUNITY_A, COMMUNITY_B])
    decision.update(decision_change)
    dataset.use_decisions = [decision]

    result = _publication_authorization(dataset, target, "export")
    assert result["authorized"] is False
    assert result["reason"] == "authorization-prerequisites-incomplete"


def test_not_required_legal_and_consent_determinations_remain_attributed(
    repo_root: Path, canonical_dataset: Dataset
):
    dataset = copy.copy(canonical_dataset)
    target = "https://example.org/resource/community-governed"
    dataset.authority_assignments = _authorities(target)
    dataset.protocol_applications = [_protocol(target)]
    decision = _use_decision(
        "not-required",
        target,
        "export",
        [COMMUNITY_A, COMMUNITY_B],
        legal_basis_status="not-required",
        consent_status="not-required",
    )
    dataset.use_decisions = [decision]

    _assert_schema_valid(repo_root, "use_decision.schema.json", decision)
    result = _publication_authorization(dataset, target, "export")
    assert result["authorized"] is True
    assert decision["legal_basis_uris"]
    assert decision["legal_basis_assessed_by_agent_uri"]
    assert decision["consent_record_uris"]
    assert decision["consent_assessed_by_agent_uri"]


def _multidimensional_governance_dataset(
    canonical_dataset: Dataset,
) -> tuple[Dataset, dict[str, list[str]], dict]:
    dataset = copy.copy(canonical_dataset)
    dimensions = {
        "targets": [
            "https://example.org/resource/community-governed-1",
            "https://example.org/resource/community-governed-2",
        ],
        "purposes": [
            PUBLICATION_PURPOSE,
            "https://example.org/purpose/accessibility",
        ],
        "audiences": [
            PUBLICATION_AUDIENCE,
            "https://example.org/audience/researchers",
        ],
        "scopes": [SOURCE_SILENT_SCOPE, "https://example.org/scope/exhibition"],
        "protocols": [
            PROTOCOL_APPLICATION,
            "https://example.org/protocol/application-2",
        ],
    }
    protocols: list[dict] = []
    for index, application_uri in enumerate(dimensions["protocols"], 1):
        protocol = _protocol(dimensions["targets"][0])
        protocol.update(
            {
                "uri": application_uri,
                "target_resource_uris": dimensions["targets"],
                "protocol_uri": f"https://example.org/protocol/cultural-care-{index}",
                "applicability_scope_uris": dimensions["scopes"],
                "integrity_attestation_uri": (
                    f"https://example.org/protocol/attestation/{index}"
                ),
            }
        )
        protocols.append(protocol)
    authorities = _authorities(dimensions["targets"][0])
    for authority in authorities:
        authority["subject_matter_uris"] = [
            *dimensions["targets"],
            *(row["uri"] for row in protocols),
            *(row["protocol_uri"] for row in protocols),
        ]
        authority["applicability_scope_uris"] = dimensions["scopes"]
    decision = _use_decision(
        "complete-multidimensional",
        dimensions["targets"][0],
        "export",
        [COMMUNITY_A, COMMUNITY_B],
    )
    decision.update(
        {
            "target_resource_uris": dimensions["targets"],
            "purpose_uris": dimensions["purposes"],
            "audience_uris": dimensions["audiences"],
            "applicability_scope_uris": dimensions["scopes"],
            "protocol_application_uris": dimensions["protocols"],
        }
    )
    dataset.authority_assignments = authorities
    dataset.protocol_applications = protocols
    dataset.use_decisions = [decision]
    return dataset, dimensions, decision


def _multidimensional_authorization(
    dataset: Dataset, dimensions: dict[str, list[str]]
) -> dict:
    return dataset.publication_authorization(
        dimensions["targets"],
        controlled_value_uri("use-action", "export"),
        purpose_uris=dimensions["purposes"],
        audience_uris=dimensions["audiences"],
        applicability_scope_uris=dimensions["scopes"],
        requires_explicit_decision=True,
    )


def test_partial_multidimensional_grants_never_authorize_the_whole_request(
    canonical_dataset: Dataset,
):
    dataset, dimensions, complete = _multidimensional_governance_dataset(
        canonical_dataset
    )
    assert _multidimensional_authorization(dataset, dimensions)["authorized"] is True

    reductions = {
        "target_resource_uris": dimensions["targets"][:1],
        "purpose_uris": dimensions["purposes"][:1],
        "audience_uris": dimensions["audiences"][:1],
        "applicability_scope_uris": dimensions["scopes"][:1],
        "protocol_application_uris": dimensions["protocols"][:1],
    }
    for field, partial_value in reductions.items():
        partial = copy.deepcopy(complete)
        partial[field] = partial_value
        partial["uri"] = f"https://example.org/use-decision/partial-{field}"
        dataset.use_decisions = [partial]
        result = _multidimensional_authorization(dataset, dimensions)
        assert result["authorized"] is False, field


def test_authority_missing_the_requested_publication_action_cannot_grant(
    canonical_dataset: Dataset,
):
    dataset, dimensions, _ = _multidimensional_governance_dataset(canonical_dataset)
    for authority in dataset.authority_assignments:
        authority["covered_action_uris"] = [
            controlled_value_uri("use-action", "display")
        ]

    result = _multidimensional_authorization(dataset, dimensions)
    assert result["authorized"] is False
    assert result["reason"] == "authorization-prerequisites-incomplete"


def test_partial_authority_subject_coverage_cannot_authorize_all_targets(
    canonical_dataset: Dataset,
):
    dataset, dimensions, _ = _multidimensional_governance_dataset(canonical_dataset)
    dataset.authority_assignments[0]["subject_matter_uris"] = [
        dimensions["targets"][0],
    ]

    result = _multidimensional_authorization(dataset, dimensions)
    assert result["authorized"] is False
    assert result["reason"] == "authorization-prerequisites-incomplete"


def test_local_protocol_sha256_is_verified_and_mismatch_fails(
    tmp_path: Path, canonical_dataset: Dataset
):
    payload = b"Locally pinned community protocol, version 1.\n"
    relative_path = Path("protocols/community-protocol.txt")
    artifact = tmp_path / relative_path
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(payload)
    protocol = _protocol("https://example.org/resource/community-governed")
    protocol.update(
        {
            "integrity_verification_method": "local-sha256",
            "protocol_artifact_path": relative_path.as_posix(),
            "integrity_attestation_uri": None,
            "protocol_integrity_sha256": hashlib.sha256(payload).hexdigest(),
        }
    )
    dataset = copy.copy(canonical_dataset)
    dataset.root = tmp_path

    assert dataset.protocol_integrity_valid(protocol) is True
    protocol["protocol_integrity_sha256"] = "0" * 64
    assert dataset.protocol_integrity_valid(protocol) is False


def test_public_build_guard_requires_every_publication_action(
    canonical_dataset: Dataset,
):
    dataset = copy.copy(canonical_dataset)
    target = "https://example.org/resource/community-governed"
    communities = [COMMUNITY_A, COMMUNITY_B]
    dataset.authority_assignments = _authorities(target)
    dataset.protocol_applications = [_protocol(target)]
    dataset.use_decisions = [
        _use_decision("export", target, "export", communities),
    ]
    with pytest.raises(ValidationError, match="action-specific authorization"):
        dataset.assert_publication_authorized()

    dataset.use_decisions.extend(
        [
            _use_decision("display", target, "display", communities),
            _use_decision("index", target, "index", communities),
        ]
    )
    dataset.assert_publication_authorized()


def _organological_records(canonical_dataset: Dataset) -> tuple[dict, dict]:
    classification = next(
        row for row in canonical_dataset.concepts if row["kind"] == "classification"
    )
    instrument = next(
        row
        for row in canonical_dataset.concepts
        if row["kind"] == "instrument" and row["resolution_status"] == "resolved"
    )
    criterion = {
        "uri": "https://example.org/criterion/bore-diameter",
        "label": "Bore diameter criterion",
        "description": "A measured bore-diameter range used as documented evidence.",
        "criterion_type": "bore-profile",
        "observable_property_uris": ["https://example.org/property/bore-diameter"],
        "procedure_uris": ["https://example.org/procedure/caliper-measurement"],
        "classification_scheme_uri": classification["scheme_uri"],
        "scheme_version_uri": canonical_dataset.concept_schemes[0]["version_uri"],
        "conclusion_classification_uris": [classification["uri"]],
        "inference_logic_uri": "https://example.org/rule/bore-diameter-criterion",
        "asserted_by_uri": PROJECT_AGENT,
        "perspective_uri": MIMO_PERSPECTIVE,
        "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
        "authority_assignment_uris": [],
        "protocol_application_uris": [],
        "source_record_uri": None,
        "evidence": [_evidence("supports", "criterion")],
        "rights_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
        "status": "active",
    }
    observation = {
        "uri": "https://example.org/observation/bore-diameter-1",
        "feature_of_interest_uri": instrument["uri"],
        "assessed_part_uri": None,
        "assessed_property_uri": "https://example.org/property/bore-diameter",
        "assessment_status": "detected",
        "result": {
            "kind": "range",
            "minimum_value": 12.1,
            "maximum_value": 12.4,
            "unit_uri": "http://qudt.org/vocab/unit/MilliM",
            "uncertainty": 0.1,
        },
        "assessment_procedure_uri": "https://example.org/procedure/caliper-measurement",
        "assessment_agent_uri": PROJECT_AGENT,
        "assessment_sensor_uri": "https://example.org/sensor/caliper-1",
        "phenomenon_start": "2026-06-01T10:00:00Z",
        "phenomenon_end": "2026-06-01T10:05:00Z",
        "assessment_time": "2026-06-01T10:05:00Z",
        "perspective_uri": MIMO_PERSPECTIVE,
        "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
        "source_record_uri": None,
        "evidence": [_evidence("documents", "observation")],
        "rights_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
        "protocol_application_uris": [],
        "authority_assignment_uris": [],
        "review_status": "unreviewed",
        "review_status_uri": review_status_uri("unreviewed"),
    }
    return criterion, observation


def _target_record(
    uri: str,
    target_kind: str,
    instrument_concept_uri: str,
) -> dict:
    return {
        "uri": uri,
        "label": uri.rsplit("/", 1)[-1].replace("-", " "),
        "target_kind": target_kind,
        "realizes_instrument_concept_uris": [instrument_concept_uri],
        "configuration_of_uri": None,
        "component_of_uri": None,
        "component_role_uri": None,
        "has_component_uris": [],
        "has_functional_module_uris": [],
        "condition_state_of_uri": None,
        "valid_from": None,
        "valid_until": None,
        "generated_by_event_uri": None,
        "ended_by_event_uri": None,
        "performance_event_uri": None,
        "actual_playing_technique_uris": [],
        "intended_playing_technique_uris": [],
        "source_record_uri": None,
        "perspective_uri": MIMO_PERSPECTIVE,
        "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
        "rights_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
        "protocol_application_uris": [],
        "authority_assignment_uris": [],
    }


def test_target_structure_rejects_inverse_cycle_and_kind_errors(
    canonical_dataset: Dataset,
):
    instrument_uri = next(
        row["uri"]
        for row in canonical_dataset.concepts
        if row["kind"] == "instrument" and row["resolution_status"] == "resolved"
    )
    inverse_parent = _target_record(
        "https://example.org/target/inverse-parent", "physical-object", instrument_uri
    )
    inverse_child = _target_record(
        "https://example.org/target/inverse-child",
        "instrument-component",
        instrument_uri,
    )
    inverse_parent["has_component_uris"] = [inverse_child["uri"]]

    cycle_a = _target_record(
        "https://example.org/target/cycle-a", "instrument-component", instrument_uri
    )
    cycle_b = _target_record(
        "https://example.org/target/cycle-b", "instrument-component", instrument_uri
    )
    cycle_a.update(
        {
            "component_of_uri": cycle_b["uri"],
            "component_role_uri": "https://example.org/role/cycle-component",
            "has_component_uris": [cycle_b["uri"]],
        }
    )
    cycle_b.update(
        {
            "component_of_uri": cycle_a["uri"],
            "component_role_uri": "https://example.org/role/cycle-component",
            "has_component_uris": [cycle_a["uri"]],
        }
    )

    kind_parent = _target_record(
        "https://example.org/target/kind-parent", "physical-object", instrument_uri
    )
    kind_child = _target_record(
        "https://example.org/target/kind-child", "physical-object", instrument_uri
    )
    kind_parent["has_component_uris"] = [kind_child["uri"]]
    kind_child.update(
        {
            "component_of_uri": kind_parent["uri"],
            "component_role_uri": "https://example.org/role/invalid-component",
        }
    )
    records = [
        inverse_parent,
        inverse_child,
        cycle_a,
        cycle_b,
        kind_parent,
        kind_child,
    ]
    dataset = copy.copy(canonical_dataset)
    dataset.metadata = copy.deepcopy(canonical_dataset.metadata)
    dataset.metadata["counts"]["organological_targets"] = len(records)
    dataset.organological_targets = records

    with pytest.raises(ValidationError) as exc_info:
        dataset.validate()
    message = str(exc_info.value)
    assert "component parent/inverse mismatch" in message
    assert "organological target relation contains a cycle: component_of_uri" in message
    assert "target kind cannot be a component" in message


def _reasoning_chain_dataset(
    canonical_dataset: Dataset,
) -> tuple[Dataset, dict, dict, dict]:
    dataset = copy.copy(canonical_dataset)
    dataset.metadata = copy.deepcopy(canonical_dataset.metadata)
    source_assertion = canonical_dataset.classification_assertions[0]
    classification_uri = source_assertion["classification_uri"]
    target_uri = source_assertion["target_uri"]
    criterion, observation = _organological_records(canonical_dataset)
    inference_logic_uri = "https://example.org/inference/bore-rule"
    criterion.update(
        {
            "classification_scheme_uri": source_assertion["classification_scheme_uri"],
            "scheme_version_uri": source_assertion["scheme_version_uri"],
            "conclusion_classification_uris": [classification_uri],
            "inference_logic_uri": inference_logic_uri,
        }
    )
    observation.update(
        {
            "feature_of_interest_uri": target_uri,
            "assessed_property_uri": criterion["observable_property_uris"][0],
            "assessment_procedure_uri": criterion["procedure_uris"][0],
        }
    )
    source_uri = "https://example.org/analysis/classification-1"
    method_uri = "https://example.org/method/observational-classification"
    assertion_uri = classification_assertion_uri(
        classification_uri,
        target_uri,
        source_record_uri=source_assertion["source_record_uri"],
        assigned_by_uri=PROJECT_AGENT,
        perspective_uri=MIMO_PERSPECTIVE,
        classification_method_uri=method_uri,
        source_uri=source_uri,
    )
    assertion = {
        "uri": assertion_uri,
        "assignment_uri": classification_assignment_uri(assertion_uri),
        "target_uri": target_uri,
        "target_type": "instrument-concept",
        "predicate_uri": "https://w3id.org/modavis/omaro#classifiedAs",
        "classification_uri": classification_uri,
        "classification_scheme_uri": source_assertion["classification_scheme_uri"],
        "scheme_version_uri": source_assertion["scheme_version_uri"],
        "assigned_by_uri": PROJECT_AGENT,
        "generated_by_uri": PROJECT_AGENT,
        "perspective_uri": MIMO_PERSPECTIVE,
        "classification_method_uri": method_uri,
        "criteria_uris": [criterion["uri"]],
        "assessment_uris": [observation["uri"]],
        "inference_logic_uri": inference_logic_uri,
        "classification_expression_uri": None,
        "stance": "proposed",
        "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
        "evidence": [_evidence("supports", "classification-chain")],
        "authority_assignment_uris": [],
        "valid_from": None,
        "valid_until": None,
        "projection_policy_uris": [CLAIMS_POLICY],
        "source_predicate_uri": None,
        "source_uri": source_uri,
        "source_record_uri": source_assertion["source_record_uri"],
        "assertion_origin": "scholarly-asserted",
    }
    dataset.classification_criteria = [criterion]
    dataset.observation_assessments = [observation]
    dataset.classification_assertions = [
        *canonical_dataset.classification_assertions,
        assertion,
    ]
    dataset.metadata["counts"]["classification_criteria"] = 1
    dataset.metadata["counts"]["observation_assessments"] = 1
    dataset.metadata["counts"]["classification_assertions"] = len(
        dataset.classification_assertions
    )
    return dataset, assertion, criterion, observation


def _registered_target_classification_dataset(
    canonical_dataset: Dataset,
) -> tuple[Dataset, dict, dict]:
    dataset, assertion, _, observation = _reasoning_chain_dataset(canonical_dataset)
    target = _target_record(
        "https://example.org/target/physical-object-1",
        "physical-object",
        assertion["target_uri"],
    )
    assertion_uri = classification_assertion_uri(
        assertion["classification_uri"],
        target["uri"],
        source_record_uri=assertion["source_record_uri"],
        assigned_by_uri=assertion["assigned_by_uri"],
        perspective_uri=assertion["perspective_uri"],
        classification_method_uri=assertion["classification_method_uri"],
        source_uri=assertion["source_uri"],
    )
    assertion.update(
        {
            "uri": assertion_uri,
            "assignment_uri": classification_assignment_uri(assertion_uri),
            "target_uri": target["uri"],
            "target_type": "physical-object",
        }
    )
    observation["feature_of_interest_uri"] = target["uri"]
    dataset.organological_targets = [target]
    dataset.metadata["counts"]["organological_targets"] = 1
    return dataset, assertion, target


def test_registered_target_classification_type_matches_kind(
    repo_root: Path, canonical_dataset: Dataset
):
    dataset, _, _ = _registered_target_classification_dataset(canonical_dataset)

    summary = dataset.validate(repo_root / "schema")

    assert summary["organological_targets"] == 1
    assert summary["classification_assertions"] == 1873


def test_registered_target_classification_rejects_type_kind_mismatch(
    canonical_dataset: Dataset,
):
    dataset, assertion, target = _registered_target_classification_dataset(
        canonical_dataset
    )
    assertion["target_type"] = "functional-module"

    with pytest.raises(ValidationError) as exc_info:
        dataset.validate()

    assert (
        "classification assertion target type/kind mismatch: "
        f"{assertion['uri']} declares functional-module but {target['uri']} is "
        "physical-object"
    ) in str(exc_info.value)


def test_instrument_concept_target_validation_is_preserved(
    canonical_dataset: Dataset,
):
    dataset, assertion, _, observation = _reasoning_chain_dataset(canonical_dataset)
    non_instrument_concept_uri = assertion["classification_uri"]
    assertion["target_uri"] = non_instrument_concept_uri
    observation["feature_of_interest_uri"] = non_instrument_concept_uri

    with pytest.raises(ValidationError) as exc_info:
        dataset.validate()

    assert (
        "classification assertion subject is not an instrument: "
        f"{non_instrument_concept_uri}"
    ) in str(exc_info.value)


def test_shacl_rejects_registered_target_type_kind_mismatch(
    repo_root: Path, canonical_dataset: Dataset
):
    dataset, assertion, target = _registered_target_classification_dataset(
        canonical_dataset
    )
    graph = dataset_graph(dataset)
    assertion_node = URIRef(assertion["uri"])
    target_node = URIRef(target["uri"])
    physical_object = URIRef(controlled_value_uri("target-type", "physical-object"))
    assert (assertion_node, OMARO_NS.targetType, physical_object) in graph
    assert (target_node, OMARO_NS.targetKind, physical_object) in graph

    invalid_graph = Graph()
    invalid_graph.add((assertion_node, RDF.type, OMARO_NS.ClassificationAssertion))
    invalid_graph.add((assertion_node, RDF.subject, target_node))
    invalid_graph.add(
        (
            assertion_node,
            OMARO_NS.targetType,
            URIRef(controlled_value_uri("target-type", "functional-module")),
        )
    )
    invalid_graph.add((target_node, RDF.type, OMARO_NS.OrganologicalTarget))
    invalid_graph.add((target_node, OMARO_NS.targetKind, physical_object))

    conforms, _, report = shacl_validate(
        invalid_graph,
        shacl_graph=str(repo_root / "schema/dataset.shacl.ttl"),
        inference="rdfs",
    )

    assert not conforms
    assert (
        "Classification assertion target type does not match the registered "
        "organological target kind."
    ) in report


def test_observation_criterion_inference_assertion_chain_validates(
    repo_root: Path, canonical_dataset: Dataset
):
    dataset, _, _, _ = _reasoning_chain_dataset(canonical_dataset)
    summary = dataset.validate(repo_root / "schema")
    assert summary["classification_assertions"] == 1873
    assert summary["classification_criteria"] == 1
    assert summary["observation_assessments"] == 1


def test_reasoning_chain_mismatches_are_rejected(canonical_dataset: Dataset):
    dataset, assertion, criterion, observation = _reasoning_chain_dataset(
        canonical_dataset
    )
    criterion["conclusion_classification_uris"] = [
        next(
            row["uri"]
            for row in canonical_dataset.concepts
            if row["kind"] == "classification"
            and row["scheme_uri"] == assertion["classification_scheme_uri"]
            and row["uri"] != assertion["classification_uri"]
        )
    ]
    criterion["inference_logic_uri"] = "https://example.org/inference/other-rule"
    observation["assessed_property_uri"] = "https://example.org/property/other"
    observation["assessment_procedure_uri"] = "https://example.org/procedure/other"
    observation["feature_of_interest_uri"] = next(
        row["uri"]
        for row in canonical_dataset.concepts
        if row["kind"] == "instrument" and row["uri"] != assertion["target_uri"]
    )

    with pytest.raises(ValidationError) as exc_info:
        dataset.validate()
    message = str(exc_info.value)
    assert "classification is not a declared criterion conclusion" in message
    assert "classification and criterion use different inference logic" in message
    assert "classification inference logic is not declared by a criterion" in message
    assert "classification assessment matches no referenced criterion" in message
    assert "classification assessment is unrelated to its target" in message
    assert "classification criterion has no matching assessment" in message


@pytest.fixture(scope="module")
def observation_projection(canonical_dataset: Dataset):
    dataset = copy.copy(canonical_dataset)
    criterion, detected = _organological_records(canonical_dataset)
    records: dict[str, dict] = {}
    for status in (
        "detected",
        "not-detected",
        "indeterminate",
        "not-observed",
        "not-applicable",
    ):
        record = copy.deepcopy(detected)
        record["uri"] = f"https://example.org/assessment/{status}"
        record["assessment_status"] = status
        if status == "not-detected":
            record["result"] = {
                "kind": "resource",
                "value_uri": "https://example.org/result/feature-absent",
            }
        elif status != "detected":
            record["result"] = None
        if status in {"not-observed", "not-applicable"}:
            record["assessment_sensor_uri"] = None
            record["phenomenon_start"] = None
            record["phenomenon_end"] = None
        records[status] = record

    assertion = copy.deepcopy(canonical_dataset.classification_assertions[0])
    assertion["criteria_uris"] = [criterion["uri"]]
    assertion["assessment_uris"] = [record["uri"] for record in records.values()]
    assertion["inference_logic_uri"] = "https://example.org/inference/rule-1"
    assertion["classification_expression_uri"] = None
    retained_concept_uris = {assertion["classification_uri"], assertion["target_uri"]}

    dataset.concepts = [
        row for row in canonical_dataset.concepts if row["uri"] in retained_concept_uris
    ]
    dataset.labels = []
    dataset.label_resources = []
    dataset.label_profiles = []
    dataset.label_assertions = []
    dataset.note_assertions = []
    dataset.source_relations = []
    dataset.concept_relation_assertions = []
    dataset.quality_findings = []
    dataset.quality_rules = []
    dataset.review_events = []
    dataset.protocol_applications = []
    dataset.use_decisions = []
    dataset.organological_targets = []
    dataset.classification_criteria = [criterion]
    dataset.observation_assessments = list(records.values())
    dataset.classification_expressions = []
    dataset.classification_assertions = [assertion]
    return dataset_graph(dataset), assertion, records


def test_cidoc_extension_namespaces_are_official_and_not_legacy(
    observation_projection,
):
    graph, _, records = observation_projection
    actual_nodes = {
        URIRef(records[status]["uri"])
        for status in ("detected", "not-detected", "indeterminate")
    }
    s27 = CRMSCI.S27_Observation

    assert str(CRMINF) == "http://www.cidoc-crm.org/extensions/crminf/"
    assert str(CRMSCI) == "http://www.cidoc-crm.org/extensions/crmsci/"
    assert set(graph.subjects(RDF.type, s27)) == actual_nodes
    legacy_prefixes = (
        "http://www.cidoc-crm.org/crminf/",
        "http://www.cidoc-crm.org/crmsci/",
    )
    assert not any(
        isinstance(term, URIRef) and str(term).startswith(legacy_prefixes)
        for triple in graph
        for term in triple
    )


def test_crminf_is_not_claimed_without_a_complete_inference_bridge(
    observation_projection,
):
    graph, assertion, _ = observation_projection
    assignment = URIRef(assertion["assignment_uri"])
    inference_logic = URIRef(assertion["inference_logic_uri"])

    assert (assignment, OMARO_NS.inferenceLogic, inference_logic) in graph
    assert (assignment, RDF.type, CRMINF.I5_Inference_Making) not in graph
    assert not list(graph.objects(assignment, CRMINF.J3_applied))
    assert not any(
        isinstance(term, URIRef) and str(term).startswith(str(CRMINF))
        for triple in graph
        for term in triple
    )


def test_assignment_distinguishes_assessments_from_actual_observations(
    observation_projection,
):
    graph, assertion, records = observation_projection
    assignment = URIRef(assertion["assignment_uri"])
    all_assessments = {URIRef(record["uri"]) for record in records.values()}
    actual_observations = {
        URIRef(records[status]["uri"])
        for status in ("detected", "not-detected", "indeterminate")
    }

    assert set(graph.objects(assignment, OMARO_NS.usedAssessment)) == all_assessments
    assert set(graph.objects(assignment, OMARO_NS.usedObservation)) == (
        actual_observations
    )


def test_shacl_rejects_nonattempt_assessment_typed_as_observation(
    repo_root: Path, observation_projection
):
    graph, _, records = observation_projection
    invalid_graph = Graph()
    for triple in graph:
        invalid_graph.add(triple)
    node = URIRef(records["not-observed"]["uri"])
    invalid_graph.add((node, RDF.type, OMARO_NS.OrganologicalObservation))
    invalid_graph.add((node, RDF.type, SOSA.Observation))
    invalid_graph.add((node, RDF.type, CRMSCI.S27_Observation))

    conforms, _, report = shacl_validate(
        invalid_graph,
        shacl_graph=str(repo_root / "schema/dataset.shacl.ttl"),
        inference="none",
        advanced=True,
    )
    assert conforms is False
    assert (
        "A non-observation or non-applicability assessment must not be typed "
        "as an observation activity."
    ) in report


def test_shacl_requires_a_result_for_not_detected_observation(
    repo_root: Path, observation_projection
):
    graph, _, records = observation_projection
    invalid_graph = Graph()
    for triple in graph:
        invalid_graph.add(triple)
    node = URIRef(records["not-detected"]["uri"])
    invalid_graph.remove((node, OMARO_NS.assessmentResult, None))
    invalid_graph.remove((node, SOSA.hasResult, None))

    conforms, _, report = shacl_validate(
        invalid_graph,
        shacl_graph=str(repo_root / "schema/dataset.shacl.ttl"),
        inference="none",
        advanced=True,
    )
    assert conforms is False
    assert (
        "A detected or not-detected observation must have exactly one result." in report
    )


def test_shacl_rejects_result_on_nonattempt_assessment(
    repo_root: Path, observation_projection
):
    graph, _, records = observation_projection
    invalid_graph = Graph()
    for triple in graph:
        invalid_graph.add(triple)
    node = URIRef(records["not-applicable"]["uri"])
    result = next(
        graph.objects(URIRef(records["detected"]["uri"]), OMARO_NS.assessmentResult)
    )
    invalid_graph.add((node, OMARO_NS.assessmentResult, result))

    conforms, _, report = shacl_validate(
        invalid_graph,
        shacl_graph=str(repo_root / "schema/dataset.shacl.ttl"),
        inference="none",
        advanced=True,
    )
    assert conforms is False
    assert (
        "A non-observation or non-applicability assessment must not have a result."
        in report
    )


def test_shacl_rejects_sosa_property_on_nonattempt_assessment(
    repo_root: Path, observation_projection
):
    graph, _, records = observation_projection
    invalid_graph = Graph()
    for triple in graph:
        invalid_graph.add(triple)
    node = URIRef(records["not-observed"]["uri"])
    invalid_graph.add(
        (
            node,
            SOSA.hasFeatureOfInterest,
            URIRef(records["not-observed"]["feature_of_interest_uri"]),
        )
    )

    conforms, _, report = shacl_validate(
        invalid_graph,
        shacl_graph=str(repo_root / "schema/dataset.shacl.ttl"),
        inference="none",
        advanced=True,
    )
    assert conforms is False
    assert (
        "A non-observation or non-applicability assessment must not use SOSA "
        "observation properties."
    ) in report


def test_shacl_accepts_controlled_scope_iri_and_ignores_code_scheme_governance(
    repo_root: Path,
):
    graph = Graph()
    scope = URIRef("https://example.org/scope/source-silent")
    agent = URIRef("https://example.org/agent/assertor")
    mode = URIRef(controlled_value_uri("scope-mode", "source-silent"))
    controlled_scheme = URIRef(f"{OMARO_NS}vocabulary-scope-mode")
    graph.add((scope, RDF.type, OMARO_NS.ApplicabilityScope))
    graph.add((scope, OMARO_NS.scopeMode, mode))
    graph.add((scope, PROV.wasAttributedTo, agent))
    graph.add((agent, RDF.type, PROV.Agent))
    graph.add((mode, RDF.type, SKOS.Concept))
    graph.add((mode, SKOS.inScheme, controlled_scheme))
    graph.add((controlled_scheme, RDF.type, SKOS.ConceptScheme))

    conforms, _, report = shacl_validate(
        graph,
        shacl_graph=str(repo_root / "schema/dataset.shacl.ttl"),
        inference="none",
        advanced=True,
    )

    assert conforms is True, report


def test_shacl_governs_domain_scheme_selected_by_scheme_type(repo_root: Path):
    graph = Graph()
    scheme = URIRef("https://example.org/scheme/domain")
    graph.add((scheme, RDF.type, SKOS.ConceptScheme))
    graph.add((scheme, OMARO_NS.schemeType, Literal("classification")))

    conforms, _, report = shacl_validate(
        graph,
        shacl_graph=str(repo_root / "schema/dataset.shacl.ttl"),
        inference="none",
        advanced=True,
    )

    assert conforms is False
    assert "schemePerspective" in report
    assert "wasAttributedTo" in report


@pytest.mark.parametrize(
    "status",
    ["detected", "not-detected", "indeterminate"],
)
def test_attempted_observations_have_actual_observation_types(
    observation_projection, status: str
):
    graph, _, records = observation_projection
    node = URIRef(records[status]["uri"])
    types = set(graph.objects(node, RDF.type))

    assert {
        OMARO_NS.ObservationAssessment,
        OMARO_NS.OrganologicalObservation,
        SOSA.Observation,
        CRMSCI.S27_Observation,
    }.issubset(types)


@pytest.mark.parametrize("status", ["not-observed", "not-applicable"])
def test_non_attempt_assessments_are_not_typed_as_observations(
    observation_projection, status: str
):
    graph, _, records = observation_projection
    node = URIRef(records[status]["uri"])

    assert set(graph.objects(node, RDF.type)) == {OMARO_NS.ObservationAssessment}
    assert not list(graph.objects(node, SOSA.hasResult))


def _dataset_with_organological_records(
    canonical_dataset: Dataset, criterion: dict, observation: dict
) -> Dataset:
    dataset = copy.copy(canonical_dataset)
    dataset.metadata = copy.deepcopy(canonical_dataset.metadata)
    dataset.metadata["counts"]["classification_criteria"] = 1
    dataset.metadata["counts"]["observation_assessments"] = 1
    dataset.classification_criteria = [criterion]
    dataset.observation_assessments = [observation]
    return dataset


def test_organological_criterion_and_range_observation_validate(
    repo_root: Path, canonical_dataset: Dataset
):
    criterion, observation = _organological_records(canonical_dataset)
    _assert_schema_valid(repo_root, "classification_criterion.schema.json", criterion)
    _assert_schema_valid(repo_root, "observation_assessment.schema.json", observation)

    dataset = _dataset_with_organological_records(
        canonical_dataset, criterion, observation
    )
    summary = dataset.validate(repo_root / "schema")
    assert summary["classification_criteria"] == 1
    assert summary["observation_assessments"] == 1


def test_not_detected_assessment_without_result_is_rejected(
    canonical_dataset: Dataset,
):
    criterion, observation = _organological_records(canonical_dataset)
    observation["assessment_status"] = "not-detected"
    observation["result"] = None
    dataset = _dataset_with_organological_records(
        canonical_dataset, criterion, observation
    )

    with pytest.raises(ValidationError) as exc_info:
        dataset.validate()

    assert "detected or not-detected assessment lacks a result" in str(exc_info.value)


@pytest.mark.parametrize("status", ["not-observed", "not-applicable"])
def test_nonattempt_assessment_with_result_is_rejected(
    canonical_dataset: Dataset, status: str
):
    criterion, observation = _organological_records(canonical_dataset)
    observation["assessment_status"] = status
    dataset = _dataset_with_organological_records(
        canonical_dataset, criterion, observation
    )

    with pytest.raises(ValidationError) as exc_info:
        dataset.validate()

    assert "nonattempt assessment must not have a result" in str(exc_info.value)


def test_inverted_observation_range_and_invalid_criterion_conclusion_are_rejected(
    canonical_dataset: Dataset,
):
    criterion, observation = _organological_records(canonical_dataset)
    invalid_conclusion = next(
        row["uri"]
        for row in canonical_dataset.concepts
        if row["kind"] == "instrument" and row["resolution_status"] == "resolved"
    )
    criterion["conclusion_classification_uris"] = [invalid_conclusion]
    observation["result"]["maximum_value"] = 11.9
    dataset = _dataset_with_organological_records(
        canonical_dataset, criterion, observation
    )

    with pytest.raises(ValidationError) as exc_info:
        dataset.validate()
    message = str(exc_info.value)
    assert "criterion conclusion is not a classification in its scheme" in message
    assert "assessment range is inverted" in message


def test_projection_contains_no_ontolex_terms(semantic_projection):
    graph, _, _ = semantic_projection
    assert not any(
        isinstance(term, URIRef) and str(term).startswith(ONTOLEX)
        for triple in graph
        for term in triple
    )


def _dataset_with_concept_relation(
    canonical_dataset: Dataset, relation: dict
) -> Dataset:
    dataset = copy.copy(canonical_dataset)
    dataset.metadata = copy.deepcopy(canonical_dataset.metadata)
    dataset.metadata["counts"]["concept_relation_assertions"] = 1
    dataset.concept_relation_assertions = [relation]
    return dataset


def test_mapping_purpose_codes_are_explicit_and_permission_neutral():
    assert CONTROLLED_CODES["mapping-purpose"] == (
        "query-expansion",
        "display-navigation",
        "data-transformation",
        "scholarly-comparison",
    )


def test_mapping_and_structural_relation_purpose_cardinalities_validate(
    repo_root: Path, canonical_dataset: Dataset
):
    mapping = _concept_relation_record(canonical_dataset)
    mapping_summary = _dataset_with_concept_relation(
        canonical_dataset, mapping
    ).validate(repo_root / "schema")
    assert mapping_summary["concept_relation_assertions"] == 1

    external_purpose_mapping = _concept_relation_record(
        canonical_dataset,
        mapping_purpose_uris=[
            "https://example.org/mapping-purpose/specialist-catalogue-audit"
        ],
    )
    external_summary = _dataset_with_concept_relation(
        canonical_dataset, external_purpose_mapping
    ).validate(repo_root / "schema")
    assert external_summary["concept_relation_assertions"] == 1

    structural = _concept_relation_record(
        canonical_dataset,
        predicate_uri="http://www.w3.org/2004/02/skos/core#related",
        mapping_purpose_uris=[],
    )
    structural["uri"] = "https://example.org/relation/structural"
    structural_summary = _dataset_with_concept_relation(
        canonical_dataset, structural
    ).validate(repo_root / "schema")
    assert structural_summary["concept_relation_assertions"] == 1


@pytest.mark.parametrize(
    ("predicate_uri", "mapping_purpose_uris"),
    [
        ("http://www.w3.org/2004/02/skos/core#closeMatch", []),
        (
            "http://www.w3.org/2004/02/skos/core#related",
            [controlled_value_uri("mapping-purpose", "display-navigation")],
        ),
    ],
)
def test_json_schema_rejects_mapping_purpose_predicate_mismatch(
    repo_root: Path,
    canonical_dataset: Dataset,
    predicate_uri: str,
    mapping_purpose_uris: list[str],
):
    schema = json.loads(
        (repo_root / "schema/concept_relation_assertion.schema.json").read_text()
    )
    record = _concept_relation_record(
        canonical_dataset,
        predicate_uri=predicate_uri,
        mapping_purpose_uris=mapping_purpose_uris,
    )
    errors = list(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record)
    )
    assert errors


@pytest.mark.parametrize(
    ("predicate_uri", "mapping_purpose_uris", "message"),
    [
        (
            "http://www.w3.org/2004/02/skos/core#closeMatch",
            [],
            "mapping relation assertion has no declared purpose",
        ),
        (
            "http://www.w3.org/2004/02/skos/core#related",
            [controlled_value_uri("mapping-purpose", "display-navigation")],
            "structural relation assertion declares a mapping purpose",
        ),
    ],
)
def test_invalid_mapping_purpose_combinations_are_rejected_by_model(
    canonical_dataset: Dataset,
    predicate_uri: str,
    mapping_purpose_uris: list[str],
    message: str,
):
    relation = _concept_relation_record(
        canonical_dataset,
        predicate_uri=predicate_uri,
        mapping_purpose_uris=mapping_purpose_uris,
    )
    with pytest.raises(ValidationError, match=message):
        _dataset_with_concept_relation(canonical_dataset, relation).validate()


def _minimal_relation_graph(predicate: URIRef, include_purpose: bool) -> Graph:
    graph = Graph()
    relation = URIRef("https://example.org/relation/shacl")
    subject = URIRef("https://example.org/concept/subject")
    obj = URIRef("https://example.org/concept/object")
    perspective = URIRef("https://example.org/perspective/organological")
    scope = URIRef("https://example.org/scope/research")
    policy = URIRef("https://example.org/policy/research")
    evidence = URIRef("https://example.org/evidence/relation")
    graph.add((relation, RDF.type, OMARO_NS.ConceptRelationAssertion))
    graph.add((relation, RDF.subject, subject))
    graph.add((relation, RDF.predicate, predicate))
    graph.add((relation, RDF.object, obj))
    graph.add((subject, RDF.type, SKOS.Concept))
    graph.add((obj, RDF.type, SKOS.Concept))
    graph.add((relation, OMARO_NS.perspective, perspective))
    graph.add((perspective, RDF.type, OMARO_NS.Perspective))
    graph.add((relation, OMARO_NS.hasApplicabilityScope, scope))
    graph.add((scope, RDF.type, OMARO_NS.ApplicabilityScope))
    graph.add((relation, OMARO_NS.underProjectionPolicy, policy))
    graph.add((policy, RDF.type, OMARO_NS.ProjectionPolicy))
    graph.add((relation, OMARO_NS.hasEvidence, evidence))
    graph.add((evidence, RDF.type, OMARO_NS.Evidence))
    if include_purpose:
        graph.add(
            (
                relation,
                OMARO_NS.mappingPurpose,
                URIRef(controlled_value_uri("mapping-purpose", "query-expansion")),
            )
        )
    return graph


@pytest.mark.parametrize(
    ("predicate", "include_purpose", "message"),
    [
        (
            SKOS.closeMatch,
            False,
            "A SKOS mapping assertion requires at least one mapping purpose.",
        ),
        (
            SKOS.related,
            True,
            "A structural SKOS relation must not declare a mapping purpose.",
        ),
    ],
)
def test_shacl_enforces_mapping_purpose_by_predicate_family(
    repo_root: Path, predicate: URIRef, include_purpose: bool, message: str
):
    conforms, _, report = shacl_validate(
        _minimal_relation_graph(predicate, include_purpose),
        shacl_graph=str(repo_root / "schema/dataset.shacl.ttl"),
        inference="none",
        advanced=True,
    )
    assert conforms is False
    assert message in report


def test_mapping_purpose_projects_but_mapping_triple_does_not(
    canonical_dataset: Dataset,
):
    relation = _concept_relation_record(canonical_dataset)
    dataset = copy.copy(canonical_dataset)
    dataset.labels = []
    dataset.label_resources = []
    dataset.label_profiles = []
    dataset.label_assertions = []
    dataset.note_assertions = []
    dataset.source_relations = []
    dataset.quality_findings = []
    dataset.quality_rules = []
    dataset.review_events = []
    dataset.protocol_applications = []
    dataset.use_decisions = []
    dataset.organological_targets = []
    dataset.classification_criteria = []
    dataset.observation_assessments = []
    dataset.classification_expressions = []
    dataset.classification_assertions = []
    dataset.concept_relation_assertions = [relation]
    graph = dataset_graph(dataset)
    node = URIRef(relation["uri"])
    purpose = URIRef(relation["mapping_purpose_uris"][0])

    assert (node, OMARO_NS.mappingPurpose, purpose) in graph
    assert (
        URIRef(relation["subject_concept_uri"]),
        URIRef(relation["predicate_uri"]),
        URIRef(relation["object_concept_uri"]),
    ) not in graph
    assert dataset.is_directly_endorsed(relation) is False


def test_sqlite_22_persists_separate_identity_tables(
    tmp_path: Path, canonical_dataset: Dataset
):
    database = tmp_path / "omaro.sqlite"
    relation = _concept_relation_record(canonical_dataset)
    dataset = copy.copy(canonical_dataset)
    dataset.concept_relation_assertions = [relation]
    _build_sqlite(dataset, database)
    connection = sqlite3.connect(database)
    try:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 20200
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table'"
            )
        }
        assert {
            "classification_assignments",
            "concept_relation_assertions",
            "review_decisions",
            "organological_targets",
            "classification_criteria",
            "observation_assessments",
            "classification_expressions",
            "protocol_applications",
            "use_decisions",
        }.issubset(tables)
        concept_relation_columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(concept_relation_assertions)"
            )
        }
        assert "mapping_purpose_uris_json" in concept_relation_columns
        assert (
            json.loads(
                connection.execute(
                    "SELECT mapping_purpose_uris_json FROM concept_relation_assertions"
                ).fetchone()[0]
            )
            == relation["mapping_purpose_uris"]
        )
        assert connection.execute(
            "SELECT count(*) FROM classification_assignments"
        ).fetchone()[0] == len(canonical_dataset.classification_assertions)
        assert connection.execute("SELECT count(*) FROM review_decisions").fetchone()[
            0
        ] == len(canonical_dataset.review_events)
        classification_target_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(classification_targets)")
        }
        assert {
            "classification_uri",
            "target_uri",
            "target_label_en",
            "target_resolution_status",
        }.issubset(classification_target_columns)
        assert (
            connection.execute(
                "SELECT count(*) FROM classification_assignments "
                "WHERE uri = assertion_uri"
            ).fetchone()[0]
            == 0
        )
        assert (
            connection.execute(
                "SELECT count(*) FROM review_decisions WHERE uri = event_uri"
            ).fetchone()[0]
            == 0
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()
