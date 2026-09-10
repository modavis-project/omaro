# Multiperspectivity, scope, and cultural validity

## Status and purpose

OMARO is a formal, provenance-aware ontology and knowledge-organization system
for classification claims. Its formal scope is assertions, perspectives,
applicability, authority, evidence, review, and governed projection. It is not
a complete domain ontology of musical-instrument construction, acoustics,
performance, social function, or cultural identity.
Hornbostel–Sachs remains one important organological scheme inside the system;
it is not promoted to a perspective-free account of every instrument.

The model can hold Hornbostel–Sachs, another scholarly scheme, a museum working
scheme, and one or more community classifications at the same time. It records
who made each assignment, which scheme version and perspective were used, the
scope in which it is claimed to apply, its evidence, and the independent review
decisions that support or contest it.

The central rule is:

> A source statement, an assignment occurrence, a review decision, and a
> direct project assertion are four different things.

Consequently, `culturally valid` is not a global Boolean. A decision may apply
for a represented community, place, period, language variety, usage domain,
playing technique, or instrument configuration, while another authorized
decision remains active for a different scope or reaches a different outcome.

## Capability versus evidence

The architecture is **multiperspectivity-capable**. The current empirical
snapshot is not yet a multiperspective corpus: all 1,872 classification
assignments are preserved occurrences of MIMO mappings under one MIMO source
perspective. There are no contributed community schemes, authority mandates,
or human/community review events. This is why the research-claims view contains
1,872 records while the project-endorsed direct view contains zero.

Three readiness levels must remain distinct:

1. **Structurally representable:** the schemas and APIs can encode multiple
   perspectives, scopes, authorities, evidence, and disagreements.
2. **Operationally tested:** synthetic conformance cases exercise policy,
   lifecycle, scope, and authority rules across Python, RDF, SHACL, and SQLite.
3. **Empirically established:** real, consented contributions and independent
   reviews exist. The current dataset has not reached this level for community
   or cultural-validity claims.

No software structure can create consent, legitimate representation, or
community agreement. Those are governed human processes whose outcomes may be
recorded here.

## Core resources

### Schemes, concepts, and perspectives

`concept_schemes.jsonl` registers independent terminology and classification
schemes. A concept belongs to exactly one scheme. Similar strings or meanings
do not merge concepts; cross-scheme relationships are qualified claims in
`concept_relation_assertions.jsonl`.

`perspectives.jsonl` identifies a standpoint: for example, a source snapshot,
a named scholarly method, a museum curatorial practice, or a community-held
classification. A perspective records its holder, lifecycle, represented
communities, and relevant authority assignments.

A perspective is attribution, not proof of authority. Calling a record a
“community perspective” is insufficient. Every represented community must be
covered by a matching mandate when a community-origin assignment or community
review is asserted.

### Assignment occurrences

`classification_assertions.jsonl` contains occurrences of an agent assigning a
scheme concept to a target. Despite the historical filename, the record does
not state timeless truth. It records target level, scheme version, claimant and
software generator, perspective, method, criteria, stance, scope, evidence,
authority, lifecycle, projection policies, and source provenance.

Occurrence identity includes the source record, assigning agent, perspective,
method, and source URI as well as the target and assigned concept. Two
independently evidenced occurrences for the same target/class pair therefore
receive different URIs. Label, note, lexical-resource, and evidence identifiers
are likewise occurrence/source-aware. Consumers must never use an array index
or the target/class pair as the occurrence identifier.

The current MIMO mappings are `source-asserted`,
`source-mapping-projection` occurrences. They use the MIMO perspective and the
`source-silent` applicability scope. This preserves what MIMO published without
manufacturing a cultural, contextual, or project-endorsed conclusion.

### Qualified hierarchy and mappings

`source_relations.jsonl` is the preserved MIMO source layer. New scholarly,
project, or community hierarchy and mapping proposals belong in
`concept_relation_assertions.jsonl`. These assertion occurrences carry the same
perspective, scope, evidence, authority, lifecycle, and policy qualifications
as classification assignments. Conflicting relations can coexist without
rewriting the source snapshot.

