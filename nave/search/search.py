"""All ES query related functionality goes into this module."""
import collections
import itertools
import logging
import re
import copy
import urllib.error
import urllib.parse
from collections import defaultdict, namedtuple
from contextlib import contextmanager

from django.conf import settings
from django.core.cache import caches
from django.core.paginator import Paginator, Page, EmptyPage, PageNotAnInteger
from django.http import QueryDict
from elasticsearch_dsl import Search, aggs, A
from elasticsearch_dsl.query import Q, Match
from elasticsearch_dsl.result import Result
from rest_framework.request import Request
import six

from nave.void.convertors import BaseConverter
from nave.search.utils import gis
from nave.search.connector import paging_cache


logger = logging.getLogger(__name__)


class NaveESQuery(object):
    """
    This class builds ElasticSearch queries from default settings and HTTP request as provided by Django

    """

    def __init__(self, index_name=None, doc_types=None, default_facets=None, size=16,
                 default_filters=None, hidden_filters=None, cluster_geo=False, geo_query=False, robust_params=True,
                 facet_size=50, converter=None, acceptance=False):
        self.acceptance = acceptance
        self.index_name = index_name
        self.doc_types = doc_types
        self.default_facets = default_facets.copy() if default_facets is not None else []
        self.size = size
        self.default_filters = default_filters
        self.hidden_filters = hidden_filters
        self.applied_filters = None
        self.robust_params = robust_params
        self.facet_size = facet_size
        self.cluster_geo = cluster_geo
        self.geo_query = geo_query
        self.cluster_factor = 3
        self.error_messages = []
        self.query = self._create_query()
        self.base_params = None
        self.facet_params = None
        self._is_item_query = False
        self.page = 1
        self.converter = converter
        self.non_legacy_keys = ['delving_deepZoomUrl', 'delving_geohash', 'delving_year', 'delving_thumbnail',
                                'delving_fullTextObjectUrl', 'delving_fullText', 'delving_geohash', 'delving_spec']

    @staticmethod
    def _as_list(param):
        """ always return params as list

        >>> NaveESQuery._as_list('sjoerd')
        ['sjoerd']

        >>> NaveESQuery._as_list(['sjoerd'])
        ['sjoerd']
        """
        if isinstance(param, list):
            params = param
        elif isinstance(param, str):
            params = [param]
        else:
            raise ValueError('this type {} is not supported'.format(type(param)))
        return list(set(params))

    def _filters_as_dict(self, filters, filter_dict=None, exclude=None):
        """
        >>> query = NaveESQuery()
        >>> query._filters_as_dict(['gemeente:best'])
        defaultdict(<type 'set'>, {'gemeente': set(['best'])})

        >>> query._filters_as_dict(['gemeente:best', 'gemeente:son en breugel'])
        defaultdict(<type 'set'>, {'gemeente': set(['son en breugel', 'best'])})


        >>> query._filters_as_dict(['gemeente:best', 'plaats:best'])
        defaultdict(<type 'set'>, {'gemeente': set(['best']), 'plaats': set(['best'])})
        """

        def is_excluded(key):
            clean_key = key.replace('.raw', '')
            return clean_key in exclude

        if filter_dict is None:
            filter_dict = defaultdict(set)
        if not isinstance(filter_dict, defaultdict):
            raise TypeError('filter_dict should be be a defaultdict(set)')

        # flatten nested list

        if filters and isinstance(filters[0], list):
            filters = filters[0]

        for filt in filters:
            if exclude and is_excluded(filt):
                continue
            elif not filt:
                continue
            elif ":" in filt:
                key, *value = filt.split(":")
                key = key.replace('_facet', '').replace('_string', '').replace('_text', '')
                if key.startswith('delving_') and key not in self.non_legacy_keys:
                    key = "legacy.{}".format(key)
                filter_dict[key].add(":".join(value).replace("\"", "'"))
            else:
                # add support for query based filters
                filter_dict['query'].add(filt)
        return filter_dict

    @staticmethod
    def _clean_params(param_dict):
        """
        >>> from django.http import QueryDict
        >>> query = NaveESQuery()
        >>> query._clean_params(QueryDict('qf=gemeente:best&qf[]=plaats:best').copy()).getlist('qf')
        [u'gemeente:best', u'plaats:best']

        >>> from django.http import QueryDict
        >>> list(query._clean_params(QueryDict('qf[]=plaats:best').copy())['qf'])
        [u'plaats:best']

        """
        for key in ["qf[]", 'hqf[]',
                    'facet.field[]', 'facet.field',
                    'facet_field']:
            replace_key = key.rstrip('[]')
            if replace_key.endswith('field'):
                replace_key = "facet"
            if key in param_dict:
                query_filters = param_dict.getlist(key)
                for query_filter in query_filters:
                    if replace_key == "facet":
                        clean_query_filter = query_filter.replace("_facet", ".raw")
                        param_dict.appendlist(replace_key, clean_query_filter)
                    else:
                        param_dict.appendlist(replace_key, query_filter)
                del param_dict[key]

        # also remove other stuff generated by JQuery
        for k, v in list(param_dict.items()):
            if k.startswith('_'):
                del param_dict[k]

        return param_dict

    @property
    def facet_list(self):
        if self.default_facets is None:
            return []
        return [facet.es_field for facet in self.default_facets]

    @staticmethod
    def apply_converter_rules(query_string, converter, as_query_dict=True, reverse=False):
        replace_dict = converter.query_key_replace_dict(reverse=reverse)
        for key, val in replace_dict.items():
            if isinstance(query_string, list):
                query_string = "&".join(query_string).replace(key, val)
            else:
                query_string = query_string.replace(key, val)
        # defaults
        if reverse:
            query_string = re.sub("([&?])q=", "\\1query=", query_string)
        else:
            query_string = re.sub("([&?])query=", "\\1q=", query_string)
        if '=delving_recordType' in query_string:
            query_string = query_string.replace(
                '=delving_recordType',
                '=legacy.delving_recordType'
            )
        if 'delving_recordType:' in query_string:
            query_string = query_string.replace(
                'delving_recordType:',
                'delving_recordType_facet:'
            )
        if as_query_dict:
            return QueryDict(query_string)
        return query_string

    @property
    def get_index_name(self):
        if not self.index_name:
            logger.warn("There should always we a index name defined.")
            return None
        if self.acceptance and self.index_name == settings.SITE_NAME:
            return "{}_acceptance".format(settings.SITE_NAME)
        return self.index_name

    def _create_query(self):
        query = Search()
        if self.get_index_name:
            query = query.index(*self._as_list(self.get_index_name))
        if self.doc_types:
            query = query.doc_type(*self._as_list(self.doc_types))
        return query

    def _create_query_string(self, query_string):
        if self._is_fielded_query(query_string):
            query_string = self._created_fielded_query(query_string)
            query = {
                "query_string": {
                    "default_field": "_all",
                    "query": query_string,
                    "auto_generate_phrase_queries": True,
                }
            }
        else:
            query = {
                "query_string": {
                    "default_field": "_all",
                    "query": query_string,
                    "auto_generate_phrase_queries": True,
                    # "default_operator": "AND",
                    "minimum_should_match": "2<50%"
                }
            }
        return query

    @staticmethod
    def _is_fielded_query(query_string):
        matcher = re.compile(r"[_a-zA-Z0-9\.]+:[\S]|\sNOT\s|\sAND\s|\sOR\s")
        return True if matcher.search(query_string) else False

    def _created_fielded_query(self, query_string):
        def multiple_replace(mapping, text):
            # Create a regular expression  from the dictionary keys
            regex = re.compile("(%s)" % "|".join(map(re.escape, mapping.keys())))

            # For each match, look-up corresponding value in dictionary
            return regex.sub(lambda mo: mapping[mo.string[mo.start():mo.end()]], text)

        mapping_dict = {
            "_text:": ".value:",
            "_facet:": ".raw:",
            "_string:": ".raw:",
            "(.*?_geohash):": "point:",
        }
        query_string = multiple_replace(mapping_dict, query_string)
        # default fielded query is to .value
        query_string = re.sub(r"([\w]+)_([\w]+):", r"\1_\2.value:", query_string)
        if "delving_spec.value" in query_string:
            query_string = query_string.replace("delving_spec.value", "system.spec.raw")
        elif "delving_" in query_string:
            exclude = "(delving_{}[a-zA-Z]+).value:".format(
                "".join(["(?!{})".format(key) for key in self.non_legacy_keys]))
            query_string = re.sub(exclude, "legacy.\\1.value:", query_string)
        return query_string

    @staticmethod
    def param_is_valid(key, params):
        param_key_list = params.get(key, [])
        is_valid = False
        if isinstance(param_key_list, list):
            is_valid = all(not param.isspace() for param in param_key_list)
        elif isinstance(param_key_list, str):
            is_valid = not param_key_list.isspace()
        return param_key_list and is_valid

    def __repr__(self):
        return str(self.query.to_dict())

    def build_query(self):
        if self.default_facets:
            for facet in self.facet_list:
                fsize = facet.facet_size
                self.query = self.query.facet(facet, size=fsize)
            # self.query = self.query.facet(*self._as_list(self.facet_list), size=self.facet_size)
        if self.default_filters:
            self.query = self.query.filter(*self._as_list(self.default_filters))
        return self.query

    nave_id_pattern = re.compile("^([^_]*?)_([^_]+?)__([^_]+)$")
    hub_id_pattern = re.compile("^([^_]*?)_(.*?)_([^_]+)$")

    def build_item_query(self, query, params, hub_id=None):
        if hub_id or 'id' in params:
            #  todo add support for idType later
            clean_id = hub_id if hub_id else params.get('id')
            if self.nave_id_pattern.findall(clean_id):
                doc_type, clean_id = clean_id.split('__')
                query = query.query.query(Q("ids", values=[clean_id], type=doc_type))
                self._is_item_query = True
            elif self.hub_id_pattern.findall(clean_id):
                from nave.lod.utils.resolver import RDFRecord
                clean_id = RDFRecord.clean_local_id(clean_id, is_hub_id=True)
                if settings.ID_QUERY_CASE_INSENSITIVE:
                    query = query.query.query(self._create_query_string("nave_id.value:{}".format(clean_id)))
                else:
                    query = query.query.query(Q("ids", values=[clean_id]))
                self._is_item_query = True
            else:
                raise ValueError("unknown clean_id type: {}".format(clean_id))
        return query

    @staticmethod
    def expand_params(param):
        key = param[0]
        value_list = param[1]
        return [(key, value) for value in value_list]

    def create_filter_query(self, field, values, operator='OR', negative=False):
        """Build a filter query"""
        formatter = '" {} "'.format(operator)
        query = '"{}"'.format(formatter.join(values))
        q = Q('query_string', default_field=field, query=query)
        return q if not negative else ~q

    def build_query_from_request(self, request, raw_query_string=None):

        @contextmanager
        def robust(key):
            try:
                yield
            except ValueError as ve:
                self.error_messages.append("param {}: {}".format(key, str(ve)))
                logger.warn(
                    "problem with param {} causing {} for request {}"
                    .format(key, ve, request.build_absolute_uri())
                )
                # if not self.robust_params:
                #     raise
                raise



        query = self.query
        if isinstance(request, Request):
            request = request._request

        # add ip based filters to hidden filters
        from nave.lod.utils.resolver import RDFRecord
        ip_filters = RDFRecord.get_filters_by_ip(request)
        if ip_filters:
            for spec in ip_filters:
                self.hidden_filters.append('-delving_spec:{}'.format(spec))

        query_string = raw_query_string if raw_query_string else request.META['QUERY_STRING']
        if self.converter is not None:
            query_dict = self.apply_converter_rules(query_string, self.converter)
        elif raw_query_string:
            query_dict = QueryDict(query_string=query_string)
        else:
            query_dict = request.query_params if isinstance(request, Request) else request.GET

        params = self._clean_params(query_dict.copy())
        facet_params = self._clean_params(query_dict.copy())

        if 'facet.limit' in params and params['facet.limit']:
            try:
                self.facet_size = int(params['facet.limit'])
            except ValueError as ve:
                logger.warn("Unable to use facet.limit: {}".format(params['facet.limit']))

        if 'facet.reset' in params:
            self.default_facets = []


        # build id based query
        query = self.build_item_query(query, params)
        if self._is_item_query:
            return query

        # remove non filter keys
        for key, value in list(facet_params.items()):
            if key in ['start', 'page', 'rows', 'format', 'diw-version', 'lang', 'callback',
                       'facetBoolType', 'facet.limit']:
                del facet_params[key]
            if not value and key in facet_params:
                del facet_params[key]

        # implement size
        if 'rows' in params:
            with robust('rows'):
                self.size = int(params.get('rows'))
        # implement paging
        if 'page' in params:
            with robust('page'):
                page = int(params.get('page'))
                self.page = page
                start = (page - 1) * self.size if page > 0 else 0
                end = start + self.size
                if end >= 10000:
                    logger.warn("Switching to search after regular paging will break on this result window.")
                    # import pdb; pdb.set_trace()
                    # build new key from params and get cache
                    # if not not found got to page 1000*10 set cache key and start paging
                    # TODO add .extra search after
                # else:
                query = query[start:end]
        elif 'start' in params and 'page' not in params:
            with robust('start'):
                start = int(params.get('start'))
                diw_version = params.get("diw-version")
                if diw_version and not diw_version.startswith("1.4"):
                    start = start - 1
                    if start < 1:
                        start = 0
                page = int(start / self.size) + 1
                if page > 0:
                    self.page = page
                end = start + self.size
                if end >= 10000:
                    # build new key from params and get cache
                    # if not not found got to page 1000*10 set cache key and start paging
                    logger.warn("Switching to search after regular paging will break on this result window.")
                    # TODO add .extra search after
                # else:
                query = query[start:end]
        else:
            query = query[:self.size]


        # add hidden filters
        exclude_filter_list = params.getlist("pop.filterkey")
        hidden_filter_dict = self._filters_as_dict(
            self.hidden_filters,
            exclude=exclude_filter_list
        ) if self.hidden_filters else defaultdict(set)
        hidden_queries = hidden_filter_dict.pop("query", [])

        # update key
        if 'query' in params and 'q' not in params:
            params['q'] = params.get('query')

        if self.param_is_valid('q', params) and not params.get('q') in ['*:*']:
            query_string = params.get('q')

            if "&quot;" in query_string:
                query_string = query_string.replace('&quot;', '"')
            for hq in hidden_queries:
                query_string = "({}) AND ({})".format(query_string, hq)
            query = query.query(self._create_query_string(query_string))
        # add lod_filtering support
        # elif "lod_id" in params:
            # lod_uri = params.get("lod_id")
            # todo implement this filter with elastic dsl
            # query = query.query(
            #         **{'rdf.object.id': lod_uri, "must": True}).filter(~Q(**{'system.about_uri': lod_uri}))
        elif hidden_queries:
            query = query.query(self._create_query_string(" ".join(hidden_queries)))
        else:
            query = query.query()

        # add filters
        filter_dict = self._filters_as_dict(self.default_filters) \
                if self.default_filters else defaultdict(set)
        if 'qf' in params:
            with robust('qf'):
                self._filters_as_dict(params.getlist('qf'), filter_dict)


        if 'hqf' in params:
            with robust('hqf'):
                hqf_list = params.getlist('hqf')
                self._filters_as_dict(
                    filters=hqf_list,
                    filter_dict=hidden_filter_dict,
                    exclude=exclude_filter_list
                )
                facet_params.pop('hqf')

        facet_bool_type_and = False
        if "facetBoolType" in params:
            facet_bool_type_and = params.get('facetBoolType').lower() in ['and']

        # create hidden query filter filter on the ES query
        hidden_facet_filter_dict = defaultdict(list)
        hidden_filter_list = []
        if hidden_filter_dict:
            for key, values in list(hidden_filter_dict.items()):
                hidden_facet_filter_list = hidden_facet_filter_dict[key]
                for value in values:
                    facet_key = self.query_to_facet_key(key)
                    if key.startswith('-'):
                        hidden_facet_filter_list.append(~Match(**{facet_key: {'query': value, 'type': 'phrase'}}))
                    else:
                        hidden_facet_filter_list.append(Match(**{facet_key: {'query': value, 'type': 'phrase'}}))
                if facet_bool_type_and or key.startswith('-'):
                    q = Q('bool', must=hidden_facet_filter_list)
                    hidden_filter_list.append(q)
                else:
                    q = Q('bool', should=hidden_facet_filter_list)
                    hidden_filter_list.append(q)
            query = query.filter('bool', must=hidden_filter_list)
        # define applied filters
        self.applied_filters = filter_dict
        applied_facet_fields = []

        # add facets
        facet_list = self._as_list(self.facet_list) if self.default_facets else []
        if 'facet' in params:
            with robust('facet'):
                facets = params.getlist('facet')
                for facet in facets:
                    facet = facet.replace('_facet', '').replace('_string', '').replace('_text', '')
                    if ',' in facet:
                        facet_list.extend(facet.split(','))
                    else:
                        facet_list.append(facet)

        # add facets to config
        # add non default facets to the bottom intersection from keys
        for facet in set(facet_list).difference(set(self.facet_list)):
            from nave.base_settings import FacetConfig
            self.default_facets.append(FacetConfig(
                es_field=facet,
                label=facet,
                size=self.facet_size
            )
        )
        facet_filter_dict = defaultdict(list)
        # this one should be used in the facets and exclude the field name.
        all_filter_list = []
        all_filter_dict = {}
        if filter_dict:
            applied_facet_fields = {key.lstrip('-+').replace('.raw', '') for key in filter_dict.keys()}
            all_filter_list = []
            for key, values in list(filter_dict.items()):
                facet_filter_list = facet_filter_dict[key]
                facet_key = self.query_to_facet_key(key)
                operator = 'OR' if not facet_bool_type_and else 'AND'
                filter_query = self.create_filter_query(
                    facet_key,
                    values,
                    operator,
                    key.startswith('-')
                )
                all_filter_list.append(filter_query)
                all_filter_dict[key] = filter_query
            query = query.post_filter('bool', must=all_filter_list)
        # create facet_filter_dict with queries with key for each facet entry
        if self.default_facets:
            with robust('facet'):
                if 'facet.size' in params:
                    self.facet_size = int(params.get('facet.size'))
                # add .raw if not already there
                # facet_list = ["{}.raw".format(facet.rstrip('.raw')) for facet in facet_list]
                for facet_config in self.default_facets:
                    facet = facet_config.es_field
                    if not facet_bool_type_and:
                        facet_filter_list = [filters for key, filters in all_filter_dict.items() if not self.check_facet_key(facet, key)]
                    else:
                        facet_filter_list = list(all_filter_dict.values())
                    a = aggs.Filter(
                        Q('bool', must=facet_filter_list)
                    )
                    lsize = facet_config.size
                    if 'facet.size' in params:
                        lsize = self.facet_size
                    a.bucket(
                        facet,
                        'terms',
                        field=facet,
                        size=lsize,
                    )
                    # create an aggregation
                    # add it as a bucket
                    query.aggs.bucket(facet, a)
        # # add clusters
        if self.cluster_geo:
            with robust('geo_cluster'):
                factor = 3
                if 'cluster.factor' in params:
                    factor = int(params.get('cluster.factor'))
                facet_filter_list = []
                filtered = bool(params.get('cluster.filtered')) if 'cluster.filtered' in params else True
                if filtered:
                    if facet_bool_type_and:
                        facet_filter_list = list(itertools.chain.from_iterable(facet_filter_dict.values()))
                    else:
                        or_filter_list = [filters for key, filters in facet_filter_dict.items() if not self.check_facet_key(facet, key)]
                        facet_filter_list = list(itertools.chain.from_iterable(or_filter_list))
                a = A(
                    'geohash_grid',
                    field='point',
                    precision=factor
                )
                query.aggs.bucket('geo_clusters', a)
        # old solr style bounding box query
        bbox_filter = None
        if {'pt', 'd'}.issubset(list(params.keys())):
            point = params.get('pt')
            distance = params.get('d')
            query = query.filter(
                Q('geo_distance', distance=distance, point=point)
            )
        # # add bounding box
        bounding_box_param_keys = gis.BOUNDING_BOX_PARAM_KEYS
        if set(bounding_box_param_keys).issubset(list(params.keys())):
            with robust(str(bounding_box_param_keys)):
                boundingbox_params = {key: val for key, val in list(params.items()) if key in bounding_box_param_keys}
                bounding_box = gis.get_lat_long_bounding_box(boundingbox_params)
                if bounding_box:
                    bbox_filter = gis.create_bbox_filter(bounding_box)
                    query = query.filter(
                        bbox_filter
                    )
        if self.geo_query:
            query = query.filter({"match": {"delving_hasGeoHash": True}})
        if 'sortBy' in params:
            sort_key = params.get('sortBy')
            if sort_key.startswith('random_'):
                seed = None
                random_sort = {'random_score': {}}
                seed = sort_key.split('_')[-1]
                random_sort['random_score']['seed'] = seed
                query = query.query({'function_score': random_sort})
            elif sort_key.startswith('random'):
                from random import randint
                seed = randint(0, 100)
                random_sort = {'random_score': {}}
                random_sort['random_score']['seed'] = seed
                query = query.query({'function_score': random_sort})
            else:
                if not sort_key.endswith(".raw"):
                    sort_key = sort_key + ".raw"
                sort_order = params.get('sortOrder')
                order = "desc" if sort_order and sort_order.lower() != "asc" else "asc"
                query = query.sort({
                    sort_key: {"order": order},
                    "legacy.delving_hubId": {"order": "desc"},
                    "system.modified_at": {"order": "desc"},
                })
        else:
            query = query.sort({
                "_score": {"order": "desc"},
                "legacy.delving_hubId": {"order": "desc"},
                "system.modified_at": {"order": "desc"},
            })

        if hasattr(settings, 'DEMOTE') and hasattr(settings, 'NEGATIVE_BOOST'):
            query = query.query(
                Q('boosting',
                    positive=Q(),
                    negative=Q("match", **settings.DEMOTE),
                    negative_boost=settings.NEGATIVE_BOOST
                  )
            )
        self.query = query
        self.facet_params = facet_params
        self.base_params = params

        import json
        logger.debug(json.dumps(query.to_dict()))
        # print(json.dumps(query.to_dict(), indent=4, sort_keys=True))
        return query

    def check_facet_key(self, facet, key):
        """Check if the key and facet match."""
        clean_facet = facet.split('.', maxsplit=1)[0]
        return clean_facet == key

    def build_geo_query(self, request):
        """ build a query for geo clustering only """
        params = request.GET.copy()
        # remove unnecessary keys
        for key in ['start', 'page', 'facet']:
            if key in params:
                params.pop(key)
        self.default_facets = []
        self.cluster_geo = True
        params['rows'] = 0
        request.GET = params
        query = self.build_query_from_request(request)
        return query

    def get_geojson_generator(self, request, max=None):
        """Return generator for Leaflet map clustering.

        """
        params = request.GET.copy()
        # remove unnecessary keys
        for key in ['start', 'page', 'facet']:
            if key in params:
                params.pop(key)
        self.default_facets = []
        request.GET = params
        search = self.build_query_from_request(request)
        # search.aggs = None
        search = search.source(include=['wgs84_pos_lat', 'wgs84_pos_long'])
        search = search.filter(
            {'exists': {'field': 'wgs84_pos_lat'}}
        ).filter(
            {'exists': {'field': 'wgs84_pos_long'}}
        )
        res = search.scan()
        seen = 0
        yield 'var edmPoints = [\n'
        for rec in res:
            lat_long = zip(rec.wgs84_pos_lat, rec.wgs84_pos_long)
            for lat, lon in lat_long:
                if lat and lon:
                    seen += 1
                    yield '[{}, {}, "{}"],\n'.format(
                            lat.raw, lon.raw, rec.meta.id
                    )
            if max and seen > max:
                break
        yield ']\n'

    def query_to_facet_key(self, facet_key):
        if facet_key.startswith('delving_spec'):
            facet_key = "system.spec.raw"
        elif facet_key.startswith('delving_') and facet_key not in self.non_legacy_keys:
            facet_key = 'legacy.{}'.format(facet_key)
        if "." not in facet_key:
            facet_key = "{}.raw".format(facet_key)
        return facet_key.lstrip('-+')

    @staticmethod
    def clean_facets(facet_dict):
        """
        Remove all .raw extensions from the facet name
        :param facet_dict:
        :return:

        """
        for key in list(facet_dict.keys()):
            if key.endswith('.raw'):
                facet_dict[key.replace('.raw', '')] = facet_dict.pop(key)
        return facet_dict


