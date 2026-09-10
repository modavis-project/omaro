# Organological foundations and methodological profile

## Purpose

OMARO is an ontology for organological claims, the activities that produce
them, their evidential basis, their situated validity, and their review and
publication governance. It is not a claim that one universal hierarchy can
exhaust the identity, construction, sound, use, history, or cultural meaning of
every instrument.

This document explains how established organological methods inform that
boundary and how they are implemented. It complements
[`RELATED_WORK.md`](RELATED_WORK.md), which covers semantic-web,
cultural-heritage, library, observation, and data-governance standards.

## What the organological literature changes

### One characteristic never supplies the whole description

CIMCIM's *Cataloguing Procedures* observes that instruments can be grouped by
place, time, culture, morphology, construction material, and function, and
that grouping by one characteristic separates objects that share another. The
same guidance distinguishes detachable items, the last functional
configuration, later faults, and repair history. These are not merely catalogue
fields: they are different objects of assertion.

OMARO consequently does not attach every classification to an undifferentiated
instrument record. `OrganologicalTarget` distinguishes physical objects,
components, functional modules, aggregates, configurations, condition states,
sounding realizations, performance events, and ensemble media. An assertion
names exactly one target level. Part classifications do not propagate to a
whole, a present fault does not rewrite an earlier configuration, and an
event-specific sounding does not become a timeless property of the object.

