# -*- coding: utf-8 -*- 
"""This module contains all the tests for the Resource Cache mechanism of Nave.
"""
import time
from urllib.parse import quote

from django.db import models
from django.test import TestCase, override_settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from rdflib import Graph
from rdflib.namespace import RDF

from lod import tasks, get_rdf_base_url
from lod.models import ResourceCacheTarget, CacheResource
from lod.utils import rdfstore
from void.tests.test_tasks import load_nquad_fixtures


class TestResourceCacheTarget(TestCase):

    def test__resource_cache_target_initialisation(self):
        target = ResourceCacheTarget()
        self.assertTrue(
            issubclass(ResourceCacheTarget, models.Model), "It should be a django model."
        )

    # check if target exists
    # create entry
    # check base_url regex
    # extract ontology from triple store or sparql endpoint
    # check classes and properties in models
    # what happens when you give a bad url
    # can't add two base_urls
    # create void dataset in the triple-store for the cached resource
    pass


class TestResourceCache(TestCase):

    def test_get_remote_lod_resource(self):
        test_uri = "http://sws.geonames.org/2759794"
        resource = CacheResource.get_remote_lod_resource(test_uri)
        assert resource is not None
        assert isinstance(resource, Graph)
        assert len(list(resource.predicates())) != 0
        assert len(list(resource.objects(predicate=RDF.type))) == 2

    def test_bad_get_remote_lod_resource(self):
        bad_uri = "http://sws.geonames.org/2759794/about2.rdf"
        resource = CacheResource.get_remote_lod_resource(bad_uri)
        assert resource is None

    def test_store_remote_cached_resource(self):
        test_uri = "http://nl.dbpedia.org/resource/Ton_Smits"
        resource = CacheResource.get_remote_lod_resource(test_uri)
        store = rdfstore._rdfstore_test
        assert len(resource) > 0
        store._clear_all()
        graph_store = store.get_graph_store
        cache_graph = "http://{}/resource/cache#graph".format(get_rdf_base_url())
        self.assertFalse(
            store.ask(
                query="where {{<{}> ?p ?o}}".format(test_uri)
            ))
        response = CacheResource.store_remote_cached_resource(resource, graph_store, cache_graph)
        assert response is not None
        assert response
        self.assertTrue(
            store.ask(
                query="where {{<{}> ?p ?o}}".format(test_uri)
            )
        )
        #  cacheUrl is no longer being added
        self.assertFalse(
            store.ask(
                query="where {{<{}> <http://schemas.delving.org/nave/terms/cacheUrl> ?o}}".format(
                    test_uri)
            )
        )

    def test_cache_url(self):
        test_uri = "http://nl.dbpedia.org/resource/Ton_Smits"
        assert '/' not in quote(test_uri, safe='')

    def test_save_cached_resource(self):
        store = rdfstore._rdfstore_test
        store._clear_all()
        graph = load_nquad_fixtures()
        assert len(graph) > 0
        graph_store = store.get_graph_store
        resource = CacheResource()
        resource.source_uri = "http://nl.dbpedia.org/resource/Ton_Smits"
        resource.save()
        assert CacheResource.objects.count() == 1
        #  from ..tasks import store_cache_resource
        response = resource.update_cached_resource(graph_store)
        assert response
        resource_object = CacheResource.objects.first()
        assert resource_object.get_spec_name() == "cache"
        assert resource_object.named_graph == resource_object.document_uri + "#graph"
        assert resource_object.stored
        assert len(resource_object.get_graph()) > 0
        assert len(resource_object.source_rdf) > 0

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND='memory')
    def test_save_cached_resource(self):
        client = Elasticsearch()
        s = Search(client).index("test")
        del_response = client.delete_by_query(index='test', q="*:*")
        es_response = s.execute()
        self.assertEquals(
            es_response.hits.total,
            0
        )
        assert CacheResource.objects.count() == 0
        store = rdfstore._rdfstore_test
        store._clear_all()
        graph = load_nquad_fixtures()
        assert len(graph) > 0
        resource = CacheResource()
        resource.source_uri = "http://nl.dbpedia.org/resource/Ton_Smits"
        resource.save()
        response = tasks.store_cache_resource.delay(obj=resource, store=store)
        assert response.status
        assert response.result
        response = tasks.update_rdf_in_index.delay(obj=resource, store=store, index='test')
        time.sleep(1)
        assert response.status
        assert response.result
        assert CacheResource.objects.count() == 1
        es_response = s.execute()
        self.assertEquals(
            es_response.hits.total,
            1
        )
        record = es_response.hits[0]
        # assert len(list(record['_source'].keys())) > 2
        resource = CacheResource.objects.first()
        es_action =  resource.create_es_action(index="test", store=store, record_type="cached")
        assert es_action is not None


class TestCacheResourceAPI(TestCase):
    pass


class TestSchema(TestCase):

    # only for local schema. Otherwise a Cache Resource Target
    pass


class TestSchemaEntry(TestCase):

    # is a class or property
    # has labels with languages

    pass