class FacetCountLink(object):
    def __init__(self, facet_name, value, count, query):
        self._value = value
        self._count = count
        self._name = facet_name
        self._clean_name = None
        self._query = query
        self._filter_query = "{}:{}".format(self._get_clean_name, self._value)
        self._facet_params = self._query.facet_params.copy()
        self._is_selected = self._set_is_selected()
        self._link = None
        self._full_link = None

    @property
    def _get_clean_name(self):
        if not self._clean_name:
            if self._query.converter:
                self._clean_name = self._query.apply_converter_rules(
                    query_string=self._name,
                    converter=self._query.converter,
                    as_query_dict=False,
                    reverse=False
                )
            else:
                self._clean_name = self._name
        return self._clean_name

    def _set_is_selected(self):
        filter_query = self._filter_query
        filter_params = self._facet_params.getlist('qf')
        return filter_query in filter_params

    @property
    def value(self):
        return self._value

    @property
    def count(self):
        return self._count

    @property
    def full_link(self):
        if not self._full_link:
            query = self._query.base_params.get('q', "")
            self._full_link = "?q={}&{}".format(query, self.link.lstrip('&?'))
        return self._full_link

    @property
    def link(self):
        if not self._link:
            facet_params = self._facet_params.copy()
            for key, value in list(facet_params.items()):
                if key in ['start', 'page', 'rows', 'format', 'diw-version', 'lang', 'callback', 'query', 'q',
                           'facet.limit', 'facetBoolType', 'facet', 'facet.reset']:
                    del facet_params[key]
                if not value and key in facet_params:
                    del facet_params[key]
            selected_facets = self._facet_params.getlist('qf')
            # todo: later replace the replace statements with urlencode() as well for query filters
            if facet_params:
                link = "{}&qf[]={}".format(
                    facet_params.urlencode().replace('qf=', 'qf[]='),
                    self._filter_query.replace(":", "%3A").replace("&", "%26").replace(';', '%3B')
                )
            else:
                link = "qf[]={}".format(
                    self._filter_query.replace(":", "%3A").replace("&", "%26").replace(';', '%3B')
                )
            if self.is_selected:
                selected_facets = [facet for facet in selected_facets if facet != self._filter_query]
                facet_params.setlist('qf', selected_facets)
                link = "{}".format(facet_params.urlencode())
            if not link:
                return ""
            if self._query.converter:
                link = self._query.apply_converter_rules(
                    query_string=link,
                    converter=self._query.converter,
                    as_query_dict=False,
                    reverse=True
                )
                self._link = link if link.startswith("&") else "&{}".format(link)
            else:
                self._link = link if link.startswith("?") else "?{}".format(link)
        return self._link

    @property
    def url(self):
        """
        Convenience function to be backwards compatible with CultureHub API
        """
        return self.link

    @property
    def display_string(self):
        return "{} ({})".format(self.value, self.count)

    @property
    def is_selected(self):
        return self._is_selected

    def __repr__(self):
        return self._filter_query

    def __str__(self):
        return "{} ({})".format(self._filter_query, self._count)


