#!/usr/bin/env python3
"""Prepare the browser and linked downloads within the GitHub Pages size limit."""

from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import tempfile
from urllib.parse import unquote, urljoin, urlsplit


MAX_SITE_BYTES = 900_000_000
DIRECTORIES = {"csv", "dataset", "legacy", "metadata", "ontology", "schema", "sqlite"}
BROWSER_FILES = {"index.html", "app.js", "styles.css"}
ROOT_FILES = {
    "index.html",
    "app.js",
    "styles.css",
    "data.json",
    "favicon.svg",
    "quality-report.json",
    "quality-report.md",
}


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in {"href", "src"} and value:
                self.targets.append(value)


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def stage(
    source: Path, output: Path, max_bytes: int = MAX_SITE_BYTES,
    browser_source: Path | None = None,
) -> dict:
    source = source.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to replace an existing directory: {output}")
    manifest = json.loads((source / "manifest.json").read_text())
    for key in ("dataset_version", "schema_version"):
        if not re.fullmatch(r"\d+\.\d+\.\d+", manifest[key]):
            raise ValueError(f"Invalid {key}")
    selected: dict[str, dict] = {}
    for row in manifest["files"]:
        relative = PurePosixPath(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe manifest path: {relative}")
        if relative.parts[0] not in DIRECTORIES and str(relative) not in ROOT_FILES:
            continue
        path = source / relative
        if path.is_symlink() or not path.resolve().is_relative_to(source):
            raise ValueError(f"Symlink outside the publication tree: {relative}")
        if str(relative) in selected:
            raise ValueError(f"Duplicate manifest path: {relative}")
        if path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
            raise ValueError(f"File differs from the verified release: {relative}")
        selected[str(relative)] = row
    required = {"index.html", "app.js", "styles.css", "data.json", "favicon.svg"}
    for directory, version in (
        ("dataset", manifest["dataset_version"]),
        ("ontology", manifest["schema_version"]),
    ):
        required.update(
            f"{directory}/{version}/{filename}"
            for filename in ("index.html", "omaro.ttl", "omaro.jsonld", "omaro.rdf")
        )
    if missing := required - selected.keys():
        raise ValueError(f"Missing browser or W3ID targets: {sorted(missing)}")
    paths = {name: source / name for name in selected}
    browser_updates = []
    if browser_source is not None:
        browser_source = browser_source.resolve()
        for name in sorted(BROWSER_FILES):
            path = browser_source / name
            if path.is_symlink() or not path.resolve().is_relative_to(browser_source):
                raise ValueError(f"Symlink outside the browser source: {name}")
            row = {"path": name, "bytes": path.stat().st_size, "sha256": digest(path)}
            browser_updates.append({**row, "release_sha256": selected[name]["sha256"]})
            selected[name] = row
            paths[name] = path
    for name in selected:
        if not name.endswith(".html"):
            continue
        parser = Links()
        parser.feed(paths[name].read_text())
        for target in parser.targets:
            resolved = urlsplit(urljoin("https://pages.invalid/" + name, target))
            if resolved.netloc != "pages.invalid":
                continue
            path = posixpath.normpath(unquote(resolved.path)).lstrip("/")
            if resolved.path.endswith("/") or path == ".":
                path = (path.rstrip("/") + "/index.html").lstrip("./")
            if path not in selected:
                raise ValueError(f"Broken local page link in {name}: {target}")
    site = {
        "scope": "GitHub Pages browser and linked downloads",
        "dataset_version": manifest["dataset_version"],
        "schema_version": manifest["schema_version"],
        "release_manifest_sha256": digest(source / "manifest.json"),
        "complete_release": f"https://github.com/modavis-project/omaro/releases/tag/v{manifest['dataset_version']}",
        "files": [selected[name] for name in sorted(selected)],
    }
    if browser_source is not None:
        site["browser_updates"] = browser_updates
    encoded = (json.dumps(site, ensure_ascii=False, indent=2) + "\n").encode()
    total = sum(row["bytes"] for row in selected.values()) + len(encoded)
    if total > max_bytes:
        raise ValueError(f"Pages site needs {total} bytes; budget is {max_bytes}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pages-stage-", dir=output.parent) as tmp:
        staging = Path(tmp) / "site"
        staging.mkdir()
        for name, row in selected.items():
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(paths[name], target)
            if digest(target) != row["sha256"]:
                raise ValueError(f"Copied page file failed verification: {name}")
        (staging / "site-manifest.json").write_bytes(encoded)
        (staging / ".nojekyll").touch()
        if output.exists():
            raise FileExistsError(
                f"Publication directory appeared during staging: {output}"
            )
        staging.rename(output)
    return {"status": "passed", "bytes": total, "files": len(selected) + 2}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("dist"))
    parser.add_argument("--output", type=Path, default=Path(".pages-site"))
    parser.add_argument(
        "--browser-source", type=Path,
        help="Use maintained index.html, app.js and styles.css; keep all released data unchanged",
    )
    args = parser.parse_args()
    print(json.dumps(stage(args.source, args.output, browser_source=args.browser_source)))
