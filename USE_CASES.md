# OMARO use cases and executable queries

## Choose a workflow

| User and question | Input and tool | Result and interpretation |
|---|---|---|
| Museum cataloguer: which source classifications accompany this instrument name? | Label search, then exact target URI with `omaro query` | Separate source occurrences with scheme, perspective, scope, evidence and assignment identity |
| Organologist: what changes with technique, configuration or performance? | Explicit target kind, context and the assessment examples | Contextual claims tied to the described occurrence; source silence remains unknown |
| Reviewer: why is a claim excluded from an endorsed view? | `Dataset.explain_endorsement` or `omaro query` | Named unmet requirements and veto decisions, with independent reviewer counts |
| Collection integrator: how do I join classifications without losing provenance? | SQLite or RDF query recipes below | One occurrence per assignment with identifiers retained; no deduplication by target/class pair |
| RAG developer: what may an answer say from this snapshot? | Query output or generated `rag-concepts.jsonl` | Source-attributed, versioned claims with explicit review and scope limitations |
| Community-governed project: may contributed material be displayed or exported? | Protocol, mandate and use-decision workflow | Action-specific authorization, independent of scholarly eligibility |

These workflows implement [COMPETENCY_QUESTIONS.md](COMPETENCY_QUESTIONS.md).
For formal interpretation, see [INFERENCE_AND_VALIDATION.md](INFERENCE_AND_VALIDATION.md).
The reference snapshot is populated with MIMO claims; richer target, assessment
and governance examples are explicitly synthetic and are not silently loaded
into it.

## 1. Find and inspect a real source classification

From the repository root after installing the locked environment:

```bash
.venv/bin/omaro query --search "Double bass" --limit 10
.venv/bin/omaro query --target-uri http://www.mimo-db.eu/InstrumentsKeywords/3111
```

Search uses case-insensitive literal substring matching over the preserved
multilingual labels and registered target labels. It can return several
concepts: choose a URI before interpreting a result. It does not infer lexical
identity, translations, language preference or semantic similarity. The limit
(1–100; default 20) bounds returned targets, retaining every classification
occurrence for each one. `matched_target_count`, `returned_target_count` and
`truncated` make truncation explicit. An unknown URI yields zero results; a
known target without assignments has an empty occurrence list. Neither is a
negative observation about an instrument.

The exact double-bass URI returns three source-derived occurrences:

| Hornbostel–Sachs notation | Recorded scope | Research selection | Direct endorsement |
|---|---|---|---|
| `321.322` | source-silent | included | ineligible |
| `321.322-5` | source-silent | included | ineligible |
| `321.322-71` | source-silent | included | ineligible |

These are statements about the MIMO instrument-name concept, not observations
of a specimen. Each `classification_occurrences` entry includes the complete
canonical `claim`, classification concept, `research_included` Boolean and
`endorsement` report. Source predicate, source record, assertion URI and
assignment URI survive. The response also identifies the dataset and ontology
versions. Current source claims lack policy opt-in, eligible stance,
context-independent scope and required reviews; an empty endorsed result is
the expected evidence state.

## 2. Supply a technique or historical context

```bash
.venv/bin/omaro query --target-uri http://www.mimo-db.eu/InstrumentsKeywords/3111 --context examples/queries/arco-context.json
```

The context fixture uses a **synthetic** technique URI and explicit timestamps.
It demonstrates the interface; it does not add an arco observation or change
the empirical source scopes. The three source-silent occurrences remain
available as research claims and ineligible for contextual endorsement.

Context is a JSON object conforming to
[`schema/query_context.schema.json`](schema/query_context.schema.json):

| Field | Meaning |
|---|---|
| `community_uris`, `place_uris`, `period_uris`, `usage_domain_uris` | Exact identifiers for contextual dimensions |
| `playing_technique_uris`, `instrument_configuration_uris`, `language_variety_uris` | Exact technique, configuration and language-variety identifiers |
| `at` | Subject-matter instant used against scope intervals |
| `as_of` | Claim/review lifecycle instant; defaults to the recorded dataset generation time |

Each URI dimension accepts one absolute URI or an array of distinct absolute
URIs. Empty arrays supply no values. Datetimes must include a timezone;
lowercase RFC 3339 `t`/`z` is normalized to uppercase for evaluation.
Unknown keys, duplicate values, relative identifiers, nulls and malformed
datetimes are rejected with exit status 2. Valid queries return JSON with exit
status 0, including no-match results. `--repo-root` is a global argument and
precedes `query`; a context file path is relative to the calling directory.

Omitting `--context` evaluates static direct endorsement. Supplying `{}` asks
for contextual evaluation without any dimensions; these modes are not
interchangeable. A specified scope requires every populated dimension to
match for positive support. Missing query values cannot establish that a
dispute is irrelevant. `as_of` changes no publication authorization and uses
no wall-clock default.

To model actual arco/pizzicato observations, create separate sounding targets
and evidence-bearing assignments as illustrated in
[the organological-assessment bundle](examples/organological-assessment/README.md).
For slide/valve trombones, target the inspected object/configuration; for
bagpipes, retain the assessed part and whole separately. The source rationale
and boundaries are in [ORGANOLOGICAL_MODEL.md](ORGANOLOGICAL_MODEL.md).

