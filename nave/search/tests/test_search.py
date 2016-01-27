import os
import pickle
from os.path import dirname, abspath
from unittest import skip

import pytest
from django.http import QueryDict
from django.test import RequestFactory, TestCase
from elasticutils import FacetResult

from search.search import NaveESQuery, GeoS, FacetCountLink, FacetLink, UserQuery, NaveFacets, NaveQueryResponse, \
    QueryPagination
from search.serializers import UserQuerySerializer, FacetCountLinkSerializer, FacetLinkSerializer, NaveFacetSerializer, \
    NaveQueryResponseSerializer, QueryPaginationSerializer

rf = RequestFactory()


pytestmark = pytest.mark.skipif(True, reason="This whole unit test needs to be migrated to use elasticsearch-dsl")


def _request(param_dict):
    return rf.get('api/search', param_dict)


def _query(query, param_dict=None, as_dict=True, from_request=True):
    if not param_dict:
        param_dict = {}
    request = _request(param_dict)
    request_query = query.build_query_from_request(request) if from_request else query
    return request_query.build_search() if as_dict else query


def _geo_query(query, param_dict=None, as_dict=True, from_request=True):
    if not param_dict:
        param_dict = {}
    request = _request(param_dict)
    request_query = query.build_geo_query(request) if from_request else query
    return request_query.build_search() if as_dict else query


def _steps(query, param_dict=None, as_dict=True, from_request=True):
    if not param_dict:
        param_dict = {}
    request = _request(param_dict)
    request_query = query.build_query_from_request(request)
    steps = request_query.steps
    return dict(steps) if as_dict else steps


# noinspection PyMethodMayBeStatic
class TestBasicQueries(TestCase):
    def test__empty_query__returns_match_all_query(self):
        assert NaveESQuery().query.steps == []


# noinspection PyMethodMayBeStatic
class TestQueryWithIndexNames(TestCase):
    def test__index_name__submitted_as_string(self):
        assert NaveESQuery(index_name='brabantcloud').query.steps == [('indexes', ('brabantcloud',))]

    def test__index_name__submitted_as_list(self):
        assert NaveESQuery(index_name=['brabantcloud', 'dcn']).query.steps == [
            ('indexes', ('dcn', 'brabantcloud'))
        ]


class TestQueryWithDoctypes(TestCase):
    def test__doctype__submitted_as_string(self):
        assert NaveESQuery(doc_types='mip_miprecord').query.steps == [('doctypes', ('mip_miprecord',))]

    def test__doctype__submitted_as_list(self):
        assert NaveESQuery(doc_types=['mip_miprecord']).query.steps == [('doctypes', ('mip_miprecord',))]


class TestQueryWithDefaultFacets(TestCase):
    def test__default_facets_as_string__should_return_facet(self):
        assert NaveESQuery(default_facets='gemeente').build_query().steps == [('facet', (('gemeente',), {'size': 50}))]

    def test__default_facets_as_list__should_not_contain_duplicates(self):
        assert NaveESQuery(default_facets=['gemeente', 'gemeente']).build_query().steps == [
            ('facet', (('gemeente',), {'size': 50}))]

    def test__default_facets__should_contain_multiple_unique_facets(self):
        assert NaveESQuery(default_facets=['gemeente', 'plaats']).build_query().steps == [
            ('facet', (('gemeente', 'plaats'), {'size': 50}))]


class TestQueryWithFacetSize(TestCase):

    def test__facet_size__with_default_settings(self):
        assert NaveESQuery(default_facets=['gemeente', 'plaats']).build_query().steps == [
            ('facet', (('gemeente', 'plaats'), {'size': 50}))]

    def test__request_query_with_page__should_return_from_based_on_size(self):
        query = NaveESQuery(default_facets=['gemeente', 'plaats'])
        assert _query(query, {'facet.size': '10'}) == {
            'facets': {'gemeente.raw': {'facet_filter': None, 'terms': {'field': 'gemeente.raw', 'size': 10}},
                       'plaats.raw': {'facet_filter': None, 'terms': {'field': 'plaats.raw', 'size': 10}}},
            'size': 16
        }


