# Organological assessment model

## Purpose and status

OMARO 0.1 models an organological classification as a qualified conclusion,
not as an intrinsic and context-free property of anything called an
instrument. The model preserves the difference between an object, its parts,
its configuration and condition, what was observed, the rule used to reason
from those observations, the activity that made an assignment, and the
resulting assertion. It can also describe classifications that apply only to a
particular sounding or performance.

The reference dataset is conservative. Its historical MIMO mappings do not
gain invented measurements, criteria, or cultural authority merely because
OMARO can represent them. The canonical target, observation-assessment,
criterion, protocol, and use-decision registries begin empty. The worked
records under
[`examples/organological-assessment/`](examples/organological-assessment/)
are explicitly illustrative and are not canonical evidence about a collection
object or community. The separate
[`examples/multidimensional-analysis/`](examples/multidimensional-analysis/)
fixture demonstrates a reproducible scalogram-style comparison over two
declared criterion selections.

## The assessment chain

The central pattern is:

```text
resolvable target, configuration, state, component, or sounding
    -> assessment of whether a named observation applies or occurred
    -> actual observation attempt, when one occurred, and its result
    -> versioned classification criterion
    -> assignment activity using assessments, criteria, and optional logic
    -> assertion entity bearing perspective, scope, stance, and evidence
    -> independent review decisions
    -> projection policy and, where required, publication authorization
```

Each arrow is traceable, but no step is inferred merely because a later step
exists. A source mapping may document an assertion without documenting any
specimen observation. An observation may be valid while a proposed
classification is rejected. An assessment may instead record that nothing was
observed or that a procedure was inapplicable. A reviewed claim may be
ineligible for public use.

