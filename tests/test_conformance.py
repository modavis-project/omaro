from __future__ import annotations

import json
import sqlite3
from copy import deepcopy

import pytest
from pyshacl import validate as shacl_validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

from omaro.builder import _build_sqlite, dataset_graph
from omaro.model import (
    CLASSIFIED_AS,
    CLAIMS_POLICY,
    ENDORSED_POLICY,
    MIMO_AGENT,
    MIMO_PERSPECTIVE,
    PROJECT_AGENT,
    Dataset,
    review_decision_uri,
)


def _review_fixture(repo_root):
    dataset = Dataset.load(repo_root / "data/canonical")
    assignment = dict(dataset.classification_assertions[0])
    assignment.update(
        {
            "uri": "https://example.org/assertion/conformance",
            "stance": "endorsed",
            "assertion_origin": "project-asserted",
            "assigned_by_uri": PROJECT_AGENT,
            "applicability_scope_uris": [
                "https://example.org/scope/context-independent"
            ],
            "projection_policy_uris": [CLAIMS_POLICY, ENDORSED_POLICY],
        }
    )
    dataset.classification_assertions = [assignment]
    dataset.source_relations = []
    dataset.labels = []
    dataset.label_assertions = []
    dataset.label_resources = []
    dataset.label_profiles = []
    dataset.note_assertions = []
    dataset.quality_findings = []
    dataset.applicability_scopes.append(
        {
            "uri": "https://example.org/scope/context-independent",
            "label": "Conformance context-independent scope",
            "scope_mode": "context-independent",
            "description": "No context restriction for the specified method and version.",
            "community_uris": [],
            "place_uris": [],
            "period_uris": [],
            "usage_domain_uris": [],
            "playing_technique_uris": [],
            "instrument_configuration_uris": [],
            "language_variety_uris": [],
            "temporal_start": None,
            "temporal_end": None,
            "asserted_by_uri": PROJECT_AGENT,
            "perspective_uri": MIMO_PERSPECTIVE,
            "source_record_uri": None,
        }
    )
    second_reviewer = "https://example.org/agent/conformance-reviewer"
    dataset.agents.append(
        {
            "uri": second_reviewer,
            "agent_type": "person",
            "name": "Conformance reviewer",
            "resource_uri": second_reviewer,
        }
    )

    def authority(uri, agent, dimensions):
        return {
            "uri": uri,
            "agent_uri": agent,
            "represented_community_uri": None,
            "authority_role": "organology-reviewer",
            "authority_basis_uri": "https://example.org/mandate/conformance",
            "conferred_by_agent_uri": PROJECT_AGENT,
            "subject_matter_uris": [assignment["uri"]],
            "covered_validation_dimensions": dimensions,
            "covered_action_uris": [],
            "applicability_scope_uris": [
                "https://example.org/scope/context-independent"
            ],
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": None,
            "delegation_permitted": False,
            "status": "active",
            "revocation_event_uri": None,
            "revocation_effect": None,
            "rights_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
            "evidence": [
                {
                    "citation": "Conformance competence mandate",
                    "evidence_type": "source-record",
                    "relation": "documents",
                    "resource_uri": "https://example.org/mandate/conformance",
                    "note": None,
                }
            ],
        }

    dataset.authority_assignments = [
        authority(
            "https://example.org/authority/conformance-1",
            MIMO_AGENT,
            ["referential", "scholarly"],
        ),
        authority(
            "https://example.org/authority/conformance-2",
            second_reviewer,
            ["scholarly"],
        ),
    ]

    def review(uri, reviewer, authority_uri, dimension, outcome="accepted"):
        return {
            "uri": uri,
            "decision_uri": review_decision_uri(uri),
            "target_assertion_uri": assignment["uri"],
            "reviewer_agent_uri": reviewer,
            "reviewer_authority": "organology",
            "authority_assignment_uris": [authority_uri],
            "review_method": "human",
            "validation_dimension": dimension,
            "outcome": outcome,
            "reviewed_at": "2026-07-18T00:00:00Z",
            "valid_until": None,
            "perspective_uri": MIMO_PERSPECTIVE,
            "represented_community_uris": [],
            "applicability_scope_uris": [
                "https://example.org/scope/context-independent"
            ],
            "evidence": [
                {
                    "citation": "Conformance review",
                    "evidence_type": "reasoning",
                    "relation": "supports",
                    "resource_uri": None,
                    "note": None,
                }
            ],
            "rationale": "Conformance decision.",
            "rights_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
            "supersedes_decision_uri": None,
            "suspends_decision_uri": None,
            "reinstates_decision_uri": None,
            "decision_status": "active",
            "projection_policy_uris": [ENDORSED_POLICY],
        }

    dataset.review_events = [
        review(
            "https://example.org/review/conformance-referential",
            MIMO_AGENT,
            dataset.authority_assignments[0]["uri"],
            "referential",
        ),
        review(
            "https://example.org/review/conformance-scholarly",
            second_reviewer,
            dataset.authority_assignments[1]["uri"],
            "scholarly",
        ),
    ]
    return dataset, assignment, review


