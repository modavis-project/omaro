from __future__ import annotations

import copy
import importlib.util
import json
import shutil
from collections import Counter
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from rdflib import URIRef

from omaro.builder import OMARO_NS, dataset_graph
from omaro.model import Dataset


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts/build_expert_review_packet.py"
)
SCRIPT_SPEC = importlib.util.spec_from_file_location(
    "build_expert_review_packet", SCRIPT_PATH
)
assert SCRIPT_SPEC is not None and SCRIPT_SPEC.loader is not None
SCRIPT_MODULE = importlib.util.module_from_spec(SCRIPT_SPEC)
SCRIPT_SPEC.loader.exec_module(SCRIPT_MODULE)
write_packet_metadata = SCRIPT_MODULE.write_packet_metadata


EXPECTED_RECORD_COUNTS = {
    "authority_assignments.jsonl": 1,
    "classification_assertions.jsonl": 9,
    "classification_criteria.jsonl": 6,
    "classification_expressions.jsonl": 2,
    "concept_relation_assertions.jsonl": 2,
    "observation_assessments.jsonl": 34,
    "organological_targets.jsonl": 17,
    "protocol_applications.jsonl": 1,
    "use_decisions.jsonl": 1,
}
EXPECTED_RECORD_TYPE_COUNTS = {
    "authority_assignment": 1,
    "classification_assertion": 9,
    "classification_criterion": 6,
    "classification_expression": 2,
    "concept_relation_assertion": 2,
    "observation_assessment": 34,
    "organological_target": 17,
    "protocol_application": 1,
    "use_decision": 1,
}


def _copy_example_bundle(repo_root, staging):
    target = staging / "examples/organological-assessment"
    target.parent.mkdir(parents=True)
    shutil.copytree(repo_root / "examples/organological-assessment", target)
    return target


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def _example_rows(repo_root: Path, filename: str) -> list[dict]:
    return _jsonl(repo_root / "examples/organological-assessment" / filename)


def test_packet_metadata_counts_every_illustrative_record(repo_root, tmp_path):
    _copy_example_bundle(repo_root, tmp_path)

    write_packet_metadata(tmp_path)
    metadata = json.loads((tmp_path / "PACKET_METADATA.json").read_text())

    assert {
        "illustrative_assessment_records",
        "illustrative_assessment_is_canonical",
        "illustrative_assessment_is_empirical",
        "illustrative_assessment_establishes_community_authorization",
    }.isdisjoint(metadata)
    assert metadata["illustrative_jsonl_records"] == sum(
        EXPECTED_RECORD_COUNTS.values()
    )
    assert metadata["illustrative_jsonl_records_by_file"] == EXPECTED_RECORD_COUNTS
    assert metadata["illustrative_jsonl_records_by_type"] == EXPECTED_RECORD_TYPE_COUNTS
    assert metadata["illustrative_bundle_is_canonical"] is False
    assert metadata["illustrative_bundle_is_empirical"] is False
    assert metadata["illustrative_bundle_establishes_community_authorization"] is False
    assert metadata["multidimensional_comparison_fixture"] == (
        "examples/multidimensional-analysis/scalogram.json"
    )
    assert metadata["multidimensional_fixture_is_normative_core_schema"] is False


