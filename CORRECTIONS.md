# Data correction policy

Every correction is classified as one of:

1. **Upstream synchronization:** MIMO changed the source concept.
2. **Mechanical correction:** serialization, language-tag, or transformation bug.
3. **Local annotation:** a transparent repository assertion not present in MIMO.
4. **Disputed assertion:** credible sources disagree; no silent replacement.

The correction record must contain the concept URI, affected release, old and new
values, language, evidence URL or bibliographic citation, category, reviewer, and
decision date. Upstream values retain MIMO provenance. Local assertions must use
a repository namespace and must never masquerade as MIMO statements.

For classification changes, the preserved MIMO relation and the repository
classification assertion are separate records. A review may accept, dispute,
reject, or supersede the repository assertion without deleting or rewriting the
source relation. A mechanical source correction must retain evidence of the old
source tuple in the correction record.

Labels and source definitions follow the same separation. Their compatibility
literals remain source-preserving values, while `label_assertions.jsonl` and
`note_assertions.jsonl` carry stable identity, agent, versioned source, and
review status. A status change must update both the status code and its registry
URI. Evidence, reviewer identity, decision date, perspective, and contextual
scope remain required correction-review material; they are not inferred from a
status value alone.

Automated quality findings never constitute corrections or reviews. They retain
`review_effect: none`; script and language signals may describe valid
transliterations, loanwords, exonyms, or historical forms.

Language-tag canonicalization is a mechanical, registry-backed transformation.
Both submitted and canonical tags, the dated registry URI, status, and any
project override must remain recorded. Canonicalizing a tag does not validate
the associated lexical form or its cultural applicability.

Linguistic profiles are separate, source-derived records. Changes to language
variety, writing system, transliteration or transcription system,
pronunciation, audio, term roles, translation status, contextual applicability,
display policy, or search policy require evidence, reviewer authority, and a
retained review event. Character-script observations may be regenerated only
from the pinned Unicode registry and literal form; they must never be used to
infer those reviewed fields. Community identifiers or Local Contexts labels
may be applied only through the relevant community's authorized process.

Accepted corrections update canonical data, fixtures, quality report, changelog,
and all derived formats. Published Zenodo files are never replaced silently; a
new dataset version is issued for substantive corrections.