def _surface_results(dataset, assignment, database_path):
    expected_triple = (
        URIRef(assignment["target_uri"]),
        URIRef(CLASSIFIED_AS),
        URIRef(assignment["classification_uri"]),
    )
    python_result = dataset.is_directly_endorsed(assignment)
    rdf_result = expected_triple in dataset_graph(dataset)
    _build_sqlite(dataset, database_path)
    with sqlite3.connect(database_path) as connection:
        sqlite_result = bool(
            connection.execute(
                "SELECT 1 FROM endorsed_classification_assertions WHERE assertion_uri = ?",
                (assignment["uri"],),
            ).fetchone()
        )
    return python_result, rdf_result, sqlite_result


def test_machine_readable_conformance_cases_are_executed(repo_root, tmp_path):
    fixture = json.loads(
        (repo_root / "conformance/multiperspectivity-cases.json").read_text(
            encoding="utf-8"
        )
    )
    expectations = {row["id"]: row for row in fixture["cases"]}

    dataset, assignment, make_review = _review_fixture(repo_root)
    assert _surface_results(dataset, assignment, tmp_path / "accepted.sqlite") == (
        True,
        True,
        True,
    )
    assert expectations["endorsed-two-independent-dimensions"][
        "expected_direct_assertion"
    ]

    no_opt_in = deepcopy(dataset)
    no_opt_in.classification_assertions[0]["projection_policy_uris"] = [CLAIMS_POLICY]
    assert _surface_results(
        no_opt_in,
        no_opt_in.classification_assertions[0],
        tmp_path / "no-opt-in.sqlite",
    ) == (False, False, False)

    missing_dimension = deepcopy(dataset)
    missing_dimension.review_events.pop()
    assert _surface_results(
        missing_dimension,
        missing_dimension.classification_assertions[0],
        tmp_path / "missing-dimension.sqlite",
    ) == (False, False, False)

    vetoed = deepcopy(dataset)
    vetoed.review_events.append(
        make_review(
            "https://example.org/review/conformance-dispute",
            MIMO_AGENT,
            vetoed.authority_assignments[0]["uri"],
            "scholarly",
            "disputed",
        )
    )
    assert _surface_results(
        vetoed,
        vetoed.classification_assertions[0],
        tmp_path / "vetoed.sqlite",
    ) == (False, False, False)

    assert not expectations["claim-does-not-opt-in"]["expected_direct_assertion"]
    assert not expectations["required-dimension-missing"]["expected_direct_assertion"]
    assert not expectations["active-veto-level-dispute"]["expected_direct_assertion"]


def _scoped_veto_fixture(repo_root, mode="specified"):
    dataset, assertion, make_review = _review_fixture(repo_root)
    scope = deepcopy(dataset.applicability_scopes[-1])
    scope.update({"uri": "https://example.org/scope/local-dispute", "scope_mode": mode})
    if mode == "specified":
        scope["playing_technique_uris"] = ["https://example.org/technique/arco"]
    dataset.applicability_scopes.append(scope)
    dataset.authority_assignments[0]["applicability_scope_uris"].append(scope["uri"])
    veto = make_review(
        "https://example.org/review/local-dispute",
        MIMO_AGENT,
        dataset.authority_assignments[0]["uri"],
        "scholarly",
        "disputed",
    )
    veto["applicability_scope_uris"] = [scope["uri"]]
    dataset.review_events.append(veto)
    return dataset, assertion, veto


def test_local_dispute_blocks_static_projection_in_every_format(repo_root, tmp_path):
    dataset, assertion, veto = _scoped_veto_fixture(repo_root)
    assert _surface_results(dataset, assertion, tmp_path / "local-veto.sqlite") == (
        False,
        False,
        False,
    )
    explanation = dataset.explain_endorsement(assertion)
    assert explanation["reason_codes"] == ["active-review-veto"]
    assert explanation["reviews"]["veto_decision_uris"] == [veto["decision_uri"]]
    assert all(row["satisfied"] for row in explanation["reviews"]["requirements"])
    cases = json.loads(
        (repo_root / "conformance/multiperspectivity-cases.json").read_text()
    )
    case = next(
        row
        for row in cases["cases"]
        if row["id"] == "local-dispute-blocks-unqualified-endorsement"
    )
    assert explanation["eligible"] is case["expected_direct_assertion"]


@pytest.mark.parametrize(
    "mode",
    [
        "source-silent",
        "not-yet-investigated",
        "known-unknown",
        "intentionally-unscoped",
    ],
)
def test_unknown_veto_scope_cannot_be_assumed_irrelevant(repo_root, mode):
    dataset, assertion, veto = _scoped_veto_fixture(repo_root, mode)
    assert not dataset.is_directly_endorsed(assertion)
    explanation = dataset.explain_endorsement(assertion, {})
    assert explanation["reviews"]["veto_decision_uris"] == [veto["decision_uri"]]
    assert not dataset.is_endorsed_for_context(assertion, {})


