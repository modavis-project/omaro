"""Preserve historical ontology documents without relabelling their contents."""

import hashlib
import json
from pathlib import Path
import shutil


def copy_historical_ontologies(source: Path, output: Path) -> None:
    for manifest_path in sorted(source.glob("ontology/*/manifest.json")):
        directory = manifest_path.parent
        manifest = json.loads(manifest_path.read_text())
        if manifest["ontology_version"] != directory.name:
            raise ValueError("Historical ontology version differs from its directory")
        rows = manifest["files"]
        if {row["path"] for row in rows} != {
            "omaro.ttl",
            "omaro.jsonld",
            "omaro.rdf",
        } or len(rows) != 3:
            raise ValueError("Historical ontology requires three preserved RDF files")
        for row in rows:
            path = directory / row["path"]
            if path.is_symlink() or path.stat().st_size != row["bytes"]:
                raise ValueError("Historical ontology file differs from its manifest")
            if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError(
                    "Historical ontology checksum differs from its manifest"
                )
        target = output / "ontology" / directory.name
        if target.exists():
            raise ValueError(
                "Historical ontology must not replace the current ontology"
            )
        target.mkdir(parents=True)
        for name in ["index.html", "manifest.json", *(row["path"] for row in rows)]:
            shutil.copyfile(directory / name, target / name)
