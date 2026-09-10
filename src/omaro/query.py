"""Publication-checked, occurrence-preserving offline classification queries."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .model import Dataset, ValidationError


def query_classifications(
    dataset: Dataset,
    *,
    target_uri: str | None = None,
    search: str | None = None,
    context: dict[str, Any] | None = None,
    limit: int = 20,
    schema_dir: Path | None = None,
) -> dict[str, Any]:
    """Return qualified claims and their endorsement explanations.

    Search is Unicode case-insensitive literal substring matching, not an
    identity, language, or similarity inference. Limits apply to targets;
    all classification occurrences for each returned target are retained.
    """
    # Check before any lookup, count, validation diagnostic, or serialization.
    # Query context is epistemic context; it cannot grant publication access.
    dataset.assert_publication_authorized()
    if (target_uri is None) == (search is None):
        raise ValidationError("supply exactly one of target_uri or search")
    if search is not None and not search.strip():
        raise ValidationError("search must contain non-whitespace text")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
        raise ValidationError("limit must be an integer from 1 to 100")
    schemas = schema_dir or dataset.root.parent.parent / "schema"
    if context is not None:
        schema = json.loads((schemas / "query_context.schema.json").read_text())
        if not Draft202012Validator(schema, format_checker=FormatChecker()).is_valid(
            context
        ):
            raise ValidationError(
                "invalid query context: use documented URI dimensions and timezone-qualified at/as_of datetimes"
            )
        # RFC 3339 permits lowercase t/z; the model uses Python's ISO parser.
        context = {
            key: value.upper() if key in {"at", "as_of"} else value
            for key, value in context.items()
        }
    dataset.validate(schemas)

    targets = {row["uri"]: row for row in dataset.concepts}
    targets.update({row["uri"]: row for row in dataset.organological_targets})
    labels: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in dataset.labels:
        labels[row["concept_uri"]].append(row)
    if target_uri is not None:
        matched = [target_uri] if target_uri in targets else []
    else:
        needle = search.strip().casefold()
        matched = sorted(
            uri
            for uri, target in targets.items()
            if needle in target.get("label", "").casefold()
            or any(needle in row["label"].casefold() for row in labels[uri])
        )
    claims: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in dataset.classification_assertions:
        claims[row["target_uri"]].append(row)
    results = []
    for uri in matched[:limit]:
        occurrences = []
        for claim in sorted(claims[uri], key=lambda row: row["uri"]):
            occurrences.append(
                {
                    "claim": claim,
                    "classification": targets[claim["classification_uri"]],
                    "research_included": dataset.claim_applies_in_context(
                        claim, context or {}
                    ),
                    "endorsement": dataset.explain_endorsement(claim, context),
                }
            )
        results.append(
            {
                "target": targets[uri],
                "labels": sorted(
                    labels[uri],
                    key=lambda row: (row["language"], row["label_type"], row["label"]),
                ),
                "classification_occurrences": occurrences,
            }
        )
    return {
        "dataset_uri": dataset.metadata["dataset_uri"],
        "dataset_version": dataset.metadata["dataset_version"],
        "ontology_version_iri": dataset.metadata["ontology_version_iri"],
        "context": context,
        "evaluation_mode": "direct" if context is None else "contextual",
        "matched_target_count": len(matched),
        "returned_target_count": len(results),
        "truncated": len(matched) > limit,
        "results": results,
    }
