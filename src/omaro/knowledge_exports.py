"""Structured OKF navigation and self-contained retrieval exports."""

from __future__ import annotations

import json
import hashlib
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import yaml

from .model import (
    BROADER,
    HS_SCHEME,
    INSTRUMENT_SCHEME,
    REPOSITORY_URI,
    Dataset,
    ValidationError,
    canonical_json,
)

OKF_VERSION = "0.2"
OKF_PROFILE_UPDATED_AT = "2026-07-29T12:45:28Z"
OKF_VERIFIER = "process:okf-projection-validation"
INTERNAL_LINK_RE = re.compile(r"\[[^]]+\]\((/[^)#]+)(?:#[^)]*)?\)")
MARKDOWN_LINK_RE = re.compile(r"\[[^]]+\]\(([^)]+)\)")
FOOTNOTE_RE = re.compile(r"\[\^([^]]+)\]")
ACTOR_RE = re.compile(r"^(?:human:[^\s]+|process:[^\s]+|[^/\s]+/[^/\s]+)$")
DATE_HEADING_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})$", re.MULTILINE)
CANONICAL_ASSERTIONS_URL = (
    f"{REPOSITORY_URI}/blob/main/data/canonical/classification_assertions.jsonl"
)
CANONICAL_LABEL_ASSERTIONS_URL = (
    f"{REPOSITORY_URI}/blob/main/data/canonical/label_assertions.jsonl"
)
CANONICAL_LABEL_RESOURCES_URL = (
    f"{REPOSITORY_URI}/blob/main/data/canonical/label_resources.jsonl"
)
CANONICAL_LABEL_PROFILES_URL = (
    f"{REPOSITORY_URI}/blob/main/data/canonical/label_profiles.jsonl"
)
CANONICAL_NOTE_ASSERTIONS_URL = (
    f"{REPOSITORY_URI}/blob/main/data/canonical/note_assertions.jsonl"
)
CANONICAL_QUALITY_FINDINGS_URL = (
    f"{REPOSITORY_URI}/blob/main/data/canonical/quality_findings.jsonl"
)