class TestQueryWithPageFromRequest(TestCase):
    query = NaveESQuery(size=16)

    def test__request_query_with_page__should_return_from_based_on_size(self):
        assert _query(self.query, {'page': '2'})['from'] == 16

    def test__request_query_with_page__should_not_contain_from_when_page_is_one(self):
        assert 'from' not in _query(self.query, {'page': '1'})


class TestFeatureCollectionFromFacets(TestCase):
    cluster_data = {'clusters': [{'total': 11, 'center': {'lat': 49.360923272727284, 'lon': 8.507787999999998},
                                  'bottom_right': {'lat': 49.354773, 'lon': 8.513811},
                                  'top_left': {'lat': 49.363794, 'lon': 8.505933}},
                                 {'doc_type': 'mip_miprecord', 'total': 1, 'doc_id': '257',
                                  'center': {'lat': 49.339103, 'lon': 8.509797}},
                                 {'doc_type': 'mip_miprecord', 'total': 1, 'doc_id': '269',
                                  'center': {'lat': 51.42821, 'lon': 5.406714}}], '_type': 'geohash',
                    'factor': 0.6}
    facets = {'places': FacetResult('places', cluster_data)}

    def test__feature_collections_returns_a_mix_of_clusters_and_doc_ids(self):
        query = GeoS()
        features = query.get_feature_collection(self.facets)
        assert features['features'][0]['id'] is None
        assert features['features'][1]['id'] == '257'
        assert features['features'][1]['properties']['doc_type'] == 'mip_miprecord'

    raw_facets = {'gemeente.raw': FacetResult('places', cluster_data),
                  'plaats.raw': FacetResult('places', cluster_data)}

    def test__facets__remove_raw_suffixes(self):
        query = NaveESQuery()
        facet_clean = query.clean_facets(self.raw_facets)
        assert list(facet_clean.keys()) == ['gemeente', 'plaats']


class TestRobustContextManager(TestCase):
    def test__nave_query__with_robust_on_bad_query_param(self):
        query = NaveESQuery(size=16, robust_params=True)
        assert 'from' not in _query(query, {'page': 'sjoerd'})
        assert query.error_messages[0] == "param page: invalid literal for int() with base 10: 'sjoerd'"

    def test__nave_query__with_robust_false_on_bad_query_param(self):
        query = NaveESQuery(size=16, robust_params=False)
        with pytest.raises(ValueError):
            _query(query, {'page': 'sjoerd'})


@skip
class TestBuildQueryFromRequestParams(TestCase):

    def test_size_rows_returned(self):
        query = NaveESQuery(size=16)
        assert _query(query, {'rows': '10'})['size'] == 10

    def test_start_from_request(self):
        """ test_start_from_request """
        query = NaveESQuery(size=16)
        assert _query(query, {'start': '16'})['from'] == 16
        assert _query(query, {'start': '16', 'page': '3'})['from'] == 32

    def test_query_input_from_request(self):
        """ test_query_input_from_request """
        query = NaveESQuery()
        assert 'query' not in _query(query, {})
        assert _query(query, {'q': 'best'})['query'] == {'match': {'_all': 'best'}}

    def test_facet_from_request(self):
        """ test_facet_from_request """
        query = NaveESQuery(default_facets=['gemeente.raw'], cluster_geo=False)
        assert 'gemeente.raw' in _query(query, {})['facets']
        assert _steps(query, {'facet': ['straat.raw', 'plaats.raw', 'plaats.raw']})['facet'] == (
            ('gemeente.raw', 'straat.raw', 'plaats.raw'), {'filtered': True, 'size': 50})

    def test_default_filters(self):
        """ test_default_filters """
        query = NaveESQuery(default_filters=['gemeente.raw:best'])
        assert _query(query)['filter'] == {'term': {'gemeente.raw': 'best'}}
        query = NaveESQuery(default_filters=['gemeente.raw:best', 'plaats.raw:best'])
        assert _query(query)['filter'] == {'and': [{'term': {'gemeente.raw': 'best'}},
                                                   {'term': {'plaats.raw': 'best'}}]}
        query = NaveESQuery(default_filters=['gemeente.raw:best', 'gemeente.raw:mill', 'plaats.raw:best'])
        assert _query(query)['filter'] == {
            'and': [{'or': [{'term': {'gemeente.raw': 'mill'}}, {'term': {'gemeente.raw': 'best'}}]},
                    {'term': {'plaats.raw': 'best'}}]}

    def test_filters_from_request(self):
        """ test_filters_from_request """
        query = NaveESQuery()
        assert 'filter' not in _query(query)
        assert _query(query, {'qf': 'gemeente.raw:best'})['filter'] == {'term': {'gemeente.raw': 'best'}}
        query = NaveESQuery()
        assert _query(query, {'qf': 'gemeente.raw:best', 'qf[]': 'plaats.raw:best'})['filter'] == {
            'and': [{'term': {'gemeente.raw': 'best'}},
                    {'term': {'plaats.raw': 'best'}}]}


