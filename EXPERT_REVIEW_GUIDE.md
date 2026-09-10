# Expert evaluation guide: OMARO

## Purpose and packet boundary

This packet supports independent evaluation of OMARO ontology 0.1.0. It asks
whether multiple scholarly, institutional, historical, curatorial, and
community perspectives can coexist without turning Hornbostel–Sachs or another
classification into unqualified truth.

The packet is self-contained for conceptual, schema, and implementation review.
It is intentionally not the complete release dataset and cannot reproduce the
full build without the omitted bulk canonical source records and dependency
environment. Small canonical registries, examples, implementation excerpts,
schemas, and conformance tests are included so experts can inspect the exact
semantics. Design rationale in the packet cites only public, independently
verifiable sources.

## Recommended reading order

1. `ORGANOLOGICAL_MODEL.md`, `ONTOLOGY_REFERENCE.md`, and
   `NAMING_AND_IDENTITY.md` — assessment workflow, formal scope, term inventory,
   artifact boundaries, canonical identifiers, and version policy.
2. `ORGANOLOGICAL_FOUNDATIONS.md`, `RELATED_WORK.md`, and
   `INTEROPERABILITY_PROFILES.md` — organological methodology, standards
   evidence, adopted and rejected patterns, and loss-aware bridge profiles.
3. `EXTERNAL_REVIEW_DECISIONS.md` — disposition of the earlier expert review
   that informed the pre-publication model.
4. `MULTIPERSPECTIVITY.md` — conceptual model, limits, policy rules, examples,
   and use cases.
5. `COMPETENCY_QUESTIONS.md` and `DATA_DICTIONARY.md` — questions the model must
   answer and normative record and projection semantics.
6. `CULTURAL_GOVERNANCE.md`, `GOVERNANCE.md`, `REVIEW_PROTOCOL.md`, and
   `DECOLONIAL_COMMITMENTS.md` — authority, disagreement, consent boundaries,
   publication authorization, lifecycle, and release gates.
7. `MODAVIS_VAO_INTEROPERABILITY.md` — supported VAO exchange mapping and the
   explicit MODAVIS non-conformance boundary.
8. `PROVENANCE.md` and `QUALITY_REPORT.md` — what the current MIMO snapshot does
   and does not establish.
9. `W3ID_REGISTRATION.md` and `w3id/` — persistent identifier contract and
   prepared resolver rules.
10. `DATA_DICTIONARY.md` and `INTEROPERABILITY_PROFILES.md` — DCAT, DQV,
    RO-Crate, and deferred collaborative-exchange boundaries.
11. `schema/`, `canonical-registries/`, `examples/`, `conformance/`,
   `ontology/0.1.0/`, `ontology/omaro-core.ttl`, `implementation/`, and
   `tests/` — machine-readable rules, all three isomorphic compact ontology
   serializations, a convenient Turtle alias, and regression coverage.

## What the model is—and is not

OMARO is a formal, provenance-aware knowledge-organization,
classification-assertion, assessment, and governance ontology. It models
schemes, perspectives, assertion and decision entities, generating activities,
targets, observations, criteria, compound expressions, scope, directional
evidence, authority, review, cultural protocols, use decisions, lifecycle, and
projections.

It is **not** a complete musical-instrument domain ontology. It does not
axiomatize construction, material, excitation, acoustic process, performance
practice, social function, or culturally grounded identity. A future domain
module is explicitly scoped in `COMPETENCY_QUESTIONS.md`, but its axioms require
organological and community expert design and were not invented in response to
review.

## Central propositions to evaluate

- Source statement, classification assertion, assignment activity, review
  event, review decision, and direct project assertion are distinct resources.
- Assertion and assignment URIs include target/class, source record, agent, perspective,
  method, and source URI. The same pair may therefore have independently
  evidenced occurrences.
- Seven scope modes distinguish source silence, incomplete investigation,
  known uncertainty, intentional lack of scope, non-applicability, specified
  context, and context-independence. None asserts metaphysical universality.
- Values within one scope dimension are alternatives; populated dimensions are
  conjunctive; multiple scopes are alternative complete scopes.
- Every human/community review has typed, exact authority coverage for agent,
  role, subject matter, dimension, scope, and decision time. Every represented
  community must be covered.
- Review decisions do not collapse to one status. Permanent supersession,
  temporary suspension, and explicit reinstatement affect only named older
  same-target decisions.
- Endorsement is declarative: claim policy membership, eligible lifecycle and
  stance, required independent reviews, scope match, and veto rules all apply.
