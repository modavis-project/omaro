from copy import copy, deepcopy
import json
import sqlite3

import pytest

from omaro.cli import main
from omaro.builder import dataset_graph
from omaro.model import Dataset, ValidationError
from omaro.query import query_classifications

DOUBLE_BASS = "http://www.mimo-db.eu/InstrumentsKeywords/3111"


@pytest.fixture(scope="module")
def dataset(repo_root):
    return Dataset.load(repo_root / "data/canonical")


def test_query_preserves_source_claims_and_explains_non_endorsement(
    dataset, monkeypatch
):
    def no_network(*args, **kwargs):
        pytest.fail("offline query attempted network access")

    monkeypatch.setattr("requests.sessions.Session.request", no_network)
    report = query_classifications(dataset, target_uri=DOUBLE_BASS)
    assert report["evaluation_mode"] == "direct"
    assert report["matched_target_count"] == report["returned_target_count"] == 1
    rows = report["results"][0]["classification_occurrences"]
    assert len(rows) == 3
    assert {row["classification"]["notation"] for row in rows} == {
        "321.322",
        "321.322-5",
        "321.322-71",
    }
    for row in rows:
        claim = row["claim"]
        assert claim in dataset.classification_assertions
        assert claim["uri"] != claim["assignment_uri"]
        assert (
            claim["source_predicate_uri"]
            == "http://www.w3.org/2004/02/skos/core#exactMatch"
        )
        assert row["research_included"]
        assert not row["endorsement"]["eligible"]
        assert row["endorsement"]["scopes"][0]["match"] is None
        assert "required-review-missing" in row["endorsement"]["reason_codes"]
        assert row["endorsement"]["reviews"]["active_authorized_decision_uris"] == []


def test_search_limits_targets_without_truncating_occurrences(dataset):
    report = query_classifications(dataset, search="dOuBlE BaSs", limit=1)
    assert report["matched_target_count"] > report["returned_target_count"] == 1
    assert report["truncated"]
    result = report["results"][0]
    expected = [
        row
        for row in dataset.classification_assertions
        if row["target_uri"] == result["target"]["uri"]
    ]
    assert [row["claim"] for row in result["classification_occurrences"]] == sorted(
        expected, key=lambda row: row["uri"]
    )


@pytest.mark.parametrize(
    "context",
    [
        {"playing_technique_uri": "https://example.org/arco"},
        {"at": "2026-07-01"},
        {"as_of": "2026-07-01T12:00:00"},
        {"community_uris": ["relative/path"]},
        {"community_uris": ["https://example.org/a", "https://example.org/a"]},
        {"place_uris": None},
    ],
)
def test_invalid_context_is_rejected_without_silent_fallback(dataset, context):
    with pytest.raises(ValidationError, match="invalid query context"):
        query_classifications(dataset, target_uri=DOUBLE_BASS, context=context)


def test_cli_context_and_unknown_target_are_explicit(repo_root, tmp_path, capsys):
    path = tmp_path / "context.json"
    path.write_text('{"at":"2026-07-01T12:00:00+02:00"}')
    assert (
        main(
            [
                "--repo-root",
                str(repo_root),
                "query",
                "--target-uri",
                "https://example.org/unknown",
                "--context",
                str(path),
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["evaluation_mode"] == "contextual"
    assert report["results"] == []
    assert report["matched_target_count"] == 0


def test_query_refuses_before_search_or_diagnostics(dataset, monkeypatch, capsys):
    governed = deepcopy(dataset)
    governed.classification_assertions[0]["assertion_origin"] = "community-asserted"
    governed.classification_assertions[0]["uri"] = (
        "https://example.org/restricted-identifier"
    )
    governed.labels[0]["label"] = "restricted payload"
    monkeypatch.setattr(Dataset, "load", lambda *args: governed)
    with pytest.raises(SystemExit) as exc:
        main(["query", "--search", "Double bass"])
    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert captured.out == ""
    assert "public build refused" in captured.err
    assert "restricted-identifier" not in captured.err
    assert "restricted payload" not in captured.err


@pytest.mark.parametrize("content", ["null", "[]", "{", '{"at":"yesterday"}'])
def test_cli_reports_context_errors_without_traceback(tmp_path, capsys, content):
    path = tmp_path / "context.json"
    path.write_text(content)
    with pytest.raises(SystemExit) as exc:
        main(["query", "--search", "Double bass", "--context", str(path)])
    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert captured.out == ""
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def test_generated_sql_and_sparql_recipes_agree(dataset, repo_root):
    query_root = repo_root / "examples/queries"
    with sqlite3.connect(
        f"file:{repo_root / 'dist/sqlite/omaro.sqlite'}?mode=ro", uri=True
    ) as connection:
        rows = connection.execute(
            (query_root / "double-bass.sql").read_text()
        ).fetchall()
    assert len(rows) == 3
    assert {row[2] for row in rows} == {"321.322", "321.322-5", "321.322-71"}
    assert all(row[-1] == 0 for row in rows)
    # Project the real occurrences and their source witnesses, without
    # repeatedly materializing unrelated labels and profiles in a query test.
    subset = copy(dataset)
    subset.classification_assertions = [
        row
        for row in dataset.classification_assertions
        if row["target_uri"] == DOUBLE_BASS
    ]
    selected = {DOUBLE_BASS} | {
        row["classification_uri"] for row in subset.classification_assertions
    }
    subset.concepts = [row for row in dataset.concepts if row["uri"] in selected]
    for name in (
        "labels",
        "label_assertions",
        "label_resources",
        "label_profiles",
        "note_assertions",
        "quality_findings",
        "source_relations",
        "classification_expressions",
    ):
        setattr(subset, name, [])
    results = list(
        dataset_graph(subset).query((query_root / "double-bass.rq").read_text())
    )
    assert [
        (str(row.assertion), str(row.assignment), str(row.notation)) for row in results
    ] == [row[:3] for row in rows]


def test_query_context_fixture_is_accepted(dataset, repo_root):
    context = json.loads((repo_root / "examples/queries/arco-context.json").read_text())
    context["at"] = context["at"].lower()
    report = query_classifications(dataset, target_uri=DOUBLE_BASS, context=context)
    assert report["evaluation_mode"] == "contextual"
    assert report["context"]["at"] == "2026-07-01T12:00:00Z"
    assert all(
        not row["endorsement"]["eligible"]
        for row in report["results"][0]["classification_occurrences"]
    )
