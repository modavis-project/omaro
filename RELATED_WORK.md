# Related work and design decisions

## Purpose and status

This document records the external standards and related organological models
that informed OMARO 0.1.0. It is a design rationale, not a claim that OMARO
replaces or conforms fully to every resource listed here. The status statements
were checked on **2026-08-31**. A later release must recheck draft and external
vocabulary versions before changing an alignment.

OMARO remains a focused ontology for qualified organological claims,
assignment activities, evidence, observations, perspectives, applicability,
review, authority, cultural protocols, and governed publication. It does not
attempt to become a complete museum-collection, conservation, performance, or
lexicographic ontology. Hornbostel–Sachs and MIMO concepts remain resources in
independent SKOS concept schemes, not OMARO classes.

The reference snapshot does not presently contain contributed
`organological_targets`, `classification_criteria`,
`observation_assessments`, `protocol_applications`, or `use_decisions`;
those canonical registries intentionally start empty. Existing source-derived
classification rows therefore use empty assessment and criterion links and no
inference logic. Compound expressions are the limited exception: the 26 source
notations containing `+` are mechanically tokenized without semantic guesses.
Schema capability and conformance fixtures must not be reported as empirical
organological or community content.

## Architectural conclusions

The additional identity, inference, validation and explainable-projection
sources checked on **2026-09-06** are documented with their implementation
consequences in [INFERENCE_AND_VALIDATION.md](INFERENCE_AND_VALIDATION.md).
The corresponding user workflows and executable recipes are in
[USE_CASES.md](USE_CASES.md). This later check does not replace the earlier
version checks for the other external vocabularies below.

The related work supports ten conclusions that govern the OMARO model:

1. A proposition must be distinct from the activity that produced it.
2. A review activity must be distinct from the decision it produced.
3. A classification should be traceable from target state through assessment,
   any actual observation and result, criterion, and inference, without
   requiring invented evidence for legacy source mappings.
4. Physical identity, configuration, condition, component structure, actual
   sounding use, and performance context must not be collapsed into one
   generic “instrument” target.
5. Compound Hornbostel–Sachs notation must be round-trippable before it is
   interpreted; an uninterpreted token is preferable to a guessed structure.
6. Epistemic endorsement, legal rights, cultural protocol, collective
   authorization, individual consent, and permission for a publication action
   are independent determinations.
7. An absent qualifier means unknown, not universal validity or unrestricted
   permission.
8. A classification tree is a versioned knowledge-organization artifact, not
   a complete OWL model of instrument objects, properties, and performances.
9. Competency questions, stakeholder scenarios, explicit requirements,
   versioning, and executable evaluation must accompany the ontology.
10. A concept mapping is suitable only for stated operations; predicate choice
    alone does not establish fitness, losslessness, or authorization for use.

## Standards baseline

