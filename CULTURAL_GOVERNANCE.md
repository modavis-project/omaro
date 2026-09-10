# Cultural governance and publication control

## Purpose and limits

This document defines the minimum cultural-governance and publication contract
for OMARO. It applies to community-origin, community-governed, culturally
sensitive, or potentially restricted organological knowledge and media. It is
not legal advice, a substitute for a community's governance, or evidence that
the current reference dataset has achieved shared governance.

The reference dataset preserves a public MIMO source snapshot. At publication
time it contains no community-contributed classification scheme, community
authority mandate, community review decision, Local Contexts Label application,
or community use decision. The relevant registries are therefore capability
and enforcement surfaces, not evidence of consent, representation, or cultural
validation. In particular, the canonical `protocol_applications` and
`use_decisions` registries intentionally begin empty. No community-governed
record may be added to a public release merely to demonstrate those schemas.

The governing principle is:

> Being permitted to hold, believe, describe, review, or technically export
> information does not by itself authorize its public use.

## Five independent determinations

Every workflow must keep the following questions separate. A positive answer
to one does not answer another.

| Determination | Question | OMARO record or control | Must not be inferred from |
|---|---|---|---|
| Epistemic review | Is a claim accepted, disputed, rejected, or unresolved in a named validation dimension and scope? | `ReviewEvent` and generated `ReviewDecision`; projection policy | Licence, consent, protocol, or publication permission |
| Legal rights | What copyright, database, contractual, privacy, statutory, or other legal conditions apply? | `rights_uri`, rights evidence, external rights statement or policy | Scholarly acceptance, public availability, or community acceptance |
| Collective authorization | Has the relevant collective, through its own procedure and authorized representative, approved a contribution, protocol, or class of uses? | `AuthorityAssignment`, `ProtocolApplication`, and community evidence | Institutional custody, scholarly expertise, individual employment, or self-identification alone |
| Individual consent | Has each identifiable person consented to the specific collection and use of their personal contribution, image, voice, biography, or other personal data? | External consent record referenced from a restricted system; public OMARO data contains only a safe authorization reference when allowed | Collective authorization, copyright ownership, participation in a public event, or consent for another purpose |
| Publication action | Is this exact action allowed for these resources, purpose, audience, scope, and time? | `UseDecision` plus publication preflight | Projection eligibility, a generic open-data policy, a protocol application, or an earlier different use |

Review dimensions remain independent. An organologist can accept the
referential or scholarly basis of a Hornbostel–Sachs assignment without
speaking for a community. An authorized community reviewer can accept or
reject community appropriateness without deciding a measurement's technical
accuracy. A rights reviewer can confirm licence compatibility without deciding
that publication is culturally appropriate.

## Normative OMARO resources

### Authority assignments

An `AuthorityAssignment` documents a mandate for an agent, role, represented
community, subject matter, validation dimensions, covered use actions,
applicability scope, validity interval, delegation rule, evidence, rights, and
revocation semantics.
Authority is evaluated at the time of the decision. It must cover relevant
subject matter through an exact target, protocol-application, or protocol URI,
as well as the decision scopes; a broad institutional role is not substituted
for a community mandate.

`covered_action_uris` is an explicit boundary on publication authority. The
agent making a `UseDecision` must hold an active rights mandate that lists the
requested action URI. Authority to approve a display does not imply authority
to approve indexing, bulk export, translation, streaming, model training, or
commercial reuse. An empty array is appropriate for a mandate that supports
epistemic review but grants no power to decide publication or reuse.

OMARO records an authority claim, but cannot determine whether a community's
actual decision procedure was legitimate. Contributors must verify the
community-defined procedure outside the schema, including any requirements for
council approval, quorum, multiple signatories, subgroup authority, gendered
or hereditary roles, compensation, appeals, or periodic renewal.

### Protocol applications

A `ProtocolApplication` records that an authoritative external or community
protocol applies to named target resources. It identifies the protocol and
type URIs, issuing and applying agents, represented communities, authority
mandates, source, scope, enforcement mode, status, validity interval, and
retrieval time.

It answers **which protocol applies**. It does not assert:

- that the classified claim is true;
- that copyright is owned or licensed;
- that every represented individual consented;
- that a requested action is permitted; or
- that repository staff may reinterpret the protocol.