def _yaml_scalar(value: Any) -> str:
    """Serialize the frontmatter subset as JSON, which is valid YAML."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _frontmatter(**fields: Any) -> str:
    rows = ["---"]
    rows.extend(
        f"{key}: {_yaml_scalar(value)}"
        for key, value in fields.items()
        if value is not None
    )
    rows.extend(("---", ""))
    return "\n".join(rows)


def _parse_iso_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"OKF {field} must be a non-empty ISO 8601 datetime")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError(f"OKF {field} is not an ISO 8601 datetime") from error
    if parsed.tzinfo is None:
        raise ValidationError(f"OKF {field} must include a timezone")
    return parsed


def _profile_generated_at(dataset: Dataset) -> str:
    candidates = (
        dataset.metadata["generated_at"],
        OKF_PROFILE_UPDATED_AT,
    )
    return max(candidates, key=lambda value: _parse_iso_datetime(value, "generated.at"))


def _generator_actor(dataset: Dataset) -> str:
    return f"omaro/{dataset.metadata['dataset_version']}"


def _okf_v02_fields(
    dataset: Dataset,
    *,
    sources: list[dict[str, Any]],
    machine_verified: bool,
) -> dict[str, Any]:
    generated_at = _profile_generated_at(dataset)
    fields: dict[str, Any] = {
        "status": "stable",
        "generated": {
            "by": _generator_actor(dataset),
            "at": generated_at,
        },
    }
    if machine_verified:
        fields["verified"] = {"by": OKF_VERIFIER, "at": generated_at}
    fields["sources"] = sources
    return fields


def _concept_sources(dataset: Dataset, concept: dict[str, Any]) -> list[dict[str, Any]]:
    scheme = next(
        row for row in dataset.concept_schemes if row["uri"] == concept["scheme_uri"]
    )
    return [
        {
            "id": "concept-record",
            "resource": concept["uri"],
            "title": f"{scheme['label']} concept record",
            "author": scheme["publisher_agent_uri"],
        },
        {
            "id": "classification-assertions",
            "resource": CANONICAL_ASSERTIONS_URL,
            "title": "Canonical qualified classification assertions",
            "author": _generator_actor(dataset),
        },
        {
            "id": "label-assertions",
            "resource": CANONICAL_LABEL_ASSERTIONS_URL,
            "title": "Qualified label assertions",
            "author": _generator_actor(dataset),
        },
        {
            "id": "label-resources",
            "resource": CANONICAL_LABEL_RESOURCES_URL,
            "title": "Assertion-scoped SKOS-XL label resources",
            "author": _generator_actor(dataset),
        },
        {
            "id": "label-profiles",
            "resource": CANONICAL_LABEL_PROFILES_URL,
            "title": "Conservative label linguistic profiles",
            "author": _generator_actor(dataset),
        },
        {
            "id": "note-assertions",
            "resource": CANONICAL_NOTE_ASSERTIONS_URL,
            "title": "Qualified note assertions",
            "author": _generator_actor(dataset),
        },
        {
            "id": "quality-findings",
            "resource": CANONICAL_QUALITY_FINDINGS_URL,
            "title": "Automated quality findings with no review effect",
            "author": _generator_actor(dataset),
        },
    ]


def _dataset_sources(dataset: Dataset) -> list[dict[str, Any]]:
    titles = (
        "MIMO Hornbostel–Sachs vocabulary API",
        "MIMO instrument-keyword vocabulary API",
    )
    sources = [
        {
            "id": f"mimo-source-{index}",
            "resource": resource,
            "title": titles[index - 1] if index <= len(titles) else "MIMO source",
            "author": "team:mimo",
        }
        for index, resource in enumerate(dataset.metadata["sources"], start=1)
    ]
    sources.extend(
        [
            {
                "id": "iana-language-subtag-registry",
                "resource": dataset.language_registries[0]["source_uri"],
                "title": "IANA Language Subtag Registry",
                "author": "team:iana",
            },
            {
                "id": "classification-assertions",
                "resource": CANONICAL_ASSERTIONS_URL,
                "title": "Canonical qualified classification assertions",
                "author": _generator_actor(dataset),
            },
            {
                "id": "label-assertions",
                "resource": CANONICAL_LABEL_ASSERTIONS_URL,
                "title": "Qualified label assertions",
                "author": _generator_actor(dataset),
            },
            {
                "id": "label-resources",
                "resource": CANONICAL_LABEL_RESOURCES_URL,
                "title": "Assertion-scoped SKOS-XL label resources",
                "author": _generator_actor(dataset),
            },
            {
                "id": "label-profiles",
                "resource": CANONICAL_LABEL_PROFILES_URL,
                "title": "Conservative label linguistic profiles",
                "author": _generator_actor(dataset),
            },
            {
                "id": "unicode-script-registry",
                "resource": dataset.script_registries[0]["profile_uri"],
                "title": "Unicode Script property profile",
                "author": "team:unicode",
            },
            {
                "id": "note-assertions",
                "resource": CANONICAL_NOTE_ASSERTIONS_URL,
                "title": "Qualified note assertions",
                "author": _generator_actor(dataset),
            },
            {
                "id": "quality-findings",
                "resource": CANONICAL_QUALITY_FINDINGS_URL,
                "title": "Automated quality findings with no review effect",
                "author": _generator_actor(dataset),
            },
        ]
    )
    return sources


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def _markdown_text(value: str) -> str:
    return " ".join(value.split()).replace("[", "\\[").replace("]", "\\]")


def _table_text(value: str) -> str:
    return _markdown_text(value).replace("|", "\\|")


@dataclass
class Navigation:
    dataset: Dataset
    concepts: dict[str, dict[str, Any]]
    parents: dict[str, list[str]]
    children: dict[str, list[str]]
    classified_instruments: dict[str, list[str]]
    instrument_classifications: dict[str, list[str]]
    classification_assertions: dict[tuple[str, str], list[dict[str, Any]]]
    labels: dict[str, list[dict[str, str]]]
    label_assertions: dict[str, list[dict[str, str]]]
    label_profiles: dict[str, dict[str, Any]]
    note_assertions: dict[str, list[dict[str, str]]]
    paths: dict[str, PurePosixPath]

    @classmethod
    def from_dataset(cls, dataset: Dataset) -> "Navigation":
        parents: dict[str, list[str]] = defaultdict(list)
        children: dict[str, list[str]] = defaultdict(list)
        classified_instruments: dict[str, list[str]] = defaultdict(list)
        instrument_classifications: dict[str, list[str]] = defaultdict(list)
        classification_assertions: dict[tuple[str, str], list[dict[str, Any]]] = (
            defaultdict(list)
        )
        for relation in dataset.source_relations:
            subject = relation["subject_uri"]
            obj = relation["object_uri"]
            if relation["predicate_uri"] == BROADER:
                parents[subject].append(obj)
                children[obj].append(subject)
        for assertion in dataset.classification_assertions:
            if assertion["stance"] in {"rejected", "superseded"}:
                continue
            if assertion["target_type"] != "instrument-concept":
                continue
            classification = assertion["classification_uri"]
            instrument = assertion["target_uri"]
            classified_instruments[classification].append(instrument)
            instrument_classifications[instrument].append(classification)
            classification_assertions[(classification, instrument)].append(assertion)

        paths: dict[str, PurePosixPath] = {}
        for concept in dataset.concepts:
            local_filename = re.sub(r"[^A-Za-z0-9._-]+", "-", concept["local_id"])
            if (
                concept["kind"] == "classification"
                and concept["scheme_uri"] == HS_SCHEME
            ):
                path = PurePosixPath(
                    "classifications", "concepts", f"{local_filename}.md"
                )
            elif (
                concept["kind"] == "instrument"
                and concept["scheme_uri"] == INSTRUMENT_SCHEME
                and concept.get("mimo_id", "").isdigit()
            ):
                number = int(concept["mimo_id"])
                start = number // 1000 * 1000
                bucket = f"{start:05d}-{start + 999:05d}"
                path = PurePosixPath("instruments", bucket, f"{local_filename}.md")
            else:
                scheme_key = hashlib.sha256(
                    concept["scheme_uri"].encode("utf-8")
                ).hexdigest()[:12]
                collision_safe_filename = (
                    f"{local_filename.strip('-') or 'concept'}-"
                    f"{hashlib.sha256(concept['uri'].encode('utf-8')).hexdigest()[:10]}"
                )
                path = PurePosixPath(
                    "schemes",
                    scheme_key,
                    concept["kind"],
                    f"{collision_safe_filename}.md",
                )
            paths[concept["uri"]] = path

        return cls(
            dataset=dataset,
            concepts=dataset.concepts_by_uri,
            parents={key: sorted(set(value)) for key, value in parents.items()},
            children={key: sorted(set(value)) for key, value in children.items()},
            classified_instruments={
                key: sorted(set(value)) for key, value in classified_instruments.items()
            },
            instrument_classifications={
                key: sorted(set(value))
                for key, value in instrument_classifications.items()
            },
            classification_assertions={
                key: sorted(value, key=lambda row: row["uri"])
                for key, value in classification_assertions.items()
            },
            labels=dataset.labels_by_concept,
            label_assertions=dataset.label_assertions_by_concept,
            label_profiles=dataset.label_profiles_by_resource_uri,
            note_assertions=dataset.note_assertions_by_concept,
            paths=paths,
        )

    def preferred(self, uri: str) -> dict[str, str]:
        return {
            row["language"]: row["label"]
            for row in self.labels.get(uri, [])
            if row["label_type"] == "preferred"
        }

    def title(self, uri: str) -> str:
        preferred = self.preferred(uri)
        if "en" in preferred:
            return preferred["en"]
        if preferred:
            return sorted(preferred.items())[0][1]
        concept = self.concepts[uri]
        return f"Unresolved {concept['kind']} {concept['local_id']}"

    def sort_key(self, uri: str) -> tuple[str, str, str]:
        concept = self.concepts[uri]
        return (concept.get("notation", ""), self.title(uri).casefold(), uri)

    def link(self, uri: str) -> str:
        return f"/{self.paths[uri].as_posix()}"

    def linked_title(self, uri: str) -> str:
        concept = self.concepts[uri]
        notation = concept.get("notation")
        title = _markdown_text(self.title(uri))
        display = f"{notation} — {title}" if notation else title
        return f"[{display}]({self.link(uri)})"

    def ancestors(self, uri: str) -> list[tuple[str, int]]:
        distances: dict[str, int] = {}
        queue = deque((parent, 1) for parent in self.parents.get(uri, []))
        while queue:
            ancestor, depth = queue.popleft()
            previous = distances.get(ancestor)
            if previous is not None and previous <= depth:
                continue
            distances[ancestor] = depth
            queue.extend(
                (parent, depth + 1) for parent in self.parents.get(ancestor, [])
            )
        return sorted(
            distances.items(),
            key=lambda row: (-row[1], self.sort_key(row[0])),
        )

    def reference(self, uri: str, *, depth: int | None = None) -> dict[str, Any]:
        concept = self.concepts[uri]
        result: dict[str, Any] = {
            "uri": uri,
            "local_id": concept["local_id"],
            "kind": concept["kind"],
            "label": self.title(uri),
            "resolution_status": concept["resolution_status"],
        }
        if concept.get("mimo_id") is not None:
            result["mimo_id"] = concept["mimo_id"]
        if concept.get("notation"):
            result["notation"] = concept["notation"]
        if depth is not None:
            result["depth"] = depth
        return result

    def classification_reference(
        self,
        classification_uri: str,
        classified_target_uri: str,
        reference_uri: str,
    ) -> dict[str, Any]:
        """Return a target reference qualified by its classification assertion."""
        result = self.reference(reference_uri)
        assertions = self.classification_assertions[
            (classification_uri, classified_target_uri)
        ]
        result["classification_assignments"] = [
            {
                "assertion_uri": assertion["uri"],
                "assignment_uri": assertion["assignment_uri"],
                "predicate_uri": assertion["predicate_uri"],
                "assertion_origin": assertion["assertion_origin"],
                "stance": assertion["stance"],
                "assigned_by_uri": assertion["assigned_by_uri"],
                "generated_by_uri": assertion["generated_by_uri"],
                "classification_method_uri": assertion["classification_method_uri"],
                "criteria_uris": assertion["criteria_uris"],
                "assessment_uris": assertion["assessment_uris"],
                "inference_logic_uri": assertion["inference_logic_uri"],
                "classification_expression_uri": assertion[
                    "classification_expression_uri"
                ],
                "perspective_uri": assertion["perspective_uri"],
                "applicability_scope_uris": assertion["applicability_scope_uris"],
                "authority_assignment_uris": assertion["authority_assignment_uris"],
                "projection_policy_uris": assertion["projection_policy_uris"],
                "evidence": assertion["evidence"],
                "source_record_uri": assertion["source_record_uri"],
                "source_predicate_uri": assertion["source_predicate_uri"],
                "source_uri": assertion["source_uri"],
                "active_review_decisions": self.dataset.active_review_decisions(
                    assertion["uri"]
                ),
            }
            for assertion in assertions
        ]
        return result


def _label_table(
    rows: Iterable[dict[str, str]], profiles: dict[str, dict[str, Any]]
) -> str:
    values = sorted(
        rows,
        key=lambda row: (
            row["language_tag"],
            row["label_role"],
            row["literal_form"].casefold(),
        ),
    )
    if not values:
        return "No labels are available for this unresolved source reference."
    body = [
        "| Language | Submitted | Tag status | Role | Label | Observed script(s) | Qualification | SKOS projection | SKOS-XL resource | Review | Assertion |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    body.extend(
        f"| `{row['language_tag']}` | `{row['submitted_language_tag']}` | "
        f"`{row['language_tag_status']}` | {row['label_role']} | "
        f"{_table_text(row['literal_form'])} | "
        f"`{','.join(profiles[row['label_resource_uri']]['observed_script_codes']) or 'none'}` | "
        f"`{profiles[row['label_resource_uri']]['translation_status']}` | "
        f"`{row['skos_projection_status']}` | "
        f"`{row['label_resource_uri']}` | `{row['review_status']}` | "
        f"`{row['uri']}` |"
        for row in values
    )
    return "\n".join(body)


def _relationship_section(
    navigation: Navigation, heading: str, uris: Iterable[str], empty: str
) -> str:
    values = sorted(set(uris), key=navigation.sort_key)
    lines = [f"# {heading}", ""]
    if values:
        lines.extend(f"- {navigation.linked_title(uri)}" for uri in values)
    else:
        lines.append(empty)
    return "\n".join(lines)


def _concept_page(navigation: Navigation, concept: dict[str, Any]) -> str:
    uri = concept["uri"]
    title = navigation.title(uri)
    preferred = navigation.preferred(uri)
    languages = sorted(preferred)
    scheme = next(
        row
        for row in navigation.dataset.concept_schemes
        if row["uri"] == concept["scheme_uri"]
    )
    if concept["kind"] == "classification" and concept["scheme_uri"] == HS_SCHEME:
        concept_type = "Hornbostel-Sachs Classification"
        description = f"Hornbostel–Sachs class {concept['notation']}: {title}."
        tags = ["classification", "hornbostel-sachs", f"notation-{concept['notation']}"]
    elif concept["kind"] == "instrument" and concept["scheme_uri"] == INSTRUMENT_SCHEME:
        concept_type = "MIMO Instrument Concept"
        description = f"MIMO musical-instrument concept for {title}."
        tags = ["instrument", "mimo", concept["resolution_status"]]
    else:
        concept_type = "Registered Scheme Concept"
        description = f"{scheme['label']} concept for {title}."
        tags = [concept["kind"], "registered-scheme"]

    parts = [
        _frontmatter(
            type=concept_type,
            title=title,
            description=description,
            resource=uri,
            tags=tags,
            **_okf_v02_fields(
                navigation.dataset,
                sources=_concept_sources(navigation.dataset, concept),
                machine_verified=True,
            ),
            dataset_version=navigation.dataset.metadata["dataset_version"],
            local_id=concept["local_id"],
            mimo_id=concept.get("mimo_id"),
            notation=concept.get("notation"),
            scheme_uri=concept["scheme_uri"],
            resolution_status=concept["resolution_status"],
            languages=languages,
        ),
        f"# {title}",
        "",
    ]
    if concept.get("notation"):
        parts.extend((f"Hornbostel–Sachs notation: `{concept['notation']}`", ""))
    parts.extend(
        (
            "# Definition",
            "",
            concept.get("definition")
            or "No definition is available in this source snapshot.",
            (
                "[Qualified note assertion]"
                f"({_markdown_text(navigation.note_assertions[uri][0]['uri'])}) "
                f"— review status "
                f"`{navigation.note_assertions[uri][0]['review_status']}`."
                "[^note-assertions]"
                if navigation.note_assertions.get(uri)
                else "No qualified note assertion is available."
            ),
            "",
            "# Labels",
            "",
            _label_table(
                navigation.label_assertions.get(uri, []),
                navigation.label_profiles,
            ),
            "",
            "Every displayed label has an assertion-scoped SKOS-XL resource plus a distinct "
            "assertion URI, source record, asserting agent, projection status, and "
            "review status.[^label-resources][^label-assertions]",
            "Observed scripts come from Unicode character properties. They do not "
            "identify a language, dialect, transliteration system, or community "
            "preference; unrecorded fields remain empty.[^label-profiles]",
            "",
        )
    )

    ancestors = navigation.ancestors(uri)
    parts.extend(("# Ancestor context", ""))
    if ancestors:
        by_depth: dict[int, list[str]] = defaultdict(list)
        for item, depth in ancestors:
            by_depth[depth].append(item)
        if all(len(values) == 1 for values in by_depth.values()):
            parts.append(
                " → ".join(
                    navigation.linked_title(by_depth[depth][0])
                    for depth in sorted(by_depth, reverse=True)
                )
            )
        else:
            for depth in sorted(by_depth):
                for item in sorted(by_depth[depth], key=navigation.sort_key):
                    parts.append(f"- Distance {depth}: {navigation.linked_title(item)}")
    else:
        parts.append("This concept is a root of its source hierarchy.")
    parts.append("")
    parts.extend(
        (
            _relationship_section(
                navigation,
                "Direct broader concepts",
                navigation.parents.get(uri, []),
                "No direct broader concept is asserted.",
            ),
            "",
            _relationship_section(
                navigation,
                "Direct narrower concepts",
                navigation.children.get(uri, []),
                "No direct narrower concept is asserted.",
            ),
            "",
        )
    )
    if concept["kind"] == "classification":
        parts.extend(
            (
                "The following links summarize qualified classification assignment "
                "occurrences. Inspect each occurrence's perspective, scope, stance, "
                "evidence, authority, reviews, and projection policies before use."
                "[^classification-assertions]",
                "",
                _relationship_section(
                    navigation,
                    "Instrument concepts appearing in classification claims",
                    navigation.classified_instruments.get(uri, []),
                    "No instrument classification claim is available for this class.",
                ),
                "",
            )
        )
    elif concept["kind"] == "instrument":
        parts.extend(
            (
                "The following links summarize qualified classification assignment "
                "occurrences. Inspect each occurrence's perspective, scope, stance, "
                "evidence, authority, reviews, and projection policies before use."
                "[^classification-assertions]",
                "",
                _relationship_section(
                    navigation,
                    "Classification claims",
                    navigation.instrument_classifications.get(uri, []),
                    "No classification claim is available for this instrument.",
                ),
                "",
            )
        )
    parts.extend(
        (
            "# Provenance",
            "",
            f"Canonical concept URI: [{uri}]({uri})[^concept-record]",
            "",
            f"Source snapshot retrieved: `{navigation.dataset.metadata['source_retrieved_at']}`. ",
            f"Dataset version: `{navigation.dataset.metadata['dataset_version']}`.",
            "",
            f"Generated by `{_generator_actor(navigation.dataset)}`. The OKF "
            f"`verified` event from `{OKF_VERIFIER}` confirms the deterministic "
            "projection and format validation only; it is not human or scholarly "
            "review of the underlying concept or classification assertions.",
            "",
            "This page is a generated navigation view. Consult the canonical source-relation and classification-assertion layers for semantics and provenance.",
            "",
            "[^concept-record]: Canonical concept record in its registered scheme.",
            "[^classification-assertions]: Canonical qualified classification assertion layer.",
            "[^label-assertions]: Canonical qualified label assertion layer.",
            "[^label-profiles]: Canonical conservative linguistic profile layer.",
            "[^note-assertions]: Canonical qualified note assertion layer.",
        )
    )
    return "\n".join(parts)


def _guide_page(
    navigation: Navigation,
    *,
    title: str,
    description: str,
    tags: list[str],
    body: str,
) -> str:
    return (
        _frontmatter(
            type="Guide",
            title=title,
            description=description,
            tags=tags,
            **_okf_v02_fields(
                navigation.dataset,
                sources=[
                    {
                        "id": "dataset-model",
                        "resource": "/dataset.md",
                        "title": "Dataset scope and knowledge model",
                        "author": _generator_actor(navigation.dataset),
                    }
                ],
                machine_verified=False,
            ),
            dataset_version=navigation.dataset.metadata["dataset_version"],
        )
        + f"# {title}\n\n{body.strip()}\n"
    )


def _build_guides(navigation: Navigation, root: Path) -> int:
    counts = navigation.dataset.metadata["counts"]
    guides = {
        "choosing-identifiers.md": (
            "Choosing stable identifiers",
            "How to identify and join classification and instrument concepts safely.",
            ["identity", "uri", "joining"],
            """
