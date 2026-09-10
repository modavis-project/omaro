"""Canonical data model loading and validation."""

from __future__ import annotations

import json
import hashlib
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

from .language_registry import LanguageSubtagRegistry
from .script_registry import UnicodeScriptRegistry

SKOS = "http://www.w3.org/2004/02/skos/core#"
REPOSITORY_URI = "https://github.com/modavis-project/omaro"
OMARO = "https://w3id.org/modavis/omaro#"
ONTOLOGY_URI = "https://w3id.org/modavis/omaro/ontology"
SCHEMA_BASE_URI = "https://w3id.org/modavis/omaro/schema/"
DATASET_BASE_URI = "https://w3id.org/modavis/omaro/dataset"
HS_SCHEME = "http://www.mimo-db.eu/HornbostelAndSachs#"
INSTRUMENT_SCHEME = "http://www.mimo-db.eu/InstrumentsKeywords#"
HS_PREFIX = "http://www.mimo-db.eu/HornbostelAndSachs/"
INSTRUMENT_PREFIX = "http://www.mimo-db.eu/InstrumentsKeywords/"
BROADER = f"{SKOS}broader"
NARROWER = f"{SKOS}narrower"
RELATED = f"{SKOS}related"
EXACT_MATCH = f"{SKOS}exactMatch"
CLOSE_MATCH = f"{SKOS}closeMatch"
BROAD_MATCH = f"{SKOS}broadMatch"
NARROW_MATCH = f"{SKOS}narrowMatch"
RELATED_MATCH = f"{SKOS}relatedMatch"
STRUCTURAL_RELATION_PREDICATES = frozenset({BROADER, NARROWER, RELATED})
MAPPING_RELATION_PREDICATES = frozenset(
    {EXACT_MATCH, CLOSE_MATCH, BROAD_MATCH, NARROW_MATCH, RELATED_MATCH}
)
CLASSIFIED_AS = f"{OMARO}classifiedAs"
PUBLICATION_ACTION_EXPORT = f"{OMARO}use-action-export"
PUBLICATION_ACTION_DISPLAY = f"{OMARO}use-action-display"
PUBLICATION_PURPOSE = f"{OMARO}use-purpose-public-reference-release"
PUBLICATION_AUDIENCE = f"{OMARO}use-audience-general-public"
HS_COMPOUND_GRAMMAR = f"{OMARO}notation-grammar-mimo-hs-plus"
MIMO_AGENT = f"{OMARO}agent-mimo"
PROJECT_AGENT = f"{OMARO}agent-omaro"
MIMO_PERSPECTIVE = f"{OMARO}perspective-mimo-source"
SOURCE_SILENT_SCOPE = f"{OMARO}scope-source-silent"
SOURCE_POLICY = f"{OMARO}projection-policy-source-faithful"
CLAIMS_POLICY = f"{OMARO}projection-policy-research-claims"
ENDORSED_POLICY = f"{OMARO}projection-policy-project-endorsed"
REVIEW_STATUS_CODES = (
    "unreviewed",
    "accepted",
    "disputed",
    "rejected",
    "superseded",
)
LABEL_PREDICATES = {
    "preferred": f"{SKOS}prefLabel",
    "alternative": f"{SKOS}altLabel",
    "hidden": f"{SKOS}hiddenLabel",
}
NOTE_PREDICATES = {
    f"{SKOS}definition",
    f"{SKOS}scopeNote",
    f"{SKOS}historyNote",
    f"{SKOS}editorialNote",
    f"{SKOS}changeNote",
    f"{SKOS}example",
}
QUALITY_RULE_DEFINITIONS = (
    (
        "skos-label-role-conflict",
        "Referential",
        "warning",
        "Identical literal has conflicting SKOS label roles",
        "The source assertions are preserved, but the lower-priority direct SKOS and SKOS-XL link is suppressed.",
    ),
    (
        "registry-invalid-language-tag",
        "Linguistic",
        "warning",
        "Submitted language tag is invalid in the IANA registry",
        "The submitted form is preserved and any project normalization is explicit.",
    ),
    (
        "noncanonical-language-tag",
        "Linguistic",
        "warning",
        "Language tag is valid but non-canonical or deprecated",
        "Canonicalization is technical metadata and does not establish linguistic validity.",
    ),
    (
        "undetermined-language",
        "Linguistic",
        "warning",
        "Language is undetermined",
        "The source label is tagged und and requires language or variety review.",
    ),
    (
        "zh-preferred-identical-to-en",
        "Linguistic",
        "warning",
        "Chinese preferred label is identical to English",
        "Identity across zh and en is a review signal, not proof of mistagging.",
    ),
    (
        "zh-preferred-placeholder-or-uncertain",
        "Linguistic",
        "warning",
        "Chinese preferred label contains a placeholder or uncertainty marker",
        "Question marks and translation placeholders require human review.",
    ),
    (
        "zh-alternative-latin-script",
        "Linguistic",
        "warning",
        "Chinese alternative label uses Latin script without Han characters",
        "This may be a valid transliteration or loanword and must not be auto-corrected.",
    ),
    (
        "definition-repeats-notation",
        "Referential",
        "warning",
        "Definition only repeats the classification notation",
        "A repeated notation does not document the concept boundary.",
    ),
)
LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
IANA_REGISTRY_SOURCE = (
    "https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry"
)
UNICODE_SCRIPT_VERSION = "17.0.0"
UNICODE_SCRIPT_SOURCE_URIS = (
    "https://www.unicode.org/Public/17.0.0/ucd/Scripts.txt",
    "https://www.unicode.org/Public/17.0.0/ucd/PropertyValueAliases.txt",
)
TERM_ROLE_CODES = (
    "endonym",
    "exonym",
    "loanword",
    "translation",
    "transliteration",
    "historical-name",
    "collector-term",
    "trade-name",
    "scholarly-name",
    "misspelling",
    "contested",
    "harmful-legacy-term",
)

TARGET_KIND_BY_TARGET_TYPE = {
    "instrument-concept": "instrument-concept",
    "physical-object": "physical-object",
    "instrument-component": "instrument-component",
    "functional-module": "functional-module",
    "instrument-aggregate": "instrument-aggregate",
    "instrument-configuration": "instrument-configuration",
    "condition-state": "condition-state",
    "sounding-realization": "sounding-realization",
    "performance-event": "performance-event",
    "ensemble-medium": "ensemble-medium",
}


class ValidationError(ValueError):
    """Raised when canonical dataset invariants are violated."""


def canonical_json(value: Any, *, indent: int | None = None) -> str:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=indent,
            separators=(",", ":") if indent is None else None,
        )
        + "\n"
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValidationError(f"{path}:{line_number}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]], key) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in sorted(rows, key=key):
            handle.write(canonical_json(row))


def classification_assertion_uri(
    classification_uri: str,
    target_uri: str,
    *,
    source_record_uri: str,
    assigned_by_uri: str,
    perspective_uri: str,
    classification_method_uri: str,
    source_uri: str,
) -> str:
    """Return a stable URI for one source assignment occurrence.

    Pair identity is deliberately insufficient: the same target/class pair may
    recur in another snapshot, perspective, method, or independently supplied
    source occurrence.  The content-addressed identifier therefore includes the
    occurrence-defining provenance that is stable within a source snapshot.
    """
    return assertion_uri(
        "classification",
        classification_uri,
        target_uri,
        source_record_uri,
        assigned_by_uri,
        perspective_uri,
        classification_method_uri,
        source_uri,
    )


def classification_assignment_uri(assertion_uri_value: str) -> str:
    """Return the activity URI paired with a classification assertion entity."""
    return assertion_uri("classification-assignment", assertion_uri_value)


def review_decision_uri(review_event_uri: str) -> str:
    """Return the durable decision entity generated by a review activity."""
    return assertion_uri("review-decision", review_event_uri)


def controlled_value_uri(category: str, code: str) -> str:
    """Expand a compact JSON code into the persistent RDF vocabulary URI."""
    return f"{OMARO}{category}-{code}"


def compound_expression_uri(source_concept_uri: str, notation: str) -> str:
    """Return a stable URI for a lossless parse of a compound source notation."""
    return assertion_uri("classification-expression", source_concept_uri, notation)


def classification_expressions_from_concepts(
    concepts: Iterable[dict[str, Any]], metadata: dict[str, Any]
) -> list[dict[str, Any]]:
    """Tokenize MIMO plus notations without guessing component or suffix scope.

    The source vocabulary establishes an ordered combination, but a bare string
    does not establish which physical subsystem a member classifies or whether
    a trailing suffix is local or shared.  Those semantics remain explicitly
    unresolved until an expert-interpreted expression supplies them.
    """
    hs_source_record_uri = source_record_uri(HS_SCHEME, metadata["source_retrieved_at"])
    notation_index = {
        row.get("notation"): row["uri"]
        for row in concepts
        if row.get("scheme_uri") == HS_SCHEME and row.get("notation")
    }
    rows: list[dict[str, Any]] = []
    for concept in concepts:
        notation = concept.get("notation")
        if (
            concept.get("scheme_uri") != HS_SCHEME
            or not notation
            or "+" not in notation
        ):
            continue
        members = notation.split("+")
        rows.append(
            {
                "uri": compound_expression_uri(concept["uri"], notation),
                "source_concept_uri": concept["uri"],
                "notation_literal": notation,
                "notation_grammar_uri": HS_COMPOUND_GRAMMAR,
                "expression_scheme_version_uri": hs_source_record_uri,
                "combination_operator": "joint",
                "members": [
                    {
                        "sequence_index": index,
                        "member_notation": member,
                        "classification_uri": notation_index.get(member),
                        "member_assertion_uri": None,
                        "member_target_uri": None,
                        "component_role_uri": None,
                        "local_suffix_notation": None,
                    }
                    for index, member in enumerate(members, 1)
                ],
                "shared_suffix_notation": None,
                "parse_status": "tokenized-uninterpreted",
                "perspective_uri": MIMO_PERSPECTIVE,
                "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
                "source_record_uri": hs_source_record_uri,
                "evidence": [
                    {
                        "citation": "MIMO Hornbostel-Sachs source notation",
                        "evidence_type": "source-record",
                        "relation": "documents",
                        "resource_uri": concept["uri"],
                        "note": (
                            "Member order is preserved; component targets and "
                            "suffix scope remain uninterpreted until expert review."
                        ),
                    }
                ],
                "authority_assignment_uris": [],
                "protocol_application_uris": [],
                "rights_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
            }
        )
    return sorted(rows, key=lambda row: row["uri"])


def review_status_uri(code: str) -> str:
    return f"{OMARO}review-status-{code}"


def assertion_uri(assertion_type: str, *parts: str) -> str:
    """Return a stable content-addressed URI for a lexical or note assertion."""
    digest = hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:32]
    return f"{OMARO}{assertion_type}-{digest}"


def label_resource_uri(
    concept_uri: str,
    language_tag: str,
    label_role: str,
    literal_form: str,
    source_record_uri: str,
    asserted_by_uri: str,
    source_uri: str,
) -> str:
    """Return a non-collapsing SKOS-XL URI for one source label occurrence."""
    return assertion_uri(
        "xl-label",
        concept_uri,
        language_tag,
        label_role,
        literal_form,
        source_record_uri,
        asserted_by_uri,
        source_uri,
    )