class FacetLink(object):
    def __init__(self, name, facet_terms, query, total=0, other=0,
                 missing=0, doc_count=0):
        self._name = name
        self._clean_name = None
        self._i18n = None
        self._doc_count = doc_count
        self._total = total
        self._other = other
        self._missing = missing
        self._query = query
        self._facet_terms = facet_terms
        self._is_selected = False
        self._facet_count_links = self._create_facet_count_links()

    def _create_facet_count_links(self):
        facet_count_links = []
        for term in self._facet_terms.buckets:
            count = term.doc_count
            value = term.key
            facet_count_links.append(
                    FacetCountLink(self._name, value, count, self._query)
            )
        return facet_count_links

    def __str__(self):
        return "{} ({})".format(self._name, self._total)

    def __repr__(self):
        return "{}".format(self._name)

    @property
    def name(self):
        return self._name

    @property
    def i18n(self):
        if not self._i18n:
            self._i18n = BaseConverter.get_translated_field(self._get_clean_name)
        return self._i18n

    @property
    def total(self):
        return self._total

    @property
    def links(self):
        return self._facet_count_links

    @property
    def link(self):
        return self._facet_count_links

    @property
    def _get_clean_name(self):
        if not self._clean_name:
            facet_name = self._name
            if any([facet_name.endswith(legacy_suffix) for legacy_suffix in ['_string', '_facet', '_text']]):
                facet_name = "_".join(facet_name.split("_")[:-1])
            if self._query.converter:
                facet_name = self._query.apply_converter_rules(
                    query_string=facet_name,
                    converter=self._query.converter,
                    as_query_dict=False,
                    reverse=False
                )
            self._clean_name = facet_name
        return self._clean_name

    @property
    def is_facet_selected(self):
        if not self._is_selected:
            facet_name = self._get_clean_name
            applied_filter_keys = self._query.applied_filters.keys()
            self._is_selected = facet_name in list(applied_filter_keys)
        return self._is_selected

    @property
    def is_selected(self):
        return self.is_facet_selected

    @property
    def missing_count(self):
        return self._missing

    @property
    def other_count(self):
        return self._other


