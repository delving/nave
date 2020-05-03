# -*- coding: utf-8 -*-
"""This module contains all the tests for the void tasks.py
"""
import os
import time

from django.conf import settings
from django.test import TestCase, override_settings
from elasticsearch_dsl import Search
from pytest import skip
from rdflib import ConjunctiveGraph, URIRef, Graph

from nave.lod.models import RDFModel
from nave.lod.utils import rdfstore
from nave.lod.utils.rdfstore import UnknownGraph
from nave.void import tasks
from nave.void.models import DataSet, EDMRecord
from nave.void.tasks import schedule_out_of_sync_datasets


def load_nquad_fixtures(path=None):
    if not path:
        path = os.path.join(settings.DJANGO_ROOT, "void", "tests", "resources", "test_rdf_quads.nq")
    graph = ConjunctiveGraph()
    graph.parse(
        source=path,
        format='nquads'
    )
    store = rdfstore._rdfstore_test
    graph_store = store.get_graph_store
    for context in graph.contexts():
        graph_store.put(context.identifier.strip("<>"), context)
    return graph


class TestNQuadFixtures(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.graph = None
        cls.store = rdfstore._rdfstore_test
        cls.store._clear_all()

    @classmethod
    def tearDownClass(cls):
        # cls.store._clear_all
        pass

    def test_if_test_store_is_empty(self):
        self.assertFalse(self.store.ask(), msg="The triple store for testing should be empty when the test starts")

    def test_loading_nquads(self):
        self.graph = load_nquad_fixtures()
        self.assertIsNotNone(self.graph)
        self.assertTrue(self.store.ask(), msg="After loading the triple store should contain triples")
        graph_contexts = len(list(self.graph.contexts()))
        assert graph_contexts == 7
        self.assertTrue(
            self.store.ask(named_graph=list(self.graph.contexts())[0].identifier),
        )
        assert len(list(self.graph.subjects())) == 136
        self.assertEquals(
            len(list(self.graph.subjects())),
            self.store.count()
        )


@skip("We are not using this type of synchronisation anymore")
class TestNarthexSynchronisation(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = rdfstore._rdfstore_test
        cls.store._clear_all()
        cls.graph = load_nquad_fixtures()
        cls.index_name = "test"
        cls.dataset_graph_uri = "http://localhost:8000/resource/dataset/ton-smits-huis/graph"
        cls.dataset_uri = "http://localhost:8000/resource/dataset/ton-smits-huis"

    @classmethod
    def setUp(cls):
        cls.graph = load_nquad_fixtures()

    @classmethod
    def tearDown(cls):
        cls.store._clear_all()

    def test_find_out_of_sync_datasets(self):
        ds_nr, ds_list = tasks.find_datasets_with_records_out_of_sync(self.store)
        assert ds_nr == 1, "There should only be one out of sync dataset"
        self.assertIn(
            self.dataset_uri,
            ds_list
        )

    def test_get_unsynced_dataset_graph_uris(self):
        graph_list = tasks.get_out_of_sync_dataset_record_graph_uris(
            self.dataset_graph_uri,
            self.store
        )
        assert len(graph_list) == 1  # only one graph should be found
        self.assertNotIn(
            "http://localhost:8000/resource/dataset/ton-smits-huis/skos",
            graph_list
        )

    def test_creation_of_dataset_from_graph(self):
        ds = DataSet.get_dataset_from_graph(
            dataset_graph_uri=self.dataset_graph_uri,
            store=self.store
        )
        self.assertIsNotNone(ds)
        self.assertIsInstance(ds, DataSet)
        self.assertEquals(
            ds.named_graph,
            URIRef(self.dataset_graph_uri)
        )
        self.assertIn(
            "Ton Smits Huis",
            [group.name for group in ds.groups.all()]
        )
        ds_from_db = DataSet.objects.get(named_graph=self.dataset_graph_uri)
        self.assertEquals(
            ds_from_db.spec,
            str(ds.spec)
        )
        self.assertTrue(
            self.store.ask(
                named_graph=self.dataset_graph_uri,
                query="""where {{?s <http://schemas.delving.eu/narthex/terms/synced> true }}"""
            )
        )

    def test_unknown_dataset_uri(self):
        self.assertRaises(
            UnknownGraph,
            DataSet.get_dataset_from_graph,
            dataset_graph_uri=self.dataset_graph_uri + "test",
            store=self.store
        )

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_schedule_out_of_sync_datasets(self):
        assert DataSet.objects.count() == 0
        assert EDMRecord.objects.count() == 0
        async_response = schedule_out_of_sync_datasets.delay(store=self.store)
        scheduled = async_response.result
        assert scheduled == 1
        ds = DataSet.objects.get(spec="ton-smits-huis")
        assert not ds.sync_in_progress
        assert ds.stay_in_sync
        assert ds.records_in_sync
        assert DataSet.objects.count() == 1
        # time.sleep(2)
        # assert EDMRecord.objects.count() == 1

    def test_synchronise_record(self):
        ds = DataSet.get_dataset_from_graph(
            dataset_graph_uri=self.dataset_graph_uri,
            store=self.store
        )
        graph_list = tasks.get_out_of_sync_dataset_record_graph_uris(
            self.dataset_graph_uri,
            self.store
        )
        es_actions = []
        edm_record, es_action = tasks.synchronise_record(
            graph_uri=graph_list[0],
            ds=ds,
            store=self.store,
            es_actions=es_actions
        )
        self.assertIsNotNone(edm_record)
        self.assertIsNotNone(es_action)
        self.assertEqual(
            EDMRecord.objects.count(),
            1,
            "Only one record should be saved"
        )
        self.assertEquals(
            edm_record.dataset,
            ds
        )
        self.assertTrue(
            edm_record.hub_id.endswith("ton-smits-huis_454"),
        )
        self.assertRegex(
            edm_record.hub_id,
            "(.*?)_(.*?)_(.*?)"
        )
        assert edm_record.document_uri == 'http://localhost:8000/resource/aggregation/ton-smits-huis/454'
        self.assertEquals(
            edm_record.named_graph,
            URIRef('http://localhost:8000/resource/aggregation/ton-smits-huis/454/graph')
        )

    def test_add_cache_uri(self):
        self.assertIsNone(
            self.store.get_cached_source_uri(
                'http://localhost:8000/resource/cache/thumbnail/brabantcloud/ton-smits-huis/454/500'
            )
        )
        update_response = tasks.add_cache_urls_to_remote_resources(self.store)
        self.assertTrue(update_response)
        response = self.store.get_cached_source_uri(
            'http://localhost:8000/resource/cache/thumbnail/brabantcloud/ton-smits-huis/454/500'
        )
        self.assertIsNotNone(response)
        self.assertEquals(
            response,
            'http://media.delving.org/thumbnail/brabantcloud/ton-smits-huis/454/500',
            "The response should be None or a single url as string"
        )

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=False,
                       BROKER_BACKEND='memory',
                       CELERY_RESULT_BACKEND='database')
    def test_synchronise_dataset(self):
        from nave.search.connector import get_es_client
        client = get_es_client()
        s = Search(client).index(self.index_name)
        del_response = client.delete_by_query(index=self.index_name, q="*:*")
        es_response = s.execute()
        self.assertEquals(
            es_response.hits.total.value,
            0
        )
        self.assertEquals(
            EDMRecord.objects.count(),
            0
        )
        assert self.store.ask(query="""where {{
            GRAPH <http://localhost:8000/resource/aggregation/ton-smits-huis/454/graph>
            {{?s <http://schemas.delving.eu/narthex/terms/synced> false}}
            }}"""
                              )
        response = tasks.synchronise_dataset_records(
            dataset_graph_uri=self.dataset_graph_uri,
            store=self.store,
            index=self.index_name
        )
        # self.assertTrue(response.successful)
        # self.assertEquals(
        #     response.result,
        #     1
        # )
        self.assertEquals(
            EDMRecord.objects.count(),
            1
        )
        time.sleep(2)
        es_response = s.execute()
        self.assertEquals(
            es_response.hits.total.value,
            1,
            "there should be one record in the test index"
        )
        record = es_response.hits[0]
        self.assertEquals(
            record.meta.doc_type,
            "void_edmrecord"
        )
        self.assertEquals(
            "_".join(record.meta.id.split('_')[1:]),
            "ton-smits-huis_454"
        )
        # test if switch is flipped
        assert self.store.ask(query="""where {{
            GRAPH <http://localhost:8000/resource/aggregation/ton-smits-huis/454/graph>
            {{?s <http://schemas.delving.eu/narthex/terms/synced> true}}
            }}"""
                              )
        # test if dataset is deleted from index
        ds = DataSet.get_dataset_from_graph(
            dataset_graph_uri=self.dataset_graph_uri, store=self.store)
        ds.delete_from_index(self.index_name)
        es_response = s.execute()
        self.assertEquals(
            es_response.hits.total.value,
            0,
            "there should be no records in the test index after the dataset is deleted"
        )
        rdf_store_response = ds.delete_from_triple_store(self.store)
        assert rdf_store_response
        assert not self.store.ask(query="""where {{
            GRAPH <http://localhost:8000/resource/dataset/ton-smits-huis/graph>
            {{?s ?p ?o}}
            }}"""
                              )

    def test_context_graph_inlining(self):
        named_graph = "http://localhost:8000/resource/aggregation/ton-smits-huis/454/graph"
        inline_id = "http://data.cultureelerfgoed.nl/semnet/7403e26d-cf33-4372-ad72-a2f9fcf8f63b"
        context_graph, nr_levels = RDFModel.get_context_graph(
            store=self.store,
            named_graph=named_graph
        )
        self.assertIsNotNone(context_graph)
        self.assertIsInstance(context_graph, Graph)
        assert URIRef(inline_id) in list(context_graph.subjects())
        predicates = set(list(context_graph.predicates()))
        assert URIRef('http://www.openarchives.org/ore/terms/aggregates') in predicates

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=False,
                       BROKER_BACKEND='memory')
    def test_graph_indexing(self):
        ds = DataSet.get_dataset_from_graph(
            dataset_graph_uri=self.dataset_graph_uri,
            store=self.store
        )
        es_actions = []
        edm_record, es_action = tasks.synchronise_record(
            graph_uri="http://localhost:8000/resource/aggregation/ton-smits-huis/454/graph",
            ds=ds,
            store=self.store,
            es_actions=es_actions
        )
        self.assertTrue(
            edm_record.hub_id.endswith("ton-smits-huis_454")
        )
        action = edm_record.create_es_action(
            index=self.index_name,
            record_type="Aggregation",
            store=self.store,
            exclude_fields=['dc_rights']
        )
        self.assertIsNotNone(action)
        assert 'dc_rights' not in action['_source']
        assert action['_source']['system']['delving_recordType'] == "Aggregation"
        required_fields = [
            "_op_type", "_index", "_type", "_id", "_source"
        ]
        #  "graph", "slug", "delving_hubId", "delving_spec", "delving_recordType"
        assert set(list(es_action.keys())).issuperset(set(required_fields))
        assert 'about' in es_action['_source']
        assert 'edm_object' in es_action['_source']
        assert 'rdf' in es_action['_source']
        assert 'system' in es_action['_source']
        subjects = es_action['_source']['dc_subject']
        assert 'dc_rights' in es_action['_source']
        inline_id = 'http://data.cultureelerfgoed.nl/semnet/7403e26d-cf33-4372-ad72-a2f9fcf8f63b'
        inlined_example = [subject for subject in subjects if 'id' in subject and subject['id'] in [inline_id]][0]
        assert inlined_example
        assert inlined_example['id'] == inline_id
        assert inlined_example['value'] == "bomen"
        assert inlined_example['lang'] == "nl"

    def test_context_graph(self):
        ds = DataSet.get_dataset_from_graph(
            dataset_graph_uri=self.dataset_graph_uri,
            store=self.store
        )
        es_actions = []
        edm_record, es_action = tasks.synchronise_record(
            graph_uri="http://localhost:8000/resource/aggregation/ton-smits-huis/454/graph",
            ds=ds,
            store=self.store,
            es_actions=es_actions
        )
        context_graph, nr_levels = edm_record.get_context_graph(store=self.store, named_graph=edm_record.named_graph)
        self.assertIsNotNone(context_graph)
        self.assertIsInstance(context_graph, Graph)
        predicates = set(list(context_graph.predicates()))
        assert URIRef('http://www.openarchives.org/ore/terms/aggregates') in predicates


