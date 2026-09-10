# Interoperability profiles

## Scope

OMARO is a focused ontology for qualified organological claims. It is not a
replacement for a museum collection model, an observation-system ontology, a
performance ontology, a unit vocabulary, a general annotation model, or a
mapping-exchange format. Interoperability is therefore based on small,
testable profiles rather than broad imports or unreviewed equivalence axioms.

This document distinguishes three levels:

- **core alignment**: emitted by the OMARO 0.1 RDF projection;
- **bridge profile**: a loss-aware mapping that can be implemented in a
  versioned exporter or importer; and
- **deferred**: a useful relation that is not yet safe or complete enough to
  claim in the release.

An informative bridge does not make OMARO conformant to the external standard.
Each implemented profile needs version-pinned fixtures, round-trip tests, and
a statement of information that cannot be carried across the boundary.

## General mapping rules

1. Reuse a resolvable external object, event, agent, concept, procedure, unit,
   or media URI when it identifies the same resource. Do not mint a duplicate
   merely to keep an OMARO namespace uniform.
2. Do not assert `owl:sameAs` from a shared label, close classification, or
   convenient record match.
3. Preserve occurrence identity. Two assignments with the same target and
   conclusion remain two assignments when their actors, times, evidence,
   methods, or sources differ.
4. Preserve direction. An imported mapping or citation that documents a source
   claim is not automatically supporting evidence.
5. Preserve unknowns. An absent external field maps to unknown or omitted data,
   not to `context-independent`, zero, false, unrestricted, or rejected.
6. Never flatten a component, configuration, condition state, or sounding
   realization into its parent physical object.
7. Run OMARO projection policy and publication authorization after import and
   before any public export. External openness does not override an applicable
   cultural protocol or use decision.

## Profile matrix

| External model | Core alignment | Bridge use | Deliberately not claimed |
|---|---|---|---|
| CIDOC CRM 7.1.3 | Classification assignment | Museum object/event integration | Complete CRM object history or CRM conformance |
| CRMsci 3.2 | Actual observation attempts only | Museum-science observation exchange | Typing non-observation assessments as observations |
| CRMinf 1.2.1 | None emitted into core | Future premise–logic–belief–conclusion profile | Inferring `I5 Inference Making` from a method URI alone |
| SOSA/SSN 2017 | Actual observation attempts, feature, property, procedure, result, time, sensor | Sensor and observation-system integration | Typing `not-observed` or `not-applicable` assessments as observations |
| QUDT | Numeric value and unit on quantity results | Units, quantity kinds, conversions | Inferred unit, dimension, or uncertainty semantics |
| LIDO 1.1 | None imported into core | Museum record and repeated classification exchange | Reimplementation of a collection record |
| Europeana Data Model 5.2.8 | None imported into core | Provider-proxy, aggregation, and digital-resource provenance | Equating a provider view with an OMARO perspective or classified target |
| ArCo network 2.0 / Musical Instrument module 1.0 | None imported into core | Italian cultural-property and musical-instrument taxon exchange | Identity between an ArCo taxon, an OMARO concept, an assertion, or an assignment activity |
| Linked Art | None imported into core | JSON-LD object and assignment presentation | Lossless one-property flattening of qualified claims |
| Web Annotation | None imported into core | Passage, image-region, and media-fragment evidence | Replacing claim or evidence-role semantics |
| SSSOM | None imported into core | Purpose-selected tabular concept-mapping exchange | Identity, truth, losslessness, universal fitness, or permission inferred from a mapping row |
| DCAT 3 | Release metadata | Stable/versioned dataset and distribution discovery | Dataset metadata as claim endorsement or cultural authority |
| DQV | Defined release-quality measurements | Fitness-for-purpose and validation metadata | Automated findings as organological review or certification |
| RO-Crate 1.3 | Release archive descriptor | Offline research-object discovery and preservation | Package licence or integrity as use authorization |
| Wikibase | None imported into core | Future collaborative statement editing | Rank or truthy triples as lossless OMARO semantics |
| Nanopublications | None imported into core | Future citable qualified-assertion packages | Immutability as truth, authority, consent, or revocability |
| Polifonia Music Instrument Ontology | None imported into core | Instrument concept and physical-realization context | Equating `InstrumentRealization` with OMARO sounding realization |
| Smart Musical Instruments Ontology | None imported into core | Sensor-, actuator-, module-, configuration-, and smart-instrument context | Treating smartness, connectivity, or device capability as a Hornbostel–Sachs class |
| Ontology for Analytic Claims in Music | None imported into core | Musicological claim and argument provenance | Treating every analytic claim as an OMARO classification assertion, review, or authorization |
| DOREMUS | None imported into core | Work, performance, casting, and medium context | Copying a performance model into OMARO |
| Performed Music Ontology | None imported into core | Planned and actual performance medium context | Equating requested medium, actual object, and sounding |
| LCMPT 2026 / MARC 382 | None imported into core | Library medium-of-performance and casting context | Treating a work/expression medium as a classified specimen |