The separation follows established semantic patterns. PROV-O distinguishes an
activity from the entity it generates; SOSA distinguishes an observation, its
feature of interest, observed property, procedure, and result; and CIDOC CRM
models classification as an assignment event. See the official
[PROV-O Recommendation](https://www.w3.org/TR/prov-o/),
[SOSA/SSN Recommendation](https://www.w3.org/TR/2017/REC-vocab-ssn-20171019/),
and [CIDOC CRM release documentation](https://cidoc-crm.org/get-last-official-release).

## 1. Resolve what is being classified

`OrganologicalTarget` prevents the word “instrument” from hiding several
different entities. A classification assertion names one `target_uri` and one
`target_type`. The optional target registry provides the structure and history
needed to resolve that URI.

| Target kind | Use it for | Do not silently treat it as |
|---|---|---|
| `instrument-concept` | A vocabulary concept for a kind of instrument | A physical specimen |
| `physical-object` | One artefact or other physical thing | Every configuration or use of that thing |
| `instrument-component` | A physical part that can be observed or classified | The complete object |
| `functional-module` | A functional sound, signal, control, or interface module | A permanently fixed physical part |
| `instrument-aggregate` | A compound instrument-level whole | An ensemble medium or every member component |
| `instrument-configuration` | A time-bounded arrangement of object, parts, modules, or signal path | The object's identity or condition |
| `condition-state` | A time-bounded preservation or damage state | The intended configuration |
| `sounding-realization` | One actual sounding occurrence or event-relative sounding state | A physical realization in another ontology |
| `performance-event` | The event in which playing or sounding occurs | The sounding of one participant |
| `ensemble-medium` | A planned or described performance medium | The physical objects actually used |

The rename from `instrument_uri` to `target_uri` is consequential. A saw,
bottle, stone, typewriter, or electronic module can be classified for an
instrumental role without asserting that the object is essentially or always a
musical instrument.

Components and configurations need their own URIs when a classification is
about them. `component_of_uri`, `has_component_uris`,
`has_functional_module_uris`, `configuration_of_uri`, and
`condition_state_of_uri` make the level explicit. A component's class never
propagates automatically to its parent.

The validator enforces the intended topology. Only configurations and sounding
realizations can use `configuration_of_uri`; only components, functional
modules, and aggregates can use `component_of_uri`; and a component link must
include a `component_role_uri`. Only a condition state can use
`condition_state_of_uri`. Only a sounding realization can name a
`performance_event_uri`, which must resolve to a performance-event target.
Actual playing techniques belong only on sounding realizations or performance
events. Every `has_component_uris` link must agree with the child's
`component_of_uri`; every functional module must also be listed as a component
and have the correct target kind. Configuration, component, and condition
parent chains must be acyclic.

For example, a detached bassoon key is an `instrument-component` with both a
parent and a component-role URI. The bassoon's present damage is a separate
`condition-state` pointing to the object or configuration. Recording the
missing key directly as a new timeless object type would fail to preserve the
distinction the topology is designed to protect.

## 2. Record assessments without turning absence into a fact

Each JSON row is an observation assessment. It identifies:

- the `feature_of_interest_uri` and optional `assessed_part_uri`;
- the `assessed_property_uri` and `assessment_procedure_uri`;
- the responsible assessment agent, optional sensor, phenomenon interval, and
  assessment time;
- the perspective and applicability scope under which it was recorded;
- evidence, rights, protocols, and review status; and
- a resource, literal, quantity, range, or null result.

The five assessment statuses are not interchangeable:

| Status | Meaning | Result rule |
|---|---|---|
| `detected` | The procedure returned a positive or otherwise detected result | A result is required |
| `not-detected` | The property was sought and the procedure returned a negative result | A result is required so the negative result is explicit |
| `indeterminate` | An observation was attempted but did not resolve the question | The result may be null or may describe the indeterminacy |
| `not-observed` | No observation was made | The result is null |
| `not-applicable` | The property or procedure does not apply to this target | The result is null |

`not-observed` must never be read as `not-detected`. This matters in historical
catalogues: silence about a key, reed, membrane, electrical connection, or
playing technique is not an observation that it was absent.

The RDF projection types only `detected`, `not-detected`, and `indeterminate`
attempts as `sosa:Observation` and CRMsci `S27 Observation`. A `not-observed`
or `not-applicable` row remains an `ObservationAssessment`; it is not an
observation activity. CRMsci 3.2's narrower `S4 Single Observation` is not
asserted because it requires one binary observed proposition.

Quantity results identify a unit URI, normally from
[QUDT](https://www.qudt.org/catalog/qudt-catalog.html), and can record stated
uncertainty or tolerance. Range results record minimum and maximum values.
These fields describe a result, not a universal confidence score. Measurement
uncertainty, inferential confidence, source reliability, review outcome, and
community authority remain separate.

Three time axes must also remain separate:

1. the target configuration or condition interval;
2. the phenomenon interval and assessment time of an assessment; and
3. the lifecycle interval of an assertion, decision, protocol, or authority.

Only an actual-attempt assessment projects its `assessment_time` as
`sosa:resultTime`. A `not-observed` or `not-applicable` assessment retains its
OMARO assessment time but receives no SOSA result-time triple.

## 3. State the criterion and inference explicitly

`ClassificationCriterion` is a versioned plan for reasoning. It identifies the
criterion type, observable properties, procedures, scheme and version,
possible conclusion classifications, author, perspective, applicability
scopes, authority assignments, protocol applications, evidence, rights,
status, and optional inference logic. It is neither the observation nor the
conclusion.

The controlled criterion types cover principal organological facets, including
primary vibrator, excitation, active sound source, resonator, construction,
material, bore profile, pitch control, physical configuration, signal path,
acoustic property, performer–instrument relation, actual technique, intended
function, actual use, manufacture, visual design, ensemble or repertoire role,
historical provenance, geographic distribution, social or ritual function,
symbolic meaning, and community category. Different schemes may legitimately
use different criteria and order them differently. The methodological basis
and grouped facet profile are documented in
[`ORGANOLOGICAL_FOUNDATIONS.md`](ORGANOLOGICAL_FOUNDATIONS.md).

An assignment lists the criteria and observation assessments it actually used.
In RDF, `omaro:usedAssessment` links every such premise;
`omaro:usedObservation` is added only for an assessment that records an actual
`detected`, `not-detected`, or `indeterminate` attempt. This avoids an OWL range
inference turning `not-observed` or `not-applicable` into an observation
activity. A named `inference_logic_uri` records the rule, decision table, or
other method that was applied. It does not by itself justify typing the
assignment as CRMinf `I5 Inference Making`: CRMinf also requires premise and
conclusion beliefs and their proposition sets. That fuller projection is
deferred. See the official
[CRMinf 1.2.1 specification](https://cidoc-crm.org/extensions/crminf/html/CRMinf_v1.2.1.html).

### Chain consistency checks

OMARO validates the declared assessment → criterion → inference → assertion
chain without pretending to prove the scientific conclusion:

1. A criterion referenced by an assertion must govern the same classification
   scheme and, when both records state one, the same scheme version.
2. If the criterion enumerates possible conclusion classes, the asserted class
   must be in that list. The assertion's scopes must be contained in the
   criterion's scopes.
3. If a criterion names an inference logic, the assertion must name the same
   one. If an assertion names a logic while criteria are present, at least one
   referenced criterion must declare it.
4. Every referenced assessment must match the property and procedure
   restrictions of at least one referenced criterion. When premises are
   supplied, each restricting criterion must in turn have a matching
   assessment.
5. An assessment must concern the assertion's target, an explicitly connected
   component/configuration/condition/occurrence, or a registered target that
   realizes the assertion's instrument concept.

Thus an observation of a bagpipe chanter can support an assertion about its
registered configuration because the targets are connected. An unrelated reed
measurement cannot be attached merely because it would make the desired class
plausible. Likewise, a criterion for a different scheme version, a bore
criterion paired only with a material observation, or an inference URI not
declared by the criterion is rejected as an incoherent derivation chain.

## 4. Keep assignment activity and assertion identity separate

One compact classification JSON record contains two identities:

- `assignment_uri` identifies the `ClassificationAssignment` activity: who
  assigned the class, the absolute `classification_method_uri`, and which
  assessments, criteria, expression, and optional inference logic were used;
- `uri` identifies the `ClassificationAssertion` entity: the proposition about
  a target and class, with its stance, perspective, scope, evidence, lifecycle,
  and projection policies.

RDF connects the pair with `prov:generated` and `prov:wasGeneratedBy`. The
assignment aligns with CIDOC CRM `E17 Type Assignment`. This permits two
institutions to produce distinct assignments of the same proposition and lets
an assignment be corrected without identifying a historical activity with its
output.

Evidence is directional. `supports`, `opposes`, `qualifies`, and `documents`
must be selected deliberately. A catalogue page can document that an
assignment occurred without supporting its correctness.

Review follows the same discipline: a `ReviewEvent` activity generates a
`ReviewDecision` entity. Acceptance, rejection, suspension, supersession, and
reinstatement apply to decisions, not to the activity that produced them.

## 5. Preserve compound notation before interpreting it

The MIMO revision explains how full Hornbostel–Sachs codes are joined for
multicategory instruments and how a suffix at the end of the series can apply
to all categories. Its Highland bagpipe example is
`422.112-7+422.22-62`: double-reed chanter with conical bore and fingerholes,
plus single-reed drones with cylindrical bore, with the final flexible-air-
reservoir suffix applying to all pipes. See pages 3–4 of the official
[MIMO Hornbostel–Sachs revision](https://mimo-international.com/documents/Hornbostel%20Sachs.pdf).

`ClassificationExpression` therefore records:

- the exact notation literal and grammar URI;
- an ordered list of member tokens;
- a combination operator;
- optional member classification, assertion, target, and component-role URIs;
- local and shared suffix notation; and
- a parse status.

`tokenized-uninterpreted` means that the original notation round trips but
component targets or suffix scope have not been asserted. An
`expert-interpreted` expression may add those links. This parse status records
structural interpretation, not review approval; review applies to the
classification assertions that use the expression. Neither status licenses an
OWL intersection or automatic whole-object inheritance.

The canonical snapshot tokenizes its 26 source notations containing `+`
without guessing. This is preferable to a confident but false parse.

## 6. Qualify perspective, applicability, and projection

Perspective answers “from whose or which institutional, scholarly, source,
technical, historical, curatorial, or community standpoint?” Applicability
scope answers “under which community, place, period, use, technique,
configuration, language variety, and subject-matter time?” They are different
questions.

Dimensions inside one applicability scope are conjunctive; multiple values
within one dimension are alternatives; multiple scope URIs on an assertion are
alternative complete scopes. `source-silent`, `not-yet-investigated`,
`known-unknown`, and `intentionally-unscoped` remain unresolved. Only an
explicit `context-independent` scope asserts independence from the modeled
context dimensions.

A projection policy can select assertions for a source-faithful, research, or
endorsed view. It cannot turn an unknown scope into universal validity, merge
perspectives, or grant permission to publish.

## Worked case 1: a Highland bagpipe compound expression

This case shows why one object/class pair is insufficient.

### Targets

Create a physical-object target for the illustrative bagpipe, a time-bounded
configuration target, and separate component targets for the chanter, drone
set, and reservoir. The configuration contains the components; the component
roles state `chanter`, `drone-set`, and `air-reservoir` through governed URIs.

### Expression

Preserve `422.112-7+422.22-62` as the expression literal. Use two ordered
members:

| Index | Member notation | Member target | Local suffix | Shared suffix |
|---:|---|---|---|---|
| 1 | `422.112-7` | chanter component | `-7` | — |
| 2 | `422.22-62` | drone-set component | — | `-62` on the expression |

The second member retains its source token for round-trip fidelity while the
expression-level `shared_suffix_notation` states the expert interpretation of
the final suffix. The reservoir target supplies a resolvable component behind
that interpretation. If the source or expert review does not justify this
scope, leave the expression `tokenized-uninterpreted` and the suffix scope
unresolved.

The linked Hornbostel–Sachs resources and the expression tokens deliberately
have different identifier granularity. In the worked fixture, member resource
[`.../318`](http://www.mimo-db.eu/HornbostelAndSachs/318) is the base class with
canonical notation `422.112`, member resource
[`.../328`](http://www.mimo-db.eu/HornbostelAndSachs/328) is the base class with
canonical notation `422.22`, and the whole assertion uses classification
resource [`.../6415`](http://www.mimo-db.eu/HornbostelAndSachs/6415), whose
canonical MIMO notation is `422.112+422.22-62`. The worked expression
`422.112-7+422.22-62` adds an exact local `-7` refinement that is not part of
any of those resource identifiers. OMARO therefore preserves the literal,
ordered source tokens, and local/shared suffixes in the expression record while
using the class URIs as semantic anchors. The expression qualifies the
base-class assertion; it does
not assert that a token string is identical to a linked class resource. If a
source registers an exact full-code concept, that concept must be linked or
mapped separately rather than inferred from the string.

### Observations and assignment

Separate observations can record the chanter's paired-lamella reed and bore,
the drones' single lamellae and bores, fingerholes on the chanter, and the
flexible reservoir connected to the pipe configuration. A criterion identifies
which observations support which Hornbostel–Sachs conclusions. The assignment
uses the observations, criterion, expression, and named inference logic; the
assertion names the configuration or aggregate target.

The model does **not** infer that the whole bagpipe is identical to either
member class, that every later configuration has the same components, or that
the source notation alone proves the observations for a particular specimen.

## Worked case 2: a tambourine across performance techniques

A tambourine has a membrane and jingles. In the MIMO revision, directly struck
drums fall under class `211`, while frame rattles fall under `112.12`; the
specific class depends on construction and on what sounds. The same physical
object can be struck, shaken, or played so that membrane and jingles sound
together. The classification system itself therefore exposes an obvious form
of multiplicity. See the corresponding definitions in the official
[MIMO Hornbostel–Sachs revision](https://mimo-international.com/documents/Hornbostel%20Sachs.pdf).

Model it at three levels:

1. The `physical-object` target retains stable identity and component links.
   Construction observations support object- or component-level claims.
2. Each actual playing occurrence receives a `sounding-realization` target
   linked to a `performance-event`, with its observed
   `actual_playing_technique_uris`.
3. Event-specific assignments classify what sounded in that occurrence. A
   struck-only claim, a shaken-jingles claim, and a simultaneous compound claim
   can coexist because their targets or applicability scopes differ.

Do not attach every technique-specific class directly to the object and expose
them as if all applied continuously. Do not suppress the membrane because the
jingles sounded, or the jingles because the membrane was struck. When both
sound, an explicit compound expression or multiple component assertions is
preferable to a guessed single “dominant” class.

## Worked case 3: a historical bassoon with changing configuration and condition

Consider a synthetic museum bassoon described as having eight keys in an early
document, modified to nine keys, and presently missing one key. These are three
different questions:

- What was the original configuration?
- What later configuration existed after modification?
- What is the object's present condition?

Create one physical-object target, two time-bounded
`instrument-configuration` targets, and one current `condition-state` target.
Historical-document evidence may `documents` or `supports` an observation of
the earlier keywork; a current visual procedure observes the present state.
The missing key belongs in the condition state and must not silently rewrite
the intended nine-key configuration as an eight-key historical configuration.

An object-level Hornbostel–Sachs assignment based on reed and bore may remain
unchanged while a finer historical typology differs by keywork. The criterion
must name the scheme whose conclusion depends on key count. This prevents a
common category error: treating every documented construction feature as if it
were a Hornbostel–Sachs discriminator.

CIMCIM's professional guidance emphasizes careful documentation of object
condition and intervention rather than collapsing them into a timeless
description. See CIMCIM's official
[care guidance for historic musical instruments](https://cimcim.mini.icom.museum/wp-content/uploads/sites/7/2019/01/The_Care_of_Historic_Musical_Instruments_small.pdf).

## Worked case 4: a community category beside Hornbostel–Sachs

This case is deliberately synthetic and must not be read as a statement about
a real community.

A community-governed scheme classifies a particular drum by ceremonial
relationship, lineage, and place. An organologist also proposes a
Hornbostel–Sachs classification from observed construction and excitation.
OMARO records two assertions with different scheme, perspective, criterion,
evidence, authority, and applicability scope. Neither assertion is a translation
or negation of the other.

The safe pattern is:

1. keep the community concept in its own governed concept scheme;
2. record an authorized community perspective and mandate for the exact subject
   matter and scope;
3. make any crosswalk a separate `ConceptRelationAssertion` with one or more
   explicit `mapping_purpose_uris`, evidence, authority, review, and scope;
4. never infer `owl:sameAs` or `skos:exactMatch` from co-classification; and
5. apply a `ProtocolApplication` and a separate action-specific `UseDecision`
   before displaying, indexing, translating, exporting, or reusing the
   community-governed material; and
6. require verified protocol resolution and integrity, active authority that
   covers the resources, scope, and exact action, and separately attributed
   legal-basis and consent determinations for the concrete use.

For example, an organologist may propose `skos:closeMatch` between the
synthetic community category and a Hornbostel–Sachs concept for
`mapping-purpose-scholarly-comparison` only. The same record does not thereby
support query expansion, public display navigation, or data transformation.
Those operations require their own declared purpose and evidence. A structural
`skos:broader`, `skos:narrower`, or `skos:related` claim instead carries an
empty purpose array. No purpose declaration grants a licence or community
permission: protocol application and the exact action-specific use decision
are still evaluated independently.

A scholarly projection may accept the morphological claim while a public
display remains unauthorized. Conversely, a community-authorized display does
not prove the Hornbostel–Sachs assignment. A nominal `granted` value is not
enough. Every applicable protocol needs `resolution_status: verified`, a
digest, and either a matching locally recomputed artifact or an identified
external attestation; machine enforcement requires the local method. The
decision must list every applicable protocol and cover all requested targets
and scopes. The referenced mandate must be active and cover the subject matter
and exact action. Both `documented` and `not-required` legal-basis and consent
states require a reference and accountable assessor. Unknown or blocked legal
basis and unknown, withheld, or withdrawn consent deny publication. Missing or
mismatched permission fails closed before any public artifact is generated.
The complete control contract is in
[CULTURAL_GOVERNANCE.md](CULTURAL_GOVERNANCE.md).

This separation implements the practical direction of the
[CARE Principles](https://www.gida-global.org/careprinciples) and references
community-applied [Local Contexts Labels](https://localcontexts.org/labels/about-the-labels/)
without treating either as a licence or as proof of classification truth.

## Modeling rules for organological contributors

1. Resolve the precise target before choosing a classification.
2. Create a configuration, state, component, or sounding target when the claim
   does not apply to the physical object as a whole across time.
3. Record `not-observed`, `not-detected`, and `indeterminate` distinctly.
4. Name the procedure, assessed property, unit, responsible assessment agent,
   and time needed to interpret a result.
5. Use a criterion only for the scheme and conclusions it actually governs.
6. Link an inference logic only when a documented logic was applied.
7. Preserve exact compound notation before assigning member or suffix scope.
8. Keep source documentation, supporting evidence, opposing evidence, and
   qualifying evidence directional.
9. Treat absent applicability context as unknown, never global.
10. Keep morphological, acoustical, functional, performance, historical, and
    community classifications as qualified perspectives rather than forcing a
    single winner.
11. Do not infer authority from expertise, affiliation, possession, or a public
    source.
12. Run publication authorization independently of epistemic projection.

## Machine-readable worked records

[`examples/organological-assessment/`](examples/organological-assessment/)
contains schema-valid JSON Lines records for the four patterns above. The
manifest identifies the schema for each file. All `example.org` object,
community, authority, and decision URIs are synthetic. The directory is kept
outside `data/canonical/` so that conformance examples cannot be mistaken for
source data, empirical observations, or community authorization.

[`examples/multidimensional-analysis/`](examples/multidimensional-analysis/)
adds a machine-readable comparison over the same three synthetic targets. It
shows that changing the selected criteria changes the nearest neighbour, while
target identity, assessment status, method, perspective, and scope remain
explicit. It is an analytical exchange example rather than a new normative
OMARO record type.
