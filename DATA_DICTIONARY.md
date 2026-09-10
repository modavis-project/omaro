# Data dictionary

## Canonical tables

### Concepts

| Field | Meaning |
|---|---|
| `uri` | Stable concept URI and primary key. |
| `scheme_uri` | Foreign key to the concept-scheme registry. |
| `kind` | `classification`, `instrument`, `facet`, or `community-category`. |
| `local_id` | Required identifier unique within the concept scheme. |
| `mimo_id` | Optional MIMO numeric identifier; null for concepts from other schemes. |
| `notation` | Hornbostel–Sachs notation; classifications only. |
| `definition` | English SKOS definition when supplied; classifications only. |
| `created` | Source-provided concept creation date when available. |
| `resolution_status` | `resolved` or `unresolved`; unresolved records are auditable target stubs. |

Concept identity is scheme-specific. Similar labels or meanings in two schemes
do not merge the concepts; use a qualified concept-relation assertion to state
the proposed mapping.

### Compatibility labels

| Field | Meaning |
|---|---|
| `concept_uri` | Foreign key to a concept. |
| `language` | BCP 47 language tag. |
| `submitted_language` | Source tag before registry-backed normalization. |
| `label_type` | `preferred`, `alternative`, or `hidden`. |
| `label` | Non-empty Unicode label. |

At most one preferred label is permitted per concept and language. A missing
row means that no label of that type was supplied; missing values are never
encoded as a language named `null`.

`labels.jsonl` is a lossless compatibility projection. Qualified consumers
should join through `label_assertions.jsonl`.

### SKOS-XL label resources

`label_resources.jsonl` contains one lexical resource for every contextual
source-label occurrence. The URI is content-addressed from concept, language,
role, literal, versioned source record, asserting agent, and source URI.
Each record has exactly one `literal_form`, its NFC `normalized_form`, a
registry-canonical `language_tag`, and `language_registry_uri`. Agent, source,
role, cultural context, and review state deliberately remain on label
assertions. Identical language-tagged spellings remain distinct resources, so
homographs and culturally distinct uses are never merged merely by string equality.

### Linguistic label profiles

`label_profiles.jsonl` contains one project-derived profile for every
assertion-scoped label resource. It records canonical BCP 47 components,
Unicode Script observations, display/search policy, provenance, and review
state. Declared script subtags and observed character scripts are separate
fields. The latter are computed from pinned Unicode 17.0.0 data and are not
language, dialect, transliteration, or cultural-identity inferences.

Fields for language variety, writing system, transliteration/transcription,
pronunciation, audio, term roles, community, place, period, and usage domain
remain null or empty until evidence and review authority are recorded.
`translation_status` is therefore `unverified` in the current source-derived
profiles.

| Field | Meaning |
|---|---|
| `uri` | Stable content-addressed project URI for the profile. |
| `label_resource_uri` | One-to-one foreign key to the SKOS-XL label resource. |
| `source_label_assertion_uri` | One-to-one foreign key to the source label assertion. |
| `language_tag` | Registry-canonical BCP 47 tag copied from the label resource. |
| `primary_language_subtag` | Primary registered language subtag. |
| `explicit_script_subtag` | Script explicitly declared in the BCP 47 tag, or null. |
| `default_script_subtag` | IANA `Suppress-Script` value where one is registered, or null; this is not an observed-script claim. |
| `region_subtag` | Region declared in the BCP 47 tag, or null. |
| `variant_subtags`, `extension_subtags`, `private_use_subtags` | Ordered BCP 47 components; empty when absent. |
| `language_variety_uri` | Evidence-backed language-variety identifier, or null. |
| `writing_system_uri` | Evidence-backed writing-system identifier, or null. |
| `observed_script_codes` | Sorted ISO 15924-style Script codes observed in non-Common, non-Inherited Unicode characters. |
| `has_common_or_inherited_characters` | Whether the literal also contains characters with Unicode Script `Common` or `Inherited`. |
| `script_observation_method` | Fixed method identifier `unicode-script-property-17.0.0`. |
| `script_registry_uri` | Foreign key to the checksummed Unicode Script registry record. |
| `transliteration_system_uri`, `transcription_system_uri` | Evidence-backed method identifiers, or null. |
| `pronunciations` | Reviewed pronunciation strings; currently empty. |
| `audio_uris` | Reviewed, rights-qualified pronunciation-audio URIs; currently empty. |
| `term_roles` | Zero or more reviewed roles: `endonym`, `exonym`, `loanword`, `translation`, `transliteration`, `historical-name`, `collector-term`, `trade-name`, `scholarly-name`, `misspelling`, `contested`, or `harmful-legacy-term`. |
| `translation_status` | `unverified`, `borrowed-translingual`, `machine-translated`, `human-translated`, `native-speaker-reviewed`, `community-reviewed`, `contested`, or `not-applicable`. |
| `applies_to` | URI arrays for communities, places, periods, and usage domains. |
| `display_policy` | `source-fallback`, `preferred-when-context-matches`, `suppress`, or `warning-only`. |
| `search_policy` | `include`, `include-with-warning`, or `exclude`. |
| `asserted_by_uri`, `source_record_uri` | Profile-generating software agent and versioned source record. |
| `assertion_origin` | `source-derived`; the profile is a conservative projection, not a source claim. |
| `review_status`, `review_status_uri` | Controlled workflow state and its registry URI. |

### Label assertions

Every compatibility label has exactly one qualified assertion. Validation fails
if either layer has a missing or additional row.

| Field | Meaning |
|---|---|
| `uri` | Stable content-addressed project URI for the label assertion. |
| `concept_uri` | Concept to which the label is applied. |
| `predicate_uri` | `skos:prefLabel`, `skos:altLabel`, or `skos:hiddenLabel`. |
| `literal_form` | Source lexical form, unchanged. |
| `normalized_form` | NFC-normalized technical comparison form; not a correction. |
| `language_tag` | Source or normalized language tag. |
| `submitted_language_tag` | Tag supplied by the source before technical normalization. |
| `language_tag_status` | Registry result: `valid`, `noncanonical`, `deprecated`, or `invalid-source-normalized`. |
| `language_registry_uri` | Foreign key to the dated IANA registry snapshot. |
| `label_resource_uri` | Foreign key to the assertion-scoped SKOS-XL lexical resource. |
| `label_role` | Compatibility role: `preferred`, `alternative`, or `hidden`. |
| `skos_projection_status` | `projected` or `suppressed-role-conflict`. |
| `asserted_by_uri` | Agent registry foreign key; initially MIMO. |
| `source_record_uri` | Versioned source-record foreign key. |
| `source_uri` | MIMO concept from which the label was retrieved. |
| `assertion_origin` | `source-asserted`. |
| `review_status` | Controlled status code. |
| `review_status_uri` | Stable review-status registry foreign key. |