## CIDOC CRM, CRMsci, and CRMinf

### CIDOC CRM 7.1.3

OMARO emits each `ClassificationAssignment` as a subclass of CIDOC CRM
`E17 Type Assignment` and uses:

| OMARO role | CIDOC CRM relation |
|---|---|
| assignment target | `P41 classified` |
| assigned classification | `P42 assigned` |
| assigning agent | `P14 carried out by` |

The distinct `ClassificationAssertion` remains a PROV entity generated by the
assignment. This preserves OMARO's proposition-bearing assertion and its
perspective, scope, stance, evidence, and projection state while allowing a
CRM consumer to discover the assignment event.

External CRM resources should carry production, modification, part addition
or removal, condition assessment, measurement, custody, acquisition, and
collection history. OMARO should use those URIs as targets, parts, states, or
source resources rather than duplicate the museum record. The authoritative
model and release files are maintained by the
[CIDOC CRM Special Interest Group](https://cidoc-crm.org/get-last-official-release).

**Boundary:** OMARO does not assert that every target is a particular CRM
class, and its current target relations are not a complete event history. A
future CRM export profile must state how target kinds map and must not infer
object identity from matching accession labels.

### CRMsci 3.2

The current stable release reorganized observation around the general
`S27 Observation` and the narrower `S4 Single Observation`. OMARO assigns
`S27 Observation` only to assessment rows whose status records an actual
attempt: `detected`, `not-detected`, or `indeterminate`. It does not assign
`S4 Single Observation`, because an OMARO result has not necessarily been
expressed as the one binary proposition that class requires. `not-observed`
and `not-applicable` rows remain OMARO `ObservationAssessment` resources and
receive no CRMsci observation type.

Assignments use `omaro:usedAssessment` for every assessment premise and add
`omaro:usedObservation` only for the three actual-attempt statuses. This is a
semantic requirement, not a redundant convenience link: the latter property's
range is `omaro:OrganologicalObservation`, so using it for `not-observed` would
create the very type assertion the status is designed to avoid.

The official [CRMsci release history](https://cidoc-crm.org/crmsci/fm_releases)
defines the extension and its relationship to CIDOC CRM.

**Boundary:** the core does not claim a complete CRMsci path for every
measurement device, dimension, sample, proposition set, or scientific
activity. A CRMsci exporter should be added only with fixtures showing how
categorical, literal, quantity, range, negative, indeterminate, and
not-observed results survive round trip.

### CRMinf 1.2.1

OMARO preserves a named `inference_logic_uri` on an assignment, but emits no
CRMinf class or property in the core projection. CRMinf `I5 Inference Making`
requires an existing `I2 Belief` as premise, an applied `I3 Inference Logic`,
and a resulting conclusion belief. A method URI alone is insufficient.

The official
[CRMinf 1.2.1 specification](https://cidoc-crm.org/extensions/crminf/html/CRMinf_v1.2.1.html)
is the versioned reference.

**Boundary:** a source mapping, cataloguer judgment, or inherited class is not
typed as inference making merely because it has a conclusion or named method.
OMARO does not invent premises for legacy data. A complete CRMinf argument
graph is deferred until premise, belief, logic, and conclusion mappings can be
losslessly tested.

## SOSA/SSN and QUDT

### SOSA/SSN

For an assessment row that records an actual attempt, the RDF projection maps
the observation to the stable 2017
[SOSA/SSN Recommendation](https://www.w3.org/TR/2017/REC-vocab-ssn-20171019/):

| OMARO JSON field or resource | SOSA term |
|---|---|
| Actual `OrganologicalObservation` | `sosa:Observation` |
| `feature_of_interest_uri` | `sosa:hasFeatureOfInterest` |
| `assessed_property_uri` | `sosa:observedProperty` |
| generated result resource | `sosa:hasResult` |
| `assessment_procedure_uri` | `sosa:usedProcedure` |
| `assessment_sensor_uri` | `sosa:madeBySensor` |
| `assessment_time` | `sosa:resultTime` |

The responsible assessment agent, perspective, evidence, applicability,
rights, protocols, review status, and the distinction among `detected`,
`not-detected`, `indeterminate`, `not-observed`, and `not-applicable` remain
OMARO/PROV qualifications.

`not-observed` and `not-applicable` are represented only through OMARO
assessment properties. They do not receive `sosa:Observation`, observation
result, or observation-procedure triples. This avoids asserting that an
activity occurred when the record says it did not.

The newer [SOSA/SSN edition](https://www.w3.org/TR/vocab-ssn-2023/) was still a
Working Draft on the design freeze date. It is monitored, not used to rewrite
the release's normative alignment.

**Boundary:** an external SOSA observation that lacks OMARO's status cannot be
assumed detected. Import must require an explicit rule or leave the status
unresolved for human review.

### QUDT

For a quantity result OMARO emits `qudt:numericValue` and `qudt:unit` alongside
its own result fields. Unit URIs should come from the official
[QUDT catalog](https://www.qudt.org/catalog/qudt-catalog.html). A source unit
must be preserved even when a normalized value is also supplied.

**Boundary:** OMARO does not infer a quantity kind, unit conversion, physical
dimension, uncertainty distribution, or significant figures. Range endpoints,
uncertainty, and tolerance have different meanings and must not be collapsed.
A QUDT conversion profile is deferred until provenance for original and
converted values is represented and tested.

## Museum exchange: LIDO and Linked Art

### LIDO 1.1

LIDO already models object identifiers, classifications, measurements, events,
rights, administrative metadata, and digital resources. OMARO should add
qualified organological claims to that ecosystem rather than reproduce an
object record. The official
[LIDO 1.1 primer](https://lido-schema.org/documents/primer/latest/lido-primer.html)
is the profile baseline.

A proposed LIDO bridge follows these rules:

| LIDO information | OMARO handling |
|---|---|
| Published object identifier | Reuse as `target_uri` for a physical-object assertion |
| Repeated object classification | Create one assertion and one assignment occurrence per classification event/source |
| Classification concept identifier | Use as `classification_uri`; retain the named scheme and version |
| Classification actor, source, date, or method | Attach to the assignment and evidence; do not concatenate into a note |
| Object part identifier | Target the part URI, not the parent object |
| Measurement or condition information | Link an external record or create an OMARO observation/state only when its semantics and provenance are known |
| Rights and record metadata | Preserve independently; do not turn them into classification endorsement or use authorization |

**Boundary:** there is no release claim of a complete LIDO application profile.
Before implementation, fixtures must cover repeated classifications, object
parts, source-only classifications, multilingual labels, rights, and record
updates without losing occurrence identity.

### Linked Art

Linked Art provides a practical assignment pattern for JSON-LD museum data.
Its official
[assertion and assignment model](https://linked.art/model/assertion/)
distinguishes a simple property from an `AttributeAssignment` carrying who,
when, and how an assertion was made.

A proposed bridge exposes a direct `classified_as` only for an OMARO assertion
that is eligible under the named projection policy. Qualified data should use
an assignment path and preserve the OMARO assertion and assignment identifiers
as external references or equivalent nodes in the application profile.

**Boundary:** flattening every accepted assertion to `classified_as` would lose
perspective, scope, stance, contrary evidence, review dimension, and policy.
The bridge must retain those qualifiers or declare the export lossy. A Linked
Art assignment is not automatically identical to an OMARO assignment unless
the event identity is documented.

### Europeana Data Model 5.2.8

The official [Europeana Data Model
documentation](https://pro.europeana.eu/page/edm-documentation) uses
`ore:Proxy` to represent a cultural heritage object as described in a
particular provider aggregation. Several proxies can therefore retain
different descriptions of the resource linked through `ore:proxyFor`, while
`ore:proxyIn` preserves each aggregation context.

A proposed bridge treats the proxy and aggregation as source-record context.
Each imported classification occurrence becomes a distinct OMARO assertion
and assignment with the proxy or its immutable record snapshot as provenance.
The resource linked by `ore:proxyFor` may be reused as the OMARO target only
after identity and target kind have been established; an `edm:ProvidedCHO`
must not be assumed to be a physical object merely from its class name.
`edm:WebResource` identifiers continue to denote digital representations.

**Boundary:** an EDM proxy is not an OMARO `Perspective`,
`ClassificationAssertion`, `ClassificationAssignment`, or organological
target. It establishes provider-view provenance, not epistemic endorsement,
cultural mandate, applicability, or permission for a new use. Rights attached
to a WebResource, ProvidedCHO, or aggregation must remain scoped to that
resource. A bridge must preserve conflicting proxy statements and must not
merge them into one direct fact.

### ArCo network 2.0 / Musical Instrument module 1.0

The Italian Ministry of Culture's [ArCo musical-instrument
module](https://w3id.org/arco/ontology/musical-instrument), version 1.0 within
the ArCo ontology network version 2.0, defines
`arco-mi:MusicalInstrumentTaxon` and specializes it as
`arco-mi:HornbostelSachsClass`. These are taxa in a catalogue knowledge-
organization model, not OMARO assertion or assignment records. The module is
direct related work for national catalogue integration.

A proposed bridge reuses the ArCo cultural-property URI as the OMARO physical
target when identity is established, retains the ArCo taxon and catalogue-
record URIs as source resources, links an ArCo taxon to an OMARO classification
concept only with an evidence-bearing mapping, and creates a distinct OMARO
assertion and assignment occurrence. Known ArCo interpretation criteria,
agents, and dating should be mapped to the matching OMARO assignment or
evidence fields rather than concatenated into a note.

**Boundary:** an ArCo taxon is not automatically the same concept as an OMARO
classification concept and is never the same event or proposition as an OMARO
assignment or assertion. The bridge must state whether it is transcribing an
existing catalogue assertion or recording a new assignment and must preserve
the source catalogue's update history. The deprecated legacy terms
`arco:MusicalInstrumentClassification` and
`arco:HornbostelSachsClassification` must not be targets for new bridges;
legacy instances remain source evidence for a version-aware migration.

## Evidence targeting: Web Annotation

OMARO evidence names a resource and its directional relation to the resource
whose envelope contains it. When the evidence is a passage, image region,
audio segment, video interval, or other fragment, the resource may be a Web
Annotation. The annotation target and selector identify the exact fragment;
the annotation body can carry a transcription, comment, or link. The normative
model is the W3C
[Web Annotation Data Model](https://www.w3.org/TR/annotation-model/).

The existing evidence `resource_uri` may contain the exact URI of that Web
Annotation or of an [IIIF Presentation API 3.0
Annotation](https://iiif.io/api/presentation/3.0/#annotations) targeting an
image region, audio/video interval, or other media fragment. OMARO still records
the directional evidence relation in its envelope. No new core annotation,
selector, or fragment field is required.

**Boundary:** Web Annotation identifies and describes the selected evidence;
it does not replace the OMARO assertion, assignment, observation, or evidence
relation. An annotation's existence does not imply `supports`. Access to a
selector target does not imply permission to redistribute the underlying
media. Fragment identifiers that disclose restricted information must not
enter a public graph.

## Musicological claims: OMAC

The [Ontology for Analytic Claims in Music](https://github.com/HCDigitalScholarship/OMAC)
models scholarly analytic claims about music and their argument context. An
OMAC claim may be linked as a source or as evidence with an explicit OMARO
evidence role. If the claim makes a classifiable organological proposition, a
bridge may create a separate OMARO assertion and assignment while retaining
the OMAC URI and publication as provenance.

**Boundary:** a broad analytic claim is not automatically an OMARO
`ClassificationAssertion`; its argument is not an OMARO `ReviewEvent`; and
publication in a scholarly source does not supply perspective-independent
validity, community authority, legal basis, consent, or permission for reuse.
The bridge must identify the exact proposition and whether the cited material
supports, opposes, qualifies, or merely documents it.

## Mapping exchange: SSSOM

SSSOM provides a tabular exchange model for mappings between semantic
entities. A versioned OMARO mapping exporter can derive an SSSOM row from each
eligible `ConceptRelationAssertion`:

| OMARO value | SSSOM slot |
|---|---|
| subject concept URI | `subject_id` |
| asserted relation URI | `predicate_id` |
| object concept URI | `object_id` |
| asserting agent | `author_id` or the applicable provenance slot |
| assertion method and rationale | mapping justification and comment fields, without conflating them |
| source record and evidence | mapping provenance fields or referenced evidence |
| mapping-purpose URIs | a documented extension or mapping-set metadata when the selected SSSOM release has no lossless row slot; never silently omitted |

The exact slot mapping must follow the selected release of the official
[SSSOM specification](https://mapping-commons.github.io/sssom/).

An exporter accepts an intended operation and selects only assertions whose
`mapping_purpose_uris` include that operation. It must not broaden
`scholarly-comparison` into query expansion or data transformation. Structural
SKOS relations carry an empty purpose array and are not mapping rows merely
because SSSOM can serialize their predicate.

**Boundary:** perspective, mapping purpose, applicability scope, authority,
review decisions, evidence direction, and projection policy may exceed a flat
SSSOM row. An export must either use documented extensions/metadata or declare
those losses. On import, a mapping row requires an explicit purpose supplied by
the importing profile or accountable curator; OMARO does not infer one from
the predicate, tool, or confidence value. The result remains a qualified
mapping assertion rather than a bare SKOS mapping triple. Confidence does not
replace review, authority, cultural validity, legal basis, consent, protocol,
or permission.

## Publication metadata: DCAT 3, DQV, and RO-Crate 1.3

### DCAT 3

The stable dataset URI identifies the maintained dataset, while the versioned
URI identifies the immutable `0.1.0` release. The generated graph uses DCAT 3
version relations between them. A separate catalogue record identifies the
metadata description. The release ZIP is a `dcat:Distribution` with its IANA
package format, byte size, licence, download URL, and an SPDX SHA-256 checksum.

The size and checksum are written to an external DCAT sidecar only after the
ZIP exists. They cannot be embedded in the archive they digest without a
circular dependency. The DOI is an identifier and landing page for the
versioned dataset, not a second dataset identity.

**Boundary:** discovery metadata, a persistent identifier, and checksum
verification do not endorse any classification. They also do not establish
community authority, consent, or permission for a use.

### Data Quality Vocabulary

`dist/metadata/dqv.ttl` publishes typed measurements for explicit repository
metrics, including target resolution, automated findings, review-event count,
and canonical validation. Every measurement names the versioned dataset, its
metric and quality dimension, generation time, and responsible software agent.
Metrics state their expected datatype and any denominator needed to interpret a
rate.

**Boundary:** DQV's subject is dataset fitness for a declared purpose. OMARO
does not type an assertion-level `QualityFinding` as a DQV certificate, equate
a DQV measurement with an organological observation, equate DQV dimensions
with review dimensions, or compute an unexplained overall score. A successful
automated validation is not human organological, linguistic, ethical, or
community review. DQV is a W3C Working Group Note rather than a Recommendation.

### RO-Crate 1.3

The release ZIP is an attached RO-Crate. Its root
`ro-crate-metadata.json` describes the versioned dataset, creator and
affiliation, licence, repository, sources, representative documentation,
examples, generated distribution directory, and complete manifests. It uses
directory-level entities where the generated manifest already inventories
thousands of files.

**Boundary:** RO-Crate makes the package self-describing; it does not replace
the canonical records, `dist/manifest.json`, external cryptographic checksum,
or provenance model. A root licence does not override resource-specific rights,
cultural protocols, or action-specific use decisions. Package integrity is not
truth, endorsement, consent, or cultural validity.

## Collaborative and citable claim exchange

### Wikibase

A future Wikibase profile can map an OMARO classification to a full statement,
use qualifiers for perspective, scope, scheme version, method, stance,
criteria, assessments, expression, validity, and origin, and retain source and
directional evidence as structured references. It must preserve the OMARO
assertion URI in a dedicated property and publish a versioned PID/QID mapping
manifest.

Wikibase rank is a display and selection mechanism, not an OMARO review or
epistemic model. `preferred` is not `endorsed`; `deprecated` is not `rejected`;
a user account is not an authority mandate; and a reference is not always
supporting evidence. Truthy `wdt:` exports omit qualifiers and are unsuitable
for scoped or culturally governed OMARO claims. Built-in labels and aliases
also cannot round-trip OMARO's source-qualified label occurrences, submitted
tags, review states, and SKOS-XL identities.

Implementation therefore waits for a round-trip fixture containing competing
perspectives, unresolved scope, directional evidence, non-observation
assessments, and a community-governed publication decision.

### Nanopublications

The nanopublication separation of assertion graph, assertion-provenance graph,
publication-information graph, and head graph is compatible with OMARO's
claim/activity separation. A future exporter should place the complete
qualified proposition in the assertion graph; assignment, premises, evidence,
source, and agents in assertion provenance; and exporter, creation time,
licence, dataset version, and projection policy in publication information.

`np:Assertion` denotes a graph rather than an OMARO assertion entity. The
nanopublication creator is not automatically the classifier, reviewer, source
author, or cultural authority. A Trusty URI establishes immutability, not
truth, authorship, consent, or authority. Network publication is itself an
OMARO-governed action, and immutable replication can conflict with required
withdrawal. The exporter is deferred until a versioned TriG profile, immutable
revision rules, authorization preflight, and sensitive-content tests exist.

## Music-instrument and performance ontologies

### Polifonia Music Instrument Ontology

Polifonia separates an instrument concept from an instrument realization. A
Polifonia instrument concept can be admitted to a governed OMARO concept
registry with its source scheme and provenance, then linked from
`realizes_instrument_concept_uris`; the current canonical validator does not
accept an unregistered concept URI in that field. A Polifonia physical
realization URI may be reused as the URI of an OMARO `physical-object` target.
The versioned ontology is published in the
[Polifonia Music Instrument Ontology repository](https://github.com/polifonia-project/music-instrument-ontology/blob/master/ontology/music-instrument.owl),
within the official
[Polifonia ontology network](https://polifonia-project.github.io/ontology-network/).

**Boundary:** Polifonia's `InstrumentRealization` denotes a physical
realization. It must not map to OMARO `sounding-realization`, which denotes an
occurrence-specific sounding. No `owl:sameAs` is emitted from a common label or
instrument type.

### Smart Musical Instruments Ontology

The [Smart Musical Instruments Ontology](https://w3id.org/smi#) covers smart
instruments, sensors, actuators, embedded intelligence, connectivity,
applications, services, and related Internet-of-Musical-Things contexts. It is
the preferred specialist graph for those device capabilities.

An OMARO bridge may use a verified device URI as a `physical-object`, identify
current control and signal elements as `functional-module` targets, assemble
them through an `instrument-configuration`, link a sensor through
`assessment_sensor_uri`, and reuse external procedure and observable-property
URIs. The resulting classification still needs its own criterion, evidence,
perspective, scope, assertion, and assignment.

**Boundary:** being networked, sensor-equipped, or computationally intelligent
is not a Hornbostel–Sachs class. A live device configuration and its sounding
realization are time-bounded targets, not permanent identities of every
component. SMI applications and services remain external context rather than
OMARO instrument classes.

### DOREMUS

DOREMUS supplies a richer event-centric model for works, expressions,
performances, casts, and musical media. Its maintained vocabulary is available
from the official [DOREMUS ontology service](https://data.doremus.org/ontology/).
OMARO may reuse a DOREMUS performance URI as a `performance-event` target or
link a sounding realization to that event. A DOREMUS medium or casting can
provide context for an `ensemble-medium` target.

**Boundary:** what a work or performance plan calls for is not automatically
what a physical object afforded or what sounded in a particular event. OMARO
does not copy work/expression/event structures, and it does not infer an
object-level Hornbostel–Sachs class from a planned medium term.

### Performed Music Ontology

The Performed Music Ontology models performed music, including performance
medium and events. The official
[Performed Music Ontology documentation](https://performedmusicontology.org/ontologies/PerformedMusicOntology.html)
can supply event, medium, ensemble, and instrument-context URIs for OMARO
targets and scopes.

**Boundary:** requested medium, actual medium, physical object, player role,
and sounding realization remain distinct. An event-specific OMARO assignment
must identify what it classifies instead of copying a medium label into an
object-level assertion.

### LCMPT 2026 and MARC 21 field 382

The maintained [Library of Congress Medium of Performance
Thesaurus](https://www.loc.gov/aba/publications/FreeLCMPT/freelcmpt.html)
provides terms for instruments, voices, and ensembles. [MARC 21 field
382](https://www.loc.gov/marc/bibliographic/concise/bd382.html) can record
soloists, doubling, alternative or partial media, performer and ensemble
counts, vocabulary source, and identifiers for works, expressions, and
manifestations.

An import should retain the complete field occurrence and its work,
expression, manifestation, or performed-expression context. A planned casting
may become or contextualize an OMARO `ensemble-medium`; a performed-expression
field may contextualize a performance event. Individual term identifiers can
participate in separately governed mappings to MIMO instrument concepts.

**Boundary:** LCMPT is a nomenclature for medium of performance, not a
morphological classification of a physical object. MARC 382 also permits
alternatives and partial statements. Neither source establishes which specimen
was present, what actually sounded, or a Hornbostel–Sachs class without
additional event or object evidence.

## Adoption and deferral register

| Decision | Status in OMARO 0.1 | Requirement before broadening it |
|---|---|---|
| PROV generation of assertions and decisions | Adopted in core | Maintain identity and lifecycle tests |
| CIDOC CRM `E17`, `P41`, `P42`, `P14` | Adopted in core | Recheck against the pinned CRM release |
| SOSA observation core and CRMsci `S27` discovery type | Adopted conditionally | Type only actual attempts; test every result/status variant |
| CRMinf inference graph | Deferred | Represent premise and conclusion beliefs as well as the applied logic |
| QUDT numeric value and unit | Adopted in core | Preserve source value and unit provenance |
| DCAT 3 release metadata | Adopted | Keep stable/versioned identities and external archive checksum tests synchronized |
| DQV defined measurements | Adopted narrowly | Add only metrics with definitions, value types, denominators, and provenance; never imply domain validation |
| RO-Crate 1.3 attached package | Adopted | Validate graph topology, local entities, metadata identity, determinism, and archive membership |
| LIDO import/export | Deferred bridge | Publish an application profile and round-trip fixtures |
| Linked Art JSON-LD export | Deferred bridge | Declare qualifier handling and loss profile |
| Europeana EDM provider-proxy bridge | Deferred bridge | Preserve proxy/aggregation provenance, target identity, digital-resource separation, conflicting descriptions, and resource-scoped rights |
| ArCo musical-instrument classification bridge | Deferred bridge | Preserve catalogue occurrence identity, criteria, provenance, and updates |
| Web Annotation selectors | Deferred evidence profile | Test selector persistence, media access, and redaction |
| SSSOM import/export | Deferred mapping profile | Version slot mappings; require an explicit import purpose; select exports by requested purpose; preserve or declare loss of every OMARO qualifier |
| Wikibase full-statement exchange | Deferred bridge | Preserve identifiers and all qualifiers; test conflicts and governance; prohibit truthy export as a lossless view |
| Nanopublication TriG export | Deferred bridge | Define immutable revision and withdrawal handling, authorization preflight, and qualified-assertion graph tests |
| Polifonia/DOREMUS/PMO links | Adopt by reference | Add reviewed examples without asserting identity |
| SMI Ontology links | Adopt by reference | Validate a smart-instrument configuration example against both models before publishing a normative bridge |
| OMAC claim links | Adopt by reference | Add an evidence-role-preserving example before publishing a normative bridge |
| LCMPT/MARC 382 bridge | Deferred bridge | Preserve work/expression context, alternatives, doubling, counts, and source vocabulary |
| Broad `owl:imports`, equivalence, or same-as mappings | Rejected by default | Require exact semantic proof and version review |

## Profile conformance tests

Every implemented bridge should demonstrate at least:

1. stable URI identity across repeated imports;
2. preservation of assertion and assignment occurrence identity;
3. preservation of target level, component, configuration, state, and event;
4. preservation or explicit declaration of lost perspective and scope;
5. distinct treatment of missing, negative, indeterminate, and inapplicable
   observations;
6. exact unit and original-value provenance;
7. directional evidence and mapping provenance;
8. no automatic `owl:sameAs`, whole-object propagation, or universal scope;
9. independent epistemic projection and publication authorization; and
10. a round-trip comparison whose expected losses are machine-readable.

Until those tests and a versioned mapping document exist, the relevant profile
is a design boundary rather than a conformance claim.