Use the complete MIMO URI as the primary key. Labels, translations, notations, and
numeric `mimo_id` values are lookup aids, not globally safe identifiers.

## Classification versus instrument concepts

- A **classification** URI identifies a Hornbostel–Sachs class and normally has a notation.
- An **instrument** URI identifies a thesaurus concept and may have labels in many languages.
- A class-to-instrument link is a source-derived `omaro:classifiedAs` assertion.
  Its preserved MIMO source predicate and review status remain attached.

## Recommended workflow

1. Resolve user text through the multilingual labels.
2. Retain every candidate URI when a label is ambiguous.
3. Use hierarchy and qualified classification assertions to disambiguate candidates.
4. Return the selected URI and dataset version with the answer.

See [multilingual search](/guides/multilingual-search.md) and
[ambiguity handling](/guides/ambiguity-and-disambiguation.md).
""",
        ),
        "navigating-the-classification.md": (
            "Navigating the classifications",
            "How to traverse Hornbostel–Sachs and MIMO hierarchy relations.",
            ["hierarchy", "classification", "navigation"],
            """
`skos:broader` points from a more specific concept to a direct broader concept.
The generated **Direct narrower concepts** lists are deterministic inverses of
those assertions. The **Ancestor path** is a convenience view, not an additional
source assertion.

