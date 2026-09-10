import hashlib
import json
import shutil

import pytest

from omaro.compatibility import copy_historical_ontologies


def test_preserves_historical_documents(repo_root, tmp_path):
    source = repo_root / "site/compatibility"
    copy_historical_ontologies(source, tmp_path)
    directory = source / "ontology/2.2.0"
    for path in directory.iterdir():
        assert (
            tmp_path / "ontology/2.2.0" / path.name
        ).read_bytes() == path.read_bytes()


def test_rejects_changed_historical_document(repo_root, tmp_path):
    source = tmp_path / "source"
    shutil.copytree(repo_root / "site/compatibility", source)
    (source / "ontology/2.2.0/omaro.ttl").write_text("changed")
    with pytest.raises(ValueError, match="differs"):
        copy_historical_ontologies(source, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_cannot_replace_current_ontology(repo_root, tmp_path):
    target = tmp_path / "ontology/2.2.0"
    target.mkdir(parents=True)
    with pytest.raises(ValueError, match="must not replace"):
        copy_historical_ontologies(repo_root / "site/compatibility", tmp_path)


def test_version_and_term_identities(repo_root):
    from rdflib import Graph, OWL, RDF, URIRef

    directory = repo_root / "site/compatibility/ontology/2.2.0"
    manifest = json.loads((directory / "manifest.json").read_text())
    for row in manifest["files"]:
        assert (
            hashlib.sha256((directory / row["path"]).read_bytes()).hexdigest()
            == row["sha256"]
        )
    graph = Graph().parse(directory / "omaro.ttl")
    ontology = URIRef("https://w3id.org/modavis/omaro/ontology")
    assert graph.value(ontology, OWL.versionIRI) == URIRef(str(ontology) + "/2.2.0")
    assert (
        URIRef("https://w3id.org/modavis/omaro#Perspective"),
        RDF.type,
        OWL.Class,
    ) in graph