def test_multidimensional_fixture_recalculates_declared_results(repo_root):
    fixture = json.loads(
        (repo_root / "examples/multidimensional-analysis/scalogram.json").read_text()
    )
    target_uris = {row["uri"] for row in fixture["targets"]}
    dimension_uris = {row["uri"] for row in fixture["dimensions"]}
    profile_dimensions = {
        row["uri"]: row["dimension_uris"] for row in fixture["profiles"]
    }
    assessments = {row["target_uri"]: row["values"] for row in fixture["assessments"]}
    status_to_value = fixture["method"]["status_to_value"]

    assert set(assessments) == target_uris
    assert status_to_value == {
        "detected": 1,
        "not-detected": 0,
        "indeterminate": None,
        "not-observed": None,
        "not-applicable": None,
    }
    for profile_uri, selected_dimensions in profile_dimensions.items():
        assert selected_dimensions
        assert set(selected_dimensions).issubset(dimension_uris), profile_uri
    for values in assessments.values():
        assert set(values) == dimension_uris
        assert set(values.values()).issubset(status_to_value)

    recalculated = []
    for comparison in fixture["comparisons"]:
        selected = profile_dimensions[comparison["profile_uri"]]
        left = assessments[comparison["left_target_uri"]]
        right = assessments[comparison["right_target_uri"]]
        comparable = []
        excluded = []
        for dimension_uri in selected:
            left_value = status_to_value[left[dimension_uri]]
            right_value = status_to_value[right[dimension_uri]]
            if left_value is None or right_value is None:
                excluded.append(dimension_uri)
            else:
                comparable.append((left_value, right_value))
        assert len(comparable) >= fixture["method"]["minimum_comparable_dimensions"]
        disagreements = sum(
            left_value != right_value for left_value, right_value in comparable
        )
        distance = disagreements / len(comparable)
        assert comparison["comparable_dimensions"] == len(comparable)
        assert comparison["excluded_dimension_uris"] == excluded
        assert comparison["disagreements"] == disagreements
        assert comparison["normalized_distance"] == distance
        recalculated.append(comparison)

    focus = fixture["focus_target_uri"]
    nearest = {
        row["profile_uri"]: (row["target_uri"], row["normalized_distance"])
        for row in fixture["nearest_by_profile"]
    }
    for profile_uri in profile_dimensions:
        candidates = [
            row
            for row in recalculated
            if row["profile_uri"] == profile_uri and row["left_target_uri"] == focus
        ]
        minimum = min(row["normalized_distance"] for row in candidates)
        winners = {
            row["right_target_uri"]
            for row in candidates
            if row["normalized_distance"] == minimum
        }
        assert winners == {nearest[profile_uri][0]}
        assert nearest[profile_uri][1] == minimum

    unresolved = copy.deepcopy(fixture)
    unresolved["assessments"][0]["values"][
        profile_dimensions[
            "https://example.org/omaro-scalogram/profile/morphological-description"
        ][0]
    ] = "not-observed"
    assert (
        status_to_value[
            unresolved["assessments"][0]["values"][
                "https://example.org/omaro-scalogram/criterion/membrane-present"
            ]
        ]
        is None
    )


def test_packet_metadata_rejects_unmanifested_jsonl(repo_root, tmp_path):
    bundle = _copy_example_bundle(repo_root, tmp_path)
    (bundle / "undeclared.jsonl").write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        ValueError, match="illustrative JSONL inventory differs from its manifest"
    ):
        write_packet_metadata(tmp_path)


def test_every_illustrative_jsonl_row_conforms_to_its_manifest_schema(repo_root):
    bundle = repo_root / "examples/organological-assessment"
    manifest = json.loads((bundle / "manifest.json").read_text())

    for entry in manifest["files"]:
        schema = json.loads((bundle / entry["schema"]).resolve().read_text())
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for line_number, row in enumerate(_jsonl(bundle / entry["path"]), start=1):
            errors = list(validator.iter_errors(row))
            assert not errors, (
                entry["path"],
                line_number,
                [error.message for error in errors],
            )


