from __future__ import annotations

from collections import Counter

import pytest

from omaro.model import (
    CLASSIFIED_AS,
    CLAIMS_POLICY,
    Dataset,
    ENDORSED_POLICY,
    EXACT_MATCH,
    MIMO_AGENT,
    MIMO_PERSPECTIVE,
    PROJECT_AGENT,
    SOURCE_POLICY,
    SOURCE_SILENT_SCOPE,
    ValidationError,
    assertion_uri,
    label_resource_uri,
    review_decision_uri,
)
from omaro.language_registry import LanguageSubtagRegistry


def test_full_canonical_dataset_validates(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    summary = dataset.validate(repo_root / "schema")
    assert summary["classifications"] == 643
    assert summary["instruments"] == 2724
    assert summary["unresolved_stubs"] == 5
    assert summary["concepts"] == 3372
    assert summary["labels"] == 42662
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
    assert summary["review_statuses"] == 5
    assert summary["language_registries"] == 1
    assert summary["script_registries"] == 1
    assert summary["quality_rules"] == 8
    assert summary["quality_findings"] == 9445
    assert summary["review_events"] == 0
    assert summary["source_relations"] == 5228
    assert summary["concept_relation_assertions"] == 0
    assert summary["classification_assertions"] == 1872


def test_languages_and_preferred_labels_are_clean(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    registry = LanguageSubtagRegistry.load(
        repo_root / "data/registries/iana-language-subtag-registry.json"
    )
    assert all(
        registry.assess(label["language"]).canonical == label["language"]
        for label in dataset.labels
    )
    assert all(
        label["language"] != "null" and label["label"] for label in dataset.labels
    )
    preferred = [
        (label["concept_uri"], label["language"])
        for label in dataset.labels
        if label["label_type"] == "preferred"
    ]
    assert max(Counter(preferred).values()) == 1


def test_known_data_characteristics_are_preserved(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    english = Counter(
        label["label"]
        for label in dataset.labels
        if label["language"] == "en" and label["label_type"] == "preferred"
    )
    assert english["Bugle"] >= 1
    assert sum(count - 1 for count in english.values() if count > 1) >= 48
    unresolved = [
        row for row in dataset.concepts if row["resolution_status"] == "unresolved"
    ]
    assert {row["mimo_id"] for row in unresolved} == {
        "2412",
        "3135",
        "3405",
        "5990",
        "6059",
    }


@pytest.mark.parametrize(
    "language,expected", [("es", 2720), ("ca", 2714), ("de", 2724)]
)
def test_instrument_language_coverage(repo_root, language, expected):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    target_uris = {
        row["uri"]
        for row in dataset.concepts
        if row["kind"] == "instrument" and row["resolution_status"] == "resolved"
    }
    covered = {
        row["concept_uri"]
        for row in dataset.labels
        if row["language"] == language and row["concept_uri"] in target_uris
    }
    assert len(covered) == expected


def test_native_skos_enrichment_is_present(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    assert sum(row["label_type"] == "alternative" for row in dataset.labels) == 6868
    assert (
        sum(
            row["language"] == "da" and row["label_type"] == "preferred"
            for row in dataset.labels
        )
        == 2477
    )
    assert sum(row["language"] == "und" for row in dataset.labels) == 1445
    assert sum(bool(row.get("created")) for row in dataset.concepts) == 2724


def test_linguistic_audit_is_deterministic_and_non_authoritative(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    assert Counter(row["rule_code"] for row in dataset.quality_findings) == {
        "skos-label-role-conflict": 89,
        "undetermined-language": 1445,
        "zh-preferred-identical-to-en": 1779,
        "zh-preferred-placeholder-or-uncertain": 53,
        "zh-alternative-latin-script": 2387,
        "definition-repeats-notation": 13,
        "registry-invalid-language-tag": 3679,
    }
    assert all(
        row["assessment_method"] == "automated-heuristic"
        and row["review_effect"] == "none"
        and row["human_review_required"] is True
        for row in dataset.quality_findings
    )
    assert all(row["review_status"] == "unreviewed" for row in dataset.label_assertions)
    normalized_danish = [
        row
        for row in dataset.label_assertions
        if row["language_tag_status"] == "invalid-source-normalized"
    ]
    assert len(normalized_danish) == 3679
    assert all(
        row["submitted_language_tag"] == "dk"
        and row["language_tag"] == "da"
        and row["language_registry_uri"].endswith(
            "#registry-iana-language-subtags-20260614"
        )
        for row in normalized_danish
    )


def test_registry_validation_and_canonicalization(repo_root):
    registry = LanguageSubtagRegistry.load(
        repo_root / "data/registries/iana-language-subtag-registry.json"
    )
    assert registry.file_date == "2026-06-14"
    assert registry.assess("EN-us").canonical == "en-US"
    assert registry.assess("en-Latn").canonical == "en"
    assert registry.assess("iw").canonical == "he"
    assert registry.assess("iw").status == "deprecated"
    assert registry.assess("dk").valid is False
    assert registry.assess("zh-Hant").valid is True


def test_mapping_coverage_and_multiplicity_are_explicit(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    mapped = Counter(row["target_uri"] for row in dataset.classification_assertions)
    resolved = [
        row["uri"]
        for row in dataset.concepts
        if row["kind"] == "instrument" and row["resolution_status"] == "resolved"
    ]
    assert sum(not mapped[uri] for uri in resolved) == 971
    assert sum(mapped[uri] > 1 for uri in resolved) == 90
    assert max(mapped[uri] for uri in resolved) == 9

    notation_by_uri = {
        row["uri"]: row["notation"]
        for row in dataset.concepts
        if row["kind"] == "classification"
    }
    actual_examples = {
        "http://www.mimo-db.eu/InstrumentsKeywords/3111": {
            "321.322",
            "321.322-5",
            "321.322-71",
        },
        "http://www.mimo-db.eu/InstrumentsKeywords/4361": {
            "423.22",
            "423.233.1",
        },
    }
    for target_uri, expected_notations in actual_examples.items():
        observed_notations = {
            notation_by_uri[row["classification_uri"]]
            for row in dataset.classification_assertions
            if row["target_uri"] == target_uri
        }
        assert observed_notations == expected_notations


def test_source_mappings_have_reversible_perspective_bearing_assignments(
    repo_root,
):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    source_pairs = {
        (row["object_uri"], row["subject_uri"])
        for row in dataset.source_relations
        if row["predicate_uri"] == EXACT_MATCH
    }
    assertion_pairs = {
        (row["target_uri"], row["classification_uri"])
        for row in dataset.classification_assertions
    }
    assert assertion_pairs == source_pairs
    assert all(
        row["predicate_uri"] == CLASSIFIED_AS
        and row["source_predicate_uri"] == EXACT_MATCH
        and row["assigned_by_uri"] == MIMO_AGENT
        and row["generated_by_uri"] == PROJECT_AGENT
        and row["perspective_uri"] == MIMO_PERSPECTIVE
        and row["stance"] == "source-asserted"
        and row["applicability_scope_uris"] == [SOURCE_SILENT_SCOPE]
        and set(row["projection_policy_uris"]) == {SOURCE_POLICY, CLAIMS_POLICY}
        and row["authority_assignment_uris"] == []
        and row["assertion_origin"] == "source-derived"
        and row["evidence"][0]["evidence_type"] == "source-record"
        for row in dataset.classification_assertions
    )


def test_endorsed_projection_requires_context_independent_scope_and_reviews(
    repo_root,
):
    dataset = Dataset.load(repo_root / "data/canonical")
    assignment = dict(dataset.classification_assertions[0])
    assignment.update(
        {
            "uri": "https://example.org/assignment/endorsed",
            "stance": "endorsed",
            "assertion_origin": "project-asserted",
            "assigned_by_uri": PROJECT_AGENT,
            "applicability_scope_uris": [
                "https://example.org/scope/context-independent"
            ],
            "projection_policy_uris": [CLAIMS_POLICY, ENDORSED_POLICY],
        }
    )
    dataset.applicability_scopes.append(
        {
            "uri": "https://example.org/scope/context-independent",
            "label": "Context-independent test scope",
            "scope_mode": "context-independent",
            "description": "Test claimant asserts context independence for this method.",
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
    second_reviewer = "https://example.org/agent/organologist-2"
    dataset.agents.append(
        {
            "uri": second_reviewer,
            "agent_type": "person",
            "name": "Second test organologist",
            "resource_uri": second_reviewer,
        }
    )

    def authority(uri: str, agent_uri: str, dimension: str):
        return {
            "uri": uri,
            "agent_uri": agent_uri,
            "represented_community_uri": None,
            "authority_role": "organology-reviewer",
            "authority_basis_uri": "https://example.org/mandate/test",
            "conferred_by_agent_uri": PROJECT_AGENT,
            "subject_matter_uris": [assignment["uri"]],
            "covered_validation_dimensions": [dimension],
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
                    "citation": "Illustrative competence mandate",
                    "evidence_type": "source-record",
                    "relation": "documents",
                    "resource_uri": "https://example.org/mandate/test",
                    "note": None,
                }
            ],
        }

    authorities = [
        authority(
            "https://example.org/authority/referential", MIMO_AGENT, "referential"
        ),
        authority(
            "https://example.org/authority/scholarly", second_reviewer, "scholarly"
        ),
    ]
    dataset.authority_assignments.extend(authorities)

    def review(uri: str, reviewer: str, dimension: str, authority_uri: str):
        return {
            "uri": uri,
            "decision_uri": review_decision_uri(uri),
            "target_assertion_uri": assignment["uri"],
            "reviewer_agent_uri": reviewer,
            "reviewer_authority": "organology",
            "authority_assignment_uris": [authority_uri],
            "review_method": "human",
            "validation_dimension": dimension,
            "outcome": "accepted",
            "reviewed_at": "2026-07-18T00:00:00Z",
            "valid_until": None,
            "perspective_uri": MIMO_PERSPECTIVE,
            "represented_community_uris": [],
            "applicability_scope_uris": [
                "https://example.org/scope/context-independent"
            ],
            "evidence": [
                {
                    "citation": "Illustrative expert review",
                    "evidence_type": "reasoning",
                    "relation": "supports",
                    "resource_uri": None,
                    "note": None,
                }
            ],
            "rationale": "The assignment is accepted for this test.",
            "rights_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
            "supersedes_decision_uri": None,
            "suspends_decision_uri": None,
            "reinstates_decision_uri": None,
            "decision_status": "active",
            "projection_policy_uris": [ENDORSED_POLICY],
        }

    reviews = [
        review(
            "https://example.org/review/referential",
            MIMO_AGENT,
            "referential",
            authorities[0]["uri"],
        ),
        review(
            "https://example.org/review/scholarly",
            second_reviewer,
            "scholarly",
            authorities[1]["uri"],
        ),
    ]
    dataset.review_events.extend(reviews)
    assert dataset.is_directly_endorsed(assignment)

    assignment["projection_policy_uris"] = [CLAIMS_POLICY]
    assert not dataset.is_directly_endorsed(assignment)
    assignment["projection_policy_uris"] = [CLAIMS_POLICY, ENDORSED_POLICY]

    reviews[1]["outcome"] = "disputed"
    assert not dataset.is_directly_endorsed(assignment)
    reviews[1]["outcome"] = "accepted"
    dataset.applicability_scopes[-1]["scope_mode"] = "specified"
    dataset.applicability_scopes[-1]["community_uris"] = [
        "https://example.org/community/a"
    ]
    assert not dataset.is_directly_endorsed(assignment)
    assert dataset.is_endorsed_for_context(
        assignment,
        {"community_uris": ["https://example.org/community/a"]},
    )
    assert not dataset.is_endorsed_for_context(
        assignment,
        {"community_uris": ["https://example.org/community/b"]},
    )
    assert not dataset.is_endorsed_for_context(assignment, {})
    dataset.applicability_scopes[-1]["community_uris"] = []
    dataset.applicability_scopes[-1]["scope_mode"] = "source-silent"
    assert not dataset.is_directly_endorsed(assignment)


def test_review_decisions_remain_non_collapsing_and_supersession_is_targeted(repo_root):
    dataset = Dataset.load(repo_root / "data/canonical")
    target = dataset.classification_assertions[0]["uri"]

    def decision(uri: str, outcome: str, supersedes: str | None = None):
        return {
            "uri": uri,
            "decision_uri": review_decision_uri(uri),
            "target_assertion_uri": target,
            "reviewer_agent_uri": MIMO_AGENT,
            "reviewer_authority": "organology",
            "authority_assignment_uris": [],
            "review_method": "human",
            "validation_dimension": "scholarly",
            "outcome": outcome,
            "reviewed_at": "2026-07-18T00:00:00Z",
            "valid_until": None,
            "perspective_uri": MIMO_PERSPECTIVE,
            "represented_community_uris": [],
            "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
            "evidence": [
                {
                    "citation": "Illustrative decision",
                    "evidence_type": "reasoning",
                    "relation": "supports",
                    "resource_uri": None,
                    "note": None,
                }
            ],
            "rationale": "Test decision.",
            "rights_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
            "supersedes_decision_uri": supersedes,
            "suspends_decision_uri": None,
            "reinstates_decision_uri": None,
            "decision_status": "active",
            "projection_policy_uris": [CLAIMS_POLICY],
        }

    accepted = decision("https://example.org/review/accepted", "accepted")
    disputed = decision("https://example.org/review/disputed", "disputed")
    dataset.review_events.extend([accepted, disputed])
    assert {row["outcome"] for row in dataset.active_review_decisions(target)} == {
        "accepted",
        "disputed",
    }

    replacement = decision(
        "https://example.org/review/replacement",
        "unverifiable",
        accepted["decision_uri"],
    )
    replacement["reviewed_at"] = "2026-07-19T00:00:00Z"
    replacement["valid_until"] = "2026-07-20T00:00:00Z"
    dataset.review_events.append(replacement)
    assert {
        row["outcome"]
        for row in dataset.active_review_decisions(target, as_of="2026-07-19T12:00:00Z")
    } == {
        "disputed",
        "unverifiable",
    }
    assert {
        row["uri"]
        for row in dataset.active_review_decisions(target, as_of="2026-07-21T00:00:00Z")
    } == {disputed["uri"]}

    reinstatement = decision("https://example.org/review/reinstatement", "accepted")
    reinstatement["reviewed_at"] = "2026-07-22T00:00:00Z"
    reinstatement["reinstates_decision_uri"] = accepted["decision_uri"]
    dataset.review_events.append(reinstatement)
    active_after_reinstatement = {
        row["uri"]
        for row in dataset.active_review_decisions(target, as_of="2026-07-23T00:00:00Z")
    }
    assert accepted["uri"] in active_after_reinstatement

    suspension = decision("https://example.org/review/suspension", "unverifiable")
    suspension["reviewed_at"] = "2026-07-24T00:00:00Z"
    suspension["valid_until"] = "2026-07-25T00:00:00Z"
    suspension["suspends_decision_uri"] = disputed["decision_uri"]
    dataset.review_events.append(suspension)
    assert disputed["uri"] not in {
        row["uri"]
        for row in dataset.active_review_decisions(target, as_of="2026-07-24T12:00:00Z")
    }
    assert disputed["uri"] in {
        row["uri"]
        for row in dataset.active_review_decisions(target, as_of="2026-07-26T00:00:00Z")
    }


def test_labels_and_notes_have_reversible_qualified_assertions(repo_root):
    dataset = Dataset.load(repo_root / "data/canonical")
    source_labels = {
        (row["concept_uri"], row["language"], row["label_type"], row["label"])
        for row in dataset.labels
    }
    asserted_labels = {
        (
            row["concept_uri"],
            row["language_tag"],
            row["label_role"],
            row["literal_form"],
        )
        for row in dataset.label_assertions
    }
    assert asserted_labels == source_labels
    assert all(
        row["asserted_by_uri"] == MIMO_AGENT
        and row["assertion_origin"] == "source-asserted"
        and row["review_status"] == "unreviewed"
        and row["uri"]
        == assertion_uri(
            "label",
            row["concept_uri"],
            row["language_tag"],
            row["label_role"],
            row["literal_form"],
            row["source_record_uri"],
            row["asserted_by_uri"],
            row["source_uri"],
        )
        for row in dataset.label_assertions
    )
    source_notes = {
        (row["uri"], row["definition"])
        for row in dataset.concepts
        if row.get("definition")
    }
    asserted_notes = {
        (row["concept_uri"], row["literal_form"]) for row in dataset.note_assertions
    }
    assert asserted_notes == source_notes
    assert all(
        row["asserted_by_uri"] == MIMO_AGENT
        and row["predicate_uri"].endswith("#definition")
        and row["review_status"] == "unreviewed"
        for row in dataset.note_assertions
    )


def test_skosxl_resources_are_stable_non_collapsing_and_context_free(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    assert len(dataset.label_resources) == len(dataset.label_assertions) == 42662
    assert all(
        set(row)
        == {
            "uri",
            "literal_form",
            "normalized_form",
            "language_tag",
            "language_registry_uri",
        }
        for row in dataset.label_resources
    )
    assert all(
        row["label_resource_uri"]
        == label_resource_uri(
            row["concept_uri"],
            row["language_tag"],
            row["label_role"],
            row["literal_form"],
            row["source_record_uri"],
            row["asserted_by_uri"],
            row["source_uri"],
        )
        for row in dataset.label_assertions
    )
    repeated = [
        row
        for row in dataset.label_resources
        if row["language_tag"] == "ko" and row["literal_form"] == "기타"
    ]
    assert len(repeated) == 6
    assert len({row["uri"] for row in repeated}) == 6


def test_linguistic_profiles_separate_declared_and_observed_evidence(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    assert len(dataset.label_profiles) == len(dataset.label_resources) == 42662
    assert {row["label_resource_uri"] for row in dataset.label_profiles} == {
        row["uri"] for row in dataset.label_resources
    }
    assert {row["translation_status"] for row in dataset.label_profiles} == {
        "unverified"
    }
    assert all(
        row["language_variety_uri"] is None
        and row["writing_system_uri"] is None
        and row["transliteration_system_uri"] is None
        and row["term_roles"] == []
        and all(not values for values in row["applies_to"].values())
        for row in dataset.label_profiles
    )
    chinese = next(
        row
        for row in dataset.label_profiles
        if row["language_tag"] == "zh" and "Hani" in row["observed_script_codes"]
    )
    assert chinese["default_script_subtag"] is None
    assert chinese["explicit_script_subtag"] is None
    latin_chinese = next(
        row
        for row in dataset.label_profiles
        if row["language_tag"] == "zh" and row["observed_script_codes"] == ["Latn"]
    )
    assert latin_chinese["translation_status"] == "unverified"
    assert latin_chinese["term_roles"] == []


def test_skos_projection_suppresses_role_conflicts_without_changing_source(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    suppressed = [
        row
        for row in dataset.label_assertions
        if row["skos_projection_status"] == "suppressed-role-conflict"
    ]
    assert len(suppressed) == 89
    assert {row["label_role"] for row in suppressed} == {"alternative"}
    assert all(row["review_status"] == "unreviewed" for row in suppressed)
    source_keys = {
        (row["concept_uri"], row["language"], row["label_type"], row["label"])
        for row in dataset.labels
    }
    assert all(
        (
            row["concept_uri"],
            row["language_tag"],
            row["label_role"],
            row["literal_form"],
        )
        in source_keys
        for row in suppressed
    )


def test_missing_label_assertion_is_rejected(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    dataset.label_assertions.pop()
    with pytest.raises(
        ValidationError,
        match="do not exactly project source labels",
    ):
        dataset.validate()


def test_classification_assertion_without_source_mapping_is_rejected(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    dataset.classification_assertions.pop()
    with pytest.raises(
        ValidationError,
        match="do not exactly project MIMO source mappings",
    ):
        dataset.validate()


def test_exact_duplicate_labels_are_rejected(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    dataset.labels.append(dict(dataset.labels[0]))
    with pytest.raises(ValidationError, match="duplicate label records"):
        dataset.validate()


def test_broader_cycles_are_rejected(repo_root):
    dataset = Dataset.load(repo_root / "data" / "canonical")
    root = next(row for row in dataset.concepts if row.get("notation") == "1")
    child_relation = next(
        row
        for row in dataset.source_relations
        if row["predicate_uri"].endswith("#broader")
        and row["object_uri"] == root["uri"]
    )
    dataset.source_relations.append(
        {
            "subject_uri": root["uri"],
            "predicate_uri": child_relation["predicate_uri"],
            "object_uri": child_relation["subject_uri"],
            "source_uri": root["uri"],
        }
    )
    with pytest.raises(ValidationError, match="hierarchy contains a cycle"):
        dataset.validate()