class NaveFacets(object):
    def __init__(self, nave_query, facets):
        self._nave_query = nave_query
        self._facets = NaveFacets._respect_facet_config_ordering(facets, nave_query.default_facets)
        self._facet_querylinks = self._create_facet_query_links()

    @staticmethod
    def _respect_facet_config_ordering(facets, facet_order):
        if not facet_order:
            facet_order = settings.FACET_CONFIG
        ordered_dict = collections.OrderedDict()
        for facet in facet_order:
            if facet.es_field in facets:
                ordered_dict[facet.es_field] = facets[facet.es_field]
        return ordered_dict

    def _create_facet_query_links(self):
        facet_query_links = collections.OrderedDict()
        for key in self._facets:
            if key in ['places.raw']:
                continue
            clean_name = key.replace('.raw', '')
            if self._nave_query.converter:
                clean_name = self._nave_query.apply_converter_rules(
                        query_string=clean_name,
                        converter=self._nave_query.converter,
                        as_query_dict=False,
                        reverse=True
                )
                clean_name = "{}_facet".format(clean_name)
            facet = self._facets[key]
            doc_count = facet.doc_count
            facet = facet[key]
            other_docs = facet.sum_other_doc_count
            total = len(facet.buckets) + other_docs
            facet_query_link = FacetLink(
                name=clean_name,
                total=total,
                # todo: replace later with count facet.total,facet.missing,
                missing=0,
                other=other_docs,
                query=self._nave_query,
                facet_terms=facet,
                doc_count=doc_count
            )
            facet_query_links[key] = facet_query_link
        return facet_query_links

    @property
    def facet_query_list(self):
        return list(self._facet_querylinks.values())

    @property
    def facet_query_dict(self):
        return self._facet_querylinks

    @property
    def raw_facets(self):
        return self._facets