The current `unreviewed` state records absence of project review. It is not a
claim that a label is linguistically, culturally, or ethically valid.
When the same literal is both preferred and non-preferred for one concept and
language, all source assertions remain intact. The project graph projects only
the highest-priority role (`preferred`, then `alternative`, then `hidden`) to
direct SKOS/SKOS-XL properties and emits a warning for each suppressed link.

### Note assertions

`note_assertions.jsonl` qualifies each source definition using the same agent,
source, origin, and review fields as label assertions. Its `predicate_uri`
currently contains `skos:definition`; the schema also permits `scopeNote`,
`historyNote`, `editorialNote`, `changeNote`, and `example`. `literal_form`,
`normalized_form`, and `language_tag` preserve and describe the note text.
Concept-level `definition` remains a compatibility projection.

### Scheme, perspective, scope, authority, and policy registries

`concept_schemes.jsonl` defines each independent terminology or classification
scheme. Besides `uri` and `label`, it records scheme type, version and version
URI, publisher, perspective, source record, governance URI, rights, lifecycle
status, and a scope note. Concepts join to this registry through `scheme_uri`.

`perspectives.jsonl` defines named epistemic, institutional, scholarly,
community, curatorial, historical, or technical standpoints. A record contains
its holder, communities it claims to represent, description, lifecycle, and
authority-assignment links. A perspective alone is attribution and does not
prove cultural authority.

`applicability_scopes.jsonl` defines the contextual boundary of a claim:

| Field | Meaning |
|---|---|
| `scope_mode` | `source-silent`, `not-yet-investigated`, `known-unknown`, `intentionally-unscoped`, `not-applicable`, `specified`, or `context-independent`. The first four yield an unknown match; none means universal truth. |
| `community_uris`, `place_uris`, `period_uris` | Community, geographic, and historical boundaries. |
| `usage_domain_uris` | Ceremonial, pedagogical, museum, performance, or other controlled usage domains. |
| `playing_technique_uris` | Techniques for which the scoped claim applies. |
| `instrument_configuration_uris` | Configurations or adaptations for which it applies. |
| `language_variety_uris` | Language-variety boundaries. |
| `temporal_start`, `temporal_end` | Exact interval boundaries where needed. |
| `asserted_by_uri`, `perspective_uri`, `source_record_uri` | Scope provenance. |

Dimensions populated within one scope are combined with AND; values in one
dimension are combined with OR. Multiple scope URIs on one assignment are
alternative complete scopes. A `specified` scope must have a boundary. All
other modes contain none. `context-independent` means independent of these
registered dimensions for the named target, method, scheme version, and
purpose; it is not a metaphysical universality claim. A scope is immutable
provenance: changing its meaning requires a new URI and new/superseding uses.

`authority_assignments.jsonl` documents a time-bounded mandate. It records the
authorized agent, optional represented community, role and basis, conferring
agent, subject matter, covered validation dimensions, `covered_action_uris`,
scopes, validity interval, delegation, status, prospective or retroactive
revocation, rights, and evidence. The current registry is intentionally empty.
Every human or community review requires at least one matching mandate.
Community review must cover every represented community, and community-origin
assignments must be covered through their community perspective. A mandate
used for a `UseDecision` must also name the exact requested action URI in
`covered_action_uris`; a general rights role, subject-matter match, or mandate
for a different action is insufficient. The array may be empty for a mandate
that does not empower its holder to make publication or reuse decisions.

| Field | Meaning |
|---|---|
| `uri` | Stable mandate URI. |
| `agent_uri`, `represented_community_uri` | Authorized agent and optional community represented by that mandate. |
| `authority_role`, `authority_basis_uri`, `conferred_by_agent_uri` | Controlled role, evidence-bearing basis resource, and conferring agent. |
| `subject_matter_uris` | One or more exact resources within the mandate's subject matter. |
| `covered_validation_dimensions` | One or more review dimensions for which the agent is authorized. |
| `covered_action_uris` | Exact publication or reuse actions the agent may decide; empty means no such action authority. |
| `applicability_scope_uris` | One or more complete scopes covered by the mandate. |
| `valid_from`, `valid_until`, `status` | Time interval and active, expired, revoked, or withdrawn lifecycle state. |
| `delegation_permitted` | Whether further delegation is authorized. It does not create a delegated mandate by itself. |
| `revocation_event_uri`, `revocation_effect` | Evidence of revocation and its prospective or retroactive effect, or null. |
| `rights_uri`, `evidence` | Rights governing the mandate record and one or more directional evidence entries. |

`projection_policies.jsonl` controls the interpretation of generated graph
views. Policies define graph role, direct-triple behavior, eligible stances,
declarative review requirements, minimum distinct reviewers, veto rules,
whether query context must match, treatment of unresolved scope, inclusion of
the source layer, and policy version. The required policies are
source-faithful, research-claims, and project-endorsed. See
`MULTIPERSPECTIVITY.md` for their decision rules and examples.

### Agent, source, and review-status registries

`agents.jsonl` records stable agents with `uri`, `agent_type`, `name`, and
`resource_uri`. The initial registry distinguishes MIMO as the source
organization from the project build pipeline as a software agent.

`source_records.jsonl` identifies the two MIMO API snapshots at the precise
retrieval time. Records include resource, title, type, scheme, publisher agent,
logical layer, rights URI, and retrieval timestamp. Their URIs contain the
snapshot timestamp so later refreshes remain distinguishable.

`review_statuses.jsonl` defines the stable URI, code, label, and meaning of
`unreviewed`, `accepted`, `disputed`, `rejected`, and `superseded`. Status
resources express workflow state; they do not substitute for review evidence or
authority.

`language_registries.jsonl` records the official IANA source, registry file
date, RFC 5646 profile, artifact checksum, and the documented legacy `dk → da`
normalization. The complete compact registry snapshot is distributed under
`metadata/iana-language-subtag-registry.json`. Registry validation replaces the
former regular-expression gate.

