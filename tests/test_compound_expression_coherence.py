from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from pyshacl import validate as shacl_validate
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import PROV, RDF, SKOS

from omaro.builder import OMARO_NS
from omaro.model import (
    CLAIMS_POLICY,
    MIMO_PERSPECTIVE,
    PROJECT_AGENT,
    SOURCE_SILENT_SCOPE,
    Dataset,
    ValidationError,
)


HS_SCHEME = "http://www.mimo-db.eu/HornbostelAndSachs#"
WHOLE_CLASS = "http://www.mimo-db.eu/HornbostelAndSachs/6415"
FIRST_MEMBER_CLASS = "http://www.mimo-db.eu/HornbostelAndSachs/318"
SECOND_MEMBER_CLASS = "http://www.mimo-db.eu/HornbostelAndSachs/328"
BASE = "https://example.org/compound-coherence"
RIGHTS = "https://creativecommons.org/publicdomain/zero/1.0/"


@pytest.fixture(scope="module")
def canonical_dataset(repo_root: Path) -> Dataset:
    return Dataset.load(repo_root / "data" / "canonical")


def _evidence(suffix: str) -> list[dict[str, str]]:
    return [
        {
            "citation": f"Synthetic compound-expression evidence {suffix}",
            "evidence_type": "reasoning",
            "relation": "supports",
            "resource_uri": f"{BASE}/evidence/{suffix}",
            "note": "A synthetic record used only to test expression coherence.",
        }
    ]


def _target(uri_suffix: str, target_kind: str) -> dict:
    return {
        "uri": f"{BASE}/target/{uri_suffix}",
        "label": uri_suffix.replace("-", " "),
        "target_kind": target_kind,
        "realizes_instrument_concept_uris": [],
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
        "rights_uri": RIGHTS,
        "protocol_application_uris": [],
        "authority_assignment_uris": [],
    }


def _assertion(
    suffix: str,
    target: dict,
    classification_uri: str,
    scheme_version_uri: str,
    source_record_uri: str,
    expression_uri: str | None = None,
) -> dict:
    assertion_uri = f"{BASE}/assertion/{suffix}"
    return {
        "uri": assertion_uri,
        "assignment_uri": f"{BASE}/assignment/{suffix}",
        "target_uri": target["uri"],
        "target_type": target["target_kind"],
        "predicate_uri": "https://w3id.org/modavis/omaro#classifiedAs",
        "classification_uri": classification_uri,
        "classification_scheme_uri": HS_SCHEME,
        "scheme_version_uri": scheme_version_uri,
        "assigned_by_uri": PROJECT_AGENT,
        "generated_by_uri": None,
        "perspective_uri": MIMO_PERSPECTIVE,
        "classification_method_uri": f"{BASE}/method/expert-decomposition",
        "criteria_uris": [],
        "assessment_uris": [],
        "inference_logic_uri": None,
        "classification_expression_uri": expression_uri,
        "stance": "proposed",
        "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
        "evidence": _evidence(suffix),
        "authority_assignment_uris": [],
        "valid_from": None,
        "valid_until": None,
        "projection_policy_uris": [CLAIMS_POLICY],
        "source_predicate_uri": None,
        "source_uri": f"{BASE}/source/{suffix}",
        "source_record_uri": source_record_uri,
        "assertion_origin": "scholarly-asserted",
    }


