# -*- coding: utf-8 -*- 
from urllib.parse import quote

import lod
from lod.templatetags.dataset_tags import get_resolved_uri
from lod.utils.resolver import RDFRecord


def test__get_rdf_base_url__return_base_url_from_settings(settings):
    settings.RDF_BASE_URL = "http://testserver"
    base_url = RDFRecord.get_rdf_base_url()
    assert base_url
    assert base_url == "testserver"
    base_url = RDFRecord.get_rdf_base_url(prepend_scheme=True, scheme="https")
    assert base_url
    assert base_url == "https://testserver"


def test__get_resolved_uri__return_resolved_uri(rf, settings):
    settings.RDF_BASE_URL = "lod.delving.org"
    settings.RDF_ROUTED_ENTRY_POINTS = ["testserver"]
    request = rf.get('/resource/dataset/dummy1')
    context = {'request': request}
    test_uri = "http://lod.delving.org/resource/dataset/dummy1"
    resolved_uri = get_resolved_uri(context, test_uri)
    assert resolved_uri
    assert resolved_uri == "http://testserver/resource/dataset/dummy1"


def test__get_resolved_uri__return_cached_uri(rf, settings):
    settings.RDF_BASE_URL = "lod.delving.org"
    settings.RDF_ROUTED_ENTRY_POINTS = ["testserver"]
    request = rf.get('/resource/dataset/dummy1')
    context = {'request': request}
    test_uri = "http://lod.external.org/resource/dataset/dummy1"
    resolved_uri = get_resolved_uri(context, test_uri)
    assert resolved_uri
    assert resolved_uri == "http://lod.delving.org/resource/cache/{}".format(quote(test_uri, safe='/'))


def test__get_resolved_uri__return_rdf_base_uri(rf, settings):
    settings.RDF_BASE_URL = "testserver"
    settings.RDF_ROUTED_ENTRY_POINTS = []
    request = rf.get('/resource/dataset/dummy1')
    context = {'request': request}
    test_uri = "http://testserver/resource/dataset/dummy1"
    resolved_uri = get_resolved_uri(context, test_uri)
    assert resolved_uri
    assert resolved_uri == test_uri