`script_registries.jsonl` records the Unicode version, Script and
ScriptExtensions source files, Unicode property profile, compact artifact path,
and SHA-256 checksum used for character-script observations. The complete
normalized snapshot is distributed under
`metadata/unicode-script-registry.json`. A script observation describes
characters in a literal, not the language, variety, community, or cultural
validity of that literal.

Because the pre-1.4 canonical snapshot did not retain the raw tag separately,
`submitted_language_tag=dk` on existing Danish records is a transparent
reconstruction of the repository's documented legacy normalization rule.
Future source refreshes capture the submitted RDF language tag directly.

### Quality rules, findings, and review events

`quality_rules.jsonl` defines eight deterministic warning rules.
`quality_findings.jsonl` links each signal to its target assertion, concept,
detector, time, validation dimension, contextual applicability, and observed
evidence. Every automated finding has `assessment_method:
automated-heuristic`, `human_review_required: true`, and `review_effect: none`.
It is neither a correction nor evidence that a form is culturally invalid.

`review_events.jsonl` is currently empty because no qualifying human or
community reviews have been completed. Each compact row represents two distinct
resources: the `ReviewEvent` activity and the `ReviewDecision` entity it
generated. Neither is a status column on a classification assertion or
assignment. Automated assessments are prohibited from this table.

| Field | Meaning |
|---|---|
| `uri` | Stable review-event URI. |
| `decision_uri` | Stable URI of the decision entity generated by the event. It must differ from `uri`. |
| `target_assertion_uri` | Assertion or profile being reviewed. |
| `reviewer_agent_uri` | Foreign key to the accountable reviewer or community agent. |
| `reviewer_authority` | `community`, `language`, `organology`, `history`, `rights`, `technical`, or `ethical`. |
| `authority_assignment_uris` | One or more matching authority mandates. Agent, role, exact subject matter, validation dimension, scope, and decision time must all be covered. |
| `review_method` | `human` or `community`; software assessment is not permitted. |
| `validation_dimension` | `referential`, `linguistic`, `community`, `historical`, `scholarly`, `ethical`, or `rights`. |
| `outcome` | `accepted`, `correction`, `disputed`, `rejected`, `unverifiable`, or `withdrawn`. |
| `reviewed_at` | Date-time of the review decision. |
| `valid_until` | Optional end of the decision's validity. |
| `perspective_uri` | Registered standpoint under which the review applies. |
| `represented_community_uris` | Communities the reviewer is explicitly acting for; empty for non-community review. |
| `applicability_scope_uris` | One or more registered contextual scopes. |
| `evidence` | One or more typed citations, each stating whether it supports, opposes, qualifies, or documents the decision. |
| `rationale` | Human-readable reason for the decision. |
| `rights_uri` | Rights or protocol URI governing the review contribution. |
| `supersedes_decision_uri` | Earlier decision permanently replaced by this decision, or null. Its expiry does not reactivate the predecessor. |
| `suspends_decision_uri` | Earlier decision temporarily suspended while this decision is active, or null. |
| `reinstates_decision_uri` | Earlier suspended decision explicitly restored by this decision, or null. |
| `decision_status` | `active`, `withdrawn`, or `superseded`. |
| `projection_policy_uris` | Policies under which the decision may affect a view. |

Active decisions are selected without collapsing perspectives. One decision may
perform at most one lifecycle action, it must reference an older decision on
the same target, and a superseding event permanently removes only its named
predecessor. Suspension and reinstatement make temporary intent explicit.

### MIMO source relations

`source_relations.jsonl` preserves the relations published by MIMO.

| Field | Meaning |
|---|---|
| `subject_uri` | Source concept URI. |
| `predicate_uri` | MIMO-published `skos:broader` or `skos:exactMatch`. |
| `object_uri` | Target concept URI. |
| `source_uri` | MIMO concept from which the relation was retrieved. |

This is an explicit source layer, not a declaration that every source predicate
is also the repository's preferred interpretation. `skos:narrower` is generated
as the inverse of `skos:broader` in RDF.

### Classification assertions

`classification_assertions.jsonl` provides a reversible semantic projection of
each MIMO class-to-target mapping and is also the canonical layer for future
scholarly, institutional, or community classification. Each compact row is an
envelope for two distinct resources: a proposition-bearing
`ClassificationAssertion` entity and the `ClassificationAssignment` activity
that generated it. It is not a universal truth claim or SKOS concept identity.

| Field | Meaning |
|---|---|
| `uri` | Stable URI of the classification assertion entity. |
| `assignment_uri` | Stable URI of the distinct generating assignment activity. |
| `target_uri` | Classified target URI. |
| `target_type` | `instrument-concept`, `physical-object`, `instrument-component`, `functional-module`, `instrument-aggregate`, `instrument-configuration`, `condition-state`, `sounding-realization`, `performance-event`, or `ensemble-medium`. |
| `predicate_uri` | Project property `omaro:classifiedAs`. |
| `classification_uri`, `classification_scheme_uri` | Assigned concept and its registered scheme. |
| `scheme_version_uri` | Versioned scheme or source-record URI, or null. |
| `assigned_by_uri`, `generated_by_uri` | Agent responsible for the assignment and optional software generator; these activity roles are distinct. |
| `perspective_uri` | Named standpoint under which the assignment was made. |
| `classification_method_uri`, `criteria_uris` | Absolute method URI and any governed classification criteria used by the assignment. |
| `assessment_uris`, `inference_logic_uri` | Observation-assessment premises and optional documented inference logic; empty or null for source transcription without such evidence. In RDF every listed premise uses `omaro:usedAssessment`, while only actual attempts also use `omaro:usedObservation`. |
| `classification_expression_uri` | Optional ordered compound expression represented by the assertion. |
| `stance` | `source-asserted`, `asserted`, `proposed`, `endorsed`, `disputed`, `rejected`, or `superseded`. |
| `applicability_scope_uris` | One or more complete alternative scopes. |
| `evidence` | Typed citations with explicit `supports`, `opposes`, `qualifies`, or `documents` relation. |
| `authority_assignment_uris` | Documented authority mandates; empty only when no authority claim is being made. |
| `valid_from`, `valid_until` | Optional temporal validity of the assignment occurrence. |
| `projection_policy_uris` | Named policies under which this occurrence is exposed. |
| `source_predicate_uri` | Original source predicate when derived; MIMO uses `skos:exactMatch`. |
| `source_uri`, `source_record_uri` | Source resource and versioned source record. |
| `assertion_origin` | `source-derived`, `project-asserted`, `scholarly-asserted`, or `community-asserted`. |