def _compound_dataset(
    canonical_dataset: Dataset,
) -> tuple[Dataset, dict, dict, list[dict], list[dict]]:
    dataset = copy.copy(canonical_dataset)
    dataset.metadata = copy.deepcopy(canonical_dataset.metadata)

    source_expression = next(
        row
        for row in canonical_dataset.classification_expressions
        if row["source_concept_uri"] == WHOLE_CLASS
    )
    whole = _target("whole", "physical-object")
    first = _target("first-component", "instrument-component")
    second = _target("second-component", "instrument-component")
    first_role = f"{BASE}/role/first"
    second_role = f"{BASE}/role/second"
    whole["has_component_uris"] = [first["uri"], second["uri"]]
    first.update({"component_of_uri": whole["uri"], "component_role_uri": first_role})
    second.update({"component_of_uri": whole["uri"], "component_role_uri": second_role})
    targets = [whole, first, second]

    expression_uri = f"{BASE}/expression/expert-bagpipe"
    first_assertion = _assertion(
        "first-component",
        first,
        FIRST_MEMBER_CLASS,
        source_expression["expression_scheme_version_uri"],
        source_expression["source_record_uri"],
    )
    second_assertion = _assertion(
        "second-component",
        second,
        SECOND_MEMBER_CLASS,
        source_expression["expression_scheme_version_uri"],
        source_expression["source_record_uri"],
    )
    whole_assertion = _assertion(
        "whole",
        whole,
        WHOLE_CLASS,
        source_expression["expression_scheme_version_uri"],
        source_expression["source_record_uri"],
        expression_uri,
    )
    assertions = [first_assertion, second_assertion, whole_assertion]

    expression = {
        "uri": expression_uri,
        "source_concept_uri": WHOLE_CLASS,
        "notation_literal": "422.112+422.22-62",
        "notation_grammar_uri": (
            "https://w3id.org/modavis/omaro#notation-grammar-mimo-hs-plus"
        ),
        "expression_scheme_version_uri": source_expression[
            "expression_scheme_version_uri"
        ],
        "combination_operator": "joint",
        "members": [
            {
                "sequence_index": 1,
                "member_notation": "422.112",
                "classification_uri": FIRST_MEMBER_CLASS,
                "member_assertion_uri": first_assertion["uri"],
                "member_target_uri": first["uri"],
                "component_role_uri": first_role,
                "local_suffix_notation": None,
            },
            {
                "sequence_index": 2,
                "member_notation": "422.22-62",
                "classification_uri": SECOND_MEMBER_CLASS,
                "member_assertion_uri": second_assertion["uri"],
                "member_target_uri": second["uri"],
                "component_role_uri": second_role,
                "local_suffix_notation": "-62",
            },
        ],
        "shared_suffix_notation": None,
        "parse_status": "expert-interpreted",
        "perspective_uri": MIMO_PERSPECTIVE,
        "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
        "source_record_uri": source_expression["source_record_uri"],
        "evidence": _evidence("expression"),
        "authority_assignment_uris": [],
        "protocol_application_uris": [],
        "rights_uri": RIGHTS,
    }

    # Put the expert interpretation before the canonical parse so the canonical
    # source-concept projection remains the authoritative source-layer link.
    dataset.classification_expressions = [
        expression,
        *canonical_dataset.classification_expressions,
    ]
    dataset.classification_assertions = [
        *canonical_dataset.classification_assertions,
        *assertions,
    ]
    dataset.organological_targets = targets
    dataset.metadata["counts"].update(
        {
            "classification_expressions": len(dataset.classification_expressions),
            "classification_assertions": len(dataset.classification_assertions),
            "organological_targets": len(targets),
        }
    )
    return dataset, expression, whole_assertion, assertions[:2], targets


def test_compound_expression_and_member_assertions_validate(
    repo_root: Path, canonical_dataset: Dataset
):
    dataset, expression, _, _, _ = _compound_dataset(canonical_dataset)

    summary = dataset.validate(repo_root / "schema")

    assert summary["classification_expressions"] == 27
    assert summary["classification_assertions"] == 1875
    assert expression["source_concept_uri"] not in {
        member["classification_uri"] for member in expression["members"]
    }


