# W3ID registration and verification

## Status

The OMARO identifiers are active following the merge of
[pull request 6739](https://github.com/perma-id/w3id.org/pull/6739) on
23 September 2026. HTML, Turtle, JSON-LD, RDF/XML and schema targets were
verified after the merge. W3ID provides persistent HTTP
identifiers; registration is not W3C standardization or endorsement.

The files in `w3id/modavis/omaro/` mirror the directory that must be added at
`ids/modavis/omaro/` in the upstream W3ID repository. They are maintained here so
resolver behavior can be reviewed and tested with the ontology release.

## Resolution contract

| Requested identifier | HTML target | RDF target |
|---|---|---|
| `https://w3id.org/modavis/omaro` | versioned ontology documentation | compact versioned OMARO vocabulary |
| `.../ontology` | redirects to `.../ontology/0.1.0` | same |
| `.../ontology/0.1.0` | immutable ontology documentation | immutable compact Turtle, JSON-LD, or RDF/XML vocabulary |
| `.../ontology/2.2.0` | historical compatibility documentation | original preserved 2.2.0 RDF files |
| `.../dataset` | current representation of the maintained dataset | same |
| `.../dataset/0.1.0` | immutable dataset landing page | combined RDF representation containing the dataset resource |
| `.../schema/<file>` | published JSON Schema or SHACL file | file media type |

The fragment in an OMARO term IRI, such as `#Perspective`, is resolved by the
namespace document because URI fragments are not sent in an HTTP request.

The stable dataset IRI identifies the maintained dataset across releases; it
is not merely an alias for the version resource. Metadata relates it to the
current immutable version with DCAT lifecycle properties, while content
negotiation may serve the current representation. Every version IRI continues
to identify exactly one immutable snapshot. The version DOI is an identifier
and landing page for the versioned dataset, not another dataset identity.

## Publication order

1. Make `modavis-project/omaro` public when the release is approved.
2. Enable GitHub Pages with `OMARO_ENABLE_PUBLIC_PAGES=true` and confirm the
   ontology, dataset, RDF and schema targets return successfully.
3. Copy `w3id/modavis/omaro/.htaccess` and `README.md` into
   `ids/modavis/omaro/` in a fork of `perma-id/w3id.org`.
4. A draft W3ID pull request may be opened before publication. Mark it ready
   for review only after the public targets and content negotiation pass.
5. After merge, run the checks below against `w3id.org` and record the result in
   the release approval evidence.
6. Only then publish metadata that describes the W3ID resolver as active.

## Verification commands

Run these without `-L` first to inspect the redirect status and `Location`, and
then with `-L` to inspect the final representation:

```bash
curl -sSI -H 'Accept: text/html' \
  https://w3id.org/modavis/omaro/ontology/0.1.0
curl -sSI -H 'Accept: text/turtle' \
  https://w3id.org/modavis/omaro/ontology/0.1.0
curl -sSI -H 'Accept: application/ld+json' \
  https://w3id.org/modavis/omaro/ontology/0.1.0
curl -sSI -H 'Accept: application/rdf+xml' \
  https://w3id.org/modavis/omaro/ontology/0.1.0
curl -sSIL https://w3id.org/modavis/omaro/schema/perspective.schema.json
curl -sSIL https://w3id.org/modavis/omaro/schema/organological_target.schema.json
curl -sSIL https://w3id.org/modavis/omaro/schema/observation_assessment.schema.json
curl -sSIL https://w3id.org/modavis/omaro/schema/classification_criterion.schema.json
curl -sSIL https://w3id.org/modavis/omaro/schema/classification_expression.schema.json
curl -sSIL https://w3id.org/modavis/omaro/schema/protocol_application.schema.json
curl -sSIL https://w3id.org/modavis/omaro/schema/use_decision.schema.json
curl -sSIL https://w3id.org/modavis/omaro/dataset/0.1.0
```

Download the three ontology serializations and parse them as RDF. Their graphs
must be isomorphic, each must declare the base ontology IRI with
`owl:versionIRI` pointing to `0.1.0`, and the versioned publication files must
match the checksums in `dist/manifest.json`.

## Persistence obligations

- Never reuse a published version IRI for different semantics.
- Retain every versioned Pages target after later releases.
- Change only the unversioned redirects when advancing the current compatible
  version.
- Keep the stable dataset resource and every immutable version resource
  distinct in DCAT, RDF, catalogue, citation, and landing-page metadata.
- Keep at least two maintainers or an organizational recovery route for the
  target repository and Pages deployment.
- Test resolver behavior in continuous integration after registration.
- If the hosting platform changes, update W3ID targets without changing OMARO
  identifiers or version semantics.

The release checklist treats repository publication, Pages deployment, W3ID merge,
and post-merge verification as external publication gates. None is silently
assumed by a local build.
