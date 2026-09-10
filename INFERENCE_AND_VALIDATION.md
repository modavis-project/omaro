# Inference, validation, and explainable projection

## Scope and theoretical basis

OMARO has three different computational responsibilities: describe what follows
from its vocabulary, check submitted records, and select claims under a review
policy. Keeping these responsibilities explicit makes a result reproducible
and prevents a successful schema check from being presented as scientific truth.

OWL uses open-world semantics: missing information need not be false, and
different names need not denote different things. Cardinality axioms can imply
identity rather than report a missing or duplicated database field. OMARO
therefore uses OWL for semantic relations and explicit disjointness, and uses
record validation for required fields and identifier uniqueness. See the W3C
[OWL 2 Primer, sections 4.3, 4.7 and 5.3](https://www.w3.org/TR/owl2-primer/).

RDF reification describes a statement occurrence without entailing its
subject–predicate–object triple. Two occurrences with the same three components
can have different provenance. OMARO preserves that distinction and applies
its explicit endorsement policy before producing a direct classification.
See [RDF 1.1 Semantics, appendix D.1](https://www.w3.org/TR/rdf11-mt/#Reif).

Organological taxonomies can mix construction, excitation and technique along
a tree path. This motivates explicit target, criterion, assessment and method
records instead of interpreting a generic hierarchy edge as a physical law.
Kolozali, Barthet, Fazekas and Sandler (2011),
[“Knowledge Representation Issues in Musical Instrument Ontology Design”](https://ismir2011.ismir.net/papers/PS3-19.pdf),
*Proceedings of ISMIR 2011*, pp. 465–470
([proceedings archive](https://archives.ismir.net/ismir2011/2011_ISMIR_Proceedings.pdf)),
provides a domain-specific rationale. The wider source and reuse decisions are
in [ORGANOLOGICAL_FOUNDATIONS.md](ORGANOLOGICAL_FOUNDATIONS.md) and
[RELATED_WORK.md](RELATED_WORK.md).

## Which mechanism establishes which result?

| Mechanism | Responsibility | What passing does not establish |
|---|---|---|
| JSON Schema | Record structure, datatypes, controlled values and conditional fields | Cross-record referential integrity or scholarly acceptance |
| `Dataset.validate` | Canonical identities, references, provenance, intervals, topology and model-wide contracts | That an assessment happened or an authority mandate is legitimate in the world |
| SHACL | Constraints on an RDF data graph, including local activity/entity separation | An OWL entailment or a community decision |
| Compact OWL vocabulary | Subclass/range consequences and the declared disjointness boundaries | Completeness of a source record, automatic classification, or review-policy execution |
| `Dataset.is_directly_endorsed` | Static direct projection under the named policy and snapshot time | Permission to publish, or validity outside the modeled claim and dimensions |
| `Dataset.is_endorsed_for_context` | Review-policy eligibility in supplied subject-matter context and lifecycle time | A new context-free triple |
| `Dataset.assert_publication_authorized` | Independent publication preflight for applicable governed resources | Epistemic endorsement or general permission for every future use |

SHACL evaluates constraints against a supplied data graph; its
[`sh:not` constraint](https://www.w3.org/TR/shacl/#NotConstraintComponent)
expresses the local type exclusion used here. Cardinality and cross-record
constraints remain in the appropriate validation layer instead of being
silently reinterpreted as inference rules.

The locked environment explicitly includes `rfc3339-validator` and
`rfc3986-validator`. `jsonschema.FormatChecker` otherwise skips these optional
formats when their implementations are absent. URI and datetime rejection is
covered by query regression tests, and the full canonical/schema suite runs
with both validators installed. See the validator's
[format-validation documentation](https://python-jsonschema.readthedocs.io/en/stable/validate/#validating-formats).

## Activity and entity identity

The compact ontology declares each of `ClassificationAssignment` and
`ReviewEvent` disjoint with each of `ClassificationAssertion`,
`ConceptRelationAssertion`, `LabelAssertion`, `NoteAssertion` and
`ReviewDecision`: ten binary `owl:disjointWith` axioms. They make the existing
entity/activity contract explicit without importing a large external ontology.
The pattern follows the entity/activity distinction in
[PROV-CONSTRAINTS, constraint 55](https://www.w3.org/TR/prov-constraints/#entity-activity-disjoint).

The canonical validator rejects intersecting URI sets across those record
roles, including collisions between different rows and registries. The SHACL
`ActivityEntitySeparationShape` rejects a node bearing both an activity class
and one of these entity classes. A per-record JSON Schema cannot enforce the
cross-registry condition. SQLite/RDF generation follows validation; database
keys alone cannot establish it across separate tables.

This is deliberately bounded. A component may play a functional-module role;
those classes are not declared disjoint. No unique-name assumption, global
disjointness of organological targets, `owl:hasKey` over target/class pairs,
or identity from equal labels is introduced.

## Support and veto have different scope obligations

For a static endorsed classification, policy membership, eligible stance,
active lifecycle, context-independent claim scope, all required accepting
reviews and the minimum number of distinct reviewers must hold. Supporting
reviews must themselves have context-independent scope. A qualifying active,
authorized veto on the claim blocks the direct projection even when its scope
is narrower or unresolved.

For contextual endorsement, accepting reviews require a positive scope match.
A veto is ignored only when the supplied context proves it disjoint. This is
an OMARO policy decision about conservative simplification, not an OWL theorem
or an external standard's universal rule.

| Veto scope compared with a contextual query | Effect |
|---|---|
| Explicitly matching | Blocks endorsement |
| Required dimension or subject-matter time omitted | May overlap; blocks endorsement |
| Source-silent or another unresolved mode | May overlap; blocks endorsement |
| At least one populated dimension has explicitly disjoint values, or supplied `at` is outside the interval | Does not block for that scope |
| Several alternative scopes | Blocks if any scope may overlap |

Dimensions are conjunctive; values inside a dimension and complete scope
records are alternatives. A known mismatch therefore proves disjointness even
when another dimension is missing. Time boundaries remain inclusive. All veto
decisions still require exact policy membership, active lifecycle and valid
authority. An unauthorized, expired or superseded decision cannot become a veto
merely by being present in a file.

`scope_matches` retains its existing positive-selection contract: an unresolved
mode returns `None`, and a specified scope with a missing required query value
returns `False`. That last result means insufficient match for selection, not
proof of disjointness. The veto evaluator uses a separate missing-is-unknown
evaluation of the same scope constraints. This distinction is necessary to
avoid treating absent query information as evidence against a dispute.

Synthetic example: two independent authorized reviewers accept a
context-independent claim. A later authorized scholarly dispute applies to
arco technique. The static direct result is false; an arco query is false; an
explicitly disjoint pizzicato query can still be true; an empty query is false.
This illustrates policy mechanics and supplies no empirical judgement about
double-bass classification.

## Explanations and reproducibility

`Dataset.explain_endorsement(assertion, context=None, policy_uri=...)` returns
the evaluator's result, not a second implementation of the policy. `None`
requests the static projection; `{}` requests contextual evaluation without
supplied dimensions. The existing Boolean APIs delegate to it. Its report
includes assertion and policy identifiers, policy version, mode, effective
`as_of`, scope matches, reason codes, active authorized decision identifiers,
veto identifiers, each required dimension's qualifying decisions and reviewer
identities, and reviewer counts. Reason codes are documented in
[USE_CASES.md](USE_CASES.md).

The explanation is a trace of the finite recorded evidence and policy, not a
probability, confidence score, full history of excluded reviews, or proof of
the organological conclusion. Use `active_review_decisions` and the review
records for history. The low-level model API assumes validated in-memory data
and does not itself authorize disclosure. The public query entry point checks
publication authorization and canonical validity before producing its report.
Query `as_of` changes epistemic evaluation only; publication preflight uses the
dataset's publication context and cannot be backdated by this option.

Lifecycle actions are ordered by parsed datetime instants, including UTC
offsets, rather than lexicographic timestamp order. For example,
`02:30+02:00` precedes `01:00Z` on the same date. Review reinstatement and
supersession must respect that chronology; successor-order validation for
review and use decisions likewise compares instants.

## Executable acceptance evidence

| Requirement | Positive example | Boundary example | Executable evidence |
|---|---|---|---|
| Preserve occurrence identity | Two claims with the same target/class remain separate | No inferred `owl:sameAs` between them | `tests/test_inference_contract.py` |
| Keep activities and entities distinct | Separate activity and generated entity | Collapsed node fails SHACL and triggers an OWL RL inconsistency diagnostic; cross-registry URI reuse fails the model | `tests/test_inference_contract.py` |
| Preserve epistemic qualification | Assignment entails its activity type | Reification does not entail `classifiedAs`; SKOS hierarchy does not become an OWL class hierarchy | `tests/test_inference_contract.py` |
| Preserve non-observation | `usedObservation` entails an assessment type | `usedAssessment` alone does not invent an observation | `tests/test_inference_contract.py` |
| Apply local disputes conservatively | Explicitly disjoint context remains eligible | Local dispute blocks Python/RDF/SQLite direct projection | `tests/test_conformance.py`, `conformance/multiperspectivity-cases.json` |
| Make real data usable | Three double-bass occurrences are retrieved with source qualifiers | No source-silent claim becomes endorsed; malformed context is rejected; denied query emits no records | `tests/test_query.py` |

OWL RL tests use the pinned `owlrl` implementation on the generated compact
vocabulary plus small synthetic graphs, without network imports. They test
specific entailment and inconsistency boundaries. They do not certify complete
OWL 2 DL profile conformance, consistency under every external import, or
organological truth. Full distribution tests additionally check the actual
canonical source, generated formats and package inventories.

## Prepublication compatibility decision

These changes repair and make executable the documented 0.1 identity and
no-active-veto contracts. The ontology remains 0.1.0, dataset/tooling 0.1.0 and
SQLite 20200 because the candidate is unpublished; no public version IRI is
being replaced. Canonical fields, source literals, occurrence identifiers and
the SQLite layout do not change. The query context schema describes an
additional tooling input, not a new canonical record type.

The stricter projection can remove a formerly eligible direct assertion when
a narrower or unresolved authorized veto exists. New identity checks can
reject formerly accepted cross-registry collisions. Consumers of earlier local
candidates must regenerate all projections and packages. Any such change
after publication requires a new immutable release and an explicit version
decision. Fresh verification is recorded separately from historical evidence
in [IMPLEMENTATION_VERIFICATION.md](IMPLEMENTATION_VERIFICATION.md).
