# coding=utf-8
"""Unit tests for the ElasticSearch RDF models."""
from search.es_models import RDFIndexRecord

test_index = "test"


def test__rdfrecord__init():
    RDFIndexRecord.init(index=test_index)
