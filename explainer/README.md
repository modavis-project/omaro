# OMARO Field Guide

A separate static web application for learning what OMARO can express, how to
use it, and how its current source evidence differs from its capabilities.
It lives alongside the existing ontology explorer in `site/`; it does not
replace that explorer or change the ontology build, canonical data, release
inventory, or active Pages workflow.

## Run locally

Use the repository's installed OMARO Python environment and Node.js 22 or
newer. This app has no npm dependencies and needs no `npm install`.

From the repository root:

```bash
cd explainer
npm run build
npm run dev
```

Open the Local URL printed by the server. The default is
[http://127.0.0.1:4173/](http://127.0.0.1:4173/). Rebuild and reload after editing;
the server serves the built files. Stop it with Ctrl+C. To use an interpreter
outside the repository's existing `.venv`, set `OMARO_PYTHON` to that executable.
Do not replace an existing Python environment to run this app.

The Python-only build alternative, from the repository root, is:

```bash
.venv/bin/python explainer/scripts/build.py
```

The output is **`explainer/dist/`**. It is independent of the repository's root
`dist/`, generated, and ignored. Serve it over HTTP; opening `index.html` with
`file://` does not reliably support JavaScript modules or data fetching.

## The learning experience

The visual direction combines a dark green reading surface, lime accents,
large serif headings and a source-record sheet. The central visual is the
knowledge structure itself; no instrument illustration is passed off as a
source object.

1. **Recognize the idea.** A familiar double-bass concept introduces three real
   source classifications. Visitors reveal claims, context, and evidence in
   place, without learning ontology vocabulary first.
2. **Choose a question.** Six paths address cataloguing, research comparison,
   review, integration, research answers, and community-governed contributions.
   Each gives an example, a limitation and a concrete next step. Process steps
   and model terms remain optional disclosures.
3. **Try the consequence.** A synthetic comparison changes between
   construction and performed-sounding profiles. An optional missing-assessment
   control demonstrates why unresolved evidence cannot silently become zero.
4. **Inspect the details.** Expandable sections expose the actual canonical
   claim, Python-generated endorsement explanation, all seven scope modes,
   five assessment states, identity boundaries, mapping purposes, governance,
   executable query recipes, standards and scholarly references.

Essential qualifications stay visible: examples are labelled real or synthetic,
source silence remains unknown, similarity is not identity, the dataset lacks
community contributions/reviews, and the release is an unpublished candidate.
Progressive disclosure hides optional complexity, not limitations necessary to
interpret a result. This follows the prioritization principle described by
[Nielsen (2006), Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/).

## Source and semantic fidelity

Every build uses `query_classifications` from `src/omaro/query.py`. That entry
point checks publication authorization **before** canonical validation,
lookup, counts or output. The app builder writes nothing until the checked
result and its curated teaching assumptions pass. It retains an earlier output
if preflight fails; a failed build must never be treated as a freshly approved
artifact. Build failures return a nonzero exit status.

The app copies the real double-bass claim envelopes verbatim, together with the
endorsement explanations returned by the canonical Python evaluator. The
browser does **not** implement an alternative review-policy evaluator. It
preserves the claim's `uri` as the assertion identity and `assignment_uri` as
the separate activity identity. Source metadata, scopes, perspectives and
snapshot versions remain available in `data.json`.

The comparison is the existing synthetic
`examples/multidimensional-analysis/scalogram.json`. JavaScript recalculates its
declared unweighted normalized Hamming distance. `detected` and `not-detected`
are binary outcomes only under that fixture's method; the other statuses are
unresolved. Temporary user overrides affect only the current page, not the
downloaded fixture or canonical records. No class assignment or endorsement is
derived from distance.

Short classification descriptions in `src/content.js` are explanatory wording;
original class definitions and identifiers remain in the downloadable payload.
Local Markdown references and query files are copied verbatim. They are source
documents for download, not a standalone mirror of every repository file they
may reference. The full source checkout supplies those further dependencies.
The bundled NOTICE, PROVENANCE and LICENSE preserve source attribution.

The builder rejects changes that would invalidate the current teaching story,
including changed notations, scopes, endorsement outcomes, review state,
interface versions or comparison shape. Review the copy and update the teaching
contract intentionally when the source evolves. The fixed unpublished status
must also be reviewed before any future public release of the ontology.

## GitHub Pages compatibility

The output consists of HTML, CSS, JavaScript, JSON and local reference files.
It needs no server application, database, account, runtime Python, API key,
CDN, external font, network data source, or build service at visit time. External
links are citations only. There are no analytics, cookies or persisted visitor
preferences.

All assets, module imports, data requests and downloads use relative paths.
In-page navigation uses fragments, so there is no history-router fallback or
rewrite requirement. The output includes `.nojekyll`.

To publish later, the **contents** of `explainer/dist/` can be the publishing
root of a separate Pages repository, or a subdirectory of a deliberately
assembled Pages artifact. GitHub documents these approaches in
[Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
and [Bypassing Jekyll](https://github.blog/news-insights/bypassing-jekyll-on-github-pages/).

[`deploy/github-pages.yml.example`](deploy/github-pages.yml.example) is an
inactive, manual-only workflow example. It builds from a checkout containing
the ontology sources, then uploads only `explainer/dist/`. It is deliberately
outside `.github/workflows/` and has not been enabled or run. The repository
already has a Pages workflow for the ontology distribution; enabling another
root deployment there would replace that site's content. Choose a separate
Pages destination or intentionally combine the artifacts before activating a
workflow. No repository or hosting settings have been changed.

To exercise a nested hosting prefix locally:

```bash
OMARO_BASE_PATH=/a-project/field-guide/ PORT=4174 npm run dev
```

## Verification

From `explainer/`, after building:

```bash
npm run check
npm test
../.venv/bin/pytest -q tests/test_build.py
../.venv/bin/ruff check scripts tests
../.venv/bin/ruff format --check scripts tests
```

The Node tests recalculate the published example, test missing/negative
evidence boundaries and identity presentation, compare claim bytes with the
canonical source, check every local HTML link and fragment, verify exact output
inventory and hashes, and make real HTTP requests at both root and nested paths.
The Python tests check teaching-data drift and verify that a denied query
produces no new output or partial payload.

Accessibility is addressed in source with semantic landmarks and headings, a
skip link, native disclosures/radios/checkboxes/selects, labelled controls,
pressed states, focus outlines, screen-reader status messages, reduced-motion
support, responsive layouts, and readable noninteractive fallback content.
Copying has a manual-selection fallback. Failed data loads expose a retry and
leave the conceptual guide readable. These measures do not constitute a WCAG
conformance certification or a completed visitor usability study.

There is no browser screenshot or interaction-test claim. The test suite covers
the application logic and static-hosting contracts; browser visual and assistive
technology evaluation can be performed separately. The ontology's prior
158-case verification remains historical; this app's checks are separate.

## Files

| Area | Responsibility |
|---|---|
| `src/index.html`, `src/styles.css` | Semantic teaching content, disclosures and responsive visual design |
| `src/content.js` | Six use-case paths and explanatory labels |
| `src/model.js` | Pure comparison, safe text escaping and record-field presentation |
| `src/app.js` | Progressive disclosure and interactive page state |
| `scripts/build.py` | Publication-checked data export, reference copies and deterministic manifest |
| `scripts/build.mjs` | Select the installed Python interpreter |
| `scripts/serve.mjs` | Loopback-only static preview with optional hosting prefix |
| `tests/` | Semantic, export and static-hosting boundary checks |
| `deploy/` | Inactive hosting example |

The separate application is not added to the ontology/dataset archive or expert
packet inventories. Preserve that separation unless their scope is explicitly
changed. The repository's CC0 dedication applies; see the root LICENSE and NOTICE.
