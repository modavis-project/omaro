#!/usr/bin/env python3
"""Build the deterministic OMARO 0.1 expert-evaluation packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from rdflib import Graph
from rdflib.compare import to_isomorphic


PACKET_NAME = "omaro-expert-evaluation-2026-09-06"
ZIP_TIMESTAMP = (2026, 9, 6, 0, 0, 0)
ONTOLOGY_VERSION = "0.1.0"
SCHEMA_VERSION = "0.1.0"
DATASET_VERSION = "0.1.0"
SQLITE_USER_VERSION = 20200

DOCUMENTS = (
    "AUTHORS.md",
    "EXPERT_REVIEW_GUIDE.md",
    "EXTERNAL_REVIEW_DECISIONS.md",
    "RELATED_WORK.md",
    "ORGANOLOGICAL_FOUNDATIONS.md",
    "ORGANOLOGICAL_MODEL.md",
    "INTEROPERABILITY_PROFILES.md",
    "MULTIPERSPECTIVITY.md",
    "ONTOLOGY_REFERENCE.md",
    "INFERENCE_AND_VALIDATION.md",
    "USE_CASES.md",
    "NAMING_AND_IDENTITY.md",
    "W3ID_REGISTRATION.md",
    "COMPETENCY_QUESTIONS.md",
    "DECOLONIAL_COMMITMENTS.md",
    "CULTURAL_GOVERNANCE.md",
    "MODAVIS_VAO_INTEROPERABILITY.md",
    "DATA_DICTIONARY.md",
    "GOVERNANCE.md",
    "REVIEW_PROTOCOL.md",
    "IMPLEMENTATION_VERIFICATION.md",
    "PROVENANCE.md",
    "QUALITY_REPORT.md",
    "README.md",
    "RELEASE_NOTES.md",
    "CHANGELOG.md",
    "CORRECTIONS.md",
    "CONTRIBUTING.md",
    "SUPPORT.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "CITATION.cff",
    "NOTICE",
    "RELEASE_STATUS.md",
    "VERSION",
    "codemeta.json",
    "LICENSE",
)

CANONICAL_REGISTRIES = (
    "metadata.json",
    "agents.jsonl",
    "source_records.jsonl",
    "concept_schemes.jsonl",
    "perspectives.jsonl",
    "applicability_scopes.jsonl",
    "authority_assignments.jsonl",
    "projection_policies.jsonl",
    "review_events.jsonl",
    "concept_relation_assertions.jsonl",
    "review_statuses.jsonl",
    "quality_rules.jsonl",
    "classification_criteria.jsonl",
    "classification_expressions.jsonl",
    "observation_assessments.jsonl",
    "organological_targets.jsonl",
    "protocol_applications.jsonl",
    "use_decisions.jsonl",
    "language_registries.jsonl",
    "script_registries.jsonl",
)

IMPLEMENTATION_FILES = (
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-lock.txt",
    "scripts/migrate_related_work.py",
    "scripts/release_check.py",
    "scripts/build_expert_review_packet.py",
    "src/omaro/__init__.py",
    "src/omaro/model.py",
    "src/omaro/builder.py",
    "src/omaro/knowledge_exports.py",
    "src/omaro/refresh.py",
    "src/omaro/ro_crate.py",
    "src/omaro/language_registry.py",
    "src/omaro/script_registry.py",
    "src/omaro/cli.py",
    "src/omaro/query.py",
)

TEST_FILES = (
    "tests/conftest.py",
    "tests/test_model.py",
    "tests/test_inference_contract.py",
    "tests/test_query.py",
    "tests/test_conformance.py",
    "tests/test_build.py",
    "tests/test_compound_expression_coherence.py",
    "tests/test_expert_packet.py",
    "tests/test_omaro_22_semantics.py",
    "tests/test_ro_crate.py",
    "tests/test_script_registry.py",
)

W3ID_FILES = (
    "w3id/modavis/omaro/.htaccess",
    "w3id/modavis/omaro/README.md",
)

ONTOLOGY_FILES = (
    "index.html",
    "omaro.ttl",
    "omaro.jsonld",
    "omaro.rdf",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_file(repo_root: Path, staging: Path, source: str, target: str) -> None:
    source_path = repo_root / source
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    target_path = staging / target
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)


def copy_directory(repo_root: Path, staging: Path, source: str, target: str) -> None:
    source_path = repo_root / source
    if not source_path.is_dir():
        raise FileNotFoundError(source_path)
    target_path = staging / target
    shutil.copytree(source_path, target_path)


def write_assignment_examples(repo_root: Path, staging: Path) -> None:
    source = repo_root / "data/canonical/classification_assertions.jsonl"
    examples = source.read_text(encoding="utf-8").splitlines()[:5]
    if len(examples) != 5:
        raise ValueError("canonical classification assertion sample requires five rows")
    target = staging / "examples/five-current-source-assertion-envelopes.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(examples) + "\n", encoding="utf-8")


def write_core_ontology(repo_root: Path, staging: Path) -> None:
    ontology_dir = repo_root / "dist/ontology" / ONTOLOGY_VERSION
    missing = [name for name in ONTOLOGY_FILES if not (ontology_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"missing OMARO ontology {ONTOLOGY_VERSION} files: {', '.join(missing)}; "
            "run omaro build first"
        )
    graphs = [
        Graph().parse(ontology_dir / "omaro.ttl", format="turtle"),
        Graph().parse(ontology_dir / "omaro.jsonld", format="json-ld"),
        Graph().parse(ontology_dir / "omaro.rdf", format="xml"),
    ]
    if not all(
        to_isomorphic(graph) == to_isomorphic(graphs[0]) for graph in graphs[1:]
    ):
        raise ValueError("versioned OMARO ontology representations are not isomorphic")
    for name in ONTOLOGY_FILES:
        copy_file(
            repo_root,
            staging,
            f"dist/ontology/{ONTOLOGY_VERSION}/{name}",
            f"ontology/{ONTOLOGY_VERSION}/{name}",
        )
    target = staging / "ontology/omaro-core.ttl"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ontology_dir / "omaro.ttl", target)


def write_manifest(staging: Path) -> None:
    files = sorted(path for path in staging.rglob("*") if path.is_file())
    lines = [
        f"{sha256(path)}  {path.relative_to(staging).as_posix()}" for path in files
    ]
    (staging / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_packet_metadata(staging: Path) -> None:
    example_dir = staging / "examples/organological-assessment"
    example_manifest = json.loads(
        (example_dir / "manifest.json").read_text(encoding="utf-8")
    )
    record_type_by_file: dict[str, str] = {}
    for entry in example_manifest.get("files", []):
        filename = entry.get("path")
        schema_name = PurePosixPath(entry.get("schema", "")).name
        if (
            not isinstance(filename, str)
            or PurePosixPath(filename).name != filename
            or not filename.endswith(".jsonl")
            or not schema_name.endswith(".schema.json")
        ):
            raise ValueError("invalid illustrative JSONL manifest entry")
        if filename in record_type_by_file:
            raise ValueError(f"duplicate illustrative JSONL manifest entry: {filename}")
        record_type_by_file[filename] = schema_name.removesuffix(".schema.json")

    actual_files = {path.name for path in example_dir.glob("*.jsonl") if path.is_file()}
    if actual_files != set(record_type_by_file):
        raise ValueError("illustrative JSONL inventory differs from its manifest")

    records_by_file: dict[str, int] = {}
    records_by_type: dict[str, int] = {}
    for filename in sorted(record_type_by_file):
        count = 0
        for line_number, line in enumerate(
            (example_dir / filename).read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid illustrative JSON in {filename}:{line_number}"
                ) from exc
            if not isinstance(record, dict):
                raise ValueError(
                    f"illustrative JSONL record is not an object: "
                    f"{filename}:{line_number}"
                )
            count += 1
        record_type = record_type_by_file[filename]
        if record_type in records_by_type:
            raise ValueError(f"duplicate illustrative record type: {record_type}")
        records_by_file[filename] = count
        records_by_type[record_type] = count

    metadata = {
        "packet": PACKET_NAME,
        "created": "2026-09-06",
        "ontology_version": ONTOLOGY_VERSION,
        "dataset_version": DATASET_VERSION,
        "schema_version": SCHEMA_VERSION,
        "sqlite_user_version": SQLITE_USER_VERSION,
        "purpose": "Independent conceptual, schema, implementation, and governance evaluation",
        "illustrative_jsonl_records": sum(records_by_file.values()),
        "illustrative_jsonl_records_by_file": records_by_file,
        "illustrative_jsonl_records_by_type": records_by_type,
        "illustrative_bundle_is_canonical": False,
        "illustrative_bundle_is_empirical": False,
        "illustrative_bundle_establishes_community_authorization": False,
        "multidimensional_comparison_fixture": (
            "examples/multidimensional-analysis/scalogram.json"
        ),
        "multidimensional_fixture_is_normative_core_schema": False,
        "canonical_source_assertion_samples": 5,
        "full_release_build_reproducible_from_packet": False,
        "omissions": [
            "bulk concepts, labels, notes, source relations, classification assertions, and quality findings",
            "full generated RDF/SQLite/site/OKF/RAG distributions",
        ],
        "entrypoint": "EXPERT_REVIEW_GUIDE.md",
    }
    (staging / "PACKET_METADATA.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_packet(repo_root: Path, output: Path) -> Path:
    with tempfile.TemporaryDirectory(prefix="omaro-expert-packet-") as directory:
        staging = Path(directory) / PACKET_NAME
        staging.mkdir()
        for name in DOCUMENTS:
            copy_file(repo_root, staging, name, name)
        for name in CANONICAL_REGISTRIES:
            copy_file(
                repo_root,
                staging,
                f"data/canonical/{name}",
                f"canonical-registries/{name}",
            )
        for path in sorted((repo_root / "schema").iterdir()):
            if path.is_file() and path.suffix in {".json", ".ttl"}:
                copy_file(
                    repo_root,
                    staging,
                    path.relative_to(repo_root).as_posix(),
                    path.relative_to(repo_root).as_posix(),
                )
        for path in sorted((repo_root / "conformance").iterdir()):
            if path.is_file():
                copy_file(
                    repo_root,
                    staging,
                    path.relative_to(repo_root).as_posix(),
                    path.relative_to(repo_root).as_posix(),
                )
        for name in IMPLEMENTATION_FILES:
            copy_file(repo_root, staging, name, f"implementation/{name}")
        for name in TEST_FILES:
            copy_file(repo_root, staging, name, name)
        for name in W3ID_FILES:
            copy_file(repo_root, staging, name, name)
        copy_directory(repo_root, staging, "examples", "examples")
        write_assignment_examples(repo_root, staging)
        write_core_ontology(repo_root, staging)
        write_packet_metadata(staging)
        write_manifest(staging)

        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(
            output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for path in sorted(staging.rglob("*")):
                if not path.is_file():
                    continue
                name = f"{PACKET_NAME}/{path.relative_to(staging).as_posix()}"
                info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes())
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    output = (
        args.output.resolve()
        if args.output is not None
        else repo_root / f"{PACKET_NAME}.zip"
    )
    result = build_packet(repo_root, output)
    print(
        json.dumps(
            {
                "path": str(result),
                "bytes": result.stat().st_size,
                "sha256": sha256(result),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