def test_compound_expression_cross_record_mismatches_are_rejected(
    canonical_dataset: Dataset,
):
    dataset, expression, whole_assertion, member_assertions, targets = (
        _compound_dataset(canonical_dataset)
    )
    invalid_perspective = f"{BASE}/perspective/invalid"
    invalid_scope = f"{BASE}/scope/invalid"
    instrument_scheme = "http://www.mimo-db.eu/InstrumentsKeywords#"

    whole_assertion.update(
        {
            "perspective_uri": invalid_perspective,
            "scheme_version_uri": None,
            "applicability_scope_uris": [invalid_scope],
            "classification_scheme_uri": instrument_scheme,
            "classification_uri": FIRST_MEMBER_CLASS,
        }
    )
    for assertion in member_assertions:
        assertion.update(
            {
                "perspective_uri": invalid_perspective,
                "scheme_version_uri": None,
                "applicability_scope_uris": [invalid_scope],
            }
        )

    expression["members"][0].update(
        {"classification_uri": None, "member_target_uri": None}
    )
    orphan = _target("orphan", "physical-object")
    targets.append(orphan)
    dataset.organological_targets = targets
    dataset.metadata["counts"]["organological_targets"] = len(targets)
    expression["members"][1].update(
        {
            "member_notation": "999",
            "classification_uri": FIRST_MEMBER_CLASS,
            "member_assertion_uri": member_assertions[1]["uri"],
            "member_target_uri": orphan["uri"],
            "component_role_uri": f"{BASE}/role/incorrect",
        }
    )

    with pytest.raises(ValidationError) as exc_info:
        dataset.validate()

    report = str(exc_info.value)
    expected_messages = (
        "classification assertion and expression use different perspectives",
        "classification assertion and expression use different scheme versions",
        "classification assertion scope is not covered by its expression",
        "classification assertion class differs from its expression source concept",
        "classification expression member belongs to another scheme",
        "expression member assertion requires a classification and target",
        "expression member classification disagrees with its assertion",
        "expression member target disagrees with its assertion",
        "expression and member assertion use different perspectives",
        "expression and member assertion use different scheme versions",
        "expression scope is not covered by its member assertion",
        "expression member role disagrees with its registered target",
        "classification expression member target is unrelated",
        "MIMO expression member notation does not match its classification",
    )
    for message in expected_messages:
        assert message in report


