# Multiperspectivity competency questions

## How to use this document

These questions define observable behavior rather than aspirational features.
The golden machine-readable cases are in
`conformance/multiperspectivity-cases.json`. Current-snapshot answers and
fixture answers are intentionally distinguished.

## Claims and provenance

### CQ1. Which occurrences classify a target under a named scheme version?

Return both assertion-entity and assignment-activity URIs, not only target/class
pairs, with assigning and generating agents, scheme/version, perspective,
method, observation and criterion premises, evidence, scope, lifecycle, origin,
and policy membership. For the current snapshot, the answer contains 1,872
MIMO source envelopes.

### CQ2. Which source statement generated an occurrence?

Follow `source_record_uri`, `source_uri`, and `source_predicate_uri`. The source
witness remains `skos:exactMatch`; the project claim is a qualified
`omaro:classifiedAs` occurrence.

### CQ3. Can the same target/class pair occur more than once?

Yes. Distinct source snapshots, agents, perspectives, methods, or source-local
occurrences receive distinct URIs. Similarity does not merge occurrences.

## Scope and context

### CQ4. Why is an absent scope not context-independent?

Inspect `scope_mode`. `source-silent`, `not-yet-investigated`,
`known-unknown`, and `intentionally-unscoped` yield an unknown match, not a
positive match. Only `context-independent` can support a static direct claim.

### CQ5. Does a specified claim match a supplied context?

Dimensions populated in one scope are AND conditions; values within a
dimension are OR alternatives. Multiple scope URIs are alternative complete
scopes. Exact URI matching is normative in 0.1.

### CQ6. What do `at` and `as_of` mean?

`at` is subject-matter time used to match temporal applicability. `as_of` is
decision/lifecycle time used to determine which claims and reviews are active.

### CQ7. How can one double bass have bowed and plucked classifications?

The current MIMO source maps “Double bass” to `321.322`, `321.322-5` (sounded
by the bare fingers), and `321.322-71` (sounded with a bow). Preserve those as
source-silent `instrument-concept` occurrences. A contextual application adds
separate `sounding-realization` occurrences whose `specified` scopes name an
arco or pizzicato URI in `playing_technique_uris`. The technique-specific
occurrences must not become unqualified claims about every use of the object.

### CQ8. When is an alto trombone a slide or valve labrosone?

The current MIMO source maps “Alto trombone” to `423.22` (slides) and
`423.233.1` (valves with a short air column). These mappings describe the
breadth of the instrument-name concept; they do not assign both constructions
to every specimen. An object-level application inspects the mechanism and
either creates a `physical-object` occurrence with a `specified` scope
naming the mechanism in `instrument_configuration_uris`, or classifies a
separately identified `instrument-configuration` target. In the latter pattern,
the target already embodies the mechanism and the scope records only additional
conditions.

### CQ9. Can one performance differ from an object's usual classification?

Yes. In the published accordion example discussed in
`ORGANOLOGICAL_FOUNDATIONS.md`, the free reeds are unused while keys and
register switches are clicked or tapped. Preserve the object or configuration
classification that describes the accordion, then target the particular
performance event or sounding realization with a separate, technique-specific
idiophonic assertion. The assignment identifies the observed active parts,
actual technique, criterion, evidence, and performance scope. It must not
rewrite the object's class or guess an exact Hornbostel–Sachs number. The
synthetic tambourine fixtures exercise the same target-and-occurrence pattern.

### CQ10. Can different analytical dimensions produce different groupings?

Yes. Represent every selected variable as a criterion with an explicit
property and procedure, and identify the complete variable set, source
dataset, normalization or analysis procedure, and algorithm through the
assignment's method, evidence, source record, and versioned
`inference_logic_uri`. A result from multidimensional scalogram analysis,
clustering, or another faceted comparison belongs to its own versioned scheme,
perspective, and scope. Changing the variables, data, or method produces a new
assignment; proximity does not imply `owl:sameAs` or an exact SKOS mapping.

### CQ10a. Is a cross-scheme mapping suitable for the requested operation?

Select a qualified `ConceptRelationAssertion` only when the requested operation
URI occurs in `mapping_purpose_uris`, then evaluate its perspective, scope,
evidence, stance, lifecycle, review, and policy. A scholarly-comparison purpose
does not imply query expansion or data transformation. Structural
broader/narrower/related assertions have an empty purpose array. Suitability
does not authorize access, display, export, or reuse; applicable protocols and
use decisions answer that separate question.

## Authority and review

### CQ11. Was a reviewer authorized for this exact decision?

Verify every referenced mandate against reviewer agent, typed reviewer role,
decision time, validation dimension, target subject matter, applicability scopes, and
retroactive revocation. A mere perspective label is insufficient.

### CQ12. Does a community review cover every represented community?

For each represented community URI, at least one referenced, valid mandate must
cover that community. One mandate cannot silently stand for the others.