BreadCrumb = namedtuple('BreadCrumb', ['href', 'display', 'field', 'localised_field', 'value', 'is_last'])


class UserQuery(object):
    def __init__(self, query, num_found):
        self._query = query
        self._query_string = None
        self._num_found = num_found
        self._items = self._create_breadcrumbs()

    def expand_params(self, param):
        key = param[0]
        if key in ['q'] and self._query.converter:
            key = "query"
        value_list = param[1]
        expanded_params = []
        for value in value_list:
            clean_value = value
            if self._query.converter:
                clean_value = self._query.apply_converter_rules(
                        query_string=clean_value,
                        converter=self._query.converter,
                        as_query_dict=False,
                        reverse=True
                )
            expanded_params.append((key, clean_value))
        return expanded_params

    def _create_breadcrumbs(self):
        breadcrumbs = []
        filters = ['qf', 'qf[]']
        base_params = [param for params in self._query.facet_params.lists() for param in self.expand_params(params) if
                       param[0] not in filters]
        filter_params = [param for params in self._query.facet_params.lists() for param in self.expand_params(params) if
                         param[0] in filters]
        query = BreadCrumb(
                href=urllib.parse.urlencode(base_params),
                display=self.terms,
                field="",
                localised_field="",
                value=self.terms,
                is_last=False
        )
        breadcrumbs.append(query)
        for filt in filter_params:
            base_params.append(filt)
            breadcrumbs.append(
                    BreadCrumb(
                            href=urllib.parse.urlencode(base_params),
                            display=filt[1],
                            field=filt[1].split(":")[0],
                            localised_field=BaseConverter.get_translated_field(filt[1].split(":")[0]),
                            value=":".join(filt[1].split(":")[1:]),
                            is_last=False
                    )
            )
        # mark last as last
        last = breadcrumbs[-1]._replace(is_last=True)
        if len(base_params) == 1:
            breadcrumbs = [last]
        else:
            breadcrumbs = breadcrumbs[:-1] + [last]
        return breadcrumbs

    @property
    def terms(self):
        if not self._query_string:
            self._query_string = self._query.base_params.get('q', "")
        if self._query.converter:
            self._query_string = self._query.apply_converter_rules(
                    query_string=self._query_string,
                    converter=self._query.converter,
                    as_query_dict=False,
                    reverse=True
            )
        return self._query_string

    @property
    def num_found(self):
        return self._num_found

    @property
    def items(self):
        return self._items

    @property
    def breadcrumbs(self):
        return self._items


