from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

import pytest

from omaro.ro_crate import (
    CULTURAL_AUTHORIZATION_NOTICE,
    DEFAULT_PATH_SPECS,
    RO_CRATE_CONTEXT,
    RO_CRATE_METADATA_NAME,
    RO_CRATE_PROFILE,
    CratePath,
    build_ro_crate_document,
    render_ro_crate_metadata,
    write_ro_crate_metadata,
)


@pytest.fixture
def release_root(tmp_path: Path) -> Path:
    root = tmp_path / "omaro-v0.1.0"
    root.mkdir()
    for spec in DEFAULT_PATH_SPECS:
        path = root.joinpath(*PurePosixPath(spec.path.rstrip("/")).parts)
        if spec.is_directory:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"fixture for {spec.path}\n", encoding="utf-8")
    return root


@pytest.fixture
def dataset_metadata() -> dict:
    return {
        "name": "OMARO",
        "title": (
            "OMARO Reference Dataset: Hornbostel–Sachs Classifications and "
            "Multilingual Musical Instrument Names"
        ),
        "dataset_version": "0.1.0",
        "schema_version": "0.1.0",
        "dataset_uri": "https://w3id.org/modavis/omaro/dataset/0.1.0",
        "doi": "10.5281/zenodo.21442777",
        "repository_uri": "https://github.com/modavis-project/omaro",
        "license": "CC0-1.0",
        "ontology_title": (
            "Ontology for Multiperspectivity, Assertions, and Review in Organology"
        ),
        "ontology_uri": "https://w3id.org/modavis/omaro/ontology",
        "ontology_version_iri": "https://w3id.org/modavis/omaro/ontology/0.1.0",
        "creators": [
            {
                "name": "Dominik Ukolov",
                "affiliations": [
                    "Research Group DIGITAL ORGANOLOGY, Leipzig University",
                    (
                        "Digital Humanities (Image/Object), "
                        "Friedrich Schiller University Jena"
                    ),
                ],
            }
        ],
        "sources": [
            "https://vocabulary.mimo-international.com/rest/v1/HornbostelAndSachs",
            "https://vocabulary.mimo-international.com/rest/v1/InstrumentsKeywords",
        ],
    }


def _entity_index(document: dict) -> dict[str, dict]:
    return {entity["@id"]: entity for entity in document["@graph"]}


def _reachable_local_ids(index: dict[str, dict]) -> set[str]:
    reached: set[str] = set()
    pending = [reference["@id"] for reference in index["./"]["hasPart"]]
    while pending:
        entity_id = pending.pop()
        if entity_id in reached:
            continue
        reached.add(entity_id)
        pending.extend(
            reference["@id"] for reference in index[entity_id].get("hasPart", [])
        )
    return reached


def test_ro_crate_13_structure_and_local_topology(
    release_root: Path, dataset_metadata: dict
):
    document = build_ro_crate_document(
        release_root, dataset_metadata, release_date="2026-08-30"
    )
    assert document["@context"] == RO_CRATE_CONTEXT
    assert len(document["@graph"]) < 100

    ids = [entity["@id"] for entity in document["@graph"]]
    assert len(ids) == len(set(ids))
    index = _entity_index(document)
    descriptor = index[RO_CRATE_METADATA_NAME]
    assert descriptor == {
        "@id": RO_CRATE_METADATA_NAME,
        "@type": "CreativeWork",
        "about": {"@id": "./"},
        "conformsTo": {"@id": RO_CRATE_PROFILE},
        "description": "RO-Crate Metadata Descriptor for the OMARO release.",
    }
    assert index["./"]["@type"] == "Dataset"

    represented_ids = {spec.path for spec in DEFAULT_PATH_SPECS}
    assert _reachable_local_ids(index) == represented_ids
    for spec in DEFAULT_PATH_SPECS:
        entity = index[spec.path]
        local_path = release_root.joinpath(*PurePosixPath(spec.path.rstrip("/")).parts)
        assert local_path.exists()
        if spec.is_directory:
            assert entity["@type"] == "Dataset"
            assert "contentSize" not in entity
            assert "encodingFormat" not in entity
        else:
            assert entity["@type"] == "File"
            assert entity["contentSize"] == str(local_path.stat().st_size)
            assert entity["encodingFormat"]