An `advisory` protocol requires people and applications to present the guidance
without claiming automated enforcement. `human-decision-required` prevents an
automatic grant. `machine-enforceable` may be used only when the relevant
authority has supplied an unambiguous rule and the implementation has a tested,
lossless action mapping.

A recorded SHA-256 digest proves only that two byte sequences are identical.
It does not prove who issued the protocol, that the resolver is authentic, that
the protocol remains current, that its interpretation is correct, or that the
applying agent has authority. `resolution_status: verified` is therefore valid
only with a named integrity method and a lowercase SHA-256 digest:

- `local-sha256` requires a safe dataset-relative `protocol_artifact_path`.
  OMARO rejects absolute paths and parent traversal, requires the file to remain
  under the dataset root, and recomputes its digest from the bundled bytes.
- `external-attestation` requires an `integrity_attestation_uri`. The public
  record identifies an external determination, but OMARO cannot independently
  recompute the bytes that were inspected or prove the attester's authority.
- `none` cannot support a `verified` protocol or a publication grant.

`machine-enforceable` is intentionally narrower: it requires a verified local
artifact, `local-sha256`, and a matching recomputed digest. An external
attestation can support integrity checking for a human-governed protocol, but
cannot make that protocol machine-enforceable. Merely supplying a well-formed
hexadecimal value is not verification. Retrieval time, version, issuer,
authority, meaning, and supersession must still be checked independently.

### Use decisions

A `UseDecision` records an action-, purpose-, audience-, scope-, and
time-specific decision for exact target resources. It identifies the deciding
agent, represented communities, authority assignments, protocol applications,
decision method, decision time, validity, and any superseded decision. The
decision is one of:

- `granted`;
- `refused`;
- `withheld`; or
- `withdrawn`.

`withheld` is not a grant and must not be interpreted as a weak refusal that an
application may override. It supports cases where a decision cannot be made,
where the authorized body declines to disclose its reason, or where further
consultation is required. A public summary or evidence URI is optional because
the justification itself may be restricted.

Each materially different action requires coverage. Displaying a label,
serving an image, streaming audio, exposing an API response, indexing a term,
including content in a bulk download, allowing commercial reuse, translating a
description, and using content in a derived corpus are not interchangeable.

The legal-basis and consent fields on a `UseDecision` are public attestations
about determinations made in responsible external systems. They are not
self-proving. `documented` requires a permitted reference to an independently
reviewed determination for the same people, resources, action, purpose,
audience, and time. `not-required` also requires an accountable determination;
it is not a default that a cultural decision maker or repository operator may
select merely because no record was found.

Accordingly, `legal_basis_status` of `documented` or `not-required` requires at
least one entry in `legal_basis_uris` and a registered
`legal_basis_assessed_by_agent_uri`. `consent_status` of `documented` or
`not-required` likewise requires at least one entry in `consent_record_uris` and a
registered `consent_assessed_by_agent_uri`. These URIs should be public-safe
audit references, not private agreements or personal data. `unknown`,
`blocked`, `withheld`, or `withdrawn` states never satisfy the positive gate.

Grant matching is containment-based. A grant must declare at least one purpose
and at least one audience, and the publication request must do the same. Every
requested purpose and audience must be contained in that one grant, as must
every requested target and scope and every applicable protocol application.
An empty purpose or audience is therefore never an unrestricted grant: it is
invalid for `granted` decisions and fails authorization in a request.

Denials are deliberately broader. For `refused`, `withheld`, or `withdrawn`,
an empty declared purpose or audience is a wildcard for that dimension;
otherwise an overlap with the request is sufficient. A denial with the exact
action, an overlapping target, and overlapping or wildcard context vetoes the
request. Requested scopes must be contained by a grant, while an overlapping
declared scope is sufficient for a denial. Every decision declares at least
one scope. The deciding agent's authority must cover the exact action. This
asymmetry prevents several dimensionally partial grants from being combined
into authority that no decision maker issued. Several otherwise complete
grants may still be needed so that every community represented by overlapping
protocols is explicitly covered.

### Review and projection