class ESPaginator(Paginator):
    """
    Override Django's built-in Paginator class to take in a count/total number of items;
    Elasticsearch provides the total as a part of the query results, so we can minimize hits.

    Also change `page()` method to use custom ESPage class (see below).
    """

    def __init__(self, *args, **kwargs):
        count = kwargs.pop('count', 0)
        super(ESPaginator, self).__init__(*args, **kwargs)
        self._count = count

    @property
    def count(self):
        """
        Returns the total number of objects, across all pages.
        """
        return self._count

    def page(self, number, just_source=True):
        """ Returns a Page object for the given 1-based page number. """
        try:
            number = self.validate_number(number)
        except EmptyPage as ep:
            logger.warn("number {} gives back empty page. Setting default to 1".format(number))
            number = 1
        except PageNotAnInteger as ep:
            logger.warn("negative number {} is not allowed. Setting default to 1".format(number))
            number = 1
        if just_source:
            # the ESPage class below extracts just the `_source` data from the hit data.
            return ESPage(self.object_list, number, self)
        return Page(self.object_list, number, self)


class ESPage(Page):
    def __getitem__(self, index):
        if not isinstance(index, (slice,) + six.integer_types):
            raise TypeError
        obj = self.object_list[index]
        return obj.get('_source', obj)


