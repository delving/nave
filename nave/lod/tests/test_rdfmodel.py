# -*- coding: utf-8 -*- 
"""This module tests the RDFModel BaseClass.
"""
from django.conf import settings
from django.test import TestCase
from rdflib import ConjunctiveGraph, URIRef, Literal, Graph
from rdflib.namespace import FOAF, RDFS, RDF, DC, SKOS

from nave.lod.models import RDFModelTest, RDFModel
from nave.lod.utils import rdfstore


class TestRDFModel(TestCase):
    """ Test the implementation of the RDFModel base class
    """

    def setUp(self):
        self.rdf = RDFModelTest.objects.create(local_id="123")
        self.graph = self.rdf.get_graph()

    def tearDown(self):
        self.rdf.delete()

    def test_rdfmodel_has_UUID(self):
        self.assertTrue(self.rdf.uuid, msg="A RDF model should always have a UUID")

    def test_rdfmodel_has_spec(self):
        """Spec must always be implement in the subclass."""
        self.assertIsNotNone(self.rdf.get_spec_name())
        self.assertEqual(self.rdf.get_spec_name(), "test_spec", msg="Spec name must always be implemented.")

    def test_rdfmodel_local_id_cannot_be_empty(self):
        self.assertIsNotNone(self.rdf.local_id, "Local Id cannot be empty")

    def test_rdfmodel_has_hub_id(self):
        self.assertEqual(
            self.rdf.hub_id,
            "{}_{}_{}".format(settings.ORG_ID, self.rdf.get_spec_name(), self.rdf.local_id),
            "hub_id should always consist of the org_id, specname, and the localId"
        )

    def test_rdfmodel_slugfield_must_be_generated_from_slug_field(self):
        assert self.rdf.slug_field is not None
        assert self.rdf.slug_field == "hub_id"
        self.assertEqual(self.rdf.slug, self.rdf.hub_id, "The model field specified in the slug_field variable should "
                                                         "be used for the slug generation.")

    def test_rdfmodel_document_uri_generation(self):
        self.assertEqual(
            self.rdf.document_uri,
            self.rdf._get_document_uri(),
            "The generate document_uri should be used to generate the document_uri"
        )

    def test_rdfmodel_generate_document_uri(self):
        document_uri_list = self.rdf._get_document_uri().split('/')[-3:]
        self.assertListEqual(document_uri_list, [self.rdf.get_rdf_type(), self.rdf.get_spec_name(), self.rdf.local_id])

    def test_rdfmodel_generate_doctype(self):
        self.assertEqual(
            self.rdf._generate_doc_type(),
            "lod_rdfmodeltest",
            "the doctype must be generated from the appname and modelname"
        )

    def test_rdfmodel_get_graph_should_have_one_graph(self):
        self.assertIsNotNone(self.rdf.named_graph)
        contexts = list(self.graph.contexts())
        self.assertEqual(
            len(contexts),
            1,
            "The graph should only contain one named graph."
        )
        self.assertEqual(
            self.rdf.named_graph,
            str(contexts[0].identifier),
            "The name of the named graph should be the same as the one generated by the model."
        )

    def test_rdfmodel_rdf_type_addition(self):
        self.assertIn(
            self.rdf.ns[self.rdf.get_rdf_type()],
            list(self.graph.objects(predicate=RDF.type))
        )

    def test_rdfmodel_add_graph_mappings(self):
        predicates = list(self.graph.predicates(subject=URIRef(self.rdf._get_document_uri())))
        expected_predicates = [DC.title, DC.identifier, RDFS.isDefinedBy]
        self.assertTrue(
            set(expected_predicates).issubset(set(predicates)),
        )
        self.assertTrue(
            self.graph.objects(
                subject=URIRef(self.rdf._get_document_uri()),
                predicate=DC.title
            ),
            "test title"
        )

    def test_rdfmodel_get_graph_about(self):
        assert self.graph is not None
        self.assertIsInstance(self.graph, ConjunctiveGraph, "The graph must support namespaces")
        subjects = set(self.graph.subjects())
        self.assertListEqual(
            sorted(list(subjects)),
            sorted([URIRef(self.rdf._generate_about_uri()), URIRef(self.rdf._get_document_uri())]),
            "The graph should contain two subjects for the record and the #about"
        )
        about = self.graph.predicate_objects(subject=URIRef(self.rdf._generate_about_uri()))
        self.assertEqual(
            len(list(about)),
            8,
            "Each about should have 8 entries"
        )
        self.assertIn(
            FOAF.Document,
            list(self.graph.objects(predicate=RDF.type))
        )


