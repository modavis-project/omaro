"""Publication checks independent of the corpus tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from stage_pages import stage


class PagesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "dist"
        self.output = self.root / "pages"
        self.source.mkdir()
        self.files = {
            "index.html": '<a href="dataset/0.1.0/omaro.ttl">RDF</a><a href="sqlite/omaro.sqlite">SQLite</a>',
            "app.js": "",
            "styles.css": "",
            "data.json": "{}",
            "favicon.svg": "",
            "sqlite/omaro.sqlite": "fixture",
            "rdf/omaro.ttl": "duplicate",
            "jsonl/concepts.jsonl": "bulk",
            "okf/index.md": "bulk",
        }
        for directory, version in (("dataset", "0.1.0"), ("ontology", "0.1.0")):
            for name in ("index.html", "omaro.ttl", "omaro.jsonld", "omaro.rdf"):
                self.files[f"{directory}/{version}/{name}"] = "fixture"
        self.write()

    def write(self) -> None:
        rows = []
        for name, text in self.files.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            data = path.read_bytes()
            rows.append(
                {
                    "path": name,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        (self.source / "manifest.json").write_text(
            json.dumps(
                {
                    "dataset_version": "0.1.0",
                    "schema_version": "0.1.0",
                    "files": rows,
                }
            )
        )

    def test_keeps_browser_downloads_and_w3id_targets_without_bulk_duplicates(
        self,
    ) -> None:
        result = stage(self.source, self.output)
        self.assertEqual(result["status"], "passed")
        self.assertTrue((self.output / "sqlite/omaro.sqlite").is_file())
        self.assertTrue((self.output / "dataset/0.1.0/omaro.ttl").is_file())
        for path in ("rdf", "jsonl", "okf", "manifest.json"):
            self.assertFalse((self.output / path).exists())
        self.assertTrue((self.output / "site-manifest.json").is_file())
        self.assertTrue((self.source / "rdf/omaro.ttl").is_file())

    def test_broken_download_link_prevents_publication(self) -> None:
        self.files["index.html"] = '<a href="missing.csv">Missing download</a>'
        self.write()
        with self.assertRaisesRegex(ValueError, "Broken local page link"):
            stage(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_modified_release_file_prevents_publication(self) -> None:
        (self.source / "app.js").write_text("unexpected")
        with self.assertRaisesRegex(ValueError, "differs from the verified release"):
            stage(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_oversized_site_is_rejected_before_copying(self) -> None:
        with self.assertRaisesRegex(ValueError, "budget"):
            stage(self.source, self.output, max_bytes=1)
        self.assertFalse(self.output.exists())

    def test_external_symlink_is_rejected(self) -> None:
        outside = self.root / "private.txt"
        outside.write_text("private")
        path = self.source / "app.js"
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            stage(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_missing_versioned_rdf_is_rejected(self) -> None:
        del self.files["dataset/0.1.0/omaro.jsonld"]
        self.write()
        with self.assertRaisesRegex(ValueError, "Missing browser or W3ID targets"):
            stage(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_site_is_preserved(self) -> None:
        self.output.mkdir()
        sentinel = self.output / "sentinel"
        sentinel.write_text("keep")
        with self.assertRaises(FileExistsError):
            stage(self.source, self.output)
        self.assertEqual(sentinel.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