class QueryPagination(object):
    def __init__(self, paginator, current_page=1):
        self._paginator = paginator
        self._page = self._paginator.page(current_page)
        self._links = None

    @property
    def page(self):
        return self._page

    @property
    def start(self):
        return self._page.start_index()

    @property
    def rows(self):
        return self._paginator.per_page

    @property
    def num_found(self):
        return self._paginator.count

    @property
    def has_next(self):
        return self._page.has_next()

    @property
    def next_page_start(self):
        if self.has_next:
            next_page = self._paginator.page(self._page.next_page_number())
            return next_page.start_index()
        return 0

    @property
    def next_page_number(self):
        if self.has_next:
            return self._page.next_page_number()
        return 0

    @property
    def has_previous(self):
        return self._page.has_previous()

    @property
    def previous_page_start(self):
        if self.has_previous:
            previous_page = self._paginator.page(self._page.previous_page_number())
            return previous_page.start_index()
        return 0

    @property
    def previous_page_number(self):
        if self.has_previous:
            return self._page.previous_page_number()
        return 0

    @property
    def first_page(self):
        return 1

    @property
    def last_page(self):
        return self._paginator.num_pages

    @property
    def current_page(self):
        return self._page.number

    @property
    def links(self):
        if not self._links:
            self._links = self._create_links()
        return self._links

    def _create_links(self):
        from_page = self._page.number - 5
        from_page = from_page
        if from_page < 1 or not self._paginator.validate_number(from_page):
            from_page = 1
        to_page = from_page + 10
        if to_page > self._paginator.num_pages or not self._paginator.validate_number(to_page):
            to_page = self._paginator.num_pages + 1
            if (to_page - 10) < 10:
                from_page = to_page - 10
                if from_page < 1:
                    from_page = 1
        page_links = []
        for page in range(from_page, to_page):
            page_number = self._paginator.page(page)
            page_links.append(PageLink(
                    page_number.start_index(),
                    page is not self._page.number,
                    page_number.number
            )
            )
        return page_links


PageLink = namedtuple('PageLink', ['start', 'is_linked', 'page_number'])


class NaveESItem(object):
    def __init__(self, es_item, converter=None):
        self._converter = converter
        self._es_item = es_item
        self._create_meta()
        self._fields = self._create_item()
        # self._canonical_url = self._create_canonical_url()

    def __getitem__(self, item):
        return self._fields[item]

    @property
    def doc_id(self):
        return self._doc_id

    @property
    def doc_type(self):
        return self._doc_type

    @property
    def fields(self):
        return self._fields

    def _create_canonical_url(self):
        # todo implement later with reverse
        pass

    def _create_meta(self):
        if isinstance(self._es_item, dict):
            self._doc_id = self._es_item.get('_id')
            self._doc_type = self._es_item.get('_type')
            self._index = self._es_item.get('_index')
            self._score = self._es_item.get('_score')
        else:
            self._doc_id = self._es_item.meta.id
            self._doc_type = self._es_item.meta.doc_type
            self._index = self._es_item.meta.index
            self._score = self._es_item.meta.score

    def _create_item(self):
        if not isinstance(self._es_item, dict):
            fields = self._es_item.to_dict()
        else:
            fields = self._es_item
        if '_source' in fields:
            fields = fields['_source']
        if self._converter and self._doc_type in ['void_edmrecord', 'indexitem']:
            fields = self._converter(es_result_fields=fields).convert()
        items = sorted(fields.items())
        return collections.OrderedDict(items)


class NaveESItemWrapper(object):
    def __init__(self, es_item, converter=None):
        self.converter = converter
        self._es_item = NaveESItem(
                es_item=es_item,
                converter=converter
        )

    @property
    def item(self):
        return self._es_item

    def __getitem__(self, item):
        return self._es_item[item]


class NaveESItemList(object):
    def __init__(self, results, converter=None):
        self._converter = converter
        self._results = results
        self._items = self._create_items()

    @property
    def items(self):
        return self._items

    def _create_items(self):
        return [NaveESItemWrapper(es_item=item, converter=self._converter) for item in self._results]


