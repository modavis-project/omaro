# Provenance and rights review

## Sources

The dataset is derived from the MIMO Skosmos vocabularies:

- `http://www.mimo-db.eu/HornbostelAndSachs#`
- `http://www.mimo-db.eu/InstrumentsKeywords#`

Canonical records retain original MIMO URIs, SKOS hierarchy, preferred labels,
definitions, and MIMO-published mapping predicates. The canonical metadata
records the precise refresh timestamp and REST endpoints.

MIMO source relations and project-facing classification semantics are separate:

- `source_relations.jsonl` and `dist/rdf/mimo-source-snapshot.ttl` preserve
  MIMO's original `skos:exactMatch` mappings.
- `classification_assertions.jsonl` projects each source mapping to the
  repository property `omaro:classifiedAs`, retains the source predicate and
  source URI, and records the MIMO source perspective, source-asserted stance,
  structured evidence, `source-silent` applicability, source/claims
  projection policies, and `assertion_origin=source-derived`.
- The main RDF graph contains no unqualified `skos:exactMatch`. Every direct
  `omaro:classifiedAs` triple must have a corresponding qualified occurrence,
  `context-independent` scope, eligible stance, explicit endorsed-policy
  membership, two independent required accepting reviews, and no active veto.
  The current graph has no such direct triples because review events are empty.

Source labels and definitions now have a parallel qualified layer:

- `label_assertions.jsonl` assigns a stable assertion URI to every compatibility
  label and records its SKOS predicate, literal, NFC form, language tag, MIMO
  agent, versioned source record, origin, and review status.
- `label_resources.jsonl` identifies each contextual source-label occurrence
  as an assertion-scoped SKOS-XL resource. Identical literals are not merged.
  It contains lexical data only; attribution,
  source, role, projection state, and review remain on assertions.
- `label_profiles.jsonl` decomposes canonical BCP 47 tags and observes Unicode
  character scripts using the checksummed Unicode 17.0.0 registry. It does not
  infer missing varieties, communities, writing systems, transliteration
  systems, or cultural validity.
- `script_registries.jsonl` records the Unicode sources, version, profile,
  artifact path, and checksum behind those observations.
- `note_assertions.jsonl` does the same for every source `skos:definition` and
  permits the other SKOS documentation predicates in the schema.
- `agents.jsonl`, `source_records.jsonl`, and `review_statuses.jsonl` are shared
  registries, so assertions do not encode agents, source snapshots, or status
  meanings as anonymous strings.
- The simple concept definitions and source label records remain lossless.
  Direct project SKOS and SKOS-XL links are validated projections of the
  qualified assertions.
- `quality_findings.jsonl` contains reproducible software-detected review
  signals derived from those assertions. Each has `review_effect=none`.
- `review_events.jsonl` is the separate evidence-bearing human/community layer;
  it remains empty until a reviewer with recorded authority completes a review.
- `concept_schemes.jsonl`, `perspectives.jsonl`,
  `applicability_scopes.jsonl`, `authority_assignments.jsonl`, and
  `projection_policies.jsonl` make the scheme, standpoint, context, authority,
  and graph-selection rules independently auditable.
- `concept_relation_assertions.jsonl` is the qualified layer for new hierarchy
  or cross-scheme mapping claims; mapping rows retain their declared
  operational purposes, while structural rows declare none. It does not
  replace MIMO source relations, and a purpose is not permission.

The initial projection is deliberately `source-asserted` and `source-silent`.
It states that MIMO maps the instrument to the
classification; it does not state that the two SKOS concepts are
interchangeable, universally applicable, culturally valid, or accepted by a
domain or community reviewer.

The `refresh-source` operation updates the known concept inventory represented
by the repository, follows relations returned for those concepts, and replaces
canonical files only after every requested source record succeeds. It does not
independently enumerate the upstream schemes and therefore does not prove that a
newly added upstream concept absent from the known inventory has been discovered.
Normal builds are offline and cannot silently mix source states.

## Transformations

- Null or empty source labels are omitted.
- Language tags are validated before publication.
- MIMO mapping predicates are preserved in a source layer and reversibly
  projected to qualified classification assertions.
- MIMO labels and definitions are preserved unchanged and reversibly projected
  to source-qualified label and note assertions.
