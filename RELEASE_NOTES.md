# OMARO Reference Dataset 0.1.0

OMARO is the Ontology for Multiperspectivity, Assertions, and Review in
Organology, developed as part of the MODAVIS PhD project. This initial release
includes the ontology, a MIMO-derived reference dataset, an offline vocabulary
browser, examples, and tools for validation, export and querying.

The dataset contains 643 Hornbostel–Sachs classifications, 2,724 resolved
instrument concepts and five unresolved references. Its 42,662 labels retain
the source wording and provenance. Classification assertions record their
perspective, scope and review status separately from the source statements.

Distributions include JSONL, CSV, Turtle, JSON-LD, RDF/XML and SQLite, with
checksums and provenance metadata. See [README.md](README.md) for installation
and use, [USE_CASES.md](USE_CASES.md) for queries, and
[ONTOLOGY_REFERENCE.md](ONTOLOGY_REFERENCE.md) for the vocabulary.

The ontology, canonical schema, reference dataset and tooling are released as
**0.1.0**. The internal SQLite format remains **20200**. Historical 2.2.0
ontology documents are retained for existing MODAVIS reference snapshots.
The reproducible build uses Python 3.13.13; consumers need Python 3.11 or newer.

## Scope and limitations

This is a derived source snapshot, not an official MIMO release. The source
refresh updates the known concept inventory represented by the repository and
follows relations returned for those concepts; it does not independently prove
that every newly added upstream concept has been discovered. Five source-mapping target
URIs did not resolve during source retrieval and are retained as explicit stubs.
Source text is preserved rather than silently corrected, and known anomalies are
reported in the quality outputs.

All 42,662 source label assertions, 643 note assertions, and 42,662 linguistic
profiles remain `unreviewed`. The 1,872 source-derived classification
assertion envelopes identify both an assertion entity and its generating
assignment activity under the MIMO source perspective and the `source-silent`
scope. There are 26 mechanically tokenized compound expressions, zero
contributed organological targets, criteria, or observation assessments, zero cultural
protocol applications or use decisions, zero evidence-bearing human/community
review events, and therefore zero direct project-endorsed classifications.
The 9,445 automated findings are review signals with `review_effect: none`, not
corrections or judgments of cultural invalidity. Unicode Script observations
describe characters only. They do not establish language, dialect,
transliteration, community preference, or cultural validity.

The release contains vocabulary metadata only. It contains no musical-instrument
images, audio, segmentation masks, or other media.

## Citation

Use the version-specific Zenodo DOI after publication:
`10.5281/zenodo.21442777`. The DOI is reserved while the deposition remains a
draft and will not resolve until the maintainer completes the publication gate.

See `CITATION.cff`, `PROVENANCE.md`, `QUALITY_REPORT.md`, and `CHANGELOG.md` for
complete citation, rights, provenance, quality, and change information.
