# Contributing

Contributions to classifications, labels, mappings, documentation, and tooling
are welcome. Data changes require stronger evidence than code-only changes.

## Development

Python 3.11 or newer is supported. Release verification uses the version in
`.python-version` (currently Python 3.13.13) and the complete lock file.

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
.venv/bin/pip install --no-deps -e .
.venv/bin/omaro validate
.venv/bin/omaro build
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

Do not edit generated files independently. Update canonical records or the
builder, then regenerate every format with `omaro build`.
Normal validation, build, test, and package commands are offline.
`refresh-source` is the only networked command and is an intentional,
transactional source-synchronization operation.

## Data corrections

Open a data-correction issue containing the stable concept, assertion, or label
profile URI; affected field; current and proposed value; language tag and
context where relevant; and a verifiable source. State whether the change
reflects MIMO upstream data, a local normalization, a reviewed contextual
annotation, or an unresolved scholarly disagreement. Never infer language,
dialect, translation status, community preference, or cultural validity from
Unicode Script observations. See `CORRECTIONS.md`.

## Ontology and interoperability proposals

A proposal for a class, property, controlled code, inference pattern, or
external bridge must include enough evidence to review both its organological
meaning and its operational cost:

1. state the concrete user, organological question, and query or exchange that
   the change enables;
2. cite public domain sources and identify whose perspective or authority they
   represent;
3. document reuse candidates and explain why a new OMARO term or bridge is
   needed instead of an existing stable URI;
4. add or update a competency question and both a positive and a boundary or
   negative example;
5. distinguish concept, object, component, configuration, condition,
   performance, sounding, proposition, activity, and decision identities;
6. implement corresponding JSON Schema, SHACL/RDF, tabular/export, and
   projection tests where the proposal affects those interfaces;
7. state migration, semantic-versioning, deprecation, W3ID, and downstream
   compatibility consequences; and
8. document evidence, scope, perspective, review, rights, community authority,
   protocol, and publication effects rather than relying on a default.

Analytical outputs such as clusters or similarities additionally identify the
versioned source dataset, selected variables, preprocessing, procedure, and
algorithm. A different variable set or method creates a distinct assignment;
it does not silently revise an earlier conclusion. Repeated use of the
`other` criterion type should trigger a term proposal under this process.

The reporting and adoption rationale is maintained in `RELATED_WORK.md` and
`ORGANOLOGICAL_FOUNDATIONS.md`. A proposal is not accepted solely because it
increases coverage or class count.

## Pull-request requirements

- Keep unrelated changes separate.
- Add tests for changed behavior and validation rules.
- Include the generated quality-report difference for data updates.
- Do not add inferred identifiers, ORCIDs, translations, or classifications
  without evidence.
- For release-affecting changes, confirm that `validate`, `build`, `pytest`,
  Ruff, `package`, `shasum -a 256 -c SHA256SUMS`, and
  `python scripts/release_check.py` pass.

By participating, contributors agree to follow `CODE_OF_CONDUCT.md`.