- Source-label occurrences receive deterministic SKOS-XL URIs. If a source
  form has conflicting SKOS roles on one concept, the preferred role is
  projected and the lower-priority direct link is suppressed; both source
  assertions remain intact and unreviewed.
- Each SKOS-XL resource receives a deterministic, one-to-one linguistic
  profile. BCP 47 components come from the pinned IANA registry; character
  Script observations come from the separately checksummed Unicode 17.0.0
  Script and ScriptExtensions data. No OntoLex form is inferred because the
  source does not establish lexical entries or grammatical form relations.
- Every source-derived classification envelope receives separate deterministic
  assertion and assignment URIs. Evidence records that the source mapping is
  documented; it does not silently endorse the mapping as context-independent
  organological truth.
- The 26 Hornbostel–Sachs source notations containing `+` are tokenized into
  ordered compound expressions without inferring component targets, roles, or
  suffix scope.
- Script observations exclude `Common` and `Inherited` from
  `observed_script_codes` while recording their presence separately. They do
  not infer language, variety, writing system, transliteration, community, or
  cultural validity.
- Linguistic and documentation heuristics generate warnings without modifying
  source values or assertion review status.
- Language tags are validated offline against the checksummed IANA Language
  Subtag Registry dated 2026-06-14. Submitted forms remain recorded separately;
  MIMO's legacy `dk` is transparently normalized to registered `da`.
  Existing Danish submitted-tag values are reconstructed from the repository's
  documented pre-1.4 normalization rule because the earlier canonical snapshot
  did not retain the raw tag separately; future refreshes capture it directly.
- Inverse `skos:narrower` triples are derived from `skos:broader`.
- Unresolved mapped target URIs are retained as unlabeled instrument stubs.
- CSV, JSONL, RDF, SQLite, OKF Markdown, self-contained RAG JSONL, and legacy
  JSON are generated from one canonical model.
- `dist/metadata/dqv.ttl` is generated from the same validated model and build
  report. Each DQV measurement names its metric, quality dimension, value type,
  computation target, generating software agent, and generation time; rate
  measurements also retain their denominator. These measurements describe
  dataset fitness and validation state only. They are not organological
  observations, review decisions, community validation, or cultural authority.
- The release archive contains a deterministic RO-Crate 1.3 descriptor that
  identifies the versioned dataset and selected local documentation,
  examples, generated directories, and manifests. It is a package-discovery
  layer, not a replacement for canonical registries, file-level manifests,
  provenance, resource-specific rights, or use decisions.
- Archive size and digest cannot be asserted inside the archive without a
  circular dependency. Packaging therefore writes a separate DCAT 3 metadata
  sidecar after the ZIP exists. The sidecar relates the stable dataset to the
  immutable version, describes the ZIP distribution, and records its byte size
  and SHA-256 checksum. `SHA256SUMS` then covers both files.
- OKF narrower links and RAG ancestor paths are convenience views derived from
  authoritative `skos:broader` assertions; they add no new source claims.
- OKF v0.2 `generated` and `sources` fields describe the Markdown projection.
  Its `verified` event records deterministic projection and format checks only;
  it is machine confirmation, not human domain review, cultural authorization,
  or acceptance of a classification assertion.

## Rights gate

The repository declares CC0 1.0 Universal. The official 2025 MIMO Data Provider
Agreement states in Article 5 that MIMO data is made available as Linked Open
Data without restrictions on third-party reuse and that MIMO applies CC0 1.0 to
data made available on its website:

`https://mimo-international.com/media/website_docs/MIMO%20data_provider_agreement_2025_v2.pdf`

This is strong documentary support for the proposed license. The review performed
on 2026-07-19 additionally confirmed that Article 2 defines the MIMO website as
including its data and machine interfaces and defines “MIMO Data” as the merged
and semantically enriched data accessible through that website, excluding
previews. This release uses only vocabulary data from those machine interfaces;
it contains no preview images, audio, video, or collection object content.

Reviewed document SHA-256:
`8b2ba6531e673dc6d4e6d242862bad6f878432cabed16759b126dd95efd047b0`.
The same official document and checksum were reverified on 2026-07-29 during
final release preparation.

Evidence-review conclusion: **accepted for the declared CC0-1.0 dataset scope**.
This records a provenance and documentary rights assessment, not legal advice or
a warranty beyond the source agreement. Accountable publication authorization
remains with the maintainer.
