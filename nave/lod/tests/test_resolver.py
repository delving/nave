# -*- coding: utf-8 -*-
"""This test module test the resolver functionality."""
from rdflib import ConjunctiveGraph

from nave.lod.utils.resolver import get_geo_points, get_internal_rdf_base_uri


def test_get_geo_points_with_bad_floats():
    graph = ConjunctiveGraph()
    triples = """
    <http://localhost:8000/resource/rce/top100/6880> <http://www.w3.org/2003/01/geo/wgs84_pos#long> "3,447957107" .
    <http://localhost:8000/resource/rce/top100/6880> <http://www.w3.org/2003/01/geo/wgs84_pos#lat> "51,2729816364" .
    """
    graph.parse(data=triples, format='nt')
    points = get_geo_points(graph)
    assert points is not None


def test_get_geo_points_with_good_floats():
    graph = ConjunctiveGraph()
    triples = """
    <http://localhost:8000/resource/rce/top100/6880> <http://www.w3.org/2003/01/geo/wgs84_pos#long> "3.447957107" .
    <http://localhost:8000/resource/rce/top100/6880> <http://www.w3.org/2003/01/geo/wgs84_pos#lat> "51.2729816364" .
    """
    graph.parse(data=triples, format='nt')
    points = get_geo_points(graph)
    assert points is not None
    assert points == [[51.2729816364, 3.447957107]]


def test__get_internal_rdf_base_uri__returns_triple_store_base_uri(settings):
    settings.RDF_BASE_URL = "acc.dcn.delving.org"
    target_uri = "http://localhost:8000/en/page/aggregation/aidsmemorial/184"
    base_url = get_internal_rdf_base_uri(target_uri)
    assert base_url
    assert base_url == "http://acc.dcn.delving.org/en/page/aggregation/aidsmemorial/184"
    target_uri = "http://localhost:9000/en/page/aggregation/aidsmemorial/184"
    base_url = get_internal_rdf_base_uri(target_uri)
    assert base_url
    assert base_url == target_uri