Start with the [classification index](/classifications/index.md), choose one of
the five top-level classes, and follow narrower links. Do not derive hierarchy
from string prefixes alone: notation is useful for display and search, while
the explicit URI relations are authoritative.

For exact or bulk traversal, use the SQLite `concept_ancestors` table rather
than reconstructing the tree from prose.
""",
        ),
        "multilingual-search.md": (
            "Multilingual search",
            "How to resolve multilingual instrument names without losing identity.",
            ["multilingual", "search", "entity-linking"],
            """
Preferred, alternative, and hidden labels are retained with BCP 47 language
tags. Search should normalize Unicode and case for candidate retrieval but must
return the original label and canonical URI.

## Retrieval sequence

1. Search labels in the requested language.
2. Include alternative labels when preferred-label matching is insufficient.
3. Keep multiple URI candidates when the same lexical form identifies different concepts.
4. Rank candidates using hierarchy, qualified classifications, and surrounding document context.
5. Report missing language coverage rather than manufacturing a translation.

MIMO's legacy `dk` tag is represented as `da`; an untagged source label would
use `und`. The [RAG JSONL guide](/guides/rag-records.md) describes the
self-contained retrieval representation.
""",
        ),
        "ambiguity-and-disambiguation.md": (
            "Ambiguity and disambiguation",
            "How agents should handle duplicate labels, aliases, and unresolved references.",
            ["ambiguity", "quality", "entity-linking"],
            """
Equal labels do not imply equal concepts. A label may be shared across languages,
appear on multiple concepts, or be both preferred and alternative in the source.

When several concepts match, present the candidates with their URIs, broader
concepts, source-derived classifications, and resolution status. Ask for additional
context when those facts do not select one candidate. Never merge concepts or
silently correct source text during retrieval.

Unresolved instrument stubs preserve mapping targets that MIMO asserted but for
which this snapshot has no resolved record. They are evidence of an incomplete
target, not permission to invent a label or definition.
""",
        ),
        "mapping-catalogue-records.md": (
            "Mapping catalogue records",
            "A source-grounded workflow for enriching collection metadata.",
            ["cataloguing", "mapping", "museum"],
            """
Treat an incoming catalogue label as a candidate lookup, not an identifier.
Resolve it to an instrument URI using language, aliases, and contextual evidence;
then retrieve explicitly classified Hornbostel–Sachs classes.

Record the selected URI, original catalogue text, matching method, dataset
version, confidence, and any human review. Preserve multiple candidates when
the evidence is insufficient. A class URI and an instrument URI describe
different entities and should occupy separate metadata fields.

Bulk workflows should use CSV or SQLite. These pages are designed for inspection,
explanation, and agent navigation.
""",
        ),
        "provenance-and-citation.md": (
            "Provenance and citation",
            "How to distinguish source assertions, generated navigation, and release metadata.",
            ["provenance", "citation", "release"],
            f"""
The canonical records retain MIMO concept URIs and source-published SKOS
relations in an explicit source layer. MIMO `skos:exactMatch` mappings are not
repeated as unqualified project assertions. Instead, generated
`omaro:classifiedAs` assertions retain their source predicate and are marked
`source-derived` and `unreviewed`.

Source retrieval time: `{navigation.dataset.metadata["source_retrieved_at"]}`
Dataset version: `{navigation.dataset.metadata["dataset_version"]}`
DOI: `{navigation.dataset.metadata["doi"]}`

Answers should cite the relevant concept URI and dataset version. Research
outputs should additionally cite the released dataset DOI. Consult the release
quality report before interpreting unresolved targets or language gaps.
""",
        ),
        "rag-records.md": (
            "Self-contained RAG records",
            "How to index and use the one-record-per-concept RAG JSONL export.",
            ["rag", "jsonl", "retrieval"],
            """
`dist/jsonl/rag-concepts.jsonl` contains one self-contained record per canonical
concept. Each record repeats identity, labels, definition, direct and transitive
hierarchy context, qualified class/instrument assertions, provenance, and a compact
`retrieval_text` field.

Index `retrieval_text` for semantic or lexical retrieval, but keep the complete
JSON object as returned metadata. Use `uri` as the document ID. After retrieval,
answer from structured fields and return canonical URIs rather than relying on
generated prose alone.