| Resource | Status on 2026-08-31 | OMARO 0.1 use |
|---|---|---|
| [RDF 1.1](https://www.w3.org/TR/rdf11-concepts/) | W3C Recommendation | Normative exchange baseline. OMARO assertion resources remain serializable with RDF 1.1 reification. |
| [RDF 1.2 Concepts](https://www.w3.org/TR/rdf12-concepts/) | Candidate Recommendation Snapshot, 2026-04-07 | Design-compatible future path for unasserted triple terms and multiple reifiers; not the normative serialization baseline. |
| [SKOS and SKOS-XL](https://www.w3.org/TR/skos-reference/) | W3C Recommendation, 2009 | Concept schemes, mappings, notations, labels, and controlled OMARO value resources. |
| [SSSOM](https://mapping-commons.github.io/sssom/) | Maintained semantic-mapping exchange specification | Planned tabular mapping profile. OMARO mapping-purpose and other claim qualifiers must be preserved through a versioned profile or declared as losses. |
| [PROV-O](https://www.w3.org/TR/prov-o/) | W3C Recommendation, 2013 | Activities, entities, agents, generation, derivation, attribution, and qualified evidence use. |
| [DCAT 3](https://www.w3.org/TR/vocab-dcat-3/) | W3C Recommendation, 2024 | Stable and versioned dataset identity plus release-distribution metadata. |
| [Data Quality Vocabulary](https://www.w3.org/TR/vocab-dqv/) | W3C Working Group Note, 2016 | Machine-readable measurements of dataset fitness and validation results. It does not assess the truth or cultural validity of an organological claim. |
| [RO-Crate 1.3](https://w3id.org/ro/crate/1.3) | Research Object community Recommendation, 2026-06-22 | Self-describing release package with a compact JSON-LD inventory of the dataset, documentation, examples, and generated distributions. |
| [SOSA/SSN](https://www.w3.org/TR/2017/REC-vocab-ssn-20171019/) | W3C Recommendation, 2017 | Stable observation vocabulary alignment. The [2023 edition](https://www.w3.org/TR/vocab-ssn-2023/) was still a Working Draft dated 2026-08-19 and is monitored, not treated as a Recommendation. |
| [CIDOC CRM 7.1.3](https://cidoc-crm.org/get-last-official-release) | Current official CIDOC CRM release, announced 2024-02-13 | Museum interoperability, especially classification as `E17 Type Assignment` and external object/event modeling. |
| [CRMinf 1.2.1](https://cidoc-crm.org/extensions/crminf/html/CRMinf_v1.2.1.html) | Stable release, 2026-04 | Methodological reference for premise, logic, belief, and conclusion graphs. A CRMinf projection is deferred until OMARO can emit that complete pattern. |
| [CRMsci 3.2](https://cidoc-crm.org/crmsci/ModelVersion/crmsci-v3.2) | Current stable CRMsci release, 2026-04 | Informative museum-science bridge. Actual observation attempts align to the general `S27 Observation`; assessment records that say no observation occurred do not. |
| [QUDT](https://www.qudt.org/doc/2026/01/DOC_SCHEMA-QUDT.html) | Published vocabulary documentation, 2026-01 | Resolvable quantity-kind and unit identifiers in numeric observation results. |
| [I-ADOPT 1.0.3](https://i-adopt.github.io/ontology/archive/1.0.3/index.html) | Versioned interoperability framework ontology | Methodological influence on decomposing an observed property from its object and context; not imported wholesale. |
| [Web Annotation](https://www.w3.org/TR/annotation-model/) | W3C Recommendation, 2017 | Recommended bridge when evidence identifies a passage, image region, or time segment. |
| [ODRL 2.2](https://www.w3.org/TR/odrl-model/) | W3C Recommendation, 2018 | Possible exchange bridge for action policies. An ODRL permission is not an OMARO cultural-authority or review decision. |
| [LIDO 1.1](https://lido-schema.org/documents/primer/2024-09-11/lido-primer.html) | Current documented LIDO generation | Museum-record exchange profile for identifiers, classifications, measurements, events, and rights; not a core import. |
| [Europeana Data Model 5.2.8](https://pro.europeana.eu/page/edm-documentation) | Published Europeana model with maintained implementation documentation | Provider-record and aggregation provenance bridge. EDM proxies can keep differing provider descriptions of one cultural heritage object distinct, but do not supply OMARO's claim, evidence, authority, or applicability semantics. |
| [ArCo network 2.0 / Musical Instrument module 1.0](https://w3id.org/arco/ontology/musical-instrument) | Published cultural-heritage ontology network and versioned instrument module | Models a `MusicalInstrumentTaxon` and the specialized `HornbostelSachsClass`; a bridge is useful for Italian catalogue records but is not an identity mapping. |
| [LCMPT 2026](https://www.loc.gov/aba/publications/FreeLCMPT/freelcmpt.html) and [MARC 21 field 382](https://www.loc.gov/marc/bibliographic/concise/bd382.html) | Maintained Library of Congress vocabulary and exchange format | Library bridge for intended, written, performed, alternative, and partial media of performance. These are not object-level Hornbostel–Sachs classifications. |
| [OntoLex-Lemon](https://www.w3.org/2016/05/ontolex/) | Final W3C Community Group Report, 2016; not a W3C Standard | Deferred until OMARO represents genuine lexical entries, grammatical forms, and senses. OMARO 0.1 removes the earlier invalid `Form` projection. |

The version table is intentionally conservative. Stable namespace terms may be
used without importing an external ontology. OMARO does not make a conformance
claim merely by using or aligning to selected terms.

## Adoption, deferral, and rejection matrix

| Related pattern or method | Decision | OMARO application and boundary |
|---|---|---|
| SKOS concept schemes and SKOS-XL label resources | **Adopt** | Hornbostel–Sachs, MIMO, community schemes, and OMARO controlled values keep independent URI identity. A SKOS concept is not converted into an OWL class. |
| SSSOM mapping exchange | **Adopt through a versioned profile** | Export only assertions suitable for the requested mapping purpose; require an explicit purpose on import; preserve every qualified OMARO field or declare its loss. |
| PROV entity/activity separation | **Adopt** | Classification and review JSON records are compact envelopes, while RDF separates the proposition or decision entity from the activity that generated it. |
| DCAT 3 dataset version and distribution metadata | **Adopt** | Keep stable and immutable version URIs distinct; publish the ZIP's size, package format, licence, and SHA-256 in an external sidecar so the archive does not contain a circular checksum claim. |
| DQV quality measurements | **Adopt narrowly** | Publish defined, typed, provenance-bearing measurements computed on the versioned dataset. Do not type assertion-level warnings as certificates or derive an unexplained aggregate score. |
| RO-Crate 1.3 attached package | **Adopt** | Put a deterministic `ro-crate-metadata.json` in the ZIP root and describe representative directories, documentation, examples, and manifests without duplicating the complete generated-file inventory. |
| CIDOC CRM `E17 Type Assignment` | **Adopt as alignment** | `ClassificationAssignment` is an assignment activity. OMARO retains its own assertion, perspective, scope, evidence, and policy semantics. |
| CRMinf premise, logic, belief, and conclusion pattern | **Adopt method; defer projection** | `inference_logic_uri` preserves a named rule or method, but that field alone does not establish an `I5 Inference Making`. A conforming bridge must also identify premise and conclusion beliefs and their proposition sets. |
| SOSA feature/property/procedure/result/time pattern | **Adopt conditionally** | Records for detected, not-detected, and indeterminate attempts may project as observations. `not-observed` and `not-applicable` are assessment outcomes, not observation activities. |
| CRMsci observation and observable-situation pattern | **Adopt conditionally** | An actual OMARO attempt may receive the broad `S27 Observation` discovery type. `S4 Single Observation` is narrower and is justified only when the observed content is one binary proposition. |
| QUDT unit identifiers | **Adopt** | Quantity and range results use URI-identified units; OMARO does not mint duplicate metre, hertz, millimetre, or ratio units. |
| I-ADOPT observable-property decomposition | **Adopt as method** | Classification criteria identify observable properties and relevant procedures. I-ADOPT does not supply units or methods, so SOSA and QUDT remain complementary. |
| RDF 1.2 triple terms and `rdf:reifies` | **Defer as normative syntax** | The model can later project one proposition with several occurrence reifiers. RDF 1.1-compatible resources remain the release baseline until the Recommendation and tool support are stable. |
| [Expressing Without Asserting](https://ceur-ws.org/Vol-3643/paper7.pdf) | **Adopt the requirement; retain standard RDF syntax** | Qualified OMARO claims remain expressible without asserting their base triples. The research `Conjectures` syntax is not a W3C standard and is not required for exchange. |
| Web Annotation and IIIF Annotation resources | **Adopt by reference for evidence targeting** | Put the exact annotation URI in the existing evidence `resource_uri` when a passage, image region, audio segment, or video interval must be identified. No new core selector field is needed. |
| ODRL policy expressions | **Defer to exchange profile** | OMARO's `UseDecision` is deliberately small and authority-aware. It may be exported to ODRL where a lossless mapping is demonstrated. |
| LIDO, CIDOC CRM, and Linked Art object records | **Bridge, do not absorb** | Object history, production, acquisition, custody, conservation, and full media description remain in museum systems. OMARO links their target and event URIs and contributes qualified classification. |
| [MINIM-UK cataloguing and metadata profile](https://minim.ac.uk/index.php/about/project-outputs/) | **Adopt as implementation precedent** | Use its documented CIMCIM/MIMO/LIDO combination to design a bounded museum import/export fixture. Do not claim MINIM-UK conformance or losslessness until that fixture is tested. |
| Europeana EDM provider proxies | **Bridge, do not equate** | An `ore:Proxy` identifies a provider-specific description in an aggregation. It can preserve source-view provenance, but it is not an OMARO perspective, assertion, assignment, or classified target. |
| Polifonia, DOREMUS, and Performed Music Ontology | **Bridge, do not equate** | Their instrument, realization, work, medium, and performance resources can be targets or linked context. OMARO avoids `owl:sameAs` without identity proof. |
| Local Contexts Labels | **Adopt by reference only** | A community-applied permanent identifier may be recorded as a protocol application. OMARO never mints, customizes, or substitutes for a Label. |
| [CARE Principles](https://www.gida-global.org/careprinciples) | **Adopt as a governance checklist where applicable** | Map authority, protocol, decision, responsibility, and ethics evidence without treating CARE as community-specific law or as a universal authorization outcome. Benefit-sharing and reciprocity remain deployment evidence. |
| Contextual-part multiplication such as the [NdFluents](https://arxiv.org/abs/1609.07102) pattern | **Do not adopt as the core pattern** | Explicit target states, configurations, sounding realizations, scopes, and occurrence resources answer OMARO's questions without creating a contextual part of every entity. A project may publish a bridge if required. |
| OntoLex `Form` typing for every SKOS-XL label | **Reject and remove** | A `Form` is a grammatical realization of a lexical entry. A source-qualified thesaurus label does not establish a lexical entry, morphology, or sense. |
| [Musical-instrument taxonomy query evaluation](https://ismir2011.ismir.net/papers/PS3-19.pdf) | **Adopt the method and separation** | Preserve classification trees as schemes, expose the property and activity relations needed by queries, and classify event-specific sounding separately from an object's usual classification. |
| [Multidimensional scalogram analysis for sound-producing instruments](https://doi.org/10.2307/852139) | **Adopt the faceted and reproducible-analysis method** | Record variables as criteria and each result as a method-, dataset-, perspective-, and scope-qualified assignment; do not turn analytical proximity into identity. |
| [Ontology for Analytic Claims in Music](https://github.com/HCDigitalScholarship/OMAC) | **Bridge selectively** | A musicological claim or argument can be retained as source or evidence. OMARO creates a distinct, narrower classification assertion and assignment only when the source proposition and act are known. |
| [Wikibase statement model](https://www.mediawiki.org/wiki/Wikibase/DataModel) | **Document; defer implementation** | Full statements, qualifiers, and references can support collaborative editing. Rank and truthy exports cannot substitute for perspective, scope, evidence direction, review, authority, or projection policy. |
| [Nanopublication guidelines](https://nanopub.net/guidelines/working_draft/) | **Document; defer implementation** | Assertion, provenance, and publication-information graphs fit OMARO's separation, but a versioned TriG profile must address qualified claims, immutable revisions, authorization, and culturally required withdrawal before network publication. |
| [Smart Musical Instruments Ontology](https://w3id.org/smi#) | **Bridge, do not absorb** | Sensors, actuators, embedded intelligence, connectivity, applications, and services remain in the specialist model; OMARO links relevant sensors, modules, configurations, procedures, and sounding targets. |
| [MIRO ontology-reporting guidelines](https://doi.org/10.1186/s13326-017-0172-7) | **Adopt as a reporting checklist** | Name, motivation, scope, knowledge acquisition, content, change management, and quality assurance are mapped to public repository evidence below. This is not a certification claim. |
| [Ten simple rules for making a vocabulary FAIR](https://doi.org/10.1371/journal.pcbi.1009041) | **Adopt as a sustainability checklist** | Maintain governed identifiers, term and vocabulary metadata, versioning, reuse, licences, and human- and machine-readable access. Active W3ID resolution and registration in appropriate vocabulary catalogues remain publication tasks; no FAIR certification is claimed. |
| Missing context interpreted as globally valid | **Reject** | `source-silent`, `not-yet-investigated`, `known-unknown`, and `intentionally-unscoped` remain unresolved under three-valued matching. |
| Unrestricted complements or exclusions over cultural groups | **Reject** | Open and community-governed value spaces cannot safely be treated as complete enumerations. Positive, evidenced scopes are the default. |
| Compound notation represented as an OWL intersection | **Reject** | A source notation can combine categories, components, refinements, and suffixes; this does not assert logical class intersection or inheritance to a whole object. |
| Broad `owl:imports`, `owl:equivalentClass`, or `owl:sameAs` assertions | **Reject by default** | Versioned bridge files and qualified mappings are safer than importing external commitments or asserting identity that has not been reviewed. |

## Requirements, claims, and reporting methodology

Kolozali and colleagues evaluated instrument-taxonomy representations with
questions about family, shape, excitation, construction, and event-specific
playing. Their results support OMARO's distinction between a scheme hierarchy
and explicit relations that answer organological queries. The published
accordion example—free reeds unused while switches and keys are tapped in one
piece—maps to an object/configuration classification plus a separate
performance and sounding-realization classification. OMARO does not rewrite
the object's usual class from one performance and does not guess an exact
idiophone number without evidence.

The [Ontology for Analytic Claims in Music](https://github.com/HCDigitalScholarship/OMAC)
is complementary evidence that musical scholarship needs first-class claim
and argument resources. An OMAC claim may be retained as an external source or
evidence resource. It becomes an OMARO classification assertion only through
an explicit bridge that identifies the exact target, predicate,
classification, perspective, scope, evidence role, and generating assignment.
OMAC argument structure is not flattened into OMARO review status, and an
analytic claim does not establish cultural authority or publication consent.

The [Smart Musical Instruments Ontology](https://w3id.org/smi#) demonstrates a
scenario- and stakeholder-driven method for sensors, actuators, embedded
intelligence, connectivity, and interacting musical services. OMARO adopts the
requirements lesson and a bridge boundary, not that complete domain model. A
sensor may populate `assessment_sensor_uri`; an external property or procedure
may be referenced by a criterion or assessment; modules may participate in an
`instrument-configuration`; and the observed result can qualify a
`sounding-realization`. Network topology, device capabilities, applications,
and services remain in the SMI or Internet-of-Musical-Things graph.

OMARO's public documentation is organized against the seven general reporting
areas in the [MIRO guidelines](https://doi.org/10.1186/s13326-017-0172-7):

| MIRO reporting area | OMARO evidence |
|---|---|
| Basic facts | `README.md`, `CITATION.cff`, `codemeta.json`, `LICENSE`, `NAMING_AND_IDENTITY.md`, and `W3ID_REGISTRATION.md` state name, identifiers, creators, licence, versions, and access. |
| Motivation | `README.md`, `MULTIPERSPECTIVITY.md`, and this document state the problem, expected benefits, and related-work decisions. |
| Scope, requirements, and audience | `ONTOLOGY_REFERENCE.md`, `ORGANOLOGICAL_FOUNDATIONS.md`, `COMPETENCY_QUESTIONS.md`, and `EXPERT_REVIEW_GUIDE.md` state boundaries, users, requirements, cases, and known limitations. |
| Knowledge acquisition | `PROVENANCE.md`, `QUALITY_REPORT.md`, source records, migration scripts, checksums, and the organological source rationale document derivation and deliberate non-invention. |
| Ontology content | `ONTOLOGY_REFERENCE.md`, `DATA_DICTIONARY.md`, JSON Schemas, SHACL, examples, and versioned OWL serializations document terms, axioms, constraints, and records. |
| Change management | `GOVERNANCE.md`, `CONTRIBUTING.md`, `SUPPORT.md`, `CHANGELOG.md`, version policy, and stable W3ID routes document ownership, issue handling, deprecation, and releases. |
| Quality assurance | Competency questions, conformance fixtures, unit and semantic tests, RDF-isomorphism checks, schema/CSV contracts, deterministic builds, manifests, and release checks provide executable evidence. |

This map makes reporting omissions reviewable; it does not claim that MIRO or
any external body has certified OMARO. Expert feedback and future organological
case annotations remain part of the release process.

OMARO also adopts the five publication commitments set out in the W3C Semantic
Web Deployment group's 2008 Editor's Draft on [principles for managing RDF
vocabularies and OWL
ontologies](https://www.w3.org/2006/07/SWD/Vocab/principles-20080316): control
and preserve the URI namespace, provide human-readable documentation, publish
a maintenance policy, identify immutable versions, and provide a formal
schema. The source is explicitly work in progress rather than a W3C
Recommendation. `W3ID_REGISTRATION.md` makes clear that the prepared namespace
is not active until its external registration and resolution checks succeed;
`ONTOLOGY_REFERENCE.md`, `GOVERNANCE.md`, `CONTRIBUTING.md`, and the versioned
OWL/RDFS serializations supply the corresponding documentation, maintenance,
version, and schema evidence. Content negotiation follows the W3C
[vocabulary-publishing recipes](https://www.w3.org/TR/swbp-vocab-pub/). These
are engineering commitments, not W3C endorsement of OMARO.

The peer-reviewed [ten rules for making a vocabulary
FAIR](https://doi.org/10.1371/journal.pcbi.1009041) supply a complementary
sustainability audit. OMARO identifies a custodian and contribution process;
uses global identifiers for the vocabulary and its terms; reuses established
models; records definitions, provenance, licence, and version metadata; and
builds human-readable HTML together with standard RDF representations. The
release also preserves immutable versions and machine-checks metadata,
serialization equivalence, and namespace targets. Two steps remain external
publication gates: activating and verifying the W3ID resolver, and registering
the released vocabulary in suitable catalogues or terminology services so it
can be discovered independently of the repository. These documented practices
support FAIR reuse but do not constitute a FAIR certification or authorize
reuse that an applicable cultural protocol restricts.

The development lifecycle is influenced by the requirements- and
competency-question-driven iteration described by the [Linked Open Terms
methodology](https://lot.linkeddata.es/) and by [eXtreme Design
(XD)](https://www.ida.liu.se/~evabl45/files/XD.pdf): stakeholder scenarios lead
to requirements and competency questions, reuse and design decisions lead to
implementation, and executable checks plus expert review feed the next
version. `CONTRIBUTING.md` makes that traceability operational for proposed
terms and bridges. OMARO does not claim LOT or XD conformance, certification,
or completion of every activity in either method.

## Publication, quality, and collaborative exchange boundaries

DCAT 3 distinguishes a dataset from its downloadable distributions and
provides explicit lifecycle-version relations. OMARO applies that distinction
to the stable dataset URI, the immutable `0.1.0` URI, and the release ZIP. The
archive's byte size and SHA-256 belong in a sidecar generated after the archive;
placing the digest of the enclosing ZIP inside that ZIP would be circular. A
DCAT catalogue record describes the metadata record itself. DCAT conformance,
package integrity, and a DOI improve discovery and verification but establish
neither organological correctness nor cultural authority.

DQV is used only for named dataset-quality metrics with explicit value types,
denominators, provenance, and computation targets. Resolution counts,
automated finding counts, review-event counts, and validation results help a
consumer judge fitness for a purpose. They do not become a composite quality
score, a review decision, an organological observation, or evidence that a
classification is culturally valid. In particular, an OMARO `QualityFinding`
retains `review_effect=none` and is not a DQV certificate.

RO-Crate complements the complete generated-file manifest with a compact
research-object description in the archive root. Directory-level entities keep
the crate usable without listing thousands of generated pages twice. Its root
licence describes the distributed package; it never overrides a protocol or
action-specific `UseDecision`. An integrity-checked crate is authentic as a
byte package only to the extent established by its checksum and publication
channel; it is not thereby true, endorsed, consented to, or authorized.

Wikibase remains attractive as a future collaborative editing interface because
its full statements support qualifiers and references. Its three ranks are too
coarse to encode OMARO stance, evidence direction, review outcome, or policy,
and its truthy export deliberately loses statement qualifications. A future
bridge must preserve the OMARO assertion URI and use full statement nodes;
`preferred`, `normal`, and `deprecated` must not be mapped mechanically to
endorsed, ordinary, and rejected claims.

Nanopublications likewise fit the separation of assertion content, assertion
provenance, and publication information. Implementation is deferred because a
Trusty URI provides immutability, not truth or authority, and immutable network
replication may conflict with culturally required withdrawal. A future profile
must publish the qualified assertion rather than an ineligible base triple,
apply publication authorization before creating the nanopublication, and link
reviews or revisions as new immutable resources rather than mutating an older
one.

## OMARO 0.1 model changes

### Resolvable targets and target kinds

The breaking rename from `instrument_uri` to `target_uri` removes the
assumption that every classifiable thing is intrinsically a musical
instrument. A physical saw, bottle, stone, electronic module, or typewriter
may have an instrumental role in one performance without changing its physical
identity. The `organological_targets` registry resolves target-level relations
and uses these kinds:

- `instrument-concept`;
- `physical-object`;
- `instrument-component`;
- `functional-module`;
- `instrument-aggregate`;
- `instrument-configuration`;
- `condition-state`;
- `sounding-realization`;
- `performance-event`; and
- `ensemble-medium`.

The distinction also prevents a terminology collision with the
[Polifonia Music Instrument Ontology](https://github.com/polifonia-project/music-instrument-ontology/blob/main/ontology/music-instrument.owl),
where `InstrumentRealization` denotes a physical realization. OMARO uses
`sounding-realization` for an occurrence-specific sounding and
`physical-object` for an artefact. The target registry can connect a physical
object to an instrument concept, a component or functional module to its
configuration, a condition state to its object, and a sounding realization to
a performance event. Production, modification, part addition or removal, and
conservation history should use external museum event models rather than be
duplicated here.

Three times must remain distinct: the lifecycle of a claim or decision, the
time during which a target state or configuration existed, and the phenomenon
interval or assessment time of an assessment. Only an actual-attempt
assessment projects its `assessment_time` to `sosa:resultTime`.

### Compact classification claim and assignment envelope

`classification_assertions.jsonl` remains convenient for validation and tabular
exchange, but one row now contains two identifiers:

- `uri` identifies the `ClassificationAssertion`, the proposition-bearing
  entity; and
- `assignment_uri` identifies the `ClassificationAssignment`, the activity
  that generated that assertion.

The assignment holds actor, method, criteria, observation-assessment premises,
and optional inference logic. The assertion holds the target/predicate/classification
proposition and its stance, perspective, applicability, evidence, lifecycle,
and projection participation. RDF links the entity and activity with
`prov:wasGeneratedBy` and `prov:generated`. The activity aligns with CIDOC CRM
`E17 Type Assignment`. An optional `inference_logic_uri` records the rule or
method used, but OMARO does not type the activity as CRMinf `I5 Inference
Making`. CRMinf 1.2.1 requires an existing premise belief and a resulting
conclusion belief, not merely a named logic.

This separation permits two institutions to assert the same target/class
proposition through distinct assignments, or one assignment to be corrected
without pretending that the proposition and the historical act are identical.
The compact JSON envelope is denormalized transport, not ontological identity.

### Compact review event and decision envelope

`review_events.jsonl` follows the same discipline:

- `uri` identifies the `ReviewEvent` activity; and
- `decision_uri` identifies the `ReviewDecision` entity generated by it.

The decision bears its target assertion, validation dimension, outcome,
rationale, scope, evidence, lifecycle, and policy participation. Lifecycle
relations address decisions through `supersedes_decision_uri`,
`suspends_decision_uri`, and `reinstates_decision_uri`. This avoids the category
error of saying that an activity itself is accepted, rejected, suspended, or
superseded.

Evidence remains directional. Every evidence item declares whether it
`supports`, `opposes`, `qualifies`, or `documents` the resource in whose
envelope it occurs. A citation is not automatically favorable evidence, and a
source record can document that a claim occurred without supporting its truth.
The RDF projection uses qualified PROV usage so that the evidence resource and
its role are queryable without changing the evidence resource's identity.

### Expressing a claim without endorsing its base triple

Research on [Expressing Without Asserting
(EWA)](https://ceur-ws.org/Vol-3643/paper7.pdf) demonstrates why disputed,
superseded, hypothetical, or merely reported cultural-heritage claims must stay
queryable without being emitted as ordinary facts. OMARO meets that requirement
with RDF 1.1-compatible reification resources: a qualified assertion records
`rdf:subject`, `rdf:predicate`, and `rdf:object`, but this does not entail the
corresponding base triple. A named projection policy emits the direct triple
only when its recorded rules make that simplification eligible.

OMARO does not adopt the paper's experimental `Conjectures` syntax or its three
knowledge states. Stance, evidence direction, review outcome, lifecycle, and
projection eligibility remain separate because a disputed claim can be well
documented, an accepted review can later be superseded, and publication
authorization is independent again. RDF 1.2 `rdf:reifies` is the preferred
future standards path once that specification and implementation support are
stable; migration must preserve assertion and assignment identities.

### Purpose-qualified mapping exchange

[SSSOM](https://mapping-commons.github.io/sssom/) provides the principal
tabular exchange framework considered for concept mappings. OMARO retains a
qualified `ConceptRelationAssertion` as its authoritative record because
perspective, applicability, evidence direction, authority, review, and
projection policy cannot be assumed to survive a flat mapping row. It also
requires every SKOS mapping assertion to name at least one intended operation:
query expansion, display navigation, data transformation, scholarly
comparison, or an externally governed purpose URI. Structural
broader/narrower/related assertions carry an empty purpose array.

Purpose makes an assertion testable against a consumer task rather than
treating `skos:exactMatch` or a confidence score as blanket fitness. OMARO does
not infer a purpose from the predicate or mapping tool. A flat export must
preserve the purpose through a documented extension or mapping-set metadata,
or explicitly disclose the loss; import requires an accountable purpose
decision instead of a guessed default. The declaration is not proof of
accuracy or losslessness and is never a licence, consent record, cultural
authorization, protocol decision, or permission to expose either concept.

### Observations, criteria, and inference

Two new registries make an organological classification auditable below the
claim layer:

```text
target or target state
    -> observation assessment
    -> actual organological observation and result, when an attempt occurred
    -> governed classification criterion
    -> assignment using an optional named inference logic
    -> classification assertion
```

The JSON registry is an observation-assessment envelope. It distinguishes the
feature of interest from an optional assessed part and identifies the assessed
property, assessment procedure, accountable agent, optional sensor, phenomenon
interval, assessment time, perspective, scope, rights, protocol applications,
evidence, and review status. Its status vocabulary prevents a common data
error:

- `detected` means a result was detected;
- `not-detected` means the procedure looked and returned a negative result;
- `indeterminate` means the attempt did not resolve the result;
- `not-observed` means no observation was made; and
- `not-applicable` means the property or procedure does not apply.

Only `detected`, `not-detected`, and `indeterminate` describe an attempted
observation and may receive SOSA or CRMsci observation typing. `not-observed`
and `not-applicable` remain assessment records, because typing a record as an
observation would contradict its stated outcome.

Accordingly, an assignment links every premise with `omaro:usedAssessment` and
uses the range-restricted `omaro:usedObservation` only for an actual attempt.
This split keeps OWL reasoning from converting a non-observation assessment
into an observation activity.

Results may be a resource, literal, quantity, or numeric range. Quantity and
range results carry a unit URI and may record uncertainty or tolerance. Those
values do not collapse observational uncertainty, inferential confidence,
source trust, scholarly review, and community authority into one score.

`ClassificationCriterion` is a versionable plan for reasoning, not an
observation and not its conclusion. It identifies a criterion type, observable
properties, procedures, scheme and scheme version, possible conclusion
classifications, an optional inference logic, perspective, evidence, rights,
and lifecycle status. Its faceted types include primary vibrator, excitation,
active sound source, resonator, construction, material, bore profile,
pitch-control mechanism, signal path, configuration, actual technique,
intended function, actual use, performer–instrument relation, acoustic
property, manufacture, visual design, ensemble or repertoire role, historical
provenance, geographic distribution, social or ritual function, symbolic
meaning, and community category. Values should be linked through observation
assessments or qualified assignments, not exposed as timeless direct facts.
The organological rationale for keeping these facets independent is developed
in [`ORGANOLOGICAL_FOUNDATIONS.md`](ORGANOLOGICAL_FOUNDATIONS.md).

Legacy MIMO mappings do not acquire invented observation assessments,
observations, or criteria. Empty arrays and absent inference logic honestly
record the limits of the source.
The new registries are a capability; their existence does not prove that
specimens have been inspected or that community knowledge has been reviewed.

### Compound classification expressions

The official [MIMO Hornbostel–Sachs revision](https://mimo-international.com/documents/Hornbostel%20Sachs.pdf)
explains that multicategory instruments can contain full codes joined in a
series and that a suffix at the end may apply across categories. The MIMO
example `422.112-7+422.22-62` describes a Highland bagpipe with a double-reed
chanter, a set of single-reed drones, and a flexible reservoir shared by the
pipes.

`classification_expressions` therefore preserves:

- the exact source notation and grammar URI;
- the scheme version and perspective;
- the ordered member tokens;
- an explicit combination operator;
- optional member classification, assertion, target, and component-role URIs;
- local and shared suffix notation; and
- parse status.

The 26 current MIMO notation values containing `+` are tokenized and marked
`tokenized-uninterpreted`. The tokenizer preserves order and round trips the
source string; it does not guess which code applies to which component or what
a suffix governs. An organology expert may later create an
`expert-interpreted` expression with component targets and explicit local or
shared suffix scope. That status describes the parse, not its review outcome;
review decisions remain attached to classification assertions. No member
classification propagates automatically to the whole instrument.

### Controlled RDF value resources

Closed JSON codes remain compact and validation-friendly. In RDF, the same
values project to persistent SKOS concepts following the pattern
`omaro:{category}-{code}`, for example
`omaro:target-kind-physical-object` rather than the untyped string
`"physical-object"`. This applies to controlled target, stance, scope, review,
evidence, result, policy, protocol, and use-decision categories where the value
is semantically a governed member of a code list.

Mapping purpose is deliberately URI-valued rather than a closed JSON code.
OMARO publishes four recommended SKOS concepts—query expansion, display
navigation, data transformation, and scholarly comparison—but accepts an
externally governed purpose concept when a community, institution, or exchange
profile needs a more precise operation. Cardinality and predicate-family rules
remain closed: mapping predicates need at least one purpose, while structural
relations have none.

The URI resource supplies identity, label, definition, notation, and scheme
membership. It is not an OWL class, and the JSON code is not a second identity.
This improves SPARQL joins, multilingual documentation, mapping, and code-list
versioning without changing the closed-world validation role of JSON Schema.

### Cultural protocols and publication authorization

`ProtocolApplication` records that an externally governed protocol applies to
specified resources, communities, authorities, scopes, and times. It does not
assert copyright ownership, factual correctness, consent, or permission for a
particular action.

`UseDecision` separately records a granted, refused, withheld, or withdrawn
decision for exact target resources, action URIs, purposes, audiences, scope,
authority, and time. A projection policy answers which scholarly claims meet a
view's epistemic rules; a use decision answers whether a concrete action may be
performed. Passing one never implies passing the other.

OMARO 0.1 applies a fail-closed publication preflight. Community-governed
material with a refused, withheld, withdrawn, missing, expired, mismatched, or
otherwise unresolved use decision must cause the public build to fail before
any export is written. Filtering after generation is not accepted because it
can leave the same content in an index, manifest, RDF graph, SQLite table,
search document, checksum list, or archive. Only authorized, sanitized
governance metadata belongs in the public repository. The full operational
rules are in [CULTURAL_GOVERNANCE.md](CULTURAL_GOVERNANCE.md).

### Removal of invalid OntoLex typing

OntoLex defines `Form` as a grammatical realization of a `LexicalEntry`, with
`writtenRep` representing that form. OMARO's source-qualified SKOS-XL labels
do not establish lexical entries, part of speech, morphological paradigms, or
lexical senses. OMARO 0.1 therefore removes both `ontolex:Form` typing and
`ontolex:writtenRep` from label resources while retaining `skosxl:Label` and
`skosxl:literalForm`.

A future lexical module may use OntoLex when it can identify genuine lexical
entries, their grammatical forms and senses, and the authority and scope of
those analyses. The removal is a semantic correction, not a rejection of
OntoLex.

## Related organological and cultural-heritage systems

### CIMCIM, MIMO, LIDO, and Europeana EDM

CIMCIM's [cataloguing procedures](https://cimcim.mini.icom.museum/wp-content/uploads/sites/7/2019/01/Newsletter_14_1989.pdf)
and [care guidance](https://cimcim.mini.icom.museum/wp-content/uploads/sites/7/2019/01/The_Care_of_Historic_Musical_Instruments_small.pdf)
recognize that musical instruments can be grouped by different characteristics
and that object condition and repair history must not be folded into a single
timeless description. OMARO's target kinds, states, observations, assignments,
and perspectives operationalize that lesson while leaving accessioning and
conservation to collection systems.

MIMO uses Hornbostel–Sachs as a versioned classification and supplies a
multilingual instrument thesaurus. MIMO's [contribution
workflow](https://mimo-international.com/MIMO/how-to-join.aspx?_lg=en-US) uses
LIDO, whose 1.1 model already covers object identifiers, repeatable
classifications, measurements, events, administrative metadata, rights, and
digital representations. OMARO should consequently publish a LIDO/MIMO
application profile rather than recreate an object catalogue. Each repeated
LIDO classification should become a distinct assertion and assignment, and a
classification of a detachable part should target the part URI rather than
silently classify its parent object.

MINIM-UK is a useful implementation precedent rather than a new semantic
dependency. Its official [project outputs](https://minim.ac.uk/index.php/about/project-outputs/)
and versioned [cataloguing and metadata
proposal](https://minim.ac.uk/wp-content/uploads/2017/08/MINIM-UK-201_Proposal-for-cataloguing-and-metadata-of-objects-for-MINIM-UK_v1.0.pdf)
document a profile assembled from CIMCIM cataloguing practice, the MIMO LIDO
branch, and the MIMO vocabulary for cross-collection discovery. OMARO should
add one bounded MINIM/LIDO bridge fixture: retain the museum record identifier
as source provenance, resolve the physical object separately from its
classification, turn each repeated classification into its own assertion and
assignment, and preserve record-level rights. The fixture should round-trip
only those declared fields. Until such a fixture is implemented and tested,
OMARO makes no MINIM-UK conformance or lossless-profile claim.

The [Europeana Data Model](https://pro.europeana.eu/page/edm-documentation)
adds a complementary provenance pattern. Its `ore:Proxy` represents a cultural
heritage object as described within a particular provider aggregation, allowing
different and potentially conflicting provider descriptions to remain
distinct. On import, OMARO should retain the proxy and aggregation as source
context, create a distinct assertion and assignment for each classification
occurrence, and classify the resource denoted by `ore:proxyFor` only after its
target kind and identity have been established. The proxy itself is not the
instrument or classification target. Nor is a provider proxy automatically an
OMARO `Perspective`: institutional record provenance does not by itself state a
scholarly standpoint, cultural authority, or applicability scope. EDM
`WebResource`, `ProvidedCHO`, and aggregation rights must also remain attached
to the resources they govern rather than being generalized into permission to
publish every OMARO qualification.

### CIDOC CRM and Linked Art

CIDOC CRM supplies the broader event-centric museum model. OMARO aligns the
classification activity to `E17 Type Assignment`; external CRM records should
carry production, modification, part addition/removal, condition assessment,
measurement, custody, and acquisition. The [Linked Art assignment
pattern](https://linked.art/model/assertion/) provides a practical JSON-LD
analogue: expose simple `classified_as` only in an eligible projection and use
an attribute-assignment path when actor, evidence, date, or competing
interpretations matter.

No OMARO alignment makes a physical object, conceptual instrument type, target
state, or assignment identical to a CIDOC CRM resource merely because their
labels look similar. Bridges must state the exact relation and external model
version.

[ArCo's musical-instrument module](https://w3id.org/arco/ontology/musical-instrument)
is especially close related work. The Musical Instrument module version 1.0,
published within the ArCo ontology network version 2.0, represents a
`MusicalInstrumentTaxon`, with `HornbostelSachsClass` as its specialized
Hornbostel–Sachs taxon. An ArCo bridge should preserve the taxon and catalogue
record as provenance, then create distinct OMARO assertion and assignment
identities when the actor, method, date, and source are known. The ArCo taxon,
the OMARO classification concept, the proposition that assigns it, and the
activity that made that assignment are different resources. They must not be
declared identical merely because they concern the same object and code.

The legacy ArCo terms `MusicalInstrumentClassification` and
`HornbostelSachsClassification` are deprecated and must not be used as targets
for new bridges. Existing data that uses them should be retained as source
provenance and migrated through an explicit, version-aware transformation.

### Performance and instrument ontologies

[DOREMUS](https://data.doremus.org/ontology/) and the [Performed Music
Ontology](https://performedmusicontology.org/ontologies/PerformedMusicOntology.html)
provide richer models for works, performance plans, media of performance, and
actual performance events. Polifonia separates an instrument concept from its
physical realization. OMARO uses resolvable target kinds and external URIs so
these resources can participate without copying their models.

This supports organologically important distinctions:

- what an object affords is not necessarily what its maker intended;
- a medium requested by a work is not necessarily what was used;
- an object's usual classification need not equal an event-specific sounding
  classification; and
- a drum kit or modular synthesizer configuration is not the same kind of
  whole as an ensemble medium.

Library description adds another important level. The 2026
[Library of Congress Medium of Performance Thesaurus](https://www.loc.gov/aba/publications/FreeLCMPT/freelcmpt.html)
names instruments, voices, and ensembles for performance-medium description,
while [MARC 21 field 382](https://www.loc.gov/marc/bibliographic/concise/bd382.html)
can distinguish soloists, doubling, alternatives, partial media, counts, and
media associated with works, expressions, or manifestations. These records
should normally connect to an OMARO `ensemble-medium`, work/expression context,
or performance event. They do not establish which physical specimen was used,
what actually sounded, or which Hornbostel–Sachs class applies. A crosswalk
from LCMPT or another nomenclature to MIMO or Hornbostel–Sachs is therefore a
qualified mapping assertion, not lexical identity.

### Community and regional classifications

A community category belongs in its own governed concept scheme with its own
labels, definitions, relations, versions, authority, rights, and applicability.
It may coexist with Hornbostel–Sachs on the same target. A crosswalk is a
qualified, purpose-specific mapping assertion; it is not evidence that the
community concept is an exact local equivalent of a Hornbostel–Sachs class.

For applicable Indigenous data, the CARE headings—Collective Benefit,
Authority to Control, Responsibility, and Ethics—are a governance checklist,
not a substitute for the relevant People's law, protocol, or authorized
decision. OMARO maps authority and control to exact mandates, protocol
applications, and action-specific use decisions, and maps responsibility and
ethics to directional evidence, attributed review, legal/consent assessments,
and fail-closed publication checks. Collective benefit, benefit-sharing, and
reciprocity require community-evaluated deployment evidence; OMARO does not
invent a universal `beneficial` core decision.

## Explicit non-equivalences

The following distinctions are normative for interpretation and mappings:

| Resource A | Is not equivalent to | Reason |
|---|---|---|
| `ClassificationAssertion` | `ClassificationAssignment` | Proposition-bearing entity versus activity that generated it. |
| `ReviewEvent` | `ReviewDecision` | Evaluation activity versus its decision entity. |
| Evidence that `documents` a claim | Evidence that `supports` it | Occurrence provenance does not establish truth. |
| Perspective holder | Authorized representative | Attribution does not prove a mandate. |
| Authority assignment | Copyright, licence, collective authorization, or individual consent | Each answers a different normative question. |
| Projection-policy eligibility | Permission to publish | Epistemic endorsement and permitted action are independent. |
| Protocol application | Use decision | A protocol applies; a separate decision authorizes or refuses an action. |
| `source-silent` scope | `context-independent` scope | Missing information is not universality. |
| `not-observed` | `not-detected` | No attempt/result versus a negative result from an observation. |
| Physical object | Instrument concept or instrumental role | Artefact identity, category, and event-specific use can differ. |
| Condition state | Instrument configuration | Damage or preservation condition is not the same as functional arrangement. |
| Sounding realization | Performance event | One sounding occurrence may be part of a wider event. |
| Library medium of performance | Physical object or actual sounding | A work/expression-level medium can be intended, alternative, partial, or differently realized in performance. |
| Hornbostel–Sachs concept | OWL class of all instruments | A knowledge-organization concept does not define an essentialist domain class. |
| Compound expression | OWL intersection or automatic whole-object class | Ordered notation can qualify components and suffix scope. |
| `skos:exactMatch` | `owl:sameAs` | Mapping proximity is not identity. |
| SKOS-XL label | OntoLex grammatical form | A thesaurus label does not by itself define a lexical entry or morphology. |
| Local Contexts Label | Licence, rights statement, or OMARO-controlled code | It is an externally governed, community-customized protocol resource. |

## Organological validation priorities

The 0.1 model should be evaluated with concrete cases rather than only class
counts. The minimum expert test set should cover:

1. a Highland bagpipe compound expression with chanter, drones, and shared
   reservoir suffix scope;
2. a double bass classified at object level and separately for arco and
   pizzicato sounding realizations;
3. an alto trombone whose slide or valve configuration is observed before a
   detailed assignment;
4. a tambourine whose membrane and jingles support different or simultaneous
   event-specific classifications;
5. a modular or electro-acoustic instrument before and after a structural
   configuration change;
6. a museum object with distinct original configuration, later modification,
   and present damaged condition;
7. an ordinary physical object that acquires an instrumental role only in a
   performance;
8. a community category coexisting with Hornbostel–Sachs without equivalence;
9. a source citation that documents a mapping while contrary evidence opposes
   it; and
10. a community-governed record whose public build is refused when use
    authorization is missing or mismatched.

These cases test the central claim of OMARO: disagreement and context can be
represented without losing source fidelity, and simplified publication occurs
only through explicit, reviewable policies.