Validation requires an exact correspondence between MIMO source exact-match
mappings and the subset of `source-derived` assertion/assignment envelopes.
Additional perspectives may add assertions and assignments for the same pair
without replacing that subset. Assertion and assignment URI uniqueness—not pair
uniqueness—is required.

### Organological targets, observation assessments, and criteria

`organological_targets.jsonl` identifies what is being inspected or classified
without assuming that every target is intrinsically an instrument. Target kinds
cover instrument concepts, physical objects, components, functional modules,
aggregates, configurations, condition states, sounding realizations,
performance events, and ensemble media. Component, configuration, condition,
realization, performance, technique, validity, perspective, scope, rights, and
protocol links remain explicit. A physical object's identity is not replaced by
one state or use.

The structural fields are constrained, not merely descriptive:

| Field | Meaning and validation rule |
|---|---|
| `realizes_instrument_concept_uris` | Instrument-concept records realized by this target; every referenced canonical concept must have kind `instrument`. |
| `configuration_of_uri` | Parent target for an `instrument-configuration` or `sounding-realization`; no other target kind may use it. |
| `component_of_uri`, `component_role_uri` | Parent and evidenced role for an `instrument-component`, `functional-module`, or `instrument-aggregate`; either both are present or both are null. |
| `has_component_uris` | Immediate component targets. Each child's `component_of_uri` must point back to this target. |
| `has_functional_module_uris` | Functional-module targets that must also occur in `has_component_uris` and have kind `functional-module`. |
| `condition_state_of_uri` | Parent target of a `condition-state`; no other target kind may use it. |
| `performance_event_uri` | Performance-event target linked from a `sounding-realization`; the referenced target must have kind `performance-event`. |
| `actual_playing_technique_uris` | Techniques evidenced for a sounding realization or performance event. Actual techniques cannot be attached to a timeless object or concept. |
| `intended_playing_technique_uris` | Intended or designed techniques, kept distinct from techniques actually observed in an occurrence. |
| `valid_from`, `valid_until` | Optional target-state interval. It is independent of observation time and assertion or authorization lifecycle. |

All structural targets must resolve, no target may point to itself, and
`configuration_of_uri`, `component_of_uri`, and `condition_state_of_uri`
chains must be acyclic. These checks prevent part/whole, state/identity, and
occurrence/type conflation before classification logic is evaluated.

Every row in `observation_assessments.jsonl` is an
`omaro:ObservationAssessment`. It records a feature of interest, optional
assessed part, assessed property, procedure, responsible assessment agent,
optional sensor, phenomenon interval, assessment time, perspective, scope,
evidence, rights, protocols, and review state. `assessment_status`
distinguishes `detected`, `not-detected`, `indeterminate`, `not-observed`, and
`not-applicable`.

Only the first three statuses assert that an observation attempt occurred.
Those rows are additionally typed `omaro:OrganologicalObservation`,
`sosa:Observation`, and CRMsci `S27 Observation`, and receive the corresponding
SOSA projection. A `not-observed` or `not-applicable` row remains solely an
OMARO assessment and uses OMARO assessment properties; it must not be queried
as an observation activity. In particular, `not-observed` is not evidence for
`not-detected`.

Classification records reference these rows through `assessment_uris`, but the
RDF distinction is exact: every referenced row is
linked with `omaro:usedAssessment`; `omaro:usedObservation` is added only for
the three actual-attempt statuses. Consumers must not treat the JSON field name
as an RDF type assertion.

| Field | Meaning and validation rule |
|---|---|
| `feature_of_interest_uri` | Target or concept whose property was assessed. |
| `assessed_part_uri` | Optional registered target that narrows the assessed part. |
| `assessed_property_uri`, `assessment_procedure_uri` | Property considered and procedure applied, planned, or assessed for applicability. |
| `assessment_agent_uri`, `assessment_sensor_uri` | Agent responsible for the assessment and optional sensor used for an actual attempt. |
| `assessment_status` | Whether a result was detected, not detected, indeterminate, not observed, or not applicable. |
| `result` | Resource, literal, quantity, range, or null. `detected` and `not-detected` require a result; `not-observed` and `not-applicable` require null. |
| `phenomenon_start`, `phenomenon_end`, `assessment_time` | Optional phenomenon interval and required time at which the actual result or non-observation assessment was produced. Only actual-attempt statuses project `assessment_time` to `sosa:resultTime`; assessment-only statuses receive no SOSA time triple. |
| `perspective_uri`, `applicability_scope_uris` | Standpoint and one or more complete contextual scopes. |
| `source_record_uri`, `evidence`, `rights_uri` | Provenance, directional evidence, and rights statement. |
| `protocol_application_uris`, `authority_assignment_uris` | Applicable governance resources; their presence does not prove observation validity or authorize publication. |
| `review_status`, `review_status_uri` | Compatibility status and its controlled registry resource. |

Results are URI categories, literals, quantities, or numeric ranges. Quantities
and ranges require a unit URI and may carry uncertainty or tolerance; a missing
observation is never encoded as a zero measurement.

`classification_criteria.jsonl` records versioned plans for classification,
including the organological facet, observable properties, permitted procedures,
scheme/version, possible conclusion classes, optional inference logic,
responsible agent, perspective, applicability scopes, authority assignments,
protocol applications, source, evidence, rights, and lifecycle. Scope,
authority, and protocol arrays qualify where and by whose mandate a criterion
may be applied; they do not turn the criterion into an observation or a
conclusion.

| Field | Meaning |
|---|---|
| `uri`, `label`, `description` | Stable identity and human-readable explanation of the criterion. |
| `criterion_type` | Controlled organological facet covering sound production (including resonator versus sympathetic vibrator), construction and acoustics, electronic or modular systems, performer relation, use, manufacture, visual design, historical/geographic context, social or ritual function, symbolic meaning, or community category. See `ORGANOLOGICAL_FOUNDATIONS.md` for the grouped profile. |
| `observable_property_uris`, `procedure_uris` | Permitted properties and procedures used to match assessment premises. Empty arrays leave that side unrestricted. |
| `classification_scheme_uri`, `scheme_version_uri` | Scheme and optional version governed by the criterion. |
| `conclusion_classification_uris` | Possible conclusion classes in that scheme. Empty means the criterion does not enumerate a closed conclusion list. |
| `inference_logic_uri` | Optional rule, decision table, or method identifier. It does not alone establish a complete CRMinf inference graph. |
| `asserted_by_uri`, `perspective_uri`, `source_record_uri` | Accountable author, standpoint, and optional source. |
| `applicability_scope_uris`, `authority_assignment_uris`, `protocol_application_uris` | Context and governance under which the criterion may be applied. |
| `evidence`, `rights_uri`, `status` | Directional evidence, rights, and draft, active, deprecated, or withdrawn lifecycle state. |

