# -*- coding: utf-8 -*-
"""
Testing the mimetype.py module
"""
import pytest
from nave.lod import RDF_SUPPORTED_MIME_TYPES
from nave.lod.utils import mimetype as mimeutils


def test_mime_to_extension():
    assert mimeutils.mime_to_extension(mimeutils.TURTLE_MIME) == "turtle"
    assert mimeutils.mime_to_extension('text/wrong_rdf') == "rdf"


def test_extension_to_mime():
    assert mimeutils.extension_to_mime("ttl") == ("turtle", mimeutils.TURTLE_MIME)
    assert mimeutils.extension_to_mime("json") == ("json-ld", mimeutils.JSONLD_MIME)
    assert mimeutils.extension_to_mime("unknown") == ("xml", mimeutils.RDFXML_MIME)


def test_result_extension_to_mime():
    assert mimeutils.result_extension_to_mime("xml") == mimeutils.XML_MIME
    with pytest.raises(KeyError):
        assert mimeutils.result_extension_to_mime("unknown") == "text/plain"


def test_best_match():
    assert mimeutils.best_match(RDF_SUPPORTED_MIME_TYPES, "text/turtle") == mimeutils.TURTLE_MIME
    assert mimeutils.best_match(RDF_SUPPORTED_MIME_TYPES, "text/unknown") == ''
    assert mimeutils.best_match(RDF_SUPPORTED_MIME_TYPES, 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8') == ''
    assert mimeutils.best_match(RDF_SUPPORTED_MIME_TYPES, None) is None