SKOS mapping predicates additionally require `mapping_purpose_uris`. OMARO's
controlled values cover query expansion, display navigation, data
transformation, and scholarly comparison; an accountable profile may use an
externally governed purpose concept. This allows two perspectives to agree
that concepts are close enough for comparative scholarship while disagreeing
about automated transformation or retrieval expansion. Structural
`broader`/`narrower`/`related` assertions carry an empty array. Purpose is a
claim about operational suitability, not truth, licence, consent, cultural
authorization, or permission, and mapping assertions remain qualified because
a bare SKOS mapping triple cannot retain that distinction.

## Applicability scope

`applicability_scopes.jsonl` distinguishes seven epistemic states:

| Mode | Meaning | Query result before policy handling |
|---|---|---|
| `source-silent` | The preserved source supplied no applicability qualifier. | unknown |
| `not-yet-investigated` | Scope has not yet been researched. | unknown |
| `known-unknown` | Investigation established that the available evidence cannot resolve scope. | unknown |
| `intentionally-unscoped` | A contributor deliberately declines to delimit scope; this is not a universality claim. | unknown |
| `not-applicable` | Context matching is not meaningful for this assertion type. | match |
| `specified` | One or more contextual boundaries are asserted. | match/non-match from the supplied context |
| `context-independent` | For the named target, scheme version, method, and purpose, none of the registered scope dimensions changes the claim. | match |

`context-independent` is deliberately narrower than “universally true.” It
does not assert validity across every ontology, culture, possible purpose, or
future circumstance. Authors must justify this mode; source silence never
implies it.

Within one `specified` scope, populated dimensions are conjunctive, and values
within one dimension are alternatives. Multiple scope URIs on one claim are
alternative complete scopes. Thus:

```text
(community A OR community B) AND place X AND ceremonial use
```

is one scope. “Community A in place X, or community B in place Z” requires two
scope records. Supported dimensions are community, place, period, usage
domain, playing technique, instrument configuration, language variety, and an
exact temporal interval. Use externally governed URIs where possible.

Scopes are provenance-bearing assertions. Correcting their meaning requires a
new scope URI and new or superseding claim/review occurrences; an existing
scope must not be silently redefined.

`Dataset.scope_matches` uses three-valued logic. The four unresolved modes
return `None`; policies then decide whether unresolved scope is included,
excluded, or included with warning. `specified` returns `True` or `False`.

For positive selection, missing a required query dimension is a non-match.
For vetoes it is insufficient evidence of disjointness: a possibly overlapping
authorized dispute blocks contextual endorsement. Any eligible active veto on
the claim, including one with narrower or unresolved scope, blocks a static
direct projection. Supporting reviews still require positive matching scope
(context-independent scope for direct projection). See
[INFERENCE_AND_VALIDATION.md](INFERENCE_AND_VALIDATION.md) for the truth table,
synthetic examples, and executable cross-format evidence.

## Authority and review

`authority_assignments.jsonl` documents a mandate: authorized agent, optional
represented community, role, conferring agent, subject matter, covered review
dimensions, scope, validity interval, delegation, evidence, rights, and
revocation semantics. Authority is checked at the time a decision was made.
A later prospective expiry or revocation does not rewrite history; an explicit
retroactive revocation invalidates earlier uses.

The evaluator requires all of the following:

- the mandate agent equals the reviewing/assigning agent;
- the mandate role matches the declared reviewer authority;
- decision time falls inside the mandate interval;
- the validation dimension, exact target subject matter, and every review
  scope are covered;
- retroactive revocation is absent;
- for community review, every represented community has a matching mandate.

This is a conservative technical minimum, not a complete theory of collective
governance. Real community procedures may require councils, multiple
signatories, quorum, consent records, compensation, access protocols, or
appeals. Such procedures must be co-designed rather than invented by this
repository.

`review_events.jsonl` stores independent, evidence-bearing decisions. Each
event identifies reviewer, authority mandate(s), dimension, outcome,
perspective, communities, scope, evidence, rationale, rights, policies, and
lifecycle.

