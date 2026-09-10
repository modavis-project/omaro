"""Boundary tests for the separate app's export, not ontology semantics."""

import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

APP = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "field_guide_build", APP / "scripts/build.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def inputs():
    data = json.loads((APP / "dist/data.json").read_text())
    dataset = SimpleNamespace(
        metadata={"schema_version": "0.1.0", "dataset_version": "0.1.0"},
        perspectives=data["perspectives"],
        review_events=[],
        authority_assignments=[],
        protocol_applications=[],
        use_decisions=[],
    )
    return dataset, {"results": [data["double_bass"]]}, data["comparison"]


def test_current_content_meets_the_curated_teaching_contract():
    MODULE.assert_teaching_contract(*inputs())


@pytest.mark.parametrize(
    "change", ["reviews", "scope", "endorsement", "notation", "method"]
)
def test_source_drift_requires_an_editorial_review(change):
    dataset, result, comparison = deepcopy(inputs())
    if change == "reviews":
        dataset.review_events = [{"uri": "https://example.org/review/new"}]
    elif change == "scope":
        result["results"][0]["classification_occurrences"][0]["endorsement"]["scopes"][
            0
        ]["scope_mode"] = "specified"
    elif change == "endorsement":
        result["results"][0]["classification_occurrences"][0]["endorsement"][
            "eligible"
        ] = True
    elif change == "notation":
        result["results"][0]["classification_occurrences"][0]["classification"][
            "notation"
        ] = "changed"
    else:
        comparison["method"]["minimum_comparable_dimensions"] = 1
    with pytest.raises(ValueError, match="changed"):
        MODULE.assert_teaching_contract(dataset, result, comparison)


def test_denied_query_leaves_no_new_output_or_partial_payload(monkeypatch, tmp_path):
    class FakeDataset:
        @staticmethod
        def load(_):
            return object()

    def denied(*args, **kwargs):
        raise ValueError("Publication denied")

    monkeypatch.setattr(MODULE, "Dataset", FakeDataset)
    monkeypatch.setattr(MODULE, "query_classifications", denied)
    monkeypatch.setattr(MODULE, "APP", tmp_path)
    with pytest.raises(ValueError, match="Publication denied"):
        MODULE.build()
    assert list(tmp_path.iterdir()) == []
