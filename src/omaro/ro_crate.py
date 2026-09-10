"""Deterministic RO-Crate metadata for an OMARO release directory."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any


RO_CRATE_CONTEXT = "https://w3id.org/ro/crate/1.3/context"
RO_CRATE_PROFILE = "https://w3id.org/ro/crate/1.3"
RO_CRATE_METADATA_NAME = "ro-crate-metadata.json"

DEFAULT_DESCRIPTION = (
    "OMARO provides an OWL ontology, validation model, release tooling, and a "
    "versioned MIMO-derived reference dataset for contextualized, evidenced, "
    "reviewable, and culturally governed organological assertions."
)
CULTURAL_AUTHORIZATION_NOTICE = (
    "The CC0 licence and file-integrity metadata describe legal reuse and "
    "bit-level fixity only. They do not establish cultural authorization, "
    "community consent, or permission to publish culturally restricted "
    "knowledge; consult CULTURAL_GOVERNANCE.md and record-level use decisions."
)

_DEFAULT_CREATOR_IDENTIFIERS = {
    "Dominik Ukolov": "https://orcid.org/0000-0002-7904-3892",
}
_SOURCE_NAMES = {
    "https://vocabulary.mimo-international.com/rest/v1/HornbostelAndSachs": (
        "MIMO Hornbostel–Sachs vocabulary source"
    ),
    "https://vocabulary.mimo-international.com/rest/v1/InstrumentsKeywords": (
        "MIMO musical-instrument names vocabulary source"
    ),
}
_ENCODING_FORMATS = {
    ".cff": "application/yaml",
    ".csv": "text/csv",
    ".html": "text/html",
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".md": "text/markdown",
    ".rdf": "application/rdf+xml",
    ".sqlite": "application/vnd.sqlite3",
    ".ttl": "text/turtle",
    ".txt": "text/plain",
    ".yaml": "application/yaml",
    ".yml": "application/yaml",
}


@dataclass(frozen=True, slots=True)
class CratePath:
    """A deliberately selected local release entity.

    Directory identifiers end in ``/`` and are represented as RO-Crate
    ``Dataset`` entities. Other identifiers represent files. ``parent`` is the
    identifier of a represented directory or ``./`` for the crate root.
    """

    path: str
    parent: str
    name: str
    description: str

    @property
    def is_directory(self) -> bool:
        return self.path.endswith("/")


DEFAULT_PATH_SPECS: tuple[CratePath, ...] = (
    CratePath(
        "dist/",
        "./",
        "Generated OMARO distribution",
        "Generated machine-readable data, ontology serializations, validation "
        "assets, reports, and access formats.",
    ),
    CratePath(
        "examples/",
        "./",
        "OMARO examples",
        "Worked examples distributed with the release.",
    ),
    CratePath(
        "examples/organological-assessment/",
        "examples/",
        "Organological assessment examples",
        "Synthetic, non-empirical examples of assessments, classification "
        "assertions, compound expressions, governance, and review inputs.",
    ),
    CratePath(
        "examples/multidimensional-analysis/",
        "examples/",
        "Multidimensional analysis example",
        "A synthetic, reproducible scalogram showing how the declared criterion "
        "set changes analytical proximity without establishing identity.",
    ),
    CratePath(
        "README.md",
        "./",
        "Release overview",
        "Entry point for installing, validating, building, and reusing OMARO.",
    ),
    CratePath(
        "LICENSE",
        "./",
        "Licence text",
        "CC0 legal text for the release; legal licensing does not establish "
        "cultural authorization or community consent.",
    ),
    CratePath(
        "CITATION.cff",
        "./",
        "Citation metadata",
        "Versioned citation metadata for the dataset and ontology release.",
    ),
    CratePath(
        "VERSION",
        "./",
        "Release version",
        "The OMARO dataset and software release version.",
    ),
    CratePath(
        "CHANGELOG.md",
        "./",
        "Changelog",
        "User-visible changes across OMARO releases.",
    ),
    CratePath(
        "RELEASE_NOTES.md",
        "./",
        "Release notes",
        "Scope, limitations, and verification information for this release.",
    ),
    CratePath(
        "DATA_DICTIONARY.md",
        "./",
        "Data dictionary",
        "Field-level definitions for OMARO canonical and exchange records.",
    ),
    CratePath(
        "ONTOLOGY_REFERENCE.md",
        "./",
        "Ontology reference",
        "Classes, properties, constraints, and modeling patterns in OMARO.",
    ),
    CratePath(
        "MULTIPERSPECTIVITY.md",
        "./",
        "Multiperspectivity guide",
        "Conceptual and practical guidance for retaining multiple organological "
        "perspectives without forced consensus.",
    ),
    CratePath(
        "INFERENCE_AND_VALIDATION.md",
        "./",
        "Inference and validation",
        "Theoretical basis, identity and entailment boundaries, review veto semantics, and executable acceptance evidence.",
    ),
    CratePath(
        "USE_CASES.md",
        "./",
        "Use cases and executable queries",
        "Offline classification lookup, contextual evaluation, explanation, SQL and SPARQL recipes, and governed reuse workflows.",
    ),
    CratePath(
        "ORGANOLOGICAL_FOUNDATIONS.md",
        "./",
        "Organological foundations",
        "Organological literature, methodological boundaries, and design "
        "consequences for OMARO.",
    ),
    CratePath(
        "ORGANOLOGICAL_MODEL.md",
        "./",
        "Organological model",
        "Operational modeling guidance for targets, criteria, assessments, "
        "expressions, assertions, and decisions.",
    ),
    CratePath(
        "CULTURAL_GOVERNANCE.md",
        "./",
        "Cultural governance guide",
        "Fail-closed publication controls, authority assignments, protocols, "
        "use decisions, and limits of legal licensing.",
    ),
    CratePath(
        "INTEROPERABILITY_PROFILES.md",
        "./",
        "Interoperability profiles",
        "Normative and informative crosswalks to related cultural-heritage and "
        "research-data standards.",
    ),
    CratePath(
        "RELATED_WORK.md",
        "./",
        "Related work",
        "Standards, ontologies, organological methods, and governance frameworks "
        "that informed OMARO.",
    ),
    CratePath(
        "COMPETENCY_QUESTIONS.md",
        "./",
        "Competency questions",
        "Queries and expected entailments used to evaluate the ontology model.",
    ),
    CratePath(
        "PROVENANCE.md",
        "./",
        "Provenance statement",
        "Source lineage, transformation boundaries, and reproducibility notes.",
    ),
    CratePath(
        "REVIEW_PROTOCOL.md",
        "./",
        "Review protocol",
        "Human review roles, decisions, evidence expectations, and escalation.",
    ),
    CratePath(
        "GOVERNANCE.md",
        "./",
        "Project governance",
        "Maintenance roles, change control, releases, and deprecation policy.",
    ),
    CratePath(
        "dist/manifest.json",
        "dist/",
        "Distribution integrity manifest",
        "Build inventory with byte counts and SHA-256 digests for generated "
        "distribution files. Fixity does not establish scholarly or cultural "
        "validity, authorization, or consent.",
    ),
    CratePath(
        "dist/rdf/omaro.ttl",
        "dist/",
        "OMARO RDF distribution",
        "Combined ontology and reference dataset in Turtle.",
    ),
    CratePath(
        "dist/schema/dataset.shacl.ttl",
        "dist/",
        "OMARO SHACL shapes",
        "Graph validation constraints for OMARO records.",
    ),
    CratePath(
        "dist/jsonl/metadata.json",
        "dist/",
        "Canonical dataset metadata",
        "Machine-readable release identity, version, sources, creators, and "
        "record counts.",
    ),
    CratePath(
        "dist/metadata/datacite.json",
        "dist/",
        "DataCite metadata",
        "DataCite-compatible metadata for the versioned dataset release.",
    ),
    CratePath(
        "dist/metadata/dqv.ttl",
        "dist/",
        "Dataset quality measurements",
        "DQV measurements with defined metrics, typed values, denominators, and "
        "build provenance. They do not establish organological or cultural "
        "validity.",
    ),
    CratePath(
        "dist/sqlite/omaro.sqlite",
        "dist/",
        "OMARO SQLite database",
        "Relational access copy of the generated reference dataset.",
    ),
    CratePath(
        "dist/quality-report.json",
        "dist/",
        "Machine-readable quality report",
        "Automated validation and quality findings; findings are review signals, "
        "not cultural or scholarly certification.",
    ),
    CratePath(
        "examples/multidimensional-analysis/README.md",
        "examples/multidimensional-analysis/",
        "Multidimensional example guide",
        "Explanation of the synthetic scalogram, its criterion sets, and its "
        "organological interpretation limits.",
    ),
    CratePath(
        "examples/multidimensional-analysis/scalogram.json",
        "examples/multidimensional-analysis/",
        "Multidimensional scalogram",
        "Machine-readable synthetic comparison of criterion-set-dependent "
        "instrument groupings.",
    ),
    CratePath(
        "examples/organological-assessment/README.md",
        "examples/organological-assessment/",
        "Assessment example guide",
        "Walkthrough of the synthetic organological examples and their limits.",
    ),
    CratePath(
        "examples/organological-assessment/manifest.json",
        "examples/organological-assessment/",
        "Assessment example manifest",
        "Inventory and declarations for the synthetic example bundle; structural "
        "integrity does not establish empirical or cultural authorization.",
    ),
    CratePath(
        "examples/organological-assessment/authority_assignments.jsonl",
        "examples/organological-assessment/",
        "Example authority assignments",
        "Synthetic authority envelopes for the worked examples.",
    ),
    CratePath(
        "examples/organological-assessment/classification_assertions.jsonl",
        "examples/organological-assessment/",
        "Example classification assertions",
        "Synthetic perspective-bearing classification assertions.",
    ),
    CratePath(
        "examples/organological-assessment/classification_criteria.jsonl",
        "examples/organological-assessment/",
        "Example classification criteria",
        "Machine-actionable criteria used in the worked assessments.",
    ),
    CratePath(
        "examples/organological-assessment/classification_expressions.jsonl",
        "examples/organological-assessment/",
        "Example classification expressions",
        "Synthetic compound Hornbostel–Sachs expressions.",
    ),
    CratePath(
        "examples/organological-assessment/concept_relation_assertions.jsonl",
        "examples/organological-assessment/",
        "Example concept-relation assertions",
        "Synthetic qualified mappings with declared operational purposes.",
    ),
    CratePath(
        "examples/organological-assessment/observation_assessments.jsonl",
        "examples/organological-assessment/",
        "Example observation assessments",
        "Synthetic attempted and non-attempted criterion assessments.",
    ),
    CratePath(
        "examples/organological-assessment/organological_targets.jsonl",
        "examples/organological-assessment/",
        "Example organological targets",
        "Synthetic whole, component, configuration, and realization targets.",
    ),
    CratePath(
        "examples/organological-assessment/protocol_applications.jsonl",
        "examples/organological-assessment/",
        "Example protocol applications",
        "Synthetic records documenting the application of a community protocol.",
    ),
    CratePath(
        "examples/organological-assessment/synthetic-community-protocol.json",
        "examples/organological-assessment/",
        "Synthetic community protocol",
        "Fictional, non-authoritative protocol used only to exercise governance "
        "controls.",
    ),
    CratePath(
        "examples/organological-assessment/use_decisions.jsonl",
        "examples/organological-assessment/",
        "Example use decisions",
        "Synthetic permission decisions for the worked governance example.",
    ),
)


def _required_text(metadata: Mapping[str, Any], key: str) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"dataset metadata requires a non-empty {key!r} string")
    return value.strip()


def _http_uri(value: str, label: str) -> str:
    if not value.startswith(("http://", "https://")):
        raise ValueError(f"{label} must be an HTTP(S) URI")
    return value


def _doi_uri(value: str) -> str:
    value = value.strip()
    if value.startswith("https://doi.org/"):
        return value
    if value.startswith("doi:"):
        value = value[4:]
    if not value.startswith("10.") or "/" not in value:
        raise ValueError("dataset metadata DOI is not recognizable")
    return f"https://doi.org/{value}"


def _license_uri(value: str) -> str:
    if value.startswith(("http://", "https://")):
        return value
    if not re.fullmatch(r"[A-Za-z0-9.+-]+", value):
        raise ValueError("dataset metadata license must be an SPDX identifier or URI")
    return f"https://spdx.org/licenses/{value}"


def _fragment_id(prefix: str, value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.decode().lower()).strip("-")
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
    return f"#{prefix}-{slug or 'entity'}-{digest}"


def _creator_and_affiliation_entities(
    metadata: Mapping[str, Any],
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    raw_creators = metadata.get("creators")
    if not isinstance(raw_creators, list) or not raw_creators:
        raise ValueError("dataset metadata requires at least one creator")

    creator_refs: list[dict[str, str]] = []
    entities: list[dict[str, Any]] = []
    affiliation_entities: dict[str, dict[str, Any]] = {}
    seen_creator_ids: set[str] = set()

    for raw_creator in raw_creators:
        if not isinstance(raw_creator, Mapping):
            raise ValueError("each dataset creator must be an object")
        name = raw_creator.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("each dataset creator requires a non-empty name")
        name = name.strip()
        identifier = next(
            (
                raw_creator.get(key)
                for key in ("orcid", "uri", "identifier")
                if isinstance(raw_creator.get(key), str)
                and raw_creator.get(key).strip()
            ),
            _DEFAULT_CREATOR_IDENTIFIERS.get(name, _fragment_id("creator", name)),
        )
        assert isinstance(identifier, str)
        identifier = identifier.strip()
        if re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", identifier):
            identifier = f"https://orcid.org/{identifier}"
        if not identifier.startswith(("#", "http://", "https://")):
            raise ValueError(
                f"creator identifier for {name!r} is not a URI or fragment"
            )
        if identifier in seen_creator_ids:
            raise ValueError(f"duplicate creator identifier: {identifier}")
        seen_creator_ids.add(identifier)

        raw_affiliations = raw_creator.get("affiliations")
        if not isinstance(raw_affiliations, list) or not raw_affiliations:
            raise ValueError(f"creator {name!r} requires at least one affiliation")
        affiliation_refs: list[dict[str, str]] = []
        for raw_affiliation in raw_affiliations:
            if isinstance(raw_affiliation, str):
                affiliation_name = raw_affiliation.strip()
                affiliation_id = _fragment_id("affiliation", affiliation_name)
            elif isinstance(raw_affiliation, Mapping):
                affiliation_name_value = raw_affiliation.get("name")
                if not isinstance(affiliation_name_value, str):
                    raise ValueError("affiliation objects require a name")
                affiliation_name = affiliation_name_value.strip()
                id_value = raw_affiliation.get("uri") or raw_affiliation.get(
                    "identifier"
                )
                affiliation_id = (
                    id_value
                    if isinstance(id_value, str) and id_value.strip()
                    else _fragment_id("affiliation", affiliation_name)
                )
            else:
                raise ValueError("affiliations must be strings or objects")
            if not affiliation_name:
                raise ValueError("affiliation names must not be empty")
            affiliation_id = affiliation_id.strip()
            if not affiliation_id.startswith(("#", "http://", "https://")):
                raise ValueError("affiliation identifiers must be URIs or fragments")
            existing = affiliation_entities.get(affiliation_id)
            organization = {
                "@id": affiliation_id,
                "@type": "Organization",
                "name": affiliation_name,
            }
            if existing is not None and existing != organization:
                raise ValueError(
                    f"conflicting affiliation identifier: {affiliation_id}"
                )
            affiliation_entities[affiliation_id] = organization
            affiliation_refs.append({"@id": affiliation_id})

        entities.append(
            {
                "@id": identifier,
                "@type": "Person",
                "name": name,
                "affiliation": sorted(affiliation_refs, key=lambda row: row["@id"]),
            }
        )
        creator_refs.append({"@id": identifier})

    entities.extend(affiliation_entities.values())
    entities.sort(key=lambda row: row["@id"])
    creator_refs.sort(key=lambda row: row["@id"])
    return creator_refs, entities


def _validated_specs(
    crate_root: Path, path_specs: Sequence[CratePath]
) -> tuple[CratePath, ...]:
    root = crate_root.resolve()
    by_id: dict[str, CratePath] = {}
    for spec in path_specs:
        if not isinstance(spec, CratePath):
            raise TypeError("path_specs entries must be CratePath instances")
        if spec.path == RO_CRATE_METADATA_NAME:
            raise ValueError(
                "the metadata descriptor cannot represent itself as a file"
            )
        pure_path = PurePosixPath(spec.path.rstrip("/"))
        canonical_path = pure_path.as_posix() + ("/" if spec.is_directory else "")
        if (
            not spec.path
            or spec.path.startswith(("/", "./"))
            or "\\" in spec.path
            or canonical_path != spec.path
            or any(part in {"", ".", ".."} for part in pure_path.parts)
        ):
            raise ValueError(f"unsafe or non-canonical crate path: {spec.path!r}")
        if spec.path in by_id:
            raise ValueError(f"duplicate crate path: {spec.path}")
        if not spec.name.strip() or not spec.description.strip():
            raise ValueError(
                f"crate entity {spec.path!r} requires name and description"
            )
        by_id[spec.path] = spec

        local_path = crate_root.joinpath(*pure_path.parts)
        try:
            local_path.resolve().relative_to(root)
        except ValueError as error:
            raise ValueError(
                f"crate path escapes the release root: {spec.path}"
            ) from error
        if local_path.is_symlink():
            raise ValueError(
                f"represented paths must not be symbolic links: {spec.path}"
            )
        if spec.is_directory:
            if not local_path.is_dir():
                raise FileNotFoundError(
                    f"represented directory does not exist: {spec.path}"
                )
        elif not local_path.is_file():
            raise FileNotFoundError(f"represented file does not exist: {spec.path}")

    children: dict[str, list[str]] = defaultdict(list)
    for spec in by_id.values():
        if spec.parent != "./":
            parent = by_id.get(spec.parent)
            if parent is None or not parent.is_directory:
                raise ValueError(
                    f"crate entity {spec.path!r} has an unrepresented directory parent"
                )
        children[spec.parent].append(spec.path)

    reached: set[str] = set()
    queue: deque[str] = deque(sorted(children["./"]))
    while queue:
        entity_id = queue.popleft()
        if entity_id in reached:
            continue
        reached.add(entity_id)
        queue.extend(sorted(children[entity_id]))
    if reached != set(by_id):
        missing = ", ".join(sorted(set(by_id) - reached))
        raise ValueError(f"crate entities are not reachable from the root: {missing}")
    return tuple(sorted(by_id.values(), key=lambda spec: spec.path))


def _encoding_format(path: str) -> str:
    if PurePosixPath(path).name in {"LICENSE", "NOTICE", "VERSION"}:
        return "text/plain"
    return _ENCODING_FORMATS.get(
        PurePosixPath(path).suffix.lower(), "application/octet-stream"
    )


def build_ro_crate_document(
    crate_root: Path,
    dataset_metadata: Mapping[str, Any],
    *,
    release_date: str,
    description: str = DEFAULT_DESCRIPTION,
    path_specs: Sequence[CratePath] = DEFAULT_PATH_SPECS,
) -> dict[str, Any]:
    """Build an RO-Crate 1.3 JSON-LD document for a materialized release root.

    The selected paths are intentionally representative. The generated
    distribution manifest remains the exhaustive file-level integrity inventory,
    avoiding a second listing of the thousands of generated access files.
    """

    if not isinstance(crate_root, Path):
        crate_root = Path(crate_root)
    if not crate_root.is_dir():
        raise FileNotFoundError(f"crate root does not exist: {crate_root}")
    try:
        date.fromisoformat(release_date)
    except (TypeError, ValueError) as error:
        raise ValueError("release_date must be an ISO 8601 calendar date") from error
    if not isinstance(description, str) or not description.strip():
        raise ValueError("crate description must be non-empty")

    specs = _validated_specs(crate_root, path_specs)
    metadata_name = _required_text(dataset_metadata, "name")
    title = _required_text(dataset_metadata, "title")
    version = _required_text(dataset_metadata, "dataset_version")
    schema_version = _required_text(dataset_metadata, "schema_version")
    dataset_uri = _http_uri(
        _required_text(dataset_metadata, "dataset_uri"), "dataset URI"
    )
    doi_uri = _doi_uri(_required_text(dataset_metadata, "doi"))
    repository_uri = _http_uri(
        _required_text(dataset_metadata, "repository_uri"), "repository URI"
    )
    license_uri = _license_uri(_required_text(dataset_metadata, "license"))

    raw_sources = dataset_metadata.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ValueError("dataset metadata requires at least one source URI")
    sources = sorted(
        {
            _http_uri(value.strip(), "source URI")
            for value in raw_sources
            if isinstance(value, str) and value.strip()
        }
    )
    if len(sources) != len(raw_sources):
        raise ValueError("dataset source URIs must be unique non-empty strings")

    creator_refs, creator_entities = _creator_and_affiliation_entities(dataset_metadata)
    child_ids: dict[str, list[str]] = defaultdict(list)
    for spec in specs:
        child_ids[spec.parent].append(spec.path)

    local_entities: list[dict[str, Any]] = []
    for spec in specs:
        entity: dict[str, Any] = {
            "@id": spec.path,
            "@type": "Dataset" if spec.is_directory else "File",
            "name": spec.name,
            "description": spec.description,
        }
        if spec.is_directory:
            if child_ids[spec.path]:
                entity["hasPart"] = [
                    {"@id": child} for child in sorted(child_ids[spec.path])
                ]
        else:
            path = crate_root.joinpath(*PurePosixPath(spec.path).parts)
            entity["contentSize"] = str(path.stat().st_size)
            entity["encodingFormat"] = _encoding_format(spec.path)
        local_entities.append(entity)

    descriptor = {
        "@id": RO_CRATE_METADATA_NAME,
        "@type": "CreativeWork",
        "about": {"@id": "./"},
        "conformsTo": {"@id": RO_CRATE_PROFILE},
        "description": "RO-Crate Metadata Descriptor for the OMARO release.",
    }
    root_entity: dict[str, Any] = {
        "@id": "./",
        "@type": "Dataset",
        "name": title,
        "alternateName": metadata_name,
        "description": description.strip(),
        "identifier": [doi_uri, dataset_uri],
        "url": dataset_uri,
        "sameAs": doi_uri,
        "version": version,
        "schemaVersion": schema_version,
        "datePublished": release_date,
        "license": {"@id": license_uri},
        "creator": creator_refs,
        "codeRepository": {"@id": repository_uri},
        "isBasedOn": [{"@id": source} for source in sources],
        "hasPart": [{"@id": child} for child in sorted(child_ids["./"])],
        "conditionsOfAccess": CULTURAL_AUTHORIZATION_NOTICE,
    }
    represented_ids = {spec.path for spec in specs}
    if "README.md" in represented_ids:
        root_entity["mainEntityOfPage"] = {"@id": "README.md"}
    if "CULTURAL_GOVERNANCE.md" in represented_ids:
        root_entity["subjectOf"] = {"@id": "CULTURAL_GOVERNANCE.md"}

    ontology_ids: list[str] = []
    contextual_entities: list[dict[str, Any]] = [
        {
            "@id": license_uri,
            "@type": "CreativeWork",
            "name": _required_text(dataset_metadata, "license"),
            "description": (
                "Dataset-level legal licence. It does not establish cultural "
                "authorization, community consent, or permission to disclose "
                "restricted knowledge."
            ),
        },
        {
            "@id": repository_uri,
            "@type": "SoftwareSourceCode",
            "name": "OMARO source repository",
        },
    ]
    contextual_entities.extend(creator_entities)
    contextual_entities.extend(
        {
            "@id": source,
            "@type": "Dataset",
            "name": _SOURCE_NAMES.get(source, f"Source dataset: {source}"),
        }
        for source in sources
    )
    for key in ("ontology_uri", "ontology_version_iri"):
        value = dataset_metadata.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"dataset metadata {key!r} must be a URI when present")
        ontology_id = _http_uri(value.strip(), key.replace("_", " "))
        if ontology_id in ontology_ids:
            continue
        ontology_ids.append(ontology_id)
        contextual_entities.append(
            {
                "@id": ontology_id,
                "@type": "CreativeWork",
                "name": (
                    _required_text(dataset_metadata, "ontology_title")
                    if key == "ontology_version_iri"
                    else "OMARO ontology"
                ),
            }
        )
    if ontology_ids:
        root_entity["isRelatedTo"] = [
            {"@id": ontology_id} for ontology_id in sorted(ontology_ids)
        ]

    contextual_entities.sort(key=lambda row: row["@id"])
    graph = [descriptor, root_entity, *local_entities, *contextual_entities]
    entity_ids = [entity["@id"] for entity in graph]
    if len(entity_ids) != len(set(entity_ids)):
        duplicates = sorted(
            entity_id
            for entity_id in set(entity_ids)
            if entity_ids.count(entity_id) > 1
        )
        raise ValueError(f"RO-Crate entity identifiers are not unique: {duplicates}")
    return {"@context": RO_CRATE_CONTEXT, "@graph": graph}


def render_ro_crate_metadata(
    crate_root: Path,
    dataset_metadata: Mapping[str, Any],
    *,
    release_date: str,
    description: str = DEFAULT_DESCRIPTION,
    path_specs: Sequence[CratePath] = DEFAULT_PATH_SPECS,
) -> bytes:
    """Return deterministic UTF-8 JSON-LD bytes for an OMARO RO-Crate."""

    document = build_ro_crate_document(
        crate_root,
        dataset_metadata,
        release_date=release_date,
        description=description,
        path_specs=path_specs,
    )
    return (
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_ro_crate_metadata(
    crate_root: Path,
    dataset_metadata: Mapping[str, Any],
    *,
    release_date: str,
    description: str = DEFAULT_DESCRIPTION,
    path_specs: Sequence[CratePath] = DEFAULT_PATH_SPECS,
) -> Path:
    """Write ``ro-crate-metadata.json`` at a materialized release root."""

    crate_root = Path(crate_root)
    target = crate_root / RO_CRATE_METADATA_NAME
    payload = render_ro_crate_metadata(
        crate_root,
        dataset_metadata,
        release_date=release_date,
        description=description,
        path_specs=path_specs,
    )
    target.write_bytes(payload)
    return target