The dimensions keep different questions separate:

- `referential`: is the target or mapping identified correctly?
- `linguistic`: is a lexical analysis appropriate in scope?
- `community`: does the represented community accept the contextual claim?
- `historical`: is it accurate for the stated period?
- `scholarly`: is it supported under the named research method?
- `ethical`: is the proposed use or presentation appropriate?
- `rights`: are access, attribution, or reuse conditions satisfied?

Reviewer authority is typed independently as `community`, `language`,
`organology`, `history`, `rights`, `technical`, or `ethical`, and the mandate
role must correspond. An organologist may support scholarly validity without
speaking for a community. An authorized community decision may dispute a term
without asserting that the organological analysis is false. Both remain
visible.

### Review lifecycle

A review event may perform at most one lifecycle action:

- `supersedes_decision_uri` permanently replaces a named earlier decision. Expiry
  of the successor does not resurrect the predecessor.
- `suspends_decision_uri` temporarily makes the named decision inactive while the
  suspension is active.
- `reinstates_decision_uri` explicitly restores a suspended decision.

The referenced decision must concern the same target and predate the lifecycle
action. Ordinary expiry and prospective mandate revocation preserve the
historical decision; status and `as_of` determine whether it is currently
effective.

## Projection policies and endorsement

`projection_policies.jsonl` is declarative. A policy lists eligible stances,
required review dimensions/authorities/outcomes, the minimum number of distinct
reviewers, veto rules, context behavior, source-layer inclusion, and version.
The same canonical evaluator materializes Python decisions, RDF direct triples,
and the SQLite endorsed table; conformance fixtures require identical results.

| Policy | Purpose | Direct triples |
|---|---|---|
| source-faithful | Preserve what a named source published. | Only in the separate source graph. |
| research-claims | Expose all qualified occurrences and evidence. | No. |
| project-endorsed | Produce the conservative project view. | Only when every rule passes. |

For policy version 2.2.0, a context-free classification becomes a direct
`omaro:classifiedAs` assertion only when:

1. the claim explicitly opts into the project-endorsed policy;
2. its stance is `asserted` or `endorsed`, and its lifecycle is active;
3. claim and review scopes are `context-independent`;
4. one authorized organology reviewer accepts the `referential` dimension;
5. a different authorized organology reviewer accepts the `scholarly`
   dimension;
6. all authority, scope, lifecycle, and subject-matter checks pass; and
7. no active authorized veto decision has outcome `correction`, `disputed`,
   `rejected`, `unverifiable`, or `withdrawn` in a listed dimension.

One favorable review cannot hide an active dispute. A `correction` outcome does
not endorse the original claim; the corrected statement is a new occurrence
that must itself pass review. A review that does not opt into the requested
policy cannot affect that policy.

Specified claims may be endorsed for a matching query context through
`Dataset.is_endorsed_for_context`; they are not flattened into a context-free
triple. The SQLite distinction is intentional:

```sql
-- All qualified occurrences, including source claims
SELECT * FROM classification_claims;

-- Context-free claims that passed the entire project-endorsed policy
SELECT * FROM classification_targets;
```

The second query currently returns zero rows.

## Actual multiplicity in the MIMO mappings

The current source snapshot already contains cases that make the need for
qualification visible. These are not invented examples: they are MIMO
`skos:exactMatch` mappings preserved by this release and projected as
source-derived `omaro:ClassificationAssertion` occurrences. They demonstrate two
different phenomena that must not be conflated:

- one instrument can be realized through different playing techniques; and
- one general instrument-name concept can cover objects with different
  constructions.

The snapshot still has only one named perspective—the MIMO source perspective.
Multiple source mappings therefore demonstrate **classification multiplicity
and a need for contextual modeling**, not completed multi-stakeholder review or
cultural validation.

### Double bass: one object, different performance realizations

