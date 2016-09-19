# -*- coding: utf-8 -*-
"""This module test the graph to legacy format convertors

"""
from unittest import TestCase

import pytest

from nave.lod.utils import rdfstore
from nave.void.convertors import ICNConverter, DefaultAPIV2Converter, EDMStrictConverter, ESEConverter
from nave.void.tests.test_es_result_fields import es_fields
from nave.void.tests.test_tasks import load_nquad_fixtures


def test__converter__must_respect_hash_in_namespace():
    dc_creator = "http://purl.org/dc/elements/1.1/creator"
    assert "{http://purl.org/dc/elements/1.1/}creator" == EDMStrictConverter.uri_to_namespaced_tag(dc_creator)
    skos_concept = "http://www.w3.org/2004/02/skos/core#Concept"
    assert EDMStrictConverter.uri_to_namespaced_tag(skos_concept).endswith("#}Concept")


@pytest.mark.usefixtures("settings")
class TestESEConvertor(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.store = rdfstore._rdfstore_test
        cls.store._clear_all()
        cls.graph = load_nquad_fixtures()
        cls.dataset_graph_uri = "http://localhost:8000/resource/dataset/ton-smits-huis/graph"
        cls.about_uri = "http://localhost:8000/resource/aggregation/ton-smits-huis/454"

    @classmethod
    def tearDownClass(cls):
        cls.store._clear_all()

    def test_bindings(self):
        converter = ESEConverter(
            graph=self.graph,
            about_uri=self.about_uri
        )
        assert converter.bindings() is not None
        output = converter.convert()
        assert output is not None
        assert len(output.keys()) > 0
        assert output.get('delving_hasDigitalObject')
        assert 'europeana_uri' in output
        assert 'europeana_isShownAt' in output
        assert '/' in output.get('europeana_uri')[0]
        assert 'Smits, Ton' in output.get('dc_creator')

    def test_edm_strict(self):
        converter = EDMStrictConverter(
            graph=self.graph,
            about_uri=self.about_uri
        )
        assert converter
        assert converter.graph
        output = converter.convert(output_format='xml')
        assert output
        assert 'datasetRecordCount'.encode("utf-8") not in output
        assert 'nave:location'.encode("utf-8") not in output

    def test_with_es_fields(self):
        converter = ICNConverter(
            es_result_fields=es_fields
        )
        assert converter._es_result_fields is not None
        output = converter.convert()
        assert output is not None
        assert len(output.keys()) > 0
        assert output.get('delving_hasDigitalObject')

    def test_with_default_v2_converter(self):
        converter = DefaultAPIV2Converter(
            es_result_fields=es_fields
        )
        assert converter
        assert converter.bindings() is None
        assert converter._es_result_fields is not None
        output = converter.convert()
        assert output
        assert 'graph' not in output
        assert 'rdf' not in output
        assert not any([k.startswith('narthex_')for k in output.keys()])
        edm_isShownBy = output.get('edm_isShownBy')
        assert edm_isShownBy
        assert len(edm_isShownBy) == 1
        assert 'raw' not in edm_isShownBy[0]