Embeddings are intentionally not distributed: they are model-specific and can
be regenerated from the versioned textual records.
""",
        ),
    }
    for filename, (title, description, tags, body) in guides.items():
        _write(
            root / "guides" / filename,
            _guide_page(
                navigation,
                title=title,
                description=description,
                tags=tags,
                body=body,
            ),
        )
    guide_index = [
        "# Guides",
        "",
        "Curated instructions for interpreting and navigating the generated knowledge bundle.",
        "",
    ]
    for filename, (title, description, _, _) in sorted(guides.items()):
        guide_index.append(f"- [{title}]({filename}) — {description}")
    _write(root / "guides" / "index.md", "\n".join(guide_index))

    dataset_page = (
        _frontmatter(
            type="Dataset",
            title=navigation.dataset.metadata["title"],
            description="A versioned SKOS-compatible snapshot of Hornbostel–Sachs and MIMO instrument concepts.",
            resource=REPOSITORY_URI,
            tags=["dataset", "skos", "organology", "multilingual"],
            **_okf_v02_fields(
                navigation.dataset,
                sources=_dataset_sources(navigation.dataset),
                machine_verified=True,
            ),
            dataset_version=navigation.dataset.metadata["dataset_version"],
        )
        + "# Dataset\n\n"
        f"This bundle describes **{counts['classifications']} classifications**, "
        f"**{counts['resolved_instruments']} resolved instrument concepts**, and "
        f"**{counts['unresolved_stubs']} unresolved instrument references**."
        "[^mimo-source-1][^mimo-source-2]\n\n"
        "# Knowledge model\n\n"
        "Concept URIs are identities. Language-tagged labels are lexical forms. "
        "`skos:broader` represents direct hierarchy edges. Qualified "
        "`omaro:classifiedAs` assertions project MIMO-published mappings without "
        "claiming concept equivalence; the original predicates remain in the "
        "separate source layer.[^classification-assertions]\n\n"
        f"All **{counts['label_assertions']} label assertions** reference "
        f"**{counts['label_resources']} non-collapsing SKOS-XL resources**; "
        f"**{counts['label_profiles']} conservative linguistic profiles**; "
        f"**{counts['note_assertions']} source definitions** also have stable "
        "qualified assertions linked to agents, versioned sources, and review "
        "statuses.[^label-resources][^label-assertions][^note-assertions]\n\n"
        f"The audit exposes **{counts['quality_findings']} automated warnings**. "
        "They have no review effect and require human interpretation."
        "[^quality-findings]\n\n"
        f"Language tags are checked offline against the pinned IANA registry "
        f"dated **{navigation.dataset.language_registries[0]['file_date']}**."
        "[^iana-language-subtag-registry]\n\n"
        f"Character scripts are observed with Unicode Script "
        f"**{navigation.dataset.script_registries[0]['unicode_version']}**; "
        "this evidence is not treated as inferred language or cultural identity."
        "[^unicode-script-registry][^label-profiles]\n\n"
        "# Navigation\n\n"
        "- [Curated guides](/guides/index.md)\n"
        "- [Hornbostel–Sachs classifications](/classifications/index.md)\n"
        "- [MIMO instrument concepts](/instruments/index.md)\n\n"
        "# Companion exports\n\n"
        "The parent distribution also contains canonical JSONL, CSV, RDF, SQLite, "
        "legacy JSON, and the self-contained `jsonl/rag-concepts.jsonl` export.\n\n"
        "# Trust scope\n\n"
        f"The OKF `verified` event from `{OKF_VERIFIER}` confirms schema, link, "
        "and deterministic projection checks. It does not constitute human domain "
        "review or acceptance of source-derived classification assertions.\n\n"
        "[^mimo-source-1]: MIMO Hornbostel–Sachs vocabulary API.\n"
        "[^mimo-source-2]: MIMO instrument-keyword vocabulary API.\n"
        "[^classification-assertions]: Canonical qualified classification assertion layer.\n"
        "[^label-assertions]: Canonical qualified label assertion layer.\n"
        "[^label-resources]: Canonical SKOS-XL label-resource layer.\n"
        "[^label-profiles]: Canonical conservative linguistic profile layer.\n"
        "[^note-assertions]: Canonical qualified note assertion layer.\n"
        "[^quality-findings]: Deterministic warning layer; not human review.\n"
        "[^iana-language-subtag-registry]: Official IANA Language Subtag Registry.\n"
        "[^unicode-script-registry]: Unicode Standard Annex #24 and pinned Script data.\n"
    )
    _write(root / "dataset.md", dataset_page)
    return len(guides) + 1


def _classification_root(navigation: Navigation, uri: str) -> str:
    ancestors = navigation.ancestors(uri)
    return ancestors[0][0] if ancestors else uri


def _build_indexes(navigation: Navigation, root: Path) -> int:
    concepts = navigation.dataset.concepts_by_uri
    classifications = [
        row
        for row in navigation.dataset.concepts
        if row["kind"] == "classification" and row["scheme_uri"] == HS_SCHEME
    ]
    instruments = [
        row
        for row in navigation.dataset.concepts
        if row["kind"] == "instrument" and row["scheme_uri"] == INSTRUMENT_SCHEME
    ]
    other_concepts = [
        row
        for row in navigation.dataset.concepts
        if row["scheme_uri"] not in {HS_SCHEME, INSTRUMENT_SCHEME}
    ]

    families: dict[str, list[str]] = defaultdict(list)
    for concept in classifications:
        families[_classification_root(navigation, concept["uri"])].append(
            concept["uri"]
        )
    classification_index = [
        "# Hornbostel–Sachs classifications",
        "",
        "Choose a top-level family, then follow explicit broader and narrower links.",
        "",
    ]
    for root_uri in sorted(families, key=navigation.sort_key):
        root_concept = concepts[root_uri]
        family_path = PurePosixPath(
            "classifications", "families", root_concept["mimo_id"], "index.md"
        )
        members = sorted(families[root_uri], key=navigation.sort_key)
        classification_index.append(
            f"- [{root_concept['notation']} — {_markdown_text(navigation.title(root_uri))}]"
            f"(/{family_path.as_posix()}) — {len(members)} concepts"
        )
        rows = [
            f"# {root_concept['notation']} — {navigation.title(root_uri)}",
            "",
            f"This family contains {len(members)} classification concepts.",
            "",
        ]
        rows.extend(f"- {navigation.linked_title(uri)}" for uri in members)
        _write(root / Path(family_path.as_posix()), "\n".join(rows))
    _write(root / "classifications" / "index.md", "\n".join(classification_index))

    buckets: dict[str, list[str]] = defaultdict(list)
    for concept in instruments:
        buckets[navigation.paths[concept["uri"]].parts[1]].append(concept["uri"])
    instrument_index = [
        "# MIMO instrument concepts",
        "",
        "Concept pages are partitioned by stable numeric MIMO ID range.",
        "",
    ]
    for bucket in sorted(buckets):
        members = sorted(buckets[bucket], key=navigation.sort_key)
        instrument_index.append(
            f"- [IDs {bucket}](/instruments/{bucket}/index.md) — {len(members)} concepts"
        )
        rows = [
            f"# Instrument IDs {bucket}",
            "",
            f"This range contains {len(members)} instrument concepts, including unresolved stubs.",
            "",
        ]
        rows.extend(f"- {navigation.linked_title(uri)}" for uri in members)
        _write(root / "instruments" / bucket / "index.md", "\n".join(rows))
    _write(root / "instruments" / "index.md", "\n".join(instrument_index))

    extra_scheme_index_link = ""
    if other_concepts:
        scheme_rows = {row["uri"]: row for row in navigation.dataset.concept_schemes}
        by_scheme: dict[str, list[str]] = defaultdict(list)
        for concept in other_concepts:
            by_scheme[concept["scheme_uri"]].append(concept["uri"])
        scheme_index = ["# Other registered concept schemes", ""]
        for scheme_uri in sorted(by_scheme):
            scheme_key = hashlib.sha256(scheme_uri.encode("utf-8")).hexdigest()[:12]
            members = sorted(by_scheme[scheme_uri], key=navigation.sort_key)
            scheme_index.append(
                f"- [{_markdown_text(scheme_rows[scheme_uri]['label'])}]"
                f"(/{PurePosixPath('schemes', scheme_key, 'index.md').as_posix()}) "
                f"— {len(members)} concepts"
            )
            rows = [
                f"# {scheme_rows[scheme_uri]['label']}",
                "",
                f"Scheme URI: `{scheme_uri}`",
                "",
            ]
            rows.extend(f"- {navigation.linked_title(uri)}" for uri in members)
            _write(root / "schemes" / scheme_key / "index.md", "\n".join(rows))
        _write(root / "schemes" / "index.md", "\n".join(scheme_index))
        extra_scheme_index_link = (
            "- [Other registered schemes](schemes/index.md) — independently "
            "identified scholarly, institutional, or community concepts\n\n"
        )

    root_index = (
        _frontmatter(okf_version=OKF_VERSION)
        + "# OMARO knowledge bundle\n\n"
        + "Progressively navigate the dataset without loading every concept into context.\n\n"
        + "## Start here\n\n"
        + "- [Dataset scope and model](dataset.md) — counts, semantics, sources, and trust scope\n"
        + "- [Interpretation and retrieval guides](guides/index.md) — safe use by people and agents\n"
        + "- [Hornbostel–Sachs classifications](classifications/index.md) — classification families and concepts\n"
        + "- [MIMO instrument concepts](instruments/index.md) — multilingual instrument concepts by ID range\n\n"
        + extra_scheme_index_link
        + "## Exact and bulk access\n\n"
        + "Use the companion SQLite, RDF, CSV, or JSONL exports for exact queries. "
        + "The self-contained RAG file is `jsonl/rag-concepts.jsonl` in the parent distribution.\n\n"
        + "OKF v0.2 provenance, generation, verification, and lifecycle fields are "
        + "recorded on concept documents. Verification denotes machine validation "
        + "of the projection, not human domain review.\n"
    )
    _write(root / "index.md", root_index)
    profile_date = OKF_PROFILE_UPDATED_AT[:10]
    source_date = navigation.dataset.metadata["source_retrieved_at"][:10]
    updates: dict[str, list[str]] = defaultdict(list)
    updates[profile_date].append(
        "- **Update**: Migrated the bundle to OKF v0.2 provenance, trust, and "
        "lifecycle fields."
    )
    updates[source_date].append(
        f"- **Generation**: Built OKF v{OKF_VERSION} navigation pages from dataset "
        f"version {navigation.dataset.metadata['dataset_version']}."
    )
    log = ["# Bundle update log", ""]
    for update_date in sorted(updates, reverse=True):
        log.extend((f"## {update_date}", *updates[update_date], ""))
    _write(
        root / "log.md",
        "\n".join(log),
    )
    return sum(path.name in {"index.md", "log.md"} for path in root.rglob("*.md"))


def _frontmatter_document(
    text: str, relative: PurePosixPath | Path
) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise ValidationError(f"OKF concept lacks frontmatter: {relative}")
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        raise ValidationError(f"OKF concept has unclosed frontmatter: {relative}")
    try:
        parsed = yaml.safe_load(parts[1])
    except yaml.YAMLError as error:
        raise ValidationError(
            f"OKF concept has invalid YAML frontmatter: {relative}"
        ) from error
    if not isinstance(parsed, dict):
        raise ValidationError(f"OKF concept frontmatter must be a mapping: {relative}")
    return parsed, parts[2]


def _validate_date(value: Any, field: str, relative: Path) -> date:
    if not isinstance(value, str):
        raise ValidationError(f"OKF {field} must be an ISO 8601 date: {relative}")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(
            f"OKF {field} must be an ISO 8601 date: {relative}"
        ) from error


def _validate_actor(value: Any, field: str, relative: Path) -> None:
    if not isinstance(value, str) or not ACTOR_RE.fullmatch(value):
        raise ValidationError(
            f"OKF {field} does not follow the v0.2 actor convention: {relative}"
        )


def _validate_usage_window(value: Any, field: str, relative: Path) -> None:
    if not isinstance(value, dict) or set(value) != {"from", "to"}:
        raise ValidationError(
            f"OKF {field} must contain exactly from and to: {relative}"
        )
    start = _validate_date(value["from"], f"{field}.from", relative)
    end = _validate_date(value["to"], f"{field}.to", relative)
    if start > end:
        raise ValidationError(f"OKF {field} begins after it ends: {relative}")


def _validate_sources(frontmatter: dict[str, Any], body: str, relative: Path) -> None:
    sources = frontmatter.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValidationError(
            f"OKF v0.2 profile requires a non-empty sources list: {relative}"
        )
    shared_window = frontmatter.get("usage_window")
    if shared_window is not None:
        _validate_usage_window(shared_window, "usage_window", relative)
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        field = f"sources[{index}]"
        if not isinstance(source, dict):
            raise ValidationError(f"OKF {field} must be a mapping: {relative}")
        resource = source.get("resource")
        if not isinstance(resource, str) or not resource:
            raise ValidationError(f"OKF {field}.resource must be non-empty: {relative}")
        source_id = source.get("id")
        if source_id is not None:
            if not isinstance(source_id, str) or not source_id:
                raise ValidationError(f"OKF {field}.id must be non-empty: {relative}")
            if source_id in source_ids:
                raise ValidationError(
                    f"OKF source id is duplicated ({source_id}): {relative}"
                )
            source_ids.add(source_id)
        if "author" in source and (
            not isinstance(source["author"], str) or not source["author"]
        ):
            raise ValidationError(f"OKF {field}.author must be non-empty: {relative}")
        if "last_modified" in source:
            _validate_date(source["last_modified"], f"{field}.last_modified", relative)
        if "usage_window" in source:
            _validate_usage_window(
                source["usage_window"], f"{field}.usage_window", relative
            )
        if "usage_count" in source:
            usage_count = source["usage_count"]
            if (
                isinstance(usage_count, bool)
                or not isinstance(usage_count, int)
                or usage_count < 0
            ):
                raise ValidationError(
                    f"OKF {field}.usage_count must be a non-negative integer: "
                    f"{relative}"
                )
            if shared_window is None and "usage_window" not in source:
                raise ValidationError(
                    f"OKF {field}.usage_count lacks a usage window: {relative}"
                )
    for footnote in set(FOOTNOTE_RE.findall(body)):
        if footnote not in source_ids:
            raise ValidationError(
                f"OKF footnote has no matching sources id ({footnote}): {relative}"
            )


def _validate_generated_and_verified(
    frontmatter: dict[str, Any], relative: Path
) -> None:
    generated = frontmatter.get("generated")
    if not isinstance(generated, dict):
        raise ValidationError(
            f"OKF v0.2 profile requires generated metadata: {relative}"
        )
    _validate_actor(generated.get("by"), "generated.by", relative)
    if "at" in generated:
        _parse_iso_datetime(generated["at"], f"generated.at in {relative}")

    verified = frontmatter.get("verified")
    if verified is None:
        return
    events = [verified] if isinstance(verified, dict) else verified
    if not isinstance(events, list) or not events:
        raise ValidationError(f"OKF verified must be a mapping or list: {relative}")
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValidationError(
                f"OKF verified[{index}] must be a mapping: {relative}"
            )
        _validate_actor(event.get("by"), f"verified[{index}].by", relative)
        if "at" not in event:
            raise ValidationError(f"OKF verified[{index}].at is required: {relative}")
        _parse_iso_datetime(event["at"], f"verified[{index}].at in {relative}")


def _validate_attested_computation(
    frontmatter: dict[str, Any], body: str, relative: Path
) -> None:
    if frontmatter["type"] != "Attested Computation":
        return
    if not isinstance(frontmatter.get("runtime"), str) or not frontmatter["runtime"]:
        raise ValidationError(f"OKF Attested Computation requires runtime: {relative}")
    parameters = frontmatter.get("parameters", [])
    if not isinstance(parameters, list):
        raise ValidationError(
            f"OKF Attested Computation parameters must be a list: {relative}"
        )
    for index, parameter in enumerate(parameters):
        if (
            not isinstance(parameter, dict)
            or not isinstance(parameter.get("name"), str)
            or not parameter["name"]
            or not isinstance(parameter.get("type"), str)
            or not parameter["type"]
            or not isinstance(parameter.get("required"), bool)
        ):
            raise ValidationError(
                f"OKF Attested Computation parameter {index} is invalid: {relative}"
            )
    for field in ("executor", "attester"):
        if field not in frontmatter:
            continue
        contract = frontmatter[field]
        if (
            not isinstance(contract, dict)
            or not isinstance(contract.get("resource"), str)
            or not contract["resource"]
        ):
            raise ValidationError(
                f"OKF Attested Computation {field}.resource is invalid: {relative}"
            )
    computation = frontmatter.get("computation")
    section = re.search(
        r"(?ms)^# Computation\s*$\n(.*?)(?=^# |\Z)",
        body,
    )
    fenced_blocks = (
        re.findall(r"(?ms)^```[^\n]*\n.*?^```\s*$", section.group(1)) if section else []
    )
    if computation is not None:
        if not isinstance(computation, str) or not computation:
            raise ValidationError(
                f"OKF Attested Computation computation path is invalid: {relative}"
            )
        if fenced_blocks:
            raise ValidationError(
                f"OKF external computation must omit an inline fence: {relative}"
            )
    elif len(fenced_blocks) != 1:
        raise ValidationError(
            f"OKF inline computation requires one fenced block: {relative}"
        )


def _validate_concept_document(text: str, relative: Path) -> None:
    frontmatter, body = _frontmatter_document(text, relative)
    concept_type = frontmatter.get("type")
    if not isinstance(concept_type, str) or not concept_type.strip():
        raise ValidationError(f"OKF concept has no non-empty type: {relative}")
    if "timestamp" in frontmatter:
        raise ValidationError(
            f"OKF v0.2 concept retains superseded timestamp: {relative}"
        )
    if re.search(r"(?m)^# Citations\s*$", body):
        raise ValidationError(
            f"OKF v0.2 concept retains superseded Citations section: {relative}"
        )
    if frontmatter.get("status") not in {"draft", "stable", "deprecated"}:
        raise ValidationError(f"OKF status is invalid or absent: {relative}")
    if "stale_after" in frontmatter:
        _validate_date(frontmatter["stale_after"], "stale_after", relative)
    _validate_generated_and_verified(frontmatter, relative)
    _validate_sources(frontmatter, body, relative)
    _validate_attested_computation(frontmatter, body, relative)


def _validate_reserved_document(root: Path, path: Path, text: str) -> None:
    relative = path.relative_to(root)
    if path.name == "index.md":
        body = text
        if path == root / "index.md":
            frontmatter, body = _frontmatter_document(text, relative)
            if frontmatter != {"okf_version": OKF_VERSION}:
                raise ValidationError(
                    f"OKF root index must declare only version {OKF_VERSION}"
                )
        elif text.startswith("---\n"):
            raise ValidationError(
                f"OKF non-root index must not contain frontmatter: {relative}"
            )
        if not re.search(r"(?m)^# .+", body) or not MARKDOWN_LINK_RE.search(body):
            raise ValidationError(
                f"OKF index lacks a heading or linked entry: {relative}"
            )
        return

    if text.startswith("---\n"):
        raise ValidationError(f"OKF log must not contain frontmatter: {relative}")
    dates = DATE_HEADING_RE.findall(text)
    if not re.search(r"(?m)^# .+", text) or not dates:
        raise ValidationError(f"OKF log lacks its heading or date entries: {relative}")
    parsed_dates = [_validate_date(value, "log date", relative) for value in dates]
    if parsed_dates != sorted(parsed_dates, reverse=True):
        raise ValidationError(f"OKF log dates are not newest first: {relative}")
    if not re.search(r"(?m)^[-*] .+", text):
        raise ValidationError(f"OKF log has no update entries: {relative}")


def _validate_okf(root: Path, concept_page_count: int) -> None:
    markdown = sorted(root.rglob("*.md"))
    if concept_page_count <= 0:
        raise ValidationError("OKF export has no concept pages")
    for path in markdown:
        relative = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        if path.name in {"index.md", "log.md"}:
            _validate_reserved_document(root, path, text)
        else:
            _validate_concept_document(text, relative)

        # Broken links are valid in OKF v0.2, but generated links are held to a
        # stronger project quality gate because every target should exist.
        for target in INTERNAL_LINK_RE.findall(text):
            candidate = root / target.lstrip("/")
            if not candidate.exists():
                raise ValidationError(
                    f"broken generated OKF link in {relative}: {target}"
                )


def build_okf(dataset: Dataset, output: Path) -> dict[str, int]:
    root = output / "okf"
    navigation = Navigation.from_dataset(dataset)
    guide_pages = _build_guides(navigation, root)
    index_pages = _build_indexes(navigation, root)
    for concept in sorted(dataset.concepts, key=lambda row: row["uri"]):
        path = root / Path(navigation.paths[concept["uri"]].as_posix())
        _write(path, _concept_page(navigation, concept))
    _validate_okf(root, len(dataset.concepts))
    return {
        "okf_concept_pages": len(dataset.concepts),
        "okf_guide_pages": guide_pages,
        "okf_index_pages": index_pages,
    }


def _group_labels(rows: Iterable[dict[str, str]]) -> dict[str, dict[str, list[str]]]:
    result: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        result[row["label_type"]][row["language"]].append(row["label"])
    return {
        label_type: {
            language: sorted(set(values), key=lambda value: (value.casefold(), value))
            for language, values in sorted(by_language.items())
        }
        for label_type in ("preferred", "alternative", "hidden")
        if (by_language := result.get(label_type))
    }


def _retrieval_text(
    navigation: Navigation,
    concept: dict[str, Any],
    relationships: dict[str, list[dict[str, Any]]],
) -> str:
    uri = concept["uri"]
    labels = _group_labels(navigation.labels.get(uri, []))
    lines = [
        f"Title: {navigation.title(uri)}",
        f"Canonical URI: {uri}",
        f"Type: {concept['kind']}",
    ]
    if concept.get("notation"):
        lines.append(f"Hornbostel-Sachs notation: {concept['notation']}")
    if concept.get("definition"):
        lines.append(f"Definition: {' '.join(concept['definition'].split())}")
    for role, by_language in labels.items():
        for language, values in by_language.items():
            lines.append(f"{role.title()} labels ({language}): {'; '.join(values)}")
    label_statuses = sorted(
        {row["review_status"] for row in navigation.label_assertions.get(uri, [])}
    )
    if label_statuses:
        lines.append(f"Label assertion review status: {', '.join(label_statuses)}")
    note_statuses = sorted(
        {row["review_status"] for row in navigation.note_assertions.get(uri, [])}
    )
    if note_statuses:
        lines.append(f"Note assertion review status: {', '.join(note_statuses)}")
    relation_names = {
        "broader": "Direct broader concepts",
        "narrower": "Direct narrower concepts",
        "classified_instruments": "Instruments in qualified classification claims",
        "instrument_classifications": "Qualified classification claims",
    }
    for key, heading in relation_names.items():
        values = relationships[key]
        if values:
            status_suffix = ""
            if values[0].get("classification_assignments"):
                stances = sorted(
                    {
                        assignment["stance"]
                        for row in values
                        for assignment in row["classification_assignments"]
                    }
                )
                perspectives = sorted(
                    {
                        assignment["perspective_uri"]
                        for row in values
                        for assignment in row["classification_assignments"]
                    }
                )
                status_suffix = (
                    f" (stances: {', '.join(stances)}; "
                    f"perspectives: {', '.join(perspectives)})"
                )
            lines.append(
                f"{heading}{status_suffix}: "
                + "; ".join(
                    f"{row.get('notation') + ' — ' if row.get('notation') else ''}{row['label']} [{row['uri']}]"
                    for row in values
                )
            )
    lines.append(
        f"Source snapshot: {navigation.dataset.metadata['source_retrieved_at']}"
    )
    return "\n".join(lines)


def build_rag_jsonl(dataset: Dataset, path: Path) -> int:
    navigation = Navigation.from_dataset(dataset)
    label_resources_by_uri = dataset.label_resources_by_uri
    label_profiles_by_resource_uri = dataset.label_profiles_by_resource_uri
    findings_by_concept: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in dataset.quality_findings:
        findings_by_concept[finding["concept_uri"]].append(finding)
    rows: list[dict[str, Any]] = []
    for concept in dataset.concepts:
        uri = concept["uri"]
        concept_label_resource_uris = {
            row["label_resource_uri"]
            for row in navigation.label_assertions.get(uri, [])
        }
        relationships = {
            "broader": [
                navigation.reference(target)
                for target in sorted(
                    navigation.parents.get(uri, []), key=navigation.sort_key
                )
            ],
            "narrower": [
                navigation.reference(target)
                for target in sorted(
                    navigation.children.get(uri, []), key=navigation.sort_key
                )
            ],
            "ancestors": [
                navigation.reference(target, depth=depth)
                for target, depth in navigation.ancestors(uri)
            ],
            "classified_instruments": [
                navigation.classification_reference(uri, target, target)
                for target in sorted(
                    navigation.classified_instruments.get(uri, []),
                    key=navigation.sort_key,
                )
            ],
            "instrument_classifications": [
                navigation.classification_reference(target, uri, target)
                for target in sorted(
                    navigation.instrument_classifications.get(uri, []),
                    key=navigation.sort_key,
                )
            ],
        }
        review_targets = {
            *(row["uri"] for row in navigation.label_assertions.get(uri, [])),
            *(row["uri"] for row in navigation.note_assertions.get(uri, [])),
            *(
                label_profiles_by_resource_uri[resource_uri]["uri"]
                for resource_uri in concept_label_resource_uris
            ),
            *(
                assignment["assertion_uri"]
                for relationship_key in (
                    "classified_instruments",
                    "instrument_classifications",
                )
                for relationship in relationships[relationship_key]
                for assignment in relationship["classification_assignments"]
            ),
        }
        record = {
            "uri": uri,
            "kind": concept["kind"],
            "local_id": concept["local_id"],
            "mimo_id": concept.get("mimo_id"),
            "scheme_uri": concept["scheme_uri"],
            "notation": concept.get("notation"),
            "definition": concept.get("definition"),
            "created": concept.get("created"),
            "resolution_status": concept["resolution_status"],
            "labels": _group_labels(navigation.labels.get(uri, [])),
            "label_resources": sorted(
                (
                    label_resources_by_uri[resource_uri]
                    for resource_uri in concept_label_resource_uris
                ),
                key=lambda row: row["uri"],
            ),
            "label_profiles": sorted(
                (
                    label_profiles_by_resource_uri[resource_uri]
                    for resource_uri in concept_label_resource_uris
                ),
                key=lambda row: row["uri"],
            ),
            "assertions": {
                "labels": sorted(
                    navigation.label_assertions.get(uri, []),
                    key=lambda row: row["uri"],
                ),
                "notes": sorted(
                    navigation.note_assertions.get(uri, []),
                    key=lambda row: row["uri"],
                ),
            },
            "relationships": relationships,
            "quality_findings": sorted(
                findings_by_concept.get(uri, []), key=lambda row: row["uri"]
            ),
            "review_events": sorted(
                (
                    row
                    for row in dataset.review_events
                    if row["target_assertion_uri"] in review_targets
                ),
                key=lambda row: row["uri"],
            ),
            "provenance": {
                "source_uri": uri,
                "source_retrieved_at": dataset.metadata["source_retrieved_at"],
                "dataset_version": dataset.metadata["dataset_version"],
                "dataset_doi": dataset.metadata["doi"],
                "dataset_sources": dataset.metadata["sources"],
                "source_relation_layer": "source_relations.jsonl",
                "classification_assertion_layer": ("classification_assertions.jsonl"),
                "concept_relation_assertion_layer": (
                    "concept_relation_assertions.jsonl"
                ),
                "concept_scheme_registry": "concept_schemes.jsonl",
                "perspective_registry": "perspectives.jsonl",
                "applicability_scope_registry": "applicability_scopes.jsonl",
                "authority_assignment_registry": "authority_assignments.jsonl",
                "projection_policy_registry": "projection_policies.jsonl",
                "label_assertion_layer": "label_assertions.jsonl",
                "label_resource_layer": "label_resources.jsonl",
                "label_profile_layer": "label_profiles.jsonl",
                "note_assertion_layer": "note_assertions.jsonl",
                "agent_registry": "agents.jsonl",
                "source_registry": "source_records.jsonl",
                "review_status_registry": "review_statuses.jsonl",
                "quality_rule_registry": "quality_rules.jsonl",
                "quality_finding_layer": "quality_findings.jsonl",
                "review_event_layer": "review_events.jsonl",
                "language_registry": dataset.language_registries[0],
                "script_registry": dataset.script_registries[0],
            },
        }
        record["retrieval_text"] = _retrieval_text(navigation, concept, relationships)
        rows.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in sorted(rows, key=lambda value: value["uri"]):
            handle.write(canonical_json(row))
    return len(rows)