Together these registries support the auditable sequence documented in
`ORGANOLOGICAL_MODEL.md`: target state → assessment → actual observation/result
when made → criterion → assignment activity → assertion entity. All three
registries intentionally contain zero contributed records in the reference
snapshot.

The validator also checks the links across that sequence. A referenced
criterion must use the assertion's scheme and, when both are stated, the same
scheme version. If it enumerates possible conclusions, the asserted class must
be among them; the assertion's scopes must be covered by the criterion's
scopes; and any named inference logic must agree. Each referenced assessment
must match the observable-property and procedure restrictions of at least one
referenced criterion. Conversely, when assessment premises are supplied, each
criterion that restricts property or procedure must have a matching
assessment. Finally, an assessment must concern the assertion target, a
structurally connected configuration/component/state/occurrence, or a target
that realizes the asserted instrument concept. These are consistency checks on
an explicit chain, not an inference engine and not proof that the conclusion is
true.

### Compound classification expressions

`classification_expressions.jsonl` preserves a compound source notation, its
grammar and scheme version, ordered members, combination operator, optional
component target and role links, local or shared suffix notation, parse status,
perspective, scope, source, and evidence. The 26 current MIMO values containing
`+` are `tokenized-uninterpreted`: their order and spelling round-trip, but no
component role or suffix scope is guessed. An independently evidenced
`expert-interpreted` expression may add that structure. Its parse status does
not imply review approval; review decisions apply to the classification
assertions that use it. A member class never propagates automatically to the
whole target.

### Cultural protocol applications and use decisions

`protocol_applications.jsonl` records that an authoritative external or
community protocol applies to exact resources, with issuing and applying
agents, represented communities, mandates, provenance, scope, enforcement
mode, lifecycle, and retrieval time.

| Field | Meaning and validation rule |
|---|---|
| `uri` | Stable identity of this application, distinct from the external `protocol_uri`. |
| `target_resource_uris` | One or more exact resources governed by this application. |
| `protocol_uri`, `protocol_type_uri` | Authoritative protocol resource and its controlled type. |
| `issued_by_agent_uri`, `applied_by_agent_uri` | Protocol issuer and agent accountable for applying it in OMARO. |
| `represented_community_uris`, `authority_assignment_uris` | Communities represented and active mandates that must cover each one. |
| `source_record_uri`, `applicability_scope_uris` | Optional source record and one or more complete scopes. |
| `status`, `valid_from`, `valid_until` | Active, withdrawn, superseded, or expired lifecycle and validity interval. |
| `supersedes_uri` | Earlier protocol application replaced by this one, or null. |
| `retrieved_at` | Time at which the protocol representation or attestation was retrieved. |
| `resolution_status` | `verified`, `unverified`, or `unavailable`. Only `verified` can support a public grant. |
| `integrity_verification_method` | `local-sha256`, `external-attestation`, or `none`. A verified application requires one of the first two methods. |
| `protocol_artifact_path` | Safe dataset-relative path used by `local-sha256`; absolute paths and parent traversal are rejected. The file must exist under the dataset root. |
| `integrity_attestation_uri` | Public-safe attestation required for `external-attestation`; it records where the external integrity determination can be audited. |
| `protocol_integrity_sha256` | Lowercase SHA-256 digest required for a verified application. With `local-sha256`, OMARO recomputes and compares it against the bundled artifact. With `external-attestation`, OMARO requires the attestation but cannot independently recompute the external bytes. |
| `enforcement_mode` | `advisory`, `human-decision-required`, or `machine-enforceable`. Machine-enforceable applications additionally require verified `local-sha256`, a bundled artifact path, and a matching digest. |

The method `none` is therefore never integrity-valid for a verified protocol.
An integrity-valid application still does not grant a use, prove a claim,
authenticate the issuer, establish legal rights, or substitute for consent.

`use_decisions.jsonl` records whether exact actions are `granted`, `refused`,
`withheld`, or `withdrawn` for exact target resources, purposes, audiences,
scopes, and times under documented authority and protocol applications.

| Field | Meaning and validation rule |
|---|---|
| `uri` | Stable identity of the decision. |
| `target_resource_uris`, `action_uris` | Non-empty sets of exact resources and actions decided. |
| `purpose_uris`, `audience_uris` | Purpose and audience context. A grant requires at least one value in each field; an empty field on a denial is a wildcard for that dimension. |
| `decision` | `granted`, `refused`, `withheld`, or `withdrawn`. Only `granted` can satisfy a positive authorization path. |
| `decided_by_agent_uri`, `represented_community_uris` | Accountable decision maker and represented communities. |
| `authority_assignment_uris`, `protocol_application_uris`, `applicability_scope_uris` | Mandates, protocols, and scopes on which the decision depends. |
| `decision_method_uri`, `decided_at`, `valid_until` | Decision procedure, decision time, and optional expiry. |
| `status`, `supersedes_decision_uri` | Active, superseded, or expired lifecycle and optional predecessor. |
| `public_evidence_uri`, `public_summary` | Optional sanitized evidence reference and summary; neither may disclose restricted deliberation. |
| `legal_basis_uris`, `legal_basis_status`, `legal_basis_assessed_by_agent_uri` | Public-safe references, controlled state, and accountable assessor for the independent legal-basis determination. |
| `consent_record_uris`, `consent_status`, `consent_assessed_by_agent_uri` | Public-safe references, controlled state, and accountable assessor for the independent consent determination. |

`legal_basis_uris`, `legal_basis_status`, and
`legal_basis_assessed_by_agent_uri` document the separately attributed legal-
rights determination. `consent_record_uris`, `consent_status`, and
`consent_assessed_by_agent_uri` document the separately attributed individual-
consent determination using public-safe references rather than private records.
For either gate, both `documented` and `not-required` require at least one
reference and a registered accountable assessor. `not-required` is a positive,
attributed determination for the concrete use, not an empty array or default.