class TestBindingSparqlResult(TestCase):
    def setUp(self):
        from .resources import sparqlwrapper_result as result

        sparql_json = result.sparql_result
        self.graph, self.nr_levels = RDFModel.get_graph_from_sparql_results(sparql_json)

    def test_binding_unpacking_single_key_dict(self):
        uri_object_dict = {
            'o': {
                'value': 'http://localhost:8000/resource/dataset/ton-smits-huis',
                'type': 'uri'
            }
        }
        obj = RDFModel.get_object_from_sparql_result(uri_object_dict)
        assert obj is not None
        assert isinstance(obj, URIRef)
        assert obj == URIRef(uri_object_dict['o']['value'])

    def test_binding_with_uri(self):
        uri_object_dict = {
            'o': {
                'value': 'http://localhost:8000/resource/dataset/ton-smits-huis',
                'type': 'uri'
            }
        }
        obj = RDFModel.get_object_from_sparql_result(uri_object_dict['o'])
        assert obj is not None
        assert isinstance(obj, URIRef)
        assert obj == URIRef(uri_object_dict['o']['value'])

    def test_with_language_literal(self):
        literal_object_dict = {
            'o3': {
                'value': 'bomen',
                'xml:lang': 'nl',
                'type': 'literal'
            }
        }
        obj = RDFModel.get_object_from_sparql_result(literal_object_dict)
        assert obj is not None
        assert isinstance(obj, Literal)
        assert obj.language == "nl"
        assert obj.datatype is None
        assert obj == Literal(
            literal_object_dict['o3']['value'],
            lang="nl"
        )

    def test_binding_with_typed_literal(self):
        object_dict = {
            'o2': {
                'value': 'false',
                'type': 'typed-literal',
                'datatype': 'http://www.w3.org/2001/XMLSchema#boolean'
            }
        }
        obj = RDFModel.get_object_from_sparql_result(object_dict)
        assert obj is not None
        assert isinstance(obj, Literal)
        assert obj.language is None
        assert obj.datatype is not None
        assert obj.datatype == URIRef("http://www.w3.org/2001/XMLSchema#boolean")
        assert obj == Literal(
            object_dict['o2']['value'],
            datatype="http://www.w3.org/2001/XMLSchema#boolean"

        )

    def test_bindings_determine_context_levels(self):
        test_list = [
            "s",
            "p",
            "o",
            "p2",
            "o2",
            "p3",
            "o3"
        ]
        levels = RDFModel.get_context_triples(test_list)
        assert len(levels) == 3
        assert len(RDFModel.get_context_triples(test_list[:3])) == 1
        assert len(RDFModel.get_context_triples(test_list[:5])) == 2
        assert levels[0] == ("s", "p", "o")
        assert levels[1] == ("o", "p2", "o2")
        assert levels[2] == ("o2", "p3", "o3")

    def test_bindings_get_graph_from_sparql_results_without_named_graph(self):
        from .resources import sparqlwrapper_result_graph_name as result

        sparql_json = result.sparql_result
        graph, nr_level = RDFModel.get_graph_from_sparql_results(
            sparql_json
        )
        assert graph is not None
        assert graph.identifier == URIRef("http://localhost:8000/resource/aggregation/ton-smits-huis/454/graph")
        assert len(graph) == 118
        predicates = set(graph.predicates())
        assert len(predicates) != 0
        assert len(predicates) == 67

    def test_bindings_get_graph_from_sparql_results(self):
        from .resources import sparqlwrapper_result as result

        sparql_json = result.sparql_result
        graph, nr_level = RDFModel.get_graph_from_sparql_results(
            sparql_json,
            named_graph="http://localhost:8000/resource/aggregation/ton-smits-huis/454/graph"
        )
        assert graph is not None
        assert graph.identifier == URIRef("http://localhost:8000/resource/aggregation/ton-smits-huis/454/graph")
        assert len(graph) == 118
        predicates = set(graph.predicates())
        assert len(predicates) != 0
        assert len(predicates) == 67
        assert URIRef("http://purl.org/dc/elements/1.1/subject") in list(predicates)
        rdf_types = sorted(set(graph.objects(predicate=RDF.type)))
        assert rdf_types == sorted({URIRef('http://www.europeana.eu/schemas/edm/ProvidedCHO'),
                                    URIRef('http://www.europeana.eu/schemas/edm/WebResource'),
                                    URIRef('http://schemas.delving.eu/nave/terms/DelvingResource'),
                                    URIRef('http://www.openarchives.org/ore/terms/Aggregation'),
                                    URIRef('http://schemas.delving.eu/narthex/terms/Record'),
                                    URIRef('http://schemas.delving.eu/nave/terms/BrabantCloudResource'),
                                    URIRef('http://schemas.delving.eu/narthex/terms/Dataset'),
                                    URIRef('http://www.w3.org/2004/02/skos/core#Concept')})
        assert Literal("bomen", lang="nl") in graph.preferredLabel(
            subject=URIRef('http://data.cultureelerfgoed.nl/semnet/7403e26d-cf33-4372-ad72-a2f9fcf8f63b')
        )[0]
        bnodes_materialized = list(graph.objects(predicate=URIRef("http://www.openarchives.org/ore/terms/aggregates")))
        assert len(bnodes_materialized) == 1

    def test_get_graph_statistics(self):
        graph = self.graph
        stats = RDFModel.get_graph_statistics(graph=graph)
        assert stats is not None
        assert isinstance(stats, dict)
        assert 'language' in stats
        assert stats['language'] == [('nl', 1)]
        assert sorted(stats['RDF class']) == sorted(
            [('skos:Concept', 7), ('nave:BrabantCloudResource', 1), ('narthex:Record', 1), ('edm:ProvidedCHO', 1),
             ('edm:WebResource', 1), ('nave:DelvingResource', 1), ('ore:Aggregation', 1), ('narthex:Dataset', 1)]
        )
        assert 'property' in stats
        assert len(stats['property']) > 0

    def test_get_geo_points(self):
        graph = Graph()
        subject = URIRef('joachim')
        graph.add((subject, URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#lat"), Literal("51.54")))
        graph.add((subject, URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#long"), Literal("5.2")))
        points = RDFModel.get_geo_points(graph)
        assert points is not None
        assert points == [[51.54, 5.2]]
        graph = Graph()
        points = RDFModel.get_geo_points(graph)
        assert points == []


class TestSKOSQueries(TestCase):


    def test_query_against_prod(self):
        target_uri = "http://data.cultureelerfgoed.nl/semnet/7403e26d-cf33-4372-ad72-a2f9fcf8f63b"
        store = rdfstore.get_rdfstore()
        query = """PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            Construct {{
             ?s ?p ?o .
             ?s skos:broader ?broader.
             ?broader skos:prefLabel ?prefLabel .
             ?o skos:prefLabel ?prefLabel .
            }}

            WHERE {{
              bind(<{}> as ?s)
              {{
              ?s skos:broader* ?broader.
              FILTER ( ?s != ?broader )
              ?broader skos:prefLabel ?prefLabel.
               ?o skos:prefLabel ?prefLabel .
              }}
              union
              {{
                ?s ?p ?o .
                  Optional {{
                   ?o skos:prefLabel ?prefLabel
                }}
              }}}}
              LIMIT 100
        """.format(target_uri)
        skos_graph = store.query(query=query)
        assert skos_graph is not None
        assert isinstance(skos_graph, ConjunctiveGraph)
        broader_links = list(skos_graph.objects(predicate=SKOS.broader))
        # assert len(broader_links) == 4
        # assert broader_links == [
        #     URIRef("http://data.cultureelerfgoed.nl/semnet/a86afdd2-ae8d-4fee-a484-472bdb3b1f8b"),
        #     URIRef("http://data.cultureelerfgoed.nl/semnet/9537d9bb-d842-4c31-bb3a-71677224eeb3"),
        #     URIRef("http://data.cultureelerfgoed.nl/semnet/a2971af0-cde7-4888-b828-33443f702e7d"),
        #     URIRef("http://data.cultureelerfgoed.nl/semnet/4c71a675-468e-4e66-94d7-6ce847d9ad32"),
        #     URIRef("http://data.cultureelerfgoed.nl/semnet/bece25a6-eb64-46e8-85a8-2a7991f02a2c"),
        # ]