- A favorable review cannot conceal an active correction, dispute, rejection,
  unverifiability, or withdrawal decision covered by the policy.
- Context-specific accepted claims remain qualified; only
  context-independent claims can become context-free direct triples.
- Project endorsement and authorized community validation remain distinct.
- Epistemic projection and authorization for a publication action remain
  independent; community-governed material fails closed when authorization is
  absent, withheld, refused, withdrawn, expired, or scope-mismatched.
- Legacy source mappings do not acquire invented observations, criteria,
  inference logic, component roles, or cultural authority.

## Current empirical state

| Record type | Count |
|---|---:|
| Concepts | 3,372 |
| Source-derived classification occurrences | 1,872 |
| Concept schemes | 2 |
| Named perspectives | 1 |
| Applicability scopes | 1 (`source-silent`) |
| Projection policies | 3 |
| Authority assignments | 0 |
| Human/community review events | 0 |
| Qualified concept-relation assertions | 0 |
| Mechanically tokenized compound expressions | 26 |
| Contributed organological targets | 0 |
| Contributed observation assessments and criteria | 0 |
| Protocol applications and use decisions | 0 |
| Direct project-endorsed classifications | 0 |

The architecture is multiperspectivity-capable; the present corpus is not yet
empirically multiperspective. The worked assessment examples and synthetic
fixtures establish software behavior, not community validation or completed
organological review.

The documentation follows the reporting areas of the MIRO ontology-reporting
guidelines through a public evidence map in `RELATED_WORK.md`. Reviewers should
still treat that map as a checklist to test, not as a conformance or
certification claim.

## Concrete cases for evaluation

The compound Highland-bagpipe notation `422.112-7+422.22-62` makes a structural
problem visible: multiple sounding components and a shared reservoir cannot be
represented safely by treating `+` as an OWL intersection or by propagating
every component class to the whole object. OMARO preserves ordered member
tokens and unresolved suffix scope until an expert supplies component targets
and a reviewed interpretation.

Two actual MIMO mapping sets make the modeling question inspectable without
inventing a community perspective:

- “Double bass” (`InstrumentsKeywords/3111`) maps to `321.322`, `321.322-5`
  (bare fingers), and `321.322-71` (bow). The proposed interpretation treats
  the detailed alternatives as realization-level, playing-technique-scoped
  occurrences.
- “Alto trombone” (`InstrumentsKeywords/4361`) maps to `423.22` (slide) and
  `423.233.1` (short-air-column valve). The proposed interpretation treats the
  detailed alternatives as object/configuration-level occurrences selected
  from observed construction.

The original occurrences remain MIMO-perspective, `source-silent`,
instrument-concept claims. The proposed contextual occurrences are an
authoring pattern only and have not been added to the canonical dataset without
evidence or review. Reviewers should assess whether the target-level and scope
distinctions are correct, whether a different instrument-domain relation is
needed, and when a broad name concept should instead be divided into narrower
concepts. `MULTIPERSPECTIVITY.md` gives the exact URIs and complete rationale.

## Normative implementation points

- OMARO ontology and canonical JSON Schema: `0.1.0`
- SQLite `PRAGMA user_version`: `20200`
- Projection-policy version: `2.2.0`
- Qualified proposition entity: `omaro:ClassificationAssertion`
- Generating activity: `omaro:ClassificationAssignment`
- Review activity and outcome entity: `omaro:ReviewEvent` and
  `omaro:ReviewDecision`
- Direct classification predicate: `omaro:classifiedAs`
- Original MIMO mapping predicate: preserved in the source graph as
  `skos:exactMatch`
- Qualified SKOS mapping assertions: one or more `omaro:mappingPurpose` values;
  structural SKOS relations: no mapping-purpose value. Review whether the
  declared operation is actually supported, independently from authorization.
- Review lifecycle: `omaro:supersedesDecision`, `omaro:suspendsDecision`, and
  `omaro:reinstatesDecision`
- Evidence direction: `omaro:evidenceRelation` with controlled support,
  opposition, qualification, or documentation roles
- RDF ontology: an `owl:Ontology` resource with a version IRI and typed
  object/datatype properties

The context-aware implementation methods are:

- `Dataset.scope_matches`
- `Dataset.claim_applies_in_context`
- `Dataset.is_directly_endorsed`
- `Dataset.is_endorsed_for_context`
- `Dataset.active_review_decisions`
- `Dataset.review_has_valid_authority`
- `Dataset.community_validation_decisions`
- `Dataset.publication_authorization`
- `Dataset.assert_publication_authorized`

