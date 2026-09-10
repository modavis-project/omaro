# VAO and MODAVIS interoperability

## Status and scope

This document defines the supported connection between OMARO Reference Dataset
0.1.0, OMARO Ontology 0.1.0, the Virtual Acoustic Object (VAO) Standard, and the
MODAVIS Ontology Network. It targets the finalized VAO 0.4.0 contract and MODAVIS
0.1.0. The VAO 0.5.0 candidate available on 2026-08-28 retains the same
classification object used here, but a candidate specification is not a stable
release dependency.

The connection is deliberately asymmetric:

- VAO can carry a compact Hornbostel–Sachs classification value in an entity
  description.
- This repository supplies the classification scheme, codes, labels,
  hierarchy, distinct assertion and assignment resources, scope, observations,
  criteria, directional evidence, and review semantics behind that compact
  value.
- MODAVIS is recorded as a related semantic standard. No OWL import,
  equivalence, subclass relationship, or MODAVIS conformance claim is made.

The versioned references are:

| Standard | Release used | Persistent reference |
|---|---:|---|
| VAO | 0.4.0, finalized | `https://w3id.org/modavis/vao/0.4.0/` |
| MODAVIS Ontology Network | 0.1.0, released | `https://w3id.org/modavis/ontology/0.1.0` |

The generated RDF and DCAT metadata connect these resources with
`dcterms:relation`. This relation means that an explicit interoperability
analysis exists; it does not mean conformance.

## VAO classification mapping

VAO permits each entity to contain zero or more `classifications`. Each value
requires an IRI-valued `scheme` and a string-valued `code`; a localized
`label` and string-valued `version` are optional. The following mapping is
lossless for those four VAO fields:

| VAO field | OMARO source | Meaning |
|---|---|---|
| `scheme` | `concept_schemes.uri` / `classification_scheme_uri` | The MIMO Hornbostel–Sachs scheme IRI. |
| `code` | `concepts.notation` / `classification_notation` | The Hornbostel–Sachs notation, retained as a string. |
| `label` | preferred labels for the classification concept | A localized display aid; never the identifier. |
| `version` | `concept_schemes.version` | The exact MIMO vocabulary snapshot used by this release. |

The generated example at
`dist/metadata/vao-classification-example.json` is:

```json
{
  "scheme": "http://www.mimo-db.eu/HornbostelAndSachs#",
  "code": "111.141",
  "label": {
    "en": "Castanets"
  },
  "version": "2026-07-19T15:10:55Z"
}
```

This object can be inserted unchanged into a VAO entity's `classifications`
array. A consumer resolves it by matching `scheme` and `code` to a canonical
classification concept. It must not join on `label`.

### What the compact VAO value does not carry

VAO's classification object is intentionally descriptive. It does not carry
OMARO's assertion URI, assignment-activity URI, target URI, compound
expression, observation or criterion links, perspective, applicability scope,
authority mandate, directional evidence, stance, review decision, protocol,
use decision, or projection policy. Consequently, the value is suitable for
exchange, discovery, filtering, and citation, but it is not a substitute for a
qualified classification assertion.

For preservation or research use, a VAO release should therefore include or
reference the release ZIP, RDF dataset, or relevant JSONL records as a separate
descriptive resource. The compact value remains the entry point; the qualified
record remains the evidence-bearing statement.

### Worked example

Suppose a VAO entity represents a digital surrogate of a pair of castanets.
Its `classifications` array can contain the object above. A catalogue can then
facet on code `111.141` or follow the scheme hierarchy. If a researcher needs
to know why the represented instrument was assigned to the class, under which
perspective, or whether a community-specific review changed its display
status, the researcher follows the corresponding qualified assertion/assignment envelope in
`classification_assertions.jsonl`, `classification-assignments.csv`, SQLite,
or RDF.

The distinction is important: a VAO entity describes a research or heritage
object, while a MIMO instrument URI in this repository identifies a vocabulary
concept. Neither identifier should be asserted as identical to the other.

## MODAVIS relationship

MODAVIS 0.1.0 offers conceptually relevant patterns:

| This repository | Related MODAVIS area | Compatibility assessment |
|---|---|---|
| Classification assertion entity and assignment activity | assertion and provenance modules | Similar reification and provenance purposes, but not currently exchange-shape compatible. |
| Applicability scope | context module | Compatible principle: absent context is not universal validity. Combination rules differ and remain application-profile responsibilities. |
| Evidence record and source record | evidence module | A future crosswalk could create `EvidenceRelation` and `SourceSnapshot` resources when all required fixity and provenance values are available. |
| Review events, decision entities, and projection policies | assertion/provenance modules | Related lifecycle concerns, but the local decision and authority model is more specialized. |
| MIMO instrument concept | instrument module | Not equivalent: a vocabulary concept is not a physical musical instrument. |

The released MODAVIS assertion exchange shape currently restricts
`modassert:assertsPredicate` to the governed `has-builder` predicate and
requires a `modinst:MusicalInstrument` subject plus a conforming evidence
relation. A local `omaro:ClassificationAssertion` uses `omaro:classifiedAs` and
normally links MIMO SKOS concepts. Declaring it to be a `modassert:Assertion`
would therefore create instances that fail the published MODAVIS exchange
shape and would blur the distinction between a physical instrument and a
vocabulary concept.

For that reason, `schema/modavis-vao-relations.ttl` contains only versioned
`dcterms:relation` statements. It contains no `owl:imports`, `owl:equivalentClass`,
`owl:equivalentProperty`, or `rdfs:subClassOf` bridge.

## Future normative bridge

A normative MODAVIS bridge should be published only after all of the following
conditions are met:

1. MODAVIS provides or approves a classification predicate and an application
   profile that admits it.
2. The bridge distinguishes a documented physical object and its state from
   its MIMO vocabulary concept and from any digital surrogate or VAO entity.
3. Each transformed assertion has conforming MODAVIS evidence relations and
   source snapshots rather than URI-only approximations.
4. Scope-combination, review-decision, authority, and projection semantics are
   specified and tested in both models.
5. Golden examples validate against the exact versioned MODAVIS ontology and
   SHACL profiles.
6. The mapping receives domain and governance review and is versioned
   independently from both source ontologies.

Until then, applications may transform local records into a separately named
application graph, but must not describe that graph as a release-provided
MODAVIS mapping or as MODAVIS-conformant.

## Benefits and use cases

- **VAO discovery:** repositories can expose familiar Hornbostel–Sachs codes
  without embedding this complete ontology in every object manifest.
- **Reproducible interpretation:** the scheme version prevents the same code
  from being interpreted against an unspecified vocabulary snapshot.
- **Progressive detail:** simple catalogues use the four-field VAO value;
  research systems follow it to qualified assertions and review evidence.
- **Cross-collection faceting:** stable scheme/code pairs support filters and
  joins across VAO carriers, collection catalogues, and this release.
- **Future knowledge-graph integration:** the documented MODAVIS boundary
  identifies the exact work needed for a valid bridge without publishing
  premature equivalences.
- **Cultural and scholarly accountability:** contextual qualifications remain
  available even when a compact exchange format cannot represent them.

## Verification

Release tests check that the generated example has the required VAO fields,
uses the canonical scheme and notation, and carries the current scheme
version. RDF tests check the two versioned `dcterms:relation` links and ensure
that the relation-only alignment file contains no OWL import, equivalence, or
subclass axioms.
