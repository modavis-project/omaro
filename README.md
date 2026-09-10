# OMARO

**Ontology for Multiperspectivity, Assertions, and Review in Organology**

OMARO records organological statements together with their sources, scope and
review status. It provides an OWL ontology, validation tools and a reference
dataset derived from Musical Instrument Museums Online (MIMO).

The dataset contains 643 Hornbostel–Sachs classifications and 2,724 resolved
instrument concepts, with preferred and alternative labels in 13 languages.
Original identifiers and statements remain available alongside qualified
assertions. Five unresolved source references are retained explicitly.

Use the [browser](https://modavis-project.github.io/omaro/) to explore the
reference data when the site is published, or build it locally as described
below. [USE_CASES.md](USE_CASES.md) provides lookup, SQL and contextual review
examples. [ONTOLOGY_REFERENCE.md](ONTOLOGY_REFERENCE.md) documents the model;
[ORGANOLOGICAL_FOUNDATIONS.md](ORGANOLOGICAL_FOUNDATIONS.md) explains its
relationship to organological methods.

Dataset and tooling version **0.1.0** use ontology/schema **0.1.0**. Publication
is in preparation: DOI `10.5281/zenodo.21442777` is reserved, and the Pages and
W3ID routes are not yet active. See [RELEASE_STATUS.md](RELEASE_STATUS.md).

## Identity

| Resource | Canonical identifier |
|---|---|
| OMARO term namespace | `https://w3id.org/modavis/omaro#` |
| OMARO Ontology | `https://w3id.org/modavis/omaro/ontology` |
| Ontology version 0.1.0 | `https://w3id.org/modavis/omaro/ontology/0.1.0` |
| Reference Dataset 0.1.0 | `https://w3id.org/modavis/omaro/dataset/0.1.0` |
| Repository | `https://github.com/modavis-project/omaro` |

The ontology, reference dataset, and tooling are separately versioned. The
W3ID resolver configuration is staged in the repository and becomes active
only after upstream registration and public-target verification. See
[NAMING_AND_IDENTITY.md](NAMING_AND_IDENTITY.md) and
[W3ID_REGISTRATION.md](W3ID_REGISTRATION.md).

## Data at a glance

| Item | Count |
|---|---:|
| Hornbostel–Sachs classifications | 643 |
| Resolved instrument concepts | 2,724 |
| Unresolved source references | 5 |
| Preferred labels | 35,794 |
| Alternative labels | 6,868 |
| Assertion-scoped SKOS-XL label resources | 42,662 |
| Conservative linguistic label profiles | 42,662 |
| Qualified label assertions | 42,662 |
| Qualified note assertions | 643 |
| MIMO source relations | 5,228 |
| Source-derived classification assertion/assignment envelopes | 1,872 |
| Mechanically tokenized compound classification expressions | 26 |
| Contributed organological targets / observation assessments / criteria | 0 / 0 / 0 |
| Cultural protocol applications / use decisions | 0 / 0 |
| Concept schemes / perspectives / applicability scopes | 2 / 1 / 1 |
| Projection policies / authority assignments | 3 / 0 |
| Contributed qualified concept-relation assertions | 0 |
| Registered agents / versioned sources / review statuses | 2 / 2 / 5 |
| Automated review signals / human review events | 9,445 / 0 |
| Pinned IANA language registry | 2026-06-14 |
| Pinned Unicode Script data | 17.0.0 |
| Preferred-label languages | 13 |

See `QUALITY_REPORT.md` for the generated release report and known gaps.
The generated static explorer is available at `dist/index.html` and is prepared
for deployment through GitHub Pages after approval.

## Compatibility contract

| Interface | Release value |
|---|---|
| Dataset | `0.1.0` |
| OMARO Ontology | `0.1.0` |
| Canonical JSON Schema | `0.1.0` |
| SQLite `PRAGMA user_version` | `20200` |
| Open Knowledge Format profile | `0.2` |
| VAO exchange mapping | `0.4.0` classification object |
| MODAVIS relationship | `0.1.0` related standard; no conformance claim |
| Minimum supported Python | `3.11` |
| Reproducible release Python | `3.13.13` |

Consumers should use canonical URIs as identifiers and treat schema-major
changes as potentially breaking. `DATA_DICTIONARY.md` is the normative
field-level guide; `PROVENANCE.md`, `QUALITY_REPORT.md`, and
`RELEASE_NOTES.md` define source history, known limitations, and release scope.
Contributors and reviewers should also consult `CORRECTIONS.md`,
`GOVERNANCE.md`, `REVIEW_PROTOCOL.md`, `MULTIPERSPECTIVITY.md`,
`COMPETENCY_QUESTIONS.md`, `DECOLONIAL_COMMITMENTS.md`,
`CULTURAL_GOVERNANCE.md`, `RELATED_WORK.md`, `ORGANOLOGICAL_MODEL.md`,
`ORGANOLOGICAL_FOUNDATIONS.md`,
`INTEROPERABILITY_PROFILES.md`,
`MODAVIS_VAO_INTEROPERABILITY.md`,
`EXTERNAL_REVIEW_DECISIONS.md`, `IMPLEMENTATION_VERIFICATION.md`,
`NAMING_AND_IDENTITY.md`, `ONTOLOGY_REFERENCE.md`, `W3ID_REGISTRATION.md`,
`CONTRIBUTING.md`, and `SECURITY.md`
before proposing or publishing changes.

## Download formats

The canonical records live in `data/canonical`. All files in `dist` are
generated from that single model:

- normalized JSON Lines and RFC 4180 CSV tables;
- separate MIMO source relations and qualified classification, concept-relation,
  label, and note layers with scheme, agent, perspective, scope, authority,
  source, review, and projection-policy registries;
- non-collapsing SKOS-XL resources with compatibility SKOS literals and explicit
  suppression metadata for 89 source label-role conflicts;
- provenance-bearing linguistic profiles using pinned Unicode Script evidence
  without inferring languages or communities; SKOS-XL label resources are not
  typed as OntoLex forms without lexical-entry evidence;
- separate target, observation-assessment, actual-observation, criterion,
  assertion, assignment, review-event, review-decision, compound-expression,
  protocol-application, and use-decision semantics (the compact
  observation-assessment table carries the status that determines the RDF
  type);
- deterministic linguistic/documentation warning records and an
  evidence-bearing human/community review-event table;
- offline BCP 47 validation and canonicalization against a checksummed,
  dated IANA Language Subtag Registry snapshot;
- self-contained RAG JSONL with identity, multilingual labels, hierarchy,
  qualified classifications, provenance, and retrieval text in every concept record;
- an Open Knowledge Format (OKF) v0.2 bundle with curated guides,
  progressive indexes, and one linked Markdown page per concept;
- an enriched `classification-assignments.csv` for join-free, perspective-aware reuse;
- a compact OWL vocabulary in Turtle, JSON-LD, and RDF/XML at
  `dist/ontology/0.1.0/`, separate from the combined reference-dataset graph;
- OWL/SKOS reference-dataset RDF in Turtle, JSON-LD, and RDF/XML;
- a separate Turtle snapshot preserving MIMO's original mapping predicates;
- SQLite with relational views, precomputed ancestors, and multilingual FTS5 search;
- JSON Schema and SHACL validation shapes;
- DQV measurements with named metrics, explicit datatypes, denominators, and
  build provenance for dataset-quality interpretation—never as substitutes
  for organological or community review;
- DCAT 3 metadata distinguishing the maintained dataset, immutable release,
  and downloadable ZIP distribution, including an externally computed size
  and SHA-256 checksum;
- an attached RO-Crate 1.3 descriptor for offline discovery of the packaged
  dataset, documentation, examples, generated directories, and manifests;
- a VAO 0.4.0 classification example and conservative, versioned relation
  metadata for VAO and MODAVIS 0.1.0;
- the v1 compatibility exports `hornbostelSachs.json` and `translations.json`.

New integrations should use assertion, assignment, target, and concept URIs
rather than labels, target/class pairs, MIMO numeric IDs, or array positions. See
[DATA_DICTIONARY.md](DATA_DICTIONARY.md) for field details.

Generated release outputs (`dist/`, the ZIP, its external DCAT sidecar, and
`SHA256SUMS`) are deliberately ignored by Git. They are rebuilt from checked-in
canonical data, verified, and attached to GitHub and Zenodo only during an
approved release. This keeps source history reviewable without storing
duplicate binary artifacts.

The release ZIP contains only generated distributions, the attached RO-Crate
descriptor, worked examples, and the public-facing license, citation,
provenance, quality, correction, and usage documents needed to understand them.
Development source remains available in GitHub; tests, workflows, draft API
payloads, and private review or sign-off records are not duplicated in the
dataset archive.

## GitHub Pages

The Pages workflow publishes the browser, versioned RDF, schemas, metadata,
CSV and SQLite downloads. It omits duplicate RDF files and bulk JSONL and OKF
exports, which remain in the complete release archive. This keeps the website
within [GitHub Pages' 1 GB limit](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
without removing browser downloads.

`python scripts/stage_pages.py` verifies the selected files against the release
manifest, checks local HTML links, and rejects sites larger than 900 MB. Its
output is `.pages-site/`, with a separate `site-manifest.json`. The complete
release manifest remains in the distribution archive.

## Install and build

Python 3.11 or newer is supported. Reproducible release builds use Python
3.13.13 and the complete dependency lock file. The manifest and SQLite metadata
record the exact Python and SQLite versions used for each generated candidate.

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
.venv/bin/pip install --no-deps -e .
.venv/bin/omaro validate
.venv/bin/omaro query --target-uri http://www.mimo-db.eu/InstrumentsKeywords/3111
.venv/bin/omaro build
.venv/bin/pytest
```

The `validate`, `build`, and `package` commands are offline. Only the explicit
`refresh-source` command accesses MIMO, and it writes no canonical data unless
every requested record in the known inventory succeeds.

```bash
.venv/bin/omaro package
```

This creates `omaro-v0.1.0.zip`, the external
`omaro-v0.1.0.dcat.ttl` metadata sidecar, and `SHA256SUMS`. The checksum file
identifies both other artifacts. The ZIP contains `ro-crate-metadata.json` and
the generated DQV measurements at `dist/metadata/dqv.ttl`.

## Structured navigation and retrieval

Open `dist/okf/index.md` to navigate the dataset progressively without loading
all 3,372 concepts into context. The generated OKF bundle separates curated
interpretation guides from source-derived classification and instrument pages.
Every page retains its canonical concept URI and links explicitly to broader,
narrower, or classified concepts. OKF v0.2 concept frontmatter records sources,
generation, lifecycle status, and—where deterministic projection checks
apply—a machine-only verification event. That verification is not human domain
review and does not change an assertion's recorded review status.
The profile targets the
[official OKF v0.2 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).

For retrieval-augmented generation, index the `retrieval_text` field in
`dist/jsonl/rag-concepts.jsonl` and retain the full JSON object as document
metadata. Use `uri` as the document ID. Answers should be assembled from the
structured fields and return canonical URIs and the recorded dataset version.
Each record includes its complete qualified label and note assertions, the
referenced SKOS-XL resources, their linguistic profiles, and relevant quality
findings. Classification relationships retain every assignment occurrence,
including its perspective, scope, authority, evidence, stance, and projection
policies. Relevant non-collapsing review events are embedded with each concept;
an
`unreviewed` source assertion must not be described as linguistically,
culturally, or scholarly validated. `quality_findings` are machine-generated
review signals with no review effect; they must not be presented as corrections.

```python
import json

with open("dist/jsonl/rag-concepts.jsonl", encoding="utf-8") as records:
    castanets = next(
        json.loads(line)
        for line in records
        if '"notation":"111.141"' in line
    )

print(castanets["uri"])
print(castanets["relationships"]["ancestors"])
```

## Examples

The repository also includes two complete modeling aids:

- [`examples/organological-assessment/`](examples/organological-assessment/)
  contains schema-valid target, assessment, criterion, expression, assertion,
  protocol, authority, and use-decision records; and
- [`examples/multidimensional-analysis/`](examples/multidimensional-analysis/)
  contains a reproducible synthetic comparison in which the same tambourine
  configuration is closest to a frame drum under structural criteria and to a
  jingle ring under performed-sounding criteria.

Both are illustrative and remain outside the canonical reference dataset.

### Python and pandas

```python
import pandas as pd

labels = pd.read_csv("dist/csv/labels.csv")
german = labels.query("language == 'de' and label_type == 'preferred'")
print(german[german["label"].str.contains("Gitarre", case=False)])
```

### JavaScript

```javascript
import fs from "node:fs";

const concepts = fs.readFileSync("dist/jsonl/concepts.jsonl", "utf8")
  .trim()
  .split("\n")
  .map(JSON.parse);
const electrophones = concepts.find((c) => c.notation === "5");
console.log(electrophones.uri);
```

### SQLite: claims versus endorsed classifications

```sql
SELECT concept_uri, label
FROM preferred_labels
WHERE language = 'de' AND label = 'Signalhorn';

-- Research view: all qualified source and contributed assignments.
SELECT pl.label, c.notation, ca.stance, ca.perspective_uri,
       ca.applicability_scope_uris_json
FROM classification_claims cc
JOIN classification_assertions ca ON ca.uri = cc.assertion_uri
JOIN concepts c ON c.uri = cc.classification_uri
JOIN preferred_labels pl ON pl.concept_uri = cc.target_uri
WHERE pl.language = 'en' AND pl.label = 'Bugle';

-- Conservative direct view: only context-independent claims that opted into
-- the policy, passed two independent required reviews, and have no active veto.
-- It is currently empty.
SELECT * FROM classification_targets;
```

### Actual context-dependent mappings

The MIMO snapshot maps “Double bass” to the morphological class `321.322`, the
bare-finger realization `321.322-5`, and the bowed realization `321.322-71`.
It also maps “Alto trombone” to both slide labrosones `423.22` and
short-air-column valve labrosones `423.233.1`. These are useful, concrete cases
of playing-technique and instrument-configuration multiplicity; they must not
be flattened into claims that every object always belongs to every detailed
class.

The source occurrences remain under the MIMO perspective with `source-silent`
scope. A reviewed application models the double-bass alternatives either as
separate `sounding-realization` targets carrying
`actual_playing_technique_uris`, or as assertions whose referenced `specified`
scopes carry `playing_technique_uris`. It models the alto-trombone alternatives
either as separately identified `instrument-configuration` targets, or as
physical-object assertions whose referenced `specified` scopes carry
`instrument_configuration_uris`. The latter two fields belong to an
`ApplicabilityScope`, not to an assignment. See the actual mappings, exact
URIs, and authoring pattern in
[MULTIPERSPECTIVITY.md](MULTIPERSPECTIVITY.md#actual-multiplicity-in-the-mimo-mappings).

### SQLite: recursive hierarchy

Precomputed ancestors make the common hierarchy query a normal indexed join:

```sql
SELECT parent.notation, parent.definition, a.depth
FROM concept_ancestors a
JOIN concepts child ON child.uri = a.concept_uri
JOIN concepts parent ON parent.uri = a.ancestor_uri
WHERE child.notation = '111.141'
ORDER BY a.depth;
```

The underlying direct relations also support arbitrary recursive traversal:

```sql
WITH RECURSIVE descendants(uri) AS (
  SELECT uri FROM concepts WHERE notation = '4'
  UNION ALL
  SELECT r.subject_uri
  FROM source_relations r JOIN descendants d ON r.object_uri = d.uri
  WHERE r.predicate_uri = 'http://www.w3.org/2004/02/skos/core#broader'
)
SELECT notation, definition FROM concepts
WHERE uri IN descendants ORDER BY notation;
```

### SQLite full-text search

```sql
SELECT concept_uri, language, label
FROM label_search
WHERE label_search MATCH 'guitar';
```

### SQLite linguistic profile audit

Observed character scripts are technical evidence, not language or cultural
inferences:

```sql
SELECT concept_uri, literal_form, language_tag, observed_script_codes_json,
       translation_status, review_status
FROM label_linguistic_profiles
WHERE language_tag = 'zh'
  AND observed_script_codes_json = '["Latn"]'
LIMIT 20;
```

### RDF and SPARQL

```python
from rdflib import Graph

graph = Graph().parse("dist/rdf/omaro.ttl")
for row in graph.query("""
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?notation ?label WHERE {
  ?concept skos:notation ?notation ; skos:prefLabel ?label .
  FILTER(LANG(?label) = "en")
} ORDER BY ?notation LIMIT 10
"""):
    print(row)
```

### Static explorer links

The explorer keeps its selected concept and display language in the URL, so a
view can be bookmarked or cited directly:

```text
dist/index.html?lang=de&concept=http%3A%2F%2Fwww.mimo-db.eu%2FInstrumentsKeywords%2F4372
```

Language selectors and concept details show human-readable language names while
retaining the corresponding BCP 47 codes.

## VAO and MODAVIS interoperability

VAO 0.4.0 can carry this release's Hornbostel–Sachs scheme IRI, notation,
localized label, and exact scheme-snapshot version in its standard
`classifications` object. The generated example is
`dist/metadata/vao-classification-example.json`.

MODAVIS 0.1.0 is connected conservatively with `dcterms:relation`. The release
does not import MODAVIS or claim that its local assertion classes conform to
the MODAVIS exchange profile. In particular, MIMO instrument vocabulary
concepts are not equated with physical `modinst:MusicalInstrument` instances.
See [MODAVIS_VAO_INTEROPERABILITY.md](MODAVIS_VAO_INTEROPERABILITY.md) for the
field mapping, worked example, conformance boundary, and future bridge gates.

## Versioning and citation

- Major versions may change schemas or supported interfaces.
- Minor versions refresh source data or add backward-compatible fields.
- Patch versions correct data without changing the schema or intended meaning.

These promises begin with publication. The first public ontology and dataset
release is 0.1.0. Original ontology documents labelled 2.2.0 in earlier MODAVIS
reference snapshots remain available at their versioned paths. They are retained
for compatibility and are not the current public ontology. Term IRIs are
unchanged; the internal SQLite format and recorded projection-policy versions
are independent of the public ontology version.

Citation metadata is in `CITATION.cff`. The version DOI
`10.5281/zenodo.21442777` is reserved in a Zenodo draft but has not been
published. Release changes are summarized in [RELEASE_NOTES.md](RELEASE_NOTES.md).

Creator: Dominik Ukolov, affiliated with Research Group DIGITAL ORGANOLOGY,
Leipzig University, and Digital Humanities (Image/Object),
Friedrich Schiller University Jena.

## Provenance, limitations, and license

MIMO URIs and MIMO-published SKOS relations are retained. Five source mapping
targets currently have no resolved instrument record and are represented as
explicit stubs. MIMO's `skos:exactMatch` predicates are preserved in the
explicit source layer and `dist/rdf/mimo-source-snapshot.ttl`. Project-facing
exports use reversible, perspective-bearing `omaro:classifiedAs` assignments
marked `source-derived`, `source-asserted`, and `source-silent`; they do
not claim that an instrument concept and an organological class are
interchangeable or universally valid. Direct project assertions require
explicit policy membership, an eligible stance, a `context-independent` scope,
independent authorized referential and scholarly acceptances, and no active
veto decision. Translation coverage varies by
language; absence means the source snapshot supplied no preferred label.
MIMO's legacy `dk` language tag is normalized to BCP 47 `da`; untagged native
labels use `und`. Source-native preferred/alternative lexical collisions are
retained and quantified in the quality report.

The repository declares CC0 1.0 Universal. The documentary rights review was
accepted for the dataset scope; accountable publication authorization remains
with the maintainer. The source tree is REUSE 3.3 compliant; `REUSE.toml` and
`LICENSES/CC0-1.0.txt` provide machine-readable license coverage. See
[PROVENANCE.md](PROVENANCE.md).

Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md), the evidence-backed
[correction policy](CORRECTIONS.md), and the [project governance](GOVERNANCE.md).
Maintainer credit, support routes, and candidate state are recorded in
[AUTHORS.md](AUTHORS.md), [SUPPORT.md](SUPPORT.md), and
[RELEASE_STATUS.md](RELEASE_STATUS.md). Repository-level machine metadata is
available in `.zenodo.json`, `codemeta.json`, `CITATION.cff`, and `VERSION`.