def test_member_assertion_requires_non_null_class_and_target_in_json_schema(
    repo_root: Path, canonical_dataset: Dataset
):
    _, expression, _, _, _ = _compound_dataset(canonical_dataset)
    schema = json.loads(
        (repo_root / "schema/classification_expression.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    assert not list(validator.iter_errors(expression))

    invalid = copy.deepcopy(expression)
    invalid["members"][0]["classification_uri"] = None
    invalid["members"][0]["member_target_uri"] = None
    errors = list(validator.iter_errors(invalid))
    assert {tuple(error.path) for error in errors} >= {
        ("members", 0, "classification_uri"),
        ("members", 0, "member_target_uri"),
    }


def test_shacl_reports_compound_expression_coherence_failures(repo_root: Path):
    graph = Graph()
    assertion = URIRef(f"{BASE}/rdf/assertion")
    assignment = URIRef(f"{BASE}/rdf/assignment")
    expression = URIRef(f"{BASE}/rdf/expression")
    member = URIRef(f"{BASE}/rdf/member")
    incomplete_member = URIRef(f"{BASE}/rdf/incomplete-member")
    member_assertion = URIRef(f"{BASE}/rdf/member-assertion")
    whole_target = URIRef(f"{BASE}/rdf/whole-target")
    member_target = URIRef(f"{BASE}/rdf/member-target")
    asserted_member_target = URIRef(f"{BASE}/rdf/asserted-member-target")
    member_class = URIRef(f"{BASE}/rdf/member-class")
    asserted_member_class = URIRef(f"{BASE}/rdf/asserted-member-class")
    source_concept = URIRef(f"{BASE}/rdf/source-concept")
    asserted_class = URIRef(f"{BASE}/rdf/asserted-class")
    assertion_scheme = URIRef(f"{BASE}/rdf/assertion-scheme")
    other_scheme = URIRef(f"{BASE}/rdf/other-scheme")
    assertion_scope = URIRef(f"{BASE}/rdf/assertion-scope")
    expression_scope = URIRef(f"{BASE}/rdf/expression-scope")
    member_scope = URIRef(f"{BASE}/rdf/member-scope")

    graph.add((assertion, RDF.type, OMARO_NS.ClassificationAssertion))
    graph.add((assertion, RDF.subject, whole_target))
    graph.add((assertion, RDF.object, asserted_class))
    graph.add((assertion, PROV.wasGeneratedBy, assignment))
    graph.add((assignment, OMARO_NS.classificationExpression, expression))
    graph.add((assertion, OMARO_NS.perspective, URIRef(f"{BASE}/rdf/perspective-a")))
    graph.add((assertion, OMARO_NS.schemeVersion, URIRef(f"{BASE}/rdf/version-a")))
    graph.add((assertion, OMARO_NS.hasApplicabilityScope, assertion_scope))
    graph.add((assertion, OMARO_NS.classificationScheme, assertion_scheme))

    graph.add((expression, RDF.type, OMARO_NS.ClassificationExpression))
    graph.add((expression, OMARO_NS.perspective, URIRef(f"{BASE}/rdf/perspective-e")))
    graph.add((expression, OMARO_NS.schemeVersion, URIRef(f"{BASE}/rdf/version-e")))
    graph.add((expression, OMARO_NS.hasApplicabilityScope, expression_scope))
    graph.add((expression, OMARO_NS.hasExpressionMember, member))
    graph.add((expression, OMARO_NS.hasExpressionMember, incomplete_member))
    graph.add(
        (
            expression,
            OMARO_NS.notationGrammar,
            OMARO_NS["notation-grammar-mimo-hs-plus"],
        )
    )
    graph.add((source_concept, RDF.type, SKOS.Concept))
    graph.add((source_concept, SKOS.inScheme, assertion_scheme))
    graph.add((source_concept, OMARO_NS.classificationExpression, expression))

    graph.add((member, RDF.type, OMARO_NS.ClassificationExpressionMember))
    graph.add((member, OMARO_NS.memberClassification, member_class))
    graph.add((member, OMARO_NS.memberTarget, member_target))
    graph.add((member, OMARO_NS.memberAssertion, member_assertion))
    graph.add((member, OMARO_NS.componentRole, URIRef(f"{BASE}/rdf/role-a")))
    graph.add((member, OMARO_NS.memberNotation, Literal("999")))
    graph.add((member_class, RDF.type, SKOS.Concept))
    graph.add((member_class, SKOS.inScheme, other_scheme))
    graph.add((member_class, SKOS.notation, Literal("422.22")))

    graph.add((incomplete_member, RDF.type, OMARO_NS.ClassificationExpressionMember))
    graph.add((incomplete_member, OMARO_NS.memberAssertion, member_assertion))
    graph.add((incomplete_member, OMARO_NS.memberNotation, Literal("422.112")))

    graph.add((member_assertion, RDF.type, OMARO_NS.ClassificationAssertion))
    graph.add((member_assertion, RDF.subject, asserted_member_target))
    graph.add((member_assertion, RDF.object, asserted_member_class))
    graph.add(
        (
            member_assertion,
            OMARO_NS.perspective,
            URIRef(f"{BASE}/rdf/perspective-member"),
        )
    )
    graph.add(
        (
            member_assertion,
            OMARO_NS.schemeVersion,
            URIRef(f"{BASE}/rdf/version-member"),
        )
    )
    graph.add((member_assertion, OMARO_NS.hasApplicabilityScope, member_scope))

    graph.add((whole_target, RDF.type, OMARO_NS.OrganologicalTarget))
    graph.add((member_target, RDF.type, OMARO_NS.OrganologicalTarget))
    graph.add(
        (whole_target, OMARO_NS.targetKind, OMARO_NS["target-type-physical-object"])
    )
    graph.add(
        (
            member_target,
            OMARO_NS.targetKind,
            OMARO_NS["target-type-instrument-component"],
        )
    )
    graph.add((member_target, OMARO_NS.componentRole, URIRef(f"{BASE}/rdf/role-b")))

    conforms, _, report = shacl_validate(
        graph,
        shacl_graph=str(repo_root / "schema/dataset.shacl.ttl"),
        inference="rdfs",
    )

    assert not conforms
    for message in (
        "must use the same perspective",
        "must use exactly the same scheme version",
        "scope must be covered by its compound expression",
        "member must belong to the assertion's classification scheme",
        "must classify as that concept",
        "must be connected to the registered whole-assertion target",
        "must also state its classification and target",
        "must equal those of its cited assertion",
        "must use the same perspective",
        "must use exactly the same scheme version",
        "scope must be covered by each cited member assertion",
        "role must equal the role on its registered target",
        "member token must equal its class notation",
    ):
        assert message in report