def test_illustrative_assessment_statuses_and_premises_are_coherent(repo_root):
    assessments = {
        row["uri"]: row
        for row in _example_rows(repo_root, "observation_assessments.jsonl")
    }
    criteria = {
        row["uri"]: row
        for row in _example_rows(repo_root, "classification_criteria.jsonl")
    }
    assertions = {
        row["uri"]: row
        for row in _example_rows(repo_root, "classification_assertions.jsonl")
    }

    assert Counter(row["assessment_status"] for row in assessments.values()) == {
        "detected": 30,
        "not-detected": 1,
        "indeterminate": 1,
        "not-observed": 1,
        "not-applicable": 1,
    }
    for assertion in assertions.values():
        assert set(assertion["assessment_uris"]).issubset(assessments)
        linked_criteria = [criteria[uri] for uri in assertion["criteria_uris"]]
        assert assertion["classification_uri"] in {
            uri
            for criterion in linked_criteria
            for uri in criterion["conclusion_classification_uris"]
        }
        assert assertion["inference_logic_uri"] in {
            criterion["inference_logic_uri"] for criterion in linked_criteria
        }
        allowed_properties = {
            uri
            for criterion in linked_criteria
            for uri in criterion["observable_property_uris"]
        }
        allowed_procedures = {
            uri for criterion in linked_criteria for uri in criterion["procedure_uris"]
        }
        for assessment_uri in assertion["assessment_uris"]:
            assessment = assessments[assessment_uri]
            assert assessment["assessed_property_uri"] in allowed_properties
            assert assessment["assessment_procedure_uri"] in allowed_procedures

    expected_properties = {
        "https://example.org/omaro-evaluation/assertion/bagpipe-compound": {
            "https://example.org/omaro-evaluation/property/reed-type",
            "https://example.org/omaro-evaluation/property/bore-profile",
            "https://example.org/omaro-evaluation/property/fingerhole-presence",
            "https://example.org/omaro-evaluation/property/reservoir-material-and-connection",
            "https://example.org/omaro-evaluation/property/drone-tuning-method",
        },
        "https://example.org/omaro-evaluation/assertion/tambourine-struck": {
            "https://example.org/omaro-evaluation/property/body-depth-to-membrane-radius-relation",
            "https://example.org/omaro-evaluation/property/handle-configuration",
            "https://example.org/omaro-evaluation/property/membrane-count",
            "https://example.org/omaro-evaluation/property/membrane-tension",
            "https://example.org/omaro-evaluation/property/excitation-mechanism",
            "https://example.org/omaro-evaluation/property/sounding-component",
        },
        "https://example.org/omaro-evaluation/assertion/tambourine-shaken": {
            "https://example.org/omaro-evaluation/property/rattling-object-attachment",
            "https://example.org/omaro-evaluation/property/intended-sound-organization",
            "https://example.org/omaro-evaluation/property/excitation-mechanism",
            "https://example.org/omaro-evaluation/property/sounding-component",
        },
        "https://example.org/omaro-evaluation/assertion/tambourine-combined-membrane": {
            "https://example.org/omaro-evaluation/property/body-depth-to-membrane-radius-relation",
            "https://example.org/omaro-evaluation/property/handle-configuration",
            "https://example.org/omaro-evaluation/property/membrane-count",
            "https://example.org/omaro-evaluation/property/membrane-tension",
            "https://example.org/omaro-evaluation/property/excitation-mechanism",
            "https://example.org/omaro-evaluation/property/sounding-component",
        },
        "https://example.org/omaro-evaluation/assertion/tambourine-combined-jingles": {
            "https://example.org/omaro-evaluation/property/rattling-object-attachment",
            "https://example.org/omaro-evaluation/property/intended-sound-organization",
            "https://example.org/omaro-evaluation/property/excitation-mechanism",
            "https://example.org/omaro-evaluation/property/sounding-component",
        },
        "https://example.org/omaro-evaluation/assertion/community-drum-hs": {
            "https://example.org/omaro-evaluation/property/membrane-presence",
            "https://example.org/omaro-evaluation/property/body-profile",
            "https://example.org/omaro-evaluation/property/body-depth-to-membrane-radius-relation",
            "https://example.org/omaro-evaluation/property/handle-configuration",
            "https://example.org/omaro-evaluation/property/membrane-count",
            "https://example.org/omaro-evaluation/property/membrane-tension",
            "https://example.org/omaro-evaluation/property/excitation-mechanism",
        },
    }
    for assertion_uri, properties in expected_properties.items():
        assert {
            assessments[uri]["assessed_property_uri"]
            for uri in assertions[assertion_uri]["assessment_uris"]
        } == properties

    expected_resource_results = {
        "observation/bagpipe-drone-air-column-tuning": (
            "value/tuning-by-varying-air-column-length"
        ),
        "observation/tambourine-struck-technique": "technique/direct-strike",
        "observation/tambourine-struck-sounding-component": ("value/membrane-sounding"),
        "observation/tambourine-shaken-technique": "technique/indirect-shaking",
        "observation/tambourine-shaken-sounding-component": ("value/jingles-sounding"),
        "observation/tambourine-combined-technique": (
            "technique/simultaneous-direct-strike-and-indirect-shaking"
        ),
        "observation/tambourine-combined-sounding-components": (
            "value/membrane-and-jingles-sounding"
        ),
        "observation/tambourine-body-depth-to-membrane-radius": (
            "value/body-depth-not-greater-than-membrane-radius"
        ),
        "observation/tambourine-handle-configuration": ("value/without-rigid-handle"),
        "observation/tambourine-membrane-tension": "value/tightly-stretched",
        "observation/tambourine-rattle-attachment": (
            "value/rattling-objects-attached-to-carrier"
        ),
        "observation/tambourine-rattle-sound-intent": ("value/sound-clusters-or-noise"),
        "observation/community-drum-body-depth-to-membrane-radius": (
            "value/body-depth-not-greater-than-membrane-radius"
        ),
        "observation/community-drum-membrane": "value/present",
        "observation/community-drum-body-profile": "value/cylindrical-body",
        "observation/community-drum-excitation": "technique/direct-strike",
        "observation/community-drum-handle-configuration": (
            "value/without-rigid-handle"
        ),
        "observation/community-drum-membrane-tension": "value/tightly-stretched",
    }
    example_base = "https://example.org/omaro-evaluation/"
    for (
        relative_assessment_uri,
        relative_result_uri,
    ) in expected_resource_results.items():
        assessment = assessments[example_base + relative_assessment_uri]
        assert assessment["result"] == {
            "kind": "resource",
            "value_uri": example_base + relative_result_uri,
        }

    for relative_assessment_uri in (
        "observation/tambourine-membrane-count",
        "observation/community-drum-membrane-count",
    ):
        result = assessments[example_base + relative_assessment_uri]["result"]
        assert result["kind"] == "quantity"
        assert result["numeric_value"] == 1
        assert result["unit_uri"] == "http://qudt.org/vocab/unit/NUM"

    targets = {
        row["uri"]: row
        for row in _example_rows(repo_root, "organological_targets.jsonl")
    }
    assert targets[example_base + "target/tambourine-shaken-sounding"][
        "actual_playing_technique_uris"
    ] == [example_base + "technique/indirect-shaking"]
    assert set(
        targets[example_base + "target/tambourine-combined-sounding"][
            "actual_playing_technique_uris"
        ]
    ) == {
        example_base + "technique/direct-strike",
        example_base + "technique/indirect-shaking",
    }

    governed_assessments = {
        "https://example.org/omaro-evaluation/observation/community-drum-membrane",
        "https://example.org/omaro-evaluation/observation/community-drum-body-profile",
        "https://example.org/omaro-evaluation/observation/community-drum-excitation",
        "https://example.org/omaro-evaluation/observation/community-drum-body-depth-to-membrane-radius",
        "https://example.org/omaro-evaluation/observation/community-drum-handle-configuration",
        "https://example.org/omaro-evaluation/observation/community-drum-membrane-count",
        "https://example.org/omaro-evaluation/observation/community-drum-membrane-tension",
    }
    authority = _example_rows(repo_root, "authority_assignments.jsonl")[0]
    protocol = _example_rows(repo_root, "protocol_applications.jsonl")[0]
    use_decision = _example_rows(repo_root, "use_decisions.jsonl")[0]
    assert governed_assessments.issubset(authority["subject_matter_uris"])
    assert governed_assessments.issubset(protocol["target_resource_uris"])
    assert governed_assessments.issubset(use_decision["target_resource_uris"])
    for assessment_uri in governed_assessments:
        assessment = assessments[assessment_uri]
        assert assessment["authority_assignment_uris"] == [authority["uri"]]
        assert assessment["protocol_application_uris"] == [protocol["uri"]]