def test_ro_crate_metadata_matches_the_release_identity(
    release_root: Path, dataset_metadata: dict
):
    index = _entity_index(
        build_ro_crate_document(
            release_root, dataset_metadata, release_date="2026-08-30"
        )
    )
    root = index["./"]
    doi_uri = "https://doi.org/10.5281/zenodo.21442777"
    dataset_uri = "https://w3id.org/modavis/omaro/dataset/0.1.0"
    assert root["name"] == dataset_metadata["title"]
    assert root["alternateName"] == "OMARO"
    assert root["version"] == "0.1.0"
    assert root["schemaVersion"] == "0.1.0"
    assert root["datePublished"] == "2026-08-30"
    assert root["identifier"] == [doi_uri, dataset_uri]
    assert root["url"] == dataset_uri
    assert root["sameAs"] == doi_uri
    assert root["license"] == {"@id": "https://spdx.org/licenses/CC0-1.0"}
    assert root["codeRepository"] == {"@id": dataset_metadata["repository_uri"]}
    assert {reference["@id"] for reference in root["isBasedOn"]} == set(
        dataset_metadata["sources"]
    )
    assert {reference["@id"] for reference in root["isRelatedTo"]} == {
        dataset_metadata["ontology_uri"],
        dataset_metadata["ontology_version_iri"],
    }
    assert root["mainEntityOfPage"] == {"@id": "README.md"}
    assert root["subjectOf"] == {"@id": "CULTURAL_GOVERNANCE.md"}

    creator = index["https://orcid.org/0000-0002-7904-3892"]
    assert root["creator"] == [{"@id": creator["@id"]}]
    assert creator["@type"] == "Person"
    assert creator["name"] == "Dominik Ukolov"
    assert len(creator["affiliation"]) == 2
    for reference in creator["affiliation"]:
        assert index[reference["@id"]]["@type"] == "Organization"

    for reference_key in ("license", "codeRepository"):
        assert root[reference_key]["@id"] in index
    for reference_key in ("creator", "isBasedOn", "isRelatedTo"):
        assert all(reference["@id"] in index for reference in root[reference_key])


def test_ro_crate_bytes_are_deterministic_and_do_not_describe_themselves(
    release_root: Path, dataset_metadata: dict
):
    first = render_ro_crate_metadata(
        release_root, dataset_metadata, release_date="2026-08-30"
    )
    target = write_ro_crate_metadata(
        release_root, dataset_metadata, release_date="2026-08-30"
    )
    assert target.name == RO_CRATE_METADATA_NAME
    assert target.read_bytes() == first
    assert (
        render_ro_crate_metadata(
            release_root, dataset_metadata, release_date="2026-08-30"
        )
        == first
    )

    document = json.loads(first)
    index = _entity_index(document)
    descriptor = index[RO_CRATE_METADATA_NAME]
    assert descriptor["@type"] == "CreativeWork"
    assert "contentSize" not in descriptor
    assert "sha256" not in descriptor
    assert RO_CRATE_METADATA_NAME not in _reachable_local_ids(index)


def test_licence_and_integrity_metadata_disclaim_cultural_authorization(
    release_root: Path, dataset_metadata: dict
):
    index = _entity_index(
        build_ro_crate_document(
            release_root, dataset_metadata, release_date="2026-08-30"
        )
    )
    root = index["./"]
    assert root["conditionsOfAccess"] == CULTURAL_AUTHORIZATION_NOTICE
    assert (
        "do not establish cultural authorization" in root["conditionsOfAccess"].lower()
    )
    assert (
        "does not establish cultural authorization"
        in index["https://spdx.org/licenses/CC0-1.0"]["description"].lower()
    )
    assert "does not establish" in index["dist/manifest.json"]["description"].lower()
    assert "cultural" in index["dist/manifest.json"]["description"].lower()
    assert (
        "does not establish"
        in index["examples/organological-assessment/manifest.json"][
            "description"
        ].lower()
    )

    text = json.dumps(index, ensure_ascii=False).lower()
    assert "cultural authorization granted" not in text
    assert "culturally authorized by" not in text


def test_generator_rejects_missing_or_unreachable_represented_paths(
    release_root: Path, dataset_metadata: dict
):
    missing = CratePath(
        "missing.json", "./", "Missing file", "A deliberately missing file."
    )
    with pytest.raises(FileNotFoundError, match="missing.json"):
        build_ro_crate_document(
            release_root,
            dataset_metadata,
            release_date="2026-08-30",
            path_specs=(missing,),
        )

    nested = release_root / "orphan"
    nested.mkdir()
    unreachable = CratePath(
        "orphan/", "unrepresented/", "Orphan", "An unreachable directory."
    )
    with pytest.raises(ValueError, match="unrepresented directory parent"):
        build_ro_crate_document(
            release_root,
            dataset_metadata,
            release_date="2026-08-30",
            path_specs=(unreachable,),
        )