def label_resources_from_assertions(
    label_assertions: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Project each contextual label occurrence into a SKOS-XL resource."""
    resources: list[dict[str, str]] = []
    for assertion in label_assertions:
        resources.append(
            {
                "uri": label_resource_uri(
                    assertion["concept_uri"],
                    assertion["language_tag"],
                    assertion["label_role"],
                    assertion["literal_form"],
                    assertion["source_record_uri"],
                    assertion["asserted_by_uri"],
                    assertion["source_uri"],
                ),
                "literal_form": assertion["literal_form"],
                "normalized_form": assertion["normalized_form"],
                "language_tag": assertion["language_tag"],
                "language_registry_uri": assertion["language_registry_uri"],
            }
        )
    return sorted(resources, key=lambda row: row["uri"])


def _label_projection_statuses(
    labels: Iterable[dict[str, Any]],
) -> dict[tuple[str, str, str, str], str]:
    """Select a SKOS-consistent direct projection while preserving source rows."""
    rows = list(labels)
    roles_by_form: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for label in rows:
        roles_by_form[(label["concept_uri"], label["language"], label["label"])].add(
            label["label_type"]
        )
    precedence = {"preferred": 0, "alternative": 1, "hidden": 2}
    statuses: dict[tuple[str, str, str, str], str] = {}
    for label in rows:
        form_key = (label["concept_uri"], label["language"], label["label"])
        roles = roles_by_form[form_key]
        selected = min(roles, key=precedence.__getitem__)
        key = (
            label["concept_uri"],
            label["language"],
            label["label_type"],
            label["label"],
        )
        statuses[key] = (
            "projected"
            if label["label_type"] == selected
            else "suppressed-role-conflict"
        )
    return statuses


def quality_rule_uri(code: str) -> str:
    return f"{OMARO}quality-rule-{code}"


def default_quality_rules() -> list[dict[str, str]]:
    return [
        {
            "uri": quality_rule_uri(code),
            "code": code,
            "validation_dimension": dimension.lower(),
            "severity": severity,
            "title": title,
            "description": description,
            "assessment_method": "automated-heuristic",
            "review_effect": "none",
        }
        for code, dimension, severity, title, description in QUALITY_RULE_DEFINITIONS
    ]


def _has_unicode_name(text: str, needle: str) -> bool:
    return any(
        character.isalpha() and needle in unicodedata.name(character, "")
        for character in text
    )


def linguistic_quality_findings(
    label_assertions: Iterable[dict[str, Any]],
    note_assertions: Iterable[dict[str, Any]],
    concepts_by_uri: dict[str, dict[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    """Generate review signals without changing assertion review status."""
    labels = list(label_assertions)
    english_preferred = {
        row["concept_uri"]: row["literal_form"]
        for row in labels
        if row["language_tag"] == "en" and row["label_role"] == "preferred"
    }
    findings: list[dict[str, Any]] = []

    def add(
        rule_code: str,
        target: dict[str, Any],
        evidence: dict[str, str],
    ) -> None:
        context = {"language_tag": target["language_tag"]}
        if target.get("label_role"):
            context["label_role"] = target["label_role"]
        findings.append(
            {
                "uri": assertion_uri("finding", rule_code, target["uri"]),
                "rule_uri": quality_rule_uri(rule_code),
                "rule_code": rule_code,
                "target_assertion_uri": target["uri"],
                "concept_uri": target["concept_uri"],
                "detected_by_uri": PROJECT_AGENT,
                "detected_at": generated_at,
                "assessment_method": "automated-heuristic",
                "validation_dimension": (
                    "referential"
                    if rule_code == "definition-repeats-notation"
                    else "linguistic"
                ),
                "severity": "warning",
                "review_effect": "none",
                "human_review_required": True,
                "applies_to": context,
                "evidence": evidence,
            }
        )

    for row in labels:
        literal = row["literal_form"]
        if row.get("language_tag_status") == "invalid-source-normalized":
            add(
                "registry-invalid-language-tag",
                row,
                {
                    "submitted_language_tag": row["submitted_language_tag"],
                    "canonical_language_tag": row["language_tag"],
                },
            )
        elif row.get("language_tag_status") in {"noncanonical", "deprecated"}:
            add(
                "noncanonical-language-tag",
                row,
                {
                    "submitted_language_tag": row["submitted_language_tag"],
                    "canonical_language_tag": row["language_tag"],
                    "status": row["language_tag_status"],
                },
            )
        if row["language_tag"] == "und":
            add("undetermined-language", row, {"observed_language_tag": "und"})
        if row.get("skos_projection_status") == "suppressed-role-conflict":
            add(
                "skos-label-role-conflict",
                row,
                {
                    "literal_form": literal,
                    "suppressed_role": row["label_role"],
                    "projection_policy": "preferred-over-alternative-over-hidden",
                },
            )
        if (
            row["language_tag"] == "zh"
            and row["label_role"] == "preferred"
            and literal == english_preferred.get(row["concept_uri"])
        ):
            add(
                "zh-preferred-identical-to-en",
                row,
                {"observed_value": literal, "comparison_language_tag": "en"},
            )
        if (
            row["language_tag"] == "zh"
            and row["label_role"] == "preferred"
            and (
                "?" in literal
                or "？" in literal
                or "to be translated" in literal.casefold()
            )
        ):
            add(
                "zh-preferred-placeholder-or-uncertain",
                row,
                {"observed_value": literal},
            )
        if (
            row["language_tag"] == "zh"
            and row["label_role"] == "alternative"
            and _has_unicode_name(literal, "LATIN")
            and not _has_unicode_name(literal, "CJK UNIFIED IDEOGRAPH")
            and not _has_unicode_name(literal, "CJK COMPATIBILITY IDEOGRAPH")
        ):
            add(
                "zh-alternative-latin-script",
                row,
                {"observed_value": literal, "detected_script": "Latn"},
            )
    for row in note_assertions:
        if row.get("language_tag_status") == "invalid-source-normalized":
            add(
                "registry-invalid-language-tag",
                row,
                {
                    "submitted_language_tag": row["submitted_language_tag"],
                    "canonical_language_tag": row["language_tag"],
                },
            )
        elif row.get("language_tag_status") in {"noncanonical", "deprecated"}:
            add(
                "noncanonical-language-tag",
                row,
                {
                    "submitted_language_tag": row["submitted_language_tag"],
                    "canonical_language_tag": row["language_tag"],
                    "status": row["language_tag_status"],
                },
            )
        concept = concepts_by_uri[row["concept_uri"]]
        if (
            row["predicate_uri"] == f"{SKOS}definition"
            and concept.get("notation")
            and row["literal_form"].strip() == concept["notation"].strip()
        ):
            add(
                "definition-repeats-notation",
                row,
                {
                    "observed_value": row["literal_form"],
                    "notation": concept["notation"],
                },
            )
    return findings


def source_record_uri(scheme_uri: str, retrieved_at: str) -> str:
    source_name = {
        HS_SCHEME: "mimo-hornbostel-sachs",
        INSTRUMENT_SCHEME: "mimo-instrument-keywords",
    }[scheme_uri]
    timestamp = re.sub(r"[^0-9A-Za-z]", "", retrieved_at)
    return f"{OMARO}source-{source_name}-{timestamp}"


def language_registry_uri(file_date: str) -> str:
    return f"{OMARO}registry-iana-language-subtags-{file_date.replace('-', '')}"


def language_registry_record(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "uri": language_registry_uri(data["file_date"]),
        "registry_type": "IANA Language Subtag Registry",
        "file_date": data["file_date"],
        "source_uri": data["source_uri"],
        "artifact_path": "registries/iana-language-subtag-registry.json",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "profile_uri": "https://www.rfc-editor.org/rfc/rfc5646",
        "normalization_overrides": {"dk": "da"},
    }


def script_registry_uri(unicode_version: str) -> str:
    return f"{OMARO}registry-unicode-scripts-{unicode_version.replace('.', '')}"


def script_registry_record(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "uri": script_registry_uri(data["unicode_version"]),
        "registry_type": "Unicode Script Property",
        "unicode_version": data["unicode_version"],
        "source_uris": data["source_uris"],
        "artifact_path": "registries/unicode-script-registry.json",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "profile_uri": "https://www.unicode.org/reports/tr24/",
    }


def label_profiles_from_assertions(
    label_assertions: Iterable[dict[str, Any]],
    language_registry: LanguageSubtagRegistry,
    script_registry: UnicodeScriptRegistry,
    script_registry_uri_value: str,
) -> list[dict[str, Any]]:
    """Create conservative linguistic profiles without guessing cultural facts."""
    rows: list[dict[str, Any]] = []
    for assertion in label_assertions:
        scripts, has_common = script_registry.observe(assertion["normalized_form"])
        components = language_registry.components(assertion["language_tag"])
        rows.append(
            {
                "uri": assertion_uri("label-profile", assertion["label_resource_uri"]),
                "label_resource_uri": assertion["label_resource_uri"],
                "source_label_assertion_uri": assertion["uri"],
                "language_tag": assertion["language_tag"],
                **components,
                "language_variety_uri": None,
                "writing_system_uri": None,
                "observed_script_codes": scripts,
                "has_common_or_inherited_characters": has_common,
                "script_observation_method": "unicode-script-property-17.0.0",
                "script_registry_uri": script_registry_uri_value,
                "transliteration_system_uri": None,
                "transcription_system_uri": None,
                "pronunciations": [],
                "audio_uris": [],
                "term_roles": [],
                "translation_status": "unverified",
                "applies_to": {
                    "community_uris": [],
                    "place_uris": [],
                    "period_uris": [],
                    "usage_domain_uris": [],
                },
                "display_policy": "source-fallback",
                "search_policy": "include-with-warning",
                "asserted_by_uri": PROJECT_AGENT,
                "source_record_uri": assertion["source_record_uri"],
                "assertion_origin": "source-derived",
                "review_status": "unreviewed",
                "review_status_uri": review_status_uri("unreviewed"),
            }
        )
    return sorted(rows, key=lambda row: row["uri"])


def language_tag_fields(
    submitted: str, registry: LanguageSubtagRegistry, registry_uri: str
) -> dict[str, str]:
    assessment = registry.assess(submitted)
    if submitted.lower() == "dk":
        return {
            "submitted_language_tag": submitted,
            "language_tag": "da",
            "language_tag_status": "invalid-source-normalized",
            "language_registry_uri": registry_uri,
        }
    if not assessment.valid or assessment.canonical is None:
        return {
            "submitted_language_tag": submitted,
            "language_tag": "und",
            "language_tag_status": "invalid-source-normalized",
            "language_registry_uri": registry_uri,
        }
    return {
        "submitted_language_tag": submitted,
        "language_tag": assessment.canonical,
        "language_tag_status": assessment.status,
        "language_registry_uri": registry_uri,
    }


def default_agents() -> list[dict[str, str]]:
    return [
        {
            "uri": MIMO_AGENT,
            "agent_type": "organization",
            "name": "Musical Instrument Museums Online (MIMO)",
            "resource_uri": "https://mimo-international.com/",
        },
        {
            "uri": PROJECT_AGENT,
            "agent_type": "software",
            "name": "OMARO build pipeline",
            "resource_uri": REPOSITORY_URI,
        },
    ]


def default_review_statuses() -> list[dict[str, str]]:
    descriptions = {
        "unreviewed": "No human review has been recorded.",
        "accepted": "Accepted by a recorded domain, linguistic, or community review.",
        "disputed": "One or more recorded perspectives dispute this assertion.",
        "rejected": "Rejected for active project use but preserved for audit.",
        "superseded": "Replaced by a later assertion or review decision.",
    }
    return [
        {
            "uri": review_status_uri(code),
            "code": code,
            "label": code.replace("-", " ").title(),
            "description": descriptions[code],
        }
        for code in REVIEW_STATUS_CODES
    ]


def default_perspectives() -> list[dict[str, Any]]:
    """Return perspectives that are actually evidenced by the source snapshot."""
    return [
        {
            "uri": MIMO_PERSPECTIVE,
            "label": "MIMO source perspective",
            "perspective_type": "source",
            "holder_agent_uri": MIMO_AGENT,
            "represented_community_uris": [],
            "description": (
                "The perspective expressed by the preserved MIMO vocabulary snapshot. "
                "It records source attribution and does not claim community authority."
            ),
            "status": "active",
            "valid_from": None,
            "valid_until": None,
            "authority_assignment_uris": [],
        }
    ]


def default_applicability_scopes() -> list[dict[str, Any]]:
    """Return the explicit epistemic scope used for source-silent claims."""
    return [
        {
            "uri": SOURCE_SILENT_SCOPE,
            "label": "Source silent about applicability",
            "scope_mode": "source-silent",
            "description": (
                "The preserved source statement supplies no applicability qualifier. "
                "Source silence must not be interpreted as context-independent validity."
            ),
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
            "perspective_uri": None,
            "source_record_uri": None,
        }
    ]


def default_projection_policies() -> list[dict[str, Any]]:
    """Return named graph/projection policies; none imply universal truth."""
    return [
        {
            "uri": SOURCE_POLICY,
            "label": "Source-faithful projection",
            "description": (
                "Preserves statements exactly as supplied by a named source in the "
                "source graph; it does not endorse them as project conclusions."
            ),
            "graph_role": "source",
            "direct_assertion": True,
            "eligible_stances": ["source-asserted"],
            "review_requirements": [],
            "minimum_independent_reviewers": 0,
            "veto_rules": [],
            "context_match_required": False,
            "unknown_scope_behavior": "warn",
            "includes_source_layer": True,
            "policy_version": "2.2.0",
        },
        {
            "uri": CLAIMS_POLICY,
            "label": "Research claims projection",
            "description": (
                "Exposes every claim occurrence and its evidence without asserting the "
                "reified proposition as an endorsed fact."
            ),
            "graph_role": "claims",
            "direct_assertion": False,
            "eligible_stances": [
                "source-asserted",
                "asserted",
                "proposed",
                "endorsed",
                "disputed",
                "rejected",
                "superseded",
            ],
            "review_requirements": [],
            "minimum_independent_reviewers": 0,
            "veto_rules": [],
            "context_match_required": False,
            "unknown_scope_behavior": "include",
            "includes_source_layer": True,
            "policy_version": "2.2.0",
        },
        {
            "uri": ENDORSED_POLICY,
            "label": "Project-endorsed projection",
            "description": (
                "Asserts only active claims that opt into this policy, satisfy every "
                "required review rule, have two independent reviewers, and have no "
                "active veto-level decision; contextual claims also require a match."
            ),
            "graph_role": "endorsed",
            "direct_assertion": True,
            "eligible_stances": ["asserted", "endorsed"],
            "review_requirements": [
                {
                    "validation_dimension": "referential",
                    "reviewer_authorities": ["organology"],
                    "outcomes": ["accepted"],
                    "minimum_independent_reviewers": 1,
                },
                {
                    "validation_dimension": "scholarly",
                    "reviewer_authorities": ["organology"],
                    "outcomes": ["accepted"],
                    "minimum_independent_reviewers": 1,
                },
            ],
            "minimum_independent_reviewers": 2,
            "veto_rules": [
                {
                    "validation_dimensions": [
                        "referential",
                        "linguistic",
                        "community",
                        "historical",
                        "scholarly",
                        "ethical",
                        "rights",
                    ],
                    "reviewer_authorities": [
                        "community",
                        "language",
                        "organology",
                        "history",
                        "rights",
                        "technical",
                        "ethical",
                    ],
                    "outcomes": [
                        "correction",
                        "disputed",
                        "rejected",
                        "unverifiable",
                        "withdrawn",
                    ],
                }
            ],
            "context_match_required": True,
            "unknown_scope_behavior": "exclude",
            "includes_source_layer": False,
            "policy_version": "2.2.0",
        },
    ]


def default_concept_schemes(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    records = {row["scheme_uri"]: row for row in source_records_from_metadata(metadata)}
    labels = {row["uri"]: row["label"] for row in metadata["schemes"]}
    return [
        {
            "uri": scheme_uri,
            "label": labels[scheme_uri],
            "scheme_type": scheme_type,
            "version": metadata["source_retrieved_at"],
            "version_uri": records[scheme_uri]["uri"],
            "publisher_agent_uri": MIMO_AGENT,
            "perspective_uri": MIMO_PERSPECTIVE,
            "source_record_uri": records[scheme_uri]["uri"],
            "governance_uri": "https://mimo-international.com/",
            "rights_uri": records[scheme_uri]["rights_uri"],
            "status": "active",
            "scope_note": scope_note,
        }
        for scheme_uri, scheme_type, scope_note in (
            (
                HS_SCHEME,
                "classification",
                "MIMO's version of the Hornbostel-Sachs classification; one "
                "organological facet rather than a universal account of an instrument.",
            ),
            (
                INSTRUMENT_SCHEME,
                "thesaurus",
                "MIMO's multilingual thesaurus of musical-instrument concepts.",
            ),
        )
    ]


def source_records_from_metadata(metadata: dict[str, Any]) -> list[dict[str, str]]:
    by_scheme = (
        (
            HS_SCHEME,
            "MIMO Hornbostel–Sachs vocabulary API snapshot",
            metadata["sources"][0],
        ),
        (
            INSTRUMENT_SCHEME,
            "MIMO instrument-keyword vocabulary API snapshot",
            metadata["sources"][1],
        ),
    )
    return [
        {
            "uri": source_record_uri(scheme_uri, metadata["source_retrieved_at"]),
            "resource_uri": resource_uri,
            "title": title,
            "source_type": "vocabulary-api-snapshot",
            "scheme_uri": scheme_uri,
            "publisher_agent_uri": MIMO_AGENT,
            "layer": "mimo-source",
            "rights_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
            "retrieved_at": metadata["source_retrieved_at"],
        }
        for scheme_uri, title, resource_uri in by_scheme
    ]


def label_assertions_from_labels(
    labels: Iterable[dict[str, Any]],
    concepts_by_uri: dict[str, dict[str, Any]],
    metadata: dict[str, Any],
    language_registry: LanguageSubtagRegistry,
    registry_uri: str,
) -> list[dict[str, str]]:
    source_labels = list(labels)
    projection_statuses = _label_projection_statuses(source_labels)
    rows = []
    for label in source_labels:
        concept_uri = label["concept_uri"]
        label_source_record_uri = source_record_uri(
            concepts_by_uri[concept_uri]["scheme_uri"],
            metadata["source_retrieved_at"],
        )
        submitted_language = label.get("submitted_language", label["language"])
        language_fields = language_tag_fields(
            submitted_language, language_registry, registry_uri
        )
        language = language_fields["language_tag"]
        role = label["label_type"]
        literal = label["label"]
        rows.append(
            {
                "uri": assertion_uri(
                    "label",
                    concept_uri,
                    language,
                    role,
                    literal,
                    label_source_record_uri,
                    MIMO_AGENT,
                    concept_uri,
                ),
                "concept_uri": concept_uri,
                "predicate_uri": LABEL_PREDICATES[role],
                "literal_form": literal,
                "normalized_form": unicodedata.normalize("NFC", literal),
                "language_tag": language,
                **language_fields,
                "label_resource_uri": label_resource_uri(
                    concept_uri,
                    language,
                    role,
                    literal,
                    label_source_record_uri,
                    MIMO_AGENT,
                    concept_uri,
                ),
                "label_role": role,
                "skos_projection_status": projection_statuses[
                    (concept_uri, language, role, literal)
                ],
                "asserted_by_uri": MIMO_AGENT,
                "source_record_uri": label_source_record_uri,
                "source_uri": concept_uri,
                "assertion_origin": "source-asserted",
                "review_status": "unreviewed",
                "review_status_uri": review_status_uri("unreviewed"),
            }
        )
    return rows


def note_assertions_from_concepts(
    concepts: Iterable[dict[str, Any]],
    metadata: dict[str, Any],
    language_registry: LanguageSubtagRegistry,
    registry_uri: str,
) -> list[dict[str, str]]:
    rows = []
    for concept in concepts:
        literal = concept.get("definition")
        if not literal:
            continue
        predicate_uri = f"{SKOS}definition"
        note_source_record_uri = source_record_uri(
            concept["scheme_uri"], metadata["source_retrieved_at"]
        )
        rows.append(
            {
                "uri": assertion_uri(
                    "note",
                    concept["uri"],
                    predicate_uri,
                    "en",
                    literal,
                    note_source_record_uri,
                    MIMO_AGENT,
                    concept["uri"],
                ),
                "concept_uri": concept["uri"],
                "predicate_uri": predicate_uri,
                "literal_form": literal,
                "normalized_form": unicodedata.normalize("NFC", literal),
                "language_tag": "en",
                **language_tag_fields("en", language_registry, registry_uri),
                "asserted_by_uri": MIMO_AGENT,
                "source_record_uri": note_source_record_uri,
                "source_uri": concept["uri"],
                "assertion_origin": "source-asserted",
                "review_status": "unreviewed",
                "review_status_uri": review_status_uri("unreviewed"),
            }
        )
    return rows


def classification_assertions_from_source_relations(
    source_relations: Iterable[dict[str, Any]],
    metadata: dict[str, Any],
    classification_expressions: Iterable[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Project MIMO exact-match mappings into qualified classification assertions."""
    hs_source_record_uri = source_record_uri(HS_SCHEME, metadata["source_retrieved_at"])
    method = controlled_value_uri("classification-method", "source-mapping-projection")
    expression_by_concept = {
        row["source_concept_uri"]: row["uri"]
        for row in classification_expressions
        if row.get("source_concept_uri") is not None
    }
    rows: list[dict[str, Any]] = []
    for relation in source_relations:
        if relation["predicate_uri"] != EXACT_MATCH:
            continue
        assertion_id = classification_assertion_uri(
            relation["subject_uri"],
            relation["object_uri"],
            source_record_uri=hs_source_record_uri,
            assigned_by_uri=MIMO_AGENT,
            perspective_uri=MIMO_PERSPECTIVE,
            classification_method_uri=method,
            source_uri=relation["source_uri"],
        )
        rows.append(
            {
                "uri": assertion_id,
                "assignment_uri": classification_assignment_uri(assertion_id),
                "target_uri": relation["object_uri"],
                "target_type": "instrument-concept",
                "predicate_uri": CLASSIFIED_AS,
                "classification_uri": relation["subject_uri"],
                "classification_scheme_uri": HS_SCHEME,
                "scheme_version_uri": hs_source_record_uri,
                "assigned_by_uri": MIMO_AGENT,
                "generated_by_uri": PROJECT_AGENT,
                "perspective_uri": MIMO_PERSPECTIVE,
                "classification_method_uri": method,
                "criteria_uris": [],
                "assessment_uris": [],
                "inference_logic_uri": None,
                "classification_expression_uri": expression_by_concept.get(
                    relation["subject_uri"]
                ),
                "stance": "source-asserted",
                "applicability_scope_uris": [SOURCE_SILENT_SCOPE],
                "evidence": [
                    {
                        "citation": "MIMO source exactMatch mapping",
                        "evidence_type": "source-record",
                        "relation": "documents",
                        "resource_uri": relation["source_uri"],
                        "note": (
                            "The project reverses the source exactMatch direction into a "
                            "qualified classifiedAs occurrence."
                        ),
                    }
                ],
                "authority_assignment_uris": [],
                "valid_from": None,
                "valid_until": None,
                "projection_policy_uris": [SOURCE_POLICY, CLAIMS_POLICY],
                "source_predicate_uri": relation["predicate_uri"],
                "source_uri": relation["source_uri"],
                "source_record_uri": hs_source_record_uri,
                "assertion_origin": "source-derived",
            }
        )
    return rows


@dataclass
class Dataset:
    root: Path
    metadata: dict[str, Any]
    agents: list[dict[str, Any]]
    source_records: list[dict[str, Any]]
    concept_schemes: list[dict[str, Any]]
    perspectives: list[dict[str, Any]]
    applicability_scopes: list[dict[str, Any]]
    authority_assignments: list[dict[str, Any]]
    projection_policies: list[dict[str, Any]]
    review_statuses: list[dict[str, Any]]
    language_registries: list[dict[str, Any]]
    script_registries: list[dict[str, Any]]
    quality_rules: list[dict[str, Any]]
    quality_findings: list[dict[str, Any]]
    review_events: list[dict[str, Any]]
    protocol_applications: list[dict[str, Any]]
    use_decisions: list[dict[str, Any]]
    organological_targets: list[dict[str, Any]]
    classification_criteria: list[dict[str, Any]]
    observation_assessments: list[dict[str, Any]]
    classification_expressions: list[dict[str, Any]]
    concepts: list[dict[str, Any]]
    labels: list[dict[str, Any]]
    label_resources: list[dict[str, Any]]
    label_profiles: list[dict[str, Any]]
    label_assertions: list[dict[str, Any]]
    note_assertions: list[dict[str, Any]]
    source_relations: list[dict[str, Any]]
    concept_relation_assertions: list[dict[str, Any]]
    classification_assertions: list[dict[str, Any]]

    @classmethod
    def load(cls, root: Path) -> "Dataset":
        root = root.resolve()
        return cls(
            root=root,
            metadata=json.loads((root / "metadata.json").read_text(encoding="utf-8")),
            agents=read_jsonl(root / "agents.jsonl"),
            source_records=read_jsonl(root / "source_records.jsonl"),
            concept_schemes=read_jsonl(root / "concept_schemes.jsonl"),
            perspectives=read_jsonl(root / "perspectives.jsonl"),
            applicability_scopes=read_jsonl(root / "applicability_scopes.jsonl"),
            authority_assignments=read_jsonl(root / "authority_assignments.jsonl"),
            projection_policies=read_jsonl(root / "projection_policies.jsonl"),
            review_statuses=read_jsonl(root / "review_statuses.jsonl"),
            language_registries=read_jsonl(root / "language_registries.jsonl"),
            script_registries=read_jsonl(root / "script_registries.jsonl"),
            quality_rules=read_jsonl(root / "quality_rules.jsonl"),
            quality_findings=read_jsonl(root / "quality_findings.jsonl"),
            review_events=read_jsonl(root / "review_events.jsonl"),
            protocol_applications=read_jsonl(root / "protocol_applications.jsonl"),
            use_decisions=read_jsonl(root / "use_decisions.jsonl"),
            organological_targets=read_jsonl(root / "organological_targets.jsonl"),
            classification_criteria=read_jsonl(root / "classification_criteria.jsonl"),
            observation_assessments=read_jsonl(root / "observation_assessments.jsonl"),
            classification_expressions=read_jsonl(
                root / "classification_expressions.jsonl"
            ),
            concepts=read_jsonl(root / "concepts.jsonl"),
            labels=read_jsonl(root / "labels.jsonl"),
            label_resources=read_jsonl(root / "label_resources.jsonl"),
            label_profiles=read_jsonl(root / "label_profiles.jsonl"),
            label_assertions=read_jsonl(root / "label_assertions.jsonl"),
            note_assertions=read_jsonl(root / "note_assertions.jsonl"),
            source_relations=read_jsonl(root / "source_relations.jsonl"),
            concept_relation_assertions=read_jsonl(
                root / "concept_relation_assertions.jsonl"
            ),
            classification_assertions=read_jsonl(
                root / "classification_assertions.jsonl"
            ),
        )

    @property
    def concepts_by_uri(self) -> dict[str, dict[str, Any]]:
        return {row["uri"]: row for row in self.concepts}

    @property
    def labels_by_concept(self) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in self.labels:
            result[row["concept_uri"]].append(row)
        return result

    @property
    def label_assertions_by_concept(self) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in self.label_assertions:
            result[row["concept_uri"]].append(row)
        return result

    @property
    def label_resources_by_uri(self) -> dict[str, dict[str, Any]]:
        return {row["uri"]: row for row in self.label_resources}

    @property
    def label_profiles_by_resource_uri(self) -> dict[str, dict[str, Any]]:
        return {row["label_resource_uri"]: row for row in self.label_profiles}

    @property
    def note_assertions_by_concept(self) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in self.note_assertions:
            result[row["concept_uri"]].append(row)
        return result

    def publication_authorization(
        self,
        target_uris: str | Iterable[str],
        action_uri: str,
        *,
        purpose_uris: str | Iterable[str] = (),
        audience_uris: str | Iterable[str] = (),
        applicability_scope_uris: str | Iterable[str] = (),
        as_of: str | None = None,
        requires_explicit_decision: bool = False,
    ) -> dict[str, Any]:
        """Evaluate authorization independently of epistemic endorsement.

        Community-governed material fails closed.  An active refusal,
        withholding, or withdrawal wins over grants.  Where several communities
        are represented by applicable protocols, every represented community
        must be covered by an active grant.  The returned trace contains only
        identifiers and decision states; private deliberation belongs outside
        this public repository.
        """

        def uri_set(value: str | Iterable[str]) -> set[str]:
            return {value} if isinstance(value, str) else set(value)

        targets = uri_set(target_uris)
        requested_purposes = uri_set(purpose_uris)
        requested_audiences = uri_set(audience_uris)
        requested_scopes = uri_set(applicability_scope_uris)
        reference_time = datetime.fromisoformat(
            (as_of or self.metadata["generated_at"]).replace("Z", "+00:00")
        )

        def active_interval(row: dict[str, Any], start_field: str) -> bool:
            start = datetime.fromisoformat(row[start_field].replace("Z", "+00:00"))
            end = (
                datetime.fromisoformat(row["valid_until"].replace("Z", "+00:00"))
                if row.get("valid_until") is not None
                else None
            )
            return start <= reference_time and (end is None or reference_time <= end)

        superseded_protocols = {
            row["supersedes_uri"]
            for row in self.protocol_applications
            if row.get("supersedes_uri")
            and row["status"] == "active"
            and active_interval(row, "valid_from")
        }
        protocols = [
            row
            for row in self.protocol_applications
            if row["status"] == "active"
            and row["uri"] not in superseded_protocols
            and targets.intersection(row["target_resource_uris"])
            and (
                not requested_scopes
                or bool(requested_scopes.intersection(row["applicability_scope_uris"]))
            )
            and active_interval(row, "valid_from")
        ]
        protocol_uris = {row["uri"] for row in protocols}
        if any(not self.protocol_integrity_valid(row) for row in protocols):
            return {
                "authorized": False,
                "reason": "protocol-integrity-unverified",
                "protocol_application_uris": sorted(protocol_uris),
                "decision_uris": [],
                "missing_community_uris": [],
            }
        superseded = {
            row["supersedes_decision_uri"]
            for row in self.use_decisions
            if row.get("supersedes_decision_uri")
            and row["status"] == "active"
            and datetime.fromisoformat(row["decided_at"].replace("Z", "+00:00"))
            <= reference_time
        }

        def context_matches(row: dict[str, Any], *, denial: bool) -> bool:
            for requested, declared in (
                (requested_purposes, set(row.get("purpose_uris", []))),
                (requested_audiences, set(row.get("audience_uris", []))),
            ):
                if denial:
                    if declared and requested and not requested.intersection(declared):
                        return False
                elif not requested or not requested.issubset(declared):
                    return False
            declared_scopes = set(row.get("applicability_scope_uris", []))
            if requested_scopes:
                return (
                    bool(requested_scopes.intersection(declared_scopes))
                    if denial
                    else requested_scopes.issubset(declared_scopes)
                )
            return denial or not declared_scopes

        candidate_decisions = [
            row
            for row in self.use_decisions
            if row["status"] == "active"
            and row["uri"] not in superseded
            and action_uri in row["action_uris"]
            and targets.intersection(row["target_resource_uris"])
            and datetime.fromisoformat(row["decided_at"].replace("Z", "+00:00"))
            <= reference_time
            and (
                row["valid_until"] is None
                or reference_time
                <= datetime.fromisoformat(row["valid_until"].replace("Z", "+00:00"))
            )
            and (
                not row["protocol_application_uris"]
                or bool(protocol_uris.intersection(row["protocol_application_uris"]))
            )
        ]
        denials = [
            row
            for row in candidate_decisions
            if row["decision"] in {"refused", "withheld", "withdrawn"}
            and context_matches(row, denial=True)
        ]
        if denials:
            return {
                "authorized": False,
                "reason": "active-denial",
                "protocol_application_uris": sorted(protocol_uris),
                "decision_uris": sorted(row["uri"] for row in denials),
                "missing_community_uris": [],
            }
        authority_by_uri = {row["uri"]: row for row in self.authority_assignments}

        def active_authority(
            authority: dict[str, Any], decision: dict[str, Any]
        ) -> bool:
            decision_time = datetime.fromisoformat(
                decision["decided_at"].replace("Z", "+00:00")
            )
            start = datetime.fromisoformat(
                authority["valid_from"].replace("Z", "+00:00")
            )
            end = (
                datetime.fromisoformat(authority["valid_until"].replace("Z", "+00:00"))
                if authority.get("valid_until") is not None
                else None
            )
            return (
                authority["status"] == "active"
                and authority["agent_uri"] == decision["decided_by_agent_uri"]
                and "rights" in authority["covered_validation_dimensions"]
                and action_uri in authority.get("covered_action_uris", [])
                and set(decision["applicability_scope_uris"]).issubset(
                    set(authority["applicability_scope_uris"])
                )
                and start <= decision_time <= reference_time
                and (end is None or reference_time <= end)
            )

        protocol_by_uri = {protocol["uri"]: protocol for protocol in protocols}

        def mandates_cover_decision_subjects(
            authorities: Iterable[dict[str, Any]], decision: dict[str, Any]
        ) -> bool:
            subjects = {
                subject
                for authority in authorities
                for subject in authority["subject_matter_uris"]
            }
            covered_targets = set(subjects)
            for protocol_uri in decision["protocol_application_uris"]:
                protocol = protocol_by_uri.get(protocol_uri)
                if protocol is None:
                    continue
                if protocol["uri"] in subjects or protocol["protocol_uri"] in subjects:
                    covered_targets.update(protocol["target_resource_uris"])
            return set(decision["target_resource_uris"]).issubset(covered_targets)

        grants: list[dict[str, Any]] = []
        invalid_grants: list[dict[str, Any]] = []
        for row in candidate_decisions:
            if row["decision"] != "granted" or not context_matches(row, denial=False):
                continue
            if not targets.issubset(set(row["target_resource_uris"])):
                invalid_grants.append(row)
                continue
            if not protocol_uris.issubset(set(row["protocol_application_uris"])):
                invalid_grants.append(row)
                continue
            valid_authorities = [
                authority_by_uri[uri]
                for uri in row["authority_assignment_uris"]
                if uri in authority_by_uri
                and active_authority(authority_by_uri[uri], row)
            ]
            represented = set(row["represented_community_uris"])
            authority_communities = {
                authority["represented_community_uri"]
                for authority in valid_authorities
                if authority["represented_community_uri"] is not None
            }
            subject_coverage = all(
                mandates_cover_decision_subjects(
                    [
                        authority
                        for authority in valid_authorities
                        if authority["represented_community_uri"] == community
                    ],
                    row,
                )
                for community in represented
            )
            if not represented:
                subject_coverage = mandates_cover_decision_subjects(
                    valid_authorities, row
                )
            legal_ready = (
                row.get("legal_basis_status") in {"documented", "not-required"}
                and bool(row.get("legal_basis_uris"))
                and row.get("legal_basis_assessed_by_agent_uri") is not None
            )
            consent_ready = (
                row.get("consent_status") in {"documented", "not-required"}
                and bool(row.get("consent_record_uris"))
                and row.get("consent_assessed_by_agent_uri") is not None
            )
            if (
                valid_authorities
                and represented.issubset(authority_communities)
                and subject_coverage
                and legal_ready
                and consent_ready
            ):
                grants.append(row)
            else:
                invalid_grants.append(row)
        required_communities = {
            community
            for protocol in protocols
            for community in protocol["represented_community_uris"]
        }
        covered_communities = {
            community
            for decision in grants
            for community in decision["represented_community_uris"]
        }
        missing = required_communities - covered_communities
        if missing or ((protocols or requires_explicit_decision) and not grants):
            return {
                "authorized": False,
                "reason": (
                    "authorization-prerequisites-incomplete"
                    if invalid_grants and not grants
                    else "explicit-authorization-required"
                ),
                "protocol_application_uris": sorted(protocol_uris),
                "decision_uris": sorted(row["uri"] for row in grants),
                "missing_community_uris": sorted(missing),
            }
        return {
            "authorized": True,
            "reason": "explicit-grant" if grants else "public-reference-baseline",
            "protocol_application_uris": sorted(protocol_uris),
            "decision_uris": sorted(row["uri"] for row in grants),
            "missing_community_uris": [],
        }

    def protocol_integrity_valid(self, protocol: dict[str, Any]) -> bool:
        """Verify a protocol pin locally or require an explicit external attestation."""
        if (
            protocol.get("resolution_status") != "verified"
            or protocol.get("protocol_integrity_sha256") is None
        ):
            return False
        method = protocol.get("integrity_verification_method")
        if method == "external-attestation":
            return isinstance(protocol.get("integrity_attestation_uri"), str)
        if method != "local-sha256":
            return False
        relative = protocol.get("protocol_artifact_path")
        if not isinstance(relative, str):
            return False
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            return False
        artifact = (self.root / relative_path).resolve()
        try:
            artifact.relative_to(self.root.resolve())
        except ValueError:
            return False
        if not artifact.is_file():
            return False
        digest = hashlib.sha256()
        with artifact.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest() == protocol["protocol_integrity_sha256"]

    def assert_publication_authorized(self) -> None:
        """Fail before any public build can expose governed material.

        A failed build emits only aggregate counts.  It does not copy a partial
        dataset or enumerate restricted resource identifiers in logs.
        """
        candidates: dict[str, dict[str, Any]] = {}

        def add_candidate(
            target_uri: str, *, scopes: Iterable[str] = (), explicit: bool
        ) -> None:
            candidate = candidates.setdefault(
                target_uri, {"explicit": False, "scopes": set()}
            )
            candidate["explicit"] = candidate["explicit"] or explicit
            candidate["scopes"].update(scopes)

        for protocol in self.protocol_applications:
            for target_uri in protocol["target_resource_uris"]:
                add_candidate(
                    target_uri,
                    scopes=protocol["applicability_scope_uris"],
                    explicit=True,
                )
        for decision in self.use_decisions:
            for target_uri in decision["target_resource_uris"]:
                add_candidate(
                    target_uri,
                    scopes=decision["applicability_scope_uris"],
                    explicit=True,
                )
        perspective_types = {
            row["uri"]: row["perspective_type"] for row in self.perspectives
        }
        scheme_perspectives = {
            row["uri"]: row["perspective_uri"] for row in self.concept_schemes
        }
        for rows in (
            self.classification_assertions,
            self.concept_relation_assertions,
            self.observation_assessments,
            self.classification_criteria,
            self.classification_expressions,
            self.organological_targets,
        ):
            for row in rows:
                if (
                    row.get("assertion_origin") == "community-asserted"
                    or perspective_types.get(row.get("perspective_uri")) == "community"
                ):
                    add_candidate(
                        row["uri"],
                        scopes=row.get("applicability_scope_uris", []),
                        explicit=True,
                    )
        for concept in self.concepts:
            scheme_perspective = scheme_perspectives.get(concept["scheme_uri"])
            if perspective_types.get(scheme_perspective) == "community":
                add_candidate(concept["uri"], explicit=True)
        perspectives_by_uri = {row["uri"]: row for row in self.perspectives}
        for scheme in self.concept_schemes:
            perspective = perspectives_by_uri.get(scheme["perspective_uri"])
            if perspective and perspective["perspective_type"] == "community":
                add_candidate(
                    scheme["uri"],
                    scopes=scheme.get("applicability_scope_uris", []),
                    explicit=True,
                )
                if scheme.get("source_record_uri") is not None:
                    add_candidate(scheme["source_record_uri"], explicit=True)
        authorities_by_uri = {row["uri"]: row for row in self.authority_assignments}
        for perspective in self.perspectives:
            if perspective["perspective_type"] != "community":
                continue
            add_candidate(perspective["uri"], explicit=True)
            add_candidate(perspective["holder_agent_uri"], explicit=True)
            for community_uri in perspective["represented_community_uris"]:
                add_candidate(community_uri, explicit=True)
            for authority_uri in perspective["authority_assignment_uris"]:
                authority = authorities_by_uri.get(authority_uri, {})
                add_candidate(
                    authority_uri,
                    scopes=authority.get("applicability_scope_uris", []),
                    explicit=True,
                )
        actions = (
            controlled_value_uri("use-action", "display"),
            controlled_value_uri("use-action", "index"),
            controlled_value_uri("use-action", "export"),
        )
        failures = 0
        for target_uri, candidate in candidates.items():
            for action_uri in actions:
                result = self.publication_authorization(
                    target_uri,
                    action_uri,
                    purpose_uris=[PUBLICATION_PURPOSE],
                    audience_uris=[PUBLICATION_AUDIENCE],
                    applicability_scope_uris=candidate["scopes"],
                    requires_explicit_decision=candidate["explicit"],
                )
                if not result["authorized"]:
                    failures += 1
        if failures:
            raise ValidationError(
                "public build refused: one or more governed resources lack "
                f"action-specific authorization ({failures} blocked checks); "
                "restricted identifiers and payloads are intentionally omitted"
            )

    def active_review_decisions(
        self,
        target_uri: str,
        policy_uri: str | None = None,
        as_of: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return active, non-superseded decisions without collapsing perspectives."""
        reference_time = datetime.fromisoformat(
            (as_of or self.metadata["generated_at"]).replace("Z", "+00:00")
        )
        occurred = [
            row
            for row in self.review_events
            if datetime.fromisoformat(row["reviewed_at"].replace("Z", "+00:00"))
            <= reference_time
        ]
        temporally_active = [
            row
            for row in occurred
            if row["decision_status"] == "active"
            and (
                row["valid_until"] is None
                or datetime.fromisoformat(row["valid_until"].replace("Z", "+00:00"))
                >= reference_time
            )
        ]
        # Supersession and reinstatement are permanent event-history actions.
        # Expiry or withdrawal of the successor does not silently resurrect a
        # predecessor. Temporary suspension is separately time-bounded.
        permanent_state: dict[str, bool] = {}
        for row in sorted(
            occurred,
            key=lambda item: (
                datetime.fromisoformat(item["reviewed_at"].replace("Z", "+00:00")),
                item["uri"],
            ),
        ):
            if row.get("supersedes_decision_uri"):
                permanent_state[row["supersedes_decision_uri"]] = False
            if row.get("reinstates_decision_uri"):
                permanent_state[row["reinstates_decision_uri"]] = True
        suspended = {
            row["suspends_decision_uri"]
            for row in temporally_active
            if row.get("suspends_decision_uri")
        }
        return [
            row
            for row in temporally_active
            if row["target_assertion_uri"] == target_uri
            and permanent_state.get(row["decision_uri"], True)
            and row["decision_uri"] not in suspended
            and (
                policy_uri is None
                or policy_uri in row.get("projection_policy_uris", [])
            )
        ]

    def _target_subject_matter_uris(self, target_uri: str) -> set[str]:
        """Return exact URIs that a mandate may use to cover a review target."""
        uris = {target_uri}
        for row in self.classification_assertions:
            if row["uri"] == target_uri:
                return uris | {
                    row["target_uri"],
                    row["classification_uri"],
                    row["classification_scheme_uri"],
                }
        for row in self.concept_relation_assertions:
            if row["uri"] == target_uri:
                return (
                    uris
                    | {
                        row["subject_concept_uri"],
                        row["object_concept_uri"],
                        row["predicate_uri"],
                    }
                    | set(row["mapping_purpose_uris"])
                )
        for rows in (self.label_assertions, self.note_assertions):
            for row in rows:
                if row["uri"] == target_uri:
                    return uris | {row["concept_uri"], row["predicate_uri"]}
        for row in self.label_profiles:
            if row["uri"] == target_uri:
                return uris | {
                    row["label_resource_uri"],
                    row["source_label_assertion_uri"],
                }
        return uris

    def review_has_valid_authority(self, review: dict[str, Any]) -> bool:
        """Check exact mandate coverage at decision time.

        Authority is evaluated when the decision was made. A later prospective
        expiry or revocation does not rewrite history; a mandate explicitly
        marked with retroactive revocation does invalidate its earlier uses.
        """
        reviewed_at = datetime.fromisoformat(
            review["reviewed_at"].replace("Z", "+00:00")
        )
        authorities = {row["uri"]: row for row in self.authority_assignments}
        referenced = [
            authorities.get(uri) for uri in review.get("authority_assignment_uris", [])
        ]
        if not referenced or any(row is None for row in referenced):
            return False
        target_matters = self._target_subject_matter_uris(
            review["target_assertion_uri"]
        )
        authority_roles = {
            "community": {
                "community-reviewer",
                "cultural-authority",
                "delegated-representative",
            },
            "language": {"language-authority"},
            "organology": {"organology-reviewer"},
            "history": {"historical-reviewer"},
            "rights": {"rights-authority"},
            "technical": {"technical-reviewer"},
            "ethical": {"ethical-reviewer"},
        }
        valid: list[dict[str, Any]] = []
        for authority in referenced:
            assert authority is not None
            authority_from = datetime.fromisoformat(
                authority["valid_from"].replace("Z", "+00:00")
            )
            authority_until = (
                datetime.fromisoformat(authority["valid_until"].replace("Z", "+00:00"))
                if authority["valid_until"] is not None
                else None
            )
            if (
                authority["agent_uri"] != review["reviewer_agent_uri"]
                or reviewed_at < authority_from
                or (authority_until is not None and reviewed_at > authority_until)
                or authority.get("revocation_effect") == "retroactive"
                or authority["authority_role"]
                not in authority_roles[review["reviewer_authority"]]
                or review["validation_dimension"]
                not in authority.get("covered_validation_dimensions", [])
                or not set(review["applicability_scope_uris"]).issubset(
                    set(authority["applicability_scope_uris"])
                )
                or not target_matters.intersection(authority["subject_matter_uris"])
            ):
                continue
            valid.append(authority)
        if not valid:
            return False
        if review["reviewer_authority"] == "community":
            represented = set(review["represented_community_uris"])
            if not represented:
                return False
            return represented.issubset(
                {
                    row["represented_community_uri"]
                    for row in valid
                    if row["represented_community_uri"] is not None
                }
            )
        return not review["represented_community_uris"]

    def _review_scope_matches(
        self,
        review: dict[str, Any],
        *,
        context: dict[str, Any] | None,
        direct: bool,
    ) -> bool:
        scopes = {row["uri"]: row for row in self.applicability_scopes}
        if direct:
            return any(
                scopes[uri]["scope_mode"] == "context-independent"
                for uri in review["applicability_scope_uris"]
            )
        assert context is not None
        return any(
            self.scope_matches(uri, context) is True
            for uri in review["applicability_scope_uris"]
        )

    def _review_policy_evaluation(
        self,
        assertion: dict[str, Any],
        policy: dict[str, Any],
        *,
        context: dict[str, Any] | None,
        direct: bool,
    ) -> dict[str, Any]:
        decisions = [
            row
            for row in self.active_review_decisions(
                assertion["uri"],
                policy["uri"],
                None if context is None else context.get("as_of"),
            )
            if self.review_has_valid_authority(row)
        ]
        # Positive support must cover the requested scope. A veto need only
        # possibly overlap it: a local dispute defeats an unqualified claim,
        # and missing context cannot prove a dispute irrelevant.
        vetoes = sorted(
            {
                row["decision_uri"]
                for row in decisions
                for rule in policy["veto_rules"]
                if (
                    row["outcome"] in rule["outcomes"]
                    and row["reviewer_authority"] in rule["reviewer_authorities"]
                    and row["validation_dimension"] in rule["validation_dimensions"]
                    and (
                        direct
                        or any(
                            self._scope_matches(uri, context, missing_is_unknown=True)
                            is not False
                            for uri in row["applicability_scope_uris"]
                        )
                    )
                )
            }
        )
        supporting = [
            row
            for row in decisions
            if self._review_scope_matches(row, context=context, direct=direct)
        ]
        qualifying_reviewers: set[str] = set()
        requirements = []
        for requirement in policy["review_requirements"]:
            matching = [
                row
                for row in supporting
                if row["outcome"] in requirement["outcomes"]
                and row["reviewer_authority"] in requirement["reviewer_authorities"]
                and row["validation_dimension"] == requirement["validation_dimension"]
            ]
            reviewers = {row["reviewer_agent_uri"] for row in matching}
            requirements.append(
                {
                    "validation_dimension": requirement["validation_dimension"],
                    "minimum_independent_reviewers": requirement[
                        "minimum_independent_reviewers"
                    ],
                    "reviewer_agent_uris": sorted(reviewers),
                    "decision_uris": sorted(row["decision_uri"] for row in matching),
                    "satisfied": len(reviewers)
                    >= requirement["minimum_independent_reviewers"],
                }
            )
            qualifying_reviewers.update(reviewers)
        return {
            "active_authorized_decision_uris": sorted(
                row["decision_uri"] for row in decisions
            ),
            "veto_decision_uris": vetoes,
            "requirements": requirements,
            "independent_reviewer_count": len(qualifying_reviewers),
            "minimum_independent_reviewers": policy["minimum_independent_reviewers"],
            "satisfied": (
                not vetoes
                and all(row["satisfied"] for row in requirements)
                and len(qualifying_reviewers) >= policy["minimum_independent_reviewers"]
            ),
        }

    def explain_endorsement(
        self,
        assertion: dict[str, Any],
        context: dict[str, Any] | None = None,
        policy_uri: str = ENDORSED_POLICY,
    ) -> dict[str, Any]:
        """Explain the same decision used by RDF and SQLite projections.

        ``context=None`` requests a static direct projection; ``{}`` requests
        contextual evaluation with no supplied dimensions. This evaluates
        epistemic eligibility, never permission to disclose or reuse a claim.
        """
        policy = next(
            row for row in self.projection_policies if row["uri"] == policy_uri
        )
        direct = context is None
        reasons = []
        if direct and not policy["direct_assertion"]:
            reasons.append("policy-does-not-project-direct-assertions")
        if direct and assertion.get("predicate_uri") in MAPPING_RELATION_PREDICATES:
            reasons.append("mapping-purpose-requires-qualified-assertion")
        if policy_uri not in assertion["projection_policy_uris"]:
            reasons.append("claim-not-in-policy")
        if assertion["stance"] not in policy["eligible_stances"]:
            reasons.append("ineligible-stance")
        as_of = (context or {}).get("as_of", self.metadata["generated_at"])
        reference_time = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        for field, reason in (
            ("valid_from", "claim-not-yet-active"),
            ("valid_until", "claim-expired"),
        ):
            if assertion.get(field) is not None:
                boundary = datetime.fromisoformat(
                    assertion[field].replace("Z", "+00:00")
                )
                if (field == "valid_from" and reference_time < boundary) or (
                    field == "valid_until" and reference_time > boundary
                ):
                    reasons.append(reason)
        scopes = {row["uri"]: row for row in self.applicability_scopes}
        scope_results = [
            {
                "scope_uri": uri,
                "scope_mode": scopes[uri]["scope_mode"],
                "match": self.scope_matches(uri, context or {}),
            }
            for uri in assertion["applicability_scope_uris"]
        ]
        if direct:
            if policy["context_match_required"] and not any(
                row["scope_mode"] == "context-independent" for row in scope_results
            ):
                reasons.append("scope-not-context-independent")
        elif not any(row["match"] is True for row in scope_results):
            if not (
                any(row["match"] is None for row in scope_results)
                and policy["unknown_scope_behavior"] in {"include", "warn"}
            ):
                reasons.append("scope-not-matched")
        reviews = self._review_policy_evaluation(
            assertion, policy, context=context, direct=direct
        )
        if reviews["veto_decision_uris"]:
            reasons.append("active-review-veto")
        if any(not row["satisfied"] for row in reviews["requirements"]):
            reasons.append("required-review-missing")
        if (
            reviews["independent_reviewer_count"]
            < reviews["minimum_independent_reviewers"]
        ):
            reasons.append("insufficient-independent-reviewers")
        return {
            "assertion_uri": assertion["uri"],
            "policy_uri": policy_uri,
            "policy_version": policy["policy_version"],
            "mode": "direct" if direct else "contextual",
            "as_of": as_of,
            "eligible": not reasons,
            "reason_codes": reasons,
            "scopes": scope_results,
            "reviews": reviews,
        }

    def is_directly_endorsed(
        self, assertion: dict[str, Any], policy_uri: str = ENDORSED_POLICY
    ) -> bool:
        """Return whether a claim may be emitted as a static direct assertion.

        A context-qualified claim remains reified even after an accepting review:
        without a query context, only a scope explicitly declared independent of
        the registered context dimensions can safely be flattened to a direct
        triple. Source silence and other unresolved scope states do not qualify.
        Purpose-qualified SKOS mappings also remain qualified because flattening
        them would discard the operation for which their suitability was stated.
        """
        return self.explain_endorsement(assertion, policy_uri=policy_uri)["eligible"]

    def scope_matches(self, scope_uri: str, context: dict[str, Any]) -> bool | None:
        """Evaluate a registered scope against a query context.

        ``None`` is the intentional three-valued result for unknown scope.
        Specified dimensions are conjunctive; values within a dimension are
        alternatives. A missing required context dimension is not a match.
        The optional ``at`` context field is an ISO 8601 datetime.
        """
        return self._scope_matches(scope_uri, context, missing_is_unknown=False)

    def _scope_matches(
        self, scope_uri: str, context: dict[str, Any], *, missing_is_unknown: bool
    ) -> bool | None:
        scope = next(
            row for row in self.applicability_scopes if row["uri"] == scope_uri
        )
        if scope["scope_mode"] in {
            "source-silent",
            "not-yet-investigated",
            "known-unknown",
            "intentionally-unscoped",
        }:
            return None
        if scope["scope_mode"] in {"context-independent", "not-applicable"}:
            return True

        missing = False
        for field in (
            "community_uris",
            "place_uris",
            "period_uris",
            "usage_domain_uris",
            "playing_technique_uris",
            "instrument_configuration_uris",
            "language_variety_uris",
        ):
            allowed = set(scope[field])
            if not allowed:
                continue
            supplied = context.get(field, [])
            supplied_values = {supplied} if isinstance(supplied, str) else set(supplied)
            if not supplied_values:
                missing = True
            elif allowed.isdisjoint(supplied_values):
                return False

        if scope["temporal_start"] is not None or scope["temporal_end"] is not None:
            if not isinstance(context.get("at"), str):
                missing = True
            else:
                at = datetime.fromisoformat(context["at"].replace("Z", "+00:00"))
                if scope["temporal_start"] is not None and at < datetime.fromisoformat(
                    scope["temporal_start"].replace("Z", "+00:00")
                ):
                    return False
                if scope["temporal_end"] is not None and at > datetime.fromisoformat(
                    scope["temporal_end"].replace("Z", "+00:00")
                ):
                    return False
        if missing:
            return None if missing_is_unknown else False
        return True

    def claim_applies_in_context(
        self,
        assertion: dict[str, Any],
        context: dict[str, Any],
        policy_uri: str = CLAIMS_POLICY,
    ) -> bool:
        """Apply a named policy's scope and lifecycle rules to one claim."""
        policy = next(
            row for row in self.projection_policies if row["uri"] == policy_uri
        )
        if policy_uri not in assertion["projection_policy_uris"]:
            return False
        if assertion["stance"] not in policy["eligible_stances"]:
            return False
        reference_time = datetime.fromisoformat(
            context.get("as_of", self.metadata["generated_at"]).replace("Z", "+00:00")
        )
        if assertion.get(
            "valid_from"
        ) is not None and reference_time < datetime.fromisoformat(
            assertion["valid_from"].replace("Z", "+00:00")
        ):
            return False
        if assertion.get(
            "valid_until"
        ) is not None and reference_time > datetime.fromisoformat(
            assertion["valid_until"].replace("Z", "+00:00")
        ):
            return False
        results = [
            self.scope_matches(scope_uri, context)
            for scope_uri in assertion["applicability_scope_uris"]
        ]
        if any(result is True for result in results):
            return True
        return any(result is None for result in results) and policy[
            "unknown_scope_behavior"
        ] in {"include", "warn"}

    def is_endorsed_for_context(
        self,
        assertion: dict[str, Any],
        context: dict[str, Any],
        policy_uri: str = ENDORSED_POLICY,
    ) -> bool:
        """Return whether an accepted claim is usable in the supplied context."""
        return self.explain_endorsement(assertion, context, policy_uri)["eligible"]

    def community_validation_decisions(
        self, target_uri: str, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Return—not collapse—accepted community-validity decisions in context."""
        return [
            row
            for row in self.active_review_decisions(
                target_uri, as_of=context.get("as_of")
            )
            if row["reviewer_authority"] == "community"
            and row["validation_dimension"] == "community"
            and row["outcome"] == "accepted"
            and self.review_has_valid_authority(row)
            and any(
                self.scope_matches(scope_uri, context) is True
                for scope_uri in row["applicability_scope_uris"]
            )
        ]

    def validate(self, schema_dir: Path | None = None) -> dict[str, Any]:
        errors: list[str] = []

        expected_identity = {
            "name": "OMARO",
            "ontology_title": (
                "Ontology for Multiperspectivity, Assertions, and Review in Organology"
            ),
            "preferred_namespace_prefix": "omaro",
            "namespace_uri": OMARO,
            "ontology_uri": ONTOLOGY_URI,
            "ontology_version_iri": (
                f"{ONTOLOGY_URI}/{self.metadata.get('schema_version', '')}"
            ),
            "dataset_uri": (
                f"{DATASET_BASE_URI}/{self.metadata.get('dataset_version', '')}"
            ),
            "repository_uri": REPOSITORY_URI,
        }
        for field, expected in expected_identity.items():
            if self.metadata.get(field) != expected:
                errors.append(
                    f"metadata {field} must identify the canonical OMARO resource: "
                    f"{expected}"
                )

        def validate_interval(
            row: dict[str, Any], start_field: str, end_field: str, label: str
        ) -> None:
            start = row.get(start_field)
            end = row.get(end_field)
            if (
                start is not None
                and end is not None
                and datetime.fromisoformat(end.replace("Z", "+00:00"))
                < datetime.fromisoformat(start.replace("Z", "+00:00"))
            ):
                errors.append(f"{label} ends before it begins: {row.get('uri')}")

        concept_uris = [row.get("uri") for row in self.concepts]
        concept_set = set(concept_uris)
        duplicates = [uri for uri, count in Counter(concept_uris).items() if count > 1]
        if duplicates:
            errors.append(f"duplicate concept URIs: {duplicates[:5]}")

        agent_uris = [row.get("uri") for row in self.agents]
        agent_set = set(agent_uris)
        duplicate_agents = [
            uri for uri, count in Counter(agent_uris).items() if count > 1
        ]
        if duplicate_agents:
            errors.append(f"duplicate agent URIs: {duplicate_agents[:5]}")
        if not {MIMO_AGENT, PROJECT_AGENT}.issubset(agent_set):
            errors.append("required MIMO and project agents are missing")
        review_uri_set = {row.get("uri") for row in self.review_statuses}

        source_record_uris = [row.get("uri") for row in self.source_records]
        source_record_set = set(source_record_uris)
        source_records_by_uri = {row["uri"]: row for row in self.source_records}
        duplicate_sources = [
            uri for uri, count in Counter(source_record_uris).items() if count > 1
        ]
        if duplicate_sources:
            errors.append(f"duplicate source-record URIs: {duplicate_sources[:5]}")
        if not set(self.metadata.get("sources", [])).issubset(
            {row.get("resource_uri") for row in self.source_records}
        ):
            errors.append("metadata source resources are missing from source records")
        for row in self.source_records:
            if row.get("publisher_agent_uri") not in agent_set:
                errors.append(
                    "source record references unknown publisher agent: "
                    f"{row.get('publisher_agent_uri')}"
                )
            scheme_uri = row.get("scheme_uri")
            if scheme_uri in {HS_SCHEME, INSTRUMENT_SCHEME} and row.get(
                "retrieved_at"
            ) != self.metadata.get("source_retrieved_at"):
                errors.append(
                    f"source record has inconsistent retrieval time: {row.get('uri')}"
                )
            if scheme_uri in {HS_SCHEME, INSTRUMENT_SCHEME}:
                expected_uri = source_record_uri(
                    scheme_uri, self.metadata["source_retrieved_at"]
                )
                if row.get("uri") != expected_uri:
                    errors.append(f"non-canonical source-record URI: {row.get('uri')}")

        scheme_uris = [row.get("uri") for row in self.concept_schemes]
        scheme_set = set(scheme_uris)
        schemes_by_uri = {row["uri"]: row for row in self.concept_schemes}
        if len(scheme_uris) != len(scheme_set):
            errors.append("duplicate concept-scheme URIs")
        metadata_scheme_set = {
            row.get("uri") for row in self.metadata.get("schemes", [])
        }
        if not metadata_scheme_set.issubset(scheme_set):
            errors.append("metadata references an unregistered concept scheme")
        for row in self.source_records:
            if row.get("scheme_uri") not in scheme_set:
                errors.append(f"source record has unknown scheme: {row.get('uri')}")

        perspective_uris = [row.get("uri") for row in self.perspectives]
        perspective_set = set(perspective_uris)
        if len(perspective_uris) != len(perspective_set):
            errors.append("duplicate perspective URIs")
        for row in self.perspectives:
            if row.get("holder_agent_uri") not in agent_set:
                errors.append(f"perspective has unknown holder: {row.get('uri')}")
            validate_interval(row, "valid_from", "valid_until", "perspective")

        scope_uris = [row.get("uri") for row in self.applicability_scopes]
        scope_set = set(scope_uris)
        if len(scope_uris) != len(scope_set):
            errors.append("duplicate applicability-scope URIs")
        for row in self.applicability_scopes:
            if row.get("asserted_by_uri") not in agent_set:
                errors.append(f"scope has unknown asserting agent: {row.get('uri')}")
            if row.get("perspective_uri") not in perspective_set | {None}:
                errors.append(f"scope has unknown perspective: {row.get('uri')}")
            if row.get("source_record_uri") not in source_record_set | {None}:
                errors.append(f"scope has unknown source record: {row.get('uri')}")
            dimension_values = [
                row.get(field, [])
                for field in (
                    "community_uris",
                    "place_uris",
                    "period_uris",
                    "usage_domain_uris",
                    "playing_technique_uris",
                    "instrument_configuration_uris",
                    "language_variety_uris",
                )
            ]
            has_boundary = any(dimension_values) or any(
                row.get(field) is not None
                for field in ("temporal_start", "temporal_end")
            )
            if row.get("scope_mode") == "specified" and not has_boundary:
                errors.append(f"specified scope has no boundary: {row.get('uri')}")
            if row.get("scope_mode") != "specified" and has_boundary:
                errors.append(
                    f"non-specified scope declares a boundary: {row.get('uri')}"
                )
            validate_interval(
                row, "temporal_start", "temporal_end", "applicability scope"
            )

        authority_uris = [row.get("uri") for row in self.authority_assignments]
        authority_set = set(authority_uris)
        authority_by_uri = {row["uri"]: row for row in self.authority_assignments}
        perspective_by_uri = {row["uri"]: row for row in self.perspectives}
        if len(authority_uris) != len(authority_set):
            errors.append("duplicate authority-assignment URIs")
        for row in self.authority_assignments:
            if row.get("agent_uri") not in agent_set:
                errors.append(
                    f"authority assignment has unknown agent: {row.get('uri')}"
                )
            if row.get("conferred_by_agent_uri") not in agent_set:
                errors.append(
                    f"authority assignment has unknown conferring agent: {row.get('uri')}"
                )
            if not set(row.get("applicability_scope_uris", [])).issubset(scope_set):
                errors.append(
                    f"authority assignment has unknown scope: {row.get('uri')}"
                )
            validate_interval(row, "valid_from", "valid_until", "authority")
            is_community_role = row.get("authority_role") in {
                "community-reviewer",
                "cultural-authority",
                "delegated-representative",
            }
            if is_community_role != (row.get("represented_community_uri") is not None):
                errors.append(
                    "authority community representation/role mismatch: "
                    f"{row.get('uri')}"
                )
            if (
                row.get("represented_community_uri") is not None
                and row.get("conferred_by_agent_uri") == PROJECT_AGENT
            ):
                errors.append(
                    f"project software cannot confer community authority: {row.get('uri')}"
                )
            if row.get("status") == "revoked":
                if (
                    row.get("revocation_event_uri") is None
                    or row.get("revocation_effect")
                    not in {"prospective", "retroactive"}
                    or row.get("valid_until") is None
                ):
                    errors.append(
                        f"revoked authority lacks event, effect, or end: {row.get('uri')}"
                    )
            elif (
                row.get("revocation_event_uri") is not None
                or row.get("revocation_effect") is not None
            ):
                errors.append(
                    f"non-revoked authority declares revocation metadata: {row.get('uri')}"
                )
        for row in self.perspectives:
            if not set(row.get("authority_assignment_uris", [])).issubset(
                authority_set
            ):
                errors.append(f"perspective has unknown authority: {row.get('uri')}")

        protocol_uris = [row.get("uri") for row in self.protocol_applications]
        protocol_set = set(protocol_uris)
        protocol_by_uri = {row["uri"]: row for row in self.protocol_applications}
        if len(protocol_uris) != len(protocol_set):
            errors.append("duplicate protocol-application URIs")
        for row in self.protocol_applications:
            if row.get("issued_by_agent_uri") not in agent_set:
                errors.append(f"protocol has unknown issuing agent: {row.get('uri')}")
            if row.get("applied_by_agent_uri") not in agent_set:
                errors.append(f"protocol has unknown applying agent: {row.get('uri')}")
            if not set(row.get("authority_assignment_uris", [])).issubset(
                authority_set
            ):
                errors.append(f"protocol has unknown authority: {row.get('uri')}")
            if not set(row.get("applicability_scope_uris", [])).issubset(scope_set):
                errors.append(f"protocol has unknown scope: {row.get('uri')}")
            if row.get("source_record_uri") not in source_record_set | {None}:
                errors.append(f"protocol has unknown source record: {row.get('uri')}")
            predecessor = row.get("supersedes_uri")
            if predecessor is not None and predecessor not in protocol_set:
                errors.append(
                    f"protocol supersedes unknown application: {row.get('uri')}"
                )
            if predecessor == row.get("uri"):
                errors.append(f"protocol supersedes itself: {row.get('uri')}")
            if (
                row.get("resolution_status") == "verified"
                and row.get("protocol_integrity_sha256") is None
            ):
                errors.append(
                    f"verified protocol lacks an integrity digest: {row.get('uri')}"
                )
            if row.get(
                "resolution_status"
            ) == "verified" and not self.protocol_integrity_valid(row):
                errors.append(
                    f"verified protocol lacks a valid local digest or external attestation: {row.get('uri')}"
                )
            if row.get("enforcement_mode") == "machine-enforceable" and (
                row.get("resolution_status") != "verified"
                or row.get("protocol_integrity_sha256") is None
                or row.get("integrity_verification_method") != "local-sha256"
                or not self.protocol_integrity_valid(row)
            ):
                errors.append(
                    f"machine-enforceable protocol is not integrity-verified: {row.get('uri')}"
                )
            represented = set(row.get("represented_community_uris", []))
            application_time = datetime.fromisoformat(
                row["valid_from"].replace("Z", "+00:00")
            )
            eligible_authorities = [
                authority_by_uri[uri]
                for uri in row.get("authority_assignment_uris", [])
                if uri in authority_by_uri
                and authority_by_uri[uri].get("status") == "active"
                and authority_by_uri[uri].get("agent_uri")
                == row.get("applied_by_agent_uri")
                and set(row.get("applicability_scope_uris", [])).issubset(
                    set(authority_by_uri[uri].get("applicability_scope_uris", []))
                )
                and datetime.fromisoformat(
                    authority_by_uri[uri]["valid_from"].replace("Z", "+00:00")
                )
                <= application_time
                and (
                    authority_by_uri[uri].get("valid_until") is None
                    or application_time
                    <= datetime.fromisoformat(
                        authority_by_uri[uri]["valid_until"].replace("Z", "+00:00")
                    )
                )
            ]

            def protocol_authority_covers(community_uri: str) -> bool:
                subjects = {
                    subject
                    for authority in eligible_authorities
                    if authority.get("represented_community_uri") == community_uri
                    for subject in authority.get("subject_matter_uris", [])
                }
                return (
                    row["uri"] in subjects
                    or row["protocol_uri"] in subjects
                    or set(row["target_resource_uris"]).issubset(subjects)
                )

            if not all(protocol_authority_covers(uri) for uri in represented):
                errors.append(
                    "protocol lacks active applying-agent authority with full "
                    f"subject coverage for every represented community: {row.get('uri')}"
                )
            validate_interval(row, "valid_from", "valid_until", "protocol application")

        use_decision_uris = [row.get("uri") for row in self.use_decisions]
        use_decision_set = set(use_decision_uris)
        if len(use_decision_uris) != len(use_decision_set):
            errors.append("duplicate use-decision URIs")
        for row in self.use_decisions:
            if row.get("decided_by_agent_uri") not in agent_set:
                errors.append(
                    f"use decision has unknown deciding agent: {row.get('uri')}"
                )
            for field in (
                "legal_basis_assessed_by_agent_uri",
                "consent_assessed_by_agent_uri",
            ):
                if row.get(field) not in agent_set | {None}:
                    errors.append(f"use decision has unknown {field}: {row.get('uri')}")
            if not set(row.get("authority_assignment_uris", [])).issubset(
                authority_set
            ):
                errors.append(f"use decision has unknown authority: {row.get('uri')}")
            if not set(row.get("protocol_application_uris", [])).issubset(protocol_set):
                errors.append(f"use decision has unknown protocol: {row.get('uri')}")
            if not set(row.get("applicability_scope_uris", [])).issubset(scope_set):
                errors.append(f"use decision has unknown scope: {row.get('uri')}")
            validate_interval(row, "decided_at", "valid_until", "use decision")
            predecessor = row.get("supersedes_decision_uri")
            if predecessor is not None and predecessor not in use_decision_set:
                errors.append(
                    f"use decision supersedes unknown decision: {row.get('uri')}"
                )
            if predecessor == row.get("uri"):
                errors.append(f"use decision supersedes itself: {row.get('uri')}")
            if row.get("legal_basis_status") in {"documented", "not-required"} and (
                not row.get("legal_basis_uris")
                or row.get("legal_basis_assessed_by_agent_uri") is None
            ):
                errors.append(
                    f"use decision lacks an attributed legal-basis determination: {row.get('uri')}"
                )
            if row.get("consent_status") in {"documented", "not-required"} and (
                not row.get("consent_record_uris")
                or row.get("consent_assessed_by_agent_uri") is None
            ):
                errors.append(
                    f"use decision lacks an attributed consent determination: {row.get('uri')}"
                )
            decision_time = datetime.fromisoformat(
                row["decided_at"].replace("Z", "+00:00")
            )
            eligible_authorities = [
                authority_by_uri[uri]
                for uri in row.get("authority_assignment_uris", [])
                if uri in authority_by_uri
                and authority_by_uri[uri].get("status") == "active"
                and authority_by_uri[uri].get("agent_uri")
                == row.get("decided_by_agent_uri")
                and "rights"
                in authority_by_uri[uri].get("covered_validation_dimensions", [])
                and set(row.get("action_uris", [])).issubset(
                    set(authority_by_uri[uri].get("covered_action_uris", []))
                )
                and set(row.get("applicability_scope_uris", [])).issubset(
                    set(authority_by_uri[uri].get("applicability_scope_uris", []))
                )
                and datetime.fromisoformat(
                    authority_by_uri[uri]["valid_from"].replace("Z", "+00:00")
                )
                <= decision_time
                and (
                    authority_by_uri[uri].get("valid_until") is None
                    or decision_time
                    <= datetime.fromisoformat(
                        authority_by_uri[uri]["valid_until"].replace("Z", "+00:00")
                    )
                )
            ]

            def use_authority_covers(
                authorities: Iterable[dict[str, Any]],
            ) -> bool:
                subjects = {
                    subject
                    for authority in authorities
                    for subject in authority.get("subject_matter_uris", [])
                }
                covered_targets = set(subjects)
                for application_uri in row.get("protocol_application_uris", []):
                    protocol = protocol_by_uri.get(application_uri)
                    if protocol is not None and (
                        protocol["uri"] in subjects
                        or protocol["protocol_uri"] in subjects
                    ):
                        covered_targets.update(protocol["target_resource_uris"])
                return set(row.get("target_resource_uris", [])).issubset(
                    covered_targets
                )

            represented = set(row.get("represented_community_uris", []))
            authority_communities = {
                authority.get("represented_community_uri")
                for authority in eligible_authorities
                if authority.get("represented_community_uri") is not None
            }
            subject_coverage = all(
                use_authority_covers(
                    [
                        authority
                        for authority in eligible_authorities
                        if authority.get("represented_community_uri") == community
                    ]
                )
                for community in represented
            )
            if not represented:
                subject_coverage = use_authority_covers(eligible_authorities)
            if (
                not eligible_authorities
                or not represented.issubset(authority_communities)
                or not subject_coverage
            ):
                errors.append(
                    "use decision lacks active action-, scope-, and "
                    f"subject-covering authority: {row.get('uri')}"
                )
            if predecessor in use_decision_set:
                previous = next(
                    item for item in self.use_decisions if item["uri"] == predecessor
                )
                if datetime.fromisoformat(
                    previous["decided_at"].replace("Z", "+00:00")
                ) >= datetime.fromisoformat(
                    row["decided_at"].replace("Z", "+00:00")
                ) or not set(previous["target_resource_uris"]).intersection(
                    row["target_resource_uris"]
                ):
                    errors.append(
                        f"use-decision supersession has a different target or time order: {row.get('uri')}"
                    )

        target_uris = [row.get("uri") for row in self.organological_targets]
        target_set = set(target_uris)
        target_by_uri = {row["uri"]: row for row in self.organological_targets}
        if len(target_uris) != len(target_set):
            errors.append("duplicate organological-target URIs")
        for row in self.organological_targets:
            if row.get("source_record_uri") not in source_record_set | {None}:
                errors.append(
                    f"organological target has unknown source: {row.get('uri')}"
                )
            if row.get("perspective_uri") not in perspective_set | {None}:
                errors.append(
                    f"organological target has unknown perspective: {row.get('uri')}"
                )
            if not set(row.get("applicability_scope_uris", [])).issubset(scope_set):
                errors.append(
                    f"organological target has unknown scope: {row.get('uri')}"
                )
            if not set(row.get("protocol_application_uris", [])).issubset(protocol_set):
                errors.append(
                    f"organological target has unknown protocol: {row.get('uri')}"
                )
            if not set(row.get("authority_assignment_uris", [])).issubset(
                authority_set
            ):
                errors.append(
                    f"organological target has unknown authority: {row.get('uri')}"
                )
            for field in (
                "configuration_of_uri",
                "component_of_uri",
                "condition_state_of_uri",
                "performance_event_uri",
            ):
                if row.get(field) not in target_set | {None}:
                    errors.append(
                        f"organological target has unknown {field}: {row.get('uri')}"
                    )
                if row.get(field) == row.get("uri"):
                    errors.append(
                        f"organological target is its own {field}: {row.get('uri')}"
                    )
            if not set(row.get("has_component_uris", [])).issubset(target_set):
                errors.append(
                    f"organological target has unknown component: {row.get('uri')}"
                )
            if not set(row.get("has_functional_module_uris", [])).issubset(target_set):
                errors.append(
                    f"organological target has unknown module: {row.get('uri')}"
                )
            kind = row.get("target_kind")
            configuration_of = row.get("configuration_of_uri")
            component_of = row.get("component_of_uri")
            condition_of = row.get("condition_state_of_uri")
            performance_event = row.get("performance_event_uri")
            if configuration_of is not None and kind not in {
                "instrument-configuration",
                "sounding-realization",
            }:
                errors.append(
                    f"only configurations or soundings may use configuration_of_uri: {row.get('uri')}"
                )
            if component_of is not None and kind not in {
                "instrument-component",
                "functional-module",
                "instrument-aggregate",
            }:
                errors.append(f"target kind cannot be a component: {row.get('uri')}")
            if (component_of is None) != (row.get("component_role_uri") is None):
                errors.append(
                    f"component target must declare both parent and role: {row.get('uri')}"
                )
            if condition_of is not None and kind != "condition-state":
                errors.append(
                    f"only a condition state may use condition_state_of_uri: {row.get('uri')}"
                )
            if performance_event is not None and kind != "sounding-realization":
                errors.append(
                    f"only a sounding realization may link to a performance event: {row.get('uri')}"
                )
            if (
                performance_event in target_by_uri
                and target_by_uri[performance_event].get("target_kind")
                != "performance-event"
            ):
                errors.append(
                    f"performance_event_uri does not identify a performance event: {row.get('uri')}"
                )
            if row.get("actual_playing_technique_uris") and kind not in {
                "sounding-realization",
                "performance-event",
            }:
                errors.append(
                    f"actual technique is attached to a non-occurrence target: {row.get('uri')}"
                )
            if not set(row.get("has_functional_module_uris", [])).issubset(
                set(row.get("has_component_uris", []))
            ):
                errors.append(
                    f"functional modules are not also declared as components: {row.get('uri')}"
                )
            for child_uri in row.get("has_component_uris", []):
                child = target_by_uri.get(child_uri)
                if child is not None and child.get("component_of_uri") != row.get(
                    "uri"
                ):
                    errors.append(
                        f"component parent/inverse mismatch: {row.get('uri')} -> {child_uri}"
                    )
            for module_uri in row.get("has_functional_module_uris", []):
                module = target_by_uri.get(module_uri)
                if (
                    module is not None
                    and module.get("target_kind") != "functional-module"
                ):
                    errors.append(
                        f"functional-module link has a different target kind: {row.get('uri')} -> {module_uri}"
                    )
            if component_of in target_by_uri and row.get("uri") not in target_by_uri[
                component_of
            ].get("has_component_uris", []):
                errors.append(
                    f"component child/inverse mismatch: {row.get('uri')} -> {component_of}"
                )
            for concept_uri in row.get("realizes_instrument_concept_uris", []):
                if (
                    concept_uri not in concept_set
                    or self.concepts_by_uri[concept_uri]["kind"] != "instrument"
                ):
                    errors.append(
                        f"organological target realizes a non-instrument concept: {row.get('uri')}"
                    )
            validate_interval(row, "valid_from", "valid_until", "organological target")

        def relation_cycle(field: str) -> bool:
            for start in target_set:
                seen: set[str] = set()
                current: str | None = start
                while current in target_by_uri:
                    if current in seen:
                        return True
                    seen.add(current)
                    current = target_by_uri[current].get(field)
            return False

        for field in (
            "configuration_of_uri",
            "component_of_uri",
            "condition_state_of_uri",
        ):
            if relation_cycle(field):
                errors.append(
                    f"organological target relation contains a cycle: {field}"
                )

        target_neighbors: dict[str, set[str]] = defaultdict(set)
        for target_record in self.organological_targets:
            source = target_record["uri"]
            linked = {
                target_record.get("configuration_of_uri"),
                target_record.get("component_of_uri"),
                target_record.get("condition_state_of_uri"),
                target_record.get("performance_event_uri"),
                *target_record.get("has_component_uris", []),
                *target_record.get("has_functional_module_uris", []),
            } - {None}
            for destination in linked:
                target_neighbors[source].add(destination)
                target_neighbors[destination].add(source)

        def related_targets(first: str, second: str) -> bool:
            if first == second:
                return True
            frontier = [first]
            visited = {first}
            while frontier:
                current = frontier.pop()
                for neighbor in target_neighbors.get(current, set()):
                    if neighbor == second:
                        return True
                    if neighbor not in visited:
                        visited.add(neighbor)
                        frontier.append(neighbor)
            return False

        criterion_uris = [row.get("uri") for row in self.classification_criteria]
        criterion_set = set(criterion_uris)
        if len(criterion_uris) != len(criterion_set):
            errors.append("duplicate classification-criterion URIs")
        for row in self.classification_criteria:
            if row.get("asserted_by_uri") not in agent_set:
                errors.append(
                    f"criterion has unknown asserting agent: {row.get('uri')}"
                )
            if row.get("perspective_uri") not in perspective_set:
                errors.append(f"criterion has unknown perspective: {row.get('uri')}")
            if row.get("classification_scheme_uri") not in scheme_set:
                errors.append(f"criterion has unknown scheme: {row.get('uri')}")
            if row.get("source_record_uri") not in source_record_set | {None}:
                errors.append(f"criterion has unknown source: {row.get('uri')}")
            if not set(row.get("applicability_scope_uris", [])).issubset(scope_set):
                errors.append(f"criterion has unknown scope: {row.get('uri')}")
            if not set(row.get("authority_assignment_uris", [])).issubset(
                authority_set
            ):
                errors.append(f"criterion has unknown authority: {row.get('uri')}")
            if not set(row.get("protocol_application_uris", [])).issubset(protocol_set):
                errors.append(f"criterion has unknown protocol: {row.get('uri')}")
            for conclusion_uri in row.get("conclusion_classification_uris", []):
                conclusion = self.concepts_by_uri.get(conclusion_uri)
                if (
                    conclusion is None
                    or conclusion.get("kind") != "classification"
                    or conclusion.get("scheme_uri")
                    != row.get("classification_scheme_uri")
                ):
                    errors.append(
                        f"criterion conclusion is not a classification in its scheme: {row.get('uri')}"
                    )

        assessment_uris = [row.get("uri") for row in self.observation_assessments]
        assessment_set = set(assessment_uris)
        if len(assessment_uris) != len(assessment_set):
            errors.append("duplicate observation-assessment URIs")
        for row in self.observation_assessments:
            if row.get("assessment_agent_uri") not in agent_set:
                errors.append(f"assessment has unknown observer: {row.get('uri')}")
            if row.get("perspective_uri") not in perspective_set:
                errors.append(f"assessment has unknown perspective: {row.get('uri')}")
            if not set(row.get("applicability_scope_uris", [])).issubset(scope_set):
                errors.append(f"assessment has unknown scope: {row.get('uri')}")
            if not set(row.get("protocol_application_uris", [])).issubset(protocol_set):
                errors.append(f"assessment has unknown protocol: {row.get('uri')}")
            if not set(row.get("authority_assignment_uris", [])).issubset(
                authority_set
            ):
                errors.append(f"assessment has unknown authority: {row.get('uri')}")
            if row.get("source_record_uri") not in source_record_set | {None}:
                errors.append(f"assessment has unknown source: {row.get('uri')}")
            if row.get("feature_of_interest_uri") not in target_set | concept_set:
                errors.append(
                    f"assessment has unknown feature of interest: {row.get('uri')}"
                )
            if row.get("assessed_part_uri") not in target_set | {None}:
                errors.append(f"assessment has unknown observed part: {row.get('uri')}")
            if row.get("review_status_uri") not in review_uri_set:
                errors.append(f"assessment has unknown review status: {row.get('uri')}")
            if row.get("review_status_uri") != review_status_uri(
                row.get("review_status", "")
            ):
                errors.append(f"assessment review status mismatch: {row.get('uri')}")
            validate_interval(
                row, "phenomenon_start", "phenomenon_end", "observation assessment"
            )
            result = row.get("result")
            status = row.get("assessment_status")
            if status in {"detected", "not-detected"} and result is None:
                errors.append(
                    "detected or not-detected assessment lacks a result: "
                    f"{row.get('uri')}"
                )
            if status in {"not-observed", "not-applicable"} and result is not None:
                errors.append(
                    f"nonattempt assessment must not have a result: {row.get('uri')}"
                )
            if (
                isinstance(result, dict)
                and result.get("kind") == "range"
                and result["maximum_value"] < result["minimum_value"]
            ):
                errors.append(f"assessment range is inverted: {row.get('uri')}")

        expression_uris = [row.get("uri") for row in self.classification_expressions]
        expression_set = set(expression_uris)
        expression_by_uri = {
            row["uri"]: row
            for row in self.classification_expressions
            if isinstance(row.get("uri"), str)
        }
        classification_assertion_by_uri = {
            row["uri"]: row
            for row in self.classification_assertions
            if isinstance(row.get("uri"), str)
        }
        classification_assertion_id_set = set(classification_assertion_by_uri)
        if len(expression_uris) != len(expression_set):
            errors.append("duplicate classification-expression URIs")
        for row in self.classification_expressions:
            if row.get("perspective_uri") not in perspective_set:
                errors.append(f"expression has unknown perspective: {row.get('uri')}")
            if not set(row.get("applicability_scope_uris", [])).issubset(scope_set):
                errors.append(f"expression has unknown scope: {row.get('uri')}")
            if not set(row.get("authority_assignment_uris", [])).issubset(
                authority_set
            ):
                errors.append(f"expression has unknown authority: {row.get('uri')}")
            if not set(row.get("protocol_application_uris", [])).issubset(protocol_set):
                errors.append(f"expression has unknown protocol: {row.get('uri')}")
            if row.get("source_record_uri") not in source_record_set:
                errors.append(f"expression has unknown source record: {row.get('uri')}")
            source_concept = self.concepts_by_uri.get(row.get("source_concept_uri"))
            if row.get("source_concept_uri") is not None and (
                source_concept is None
                or source_concept.get("kind") != "classification"
                or source_concept.get("notation") != row.get("notation_literal")
            ):
                errors.append(
                    f"expression source concept/notation mismatch: {row.get('uri')}"
                )
            members = row.get("members", [])
            sequence = [member.get("sequence_index") for member in members]
            if sequence != list(range(1, len(members) + 1)):
                errors.append(
                    f"expression member sequence is not contiguous: {row.get('uri')}"
                )
            for member in members:
                classification_uri = member.get("classification_uri")
                classification = None
                if classification_uri is not None:
                    classification = self.concepts_by_uri.get(classification_uri)
                    if (
                        classification is None
                        or classification.get("kind") != "classification"
                    ):
                        errors.append(
                            f"expression member has unknown classification: {row.get('uri')}"
                        )
                member_assertion_uri = member.get("member_assertion_uri")
                if member_assertion_uri not in classification_assertion_id_set | {None}:
                    errors.append(
                        f"expression member has unknown assertion: {row.get('uri')}"
                    )
                member_target_uri = member.get("member_target_uri")
                if member_target_uri not in target_set | concept_set | {None}:
                    errors.append(
                        f"expression member has unknown target: {row.get('uri')}"
                    )
                if (
                    row.get("notation_grammar_uri") == HS_COMPOUND_GRAMMAR
                    and classification is not None
                    and isinstance(classification.get("notation"), str)
                ):
                    notation = classification["notation"]
                    member_notation = member.get("member_notation")
                    if member_notation != notation and not (
                        isinstance(member_notation, str)
                        and member_notation.startswith(f"{notation}-")
                    ):
                        errors.append(
                            "MIMO expression member notation does not match its "
                            f"classification: {row.get('uri')} member "
                            f"{member.get('sequence_index')}"
                        )
                referenced_assertion = classification_assertion_by_uri.get(
                    member_assertion_uri
                )
                if member_assertion_uri is not None and (
                    classification_uri is None or member_target_uri is None
                ):
                    errors.append(
                        "expression member assertion requires a classification "
                        f"and target: {row.get('uri')} member "
                        f"{member.get('sequence_index')}"
                    )
                if referenced_assertion is not None:
                    if classification_uri is not None and member_target_uri is not None:
                        if classification_uri != referenced_assertion.get(
                            "classification_uri"
                        ):
                            errors.append(
                                "expression member classification disagrees with "
                                f"its assertion: {row.get('uri')} member "
                                f"{member.get('sequence_index')}"
                            )
                        if member_target_uri != referenced_assertion.get("target_uri"):
                            errors.append(
                                "expression member target disagrees with its "
                                f"assertion: {row.get('uri')} member "
                                f"{member.get('sequence_index')}"
                            )
                    if referenced_assertion.get("perspective_uri") != row.get(
                        "perspective_uri"
                    ):
                        errors.append(
                            "expression and member assertion use different "
                            f"perspectives: {row.get('uri')} member "
                            f"{member.get('sequence_index')}"
                        )
                    if referenced_assertion.get("scheme_version_uri") != row.get(
                        "expression_scheme_version_uri"
                    ):
                        errors.append(
                            "expression and member assertion use different scheme "
                            f"versions: {row.get('uri')} member "
                            f"{member.get('sequence_index')}"
                        )
                    if not set(row.get("applicability_scope_uris", [])).issubset(
                        set(referenced_assertion.get("applicability_scope_uris", []))
                    ):
                        errors.append(
                            "expression scope is not covered by its member "
                            f"assertion: {row.get('uri')} member "
                            f"{member.get('sequence_index')}"
                        )
                registered_member_target = target_by_uri.get(member_target_uri)
                component_role_uri = member.get("component_role_uri")
                if (
                    registered_member_target is not None
                    and component_role_uri is not None
                    and registered_member_target.get("component_role_uri")
                    != component_role_uri
                ):
                    errors.append(
                        "expression member role disagrees with its registered "
                        f"target: {row.get('uri')} member "
                        f"{member.get('sequence_index')}"
                    )
            if (
                row.get("parse_status") == "expert-interpreted"
                and not any(
                    member.get("member_target_uri") is not None
                    or member.get("component_role_uri") is not None
                    or member.get("local_suffix_notation") is not None
                    for member in members
                )
                and row.get("shared_suffix_notation") is None
            ):
                errors.append(
                    f"interpreted expression contains no interpreted structure: {row.get('uri')}"
                )
        expected_expressions = classification_expressions_from_concepts(
            self.concepts, self.metadata
        )
        source_expressions = [
            row
            for row in self.classification_expressions
            if row.get("parse_status") == "tokenized-uninterpreted"
        ]
        if source_expressions != expected_expressions:
            errors.append(
                "classification expressions do not exactly match the deterministic source-notation parse"
            )

        policy_uris = [row.get("uri") for row in self.projection_policies]
        policy_set = set(policy_uris)
        if len(policy_uris) != len(policy_set):
            errors.append("duplicate projection-policy URIs")
        if not {SOURCE_POLICY, CLAIMS_POLICY, ENDORSED_POLICY}.issubset(policy_set):
            errors.append("required source, claims, and endorsed policies are missing")
        policies_by_uri = {row["uri"]: row for row in self.projection_policies}
        for expected in default_projection_policies():
            if policies_by_uri.get(expected["uri"]) != expected:
                errors.append(
                    f"required projection policy differs from canonical semantics: {expected['uri']}"
                )

        for row in self.concept_schemes:
            if row.get("publisher_agent_uri") not in agent_set:
                errors.append(f"concept scheme has unknown publisher: {row.get('uri')}")
            if row.get("perspective_uri") not in perspective_set:
                errors.append(
                    f"concept scheme has unknown perspective: {row.get('uri')}"
                )
            if row.get("source_record_uri") not in source_record_set | {None}:
                errors.append(f"concept scheme has unknown source: {row.get('uri')}")
            elif row.get("source_record_uri") is not None and source_records_by_uri[
                row["source_record_uri"]
            ]["scheme_uri"] != row.get("uri"):
                errors.append(
                    f"concept scheme source record belongs to another scheme: {row.get('uri')}"
                )

        review_codes = [row.get("code") for row in self.review_statuses]
        review_uris = [row.get("uri") for row in self.review_statuses]
        review_status_by_code = {
            row["code"]: row
            for row in self.review_statuses
            if isinstance(row.get("code"), str)
        }
        if len(review_codes) != len(set(review_codes)) or len(review_uris) != len(
            set(review_uris)
        ):
            errors.append("duplicate review-status code or URI")
        if set(review_codes) != set(REVIEW_STATUS_CODES):
            errors.append("review-status registry does not contain the required codes")
        for row in self.review_statuses:
            if row.get("uri") != review_status_uri(row.get("code", "")):
                errors.append(f"non-canonical review-status URI: {row.get('uri')}")

        if len(self.language_registries) != 1:
            errors.append("exactly one IANA language registry is required")
            registry_record: dict[str, Any] = {}
            language_registry = None
        else:
            registry_record = self.language_registries[0]
            registry_path = self.root.parent / registry_record["artifact_path"]
            if not registry_path.exists():
                errors.append(f"language registry artifact is missing: {registry_path}")
                language_registry = None
            else:
                language_registry = LanguageSubtagRegistry.load(registry_path)
                actual_hash = hashlib.sha256(registry_path.read_bytes()).hexdigest()
                if registry_record.get("sha256") != actual_hash:
                    errors.append("language registry artifact checksum mismatch")
                if registry_record.get("file_date") != language_registry.file_date:
                    errors.append("language registry file date mismatch")
                if registry_record.get("source_uri") != IANA_REGISTRY_SOURCE:
                    errors.append("language registry source URI mismatch")
                if registry_record.get("uri") != language_registry_uri(
                    language_registry.file_date
                ):
                    errors.append("non-canonical language registry URI")

        if len(self.script_registries) != 1:
            errors.append("exactly one Unicode Script registry is required")
            script_registry_record_value: dict[str, Any] = {}
            script_registry = None
        else:
            script_registry_record_value = self.script_registries[0]
            script_registry_path = (
                self.root.parent / script_registry_record_value["artifact_path"]
            )
            if not script_registry_path.exists():
                errors.append(
                    f"script registry artifact is missing: {script_registry_path}"
                )
                script_registry = None
            else:
                script_registry = UnicodeScriptRegistry.load(script_registry_path)
                actual_hash = hashlib.sha256(
                    script_registry_path.read_bytes()
                ).hexdigest()
                if script_registry_record_value.get("sha256") != actual_hash:
                    errors.append("script registry artifact checksum mismatch")
                if (
                    script_registry_record_value.get("unicode_version")
                    != UNICODE_SCRIPT_VERSION
                    or script_registry.unicode_version != UNICODE_SCRIPT_VERSION
                ):
                    errors.append("Unicode Script registry version mismatch")
                if tuple(script_registry_record_value.get("source_uris", [])) != (
                    UNICODE_SCRIPT_SOURCE_URIS
                ):
                    errors.append("Unicode Script registry sources mismatch")
                if script_registry_record_value.get("uri") != script_registry_uri(
                    script_registry.unicode_version
                ):
                    errors.append("non-canonical script registry URI")

        def validate_assertion_context(row: dict[str, Any], kind: str) -> None:
            if row.get("asserted_by_uri") not in agent_set:
                errors.append(
                    f"{kind} references unknown asserting agent: "
                    f"{row.get('asserted_by_uri')}"
                )
            if row.get("source_record_uri") not in source_record_set:
                errors.append(
                    f"{kind} references unknown source record: "
                    f"{row.get('source_record_uri')}"
                )
            status = row.get("review_status")
            status_record = review_status_by_code.get(status)
            if status_record is None:
                errors.append(f"{kind} has unknown review status: {status}")
            elif row.get("review_status_uri") != status_record["uri"]:
                errors.append(
                    f"{kind} review-status URI does not match code: {row.get('uri')}"
                )

        notation_keys = [
            (row.get("scheme_uri"), row.get("notation"))
            for row in self.concepts
            if row.get("notation")
        ]
        duplicate_notations = [
            key for key, count in Counter(notation_keys).items() if count > 1
        ]
        if duplicate_notations:
            errors.append(
                f"duplicate notation within scheme: {duplicate_notations[:5]}"
            )
        local_id_keys = [
            (row.get("scheme_uri"), row.get("local_id")) for row in self.concepts
        ]
        if len(local_id_keys) != len(set(local_id_keys)):
            errors.append("duplicate local identifier within concept scheme")
        for row in self.concepts:
            if row.get("scheme_uri") not in scheme_set:
                errors.append(f"concept references unknown scheme: {row.get('uri')}")

        preferred_keys: list[tuple[str, str]] = []
        label_keys: list[tuple[str, str, str, str]] = []
        for row in self.labels:
            uri = row.get("concept_uri")
            language = row.get("language")
            label = row.get("label")
            if uri not in concept_set:
                errors.append(f"label references unknown concept: {uri}")
            if not isinstance(language, str):
                errors.append(f"invalid language tag: {language!r} for {uri}")
            elif language_registry is not None:
                assessment = language_registry.assess(language)
                if not assessment.valid or assessment.canonical != language:
                    errors.append(
                        f"non-canonical compatibility language tag: {language!r} for {uri}"
                    )
            if not isinstance(label, str) or not label.strip():
                errors.append(f"empty label for {uri}")
            if row.get("label_type") == "preferred":
                preferred_keys.append((uri, language))
            label_keys.append((uri, language, row.get("label_type"), label))
        duplicate_labels = [
            key for key, count in Counter(label_keys).items() if count > 1
        ]
        if duplicate_labels:
            errors.append(f"duplicate label records: {duplicate_labels[:5]}")
        conflicting = [
            key for key, count in Counter(preferred_keys).items() if count > 1
        ]
        if conflicting:
            errors.append(f"multiple preferred labels per language: {conflicting[:5]}")

        label_resource_uris: list[str] = []
        projected_label_resources: set[tuple[str, str, str, str, str]] = set()
        assertion_by_label_resource = {
            row.get("label_resource_uri"): row for row in self.label_assertions
        }
        for row in self.label_resources:
            uri = row.get("uri")
            language = row.get("language_tag")
            literal = row.get("literal_form")
            label_resource_uris.append(uri)
            matching_assertion = assertion_by_label_resource.get(uri)
            if matching_assertion is not None:
                projected_label_resources.add(
                    (
                        matching_assertion["concept_uri"],
                        language,
                        matching_assertion["label_role"],
                        literal,
                        uri,
                    )
                )
            if row.get("normalized_form") != unicodedata.normalize(
                "NFC", literal if isinstance(literal, str) else ""
            ):
                errors.append(f"label resource has incorrect NFC form: {uri}")
            if row.get("language_registry_uri") != registry_record.get("uri"):
                errors.append(f"label resource has unknown language registry: {uri}")
            if language_registry is not None and isinstance(language, str):
                assessment = language_registry.assess(language)
                if not assessment.valid or assessment.canonical != language:
                    errors.append(f"label resource has non-canonical language: {uri}")
            if matching_assertion is not None:
                expected_uri = label_resource_uri(
                    matching_assertion["concept_uri"],
                    language,
                    matching_assertion["label_role"],
                    literal,
                    matching_assertion["source_record_uri"],
                    matching_assertion["asserted_by_uri"],
                    matching_assertion["source_uri"],
                )
                if uri != expected_uri:
                    errors.append(f"non-canonical label resource URI: {uri}")
        if len(label_resource_uris) != len(set(label_resource_uris)):
            errors.append("duplicate label-resource URIs")
        source_label_resources = {
            (
                row["concept_uri"],
                row["language"],
                row["label_type"],
                row["label"],
                label_resource_uri(
                    row["concept_uri"],
                    row["language"],
                    row["label_type"],
                    row["label"],
                    schemes_by_uri[
                        self.concepts_by_uri[row["concept_uri"]]["scheme_uri"]
                    ]["source_record_uri"],
                    MIMO_AGENT,
                    row["concept_uri"],
                ),
            )
            for row in self.labels
        }
        if projected_label_resources != source_label_resources:
            missing = sorted(source_label_resources - projected_label_resources)
            extra = sorted(projected_label_resources - source_label_resources)
            errors.append(
                "label resources do not exactly project source forms: "
                f"missing={missing[:3]}, extra={extra[:3]}"
            )
        label_resource_set = set(label_resource_uris)
        projection_statuses = _label_projection_statuses(self.labels)

        label_assertion_uris: list[str] = []
        projected_labels: set[tuple[str, str, str, str]] = set()
        for row in self.label_assertions:
            uri = row.get("uri")
            concept_uri = row.get("concept_uri")
            language = row.get("language_tag")
            role = row.get("label_role")
            literal = row.get("literal_form")
            label_assertion_uris.append(uri)
            projected_labels.add((concept_uri, language, role, literal))
            validate_assertion_context(row, "label assertion")
            submitted_language = row.get("submitted_language_tag")
            if language_registry is not None and isinstance(submitted_language, str):
                expected_language_fields = language_tag_fields(
                    submitted_language,
                    language_registry,
                    registry_record["uri"],
                )
                for field, expected_value in expected_language_fields.items():
                    if row.get(field) != expected_value:
                        errors.append(
                            f"label assertion language metadata mismatch: {uri}"
                        )
                        break
            if concept_uri not in concept_set:
                errors.append(
                    f"label assertion references unknown concept: {concept_uri}"
                )
                continue
            if row.get("predicate_uri") != LABEL_PREDICATES.get(role):
                errors.append(f"label assertion predicate/role mismatch: {uri}")
            occurrence_parts = (
                concept_uri,
                language,
                role,
                literal,
                row.get("source_record_uri"),
                row.get("asserted_by_uri"),
                row.get("source_uri"),
            )
            expected_label_resource = (
                label_resource_uri(*occurrence_parts)
                if all(isinstance(value, str) for value in occurrence_parts)
                else None
            )
            if row.get("label_resource_uri") != expected_label_resource:
                errors.append(f"label assertion resource mismatch: {uri}")
            if row.get("label_resource_uri") not in label_resource_set:
                errors.append(f"label assertion references unknown resource: {uri}")
            expected_projection_status = projection_statuses.get(
                (concept_uri, language, role, literal)
            )
            if row.get("skos_projection_status") != expected_projection_status:
                errors.append(f"label assertion projection status mismatch: {uri}")
            if row.get("normalized_form") != unicodedata.normalize(
                "NFC", literal if isinstance(literal, str) else ""
            ):
                errors.append(f"label assertion has incorrect NFC form: {uri}")
            if row.get("source_uri") != concept_uri:
                errors.append(f"label assertion source URI mismatch: {uri}")
            if row.get("assertion_origin") != "source-asserted":
                errors.append(f"label assertion has unsupported origin: {uri}")
            concept_scheme_uri = self.concepts_by_uri[concept_uri]["scheme_uri"]
            assertion_source = source_records_by_uri.get(row.get("source_record_uri"))
            expected_source = schemes_by_uri[concept_scheme_uri]["source_record_uri"]
            source_mismatch = (
                assertion_source is None
                or assertion_source["scheme_uri"] != concept_scheme_uri
                or (
                    concept_scheme_uri in {HS_SCHEME, INSTRUMENT_SCHEME}
                    and row.get("source_record_uri") != expected_source
                )
            )
            if source_mismatch:
                errors.append(f"label assertion source record mismatch: {uri}")
            if all(isinstance(value, str) for value in occurrence_parts):
                expected_uri = assertion_uri("label", *occurrence_parts)
                if uri != expected_uri:
                    errors.append(f"non-canonical label assertion URI: {uri}")
        duplicate_label_assertion_uris = [
            uri for uri, count in Counter(label_assertion_uris).items() if count > 1
        ]
        if duplicate_label_assertion_uris:
            errors.append(
                f"duplicate label assertion URIs: {duplicate_label_assertion_uris[:5]}"
            )
        source_labels = set(label_keys)
        if projected_labels != source_labels:
            missing = sorted(source_labels - projected_labels)
            extra = sorted(projected_labels - source_labels)
            errors.append(
                "label assertions do not exactly project source labels: "
                f"missing={missing[:3]}, extra={extra[:3]}"
            )

        profile_uris: list[str] = []
        profiled_resources: list[str] = []
        assertion_by_uri = {row["uri"]: row for row in self.label_assertions}
        for row in self.label_profiles:
            uri = row.get("uri")
            resource_uri = row.get("label_resource_uri")
            assertion = assertion_by_uri.get(row.get("source_label_assertion_uri"))
            profile_uris.append(uri)
            profiled_resources.append(resource_uri)
            validate_assertion_context(row, "label profile")
            if resource_uri not in label_resource_set:
                errors.append(f"label profile references unknown resource: {uri}")
                continue
            if assertion is None or assertion.get("label_resource_uri") != resource_uri:
                errors.append(f"label profile assertion/resource mismatch: {uri}")
                continue
            expected_uri = assertion_uri("label-profile", resource_uri)
            if uri != expected_uri:
                errors.append(f"non-canonical label profile URI: {uri}")
            if row.get("language_tag") != assertion["language_tag"]:
                errors.append(f"label profile language mismatch: {uri}")
            if language_registry is not None:
                expected_components = language_registry.components(
                    assertion["language_tag"]
                )
                if any(
                    row.get(field) != value
                    for field, value in expected_components.items()
                ):
                    errors.append(f"label profile BCP 47 components mismatch: {uri}")
            if script_registry is not None:
                expected_scripts, expected_common = script_registry.observe(
                    assertion["normalized_form"]
                )
                if (
                    row.get("observed_script_codes") != expected_scripts
                    or row.get("has_common_or_inherited_characters") != expected_common
                ):
                    errors.append(f"label profile script observation mismatch: {uri}")
            if row.get("script_registry_uri") != script_registry_record_value.get(
                "uri"
            ):
                errors.append(f"label profile script registry mismatch: {uri}")
            if row.get("assertion_origin") != "source-derived":
                errors.append(f"label profile has unsupported origin: {uri}")
            if row.get("asserted_by_uri") != PROJECT_AGENT:
                errors.append(f"label profile has unexpected agent: {uri}")
            if row.get("term_roles"):
                invalid_roles = set(row["term_roles"]) - set(TERM_ROLE_CODES)
                if invalid_roles:
                    errors.append(f"label profile has invalid term roles: {uri}")
        if len(profile_uris) != len(set(profile_uris)):
            errors.append("duplicate label-profile URIs")
        if len(profiled_resources) != len(set(profiled_resources)):
            errors.append("multiple label profiles for one resource")
        if set(profiled_resources) != label_resource_set:
            errors.append("label profiles do not exactly cover label resources")

        note_assertion_uris: list[str] = []
        projected_notes: set[tuple[str, str, str, str]] = set()
        for row in self.note_assertions:
            uri = row.get("uri")
            concept_uri = row.get("concept_uri")
            predicate = row.get("predicate_uri")
            language = row.get("language_tag")
            literal = row.get("literal_form")
            note_assertion_uris.append(uri)
            projected_notes.add((concept_uri, predicate, language, literal))
            validate_assertion_context(row, "note assertion")
            submitted_language = row.get("submitted_language_tag")
            if language_registry is not None and isinstance(submitted_language, str):
                expected_language_fields = language_tag_fields(
                    submitted_language,
                    language_registry,
                    registry_record["uri"],
                )
                for field, expected_value in expected_language_fields.items():
                    if row.get(field) != expected_value:
                        errors.append(
                            f"note assertion language metadata mismatch: {uri}"
                        )
                        break
            if concept_uri not in concept_set:
                errors.append(
                    f"note assertion references unknown concept: {concept_uri}"
                )
                continue
            if predicate not in NOTE_PREDICATES:
                errors.append(f"note assertion has unsupported predicate: {predicate}")
            if row.get("normalized_form") != unicodedata.normalize(
                "NFC", literal if isinstance(literal, str) else ""
            ):
                errors.append(f"note assertion has incorrect NFC form: {uri}")
            if row.get("source_uri") != concept_uri:
                errors.append(f"note assertion source URI mismatch: {uri}")
            if row.get("assertion_origin") != "source-asserted":
                errors.append(f"note assertion has unsupported origin: {uri}")
            concept_scheme_uri = self.concepts_by_uri[concept_uri]["scheme_uri"]
            assertion_source = source_records_by_uri.get(row.get("source_record_uri"))
            expected_source = schemes_by_uri[concept_scheme_uri]["source_record_uri"]
            source_mismatch = (
                assertion_source is None
                or assertion_source["scheme_uri"] != concept_scheme_uri
                or (
                    concept_scheme_uri in {HS_SCHEME, INSTRUMENT_SCHEME}
                    and row.get("source_record_uri") != expected_source
                )
            )
            if source_mismatch:
                errors.append(f"note assertion source record mismatch: {uri}")
            occurrence_parts = (
                concept_uri,
                predicate,
                language,
                literal,
                row.get("source_record_uri"),
                row.get("asserted_by_uri"),
                row.get("source_uri"),
            )
            if all(isinstance(value, str) for value in occurrence_parts):
                expected_uri = assertion_uri("note", *occurrence_parts)
                if uri != expected_uri:
                    errors.append(f"non-canonical note assertion URI: {uri}")
        duplicate_note_assertion_uris = [
            uri for uri, count in Counter(note_assertion_uris).items() if count > 1
        ]
        if duplicate_note_assertion_uris:
            errors.append(
                f"duplicate note assertion URIs: {duplicate_note_assertion_uris[:5]}"
            )
        source_notes = {
            (row["uri"], f"{SKOS}definition", "en", row["definition"])
            for row in self.concepts
            if row.get("definition")
        }
        if projected_notes != source_notes:
            missing = sorted(source_notes - projected_notes)
            extra = sorted(projected_notes - source_notes)
            errors.append(
                "note assertions do not exactly project source notes: "
                f"missing={missing[:3]}, extra={extra[:3]}"
            )

        relation_keys: list[tuple[str, str, str]] = []
        for row in self.source_relations:
            subject = row.get("subject_uri")
            predicate = row.get("predicate_uri")
            obj = row.get("object_uri")
            relation_keys.append((subject, predicate, obj))
            if subject not in concept_set:
                errors.append(f"relation has unknown subject: {subject}")
            if obj not in concept_set:
                errors.append(f"relation has unknown object: {obj}")
            if predicate not in {BROADER, EXACT_MATCH}:
                errors.append(f"unsupported authoritative relation: {predicate}")
            if subject == obj:
                errors.append(f"self-referential relation: {(subject, predicate, obj)}")
            if subject in concept_set and obj in concept_set:
                subject_kind = self.concepts_by_uri[subject]["kind"]
                object_kind = self.concepts_by_uri[obj]["kind"]
                if predicate == BROADER and subject_kind != object_kind:
                    errors.append(f"cross-scheme broader relation: {(subject, obj)}")
                if predicate == EXACT_MATCH and (subject_kind, object_kind) != (
                    "classification",
                    "instrument",
                ):
                    errors.append(
                        f"invalid classification/instrument mapping: {(subject, obj)}"
                    )
        duplicate_relations = [
            key for key, count in Counter(relation_keys).items() if count > 1
        ]
        if duplicate_relations:
            errors.append(f"duplicate source relations: {duplicate_relations[:5]}")

        assertion_uris: list[str] = []
        assertion_pairs: list[tuple[str, str]] = []
        source_exact_matches = {
            (
                row["subject_uri"],
                row["predicate_uri"],
                row["object_uri"],
                row["source_uri"],
            )
            for row in self.source_relations
            if row["predicate_uri"] == EXACT_MATCH
        }
        projected_source_matches: set[tuple[str, str, str, str]] = set()
        assignment_uris: list[str] = []
        source_expression_by_concept = {
            row["source_concept_uri"]: row["uri"]
            for row in self.classification_expressions
            if row.get("source_concept_uri") is not None
        }
        criterion_by_uri = {row["uri"]: row for row in self.classification_criteria}
        assessment_by_uri = {row["uri"]: row for row in self.observation_assessments}

        def assessment_relevant_to_target(
            assessment: dict[str, Any], target_uri: str
        ) -> bool:
            assessed = {
                assessment.get("feature_of_interest_uri"),
                assessment.get("assessed_part_uri"),
            } - {None}
            if target_uri in assessed:
                return True
            if target_uri in concept_set:
                return any(
                    target_uri
                    in target_by_uri.get(assessed_uri, {}).get(
                        "realizes_instrument_concept_uris", []
                    )
                    for assessed_uri in assessed
                )
            return any(
                assessed_uri in target_set and related_targets(target_uri, assessed_uri)
                for assessed_uri in assessed
            )

        for row in self.classification_assertions:
            classification_assertion_id = row.get("uri")
            assignment_id = row.get("assignment_uri")
            assignment_uris.append(assignment_id)
            target_uri = row.get("target_uri")
            classification_uri = row.get("classification_uri")
            registered_target = target_by_uri.get(target_uri)
            source_predicate = row.get("source_predicate_uri")
            source_uri = row.get("source_uri")
            assertion_uris.append(classification_assertion_id)
            assertion_pairs.append((target_uri, classification_uri))
            is_mimo_mapping = (
                row.get("assertion_origin") == "source-derived"
                and row.get("classification_scheme_uri") == HS_SCHEME
                and row.get("perspective_uri") == MIMO_PERSPECTIVE
            )
            if is_mimo_mapping:
                projected_source_matches.add(
                    (
                        classification_uri,
                        source_predicate,
                        target_uri,
                        source_uri,
                    )
                )
            if row.get("assigned_by_uri") not in agent_set:
                errors.append(
                    "classification assertion has unknown assigning agent: "
                    f"{classification_assertion_id}"
                )
            if assignment_id == classification_assertion_id:
                errors.append(
                    f"classification assertion and assignment share an identity: {classification_assertion_id}"
                )
            if not set(row.get("criteria_uris", [])).issubset(criterion_set):
                errors.append(
                    f"classification assertion has unknown criterion: {classification_assertion_id}"
                )
            if not set(row.get("assessment_uris", [])).issubset(assessment_set):
                errors.append(
                    f"classification assertion has unknown assessment: {classification_assertion_id}"
                )
            linked_criteria = [
                criterion_by_uri[uri]
                for uri in row.get("criteria_uris", [])
                if uri in criterion_by_uri
            ]
            linked_assessments = [
                assessment_by_uri[uri]
                for uri in row.get("assessment_uris", [])
                if uri in assessment_by_uri
            ]
            for criterion in linked_criteria:
                if criterion["classification_scheme_uri"] != row.get(
                    "classification_scheme_uri"
                ):
                    errors.append(
                        f"classification criterion uses another scheme: {classification_assertion_id}"
                    )
                if (
                    criterion.get("scheme_version_uri") is not None
                    and row.get("scheme_version_uri") is not None
                    and criterion["scheme_version_uri"] != row["scheme_version_uri"]
                ):
                    errors.append(
                        f"classification criterion uses another scheme version: {classification_assertion_id}"
                    )
                conclusions = set(criterion.get("conclusion_classification_uris", []))
                if conclusions and row.get("classification_uri") not in conclusions:
                    errors.append(
                        f"classification is not a declared criterion conclusion: {classification_assertion_id}"
                    )
                if not set(row.get("applicability_scope_uris", [])).issubset(
                    set(criterion.get("applicability_scope_uris", []))
                ):
                    errors.append(
                        f"classification scope is not covered by its criterion: {classification_assertion_id}"
                    )
                criterion_logic = criterion.get("inference_logic_uri")
                if criterion_logic is not None and criterion_logic != row.get(
                    "inference_logic_uri"
                ):
                    errors.append(
                        f"classification and criterion use different inference logic: {classification_assertion_id}"
                    )
            if (
                row.get("inference_logic_uri") is not None
                and linked_criteria
                and row["inference_logic_uri"]
                not in {
                    criterion.get("inference_logic_uri")
                    for criterion in linked_criteria
                }
            ):
                errors.append(
                    f"classification inference logic is not declared by a criterion: {classification_assertion_id}"
                )
            for assessment in linked_assessments:
                matches_criterion = any(
                    (
                        not criterion.get("observable_property_uris")
                        or assessment["assessed_property_uri"]
                        in criterion["observable_property_uris"]
                    )
                    and (
                        not criterion.get("procedure_uris")
                        or assessment["assessment_procedure_uri"]
                        in criterion["procedure_uris"]
                    )
                    for criterion in linked_criteria
                )
                if linked_criteria and not matches_criterion:
                    errors.append(
                        f"classification assessment matches no referenced criterion: {classification_assertion_id}"
                    )
                if not assessment_relevant_to_target(assessment, target_uri):
                    errors.append(
                        f"classification assessment is unrelated to its target: {classification_assertion_id}"
                    )
            for criterion in linked_criteria:
                if (
                    linked_assessments
                    and (
                        criterion.get("observable_property_uris")
                        or criterion.get("procedure_uris")
                    )
                    and not any(
                        (
                            not criterion.get("observable_property_uris")
                            or assessment["assessed_property_uri"]
                            in criterion["observable_property_uris"]
                        )
                        and (
                            not criterion.get("procedure_uris")
                            or assessment["assessment_procedure_uri"]
                            in criterion["procedure_uris"]
                        )
                        for assessment in linked_assessments
                    )
                ):
                    errors.append(
                        f"classification criterion has no matching assessment: {classification_assertion_id}"
                    )
            if row.get("classification_expression_uri") not in expression_set | {None}:
                errors.append(
                    f"classification assertion has unknown expression: {classification_assertion_id}"
                )
            expression = expression_by_uri.get(row.get("classification_expression_uri"))
            if expression is not None:
                if row.get("perspective_uri") != expression.get("perspective_uri"):
                    errors.append(
                        "classification assertion and expression use different "
                        f"perspectives: {classification_assertion_id}"
                    )
                if row.get("scheme_version_uri") != expression.get(
                    "expression_scheme_version_uri"
                ):
                    errors.append(
                        "classification assertion and expression use different "
                        f"scheme versions: {classification_assertion_id}"
                    )
                if not set(row.get("applicability_scope_uris", [])).issubset(
                    set(expression.get("applicability_scope_uris", []))
                ):
                    errors.append(
                        "classification assertion scope is not covered by its "
                        f"expression: {classification_assertion_id}"
                    )
                if expression.get("source_concept_uri") is not None and row.get(
                    "classification_uri"
                ) != expression.get("source_concept_uri"):
                    errors.append(
                        "classification assertion class differs from its "
                        f"expression source concept: {classification_assertion_id}"
                    )
                for member in expression.get("members", []):
                    member_classification_uri = member.get("classification_uri")
                    member_classification = self.concepts_by_uri.get(
                        member_classification_uri
                    )
                    if (
                        member_classification_uri is not None
                        and member_classification is not None
                        and member_classification.get("scheme_uri")
                        != row.get("classification_scheme_uri")
                    ):
                        errors.append(
                            "classification expression member belongs to another "
                            f"scheme: {classification_assertion_id} member "
                            f"{member.get('sequence_index')}"
                        )
                    member_target_uri = member.get("member_target_uri")
                    if (
                        registered_target is not None
                        and member_target_uri in target_by_uri
                        and not related_targets(target_uri, member_target_uri)
                    ):
                        errors.append(
                            "classification expression member target is unrelated "
                            f"to its whole assertion target: "
                            f"{classification_assertion_id} member "
                            f"{member.get('sequence_index')}"
                        )
            if row.get("generated_by_uri") not in agent_set | {None}:
                errors.append(
                    "classification assertion has unknown generating agent: "
                    f"{classification_assertion_id}"
                )
            if row.get("perspective_uri") not in perspective_set:
                errors.append(
                    "classification assertion has unknown perspective: "
                    f"{classification_assertion_id}"
                )
            if row.get("classification_scheme_uri") not in scheme_set:
                errors.append(
                    "classification assertion has unknown scheme: "
                    f"{classification_assertion_id}"
                )
            if row.get("source_record_uri") not in source_record_set:
                errors.append(
                    "classification assertion has unknown source record: "
                    f"{classification_assertion_id}"
                )
            if not set(row.get("applicability_scope_uris", [])).issubset(scope_set):
                errors.append(
                    "classification assertion has unknown scope: "
                    f"{classification_assertion_id}"
                )
            if not set(row.get("projection_policy_uris", [])).issubset(policy_set):
                errors.append(
                    "classification assertion has unknown projection policy: "
                    f"{classification_assertion_id}"
                )
            if not set(row.get("authority_assignment_uris", [])).issubset(
                authority_set
            ):
                errors.append(
                    "classification assertion has unknown authority assignment: "
                    f"{classification_assertion_id}"
                )
            validate_interval(
                row, "valid_from", "valid_until", "classification assertion"
            )
            target_type = row.get("target_type")
            if registered_target is not None:
                expected_kind = TARGET_KIND_BY_TARGET_TYPE.get(target_type)
                actual_kind = registered_target.get("target_kind")
                if expected_kind != actual_kind:
                    errors.append(
                        "classification assertion target type/kind mismatch: "
                        f"{classification_assertion_id} declares {target_type} but "
                        f"{target_uri} is {actual_kind}"
                    )
            elif target_type != "instrument-concept":
                errors.append(
                    "classification assertion references unknown organological "
                    f"target: {target_uri}"
                )
            if target_type == "instrument-concept" and target_uri not in concept_set:
                errors.append(
                    f"classification assertion references unknown instrument: {target_uri}"
                )
            if classification_uri not in concept_set:
                errors.append(
                    "classification assertion references unknown classification: "
                    f"{classification_uri}"
                )
            if (
                target_type == "instrument-concept"
                and target_uri in concept_set
                and self.concepts_by_uri[target_uri]["kind"] != "instrument"
            ):
                errors.append(
                    f"classification assertion subject is not an instrument: {target_uri}"
                )
            if classification_uri in concept_set and self.concepts_by_uri[
                classification_uri
            ]["scheme_uri"] != row.get("classification_scheme_uri"):
                errors.append(
                    "classification assertion object/scheme mismatch: "
                    f"{classification_uri}"
                )
            if row.get("predicate_uri") != CLASSIFIED_AS:
                errors.append(
                    f"unsupported classification predicate: {row.get('predicate_uri')}"
                )
            if is_mimo_mapping and source_predicate != EXACT_MATCH:
                errors.append(
                    f"unsupported source mapping predicate: {source_predicate}"
                )
            if is_mimo_mapping:
                if (
                    row.get("assigned_by_uri") != MIMO_AGENT
                    or row.get("generated_by_uri") != PROJECT_AGENT
                    or row.get("stance") != "source-asserted"
                    or row.get("applicability_scope_uris") != [SOURCE_SILENT_SCOPE]
                    or set(row.get("projection_policy_uris", []))
                    != {SOURCE_POLICY, CLAIMS_POLICY}
                    or row.get("authority_assignment_uris") != []
                    or row.get("criteria_uris") != []
                    or row.get("assessment_uris") != []
                    or row.get("inference_logic_uri") is not None
                    or row.get("classification_expression_uri")
                    != source_expression_by_concept.get(classification_uri)
                ):
                    errors.append(
                        "MIMO classification projection changes source-claim semantics: "
                        f"{classification_assertion_id}"
                    )
                expected_uri = (
                    classification_assertion_uri(
                        classification_uri,
                        target_uri,
                        source_record_uri=row["source_record_uri"],
                        assigned_by_uri=row["assigned_by_uri"],
                        perspective_uri=row["perspective_uri"],
                        classification_method_uri=row["classification_method_uri"],
                        source_uri=row["source_uri"],
                    )
                    if isinstance(classification_uri, str)
                    and isinstance(target_uri, str)
                    else None
                )
                if classification_assertion_id != expected_uri:
                    errors.append(
                        "non-canonical source classification assertion URI: "
                        f"{classification_assertion_id}"
                    )
                elif assignment_id != classification_assignment_uri(expected_uri):
                    errors.append(
                        "non-canonical source classification assignment URI: "
                        f"{assignment_id}"
                    )
            perspective = perspective_by_uri.get(row.get("perspective_uri"))
            requires_community_authority = row.get(
                "assertion_origin"
            ) == "community-asserted" or (
                perspective is not None
                and perspective.get("perspective_type") == "community"
            )
            if requires_community_authority:
                referenced = [
                    authority_by_uri[uri]
                    for uri in row.get("authority_assignment_uris", [])
                    if uri in authority_by_uri
                ]
                required_communities = set(
                    perspective.get("represented_community_uris", [])
                    if perspective is not None
                    else []
                )
                assertion_time = datetime.fromisoformat(
                    (row.get("valid_from") or self.metadata["generated_at"]).replace(
                        "Z", "+00:00"
                    )
                )
                matters = {
                    classification_assertion_id,
                    target_uri,
                    classification_uri,
                    row.get("classification_scheme_uri"),
                }
                covered_communities = {
                    authority["represented_community_uri"]
                    for authority in referenced
                    if authority.get("agent_uri") == row.get("assigned_by_uri")
                    and authority.get("status") == "active"
                    and authority.get("authority_role")
                    in {
                        "community-reviewer",
                        "cultural-authority",
                        "delegated-representative",
                    }
                    and authority.get("represented_community_uri") is not None
                    and authority.get("uri")
                    in (perspective or {}).get("authority_assignment_uris", [])
                    and set(row.get("applicability_scope_uris", [])).issubset(
                        set(authority.get("applicability_scope_uris", []))
                    )
                    and matters.intersection(authority.get("subject_matter_uris", []))
                    and assertion_time
                    >= datetime.fromisoformat(
                        authority["valid_from"].replace("Z", "+00:00")
                    )
                    and (
                        authority.get("valid_until") is None
                        or assertion_time
                        <= datetime.fromisoformat(
                            authority["valid_until"].replace("Z", "+00:00")
                        )
                    )
                    and authority.get("revocation_effect") != "retroactive"
                }
                if not required_communities or not required_communities.issubset(
                    covered_communities
                ):
                    errors.append(
                        "community classification lacks matching active authority: "
                        f"{classification_assertion_id}"
                    )
        duplicate_assertion_uris = [
            uri for uri, count in Counter(assertion_uris).items() if count > 1
        ]
        if duplicate_assertion_uris:
            errors.append(
                f"duplicate classification assertion URIs: {duplicate_assertion_uris[:5]}"
            )
        duplicate_assignment_uris = [
            uri for uri, count in Counter(assignment_uris).items() if count > 1
        ]
        if duplicate_assignment_uris:
            errors.append(
                f"duplicate classification assignment URIs: {duplicate_assignment_uris[:5]}"
            )
        if set(assertion_uris).intersection(assignment_uris):
            errors.append("classification assertion and assignment URI spaces overlap")
        if projected_source_matches != source_exact_matches:
            missing = sorted(source_exact_matches - projected_source_matches)
            extra = sorted(projected_source_matches - source_exact_matches)
            errors.append(
                "classification assertions do not exactly project MIMO source mappings: "
                f"missing={missing[:3]}, extra={extra[:3]}"
            )

        relation_assertion_uris: list[str] = []
        for row in self.concept_relation_assertions:
            uri = row.get("uri")
            relation_assertion_uris.append(uri)
            predicate_uri = row.get("predicate_uri")
            mapping_purpose_uris = row.get("mapping_purpose_uris", [])
            if len(mapping_purpose_uris) != len(set(mapping_purpose_uris)):
                errors.append(f"relation assertion repeats a mapping purpose: {uri}")
            if predicate_uri in MAPPING_RELATION_PREDICATES:
                if not mapping_purpose_uris:
                    errors.append(
                        f"mapping relation assertion has no declared purpose: {uri}"
                    )
            elif predicate_uri in STRUCTURAL_RELATION_PREDICATES:
                if mapping_purpose_uris:
                    errors.append(
                        "structural relation assertion declares a mapping purpose: "
                        f"{uri}"
                    )
            else:
                errors.append(
                    f"relation assertion has unsupported predicate: {predicate_uri}"
                )
            if row.get("subject_concept_uri") not in concept_set:
                errors.append(f"relation assertion has unknown subject: {uri}")
            if row.get("object_concept_uri") not in concept_set:
                errors.append(f"relation assertion has unknown object: {uri}")
            if row.get("assigned_by_uri") not in agent_set:
                errors.append(f"relation assertion has unknown assigning agent: {uri}")
            if row.get("generated_by_uri") not in agent_set | {None}:
                errors.append(f"relation assertion has unknown generating agent: {uri}")
            if row.get("perspective_uri") not in perspective_set:
                errors.append(f"relation assertion has unknown perspective: {uri}")
            if row.get("source_record_uri") not in source_record_set:
                errors.append(f"relation assertion has unknown source record: {uri}")
            if not set(row.get("applicability_scope_uris", [])).issubset(scope_set):
                errors.append(f"relation assertion has unknown scope: {uri}")
            if not set(row.get("projection_policy_uris", [])).issubset(policy_set):
                errors.append(
                    f"relation assertion has unknown projection policy: {uri}"
                )
            if not set(row.get("authority_assignment_uris", [])).issubset(
                authority_set
            ):
                errors.append(f"relation assertion has unknown authority: {uri}")
            validate_interval(
                row, "valid_from", "valid_until", "concept relation assertion"
            )
        if len(relation_assertion_uris) != len(set(relation_assertion_uris)):
            errors.append("duplicate concept-relation assertion URIs")

        expected_rules = sorted(default_quality_rules(), key=lambda row: row["uri"])
        if self.quality_rules != expected_rules:
            errors.append("quality-rule registry differs from the canonical rules")
        rule_by_uri = {row.get("uri"): row for row in self.quality_rules}
        target_assertion_uris = set(
            label_assertion_uris
            + note_assertion_uris
            + assertion_uris
            + relation_assertion_uris
            + profile_uris
        )
        expected_findings = linguistic_quality_findings(
            self.label_assertions,
            self.note_assertions,
            self.concepts_by_uri,
            self.metadata["generated_at"],
        )
        if self.quality_findings != sorted(
            expected_findings, key=lambda row: row["uri"]
        ):
            errors.append(
                "quality findings do not exactly match the deterministic audit"
            )
        finding_uris: list[str] = []
        for row in self.quality_findings:
            finding_uris.append(row.get("uri"))
            if row.get("rule_uri") not in rule_by_uri:
                errors.append(f"quality finding has unknown rule: {row.get('uri')}")
            if row.get("target_assertion_uri") not in target_assertion_uris:
                errors.append(
                    f"quality finding has unknown target assertion: {row.get('uri')}"
                )
            if row.get("detected_by_uri") != PROJECT_AGENT:
                errors.append(
                    f"quality finding has unexpected detector: {row.get('uri')}"
                )
            if row.get("review_effect") != "none":
                errors.append(
                    f"automated quality finding changes review state: {row.get('uri')}"
                )
            expected_uri = assertion_uri(
                "finding", row.get("rule_code", ""), row.get("target_assertion_uri", "")
            )
            if row.get("uri") != expected_uri:
                errors.append(f"non-canonical quality-finding URI: {row.get('uri')}")
        if len(finding_uris) != len(set(finding_uris)):
            errors.append("duplicate quality-finding URIs")

        review_event_uris: list[str] = []
        for row in self.review_events:
            review_event_uris.append(row.get("uri"))
            if row.get("decision_uri") != review_decision_uri(row.get("uri", "")):
                errors.append(f"non-canonical review-decision URI: {row.get('uri')}")
            if row.get("target_assertion_uri") not in target_assertion_uris:
                errors.append(
                    f"review event has unknown target assertion: {row.get('uri')}"
                )
            if row.get("reviewer_agent_uri") not in agent_set:
                errors.append(f"review event has unknown reviewer: {row.get('uri')}")
            if row.get("perspective_uri") not in perspective_set:
                errors.append(f"review event has unknown perspective: {row.get('uri')}")
            if not set(row.get("applicability_scope_uris", [])).issubset(scope_set):
                errors.append(f"review event has unknown scope: {row.get('uri')}")
            if not set(row.get("projection_policy_uris", [])).issubset(policy_set):
                errors.append(
                    f"review event has unknown projection policy: {row.get('uri')}"
                )
            authority_uris_for_review = set(row.get("authority_assignment_uris", []))
            if not authority_uris_for_review.issubset(authority_set):
                errors.append(f"review event has unknown authority: {row.get('uri')}")
            if not self.review_has_valid_authority(row):
                errors.append(
                    f"review authority does not cover agent, target, scope, dimension, or time: {row.get('uri')}"
                )
            if row.get("reviewer_authority") == "community":
                perspective = perspective_by_uri.get(row.get("perspective_uri"), {})
                if (
                    row.get("review_method") != "community"
                    or not authority_uris_for_review.issubset(
                        set(perspective.get("authority_assignment_uris", []))
                    )
                    or not set(row.get("represented_community_uris", [])).issubset(
                        set(perspective.get("represented_community_uris", []))
                    )
                ):
                    errors.append(
                        f"community review authority does not cover decision: {row.get('uri')}"
                    )
            if (
                row.get("validation_dimension") == "community"
                and row.get("reviewer_authority") != "community"
            ):
                errors.append(
                    f"community-validity decision lacks community authority: {row.get('uri')}"
                )
            lifecycle_links = [
                row.get(field)
                for field in (
                    "supersedes_decision_uri",
                    "suspends_decision_uri",
                    "reinstates_decision_uri",
                )
                if row.get(field) is not None
            ]
            if row.get("decision_uri") in lifecycle_links:
                errors.append(f"review event targets itself: {row.get('uri')}")
            if len(lifecycle_links) > 1:
                errors.append(
                    f"review event declares several lifecycle actions: {row.get('uri')}"
                )
            if (
                row.get("suspends_decision_uri") is not None
                and row.get("valid_until") is None
            ):
                errors.append(
                    f"temporary review suspension has no end: {row.get('uri')}"
                )
            validate_interval(row, "reviewed_at", "valid_until", "review event")
        if len(review_event_uris) != len(set(review_event_uris)):
            errors.append("duplicate review-event URIs")
        review_decision_uris = [row.get("decision_uri") for row in self.review_events]
        if len(review_decision_uris) != len(set(review_decision_uris)):
            errors.append("duplicate review-decision URIs")
        review_decision_set = set(review_decision_uris)
        occurrence_entities = set(
            assertion_uris
            + relation_assertion_uris
            + label_assertion_uris
            + note_assertion_uris
            + review_decision_uris
        )
        occurrence_activities = set(assignment_uris + review_event_uris)
        if occurrence_entities.intersection(occurrence_activities):
            errors.append(
                "assertion/decision entity and assignment/review activity URI spaces overlap"
            )
        for row in self.review_events:
            for field in (
                "supersedes_decision_uri",
                "suspends_decision_uri",
                "reinstates_decision_uri",
            ):
                predecessor_uri = row.get(field)
                if predecessor_uri is None:
                    continue
                if predecessor_uri not in review_decision_set:
                    errors.append(
                        f"review lifecycle action targets unknown decision: {row.get('uri')}"
                    )
                    continue
                predecessor = next(
                    item
                    for item in self.review_events
                    if item["decision_uri"] == predecessor_uri
                )
                if predecessor["target_assertion_uri"] != row[
                    "target_assertion_uri"
                ] or datetime.fromisoformat(
                    predecessor["reviewed_at"].replace("Z", "+00:00")
                ) >= datetime.fromisoformat(row["reviewed_at"].replace("Z", "+00:00")):
                    errors.append(
                        f"review lifecycle action has a different target or time order: {row.get('uri')}"
                    )

        broader_parents: dict[str, list[str]] = defaultdict(list)
        for subject, predicate, obj in relation_keys:
            if predicate == BROADER and subject in concept_set and obj in concept_set:
                broader_parents[subject].append(obj)
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(uri: str) -> bool:
            if uri in visiting:
                return True
            if uri in visited:
                return False
            visiting.add(uri)
            cyclic = any(visit(parent) for parent in broader_parents[uri])
            visiting.remove(uri)
            visited.add(uri)
            return cyclic

        if any(visit(uri) for uri in concept_set):
            errors.append("skos:broader hierarchy contains a cycle")

        for row in self.concepts:
            if row.get(
                "resolution_status"
            ) == "resolved" and not self.labels_by_concept.get(row["uri"]):
                errors.append(f"resolved concept has no label: {row['uri']}")

        if schema_dir:
            schemas = {
                "agent": json.loads((schema_dir / "agent.schema.json").read_text()),
                "source_record": json.loads(
                    (schema_dir / "source_record.schema.json").read_text()
                ),
                "concept_scheme": json.loads(
                    (schema_dir / "concept_scheme.schema.json").read_text()
                ),
                "perspective": json.loads(
                    (schema_dir / "perspective.schema.json").read_text()
                ),
                "applicability_scope": json.loads(
                    (schema_dir / "applicability_scope.schema.json").read_text()
                ),
                "authority_assignment": json.loads(
                    (schema_dir / "authority_assignment.schema.json").read_text()
                ),
                "projection_policy": json.loads(
                    (schema_dir / "projection_policy.schema.json").read_text()
                ),
                "review_status": json.loads(
                    (schema_dir / "review_status.schema.json").read_text()
                ),
                "language_registry": json.loads(
                    (schema_dir / "language_registry.schema.json").read_text()
                ),
                "script_registry": json.loads(
                    (schema_dir / "script_registry.schema.json").read_text()
                ),
                "quality_rule": json.loads(
                    (schema_dir / "quality_rule.schema.json").read_text()
                ),
                "quality_finding": json.loads(
                    (schema_dir / "quality_finding.schema.json").read_text()
                ),
                "review_event": json.loads(
                    (schema_dir / "review_event.schema.json").read_text()
                ),
                "protocol_application": json.loads(
                    (schema_dir / "protocol_application.schema.json").read_text()
                ),
                "use_decision": json.loads(
                    (schema_dir / "use_decision.schema.json").read_text()
                ),
                "organological_target": json.loads(
                    (schema_dir / "organological_target.schema.json").read_text()
                ),
                "classification_criterion": json.loads(
                    (schema_dir / "classification_criterion.schema.json").read_text()
                ),
                "observation_assessment": json.loads(
                    (schema_dir / "observation_assessment.schema.json").read_text()
                ),
                "classification_expression": json.loads(
                    (schema_dir / "classification_expression.schema.json").read_text()
                ),
                "concept": json.loads((schema_dir / "concept.schema.json").read_text()),
                "label": json.loads((schema_dir / "label.schema.json").read_text()),
                "label_resource": json.loads(
                    (schema_dir / "label_resource.schema.json").read_text()
                ),
                "label_profile": json.loads(
                    (schema_dir / "label_profile.schema.json").read_text()
                ),
                "label_assertion": json.loads(
                    (schema_dir / "label_assertion.schema.json").read_text()
                ),
                "note_assertion": json.loads(
                    (schema_dir / "note_assertion.schema.json").read_text()
                ),
                "source_relation": json.loads(
                    (schema_dir / "source_relation.schema.json").read_text()
                ),
                "concept_relation_assertion": json.loads(
                    (schema_dir / "concept_relation_assertion.schema.json").read_text()
                ),
                "classification_assertion": json.loads(
                    (schema_dir / "classification_assertion.schema.json").read_text()
                ),
                "metadata": json.loads(
                    (schema_dir / "metadata.schema.json").read_text()
                ),
            }
            for name, rows in (
                ("agent", self.agents),
                ("source_record", self.source_records),
                ("concept_scheme", self.concept_schemes),
                ("perspective", self.perspectives),
                ("applicability_scope", self.applicability_scopes),
                ("authority_assignment", self.authority_assignments),
                ("projection_policy", self.projection_policies),
                ("review_status", self.review_statuses),
                ("language_registry", self.language_registries),
                ("script_registry", self.script_registries),
                ("quality_rule", self.quality_rules),
                ("quality_finding", self.quality_findings),
                ("review_event", self.review_events),
                ("protocol_application", self.protocol_applications),
                ("use_decision", self.use_decisions),
                ("organological_target", self.organological_targets),
                ("classification_criterion", self.classification_criteria),
                ("observation_assessment", self.observation_assessments),
                ("classification_expression", self.classification_expressions),
                ("concept", self.concepts),
                ("label", self.labels),
                ("label_resource", self.label_resources),
                ("label_profile", self.label_profiles),
                ("label_assertion", self.label_assertions),
                ("note_assertion", self.note_assertions),
                ("source_relation", self.source_relations),
                ("concept_relation_assertion", self.concept_relation_assertions),
                ("classification_assertion", self.classification_assertions),
                ("metadata", [self.metadata]),
            ):
                validator = Draft202012Validator(
                    schemas[name], format_checker=FormatChecker()
                )
                for index, row in enumerate(rows):
                    for error in validator.iter_errors(row):
                        errors.append(f"{name}[{index}] schema: {error.message}")

        languages = Counter(
            row["language"] for row in self.labels if row["label_type"] == "preferred"
        )
        summary = {
            "concepts": len(self.concepts),
            "classifications": sum(
                row["kind"] == "classification" for row in self.concepts
            ),
            "instruments": sum(
                row["kind"] == "instrument" and row["resolution_status"] == "resolved"
                for row in self.concepts
            ),
            "unresolved_stubs": sum(
                row["resolution_status"] == "unresolved" for row in self.concepts
            ),
            "labels": len(self.labels),
            "label_resources": len(self.label_resources),
            "label_profiles": len(self.label_profiles),
            "label_assertions": len(self.label_assertions),
            "note_assertions": len(self.note_assertions),
            "agents": len(self.agents),
            "source_records": len(self.source_records),
            "concept_schemes": len(self.concept_schemes),
            "perspectives": len(self.perspectives),
            "applicability_scopes": len(self.applicability_scopes),
            "authority_assignments": len(self.authority_assignments),
            "projection_policies": len(self.projection_policies),
            "review_statuses": len(self.review_statuses),
            "language_registries": len(self.language_registries),
            "script_registries": len(self.script_registries),
            "quality_rules": len(self.quality_rules),
            "quality_findings": len(self.quality_findings),
            "review_events": len(self.review_events),
            "protocol_applications": len(self.protocol_applications),
            "use_decisions": len(self.use_decisions),
            "organological_targets": len(self.organological_targets),
            "classification_criteria": len(self.classification_criteria),
            "observation_assessments": len(self.observation_assessments),
            "classification_expressions": len(self.classification_expressions),
            "source_relations": len(self.source_relations),
            "concept_relation_assertions": len(self.concept_relation_assertions),
            "classification_assertions": len(self.classification_assertions),
            "languages": dict(sorted(languages.items())),
        }
        expected_counts = {
            "concepts": summary["concepts"],
            "classifications": summary["classifications"],
            "resolved_instruments": summary["instruments"],
            "unresolved_stubs": summary["unresolved_stubs"],
            "labels": summary["labels"],
            "label_resources": summary["label_resources"],
            "label_profiles": summary["label_profiles"],
            "label_assertions": summary["label_assertions"],
            "note_assertions": summary["note_assertions"],
            "agents": summary["agents"],
            "source_records": summary["source_records"],
            "concept_schemes": summary["concept_schemes"],
            "perspectives": summary["perspectives"],
            "applicability_scopes": summary["applicability_scopes"],
            "authority_assignments": summary["authority_assignments"],
            "projection_policies": summary["projection_policies"],
            "review_statuses": summary["review_statuses"],
            "language_registries": summary["language_registries"],
            "script_registries": summary["script_registries"],
            "quality_rules": summary["quality_rules"],
            "quality_findings": summary["quality_findings"],
            "review_events": summary["review_events"],
            "protocol_applications": summary["protocol_applications"],
            "use_decisions": summary["use_decisions"],
            "organological_targets": summary["organological_targets"],
            "classification_criteria": summary["classification_criteria"],
            "observation_assessments": summary["observation_assessments"],
            "classification_expressions": summary["classification_expressions"],
            "source_relations": summary["source_relations"],
            "concept_relation_assertions": summary["concept_relation_assertions"],
            "classification_assertions": summary["classification_assertions"],
        }
        if self.metadata.get("counts") != expected_counts:
            errors.append("canonical metadata counts do not match records")
        if self.metadata.get("language_coverage") != summary["languages"]:
            errors.append(
                "canonical metadata language coverage does not match preferred labels"
            )
        unresolved = sorted(
            row["uri"]
            for row in self.concepts
            if row["resolution_status"] == "unresolved"
        )
        if self.metadata.get("unresolved_references") != unresolved:
            errors.append(
                "canonical metadata unresolved references do not match records"
            )
        checksums = {
            name: hashlib.sha256((self.root / name).read_bytes()).hexdigest()
            for name in (
                "agents.jsonl",
                "source_records.jsonl",
                "concept_schemes.jsonl",
                "perspectives.jsonl",
                "applicability_scopes.jsonl",
                "authority_assignments.jsonl",
                "projection_policies.jsonl",
                "review_statuses.jsonl",
                "language_registries.jsonl",
                "script_registries.jsonl",
                "quality_rules.jsonl",
                "quality_findings.jsonl",
                "review_events.jsonl",
                "protocol_applications.jsonl",
                "use_decisions.jsonl",
                "organological_targets.jsonl",
                "classification_criteria.jsonl",
                "observation_assessments.jsonl",
                "classification_expressions.jsonl",
                "concepts.jsonl",
                "labels.jsonl",
                "label_resources.jsonl",
                "label_profiles.jsonl",
                "label_assertions.jsonl",
                "note_assertions.jsonl",
                "source_relations.jsonl",
                "concept_relation_assertions.jsonl",
                "classification_assertions.jsonl",
            )
        }
        if self.metadata.get("canonical_checksums") != checksums:
            errors.append("canonical metadata checksums do not match canonical files")
        if errors:
            raise ValidationError("\n".join(errors[:50]))
        return summary