`at` is subject-matter time used for temporal scope matching; `as_of` is the
lifecycle time at which claims, mandates, suspensions, and decisions are
evaluated.

## Project-endorsed policy 2.2.0

A context-free direct assertion requires:

1. explicit claim opt-in to the project-endorsed policy;
2. active `asserted` or `endorsed` stance;
3. a `context-independent` claim scope;
4. authorized acceptance of the `referential` dimension by one organologist;
5. authorized acceptance of the `scholarly` dimension by a different
   organologist;
6. a matching scope on each decision; and
7. no active authorized veto outcome in any listed dimension/authority.

The exact rules are data in `projection_policies.jsonl`, not duplicated SQL.
The build evaluates them once and materializes identical results into RDF and
SQLite. Golden conformance cases compare the Python, RDF, and SQLite outcomes.

## Questions for expert evaluation

### Ontology and epistemology

- Is the proposition entity versus assignment activity distinction the right
  identity boundary?
- Are scheme, perspective, method, stance, evidence, scope, and authority
  sufficiently separate?
- Does “context-independent for named dimensions, method, scheme version, and
  purpose” avoid the problems of an “explicitly universal” claim?
- Is a separate expert-designed instrument-domain module the right boundary?

### Scope

- Are the four unresolved states meaningfully distinct in practice?
- Is `not-applicable` safely defined, or should it be restricted by assertion
  type?
- Are the seven URI dimensions and exact interval sufficient?
- Which semantic containment, exclusion, uncertainty, or temporal relations
  are essential before real contextual deployment?

### Authority and cultural validity

- Are exact role/dimension/subject/scope/time checks an appropriate minimum?
- How should councils, quorum, layered representation, delegation, withdrawal,
  sensitive evidence, and community-controlled records be represented?
- Which authority or decision records may be public, restricted, or only
  referenced?
- Does the model adequately prevent scholarly endorsement from being described
  as community validation?

### Policy and conflict

- Are referential plus scholarly review by two independent organologists the
  right default, or should requirements vary by claim type?
- Should a veto block globally, only in an intersecting scope, or according to
  a precedence rule?
- Does permanent supersession plus explicit suspension/reinstatement cover the
  required lifecycle cases?
- Are additional conflict-of-interest, appeal, compensation, or consent gates
  needed before accepting real contributions?

### Implementations and projections

- Do JSON Schema, model validation, SHACL, RDF, SQLite, CSV, RAG, and site data
  preserve equivalent meanings?
- Do the compact JSON envelopes and normalized RDF/SQLite projections keep
  assertion/assignment and review-event/decision identities distinct?
- Do observation status, criterion, quantity, target-state, component, and
  compound-expression records answer real organological workflows without
  manufacturing facts absent from the source?
- Does the multidimensional fixture adequately demonstrate that analytical
  similarity depends on a declared criterion set, procedure, perspective,
  scope, missing-value policy, and method rather than revealing intrinsic
  identity?
- Does publication authorization reliably prevent governed material from
  entering every output surface, including indexes, manifests, logs, examples,
  and archives?
- Are the OWL declarations strong enough without overclaiming a domain model?
- Should context-qualified direct assertions ever be emitted into named
  contextual graphs, or always remain qualified resources?
- Are the canonical W3ID routes, immutable version targets, content negotiation,
  and persistence obligations in `W3ID_REGISTRATION.md` sufficient for public
  ontology registration?
- Do the DCAT stable/versioned identities, external archive checksum, DQV
  metric definitions and denominators, and RO-Crate graph provide enough
  release context without implying organological correctness or cultural
  authority?
- Are the documented Wikibase and nanopublication loss boundaries sufficient
  to prevent ranks, truthy triples, references, or immutable identifiers from
  being mistaken for OMARO review, endorsement, consent, or permission?

## Known limitations

- There are no real community authority mandates or human review events.
- The default policy is a conservative project decision, not an expert
  consensus standard.
- External controlled URIs may have their own governance limitations.
- Exact URI matching does not yet infer scope hierarchy or temporal overlap.
- The model records authority claims but cannot create legitimacy, consent, or
  agreement.
- Real community-contributed content and access rules require co-designed
  governance, authority evidence, consent where applicable, and publication
  decisions; the presence of corresponding schema fields proves none of these.
- The current MIMO snapshot is neither an official MIMO release nor a completed
  expert validation of Hornbostel–Sachs.