Source: [CIMCIM, *Cataloguing Procedures*](https://cimcim.mini.icom.museum/wp-content/uploads/sites/7/2019/01/Newsletter_14_1989.pdf).

### Description can be multidimensional without becoming one larger tree

Mantle Hood proposed the organogram as a compact, comprehensive description
that supplements a Sachs–Hornbostel position with information such as playing
technique, performer–instrument relation, manufacture, and cultural factors.
The important methodological lesson for OMARO is not to reproduce the diagram
as another universal taxonomy. It is to keep independently evidenced
descriptors independent and allow a research question to select the relevant
axes.

OMARO implements this lesson through separate observation assessments and
classification criteria. A material assessment, a performer-action assessment,
a construction assessment, and a use-context assessment can coexist without
being forced into one permanent ordering. A criterion records which of those
assessments a particular assignment used; it does not turn every recorded
descriptor into a Hornbostel–Sachs discriminator.

Source: [Mantle Hood, *The Ethnomusicologist*, 2nd edition](https://books.google.com/books/about/The_Ethnomusicologist.html?id=VOg5AQAAIAAJ).

### Multivariate analysis must preserve its selected dimensions

Lysloff and Matson proposed a non-hierarchical analysis of sound-producing
instruments using a structured set of variables and multidimensional
scalogram analysis. The method can expose similarities hidden by one fixed
tree, but its groupings depend on the selected variables, encoded values,
dataset, and analytical procedure. A computed neighborhood or cluster is
therefore an analysis result, not an intrinsic identity.

In OMARO, every selected variable is represented by a criterion and its
observable-property URI. Their distinction between a broad resonator and a
narrowly tuned sympathetic vibrator is retained through separate
`resonator` and `sympathetic-vibrator` criterion types. The assignment names
the method, complete criterion set, premises, source dataset, perspective, and
scope; `inference_logic_uri` points to the versioned analysis specification.
Any resulting group belongs to a named, versioned scheme and can coexist with
Hornbostel–Sachs. A new variable selection or algorithm creates a new
assignment rather than silently changing the earlier result.

This pattern supports exploratory comparison, collection discovery, teaching,
and similarity search across conventional families. OMARO stores the
reproducible semantics and provenance of the analysis; it does not prescribe a
single clustering algorithm or treat proximity as `skos:exactMatch`.

The machine-readable
[`examples/multidimensional-analysis/scalogram.json`](examples/multidimensional-analysis/scalogram.json)
fixture makes this dependency visible. With the same three synthetic targets,
a membrane-construction profile places a tambourine beside a frame drum, while
a performed-rattling profile places it beside a jingle ring. The accompanying
README documents the distance calculation, unresolved-value handling, and the
mapping from variables and cells to OMARO criteria and assessments.

Source: [René T. A. Lysloff and Jim Matson, “A New Approach to the
Classification of Sound-Producing Instruments”](https://doi.org/10.2307/852139).

### Classification systems embody different concepts and structures

Margaret Kartomi's comparative work treats instrument classifications as
culturally and historically situated systems and distinguishes methodologies
such as taxonomies, keys, paradigms, and typologies, together with downward and
upward grouping. A culture-specific system is therefore not a deficient local
version of Hornbostel–Sachs, and not every classification is a tree.

OMARO keeps each classification or terminology in its own versioned
`skos:ConceptScheme`. The scheme's concepts, relations, labels, governance, and
perspective retain their own identities. An assignment identifies the exact
scheme and version it used. A community or regional category may coexist with
a Hornbostel–Sachs classification of the same target. Any crosswalk is a
qualified `ConceptRelationAssertion`, never an equality inferred from
co-classification or similar wording.

Keys or decision procedures should be named by `classification_method_uri`
and, where a rule was actually applied, `inference_logic_uri`. Paradigmatic or
faceted systems should use several qualified assertions or criteria rather
than an invented `skos:broader` tree. Source-native structures that SKOS cannot
express losslessly remain linked external resources instead of being flattened.

Sources: [Margaret Kartomi, *On Concepts and Classifications of Musical Instruments*](https://research.monash.edu/en/publications/on-concepts-and-classifications-of-musical-instruments/) and [Kartomi, “The classification of musical instruments: changing trends in research”](https://research.monash.edu/en/publications/the-classification-of-musical-instruments-changing-trends-in-rese/).

### A taxonomy is evidence, not the whole domain ontology

Kolozali, Barthet, Fazekas, and Sandler compared musical-instrument taxonomies
through competency-like SPARQL queries. They found that a path through a tree
often mixes family, construction, excitation, playing technique, pitch, and
other relations while exposing only a generic parent–child edge. The tree can
preserve a classification system, but it cannot by itself answer which
property a level encodes or why a particular object belongs there.

OMARO therefore represents Hornbostel–Sachs and other classifications as SKOS
concept schemes and represents their application through qualified assertion
and assignment resources. A `skos:broader` path is never translated
mechanically into an OWL subclass chain for physical instruments. Observable
shape, material, valves, excitation, and technique are modeled as separately
evidenced assessments and criteria. Query tests ask for those explicit
relations rather than attempting to recover them from an unknown depth in a
notation hierarchy.

The paper's performance example is particularly useful: an accordion's reeds
are not used in a specific piece; register switches and keys are instead
clicked and tapped, producing an idiophonic use. OMARO would retain the
object/configuration-level free-reed classification, create a performance
event and sounding-realization target for that occurrence, record the actual
techniques and active sound-producing parts, and attach the performance-
specific idiophonic conclusion only to that occurrence. The two conclusions
answer different target-and-scope questions and do not contradict one another.
The exact idiophone class must be supplied by organological analysis rather
than guessed from the narrative.

Source: [Sefki Kolozali, Mathieu Barthet, György Fazekas, and Mark Sandler,
“Knowledge Representation Issues in Musical Instrument Ontology Design”](https://ismir2011.ismir.net/papers/PS3-19.pdf).

### Organology is classificatory, analytic, and applied

Sue Carole DeVale describes organology as a network involving classificatory,
analytic, and applied work. OMARO's core is strongest in classificatory
organology: it represents a classification conclusion and the accountable
activity that produced it. Its assessment, target, evidence, and event links
support selected analytic questions. It does not claim to replace complete
models of manufacture, acoustics, conservation, performance, social life, or
instrument making.

Those richer records remain in museum, conservation, acoustics, performance,
or community systems. OMARO links their stable resources as targets,
procedures, evidence, events, and values. This boundary keeps the ontology
reusable: a collection need not abandon LIDO or CIDOC CRM, and a performance
project need not abandon its event ontology, to exchange a qualified
organological conclusion.

Source: [Sue Carole DeVale (ed.), *Issues in Organology*](https://schoolofmusic.ucla.edu/resources/ethnomusicology-publications/selected-reports-in-ethnomusicology/selected-reports-vol-viii-issues-in-organology/).

### Facets do not exhaust an instrument's social life

Eliot Bates argues for studying musical instruments within changing,
heterogeneous networks of people, practices, institutions, technologies, and
meanings rather than treating an object as a passive bundle of stable
attributes. This is a necessary limit on any multidimensional model: adding
more descriptive axes to an organogram or database does not by itself produce
a social biography or explain agency, circulation, attachment, conflict, or
historical change.

OMARO can represent qualified conclusions from such research. A study may use
`social-or-ritual-function`, `performer-instrument-relation`,
`historical-provenance`, `actual-use`, or `ensemble-or-repertoire-role`
criteria; target a configuration, condition, performance, or sounding event;
and retain its sources, time, perspective, and applicability. Those facets are
claims selected for a stated inquiry, not the complete social relations of an
instrument. People, production, exchange, custody, repair, circulation,
performance, and institutional events should remain in a suitable social,
museum, archival, or event model and be linked by stable URIs. A later study
may produce a new, equally traceable assignment rather than overwriting the
earlier account.

Source: [Eliot Bates, “The Social Life of Musical
Instruments”](https://doi.org/10.5406/ethnomusicology.56.3.0363).

### Alternative physical principles must remain comparable, not collapsed

Hornbostel–Sachs organizes instruments through a sequence of divisive criteria.
Schaeffner instead begins from vibrating solid bodies and vibrating air;
Sakurai proposed another reconsideration of the primary classes. These systems
show that even apparently physical classifications select and order features
differently.

OMARO therefore treats a class as a concept in a named scheme, not as an OWL
natural kind. The assessed material or sound-producing behavior can be shared
evidence while the conclusion differs by scheme and method. A mapping between
two resulting classes must say whether it is exact, close, broader, narrower,
or merely related, and must retain its evidence, scope, perspective, and
review. It must not be upgraded to `owl:sameAs`.

Sources: [André Schaeffner, *Origine des instruments de musique*](https://classiques.uqam.ca/contemporains/schaeffner_andre/origines_instruments_musique/origines_instruments_musique_tdm.html)
and [Tetsuo Sakurai, “The Classification of Musical Instruments
Reconsidered”](https://doi.org/10.15021/00004491).

### Playing technique is an activity and a frame of reference

Tellef Kvifte's work on traditional and electronic instruments argues against
permanent hierarchies of descriptive variables and places performer action,
instrument control, and musical result in relation. Construction, acoustic
behavior, technique, and culturally meaningful use interact, but they are not
identical.

OMARO consequently separates intended technique from actual technique. An
object or configuration may record intended techniques; an actual technique
belongs to a sounding realization or performance event. Classification of a
performed sounding should target that occurrence rather than attach every
possible technique-specific class to the physical object. Functional modules
and configurations make electronic and modular signal/control arrangements
addressable without assuming that every module is a permanent physical part.

Source: [Tellef Kvifte, *Instruments and the Electronic Age*](https://www.researchgate.net/publication/270819567_Instruments_and_the_Electronic_Age_Toward_a_Terminology_for_a_Unified_Description_of_Playing_Technique).

The same separation permits a bridge to the [Smart Musical Instruments
Ontology](https://w3id.org/smi#). Its sensor, actuator, embedded-intelligence,
connectivity, and audio-processing descriptions can remain in that specialist
model. OMARO can reference a sensor from an assessment, represent a temporary
assembly through functional modules and a configuration target, and classify
the resulting sounding occurrence without treating “smart” as a
Hornbostel–Sachs family or copying an Internet-of-Musical-Things ontology into
the core.

### Field documentation without context is not an adequate instrument record

Geneviève Dournon's handbook treats collection in the field as a way to retain
the social and musical context without which an object record loses much of
its cultural and scientific meaning. For OMARO, a specimen measurement and a
community account are different kinds of evidence, not interchangeable inputs
to one confidence score.

Observation assessments therefore record procedure, responsible agent,
feature, part, property, time, perspective, scope, source, evidence, and
rights. Community knowledge additionally requires explicit authority and any
applicable cultural protocol. A community category is maintained in its own
scheme and cannot be derived solely from morphology. Public permission is
evaluated separately from scholarly acceptance.

Source: [Geneviève Dournon, *Handbook for the Collection of Traditional Music and Musical Instruments*](https://search.worldcat.org/title/Handbook-for-the-collection-of-traditional-music-and-musical-instruments/oclc/44460715).

## Normative distinctions for OMARO data

The following distinctions are required when creating or mapping data:

| Question | OMARO record | Common error prevented |
|---|---|---|
| What exactly is described? | `OrganologicalTarget` and `target_type` | Treating object, component, configuration, condition, and sounding as one thing |
| What property was considered? | `ObservationAssessment` | Treating catalogue silence as a negative observation |
| Did an observation activity occur? | Assessment status and conditional `OrganologicalObservation` typing | Calling `not-observed` an observation |
| Which analytical facet matters? | `ClassificationCriterion.criterion_type` and property/procedure links | Assuming every descriptive feature determines every classification |
| Which system and version supplied the class? | `classification_scheme_uri` and `scheme_version_uri` | Merging structurally different schemes |
| How was the conclusion reached? | `ClassificationAssignment`, criteria, assessments, and optional logic | Confusing a proposition with the act or method that generated it |
| From whose standpoint? | `Perspective` | Treating an institutional record as a neutral view |
| Where and when does it apply? | `ApplicabilityScope` | Promoting missing context to universal truth |
| Who is entitled to decide? | `AuthorityAssignment` | Inferring community authority from expertise or affiliation |
| Is it accepted, disputed, or replaced? | `ReviewEvent` and `ReviewDecision` | Overwriting disagreement with one mutable status |
| May it be displayed, indexed, exported, or reused? | `ProtocolApplication` and action-specific `UseDecision` | Treating epistemic acceptance or a licence as sufficient permission |

## Organological facet profile

`ClassificationCriterion` uses controlled facet types so assignments can be
compared without prescribing one universal order. The profile covers five
families:

| Family | Representative criterion types | Typical question |
|---|---|---|
| Sound production | `primary-vibrator`, `excitation-mechanism`, `active-sound-source`, `resonator`, `sympathetic-vibrator`, `sound-propagation` | What vibrates, how is it excited, and how does the sound propagate? |
| Construction and acoustics | `construction`, `material`, `bore-profile`, `pitch-control`, `tuning-range`, `acoustic-property` | Which physical or measurable properties matter for this method? |
| Electronic and modular systems | `controller-interface`, `signal-generator`, `signal-processor`, `amplifier`, `transducer`, `radiator`, `physical-configuration` | Which current control, signal, and output configuration is classified? |
| Performance relation | `actual-technique`, `performer-instrument-relation`, `ensemble-or-repertoire-role`, `actual-use`, `intended-function` | What did a performer do, what sounded, and in which musical role? |
| Historical and cultural interpretation | `manufacture`, `visual-design`, `historical-provenance`, `geographic-distribution`, `social-or-ritual-function`, `symbolic-meaning`, `community-category` | Which historical, social, or community-governed basis supports this conclusion? |

These codes classify the basis of a criterion, not the instrument. A project
may use an absolute property or procedure URI from a specialist vocabulary.
The `other` code is retained for a documented facet that does not fit the
release profile; repeated use should trigger a proposal to extend the profile.

## Synthetic comparison example

Consider one synthetic electroacoustic performance setup containing a physical
controller, a software sound generator, an amplifier, and a loudspeaker.

1. A configuration-oriented assignment can classify the current functional
   modules and signal path. Its target is the time-bounded
   `instrument-configuration`.
2. A performance-oriented assignment can classify the sounding produced when
   a performer moves the controller. Its target is a
   `sounding-realization`, and the actual technique is recorded on that
   occurrence.
3. A maker or performer terminology may classify the setup in a separate
   technical or community-governed scheme. That assertion has its own
   perspective, criterion, and evidence.
4. A museum catalogue can retain the physical controller and loudspeaker as
   separate collection objects while linking them to the configuration.
5. A smart-instrument record can retain sensor, actuator, service, and network
   details in the SMI Ontology while OMARO records only the qualified
   organological conclusion and the assessments it actually used.

All five records can be true in their stated frames without sharing a class,
target level, or authority. A generic interface may show the qualified records
together. It must not select one as the intrinsic identity of the setup unless
an explicit projection policy makes that simplification eligible.

## Adoption tests for further organological methods

A proposed method or vocabulary is integrated into OMARO only when it passes
all applicable tests:

1. **Distinct question:** it answers a question not already represented by a
   target, assessment, criterion, scope, perspective, evidence, authority, or
   decision.
2. **Category safety:** it does not collapse an object into its use, a part
   into a whole, a classification into a natural kind, or an observation into
   its conclusion.
3. **Source fidelity:** the mapping preserves the external scheme, version,
   and native structure and does not claim stronger identity than the source
   supports.
4. **Cultural validity:** a scholarly mapping cannot manufacture community
   authority, consent, unrestricted access, or an equivalence to a community
   concept.
5. **Executable meaning:** any normative rule has JSON Schema, model,
   SHACL/conformance, and projection tests proportionate to its effect.
6. **Round trip:** source notation and identifiers survive import and export
   even when OMARO cannot yet interpret their full semantics.
7. **Operational value:** the addition enables a documented query, exchange,
   validation, review, or publication use case rather than only increasing the
   class count.

## Expert evaluation questions

Organology reviewers should test the profile with concrete records:

- Can two classification systems use the same assessment but reach different,
  traceable conclusions without contradiction?
- Can a component be classified without the class propagating to its parent?
- Can original configuration, later modification, and present condition be
  retrieved independently?
- Can intended technique, actual performer action, and sounding result differ?
- Can a non-hierarchical or community scheme remain intact without being
  forced into Hornbostel–Sachs?
- Can an organogram-like description be assembled from independent facets
  without turning all of them into one classification?
- Can a source-documented claim remain visible while an opposing review is
  retained and a simplified projection is vetoed?
- Can public use fail closed even when the morphological classification is
  scholarly accepted?

The worked machine-readable cases in
[`examples/organological-assessment/`](examples/organological-assessment/)
exercise the target, assessment, criterion, inference, compound-expression,
performance, historical-state, and community-governance parts of this method.