Publication grant matching is deliberately asymmetric. A grant must declare
at least one purpose and audience, contain every requested purpose, audience,
target, and scope, and name every applicable protocol application. A request
that requires an explicit grant supplies at least one purpose and audience;
empty values cannot mean an unrestricted grant. Its deciding agent must have
an active authority assignment whose `covered_action_uris` contains the exact
requested action. A refusal, withholding, or withdrawal needs only an
overlapping target and matching action/context to veto the request. An empty
purpose or audience on a denial acts as a wildcard for that dimension;
otherwise an overlap is sufficient. Every decision declares at least one
scope, and a denial matches a request through scope overlap. A narrow grant
cannot cancel a relevant denial. Every represented community from the
applicable protocols must be covered by an active grant. Several complete
grants may jointly cover different communities, but partial target, scope,
purpose, audience, or protocol coverage is never unioned into a new grant. The
public build checks these authorization gates before writing any output.
Community-governed material fails closed when the positive path is missing,
ambiguous, expired, or contradicted. See `CULTURAL_GOVERNANCE.md` for the
independent truth, rights, collective-authority, individual-consent, and
publication-action gates.

Two actual mapping sets illustrate how target level and scope prevent false
flattening. “Double bass” maps to `321.322`, `321.322-5`, and `321.322-71`;
reviewed technique-specific uses belong on separate `sounding-realization`
targets carrying `actual_playing_technique_uris`, or on assertions referencing
`specified` scopes whose `playing_technique_uris` state when the claim applies.
“Alto trombone” maps to `423.22` and `423.233.1`; an inspected specimen receives
the supported physical-object assertion referencing a `specified` scope whose
`instrument_configuration_uris` identifies the mechanism, or each mechanism is
modeled as a separately identified `instrument-configuration` target. The two
scope fields belong to `ApplicabilityScope`; neither is an assignment field.
The source-derived mappings themselves remain `instrument-concept` occurrences
with `source-silent` scope. See `MULTIPERSPECTIVITY.md` for exact concept URIs,
the distinction between perspective and scope, and the authoring pattern.

`concept_relation_assertions.jsonl` applies the same perspective, scope,
evidence, stance, authority, source, and policy pattern to qualified SKOS
hierarchy and mapping proposals. It is the correct layer for alternative
broader/narrower/related relations or cross-scheme mappings; MIMO's unmodified
relations remain in `source_relations.jsonl`.

| Field | Meaning |
|---|---|
| `uri` | Stable identifier for this qualified relation assertion. |
| `subject_concept_uri`, `predicate_uri`, `object_concept_uri` | Reified SKOS relation. Supported structural predicates are `broader`, `narrower`, and `related`; supported mapping predicates are `exactMatch`, `closeMatch`, `broadMatch`, `narrowMatch`, and `relatedMatch`. |
| `assigned_by_uri`, `generated_by_uri` | Accountable asserting agent and optional software generator. |
| `perspective_uri`, `relation_method_uri` | Standpoint and method under which the relation is proposed. |
| `mapping_purpose_uris` | Operations for which a SKOS mapping is stated to be suitable. A mapping predicate requires one or more values; a structural predicate requires an empty array. OMARO provides `query-expansion`, `display-navigation`, `data-transformation`, and `scholarly-comparison` purpose concepts, while externally governed purpose URIs remain valid. |
| `stance`, `applicability_scope_uris` | Claim position and one or more complete alternative applicability scopes. |
| `evidence`, `authority_assignment_uris` | Directional evidence and any exact mandates claimed by the assertion. |
| `valid_from`, `valid_until` | Optional assertion-validity interval. |
| `projection_policy_uris` | Policies under which the qualified assertion may be evaluated. |
| `source_record_uri`, `assertion_origin` | Versioned provenance record and origin category. |

A mapping-purpose value is an operational suitability claim, not a guarantee
of truth, a lossless conversion, a licence, community authorization, consent,
or permission to expose either concept. Mapping assertions therefore remain
qualified in RDF: emitting a bare SKOS mapping triple would discard their
purpose. Publication and reuse are evaluated independently through applicable
`ProtocolApplication` and action-, purpose-, audience-, scope-, and
time-specific `UseDecision` records.

MIMO's legacy Danish tag `dk` is normalized to BCP 47 `da`; untagged source
labels use `und`.

## Convenience classification CSV

`dist/csv/classification-assignments.csv` contains one row per assignment
occurrence. Array and evidence fields use canonical JSON inside CSV cells.

| Field | Meaning |
|---|---|
| `assertion_uri` | Stable classification-assertion identifier. |
| `classification_uri` | Stable classification join key. |
| `classification_notation` | Hornbostel–Sachs notation. |
| `classification_label_en` | English preferred classification label. |
| `assignment_uri` | Stable assignment-activity identifier. |
| `target_uri` | Stable classified-target join key. |
| `target_label_en` | English preferred label; empty for unresolved stubs. |
| `target_resolution_status` | `resolved` or `unresolved`. |
| `target_type`, `classification_scheme_uri`, `scheme_version_uri` | Target level and scheme identity. |
| `assertion_origin`, `stance` | Provenance class and claimant stance. |
| `assigned_by_uri`, `generated_by_uri`, `perspective_uri` | Claimant, generator, and standpoint. |
| `classification_method_uri`, `criteria_uris_json` | Absolute method URI and governed criteria. |
| `assessment_uris_json`, `inference_logic_uri`, `classification_expression_uri` | Observation-assessment premises, inference logic, and compound expression. Status determines whether a premise is also an actual observation in RDF. |
| `applicability_scope_uris_json`, `evidence_json` | Context and evidence. |
| `authority_assignment_uris_json`, `valid_from`, `valid_until` | Authority and validity lifecycle. |
| `projection_policy_uris_json` | Named graph policies. |
| `source_record_uri` | Versioned source-record foreign key. |
| `source_predicate_uri` | Preserved MIMO mapping predicate. |
| `source_uri` | MIMO source concept for the mapping. |

Consult both canonical layers when auditing how a classification was derived.

`dist/csv/concept-relation-assertions.csv` and the SQLite
`concept_relation_assertions` table expose `mapping_purpose_uris_json` as a
canonical JSON array. Consumers must preserve that column when exchanging a
mapping; dropping it changes the meaning of the assertion. Structural
broader/narrower/related rows retain the column with `[]`.

## SQLite

