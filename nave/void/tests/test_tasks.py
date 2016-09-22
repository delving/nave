# -*- coding: utf-8 -*- 
"""This module contains all the tests for the void tasks.py
"""
import os
import time

from django.conf import settings
from django.test import TestCase, override_settings
from rdflib import ConjunctiveGraph, URIRef, Graph

from nave.lod.utils import rdfstore


def load_nquad_fixtures(path=None):
    if not path:
        path = os.path.join(settings.DJANGO_ROOT, "void", "tests", "resources", "test_rdf_quads.nq")
    graph = ConjunctiveGraph()
    graph.parse(
        source=path,
        format='nquads'
    )
    store = rdfstore.create_rdf_store("test")
    graph_store = store.get_graph_store
    for context in graph.contexts():
        graph_store.put(context.identifier.strip("<>"), context)
    return graph


class TestNQuadFixtures(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.graph = None
        cls.store = rdfstore.create_rdf_store("test")
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
