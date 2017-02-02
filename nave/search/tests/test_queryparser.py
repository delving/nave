# -*- coding: utf-8 -*-
""" Test Nave QueryParser."""
from functools import partial

from django.test import TestCase

from search.search import NaveESQuery


def test_normal_query_string():
    response = NaveESQuery._is_fielded_query("A query")
    assert response is not None
    assert not response
    assert not NaveESQuery._is_fielded_query("one and two")


def test_fielded_query():
    response = NaveESQuery._is_fielded_query("dc_subject.value:bloemen")
    assert response is not None
    assert response
    assert NaveESQuery._is_fielded_query("_id:123")
    assert NaveESQuery._is_fielded_query("one AND two")
    assert NaveESQuery._is_fielded_query("rdf.object.value:bloemen")


def test_query_cleanup():
    query = NaveESQuery()
    assert query._created_fielded_query(query_string="dc_subject_facet:bloem") == "dc_subject.raw:bloem"
    assert query._created_fielded_query(query_string="dc_subject_string:bloem") == "dc_subject.raw:bloem"
    assert query._created_fielded_query(query_string="dc_subject_text:bloem") == "dc_subject.value:bloem"
    assert query._created_fielded_query(query_string="dc_subject.value:bloem") == "dc_subject.value:bloem"


def test_multi_string_query_cleanup():
    query = NaveESQuery()
    res = query._created_fielded_query(
        query_string="dc_subject_facet:bloem AND dc_title_text:roos"
    )
    res == "dc_subject.raw:bloem AND dc_title.value:roos"