The database contains `schemes`, `perspectives`, `applicability_scopes`,
`projection_policies`, `authority_assignments`, `concepts`, `labels`, `label_resources`,
`label_assertions`, `label_profiles`, `note_assertions`,
`language_registries`, `script_registries`, `source_relations`,
`organological_targets`, `classification_criteria`,
`observation_assessments`, `classification_expressions`,
`classification_assertions`, `classification_assignments`,
`concept_relation_assertions`, `protocol_applications`, `use_decisions`,
`agents`, `source_records`, `review_statuses`, `quality_rules`,
`quality_findings`, `review_events`, `review_decisions`, `concept_ancestors`,
and `metadata`.
`concept_ancestors` materializes every transitive `skos:broader` path using the
minimum distance (`depth`), excluding self-relations. Direct parents have depth
1. The indexed reverse lookup supports efficient descendant queries without
recursive SQL.

`assertions` is a normalized union of classification, label, and note
assertions. It exposes a common subject–predicate–object shape plus claimant,
source, origin, and stance fields; literal objects and URI objects remain in
separate nullable columns so their RDF distinction is not lost.
`audit_queue` exposes all machine findings awaiting human interpretation.

`preferred_labels`, `labels_enriched`, `skosxl_labels`,
`label_linguistic_profiles`, `notes_enriched`, `assertions`, `audit_queue`,
`classification_claims`, `classification_targets`,
`classification_claims_enriched`, and `mimo_source_exact_matches` are
read-only views. `classification_claims` lists every qualified assignment.
`classification_targets` is deliberately narrower. It is backed by the
materialized `endorsed_classification_assertions` set produced by the same
canonical policy evaluator used for RDF. In policy 2.2.0, a claim must opt into
the endorsed policy, be active and eligible, use a `context-independent` scope,
have independent authorized `referential` and `scholarly` acceptances, and have
no active veto decision. A specified claim requires query context and therefore
cannot be flattened into this static view.
The source view exposes preserved MIMO mappings for audit. `label_search` is an
FTS5 table using SQLite's Unicode tokenizer. The metadata table records the
Python and SQLite versions used to build the database.

For context-aware selection that cannot be expressed by a context-free SQL
view, `Dataset.scope_matches`, `Dataset.claim_applies_in_context`,
`Dataset.is_endorsed_for_context`, and
`Dataset.community_validation_decisions` implement the documented AND/OR,
unresolved-scope, lifecycle, endorsement, and community-authority rules. Query
context uses URI arrays for the seven scope dimensions, `at` for subject-matter
time, and `as_of` for claim/review lifecycle time.

Use `PRAGMA user_version` to detect database schema version `20200`, meaning
schema 0.1.0. URI columns—not labels, pair identity, or `mimo_id`—are the
supported join keys.

## RDF layers

The project namespace is
`https://w3id.org/modavis/omaro#` (`omaro:`).
SKOS-XL uses `http://www.w3.org/2008/05/skos-xl#`, provenance uses
`http://www.w3.org/ns/prov#`, and observations use
`http://www.w3.org/ns/sosa/`. OMARO does not emit OntoLex forms without genuine
lexical-entry evidence.

`dist/rdf/omaro.*` is the project-facing graph. It contains
source hierarchy relations and qualified `omaro:classifiedAs` assertions but no
unqualified `skos:exactMatch`. Each assertion entity uses RDF statement
subject/predicate/object links and `prov:wasGeneratedBy` to a distinct assignment
activity. Together they retain scheme, perspective, scope, method, premises,
stance, directional evidence, authority, policies, source, and lifecycle. A direct
`omaro:classifiedAs` triple is emitted only by the project-endorsed rule described
above; the current graph has none because no qualifying review exists.

Classification assignments use `omaro:usedAssessment` for every premise named
by the compact record. They additionally use `omaro:usedObservation` only for a
premise typed as an actual organological observation. This preserves
`not-observed` and `not-applicable` as non-activity assessments in OWL-aware
consumers.

`dist/ontology/0.1.0/omaro.*` is the compact, version-addressed ontology
vocabulary. It contains the stable and versioned ontology headers plus all
owned class and property declarations, labels, definitions, types, stable
ranges, and the ontology-owned mapping-purpose concept scheme and terms. It
deliberately excludes MIMO concepts, source assertions, review
findings, and other reference-dataset instances. The three serializations are
RDF-isomorphic.

`omaro:Perspective`, `omaro:ApplicabilityScope`, `omaro:AuthorityAssignment`,
`omaro:ClassificationAssignment`, `omaro:ReviewEvent`,
`omaro:ReviewDecision`, `omaro:OrganologicalTarget`,
`omaro:ObservationAssessment`, `omaro:OrganologicalObservation`,
`omaro:ClassificationCriterion`,
`omaro:ClassificationExpression`, `omaro:ProtocolApplication`,
`omaro:UseDecision`, `omaro:ProjectionPolicy`, `omaro:Evidence`, and
`omaro:ConceptRelationAssertion` are first-class RDF resources. SHACL checks their
required links and cardinalities; the canonical validator additionally checks
scope logic, source reversibility, policy membership, authority matching, and
review supersession.

The graph declares the stable ontology IRI as `owl:Ontology`, links it to the
immutable 0.1.0 version IRI, declares every owned property as an OWL object or
datatype property, and emits lifecycle dates as typed XSD values. The canonical
term namespace is `https://w3id.org/modavis/omaro#`. Resolver rules and
versioned publication targets are staged in `w3id/modavis/omaro/`; resolution
must not be described as active until the upstream W3ID registration and
post-deployment checks in `W3ID_REGISTRATION.md` are complete.

The graph also contains URI-identified `skosxl:Label` resources, each with
exactly one `skosxl:literalForm`. A `omaro:LabelProfile` linked from each label resource
projects BCP 47 components, observed Script codes, policies, context,
provenance, and review state. Language and Script registry entities identify
the dated evidence used by the projection. `omaro:LabelAssertion` and
`omaro:NoteAssertion` resources are represented
using RDF statement subject/predicate/object links, PROV attribution and
derivation, versioned source records, and review-status resources. Direct SKOS
label and definition literals remain compatibility triples. Each label
assertion links to its lexical resource with `omaro:labelResource`; direct
`skosxl:prefLabel`, `skosxl:altLabel`, and `skosxl:hiddenLabel` links mirror the
SKOS-compatible projection.

`omaro:QualityFinding` resources link warnings to their rule, target assertion,
concept, detector, validation dimension, and explicit `reviewEffect "none"`.

## Publication and quality metadata

`dist/metadata/dqv.ttl` contains DQV measurements computed on the immutable
dataset version. Stable metric resources define their quality dimension,
expected datatype, and interpretation. Measurements retain the software agent,
generation time, and any denominator needed for a rate. They describe dataset
fitness signals only: they are not organological observations, review events,
quality certificates, cultural validation, or permission decisions.

