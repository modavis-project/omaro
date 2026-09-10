# Dataset quality report

Dataset version: `0.1.0`
Source retrieved: `2026-07-19T15:10:55Z`

| Metric | Value |
|---|---:|
| Classifications | 643 |
| Resolved instruments | 2724 |
| Unresolved instrument stubs | 5 |
| Preferred labels | 35794 |
| Alternative labels | 6868 |
| Assertion-scoped SKOS-XL label resources | 42662 |
| Conservative linguistic label profiles | 42662 |
| Unicode Script registry snapshots | 1 |
| Profiles with explicit BCP 47 script | 0 |
| Profiles with recorded language variety | 0 |
| Profiles with recorded transliteration system | 0 |
| Profiles with reviewed term roles | 0 |
| Qualified label assertions | 42662 |
| Unreviewed label assertions | 42662 |
| Qualified note assertions | 643 |
| Unreviewed note assertions | 643 |
| Registered agents | 2 |
| Versioned source records | 2 |
| Review statuses | 5 |
| Automated quality findings | 9445 |
| Human/community review events | 0 |
| Registered perspectives | 1 |
| Registered applicability scopes | 1 |
| Registered authority assignments | 0 |
| Projection policies | 3 |
| IANA language-registry snapshots | 1 |
| MIMO source relations | 5228 |
| Source-derived classification assertions | 1872 |
| Source-asserted classification assignments | 1872 |
| Qualified concept-relation assertions | 0 |
| Instrument hierarchy source relations | 2718 |
| Concepts with source creation date | 2724 |
| Classifications without classified instruments | 314 |
| Resolved instruments without classifications | 971 |
| Resolved instruments with multiple classifications | 90 |
| Maximum classifications on one resolved instrument | 9 |
| Duplicate English label occurrences | 56 |
| Source lexical forms asserted as both preferred and non-preferred | 89 |

Both migration baselines match: **True**.

MIMO's `skos:exactMatch` mappings are preserved only in the explicit source
layer. The project-facing classification assignments use `omaro:classifiedAs`,
retain their source predicate, source perspective, evidence, and an explicit
`source-silent` applicability scope. Source silence is not context-independent
validity. These source claims remain qualified occurrences and do not become
direct project assertions without explicit policy membership, an eligible
stance, a context-independent scope, independent authorized referential and
scholarly acceptances, and the absence of an active veto.

Every compatibility label and source definition now has a stable qualified
assertion linked to an agent, a versioned source record, and a review-status
resource. These records preserve source evidence; `unreviewed` does not imply
linguistic, community, or scholarly acceptance.

Every label resource also has a conservative linguistic profile. Declared BCP
47 components are kept distinct from Unicode Script observations made against
the pinned Unicode `17.0.0` data.
Missing variety, writing-system, transliteration, community, place, period,
usage-domain, pronunciation, audio, and term-role evidence remains explicitly
empty; the pipeline does not infer it.

## Automated linguistic and documentation audit

| Rule | Open findings |
|---|---:|
| `definition-repeats-notation` | 13 |
| `registry-invalid-language-tag` | 3679 |
| `skos-label-role-conflict` | 89 |
| `undetermined-language` | 1445 |
| `zh-alternative-latin-script` | 2387 |
| `zh-preferred-identical-to-en` | 1779 |
| `zh-preferred-placeholder-or-uncertain` | 53 |

All findings are deterministic review signals with `review_effect: none`.
They do not establish that a label is wrong and do not change assertion review
status. Script mismatch may indicate a valid transliteration, loanword, exonym,
or translingual form. Human or community review must record evidence,
perspective, authority, and contextual applicability in a review event.

The language-tag gate uses the vendored IANA registry dated
`2026-06-14`. Submitted tags are retained
separately from canonical tags. The legacy MIMO `dk` value is explicitly
recorded as invalid source metadata normalized by the project to registered
language tag `da`; this technical normalization does not validate the label.

Cross-type lexical collisions are retained because they are present in MIMO's
native RDF. They are reported for review rather than silently discarded.

## Preferred-label coverage for resolved instruments

| Language | Present | Missing |
|---|---:|---:|
| `ca` | 2714 | 10 |
| `da` | 2477 | 247 |
| `de` | 2724 | 0 |
| `en` | 2724 | 0 |
| `es` | 2720 | 4 |
| `eu` | 2724 | 0 |
| `fr` | 2724 | 0 |
| `it` | 2724 | 0 |
| `ko` | 2724 | 0 |
| `nl` | 2724 | 0 |
| `pl` | 2724 | 0 |
| `sv` | 2724 | 0 |
| `zh` | 2724 | 0 |

## Unresolved source targets

- `http://www.mimo-db.eu/InstrumentsKeywords/2412`
- `http://www.mimo-db.eu/InstrumentsKeywords/3135`
- `http://www.mimo-db.eu/InstrumentsKeywords/3405`
- `http://www.mimo-db.eu/InstrumentsKeywords/5990`
- `http://www.mimo-db.eu/InstrumentsKeywords/6059`