### CQ13. Which active decisions disagree?

Return all active, non-superseded, non-suspended decision occurrences. Do not
collapse them into one review status.

### CQ14. What happens when a successor expires?

Permanent supersession remains effective. A predecessor returns only after an
explicit reinstatement. A separately declared temporary suspension ends at its
`valid_until` time.

## Projection

### CQ15. May a claim be flattened when it did not opt into the policy?

No. Claim policy membership is mandatory even if eligible accepting reviews
exist.

### CQ16. What does the project-endorsed policy require?

For a context-free classification in policy version 2.2.0:

1. the claim opts into the policy and has an eligible stance and active
   lifecycle;
2. claim and supporting reviews use `context-independent` scope;
3. one authorized organological reviewer accepts the referential dimension;
4. a second independent authorized organological reviewer accepts the
   scholarly dimension; and
5. no active authorized decision matches the policy's veto rule.

Context-aware evaluation uses matching specified scopes instead of requiring
`context-independent` scope.

### CQ17. Which disputes would a simplified projection hide?

Evaluate active decisions against `veto_rules` before projection. In the
endorsed policy, correction, dispute, rejection, unverifiability, or withdrawal
in any listed dimension and authority class blocks simplification.

### CQ18. What did an assignment assess or observe, and how did it reach its conclusion?

Follow `assessment_uris` to the feature, optional assessed part, assessed
property, procedure, assessment status, result, responsible assessment agent,
phenomenon interval, and assessment time; then follow `criteria_uris` and
`inference_logic_uri`. Only an actual-attempt assessment projects its
`assessment_time` to `sosa:resultTime`. Empty links on a legacy source mapping
mean that the source did not supply this assessment chain, not that an
observation found no relevant feature. In RDF, follow `omaro:usedAssessment`
for every premise and `omaro:usedObservation` only for premises whose status
records an actual attempt.

### CQ19. How is a compound Hornbostel–Sachs expression interpreted?

Return the exact notation, grammar, ordered members, component targets and
roles when known, local or shared suffix scope, and parse status. The 26 current
MIMO expressions containing `+` are tokenized but uninterpreted. No member class
is inherited automatically by the whole target.

### CQ20. May an eligible claim enter a public output?

Evaluate publication authorization separately from epistemic projection. For
community-governed material, every relevant action, target, purpose, audience,
scope, time, protocol, represented community, and authority mandate must be
covered by an active grant, with no refusal, withholding, withdrawal, expiry,
or ambiguity. Otherwise the entire public build fails before writing output.

### CQ21. Why is a particular occurrence excluded from endorsement?

`Dataset.explain_endorsement` and `omaro query` return the exact evaluator's
policy/version, lifecycle time, scope results, unmet review requirements,
qualifying reviewer identities and veto decision URIs. A local or unresolved
authorized dispute blocks an unqualified projection; a contextual query can
ignore it only when the supplied context proves it disjoint. An empty query
does not establish disjointness. Tests in `tests/test_conformance.py` check
Python/RDF/SQLite agreement and contextual boundary cases.

### CQ22. Can an assignment or review activity share an assertion/decision identity?

No. Canonical validation rejects collisions across these URI sets, SHACL
rejects the corresponding collapsed RDF nodes, and the compact ontology
declares the ten local class disjointness axioms. OWL RL tests also establish
that statement reification does not entail endorsement or merge equal
target/class occurrences (`tests/test_inference_contract.py`).

Executable real-snapshot lookup and SQL/SPARQL recipes, including expected
double-bass results, are in [USE_CASES.md](USE_CASES.md). The source-backed
requirement-to-test map is in
[INFERENCE_AND_VALIDATION.md](INFERENCE_AND_VALIDATION.md).

## Current answers

The current source snapshot has one source perspective, one `source-silent`
scope, no registered authority mandates, and no human/community reviews.
Therefore:

- the research-claims view contains 1,872 qualified occurrences;
- the snapshot contains 26 tokenized compound expressions and no contributed
  target, observation-assessment, criterion, protocol-application, or
  use-decision rows;
- the project-endorsed classification view contains zero rows;
- community-validation queries return no decisions; and
- the data demonstrates representational capacity, not populated plurality or
  validated participation.

## Future-module questions

The following remain deliberate boundaries of schema 0.1 and are acceptance
criteria for later modules or deployment profiles:

- Which expert-governed external vocabularies define components, materials,
  excitations, signal paths, acoustic processes, and configurations beyond the
  generic target/observation-assessment/criterion pattern?
- Which real community procedure, mandate, consent record, and benefit
  assessment authorizes contributed names or knowledge for a particular use?
- Which geographic, language, or community hierarchy version justifies a
  non-exact scope match?
- Which collection, custody, removal, acquisition, restitution, or digital
  surrogate events apply to a physical instrument?
