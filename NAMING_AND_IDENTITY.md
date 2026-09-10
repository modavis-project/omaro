# OMARO naming and identity policy

## Canonical name

**OMARO** is the project and system name. It expands to **Ontology for
Multiperspectivity, Assertions, and Review in Organology**. Use the expansion
on first mention in scholarly prose and use OMARO thereafter.

The name identifies a family of coordinated deliverables rather than one
undifferentiated file:

| Deliverable | Canonical name | Current version |
|---|---|---:|
| Semantic model | OMARO Ontology | `0.1.0` |
| MIMO-derived data release | OMARO Reference Dataset | `0.1.0` |
| Validator, builders, and command-line interface | OMARO tooling | `0.1.0` |

The ontology, dataset and tooling begin their public release series at 0.1.0.
They remain distinct deliverables and may evolve independently. The ontology
defines the model; the reference dataset applies it to preserved source data.

## Canonical identifiers

| Purpose | Identifier |
|---|---|
| Preferred prefix | `omaro` |
| Term namespace | `https://w3id.org/modavis/omaro#` |
| Ontology IRI | `https://w3id.org/modavis/omaro/ontology` |
| Version IRI | `https://w3id.org/modavis/omaro/ontology/0.1.0` |
| Dataset series | `https://w3id.org/modavis/omaro/dataset` |
| Dataset version | `https://w3id.org/modavis/omaro/dataset/0.1.0` |
| Repository | `https://github.com/modavis-project/omaro` |
| Python distribution and import package | `omaro` |
| Command-line program | `omaro` |
| Release archive | `omaro-v0.1.0.zip` |

The W3ID namespace becomes operational only after the resolver configuration
in `w3id/modavis/omaro/` is accepted by the W3ID service and the publication
targets are live. Until then these are canonical intended identifiers, not a
claim that resolution has already been activated.

## Identity boundaries

OMARO owns the assertion, assignment, target, observation, criterion, compound
expression, perspective, applicability, authority, review, cultural-protocol,
use-decision, projection-policy, evidence, and linguistic-profile terms in its
namespace.
It does not re-identify MIMO concepts. Hornbostel–Sachs class and instrument
concept identifiers therefore remain in their MIMO namespaces, and OMARO
records qualified statements about them.

The following are deliberately distinct:

- an instrument or classification concept supplied by MIMO;
- an OMARO assertion entity concerning that concept;
- the assignment activity that generated that assertion;
- a review event and the distinct decision entity it generated;
- the OMARO Ontology that defines the assertion model;
- the OMARO Reference Dataset that contains one source snapshot; and
- a view produced by an OMARO projection policy.

Equal labels, the same target/class pair, or inclusion in the same archive do
not collapse these identities.

## Versioning and persistence

The unversioned ontology IRI may redirect to the current compatible ontology
release. A version IRI is immutable: after publication, its representations
must never be replaced by semantically different content. Dataset-version
IRIs are also immutable. New releases receive new version IRIs and retain old
publication targets.

Term IRIs use the hash namespace. A browser does not transmit the fragment
after `#`; content negotiation therefore occurs on the namespace document as a
whole. Individual terms remain addressable as fragments within its HTML or RDF
representation.

OMARO was renamed before publication. No compatibility aliases for earlier
development-only package names or namespaces are provided. Introducing such
aliases would unnecessarily turn unpublished identifiers into a permanent
maintenance commitment.

## Recommended references

In prose:

> OMARO (Ontology for Multiperspectivity, Assertions, and Review in
> Organology), ontology version 0.1.0.

When citing the empirical snapshot, cite the **OMARO Reference Dataset,
version 0.1.0** and its version DOI after publication. When documenting a data
model or integration, cite the ontology version IRI. Applications should store
both the assertion URI and the ontology or dataset version used to interpret
it.
