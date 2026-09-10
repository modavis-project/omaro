# Illustrative organological assessment records

These records demonstrate OMARO 0.1 target, observation-assessment, criterion,
classification-expression, assignment/assertion, authority, protocol, and
use-decision shapes. They are not part of `data/canonical/` and are not loaded
by the OMARO build.

All collection objects, observations, events, agents, community resources,
mandates, and decisions under `https://example.org/omaro-evaluation/` are
synthetic. They do not describe a real object or community and do not supply
real authority or permission. References to MIMO identify the published
classification source used to explain notation; they do not turn the
illustrative specimen observations into empirical evidence.

Each non-empty line in a `.jsonl` file is one record conforming to the JSON
Schema named for that file in `manifest.json`. The bundle deliberately tests
the new record shapes, not the complete canonical-dataset foreign-key and
checksum contract. Referenced perspectives, scopes, agents, schemes,
procedures, properties, rights statements, and review statuses are therefore
URI placeholders or existing public vocabulary resources rather than a second
copy of the canonical registries.

Every row in `observation_assessments.jsonl` is an
`omaro:ObservationAssessment`. Rows with `detected`, `not-detected`, or
`indeterminate` status also represent actual observation attempts and project
to `omaro:OrganologicalObservation`, SOSA `Observation`, and CRMsci
`S27 Observation`. The bundle contains all five assessment statuses:

| Status | Rows | Meaning in this bundle |
|---|---:|---|
| `detected` | 30 | A synthetic attempt produced a positive or categorical result. |
| `not-detected` | 1 | A synthetic inspection looked for active woodworm evidence and returned an explicit negative result. |
| `indeterminate` | 1 | A synthetic performance observation occurred but did not determine the jingle alloy. |
| `not-observed` | 1 | The fixture explicitly records that no bore measurement was made. |
| `not-applicable` | 1 | Present-day direct inspection is inapplicable to a separately identified historical configuration. |

The `not-observed` and `not-applicable` rows remain assessments only: they do
not assert that an observation occurred. This is why absence of a catalogue
entry cannot be treated as a negative measurement. Classification assignments
link every listed premise with `omaro:usedAssessment` and add
`omaro:usedObservation` only for the three actual-attempt statuses. The
historical bassoon assignment uses both its documentary key-count observation
and the separate `not-applicable` direct-inspection assessment. The latter
qualifies the method; it is not negative evidence for the key count and
receives no `omaro:usedObservation` triple.

The examples use absolute `classification_method_uri` values. Every target,
assessment, criterion, and classification expression explicitly states its
authority and protocol links; expressions also carry an explicit rights URI.
Empty authority and protocol arrays are deliberate for the non-governed
bagpipe, tambourine, and bassoon fixtures rather than missing data. The
community-drum target, its seven construction, morphology, and excitation
assessments, and its two criteria instead reference the covered synthetic
mandate and protocol. Neither compound expression contains community-governed
material, so both use empty governance arrays and the fixture's CC0 rights URI.

The worked premise lists are intentionally complete for the exact conclusions
they propose. The bagpipe assignment includes separate chanter and drone bore
assessments, reed, fingerhole, and reservoir assessments, and a functional
assessment reporting drone tuning by varying effective air-column length. That
last premise is required for the `-62` feature represented by the linked whole
classification resource.

