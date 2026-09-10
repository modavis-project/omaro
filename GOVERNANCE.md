# Governance

## Roles

- **Maintainer:** approves releases, schemas, licensing statements, and project policy.
- **Data curator:** reviews provenance, vocabulary changes, and quality reports.
- **Domain reviewer:** evaluates organological meaning and contested assertions.
- **Language reviewer:** evaluates lexical form, language variety, writing
  system, translation/transliteration status, and usage context within their
  documented competence.
- **Community reviewer or cultural authority:** evaluates community preference,
  protocols, permissions, and culturally sensitive use under authority defined
  by the represented community rather than by the repository.
- **Contributor:** proposes documented code, data, or documentation changes.

Dominik Ukolov is the initial maintainer. MODAVIS Project is the initial data
curation organization. Additional maintainers may be added through a documented
decision by existing maintainers.

## Decisions

Routine code changes require one maintainer review. Data corrections require a
curator review; hierarchy, mapping, deprecated terminology, or culturally
sensitive changes additionally require a domain reviewer. Licensing and breaking
schema changes require explicit maintainer approval and a recorded rationale.

If reviewers disagree, preserve the sourced upstream statement and every
scoped decision. Source-layer predicates are never changed merely to express a
project interpretation. Review decisions are immutable, perspective-bearing
events; they do not collapse into one status on the target assignment. A new
decision may permanently supersede, temporarily suspend, or explicitly
reinstate one earlier event while unrelated scholarly, historical, linguistic,
or community decisions remain active and auditable. Expiry of a superseding
event never resurrects its predecessor.

No contributor may describe a claim as context-independent merely because its
source or scope is silent. `source-silent`, `not-yet-investigated`,
`known-unknown`, `intentionally-unscoped`, `not-applicable`, `specified`, and
`context-independent` are separate governance decisions. Direct project RDF
and the endorsed SQLite view require explicit membership in the
project-endorsed policy, an eligible stance, a context-independent scope, two
independent required acceptances, and no active veto decision. Context-specific
claims remain qualified and must be selected with a matching application
context.

The assertion registries distinguish a source publisher from the software agent
that creates a project projection. A controlled status URI records state but
does not establish review authority: human, linguistic, scholarly, or community
acceptance requires a documented reviewer and evidence under
`REVIEW_PROTOCOL.md`.

Every human/community review requires evidence-bearing authority assignment(s)
whose agent, role, subject matter, validation dimension, scope, and decision
time match. Community representation additionally requires a mandate for every
represented community. Repository staff and domain experts cannot confer
community authority on themselves. A later prospective expiry preserves the
historical validity of a decision; an explicit retroactive revocation does not.
See
`MULTIPERSPECTIVITY.md` for the formal model and examples.

Reviewers must disclose relevant institutional, financial, authorship, or
community-representation conflicts. A contributor must not be the sole
approver of their own culturally or linguistically substantive assertion.
Language and community review should be compensated where project resources
permit; lack of funding must be disclosed rather than replaced with automated
claims of validation.

## Appeals, withdrawal, and community protocols

Any affected person or community may request correction, contextual restriction,
withdrawal from project-facing display/search, or reconsideration of an
assertion. The request must be acknowledged privately when sensitive, assigned
a stable decision record, evaluated by reviewers with relevant authority, and
resolved as accepted, disputed, rejected, or superseded with a rationale.
Preserved source-layer facts remain auditable, but project-facing display and
search policies may suppress harmful or unauthorized material without erasing
the historical record.

Community-controlled identifiers, Traditional Knowledge Labels, Biocultural
Labels, or similar protocols are recorded only when supplied or authorized
through the relevant community's decision-making process. Repository staff do
not assign them unilaterally. Rights, attribution, access conditions, and
withdrawal terms for community-contributed material remain attached to that
material and do not automatically inherit the MIMO-derived layer's CC0 status.

## Releases

Releases follow semantic versioning, immutable version DOIs, the quality gates
in `REVIEW_PROTOCOL.md`, and the operational steps in `RELEASE_CHECKLIST.md`.
No automated process is authorized to publish a DOI release.