def test_example_assignment_distinguishes_non_observation_assessment(repo_root):
    example_assertions = _example_rows(repo_root, "classification_assertions.jsonl")
    example_assertion = next(
        row
        for row in example_assertions
        if row["uri"].endswith("/bassoon-original-eight-key")
    )
    assessments_by_uri = {
        row["uri"]: row
        for row in _example_rows(repo_root, "observation_assessments.jsonl")
    }
    criteria = _example_rows(repo_root, "classification_criteria.jsonl")

    dataset = copy.copy(Dataset.load(repo_root / "data/canonical"))
    for field in (
        "agents",
        "source_records",
        "concept_schemes",
        "perspectives",
        "authority_assignments",
        "review_statuses",
        "language_registries",
        "script_registries",
        "quality_rules",
        "quality_findings",
        "review_events",
        "protocol_applications",
        "use_decisions",
        "organological_targets",
        "classification_expressions",
        "concepts",
        "labels",
        "label_resources",
        "label_profiles",
        "label_assertions",
        "note_assertions",
        "source_relations",
        "concept_relation_assertions",
    ):
        setattr(dataset, field, [])
    dataset.classification_criteria = criteria
    dataset.observation_assessments = list(assessments_by_uri.values())
    dataset.classification_assertions = example_assertions

    # The example bundle explicitly is not foreign-key complete. Supply
    # unresolved scope registrations only in this isolated projection fixture;
    # they cannot establish a positive match or an endorsement. The shared
    # evaluator now inspects scope definitions even for ineligible claims.
    scope_template = dataset.applicability_scopes[0]
    for uri in sorted(
        {uri for row in example_assertions for uri in row["applicability_scope_uris"]}
    ):
        scope = copy.deepcopy(scope_template)
        scope.update(
            {
                "uri": uri,
                "label": "Unresolved scope in the isolated projection fixture",
                "scope_mode": "not-yet-investigated",
                "description": "The fragment does not supply this scope definition.",
                "source_record_uri": None,
            }
        )
        dataset.applicability_scopes.append(scope)

    graph = dataset_graph(dataset)
    assert not list(graph.triples((None, OMARO_NS.classifiedAs, None)))
    for assertion in example_assertions:
        assignment_uri = URIRef(assertion["assignment_uri"])
        for assessment_uri in assertion["assessment_uris"]:
            assessment_ref = URIRef(assessment_uri)
            assert (assignment_uri, OMARO_NS.usedAssessment, assessment_ref) in graph
            is_observation = assessments_by_uri[assessment_uri][
                "assessment_status"
            ] in {"detected", "not-detected", "indeterminate"}
            assert (
                (
                    assignment_uri,
                    OMARO_NS.usedObservation,
                    assessment_ref,
                )
                in graph
            ) is is_observation

    assignment = URIRef(example_assertion["assignment_uri"])
    actual = URIRef(
        "https://example.org/omaro-evaluation/observation/bassoon-original-key-count"
    )
    non_observation = URIRef(
        "https://example.org/omaro-evaluation/assessment/"
        "bassoon-original-direct-inspection-not-applicable"
    )

    assert (assignment, OMARO_NS.usedAssessment, actual) in graph
    assert (assignment, OMARO_NS.usedObservation, actual) in graph
    assert (assignment, OMARO_NS.usedAssessment, non_observation) in graph
    assert (assignment, OMARO_NS.usedObservation, non_observation) not in graph