@pytest.mark.parametrize(
    "context, eligible",
    [
        ({}, False),
        ({"playing_technique_uris": "https://example.org/technique/arco"}, False),
        ({"playing_technique_uris": ["https://example.org/technique/pizzicato"]}, True),
        (
            {
                "playing_technique_uris": [
                    "https://example.org/technique/arco",
                    "https://example.org/technique/pizzicato",
                ]
            },
            False,
        ),
    ],
)
def test_contextual_veto_requires_proven_disjointness_to_ignore(
    repo_root, context, eligible
):
    dataset, assertion, _ = _scoped_veto_fixture(repo_root)
    assert dataset.is_endorsed_for_context(assertion, context) is eligible
    assert dataset.explain_endorsement(assertion, context)["eligible"] is eligible


def test_veto_overlap_checks_all_dimensions_and_time(repo_root):
    dataset, assertion, veto = _scoped_veto_fixture(repo_root)
    scope = dataset.applicability_scopes[-1]
    scope["temporal_start"] = "2026-01-01T00:00:00Z"
    scope["temporal_end"] = "2026-02-01T00:00:00Z"
    # Missing technique cannot establish support, but a known date outside
    # the interval proves disjointness even with the technique unspecified.
    assert dataset.is_endorsed_for_context(assertion, {"at": "2026-03-01T00:00:00Z"})
    assert not dataset.is_endorsed_for_context(
        assertion, {"at": "2026-02-01T01:00:00+01:00"}
    )
    # Policy membership and valid authority are still required for a veto.
    veto["projection_policy_uris"] = []
    assert dataset.is_directly_endorsed(assertion)
    veto["projection_policy_uris"] = [ENDORSED_POLICY]
    dataset.authority_assignments[0]["applicability_scope_uris"].remove(scope["uri"])
    assert dataset.is_directly_endorsed(assertion)


def test_review_lifecycle_orders_instants_instead_of_timestamp_text(repo_root):
    dataset, assertion, make_review = _review_fixture(repo_root)
    original = dataset.review_events[0]
    superseding = make_review(
        "https://example.org/review/superseding-offset",
        MIMO_AGENT,
        dataset.authority_assignments[0]["uri"],
        "referential",
    )
    superseding["reviewed_at"] = "2026-07-18T02:30:00+02:00"
    superseding["supersedes_decision_uri"] = original["decision_uri"]
    reinstating = make_review(
        "https://example.org/review/reinstating-offset",
        MIMO_AGENT,
        dataset.authority_assignments[0]["uri"],
        "referential",
    )
    reinstating["reviewed_at"] = "2026-07-18T01:00:00Z"
    reinstating["reinstates_decision_uri"] = original["decision_uri"]
    dataset.review_events.extend([superseding, reinstating])
    assert original["decision_uri"] not in {
        row["decision_uri"]
        for row in dataset.active_review_decisions(
            assertion["uri"], as_of="2026-07-18T00:45:00Z"
        )
    }
    assert original["decision_uri"] in {
        row["decision_uri"]
        for row in dataset.active_review_decisions(
            assertion["uri"], as_of="2026-07-18T01:15:00Z"
        )
    }


def test_all_represented_communities_need_matching_mandates(repo_root):
    dataset, assignment, make_review = _review_fixture(repo_root)
    communities = [
        "https://example.org/community/a",
        "https://example.org/community/b",
    ]
    for authority, community in zip(dataset.authority_assignments, communities):
        authority["agent_uri"] = MIMO_AGENT
        authority["represented_community_uri"] = community
        authority["authority_role"] = "community-reviewer"
        authority["covered_validation_dimensions"] = ["community"]
    review = make_review(
        "https://example.org/review/community",
        MIMO_AGENT,
        dataset.authority_assignments[0]["uri"],
        "community",
    )
    review["reviewer_authority"] = "community"
    review["review_method"] = "community"
    review["represented_community_uris"] = communities
    assert not dataset.review_has_valid_authority(review)
    review["authority_assignment_uris"] = [
        row["uri"] for row in dataset.authority_assignments
    ]
    assert dataset.review_has_valid_authority(review)


def test_shacl_rejects_reversed_classification_lifecycle(repo_root):
    mic = Namespace("https://w3id.org/modavis/omaro#")
    graph = Graph()
    assertion = URIRef("https://example.org/assertion/reversed-lifecycle")
    graph.add((assertion, RDF.type, mic.ClassificationAssertion))
    graph.add(
        (
            assertion,
            mic.validFrom,
            Literal("2027-01-01T00:00:00Z", datatype=XSD.dateTime),
        )
    )
    graph.add(
        (
            assertion,
            mic.validUntil,
            Literal("2026-01-01T00:00:00Z", datatype=XSD.dateTime),
        )
    )
    conforms, _, report = shacl_validate(
        graph,
        shacl_graph=str(repo_root / "schema/dataset.shacl.ttl"),
        advanced=True,
    )
    assert not conforms
    assert "Classification validity ends before it begins." in report
