# -*- coding: utf-8 -*-
"""Unit Tests for Facets.

This module contains the unit-tests for facets.
"""
import pytest

from nave.rdf.search import facets


def test__facets__package_should_have_a_docstring():
    """Test for module docstring."""
    assert facets.__doc__


def test__facetconfig__should_have_a_docstring():
    """Test for class docstring."""
    assert facets.FacetConfig.__doc__


def test__facetconfig__on_new_should_have_an_es_field():
    """Test for required name."""
    with pytest.raises(TypeError) as attr_error:
        facets.FacetConfig()
    assert 'es_field' in str(attr_error)
    config = facets.FacetConfig(es_field="dc_subject")
    assert config
    assert config._es_field == "dc_subject"


def test__facetconfig__es_field_should_endswith_raw():
    """Test es_field property always endswith '.raw'."""
    assert facets.FacetConfig.es_field.__doc__
    config = facets.FacetConfig(es_field="dc_subject")
    assert config.es_field
    assert config.es_field.endswith('.raw')