class NaveQueryResponseWrapper(object):
    """
    This is a utility class to wrap the API response

    With normal library use you would only need NaveQueryResponse
    """

    def __init__(self, nave_query_response):
        self._query_response = nave_query_response

    @property
    def response(self):
        return self._query_response

    @property
    def data(self):
        return self._query_response

    @property
    def query(self):
        return self._query_response.query


class NaveItemResponse(object):
    def __init__(self, query, nave_query, index, mlt=False, mlt_items=None,
                 mlt_count=5, mlt_filter_query=None, rdf_record=None):
        self._index = index
        self._query = query
        self._nave_query = nave_query
        self._results = self._query.execute()
        self._mlt = mlt
        self._doc_type = None
        self._id = None
        self._item = None
        self._mlt_count = mlt_count
        self._mlt_filter_query = mlt_filter_query
        self._mlt_items = mlt_items
        self._rdf_record = rdf_record
        self._mlt_results = self._create_mlt()

    def get_mlt(self):
        return self._mlt_results

    def _create_mlt(self):
        if self._mlt and self._rdf_record:
            items = self._rdf_record.get_more_like_this(
                mlt_count=self._mlt_count,
                mlt_fields=self._nave_query.mlt_fields,
                filter_query=self._mlt_filter_query,
                wrapped=False,
                converter=self._nave_query.get_converter()
            )
            return items
        elif self._mlt and self.item:
            # todo: remove this later.
            doc_type = self.item.doc_type
            doc_id = self.item.doc_id
            from .connector import get_es_client
            s = Search(index=self._index)
            mlt_query = s.query(
                    'more_like_this',
                    fields=self._nave_query.mlt_fields,
                    min_term_freq=1,
                    max_query_terms=12,
                    include=False,
                    like=[{
                        "_index": self._index,
                        "_type": doc_type,
                        "_id": doc_id
                    }]
            )[:self._mlt_count]
            if self._mlt_filter_query:
                for k, v in self._mlt_filter_query.items():
                    if not k.endswith('.raw'):
                        k = "{}.raw".format(k)
                    mlt_query = mlt_query.filter("term", **{k: v})
            hits = mlt_query.execute()
            items = []
            for item in hits:
                nave_item = NaveESItem(item, self._nave_query.get_converter())
                items.append(nave_item)
            return items
        return ""

    @property
    def item(self):
        if not self._item:
            if self._results.hits.total > 0:
                es_item = self._results.hits[0]
                self._item = NaveESItem(es_item)
        return self._item

    @property
    def related_items(self):
        return self._mlt_results


class NaveQueryResponse(object):
    """
    This class encapsulates the responses of the NaveQuery.

    The elements can be used to render the results
    """

    def __init__(self, query, converter=None, api_view=None):

        self._converter = converter
        self._query = query
        self._api_view = api_view
        self._results = query.query.execute()
        self._num_found = None
        self._user_query = UserQuery(self._query, self.num_found)
        self._items = None
        self._facets = None
        self._pagination = None
        self._geojson_clusters = None
        self._paginator = None
        self._rows = self._query.size

    def set_cache_page(self):
       """Set the seach_after key for ElasticSearch."""
       sort_key = self._result.hits[-1].meta.sort
       # todo implement the rest
       # get all params replace start or page append __ number
       page_key = ''
       page_cache.set(page_key, str(sort_key), 300)


    @property
    def query(self):
        return self._query

    @property
    def es_results(self):
        return self._results

    @property
    def user_query(self):
        if not self._user_query:
            self._user_query = UserQuery(self._query, self.num_found)
        return self._user_query

    @property
    def num_found(self):
        if not self._num_found:
            self._num_found = self.es_results.hits.total
        return self._num_found

    @property
    def paginator(self):
        if not self._paginator:
            self._paginator = ESPaginator(self.es_results.hits, self._rows, count=self.num_found)
        return self._paginator

    @property
    def pagination(self):
        if not self._pagination:
            self._pagination = QueryPagination(
                    self.paginator,
                    self._query.page
            )
        return self._pagination

    @property
    def items(self):
        """
        :return: a list of result items
        """
        if not self._items:
            self._items = NaveESItemList(
                    results=self._results.hits.hits,
                    converter=self._converter).items
        return self._items

    @property
    def facets(self):
        """
        NaveFacets as a list
        """
        if not self._facets:
            self._facets = NaveFacets(
                self._query,
                self._results.aggregations
            )
        return self._facets

    @property
    def facet_dict(self):
        """Facets as a dictionary by raw facet query, e.g. gemeente.raw"""
        return self.facets.facet_query_dict

    @property
    def facet_list(self):
        """Facets as a list of FacetConfigs to be used directly in the views"""
        facets = self._api_view.facets
        facet_query_links = self.facet_dict
        for conf in facets:
            key = conf.es_field
            links = facet_query_links.get(key)
            conf.facet_link = links
        return facets

    @property
    def geojson_clusters(self):
        if not self._geojson_clusters and 'places' in self._results.facets:
            self._geojson_clusters = self._query.query.places_as_geojson(self.facets)
        return self._geojson_clusters

    @property
    def facet_query_links(self):
        return self.facets.facet_query_list

    @property
    def layout(self):
        converter = self._converter
        if not converter and settings.DEFAULT_V1_CONVERTER is not None:
            from nave.void import REGISTERED_CONVERTERS
            converter = REGISTERED_CONVERTERS.get(settings.DEFAULT_V1_CONVERTER, None)
        if not converter:
            return {}
        layout_fields = converter().get_layout_fields()
        return {"layout": layout_fields}