## 3. Explain an endorsement decision

```python
from pathlib import Path
from omaro.model import Dataset

dataset = Dataset.load(Path("data/canonical"))
dataset.assert_publication_authorized()
dataset.validate(Path("schema"))
claim = next(row for row in dataset.classification_assertions
             if row["target_uri"] == "http://www.mimo-db.eu/InstrumentsKeywords/3111")
report = dataset.explain_endorsement(claim)
print(report["eligible"], report["reason_codes"])
```

All applicable failures are returned in deterministic order. An eligible
result has no reason codes. The explanation includes per-dimension qualifying
review decisions and reviewer agent URIs; repeated decisions from one agent
do not create additional independent reviewers.

| Reason code | Interpretation |
|---|---|
| `policy-does-not-project-direct-assertions` | The selected policy does not permit static flattening |
| `mapping-purpose-requires-qualified-assertion` | A purpose-qualified mapping must remain qualified |
| `claim-not-in-policy` | The occurrence did not opt into this policy |
| `ineligible-stance` | Its recorded stance is not eligible under the policy |
| `claim-not-yet-active`, `claim-expired` | The occurrence is outside its lifecycle interval at `as_of` |
| `scope-not-context-independent` | A static projection lacks the required explicit scope |
| `scope-not-matched` | Contextual selection lacks a sufficient match under the policy |
| `active-review-veto` | A qualifying authorized decision blocks this projection |
| `required-review-missing` | At least one review requirement is unsatisfied |
| `insufficient-independent-reviewers` | Too few distinct qualifying reviewer agents |

The `reviews` object identifies active authorized decisions in the selected
policy and the subset that vetoes the projection. It is not the complete
review history. Read the underlying event/decision records to investigate
expiry, supersession, suspension, authority failure or a different policy.
The trace does not establish the truth of the conclusion or confer permission
to use it.

## 4. Query a generated distribution

Build the repository with `.venv/bin/omaro build` first. From the root of the
source checkout or extracted dataset archive, a SQLite client can run:

```bash
sqlite3 -readonly -header -csv dist/sqlite/omaro.sqlite < examples/queries/double-bass.sql
```

The query returns assertion and assignment identities, the three notations,
perspective and scope, preserved source predicate, and a static endorsement
flag. It uses the materialized endorsement table produced by the Python
evaluator; it does not invent a second SQL review-policy implementation.

The canonical-data CLI validates the complete input on each invocation. For
repeated lookups, reuse a checked SQLite distribution or validate an in-memory
`Dataset` once before calling the low-level evaluation methods.

[`examples/queries/double-bass.rq`](examples/queries/double-bass.rq) is a
SPARQL 1.1 `SELECT` over `dist/rdf/omaro.ttl`, with the same target and occurrence
identities. Execute it in an RDFLib environment with:

```python
from pathlib import Path
from rdflib import Graph

graph = Graph().parse("dist/rdf/omaro.ttl", format="turtle")
result = graph.query(Path("examples/queries/double-bass.rq").read_text())
print(result.serialize(format="csv").decode("utf-8"))
```

The RDF graph is large; SQLite is convenient for routine lookups. The compact
`dist/ontology/0.1.0/` vocabulary contains no empirical assignments and cannot
answer the dataset query by itself. The source-only MIMO snapshot likewise
does not contain OMARO assignment envelopes. The SQL and SPARQL examples are
exercised against generated projections in `tests/test_query.py`.

The dataset ZIP includes these query files and documentation. The Python
tooling and its complete canonical inputs require the source checkout; the
expert packet is not a substitute for that checkout.

## 5. Assemble an accountable research or RAG answer

For the current example, an appropriate answer is: “The MIMO-derived snapshot
records three double-bass classification occurrences, including finger-sounded
and bowed variants; their applicability is source-silent and they have no
project endorsement.” Return the target URI, individual assertion URIs, source
record and dataset version alongside that answer. A later review or contributed
context must remain attached to its own occurrence.

Use the complete claim and structured fields when constructing answers.
`research_included` means selected for inspection, not accepted as a fact.
Do not turn search hits, similar labels, a generic hierarchy path, or an empty
assessment list into construction, linguistic, community or performance facts.
For method-dependent comparisons, use the
[multidimensional-analysis example](examples/multidimensional-analysis/README.md)
and preserve its selected dimensions, missing-value treatment and procedure.

## 6. Contribute governed material

Follow [CULTURAL_GOVERNANCE.md](CULTURAL_GOVERNANCE.md) and
[REVIEW_PROTOCOL.md](REVIEW_PROTOCOL.md): identify the target and represented
communities, preserve a real mandate and protocol, record the applicable
action/purpose/audience/scope/time, and obtain the matching use decision.
The query command deliberately applies the same publication preflight as the
public build before searching or returning counts. A denied dataset emits no
partial query result. There is no bypass option or automatic conversion of
scholarly acceptance into permission.

The illustrative community records demonstrate the mechanics only. They do
not authorize any actual community material. Remaining scientific and
community decisions are human processes, separately identified in
[RELEASE_STATUS.md](RELEASE_STATUS.md).