`omaro-v0.1.0.dcat.ttl` is generated after the release archive and remains
outside it. It distinguishes the stable dataset from version `0.1.0`, describes
the ZIP as a DCAT distribution, and records download URL, IANA package format,
byte size, distribution licence, and SPDX SHA-256 checksum. A DCAT catalogue
record identifies the metadata sidecar. `SHA256SUMS` verifies both the archive
and sidecar; the sidecar cannot contain its own checksum without a circular
claim.

The release ZIP contains `ro-crate-metadata.json` in its root. This RO-Crate
1.3 JSON-LD descriptor identifies the root dataset and representative local
directories, documentation, examples, and manifests. Directory entities avoid
duplicating the complete generated-file inventory in `dist/manifest.json`.
Every represented local entity exists in the archive and is reachable through
`hasPart`. RO-Crate metadata supplements rather than replaces the canonical
registries, manifests, RDF provenance, or external checksum.

`dist/rdf/mimo-source-snapshot.ttl` is the preserved MIMO source graph. It
retains MIMO's original `skos:exactMatch` mappings and identifies the snapshot
as a provenance bundle.

## VAO and MODAVIS interoperability metadata

`dist/metadata/vao-classification-example.json` is a standalone instance of
the VAO 0.4.0 classification object. Its `scheme`, `code`, localized `label`,
and `version` are derived from the canonical classification concept and scheme
registry; no value is maintained separately.

The dataset, ontology header, DCAT record, and
`dist/schema/modavis-vao-relations.ttl` link to the finalized VAO 0.4.0 and
released MODAVIS 0.1.0 resources with `dcterms:relation`. These are discovery
links, not `dcterms:conformsTo` claims. The relation file deliberately contains
no OWL imports, equivalence axioms, or subclass axioms. Field mappings and the
reason for this boundary are normative in `MODAVIS_VAO_INTEROPERABILITY.md`.

## Query input and explanation API

`omaro query` reads canonical data and returns complete classification
occurrences with selection and endorsement explanations. Its optional context
is a tooling input defined by `schema/query_context.schema.json`, not a new
canonical table. The URI dimensions, `at`/`as_of`, result fields, reason codes,
error behavior and tested recipes are specified in [USE_CASES.md](USE_CASES.md).
`Dataset.explain_endorsement` is the shared implementation behind the Boolean
endorsement APIs; it does not grant publication permission. The query entry
point checks publication authorization before returning records or counts.

Activity/entity URI separation and the distinct scope obligations for positive
review support and review vetoes are normative cross-record contracts detailed
in [INFERENCE_AND_VALIDATION.md](INFERENCE_AND_VALIDATION.md).

## Open Knowledge Format bundle

`dist/okf` is a generated OKF v0.2 navigation view. Its root `index.md` declares
`okf_version: "0.2"` and points
to curated interpretation guides, Hornbostel–Sachs family indexes, and MIMO
instrument ID-range indexes. Non-reserved documents contain YAML frontmatter;
the required `type` distinguishes datasets, guides, classifications, and
instrument concepts. `resource` contains the canonical MIMO URI.
The implemented profile follows the official specification at
`https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md`.

The v0.2 frontmatter uses `generated` instead of the superseded v0.1
`timestamp`. Every concept document also records `status` and `sources`.
Generated dataset and vocabulary-concept pages contain a `verified` event from
`process:okf-projection-validation`; this means that the deterministic
projection, YAML profile, links, and canonical consistency passed machine
checks. Guides intentionally carry no `verified` field because their
interpretive advice has not been independently confirmed. Neither form implies
human organological review. Assertion-level review remains in the
classification, label, and note assertion layers.

MIMO Hornbostel–Sachs classification pages use
`classifications/concepts/<local_id>.md`. Numeric MIMO
instrument pages are partitioned into stable ranges under
`instruments/<range>/<local_id>.md`; other scheme concepts use
`schemes/<scheme-hash>/<kind>/<sanitized-local-id>-<uri-hash>.md` to prevent
path collisions across schemes and writing systems. Markdown links expose direct broader,
narrower, and qualified classification relationships. Label tables expose the
submitted and canonical tags, registry status, role, observed Script codes,
translation status, SKOS projection state, SKOS-XL resource, assertion URI,
and review status. Page `sources` identify the relevant concept plus canonical
classification, label, profile, note, and quality layers. The referenced
profile records in turn identify the versioned source, IANA registry, and
Unicode Script registry used by the projection.
The OKF pages are
convenience views; the canonical source and classification-assertion layers
remain the auditable records.

## Self-contained RAG JSONL

`dist/jsonl/rag-concepts.jsonl` contains one record per canonical concept:

| Field | Meaning |
|---|---|
| `uri` | Canonical concept URI and recommended retrieval document ID. |
| `kind`, `local_id`, `mimo_id`, `scheme_uri`, `notation` | Stable identity and optional MIMO metadata. |
| `definition`, `created`, `resolution_status` | Source content and resolution state. |
| `labels` | Compatibility preferred, alternative, and hidden labels grouped by language. |
| `label_resources` | Complete assertion-scoped SKOS-XL lexical resources referenced by the concept. |
| `label_profiles` | Complete conservative linguistic profiles for those resources. |
| `assertions` | Complete qualified label and note assertions for the concept. |
| `quality_findings` | Deterministic warnings targeting the concept's assertions; each retains `review_effect: none`. |
| `review_events` | All decisions targeting this concept's label, note, profile, or classification occurrences; decisions are not collapsed. |
| `relationships` | Direct broader/narrower links, transitive ancestors with depth, and qualified classifications. |
| `provenance` | Source URI, retrieval time, dataset version, DOI, layer and registry names, and source endpoints. |
| `retrieval_text` | Compact textual representation suitable for lexical or embedding indexes. |

Classification relationship entries contain compact target references plus
every assignment occurrence with its URI, origin, stance, assigning agent,
perspective, scopes, evidence, authority, policies, original predicate, and
source.
Other relationship entries contain the target URI, MIMO ID, kind, display
label, resolution status, and notation where applicable. Embeddings are not
distributed because they are model-specific.

## Legacy JSON

The root JSON files are non-normative convenience projections for the original
scripts. Schema 0.1 makes no backward-compatibility guarantee for them. They
cannot express multiple perspectives, scopes, authority, evidence, or
non-collapsing review decisions and must not be used for culturally sensitive
or policy-aware applications.
