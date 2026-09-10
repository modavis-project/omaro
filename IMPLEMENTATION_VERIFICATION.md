# Verification

OMARO is checked at four levels: canonical validation, semantic constraints,
complete cross-format projection, and reproducible release packaging.

The reference corpus passed all 158 tests with Python 3.13.13 and the locked
dependencies on 8 September 2026. This result predates the final documentation
and website preparation. It is not a claim that external publication is complete.
The repository workflows provide verification of the current revision.

The suite checks stable identifiers, source preservation, applicability and
review semantics, publication authorization, complete RDF/CSV/JSONL/SQLite
agreement, independent-process reproducibility, and archive contents and
checksums. RDF isomorphism comparisons include the entire graphs; formats are
loaded sequentially to limit peak memory.

Run the following from the repository root after installing the locked dependencies:

```sh
omaro validate
omaro build
ruff check src tests scripts
ruff format --check src tests scripts
pytest -q
omaro package
python scripts/release_check.py
```

On Linux verify the archive and sidecar with `sha256sum --check SHA256SUMS`;
on macOS use `shasum -a 256 -c SHA256SUMS`.

The separate field guide has Node and Python tests under `explainer/tests`.
Its examples distinguish synthetic demonstrations from source assertions.
Automated checks establish structural consistency and reproducibility;
empirical claims and community review require their own evidence.

CI runs the complete test collection in four groups. Corpus builds run in separate
processes so later tests do not inherit their allocator footprint. The final
artifact requires successful coverage receipts for every collected test; failures,
skips, omissions and duplicate receipts are rejected. Run the same checks locally
with `python scripts/run_tests.py`, or inspect the groups with `--plan`.
