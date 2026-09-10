# Domain and release review protocol

## Domain sample

Before v0.1.0 publication, an independent reviewer should inspect at least:

- ten concepts from each top-level Hornbostel–Sachs class;
- all top-level concepts and boundary cases containing suffix notation;
- twenty multilingual instrument records, including non-Latin scripts;
- twenty qualified label assertions and ten qualified note assertions,
  including `und`, non-Latin scripts, transliterated forms, and definitions
  containing historical place terminology;
- twenty linguistic label profiles, comparing the BCP 47 decomposition,
  declared/default scripts, observed character scripts, qualification fields,
  display/search policy, provenance, and review state with their source
  assertions;
- all 89 label assertions whose direct SKOS/SKOS-XL projection is suppressed
  because the same form is also preferred for the same concept and language;
- twenty preserved MIMO mappings and their source-derived classification
  assertion/assignment envelopes, checking distinct entity/activity identity,
  scheme, source perspective, `source-silent` scope, directional evidence,
  stance, and projection policies, including generic and culturally specific
  instrument concepts;
- all 26 tokenized compound expressions, checking exact round trip, member
  order, and the absence of invented component roles or suffix scope;
- every contributed target, observation, criterion, protocol application, and
  use decision; zero current records must not be reported as completed review;
- every proposed non-source perspective, authority assignment,
  `context-independent` scope, and claim eligible for the project-endorsed
  policy;
- every unresolved source target and every newly normalized language tag;
- examples with duplicate English labels and multiple classifications.

For each sampled assertion, record assertion URI, subject, predicate, object or
literal, language tag where applicable, verdict (`accepted`, `correction`,
`disputed`, `rejected`, `unverifiable`, or `withdrawn`), evidence, reviewer,
authority mandate where applicable, perspective, complete applicability scope,
represented communities, projection policies, rationale, lifecycle, and date
in a review event attached to the release review. A review does not mutate a
classification assignment or rewrite a preserved MIMO predicate or literal.
Multiple scoped decisions may coexist. A later decision may supersede, suspend,
or reinstate only the older same-target decision it explicitly names. Supersession
is permanent; successor expiry does not restore the predecessor. Working
review records may contain operational or reviewer information and remain
private unless publication is necessary and explicitly approved. Corrections
follow `CORRECTIONS.md`.

For a label-profile review, additionally record the profile and label-resource
URIs, validation dimension, reviewer competence or community authority,
translation status, term role, relevant variety/writing-system identifiers,
applicable community/place/period/domain, and display/search decision. Observed
Unicode Script is evidence about characters only and cannot establish any of
those reviewed claims.

## Automated gates

- JSON Schema, SHACL, relational integrity, and cross-format equivalence pass.
- Stable SKOS-XL label-resource, assertion, agent, source-record, and
  review-status identifiers resolve
  consistently across canonical JSONL, CSV, RDF, SQLite, OKF, and RAG exports.
- Every classification and concept-relation occurrence resolves its scheme,
  perspective, scopes, agents, authority, source, and projection policies.
  Source-derived MIMO assignments exactly reproduce the source mappings, while
  independently identified occurrences for other perspectives may coexist.
- Every classification envelope has distinct assertion and assignment URIs;
  every review envelope has distinct event and decision URIs. RDF and SQLite
  preserve those identity boundaries and their PROV generation links.
- Every evidence item records a directional role. A source can document that a
  claim occurred without supporting its truth.
- The seven scope states validate, `source-silent` and the other unresolved
  states never become `context-independent`, and specified scopes contain at
  least one boundary. The endorsed static view admits only claims that opt into
  the policy, are eligible and context-independent, satisfy authorized
  referential and scholarly acceptances by two distinct agents, and have no
  active veto. A `correction` does not endorse the original target; the
  corrected assertion is a separately identified occurrence.
- Review support and veto have different scope obligations. Acceptances must
  positively match the requested context, or be context-independent for a
  direct projection. A narrower or unresolved authorized veto still blocks a
  static direct claim. A contextual query ignores a veto only when supplied
  values prove its scope disjoint; omitted dimensions cannot establish that.
  `Dataset.explain_endorsement` exposes the applicable requirements and veto
  decision URIs; see [INFERENCE_AND_VALIDATION.md](INFERENCE_AND_VALIDATION.md).
- Every review resolves to one or more mandates matching reviewer, reviewer
  role, exact subject matter, validation dimension, scope, and decision time.
  Community review covers every represented community. Technical, linguistic,
  or scholarly expertise is not a substitute for community authority.
- Review decisions remain non-collapsing: supersession, suspension, and
  reinstatement are explicit; withdrawn decisions cannot endorse a claim;
  disagreement across perspectives remains queryable; and an expired successor
  never resurrects a superseded decision.
- Golden conformance cases produce identical direct-endorsement results in the
  Python evaluator, RDF graph, and materialized SQLite endorsed set. They cover
  missing policy opt-in, missing required dimensions, active veto, independent
  reviewers, authority coverage, and reversed lifecycle dates.
- Every label resource has exactly one linguistic profile. Observed Unicode
  Script must not be treated as proof of language, dialect, transliteration,
  community preference, or cultural validity; those claims require evidence
  and recorded review authority.
- Every profile links to exactly one source label assertion and projects to one
  RDF `omaro:LabelProfile`; each SKOS-XL resource has exactly one
  language-tagged `skosxl:literalForm`. No OntoLex form is emitted without a
  genuine lexical-entry model.
- Deterministic audit totals reproduce, every automated finding retains
  `review_effect: none`, and automated output cannot populate the
  human/community review-event table.
- The vendored IANA registry date and checksum match its registry record; every
  compatibility tag is registered and canonical, while submitted source tags
  and normalization status remain independently auditable.
- The vendored Unicode Script sources, Unicode version, normalized artifact,
  and checksum match the script-registry record.
- Every SKOS-XL resource has exactly one literal form; every projected direct XL
  link corresponds to the retained simple SKOS literal, and conflicting source
  roles remain accessible through qualified assertions and the raw source graph.
- OKF v0.2 YAML, reserved-file structure, source identifiers, lifecycle fields,
  actor identifiers, timestamps, footnote attribution, and generated internal
  links pass validation.
- Canonical and release checksums match.
- Publication preflight runs before any output is written and fails closed for
  community-governed resources lacking an active, scope-matched positive use
  decision. Refused, withheld, withdrawn, expired, or ambiguous decisions
  cannot be overridden by an epistemic projection or open licence.
- Full build is deterministic in the pinned Linux environment.
- Baseline changes and missing-language coverage are explained.
- Citation, DataCite, DCAT/VoID, CFF, and Zenodo metadata agree on DOI and version.
- OMARO ontology and canonical schema `0.1.0`, SQLite
  `PRAGMA user_version=20200`, dataset/tooling `0.1.0`, and OKF profile
  `0.2` remain mutually consistent across documentation and generated metadata.

## Sign-off

Release requires maintainer, data-curator, rights/provenance, and domain-review
sign-off. The public quality report records the resulting dataset findings
without publishing private reviewer notes or internal operational records.
An independent human organology review remains recommended because automated
source fidelity cannot adjudicate scholarly disagreements in MIMO.
An OKF `verified` event emitted by the build must therefore never be treated as
domain-review sign-off; assertion review is recorded separately under the
domain sample procedure above.
Release documentation must state the number of completed human/community review
events. A zero count is permissible for a clearly labeled source snapshot, but
the release must not claim linguistic, community, scholarly, or cultural
validation that has not occurred.