class TestGeoQueriesFromRequestParams(TestCase):
    def test__geo_query__with_bounding_box(self):
        query = NaveESQuery()
        assert 'filter' not in _query(query)
        query = NaveESQuery()
        bbox_query = _query(query, {"min_y": 49.350503, "min_x": 8.614178, "max_x": 49.321861, "max_y": 8.677397})
        assert bbox_query['filter']['geo_bounding_box'] == {
            'point': {'bottom_left': {'lat': 8.614178, 'lon': 49.350503},
                      'top_right': {'lat': 49.321861, 'lon': 8.677397}}}

    def test__geo_query_with_rd_bounding_box(self):
        query = NaveESQuery()
        bbox_query = _query(query, {"min_x": 411166, "min_y": 148702, "max_x": 41266, "max_y": 148702})
        assert bbox_query['filter']['geo_bounding_box'] == {
            'point': {'bottom_left': {'lat': 49.275407, 'lon': 8.906506},
                      'top_right': {'lat': 49.319371, 'lon': 3.823565}}}

    def test__geo_query__robustness_with_bad_bounding_box(self):
        query = NaveESQuery()
        bad_bbox_query = _query(query, {"min_x": 49.350503, "min_y": 8.614178, "max_x": 49.321861, "max_y": None})
        assert 'filter' not in bad_bbox_query
        query = NaveESQuery()
        bad_bbox_query = _query(query, {"min_x": "49.350503", "min_y": "8.614178", "max_x": "49.321861",
                                        "max_y": "string"})
        assert 'filter' not in bad_bbox_query
        query = NaveESQuery()
        bad_bbox_query = _query(query, {"min_x": "49.350503", "min_y": "8.614178", "max_x": "49.321861"})
        assert 'filter' not in bad_bbox_query

    def test__geo_query__with_geo_clustering(self):
        query = NaveESQuery(cluster_geo=True)
        assert _query(query)['facets']['places']['geohash'] == {'factor': 0.6, 'field': 'point', 'show_doc_id': True}
        assert _query(query, {'cluster.factor': '0.9'})['facets']['places']['geohash'] == {'factor': 0.9,
                                                                                           'field': 'point',
                                                                                           'show_doc_id': True}
        query = NaveESQuery(cluster_geo=False)
        assert 'facets' not in _query(query)

    def test__geo_query__build_from_params(self):
        query = NaveESQuery()
        assert _geo_query(query, {'start': '10', 'page': '1', 'facet': 'gemeente'}) == {
            'facets': {
                'places': {'facet_filter': None, 'geohash': {'factor': 0.6, 'field': 'point', 'show_doc_id': True}}},
            'size': 0}

    def test__geo_query__with_additional_filterning(self):
        query = NaveESQuery()
        assert _geo_query(query, {'start': '10', 'page': '1', 'facet': 'gemeente', 'qf': 'gemeente:best'}) == {
            'facets': {
                'places': {'facet_filter': {'term': {'gemeente.raw': 'best'}},
                           'geohash': {'factor': 0.6, 'field': 'point', 'show_doc_id': True}}}, 'filter': {
            'term': {'gemeente.raw': 'best'}}, 'size': 0}


