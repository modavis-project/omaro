"""Entailment and identity boundaries of the compact, import-free vocabulary."""

from copy import deepcopy
from dataclasses import fields

import pytest
from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate as shacl_validate
from rdflib import Graph, Namespace
from rdflib.namespace import OWL, PROV, RDF, RDFS, SH, SKOS

from omaro.builder import OMARO_NS as O, dataset_graph, ontology_schema_graph
from omaro.model import Dataset, ValidationError

EX = Namespace("https://example.org/inference/")


@pytest.fixture(scope="module")
def vocabulary(repo_root):
    dataset = Dataset.load(repo_root / "data/canonical")
    # Exercise the generator without materializing the empirical graph.
    for field in fields(dataset):
        if isinstance(getattr(dataset, field.name), list):
            setattr(dataset, field.name, [])
    return ontology_schema_graph(dataset, dataset_graph(dataset))


def test_local_disjointness_survives_compact_ontology_extraction(vocabulary):
    assert (
        O.ClassificationAssignment,
        OWL.disjointWith,
        O.ClassificationAssertion,
    ) in vocabulary
    assert (O.ReviewEvent, OWL.disjointWith, O.ReviewDecision) in vocabulary
    assert len(list(vocabulary.triples((None, OWL.disjointWith, None)))) == 10
    assert not list(vocabulary.triples((None, OWL.imports, None)))
    assert (
        O.InstrumentComponent,
        OWL.disjointWith,
        O.FunctionalModule,
    ) not in vocabulary


def test_reasoning_preserves_occurrences_and_does_not_invent_endorsement(vocabulary):
    graph = Graph() + vocabulary
    for assertion in (EX.claim1, EX.claim2):
        graph.add((assertion, RDF.type, O.ClassificationAssertion))
        graph.add((assertion, RDF.subject, EX.target))
        graph.add((assertion, RDF.predicate, O.classifiedAs))
        graph.add((assertion, RDF.object, EX.category))
    graph.add((EX.category, RDF.type, SKOS.Concept))
    graph.add((EX.category, SKOS.broader, EX.parentCategory))
    graph.add((EX.assignment, RDF.type, O.ClassificationAssignment))
    graph.add((EX.assignment, O.usedAssessment, EX.unobserved))
    graph.add((EX.assignment, O.usedObservation, EX.attempted))
    DeductiveClosure(OWLRL_Semantics).expand(graph)
    errors = Namespace("http://www.daml.org/2002/03/agents/agent-ont#")
    assert not list(graph.objects(None, errors.error))
    assert (EX.assignment, RDF.type, PROV.Activity) in graph
    assert (EX.claim1, RDF.type, PROV.Entity) in graph
    assert (EX.attempted, RDF.type, O.ObservationAssessment) in graph
    assert (EX.unobserved, RDF.type, O.OrganologicalObservation) not in graph
    assert (EX.target, O.classifiedAs, EX.category) not in graph
    assert (EX.claim1, OWL.sameAs, EX.claim2) not in graph
    assert (EX.category, RDFS.subClassOf, EX.parentCategory) not in graph


def test_owl_rl_detects_collapsed_activity_and_decision(vocabulary):
    graph = Graph() + vocabulary
    graph.add((EX.collapsed, RDF.type, O.ReviewEvent))
    graph.add((EX.collapsed, RDF.type, O.ReviewDecision))
    DeductiveClosure(OWLRL_Semantics).expand(graph)
    errors = Namespace("http://www.daml.org/2002/03/agents/agent-ont#")
    assert list(graph.objects(None, errors.error))


@pytest.mark.parametrize("activity", [O.ClassificationAssignment, O.ReviewEvent])
@pytest.mark.parametrize(
    "entity",
    [
        O.ClassificationAssertion,
        O.ConceptRelationAssertion,
        O.LabelAssertion,
        O.NoteAssertion,
        O.ReviewDecision,
    ],
)
def test_shacl_rejects_activity_entity_collapse(repo_root, activity, entity):
    shapes = Graph().parse(repo_root / "schema/dataset.shacl.ttl")
    shape = next(
        uri
        for uri in shapes.subjects(RDF.type, SH.NodeShape)
        if str(uri).endswith("#ActivityEntitySeparationShape")
    )
    graph = Graph()
    graph.add((EX.activity, RDF.type, activity))
    graph.add((EX.entity, RDF.type, entity))
    assert shacl_validate(graph, shacl_graph=shapes, use_shapes=[shape])[0]
    graph.add((EX.activity, RDF.type, entity))
    conforms, report, _ = shacl_validate(graph, shacl_graph=shapes, use_shapes=[shape])
    assert not conforms
    assert (None, SH.focusNode, EX.activity) in report


def test_model_rejects_cross_registry_activity_entity_collision(repo_root):
    dataset = Dataset.load(repo_root / "data/canonical")
    dataset.classification_assertions = deepcopy(dataset.classification_assertions)
    dataset.classification_assertions[0]["assignment_uri"] = dataset.label_assertions[
        0
    ]["uri"]
    with pytest.raises(
        ValidationError,
        match="assertion/decision entity and assignment/review activity URI spaces overlap",
    ):
        dataset.validate()


def test_model_rejects_cross_event_review_decision_collision(repo_root):
    dataset = Dataset.load(repo_root / "data/canonical")
    # Take the existing review fixture without depending on its validity; the
    # new guard must also reject a decision reused by another activity.
    from test_conformance import _review_fixture

    fixture, _, _ = _review_fixture(repo_root)
    dataset.review_events = deepcopy(fixture.review_events)
    dataset.review_events[1]["uri"] = dataset.review_events[0]["decision_uri"]
    with pytest.raises(
        ValidationError,
        match="assertion/decision entity and assignment/review activity URI spaces overlap",
    ):
        dataset.validate()