The tambourine assignments use separate criteria for
[`211.311`](http://www.mimo-db.eu/HornbostelAndSachs/116) and
[`112.12`](http://www.mimo-db.eu/HornbostelAndSachs/43). A proposed `211.311`
premise set records a body depth not greater than the membrane radius, no rigid
handle, exactly one tightly stretched membrane, direct striking, and the
membrane sounding. A proposed `112.12` premise set records rattling objects
attached to the object that serves as their carrier, an intention to produce
sound clusters or noise, indirect shaking, and the attached objects sounding.
The combined occurrence explicitly records both direct striking and indirect
shaking, so its two member assertions reuse the appropriate construction
premises without treating either class as supported by technique alone.

The drum `211.311` premise set records a cylindrical body, a body depth not
greater than the membrane radius, no rigid handle, exactly one tightly
stretched membrane, and direct striking. Every one of these records is
synthetic, proposed, and unreviewed; premise completeness within the fixture is
not empirical evidence that a real instrument has those features, nor does it
turn the illustrative inference identifiers into executable rules.

The `inference_logic_uri` values are stable illustrative identifiers, not
included executable rule artifacts. Before any such logic is promoted beyond a
draft example, its publisher should provide an immutable, versioned and
retrievable rule specification or decision table. That artifact should define
accepted property, procedure, status and result inputs; conclusion classes;
the role of qualifying non-observation assessments; accountable authors and
review; rights; a content digest; and positive and negative conformance tests.
Until then, the URIs document a claimed reasoning step without making it
machine-reproducible.

The bagpipe fixture also demonstrates an important identifier boundary. Its
exact expression is `422.112-7+422.22-62`, but the linked member resources
[`.../318`](http://www.mimo-db.eu/HornbostelAndSachs/318) and
[`.../328`](http://www.mimo-db.eu/HornbostelAndSachs/328) are base classes with
canonical notations `422.112` and `422.22`. The whole assertion uses
classification resource
[`.../6415`](http://www.mimo-db.eu/HornbostelAndSachs/6415), whose canonical
MIMO notation is `422.112+422.22-62`, without the local `-7` refinement. The
expression record therefore preserves the exact literal, ordered member
tokens, and local/shared suffixes while the class URIs remain semantic anchors.
It neither relabels those resources nor treats token strings as URI identity;
an exact
full-code concept would require its own registered URI or explicit mapping.

The cases are:

- a Highland bagpipe configuration with an expert-interpreted compound
  expression and explicit chanter, drone-set, and shared-reservoir targets;
- a tambourine with separate struck, shaken, and simultaneous sounding
  realizations;
- a synthetic historical bassoon with original and modified configurations
  plus a distinct present condition state; and
- a synthetic community-governed drum category that coexists with a
  Hornbostel–Sachs claim and has an action-specific display grant.

## Purpose-qualified relation examples

`concept_relation_assertions.jsonl` contrasts a mapping with a structural
relation. The first row proposes `skos:closeMatch` between the Hornbostel–Sachs
`211.311` fixture class and a synthetic museum frame-drum category. It names
only `mapping-purpose-query-expansion` and
`mapping-purpose-scholarly-comparison`. A consumer may therefore consider it
for those operations under the assertion's perspective, scope, evidence,
stance, and policy; it may not silently use the row for data transformation or
display navigation. The mapping stays reified in RDF because a bare
`skos:closeMatch` triple would erase that operational boundary.

The second row proposes an in-vocabulary `skos:related` relation between two
synthetic museum categories used in the tambourine example. Its
`mapping_purpose_uris` array is empty: it states vocabulary structure rather
than a purpose-qualified cross-scheme mapping. JSON Schema, model validation,
and SHACL reject the inverse combinations—a mapping without a purpose and a
structural relation with one.

Neither example grants permission. Even the display-navigation purpose would
mean only that a mapping was considered suitable for constructing a link; an
applicable protocol and an action-, purpose-, audience-, scope-, and
time-specific use decision would still govern whether either concept and its
supporting material may be displayed. Both records are synthetic, proposed,
unreviewed fragments and make no blanket claim of mapping safety or identity.

## Governed fixture contract

The community-governed case includes a synthetic active mandate in
`authority_assignments.jsonl`. Its subject matter covers every governed target
listed by the protocol and use decision, its scope matches those records, and
its validity interval covers the protocol application and decision time. Its
`covered_action_uris` contains only the display action used by the decision.
This demonstrates structural coverage only; it does not claim real authority
or authorize any unlisted action.

`synthetic-community-protocol.json` contains the exact synthetic protocol
bytes used by the fixture. `protocol_applications.jsonl` records
`resolution_status: verified`, `integrity_verification_method: local-sha256`,
the safe dataset-relative `protocol_artifact_path`, and the artifact's lowercase
SHA-256 digest in `protocol_integrity_sha256`. The external-attestation field is
null because this fixture is checked locally. Changing the file without
updating and re-verifying the digest invalidates the fixture. `unverified` or
`unavailable` resolution, `none` verification, an unsafe or missing path, or a
missing or mismatched digest cannot support this public grant. An external
attestation would instead require `integrity_attestation_uri`; it would not be
sufficient for `machine-enforceable` mode.

The display grant in `use_decisions.jsonl` names its synthetic assessment in
`legal_basis_uris`, sets `legal_basis_status` to `documented`, and attributes
that determination with `legal_basis_assessed_by_agent_uri`. Its
`consent_status` is `not-required` because the fixture contains no person,
voice, image, interview, or other personal contribution, but the field is not
left unsupported: `consent_record_uris` names the synthetic not-required
assessment and `consent_assessed_by_agent_uri` names its accountable assessor.
For both legal basis and consent, `documented` and `not-required` require a
reference and assessor. `not-required` must be established for the concrete
use; it is not a default for real data. `unknown`, `withheld`, or `withdrawn`
consent and `unknown` or `blocked` legal basis do not permit publication.

A `granted` decision is usable only while every applicable protocol is resolved
and integrity-verified, every referenced authority assignment is active and
covers the targets, scope, community, exact action, and decision time, and the
legal-basis and consent states allow the exact use. A grant must contain all
requested targets and scopes and every applicable protocol; its declared
purpose and audience restrictions must also contain the request. Partial grants
across targets, scopes, purposes, audiences, or protocols are not combined;
separate complete grants may still be required for different represented
communities. A matching refusal, withholding, or withdrawal vetoes the request.
The fixture grant covers only its named display action,
expert-evaluation purpose, appointed-reviewer audience, targets, scope, and
time. It does not authorize indexing, bulk export, translation, media
publication, or any other use.