class TestUserQuery(TestCase):

    def test__user_query__with_filters(self):
        query = NaveESQuery()
        query.facet_params = QueryDict('q=hoofdstraat&rows=5&facet=gemeente&facet=plaats&qf=gemeente:Best&qf=plaats:Best')

        user_query = UserQuery(query, 10)
        assert len(user_query.items) == 3
        assert user_query.items[0].value == 'hoofdstraat'
        assert not user_query.items[0].is_last
        assert user_query.items[2].is_last
        assert user_query.items[2].value == 'Best'
        assert user_query.items[2].field == 'plaats'
        assert user_query._num_found == 10
        assert user_query.terms == 'hoofdstraat'

    def test__user_query__without_filters(self):
        query = NaveESQuery()
        query.facet_params = QueryDict('q=hoofdstraat&rows=5&facet=gemeente&facet=plaats')

        user_query = UserQuery(query, 10)
        assert len(user_query.items) == 1
        assert user_query.items[0].value == 'hoofdstraat'
        assert user_query.items[0].is_last

    def test__user_query_serializer(self):
        query = NaveESQuery()
        query.facet_params = QueryDict('q=hoofdstraat&rows=5&facet=gemeente&facet=plaats&qf=gemeente:Best&qf=plaats:Best')
        user_query = UserQuery(query, 10)

    def test__breadcrumb__serializer(self):
        query = NaveESQuery()
        query.facet_params = QueryDict('q=hoofdstraat&rows=5&facet=gemeente&facet=plaats&qf=gemeente:Best&qf=plaats:Best')
        user_query = UserQuery(query, 10)


