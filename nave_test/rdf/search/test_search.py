from nave.rdf.search import Searcher


def test__searcher__raw__init():
    search = Searcher()
    assert search


def test__searcher__facet_list_should_be_empty_when_no_facets_are_given():
    search = Searcher()
    facet_list = search.facet_list
    assert facet_list == []


def test__searcher__can_be_initialised_with_default_facets():
    search = Searcher()
    assert not search.default_facets
    facets = ["gemeente"]
    search = Searcher(default_facets=facets)
    assert search.default_facets == facets
