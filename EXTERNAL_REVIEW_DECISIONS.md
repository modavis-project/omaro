# External review decision record

## Purpose and status

This record evaluates the external expert review received on 2026-08-28 and
states what changed in response. It is normative for the disposition of review
recommendations, but it does not turn the reviewer's proposals into project
requirements merely by repeating them.

The review was persuasive on the framework's actual boundary: this project is
a provenance-aware, multiperspectivity-capable knowledge-organization and
classification-assertion framework for Hornbostel–Sachs/MIMO. Its formal
ontology concerns claims, provenance, perspective, applicability, assignment
activities, observations, criteria, authority, review, lifecycle, governed
publication, and projection. Its bounded organological assessment layer is not
a complete domain ontology of instrument materials, acoustics, performance,
museum history, or social constitution.

## Dispositions

| Review point | Decision | Result |
|---|---|---|
| Characterize the project more precisely | Accepted | README and conceptual documentation distinguish the SKOS knowledge-organization layer, the assertion/governance ontology, and the prospective instrument-domain module. |
| Distinguish architectural from empirical multiperspectivity | Accepted | Documentation now separates model readiness, populated plurality, and validated participation. Only model readiness is currently demonstrated. |
| Direct endorsement omitted claim policy membership | Accepted as a defect | `Dataset.is_directly_endorsed` now rejects a claim that does not itself name the requested policy. The machine-readable conformance suite verifies identical Python, RDF, and SQLite results. |
| One favorable review could hide an active dispute | Accepted | Projection policies now contain conjunctive `review_requirements`, an overall `minimum_independent_reviewers`, and `veto_rules`. The endorsed policy requires independent accepted referential and scholarly reviews and blocks any covered active correction, dispute, rejection, unverifiable, or withdrawal decision. |
| Expiring a successor resurrected its predecessor | Accepted as a defect | Supersession is permanent event history. Expiry or withdrawal of a successor does not reactivate the named predecessor. Temporary suspension and explicit reinstatement are separate lifecycle actions. |
| Lifecycle validation was inconsistent | Accepted | Classification, perspective, scope, authority, review, and qualified concept-relation intervals are checked by the canonical validator. RDF dates are typed, and SHACL-SPARQL enforces interval ordering. |
| Authority coverage was under-enforced | Accepted with a bounded implementation | Review decisions require one or more competence/mandate records. Exact agent, typed reviewer-role, decision-time, validation-dimension, subject-matter, target-scope, and retroactive-revocation checks are enforced. Community reviews require mandate coverage for every represented community. A community perspective cannot bypass authority by using another origin label. |
| Authority needs collective, delegated, dissenting, compensation, and conflict procedures | Accepted as a governance requirement, deferred as a final data model | These structures require community co-design and real institutional roles. The project will not invent representative procedures on a community's behalf. Current exact mandate semantics are documented as a conservative minimum, not a completed theory of authority. |
| `unknown-or-unscoped` collapsed distinct states | Accepted | It is replaced by `source-silent`, `not-yet-investigated`, `known-unknown`, `intentionally-unscoped`, `not-applicable`, `specified`, and `context-independent`. The current MIMO mapping scope is specifically `source-silent`. |
| Replace metaphysical universality | Accepted | `explicitly-universal` is replaced by `context-independent`. It means independent of the scope dimensions for the named scheme version, method, target, and purpose—not universally true in every ontology or culture. |
| Add hierarchical or probabilistic scope matching | Valid, deferred | Exact URI matching remains normative in 0.1. Geographic containment, community/subgroup relations, uncertain time, exclusion, and probabilistic scope require declared external-vocabulary versions and conflict semantics before implementation. |
| Scope resources should be immutable/versioned | Accepted as an authoring invariant | Published scope URIs identify immutable expressions. A changed scope receives a new URI; modifying a referenced scope in place is prohibited by governance. Content-addressed scope IDs remain a future tooling improvement. |
| Pair-based assignment identifiers contradicted occurrence identity | Accepted | Source classification IDs now include source record, assigning agent, perspective, method, and source occurrence. Lexical/note IDs include their source snapshot and agent. Evidence RDF identifiers use evidence content rather than list position. |
| Too much meaning lived only in Python/SQLite | Accepted in part | Review policy expressions are canonical JSON/RDF data; lifecycle constraints are in SHACL-SPARQL; dates are typed; a golden conformance suite is published. SQLite's static endorsed table is materialized from the same Python evaluator used by RDF generation, preventing an independent SQL policy dialect from drifting. A fully portable rule engine remains future work. |
| Publish competency questions | Accepted | `COMPETENCY_QUESTIONS.md` and `conformance/multiperspectivity-cases.json` define required questions and golden outcomes. |
| Add `owl:Ontology`, version information, typed properties, PROV-O/CIDOC CRM mappings | Accepted conservatively | RDF publishes an `owl:Ontology` resource, version IRI/information, typed dates, PROV entity/activity separation, CIDOC CRM `E17 Type Assignment`, and conditional SOSA/CRMsci `S27 Observation` typing for actual observation attempts. CRMinf is deferred until premise and conclusion beliefs and proposition sets can be represented. Broad imports and equivalence remain excluded. |
| Replace the repository namespace | Accepted before publication | OMARO uses the staged persistent namespace `https://w3id.org/modavis/omaro#`. Resolver activation remains contingent on upstream W3ID registration and verified public targets. |
| Add a formal organological domain ontology | Accepted as a bounded assessment layer | Schema 0.1 adds targets, configurations, components, condition states, observations, results, criteria, sounding realizations, and compound expressions. It does not invent complete material, acoustic, performance, museum-event, or culturally grounded taxonomies. Hornbostel–Sachs concepts remain SKOS concepts and conclusions remain qualified assertions. |
| Add first-class contributed lexical assertions | Accepted as governed capability, not represented as completed participation | Existing assertion and label-profile patterns are combined with authority, protocol applications, action-specific use decisions, rights, consent boundaries, display/search controls, and withdrawal. The reference snapshot contains no community-contributed records or community authorization claim. |
| Integrate decolonization | Accepted as architecture and practice, not a completion label | `DECOLONIAL_COMMITMENTS.md` defines operational requirements and evidence gates. The project describes itself as decolonization-aware, not decolonized. No community authority or participation is fabricated. |
| Expert packet claimed executable self-containment | Accepted as a documentation defect | The guide now states that the review ZIP is conceptually self-contained but deliberately not a build-reproduction archive because bulk canonical data and registries are excluded. |

## Why some valid recommendations are not implemented immediately

A formal instrument-domain ontology, a contributed community lexical model,
semantic community/geography hierarchies, and collective authority procedures
would materially determine other people's knowledge and governance. Building
placeholder classes without domain or community co-design would create the
appearance of completeness while reproducing the exact authority problem this
framework is intended to expose. These items therefore have explicit module
boundaries and acceptance criteria rather than speculative production terms.

## Version and compatibility consequence

These decisions and the subsequent related-work integration define OMARO
ontology/canonical schema `0.1.0` and SQLite `PRAGMA user_version=20200`. The
ontology is unpublished, so identifiers and field names were corrected
directly. No compatibility layer is provided for earlier development snapshots.

## Verification evidence

- `conformance/multiperspectivity-cases.json` publishes expected results.
- `tests/test_conformance.py` evaluates positive endorsement, missing opt-in,
  incomplete review, veto, authority coverage, and SHACL lifecycle behavior.
- `tests/test_model.py` tests context matching and permanent supersession,
  temporary suspension, and explicit reinstatement.
- The canonical snapshot still contains 1,872 source-silent MIMO assignment
  occurrences, no authority assignments, no human/community review decisions,
  and zero direct project-endorsed classifications.