class TestFacets(TestCase):

    rf = RequestFactory()
    get_request = rf.get('/api/search/geo_cluster', {})
    get_request.GET = QueryDict('q=hoofdstraat&rows=5&page=1&facet=gemeente&facet=plaats&qf=gemeente:Best&qf=plaats:Best')

    query = NaveESQuery()
    query.build_query_from_request(get_request)

    test_facets = {
        'gemeente.raw': FacetResult('gemeente.raw', {'_type': 'terms', 'total': 73, 'terms': [{'count': 73, 'term': 'Best'}], 'other': 0,
                          'missing': 0}),
        'plaats.raw': FacetResult('plaats.raw', {'_type': 'terms', 'total': 67,
                        'terms': [{'count': 26, 'term': 'Vleut'}, {'count': 18, 'term': 'Best'},
                                   {'count': 11, 'term': 'Batadorp'}, {'count': 10, 'term': 'Aarle'},
                                   {'count': 2, 'term': 'Driehoek'}], 'other': 0, 'missing': 6}),
        'straat.raw': FacetResult('straat.raw', {'_type': 'terms', 'total': 73, 'terms': [{'count': 11, 'term': 'Oedenrodeseweg St.'},
                                                                     {'count': 6, 'term': 'Hoofdstraat'},
                                                                     {'count': 5, 'term': 'Batalaan'},
                                                                     {'count': 4, 'term': 'Nieuwstraat'},
                                                                     {'count': 4, 'term': 'Klaverhoekseweg'},
                                                                     {'count': 4, 'term': 'Kapelweg'},
                                                                     {'count': 4, 'term': 'Hoge Vleutweg'},
                                                                     {'count': 4, 'term': 'Broekstraat'},
                                                                     {'count': 3, 'term': 'Kerkhofpad'},
                                                                     {'count': 3, 'term': 'Europaplein'},
                                                                     {'count': 3, 'term': 'Aarleseweg'},
                                                                     {'count': 2, 'term': 'Margrietstraat, Prinses'},
                                                                     {'count': 2, 'term': 'Franciscusweg St.'},
                                                                     {'count': 2, 'term': 'Driehoekweg'},
                                                                     {'count': 2, 'term': 'Antoniusweg Sint'},
                                                                     {'count': 2, 'term': 'Annaweg Sint'},
                                                                     {'count': 2, 'term': 'Amsterdamsestraat'},
                                                                     {'count': 1, 'term': 'Molenstraat'},
                                                                     {'count': 1, 'term': 'Kruisparkweg'},
                                                                     {'count': 1, 'term': 'Kanaaldijk'},
                                                                     {'count': 1, 'term': 'Hokkelstraat'},
                                                                     {'count': 1, 'term': 'Hoefweg'},
                                                                     {'count': 1, 'term': 'Hoefkestraat'},
                                                                     {'count': 1, 'term': 'Hartstraat H.'},
                                                                     {'count': 1, 'term': 'Eindhovenseweg'},
                                                                     {'count': 1, 'term': 'Burgstraat'},
                                                                     {'count': 1, 'term': 'Broekdijk'}],
                        'other': 0,
                        'missing': 0})
    }

    def test__facet_count_links__when_selected(self):

        link = FacetCountLink('plaats', 'Best', 12, self.query)
        assert link.is_selected
        assert link.value == 'Best'
        assert link._filter_query == 'plaats:Best'
        assert link.link == 'q=hoofdstraat&facet=gemeente&facet=plaats&rows=5&qf=gemeente%3ABest'
        assert link.count == 12
        link_ser = FacetCountLinkSerializer(link)
        assert link_ser.data == {
            'url': 'q=hoofdstraat&facet=gemeente&facet=plaats&rows=5&qf=gemeente%3ABest',
            'isSelected': True, 'value': 'Best', 'count': 12, 'displayString': 'Best (12)'
        }

        link = FacetCountLink('gemeente', 'Eindhoven', 10, self.query)
        assert not link.is_selected
        assert link.link == 'q=hoofdstraat&facet=gemeente&facet=plaats&rows=5&qf=gemeente%3ABest&qf=plaats%3ABest&qf=gemeente%3AEindhoven'

        link_ser = FacetCountLinkSerializer(link)
        assert link_ser.data == {
            'url': 'q=hoofdstraat&facet=gemeente&facet=plaats&rows=5&qf=gemeente%3ABest&qf=plaats%3ABest&qf=gemeente%3AEindhoven',
            'isSelected': False, 'value': 'Eindhoven', 'count': 10, 'displayString': 'Eindhoven (10)'
        }

    def test__facet_query_links__when_selected(self):
        link = FacetLink('plaats', self.test_facets.get('plaats.raw'), self.query, 67, 6, 0)
        assert link.is_facet_selected
        assert link.total == 67
        assert link.missing_count == 0
        assert link.other_count == 6
        assert link.name == 'plaats'
        assert len(link.links) == 5
        assert len([count for count in link.links if count.is_selected]) == 1
        assert len([count for count in link.links if not count.is_selected]) == 4

        link_ser = FacetLinkSerializer(link)
        assert link_ser.data == {'name': 'plaats', 'isSelected': True, 'i18n': 'plaats', 'total': 67,
                                 'missingDocs': 0, 'otherDocs': 6, 'links': [{
                                                                             'url': 'q=hoofdstraat&facet=gemeente&facet=plaats&rows=5&qf=gemeente%3ABest&qf=plaats%3ABest&qf=plaats%3AVleut',
                                                                             'isSelected': False, 'value': 'Vleut',
                                                                             'count': 26,
                                                                             'displayString': 'Vleut (26)'}, {
                                                                             'url': 'q=hoofdstraat&facet=gemeente&facet=plaats&rows=5&qf=gemeente%3ABest',
                                                                             'isSelected': True, 'value': 'Best',
                                                                             'count': 18,
                                                                             'displayString': 'Best (18)'}, {
                                                                             'url': 'q=hoofdstraat&facet=gemeente&facet=plaats&rows=5&qf=gemeente%3ABest&qf=plaats%3ABest&qf=plaats%3ABatadorp',
                                                                             'isSelected': False, 'value': 'Batadorp',
                                                                             'count': 11,
                                                                             'displayString': 'Batadorp (11)'}, {
                                                                             'url': 'q=hoofdstraat&facet=gemeente&facet=plaats&rows=5&qf=gemeente%3ABest&qf=plaats%3ABest&qf=plaats%3AAarle',
                                                                             'isSelected': False, 'value': 'Aarle',
                                                                             'count': 10,
                                                                             'displayString': 'Aarle (10)'}, {
                                                                             'url': 'q=hoofdstraat&facet=gemeente&facet=plaats&rows=5&qf=gemeente%3ABest&qf=plaats%3ABest&qf=plaats%3ADriehoek',
                                                                             'isSelected': False, 'value': 'Driehoek',
                                                                             'count': 2,
                                                                             'displayString': 'Driehoek (2)'}]}

    def test__nave_facets__when_selected(self):
        facets = NaveFacets(self.query, self.test_facets)
        assert len(facets.facet_query_list) == 3
        gemeente = [link for link in facets.facet_query_list if link.name == 'gemeente'][0]
        assert gemeente.total == 73
        assert len(gemeente.links) == 1
        facet_names = [link.name for link in facets.facet_query_list]
        assert facet_names == ['gemeente', 'straat', 'plaats']

        facets_ser = NaveFacetSerializer(facets)
        assert list(facets_ser.data.keys()) == ["facets"]
        assert len(facets_ser.data.get('facets')) == 3


