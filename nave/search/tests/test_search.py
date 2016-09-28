from nave.search.search import NaveESQuery
from nave.base_settings import FacetConfig

def test__naveesquery__must_have_default_facets_as_facets():
    es_query = NaveESQuery()
    assert es_query.facet_list == []
    facet = FacetConfig("gemeente.raw", label="Gemeente")
    es_query = NaveESQuery(default_facets=[facet])
    facet_list = es_query.facet_list
    assert facet_list
    assert len(facet_list) == 1
    assert "gemeente.raw" in facet_list