A projection policy determines which qualified claims may appear in a named
epistemic view. It does not authorize publication. A claim may pass scholarly
review but be withheld from every public output. Conversely, a source may be
legally and culturally publishable while its classification remains disputed.
Applications must report those states separately.

## Fail-closed publication behavior

Community-governed material is denied public output unless a complete positive
authorization path exists. The preflight must establish all of the following:

1. every governed target resource is identified before generation begins;
2. every applicable active protocol application is resolved and passes its
   stated local or external integrity-verification method;
3. the requested action and time are covered by an active `granted` use
   decision; all requested targets and scopes, every applicable protocol, and
   all purpose or audience restrictions must be contained by that grant;
4. every required authority assignment is active, covers the represented
   community, relevant subject matter, decision scopes, exact action, and
   decision time, and has not been retroactively revoked;
5. any required individual-consent determination is referenced and attributed
   to its accountable assessor for the same purpose and action; an attributed
   `not-required` determination is also explicit;
6. the legal-basis determination is independently referenced and attributed to
   its accountable assessor for the action, including when it is
   `not-required`;
7. no active `refused`, `withheld`, or `withdrawn` decision covers the action;
8. no active superseding protocol or decision invalidates the path; and
9. only the public, sanitized authorization metadata approved for disclosure
   would enter the release.

If any fact is missing, ambiguous, expired, unavailable, scope-mismatched, or
in conflict, the result is **not authorized**. Administrators cannot turn an
unknown into a grant through a configuration default.

The check occurs before any public output is written. Post-generation row
filtering is prohibited because the same material can survive in:

- RDF or JSON-LD graphs;
- CSV or JSON Lines tables;
- SQLite tables, views, full-text indexes, or search snippets;
- manifests, catalog records, statistics, validation messages, and logs;
- documentation examples or screenshots;
- retrieval or derived-data bundles;
- checksums, filenames, URL slugs, and archive members; or
- version-control history and release caches.

A failing preflight aborts the entire public build. It does not emit a partial
archive. Diagnostic output must identify internal record IDs without repeating
restricted names, descriptions, locations, or protocol rationales.

## Local Contexts integration by reference