class TestNaveQueryResponse(TestCase):

    query = NaveESQuery(index_name=['brabantcloud'], doc_types=['mip_miprecord'])
    rf = RequestFactory()
    test_bbox = {'q': 'best', 'qf': ['gemeente:Best'], 'facet': ['gemeente, plaats']}
    get_request = rf.get('/api/search/v1', test_bbox)
    query.build_query_from_request(get_request)

    results = pickle.load(open(os.path.join(dirname(abspath(__file__)), 'resources', 'es_results.p'), 'rb'))

    def test__user_query__with_filters(self):
        response = NaveQueryResponse(self.query)
        response._results = self.results
        assert response.user_query.num_found == 73
        assert response.user_query.terms == 'best'
        assert len(response.user_query._items) == 2

    def test__user_query__serializer(self):
        response = NaveQueryResponse(self.query)
        response._results = self.results
        serializer = UserQuerySerializer(response.user_query)
        assert serializer.data == {'numfound': 73, 'terms': 'best', 'breadCrumbs': [
            {'href': 'q=best&facet=gemeente%2C+plaats', 'display': 'best', 'field': '', 'localised_fied': '',
             'value': 'best', 'is_last': False},
            {'href': 'q=best&facet=gemeente%2C+plaats&qf=gemeente%3ABest', 'display': 'gemeente:Best',
             'field': 'gemeente', 'localised_fied': 'gemeente', 'value': 'Best', 'is_last': True}]}

    def test__facets__with_filters(self):
        response = NaveQueryResponse(self.query)
        response._results = self.results
        assert isinstance(response.facets, NaveFacets)
        assert len(response.facets.facet_query_list) == 2

    def test__nave_query_response__serialized(self):
        response = NaveQueryResponse(self.query)
        response._results = self.results
        assert isinstance(response.facets, NaveFacets)
        serializer = NaveQueryResponseSerializer(response)
        print(serializer.data)
        assert 'facets' in serializer.data
        assert 'pagination' in serializer.data
        assert 'query' in serializer.data

    def test__pagination__serialized(self):
        response = NaveQueryResponse(self.query)
        response._results = self.results
        assert isinstance(response.pagination, QueryPagination)
        pagination = response.pagination
        assert pagination.first_page == 1
        assert not pagination.has_previous
        assert pagination.first_page == 1
        assert pagination.last_page == 5
        assert pagination.start == 1
        assert len(pagination.links) == 5
        pagination_ser = QueryPaginationSerializer(pagination).data
        assert list(pagination_ser.keys()) == ['start',
                                         'rows',
                                         'numFound',
                                         'hasNext',
                                         'nextPage',
                                         'nextPageNumber',
                                         'hasPrevious',
                                         'previousPage',
                                         'previousPageNumber',
                                         'firstPage',
                                         'lastPage',
                                         'links']