MIMO instrument concept
[`3111`](http://www.mimo-db.eu/InstrumentsKeywords/3111), “Double bass”, has
three mappings in the snapshot:

| Hornbostel–Sachs notation | Concept URI | English class label |
|---|---|---|
| `321.322` | `http://www.mimo-db.eu/HornbostelAndSachs/206` | Necked box lutes or necked guitars |
| `321.322-5` | `http://www.mimo-db.eu/HornbostelAndSachs/6471` | Necked box lutes or necked guitars sounded by the bare fingers |
| `321.322-71` | `http://www.mimo-db.eu/HornbostelAndSachs/6473` | Necked box lutes or necked guitars sounded by bowing with a bow |

The first mapping classifies morphology at a broader level. The other two
introduce playing technique. The same double bass can be bowed in an arco
passage and plucked in a pizzicato passage. It would therefore be misleading
to turn the two technique-specific mappings into timeless, unqualified facts
about every use of the physical object.

The preserved MIMO occurrences correctly remain:

- targeted at the `instrument-concept`;
- attributed to the MIMO source perspective;
- assigned the `source-silent` scope because MIMO supplied no applicability
  record; and
- visible through the source-faithful and research-claims policies, not the
  project-endorsed direct view.

A reviewed application can add—not replace—more precise occurrences. For
example:

| New occurrence | `target_type` | `classification_uri` | Target fact and referenced `specified` scope |
|---|---|---|---|
| Morphological catalogue claim | `physical-object` | `.../HornbostelAndSachs/206` | the inspected object or configuration |
| Arco realization | `sounding-realization` | `.../HornbostelAndSachs/6473` | target `actual_playing_technique_uris = [arco]`; scope `playing_technique_uris = [arco]` when that claim boundary must also be explicit |
| Pizzicato realization | `sounding-realization` | `.../HornbostelAndSachs/6471` | target `actual_playing_technique_uris = [pizzicato]`; scope `playing_technique_uris = [pizzicato]` when that claim boundary must also be explicit |

Here `arco` and `pizzicato` stand for registered, governed technique URIs, not
free-text strings. Each row is a separate assignment occurrence with its own
agent, perspective, method, evidence, source, lifecycle, policies, and review
events. If the application classifies the performance event itself rather than
the instrument as realized in it, `target_type = performance-event` is
available, but that choice must be fixed by the application's profile.

The two technique fields answer different questions.
`actual_playing_technique_uris` belongs to an `OrganologicalTarget` and records
what occurred in that sounding realization or performance event.
`playing_technique_uris` belongs to an `ApplicabilityScope` and states the
technique context in which an assertion is claimed to apply. Neither field
belongs to the assignment. An assignment identifies the target and references
one or more complete scopes.

In compact form, the relevant target, scope, and assignment fields are:

```json
{
  "target": {
    "uri": "https://example.org/realization/double-bass-42-pizzicato",
    "target_kind": "sounding-realization",
    "actual_playing_technique_uris": ["https://example.org/technique/pizzicato"]
  },
  "scope": {
    "scope_mode": "specified",
    "playing_technique_uris": ["https://example.org/technique/pizzicato"]
  },
  "assignment": {
    "target_uri": "https://example.org/realization/double-bass-42-pizzicato",
    "target_type": "sounding-realization",
    "classification_uri": "http://www.mimo-db.eu/HornbostelAndSachs/6471",
    "applicability_scope_uris": ["https://example.org/scope/pizzicato"],
    "perspective_uri": "https://example.org/perspective/cataloguer",
    "classification_method_uri": "https://example.org/organology/method/observed-playing-technique"
  }
}
```

This is an explanatory fragment, not a complete canonical record. The complete
target, scope, and assignment also require the provenance, evidence, lifecycle,
policy, agent, scheme-version, and authority fields defined in
`DATA_DICTIONARY.md` and the JSON Schemas.

### Alto trombone: one name, different mechanical configurations

MIMO instrument concept
[`4361`](http://www.mimo-db.eu/InstrumentsKeywords/4361), “Alto trombone”, has
two mappings in the snapshot:

| Hornbostel–Sachs notation | Concept URI | English class label |
|---|---|---|
| `423.22` | `http://www.mimo-db.eu/HornbostelAndSachs/356` | Labrosones with slides |
| `423.233.1` | `http://www.mimo-db.eu/HornbostelAndSachs/2160` | Valve trumpets with short air column (less than 2 m) |

The Hornbostel–Sachs class label “valve trumpets” is a technical class label;
it does not mean that the catalogued object is vernacularly named a trumpet.
The two mappings indicate that the general name concept can cover a
slide-configured alto trombone and a valve-configured alto trombone. Unlike the
double-bass case, an ordinary physical specimen does not change between these
mechanisms during a performance. The distinction normally belongs to the
object's construction or to a separately identified configuration.

An object-level catalogue must inspect the specimen and create only the
supported occurrence:

| Observed physical object | `target_type` | `classification_uri` | Referenced `specified` scope |
|---|---|---|---|
| Alto trombone with telescopic slide | `physical-object` | `.../HornbostelAndSachs/356` | `instrument_configuration_uris = [slide mechanism]` |
| Alto trombone with valves | `physical-object` | `.../HornbostelAndSachs/2160` | `instrument_configuration_uris = [valve mechanism]` |

The two source mappings must not cause every object labeled “alto trombone” to
receive both detailed classifications. If a rare hybrid or reconfigurable
instrument supports both mechanisms, an application may instead identify each
configuration as its own `instrument-configuration` target. In that pattern the
target already embodies the mechanism; scopes should record only additional
conditions, such as a period of availability, rather than redundantly treating
the mechanism as external context. Provide separate, possibly time-bounded
occurrences and evidence for each configuration.

Here `instrument_configuration_uris` is likewise a field on the referenced
`ApplicabilityScope`, not on the assignment. When the mechanism is represented
as its own `instrument-configuration` target, the assignment instead points to
that target and the scope need not repeat the mechanism.

### Perspective and scope do different jobs

In both examples, `perspective_uri` identifies **whose or which methodological
standpoint** produced the assignment: MIMO, a museum catalogue, a named
organological study, or another authorized source. The applicability scope
identifies **when or for which realization/configuration** the assignment is
claimed to apply. A playing technique or valve mechanism is therefore not
itself a perspective, and a curator's perspective is not a substitute for a
scope. Keeping these fields separate is what permits the system to represent
agreement, alternatives, and genuine disagreement without treating all
multiple mappings as contradictions.

## Additional worked examples

### 1. Preserved MIMO mapping

```json
{
  "uri": "https://example.org/assertion/mimo-occurrence",
  "assignment_uri": "https://example.org/assignment/mimo-occurrence",
  "target_uri": "http://www.mimo-db.eu/InstrumentsKeywords/42",
  "classification_uri": "http://www.mimo-db.eu/HornbostelAndSachs/111.141",
  "classification_scheme_uri": "http://www.mimo-db.eu/HornbostelAndSachs#",
  "assigned_by_uri": "https://example.org/agent/mimo",
  "perspective_uri": "https://example.org/perspective/mimo-source",
  "classification_method_uri": "https://w3id.org/modavis/omaro#classification-method-source-mapping-projection",
  "stance": "source-asserted",
  "applicability_scope_uris": ["https://example.org/scope/source-silent"],
  "authority_assignment_uris": [],
  "projection_policy_uris": [
    "https://example.org/policy/source-faithful",
    "https://example.org/policy/research-claims"
  ],
  "source_record_uri": "https://example.org/source/mimo-snapshot-2026",
  "source_uri": "http://www.mimo-db.eu/HornbostelAndSachs/111.141"
}
```

This is retrievable evidence that MIMO published a mapping. It cannot enter the
endorsed view: it neither opts into that policy nor claims a context-independent
scope, eligible stance, or completed reviews.

### 2. Community-scoped alternative

An authorized community body classifies a particular instrument configuration
under its own scheme for ceremonial use in one place. The contributor creates
the community scheme and perspective, a `specified` scope, the authority
mandate(s), a classification occurrence, and a separate community review. The
MIMO occurrence remains unchanged. A matching contextual application may use
the community assignment; a generic application shows both qualified claims.

### 3. Scholarly acceptance and community dispute

An organological review accepts the scholarly reasoning. An authorized
community review disputes the public terminology in its scope. Both reviews
stay active. The veto rule blocks endorsement in the affected policy/scope,
while a research interface can display the disagreement and evidence.

### 4. Supersession does not resurrect an error

Review R1 accepts a claim. Later R2 supersedes R1 and rejects it. R2 has a
`valid_until` date. After that date, R1 remains superseded; it does not become
active again. A new R3 must explicitly record the next decision.

### 5. Two-review endorsement

Claim C opts into the endorsed policy and has a `context-independent` scope.
Reviewer A has an organology mandate and accepts its referential correctness.
Reviewer B independently has an organology mandate and accepts its scholarly
support. With no veto event, C enters the direct view. If both decisions came
from Reviewer A, the two-independent-reviewer condition would fail.

## Benefits and use cases

- **Comparative organology:** compare several schemes without forcing a master
  hierarchy.
- **Museum cataloguing:** retain Hornbostel–Sachs lookup while presenting
  community terminology and classification only in appropriate contexts.
- **Community-governed description:** attach claims to mandates, scope, rights,
  evidence, expiry, and withdrawal instead of using unsupported “validated”
  labels.
- **Historical research:** keep time-bounded classifications and terminology
  alongside current claims.
- **Configuration/performance analysis:** classify a realization, adaptation,
  or technique without generalizing to every instance of an instrument.
- **Faceted and multivariate comparison:** vary observable dimensions and
  analytical procedures, preserve each method- and dataset-specific grouping,
  and compare the results without treating proximity as identity.
- **Electronic, modular, and smart instruments:** distinguish device,
  functional module, live configuration, performer interaction, sensor
  assessment, and sounding occurrence while linking specialist SMI or
  Internet-of-Musical-Things descriptions.
- **Search and recommendation:** retrieve broadly, then rank or filter by
  perspective, scope, stance, evidence, and policy.
- **Musicological claim integration:** connect published analytic arguments to
  narrower organological assertions with explicit evidence direction rather
  than converting every citation into endorsement.
- **Data integration:** express cross-scheme mappings as qualified proposals,
  avoiding identity based on labels or `skos:exactMatch` alone.
- **Dispute/correction workflows:** supersede, suspend, reinstate, withdraw, or
  contest a decision without erasing provenance.
- **Responsible AI/RAG:** return claimant, perspective, scope, evidence, and
  active disagreement so generated text does not convert a source mapping into
  universal fact.

## Deliberate boundaries and future modules

The following remain valid extensions and deployment responsibilities beyond
the bounded schema 0.1 assessment and governance layer:

- expert-governed domain vocabularies for material, construction, excitation,
  acoustic process, performance practice, social function, and culturally
  grounded roles;
- real community contribution and lexical workflows using co-designed consent,
  attribution, access, protocol, benefit, and withdrawal procedures;
- collective-authority procedures and evidence co-designed with participating
  communities rather than inferred from schema fields;
- semantic scope hierarchies, exclusions, uncertainty weights, and more complex
  temporal logic; and
- active W3ID resolution after the staged rules and public targets are approved
  and verified.

These omissions prevent the project from inventing domain axioms, community
procedures, or preservation promises without the experts and institutions who
must govern them. See `COMPETENCY_QUESTIONS.md`, `DECOLONIAL_COMMITMENTS.md`, and
`EXTERNAL_REVIEW_DECISIONS.md`.

## Authoring checklist

Before adding a non-source assignment or relation:

1. register scheme, concept, agent, perspective, and exact source/version;
2. select one of the seven scope modes and justify it;
3. create an occurrence with evidence and an intended projection policy;
4. record every required mandate before claiming community origin or review;
5. add independent review events without overwriting other decisions;
6. use explicit lifecycle relations for replacement, suspension, or return;
7. run JSON Schema, model, SHACL, relational, and cross-format conformance
   checks.

Never infer community, language variety, cultural validity, consent, or
context-independence from a label, script observation, institution, expertise,
or absence of dispute.