[Local Contexts](https://localcontexts.org/labels/about-the-labels/) describes
Traditional Knowledge and Biocultural Labels as community tools for expressing
local conditions for sharing, access, provenance, protocol, and permission.
Only a [Community account can customize and apply
Labels](https://localcontexts.org/support/working-with-labels/), and each Label
has a permanent identifier. OMARO therefore follows these rules:

1. Record the permanent identifier of the customized, community-applied Label
   or Hub project; do not mint an OMARO imitation.
2. Record the issuing community and application provenance only as supplied or
   authorized through the proper Local Contexts workflow.
3. Do not copy or alter Label icons, titles, or text outside the applicable
   display terms. Do not replace a live customized description with the generic
   template.
4. Do not type a Label as `dcterms:license`, an ODRL permission, a generic
   rights statement, an OMARO review outcome, or a use decision.
5. Treat the Label as a protocol resource. Create a separate `UseDecision` for
   the repository's exact publication action when the applicable community
   procedure requires one.
6. Recheck the referenced application and status before release. If the
   resource cannot be resolved or its current application cannot be verified,
   fail closed.
7. Cache only the minimum public metadata necessary for integrity and offline
   audit, and only when that caching is permitted.

Label categories have different force. A provenance Label identifies cultural
authority or interests; a protocol Label communicates access expectations; a
permission Label identifies activities generally approved by the community.
None is safely reduced to one Boolean `open` flag. Uses outside the stated
permission require engagement with the primary cultural authority.

Local Contexts [Notices](https://localcontexts.org/notices/about-the-notices/)
have a different issuer and function. Institutions and researchers use them to
identify Indigenous collections or data, disclose possible rights and
interests, and open a path to engagement; communities may later add Labels.
A Notice is therefore a risk and engagement signal, not community
authorization. OMARO may reference it as source or protocol evidence, but it
must not convert a Notice into a `granted` use decision or treat institutional
application as a community mandate.

[Mukurtu cultural protocols](https://docs.mukurtu.org/communities-cultural-protocols-categories/UnderstandingCommunitiesAndCulturalProtocols/)
provide a useful operational comparison rather than a conformance target.
Mukurtu assigns content to one or more community-managed protocols, including
overlapping protocols from different communities. OMARO likewise preserves
every applicable protocol and fails closed on unresolved overlap; it does not
flatten several protocol memberships into the least restrictive access level.

## Principles and professional standards

### CARE

The [CARE Principles for Indigenous Data
Governance](https://www.gida-global.org/careprinciples) emphasize Collective
Benefit, Authority to Control, Responsibility, and Ethics. They complement,
rather than replace, data-oriented findability and interoperability. For OMARO
this means:

- a technically reusable graph is not necessarily authorized for every reuse;
- communities determine governance protocols for data about their peoples,
  territories, cultural heritage, and knowledge;
- the project must account for benefit, participation, attribution,
  stewardship, and foreseeable downstream harm; and
- the community, not only the repository, evaluates whether a use is
  beneficial and ethically acceptable.

OMARO can record parts of this process but cannot claim CARE implementation
from schema fields alone. Such a claim requires evidence of community
participation, decision power, benefit, and evaluation across the data
lifecycle.

The mapping is deliberately partial. `AuthorityAssignment`,
`ProtocolApplication`, and action-specific `UseDecision` records can document
Authority to Control. Directional evidence, attributed review decisions,
legal-basis and consent assessments, and the fail-closed publication preflight
support Responsibility and Ethics. Collective Benefit, benefit-sharing, and
reciprocity must be demonstrated by community-evaluated deployment evidence,
such as a governed project agreement or benefit-and-risk assessment, and
referenced only where disclosure is authorized. OMARO does not turn that
evidence into a universal `beneficial` outcome or a substitute use decision.

CARE is specifically an Indigenous data-governance framework. It must not be
universalized into a generic rule that erases the sovereignty, law, and
locally designed standards of particular Indigenous Peoples. For non-Indigenous
community-governed material, CARE may prompt useful questions, but the
community's own governance and the applicable ethical and legal frameworks
remain authoritative.

### UNESCO living-heritage ethics

The [UNESCO 2003 Convention](https://ich.unesco.org/en/convention) expressly
includes instruments, objects, artefacts, and cultural spaces associated with
practices, expressions, knowledge, and skills. An organological record can
therefore concern living heritage even when its immediate target is a museum
object. Article 15 calls for the widest possible participation of the
communities, groups, and individuals who create, maintain, and transmit that
heritage.

UNESCO's [Ethical Principles for Safeguarding Intangible Cultural
Heritage](https://ich.unesco.org/en/ethics-and-ich-00866) add practical
requirements that are directly relevant to OMARO: communities have the primary
role in safeguarding; engagement depends on free, prior, sustained, and
informed consent; customary access restrictions must be respected; heritage
must not be subjected to external judgments of value; communities should
assess threats such as decontextualization, commodification, and
misrepresentation; and the dynamic character of living heritage must remain
visible.

Consequently, a community category is not merely another value in a static
taxonomy. Its meaning, authorized labels, holders, protocol, and scope may
change, and the community may determine that classification, translation,
comparison, or public indexing itself creates harm. Versioning and withdrawal
mechanisms support that governance but do not replace sustained participation.
OMARO does not claim compliance with the Convention or its Operational
Directives; institutional and State Party obligations remain outside the
ontology.

### ICOM

The [ICOM Code of Ethics for
Museums](https://icom.museum/en/resources/standards-guidelines/code-of-ethics/),
including the revised Code adopted in 2026, is the professional baseline for
museum stewardship, due diligence, provenance, community relationships,
confidential or sensitive information, restitution, and responsible access.
OMARO's source preservation does not displace an institution's ethical and
legal obligations. A museum must not use a technically valid OMARO export to
bypass its own collections, source-community, access, or return procedures.

### WIPO

[WIPO's guidance on documenting traditional knowledge and traditional cultural
expressions](https://www.wipo.int/en/web/traditional-knowledge/resources/tk-and-tces)
warns that documentation and display can increase vulnerability to
misappropriation and misuse and calls for clear objectives plus assessment of
risks and benefits. Before OMARO records or enriches culturally sensitive
organological material, the responsible project must assess at least:

- who asked for and benefits from documentation;
- whether non-documentation or a non-public record is preferable;
- whether classification, translation, geolocation, or linking makes sensitive
  knowledge easier to discover;
- whether copyright law leaves gaps in customary or collective interests;
- whether a persistent identifier or released archive would frustrate later
  withdrawal; and
- which customary law, national law, contracts, institutional policies, or
  community protocols also apply.

Legal public-domain status is not an ethical clearance.

### IEEE 2890-2025

[IEEE 2890-2025](https://standards.ieee.org/ieee/2890/10318/) is an active
recommended practice for provenance of Indigenous Peoples' data. It establishes
parameters intended to make Indigenous relationships to data visible and to
support governance, decision-making, participation, collaboration, and future
use. OMARO's represented-community, authority, protocol, source, scope, and use
decision fields follow that provenance direction.

The repository does not claim IEEE 2890 conformance unless a separate,
versioned conformance assessment demonstrates every required parameter. An
OMARO URI that names a community is not by itself adequate provenance.

## Inherited-source risk screening

An upstream source can be public, institutionally trusted, and openly licensed
while still carrying cultural, privacy, provenance, or safety risks. A source's
licence covers only the rights it can grant. It does not establish community
authorization, representative legitimacy, ethical suitability, factual
accuracy, or consent by named or recorded people.

Every new or refreshed source requires a documented screening before canonical
ingestion. The screen should ask whether the source contains or may reveal:

- sacred, secret, ceremonial, gender-restricted, age-restricted, seasonal, or
  initiatory knowledge;
- recordings, photographs, names, biographies, interviews, or performances of
  identifiable people;
- precise locations of culturally sensitive objects, sites, communities, or
  custodians;
- funerary, ancestral, looted, coerced, missionary, military, or otherwise
  contested collection contexts;
- culturally restricted maker, owner, performer, clan, lineage, or ceremonial
  role information;
- community terms presented without provenance or as universal synonyms;
- historical descriptions containing derogatory, imposed, or extractive
  terminology;
- upstream Local Contexts Notices or Labels, access flags, takedown requests,
  or institution-specific restrictions;
- unresolved restitution, repatriation, ownership, or custody claims; or
- links whose surrounding page discloses more than the imported field.

The outcome is recorded as a review signal, not as proof that no risk exists.
High-risk or unresolved material is quarantined from the public repository
until the appropriate people and institutions decide what may be recorded and
used. A `source-faithful` graph is not automatically a public graph.

Source lineage must retain the upstream record and version, retrieval time,
applicable terms, transformations, identified protocol or notice, target
resource, and screening decision. Corrections should create new occurrences or
superseding records rather than silently rewriting the historical source
witness.

## Private and restricted data rules

The public repository, release archive, issue tracker, test fixtures, logs, and
commit history must never contain restricted governance evidence or personal
data merely because a schema has a field for it. In particular, do not commit:

- private contact details, identity documents, signatures, or direct account
  identifiers;
- full consent forms, meeting minutes, ballots, council deliberations, quorum
  evidence, or confidential mandate documents;
- private Local Contexts Hub material or non-public community protocol text;
- restricted cultural names, narratives, descriptions, translations, or
  locations;
- unpublished images, audio, video, transcripts, or technical measurements
  whose release could disclose restricted knowledge;
- security credentials, access URLs, encryption keys, or repository tokens;
  or
- a refusal or withdrawal rationale when the rationale itself is sensitive.

Restricted evidence belongs in a separately administered system with access
control, encryption, minimal collection, retention and deletion rules, audit
logging, incident response, and named institutional responsibility. The public
OMARO record may expose only an opaque evidence or authorization identifier,
status, date, and safe summary, and only if disclosure of those facts is itself
authorized.

Pseudonymization is not assumed to be anonymization. Instrument descriptions,
place, community, role, date, and media can re-identify a person or disclose a
restricted event when combined. Data minimization must be evaluated over the
whole release, not field by field.

Public version control is effectively irreversible because clones and archives
can persist after deletion. A withdrawal workflow can stop future official
distribution and preserve a restricted audit trail, but it cannot promise to
recall every prior copy. This limitation must be explained before contribution
and considered when choosing whether to publish at all.

## Synthetic organological examples

The following examples are deliberately synthetic. They demonstrate decision
separation and must not be presented as statements about a real community.

### Community category and Hornbostel–Sachs

A community-governed scheme classifies a particular drum by ceremonial role,
lineage, and relationship to a named place. An organologist also assigns a
Hornbostel–Sachs membranophone class based on observed construction.

- The two concepts remain in independent schemes.
- The observations may support the Hornbostel–Sachs assignment but do not
  establish the community category.
- An authorized community review can accept the community claim in its stated
  scope without declaring Hornbostel–Sachs false.
- A mapping between the concepts requires its own evidence, purpose, scope,
  authority, and review; no `owl:sameAs` or automatic `skos:exactMatch` is
  emitted.
- Permission to display the community term is a separate use decision.

### Ceremonial rattle recording

A museum holds a recording of a rattle in a restricted ceremony. A researcher
can verify the instrument's excitation mechanism and the catalogue can retain
a private observation. That scholarly result does not authorize streaming the
audio, publishing a transcript, indexing the ceremonial name, or disclosing
the place and date.

If the protocol application requires a community decision and no matching
`granted` use decision covers public streaming, the build fails before any
audio URL, waveform metadata, search token, or explanatory text is exported.
The public record may contain only the safe fact that access is restricted if
that statement is itself approved.

### Maker interview

An authorized community body approves a terminology project and identifies an
appropriate instrument name. A maker participates in an interview and
pronounces the term.

- Collective authorization can govern the terminology project.
- The maker's individual consent is still required for recording, quotation,
  voice publication, transcription, translation, and future derived uses.
- Copyright or performer rights in the recording remain separate.
- A use decision for displaying the term does not authorize publishing the
  audio.
- Withdrawal of audio permission need not erase the separately authorized
  classification claim, but future public builds must omit the audio and every
  derivative that is no longer covered.

### Public legacy catalogue with a restricted name

An openly licensed historic catalogue includes a culturally restricted name
and an imposed colonial instrument category. OMARO may preserve the source's
existence in a restricted audit record. The licence does not compel
republication of the name, and source fidelity does not require presenting the
category as an endorsed fact.

Risk screening triggers engagement with the relevant authority. A public
projection may, if authorized, expose a corrected name, contextual warning,
and qualified historical source claim while withholding the restricted form.
If the allowed public description cannot be determined without exposing the
restricted content, no record is published.

### Internal plurality

Two authorized bodies or subgroups reach different decisions for different
ceremonial roles, territories, or audiences. OMARO records separate mandates,
perspectives, scopes, and use decisions. It does not calculate a majority
result, manufacture a single “community view,” or let one mandate silently
override another outside its coverage. A public action must satisfy every
applicable decision; unresolved overlap fails closed.

## Release and audit checklist

Before a public release containing community-governed material, the release
manager must be able to answer **yes** to every applicable question:

1. Are the represented community and authorized decision process identified
   through evidence the community permits us to retain?
2. Does each authority assignment cover relevant target or protocol subject
   matter, scope, exact action, deciding agent, and decision time?
3. Does each grant contain every requested target and scope and every
   applicable protocol, without combining partial grants?
4. Are collective authorization and all required individual-consent
   determinations current, attributed, and referenced for the exact actions,
   purposes, and audiences, including an explicit `not-required` finding where
   applicable?
5. Is the legal-basis determination independently referenced, attributed, and
   compatible with those actions?
6. Are Local Contexts and other protocols referenced from authoritative,
   current applications without copying or altering governed content, and has
   each application passed its declared integrity method?
7. Are refusals, withheld decisions, withdrawals, supersessions, expiry, and
   conflicts handled as denials?
8. Has inherited-source risk been screened across content, links, metadata,
   indexes, statistics, and combinations of fields?
9. Does the preflight run before all generators and fail without partial
   output?
10. Is the public governance metadata minimal, sanitized, and authorized for
   publication?
11. Are restricted evidence and personal data absent from source control,
    artifacts, logs, tests, and caches?
12. Can the release be rebuilt deterministically with the same authorization
    decisions and audit identifiers?
13. Has the participating community evaluated the proposed public result and
    its expected benefit?

A “no,” unknown, or unresolved answer blocks publication of the affected
material. Technical deadlines, source openness, or prior publication elsewhere
do not override this gate.
