"""Build an isolated, publication-checked static OMARO field guide."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from omaro.model import Dataset
from omaro.query import query_classifications

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
TARGET = "http://www.mimo-db.eu/InstrumentsKeywords/3111"
DOCUMENTS = (
    "USE_CASES.md",
    "INFERENCE_AND_VALIDATION.md",
    "DATA_DICTIONARY.md",
    "ORGANOLOGICAL_MODEL.md",
    "CULTURAL_GOVERNANCE.md",
    "RELATED_WORK.md",
    "ONTOLOGY_REFERENCE.md",
    "MULTIPERSPECTIVITY.md",
    "REVIEW_PROTOCOL.md",
    "RELEASE_STATUS.md",
    "PROVENANCE.md",
)


def assert_teaching_contract(dataset: Dataset, result: dict, comparison: dict) -> None:
    """Reject source drift that would make the curated explanation misleading."""
    if (
        dataset.metadata["schema_version"] != "0.1.0"
        or dataset.metadata["dataset_version"] != "0.1.0"
        or len(dataset.perspectives) != 1
        or dataset.review_events
        or dataset.authority_assignments
        or dataset.protocol_applications
        or dataset.use_decisions
    ):
        raise ValueError(
            "The reference snapshot changed; review the field guide's capability and evidence statements."
        )
    targets = result["results"]
    if len(targets) != 1 or targets[0]["target"]["uri"] != TARGET:
        raise ValueError(
            "The teaching target changed; review the double-bass explanation."
        )
    rows = targets[0]["classification_occurrences"]
    expected_reasons = {
        "claim-not-in-policy",
        "ineligible-stance",
        "scope-not-context-independent",
        "required-review-missing",
        "insufficient-independent-reviewers",
    }
    if len(rows) != 3 or {row["classification"]["notation"] for row in rows} != {
        "321.322",
        "321.322-5",
        "321.322-71",
    }:
        raise ValueError(
            "The source classifications changed; review the teaching example."
        )
    for row in rows:
        if (
            row["endorsement"]["eligible"]
            or not row["research_included"]
            or set(row["endorsement"]["reason_codes"]) != expected_reasons
            or {scope["scope_mode"] for scope in row["endorsement"]["scopes"]}
            != {"source-silent"}
        ):
            raise ValueError(
                "The source claim's interpretation changed; review the field guide."
            )
    if (
        comparison["status"] != "synthetic-illustrative"
        or len(comparison["profiles"]) != 2
        or any(
            len(profile["dimension_uris"]) != 3 for profile in comparison["profiles"]
        )
        or comparison["method"]["minimum_comparable_dimensions"] != 3
        or comparison["method"]["distance_formula"]
        != "disagreements / comparable_dimensions"
    ):
        raise ValueError(
            "The comparison method changed; review the interactive lesson."
        )


def build() -> None:
    dataset = Dataset.load(ROOT / "data/canonical")
    # Fail before writing even a temporary output, including on query errors.
    result = query_classifications(dataset, target_uri=TARGET)
    comparison = json.loads(
        (ROOT / "examples/multidimensional-analysis/scalogram.json").read_text()
    )
    assert_teaching_contract(dataset, result, comparison)
    target = result["results"][0]
    payload = {
        "dataset_version": dataset.metadata["dataset_version"],
        "ontology_version": dataset.metadata["ontology_version_iri"].rsplit("/", 1)[-1],
        "generated_at": dataset.metadata["generated_at"],
        "dataset_uri": dataset.metadata["dataset_uri"],
        "status": "unpublished-candidate",
        "counts": {
            "concepts": len(dataset.concepts),
            "classification_occurrences": len(dataset.classification_assertions),
            "review_events": len(dataset.review_events),
        },
        "double_bass": target,
        "scopes": dataset.applicability_scopes,
        "sources": dataset.source_records,
        "perspectives": dataset.perspectives,
        "comparison": comparison,
    }
    with tempfile.TemporaryDirectory(prefix=".build-", dir=APP) as directory:
        stage = Path(directory)
        for name in (
            "index.html",
            "styles.css",
            "app.js",
            "model.js",
            "content.js",
            "favicon.svg",
        ):
            shutil.copyfile(APP / "src" / name, stage / name)
        (stage / ".nojekyll").touch()
        (stage / "data.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        reference = stage / "reference"
        reference.mkdir()
        for name in DOCUMENTS:
            shutil.copyfile(ROOT / name, reference / name)
        for name in ("double-bass.sql", "double-bass.rq", "arco-context.json"):
            shutil.copyfile(ROOT / "examples/queries" / name, reference / name)
        for name in ("query_context.schema.json", "dataset.shacl.ttl"):
            shutil.copyfile(ROOT / "schema" / name, reference / name)
        shutil.copyfile(
            ROOT / "examples/multidimensional-analysis/scalogram.json",
            reference / "scalogram.json",
        )
        shutil.copyfile(
            ROOT / "examples/multidimensional-analysis/README.md",
            reference / "COMPARISON.md",
        )
        shutil.copyfile(ROOT / "NOTICE", reference / "NOTICE")
        shutil.copyfile(ROOT / "LICENSE", reference / "LICENSE")
        manifest = {
            path.relative_to(stage).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(stage.rglob("*"))
            if path.is_file()
        }
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        output = APP / "dist"
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(stage, output)
    print(
        f"Built {len(manifest) + 1} static files in explainer/dist; publication and canonical validation passed."
    )


if __name__ == "__main__":
    build()
