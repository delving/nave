"""
All ES query related functionality goes into this module
"""
import collections
import logging
import re
import urllib.error
import urllib.parse
from collections import defaultdict, namedtuple
from contextlib import contextmanager

import geojson
from django.conf import settings
from django.core.paginator import Paginator, Page, EmptyPage, PageNotAnInteger
from django.http import QueryDict
from elasticsearch_dsl import Search
from elasticsearch_dsl.result import Result
from .elasticutils import S, F, Q
from geojson import Point, Feature, FeatureCollection
# noinspection PyMethodMayBeStatic
from rest_framework.request import Request
import six


from .utils import gis
from void.convertors import BaseConverter

logger = logging.getLogger(__name__)


class GeoS(S):
    BOUNDING_BOX_PARAM_KEYS = ['min_x', 'min_y', 'max_x', 'max_y']

    def process_filter_bbox(self, key, val, action):

        def valid_bbox_filter():
            valid_keys = self.BOUNDING_BOX_PARAM_KEYS.sort()
            values_are_valid = all(isinstance(coor, float) for coor in list(val.values()))
            return isinstance(val, dict) and val.keys.sort() is valid_keys and values_are_valid

        if not valid_bbox_filter:
            return
        key = key if key is not None else "point"

        geo_filter = {
            "geo_bounding_box": {
                key: {
                    "bottom_left": {
                        "lat": val.get('min_x'),
                        "lon": val.get('min_y')
                    },
                    "top_right": {
                        "lat": val.get('max_x'),
                        "lon": val.get('max_y')
                    }
                }
            }
        }
        return geo_filter

    def process_filter_polygon(self, key, val, action):
        # TODO finish implementation
        """
        Filter results by polygon
        http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl-geo-polygon-filter.html
        """

        def valid_polygon_filter():
            valid_keys = self.BOUNDING_BOX_PARAM_KEYS.sort()
            values_are_valid = all(isinstance(coor, float) for coor in list(val.values()))
            return isinstance(val, dict) and val.keys.sort() is valid_keys and values_are_valid

        if not valid_polygon_filter:
            return
        key = key if key is not None else "point"

        polygon_filter = {
            "geo_polygon": {
                key: [
                    {"lat": 40, "lon": -70},
                    {"lat": 30, "lon": -80},
                    {"lat": 20, "lon": -90}
                ]
            }
        }
        return polygon_filter

    def facet_geocluster(self, filtered=True, factor=0.6):
        """
        Add facets for clustered geo search.

        Note: It should always be the last in the chain
        """
        cluster_config = {
            "geohash": {
                "field": "point",
                "factor": factor,
                'show_doc_id': True
            }
        }
        query = self.query()
        if filtered:
            filt = query.build_search().get('filter')
            filtered = {'filter': filt}
            filtered.update(cluster_config)
            cluster_config = filtered
        return query.facet_raw(places=cluster_config)

    @staticmethod
    def get_feature_collection(facets):
        features = []
        if 'places' in facets:
            for place in facets.get('places').clusters:
                total = place.get('total', 0)
                center = place.get('center')
                center_point = Point((center['lon'], center['lat']))
                properties = {'count': total}
                feature_id = place.get('doc_id')
                extra_properties = {key: place.get(key) for key in list(place.keys()) if key in ['doc_type']}
                if extra_properties:
                    properties.update(extra_properties)
                features.append(Feature(geometry=center_point, id=feature_id, properties=properties))
        return FeatureCollection(features)

    @staticmethod
    def get_geojson(feature_collection):
        return geojson.dumps(feature_collection)

    def places_as_geojson(self, facets):
        features = self.get_feature_collection(facets)
        return self.get_geojson(features)

    @staticmethod
    def get_lat_long_bounding_box(boundingbox_params):
        bounding_box = {}
        if all('.' in coor for coor in list(boundingbox_params.values())):
            bounding_box = {key: float(value) for key, value in list(boundingbox_params.items())}
        elif all('.' not in coor for coor in list(boundingbox_params.values())):
            # converting rd to lat long
            min_y, min_x = gis.rd_to_wgs84(boundingbox_params.get('min_x'), boundingbox_params.get('min_y'))
            max_y, max_x = gis.rd_to_wgs84(boundingbox_params.get('max_x'), boundingbox_params.get('max_y'))
            bounding_box['min_x'] = min_x
            bounding_box['min_y'] = min_y
            bounding_box['max_x'] = max_x
            bounding_box['max_y'] = max_y
        return bounding_box


    @staticmethod
    def get_solr_style_bounding_box(distance, point):
        """The hub2 equivalent filter for a bounding box."""
        # lonLat conform geojson
        lat, lon = point.split(',')
        point = "{},{}".format(lon, lat)
        bb_filter = {
            "geo_distance": {
                "distance": "{}km".format(distance),
                "point": point
            }
        }
        return bb_filter


class NaveESQuery(object):
    """
    This class builds ElasticSearch queries from default settings and HTTP request as provided by Django

    """

    def __init__(self, index_name=None, doc_types=None, default_facets=None, size=16,
                 default_filters=None, hidden_filters=None, cluster_geo=False, geo_query=False, robust_params=True, facet_size=50,
                 converter=None, acceptance=False):
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
        self.cluster_factor = 0.6
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

        >>> _as_list('sjoerd')
        ['sjoerd']

        >>> _as_list(['sjoerd'])
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
        >>> _filters_as_dict(['gemeente:best'])
        defaultdict(<type 'set'>, {'gemeente': set(['best'])})

        >>> _filters_as_dict(['gemeente:best', 'gemeente:son en breugel'])
        defaultdict(<type 'set'>, {'gemeente': set(['son en breugel', 'best'])})


        >>> _filters_as_dict(['gemeente:best', 'plaats:best'])
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
            elif ":" in filt:
                key, *value = filt.split(":")
                key = key.replace('_facet', '')
                if key.startswith('delving_') and key not in self.non_legacy_keys:
                    key = "legacy.{}".format(key)
                filter_dict[key].add(":".join(value))
            else:
                # add support for query based filters
                filter_dict['query'].add(filt)
        return filter_dict

    @staticmethod
    def _clean_params(param_dict):
        """
        >>> from django.http import QueryDict
        >>> _clean_params(QueryDict('qf=gemeente:best&qf[]=plaats:best').copy()).getlist('qf')
        [u'gemeente:best', u'plaats:best']

        >>> from django.http import QueryDict
        >>> list(_clean_params(QueryDict('qf[]=plaats:best').copy())['qf'])
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
        query = GeoS().es(urls=settings.ES_URLS, timeout=settings.ES_TIMEOUT)
        if self.get_index_name:
            query = query.indexes(*self._as_list(self.get_index_name))
        if self.doc_types:
            query = query.doctypes(*self._as_list(self.doc_types))
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
        query_string = re.sub("([\w]+)_([\w]+):", r"\1_\2.value:", query_string)
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
        return str(self.query.steps)

    def build_query(self):
        if self.default_facets:
            self.query = self.query.facet(*self._as_list(self.facet_list), size=self.facet_size)
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
                query = query.query.query(_id=clean_id, _type=doc_type)
                self._is_item_query = True
            elif self.hub_id_pattern.findall(clean_id):
                from lod.utils.resolver import RDFRecord
                clean_id = RDFRecord.clean_local_id(clean_id, is_hub_id=True)
                query = query.query.query(_id=clean_id)
                self._is_item_query = True
            else:
                raise ValueError("unknown clean_id type: {}".format(clean_id))
        return query

    @staticmethod
    def expand_params(param):
        key = param[0]
        value_list = param[1]
        return [(key, value) for value in value_list]

    def build_query_from_request(self, request, raw_query_string=None):

        @contextmanager
        def robust(key):
            try:
                yield
            except ValueError as ve:
                self.error_messages.append("param {}: {}".format(key, str(ve)))
                logger.warn(
                        "problem with param {} causing {} for request {}".format(key, ve, request.build_absolute_uri()))
                # if not self.robust_params:
                #     raise
                raise

        query = self.query
        if isinstance(request, Request):
            request = request._request
        query_string = raw_query_string if raw_query_string else request.META['QUERY_STRING']
        if self.converter is not None:
            query_dict = self.apply_converter_rules(query_string, self.converter)
        elif raw_query_string:
            query_dict = QueryDict(query_string=query_string)
        else:
            query_dict = request.query_params if isinstance(request, Request) else request.GET

        params = self._clean_params(query_dict.copy())
        facet_params = self._clean_params(query_dict.copy())
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
                query = query[start:end]
        elif 'start' in params and 'page' not in params:
            with robust('start'):
                start = int(params.get('start'))
                page = int(start / self.size) + 1
                if page > 0:
                    self.page = page
                end = start + self.size
                query = query[start:end]
        else:
            query = query[:self.size]
        # update key
        if 'query' in params and 'q' not in params:
            params['q'] = params.get('query')
        # add hidden filters:
        exclude_filter_list = params.getlist("pop.filterkey")
        hidden_filter_dict = self._filters_as_dict(
            self.hidden_filters,
            exclude=exclude_filter_list
        ) if self.hidden_filters else defaultdict(set)
        hidden_queries = hidden_filter_dict.pop("query", [])
        if self.param_is_valid('q', params) and not params.get('q') in ['*:*']:
            query_string = params.get('q')

            if "&quot;" in query_string:
                query_string = query_string.replace('&quot;', '"')
            for hq in hidden_queries:
                query_string = "{} {}".format(query_string, hq)
            query = query.query_raw(self._create_query_string(query_string))
        # add lod_filtering support
        elif "lod_id" in params:
            lod_uri = params.get("lod_id")
            query = query.query(
                    **{'rdf.object.id': lod_uri, "must": True}).filter(~F(**{'system.about_uri': lod_uri}))
        elif hidden_queries:
            query = query.query_raw(self._create_query_string(" ".join(hidden_queries)))
        else:
            query = query.query()

        # add filters
        filter_dict = self._filters_as_dict(self.default_filters) if self.default_filters else defaultdict(set)
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
            facet_bool_type_and = params.get("facetBoolType").lower() in ["and"]
        # Important: hidden query filters need to be additional query and not filters.
        if hidden_filter_dict:
            for key, values in hidden_filter_dict.items():
                f = F()
                for value in values:
                    clean_value = value
                    if clean_value.startswith('"') and clean_value.endswith('"'):
                        clean_value = clean_value.strip('"')
                    if key.startswith('-'):
                        f |= ~F(**{self.query_to_facet_key(key): clean_value})
                    elif facet_bool_type_and:
                        f &= F(**{self.query_to_facet_key(key): clean_value})
                    else:
                        f |= F(**{self.query_to_facet_key(key): clean_value})

                query = query.filter(f)
                # todo: remove old solution later
                # query_list = []
                # for value in values:
                #     if key.startswith('-'):
                #         query_list.append("(NOT {})".format(value))
                #     else:
                #         query_list.append("{}".format(value))
                # if facet_bool_type_and:
                #     query_string = " AND ".join(query_list)
                # else:
                #     query_string = " OR ".join(query_list)
                # query = query.filter(F(**{self.query_to_facet_key(key): "({})".format(query_string)}))
        applied_facet_fields = []

        if filter_dict:
            for key, values in list(filter_dict.items()):
                applied_facet_fields.append(key.lstrip('-+').replace('.raw', ''))
                f = F()
                for value in values:
                    clean_value = value
                    if clean_value.startswith('"') and clean_value.endswith('"'):
                        clean_value = clean_value.strip('"')
                    if key.startswith('-'):
                        f |= ~F(**{self.query_to_facet_key(key): clean_value})
                    elif facet_bool_type_and:
                        f &= F(**{self.query_to_facet_key(key): clean_value})
                    else:
                        f |= F(**{self.query_to_facet_key(key): clean_value})

                query = query.filter(f)
        filter_dict.update(hidden_filter_dict)
        self.applied_filters = filter_dict
        # old solr style bounding box query
        bbox_filter = None
        if {'pt', 'd'}.issubset(list(params.keys())):
            point = params.get('pt')
            if point:
                bbox_filter = GeoS.get_solr_style_bounding_box(params.get('d', '10'), point)
                query = query.filter_raw(bbox_filter)
                # todo: test this with the monument data
        # add facets
        facet_list = self._as_list(self.facet_list) if self.default_facets else []
        if 'facet' in params:
            with robust('facet'):
                facets = params.getlist('facet')
                for facet in facets:
                    if ',' in facet:
                        facet_list.extend(facet.split(','))
                    else:
                        facet_list.append(facet)
        # add facets to config
        # add non default facets to the bottom intersection from keys
        for facet in set(facet_list).difference(set(self.facet_list)):
            from base_settings import FacetConfig
            self.default_facets.append(FacetConfig(
                es_field=facet,
                label=facet
            ))
        if facet_list:
            with robust('facet'):
                if 'facet.size' in params:
                    self.facet_size = int(params.get('facet.size'))
                facet_filt_dict = {"{}.raw".format(k.replace('.raw', '')): list(v) for k, v in filter_dict.items()}
                for facet in facet_list:
                    # remove current facet from filter dict
                    if not facet_bool_type_and:
                        facet_filter = {k: v for k, v in facet_filt_dict.items() if k != facet}
                    else:
                        facet_filter = facet_filt_dict
                    # implement facet raw queries
                    formatted_facet_filter = {
                        facet:
                            {
                                'terms': {'field': facet, 'size': self.facet_size}
                            }
                    }
                    and_facet_filter_list = [{"terms": {k: v}} for k, v in facet_filter.items()]
                    if bbox_filter:
                        and_facet_filter_list.append(bbox_filter)
                    if and_facet_filter_list:
                        formatted_facet_filter = {
                            facet: {
                                'aggs': formatted_facet_filter,
                                'filter': {
                                    'and': and_facet_filter_list
                                }
                            }
                        }
                    query = query.facet_raw(**formatted_facet_filter)
        # add bounding box
        bounding_box_param_keys = GeoS.BOUNDING_BOX_PARAM_KEYS
        if set(bounding_box_param_keys).issubset(list(params.keys())):
            with robust(str(bounding_box_param_keys)):
                boundingbox_params = {key: val for key, val in list(params.items()) if key in bounding_box_param_keys}
                bounding_box = GeoS.get_lat_long_bounding_box(boundingbox_params)
                if bounding_box:
                    query = query.filter(point__bbox=bounding_box)
        # add clusters
        if self.cluster_geo:
            with robust('geo_cluster'):
                filtered = bool(params.get('cluster.filtered')) if 'cluster.filtered' in params else True
                if 'cluster.factor' in params:
                    factor = float(params.get('cluster.factor'))
                    query = query.facet_geocluster(factor=factor, filtered=filtered)
                else:
                    query = query.facet_geocluster(filtered=filtered)
        if self.geo_query:
            query = query.query_raw({"match": {"delving_hasGeoHash": True}})
        self.query = query
        self.facet_params = facet_params
        self.base_params = params
        import json
        logger.info(json.dumps(query.build_search()))
        return query

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

    def query_to_facet_key(self, facet_key):
        if facet_key.startswith('delving_spec'):
            facet_key = "system.spec.raw"
        elif facet_key.startswith('delving_') and facet_key not in self.non_legacy_keys:
            facet_key = 'legacy.{}'.format(facet_key)
        if "." not in facet_key:
            facet_key = "{}.raw".format(facet_key)
        return facet_key.lstrip('-')

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
                           'facet.limit', 'facetBoolType', 'facet']:
                    del facet_params[key]
                if not value and key in facet_params:
                    del facet_params[key]
            selected_facets = self._facet_params.getlist('qf')
            # todo: later replace the replace statements with urlencode() as well for query filters
            if facet_params:
                link = "{}&qf[]={}".format(
                    facet_params.urlencode(),
                    self._filter_query.replace(":", "%3A").replace("&", "%26")
                )
            else:
                link = "qf[]={}".format(
                    self._filter_query.replace(":", "%3A").replace("&", "%26")
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
    def __init__(self, name, facet_terms, query, total=0, other=0, missing=0):
        self._name = name
        self._clean_name = None
        self._i18n = None
        self._total = total
        self._other = other
        self._missing = missing
        self._query = query
        self._facet_terms = facet_terms
        self._is_selected = False
        self._facet_count_links = self._create_facet_count_links()

    def _create_facet_count_links(self):
        facet_count_links = []
        if 'buckets' not in self._facet_terms:
            for k, v in self._facet_terms.items():
                if k != 'doc_count':
                    self._facet_terms = v
        for term in self._facet_terms.get('buckets'):
            count = term.get('doc_count')
            value = term.get('key')
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
            ordered_dict[facet.es_field] = facets.get(facet.es_field)
        return ordered_dict

    def _create_facet_query_links(self):
        facet_query_links = collections.OrderedDict()
        for key, facet in self._facets.items():
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
            facet_query_link = FacetLink(
                    name=clean_name,
                    # todo: replace later with count facet.total,
                    total=0,
                    # todo: replace later with count facet.total,facet.missing,
                    missing=0,
                    # todo: replace later with count facet.total,facet.other,
                    other=0,
                    query=self._nave_query,
                    facet_terms=facet
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
        count = kwargs.pop('count', None)
        super(ESPaginator, self).__init__(*args, **kwargs)
        self._count = count

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
        if isinstance(self._es_item, Result):
            self._doc_id = self._es_item.meta.id
            self._doc_type = self._es_item.meta.doc_type
            self._index = self._es_item.meta.index
            self._score = self._es_item.meta.score
        else:
            # todo: deprecate this elasticutils code later
            self._doc_id = self._es_item.get('_id')
            self._doc_type = self._es_item.get('_type')
            self._index = self._es_item.get('_index')
            self._score = self._es_item.get('_score')

    def _create_item(self):
        # todo filter out None later
        if isinstance(self._es_item, Result):
            fields = self._es_item.to_dict()
        else:
            fields = self._es_item['_source']
        if self._converter and self._doc_type == "void_edmrecord":
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
            from . import get_es_client
            s = Search(using=get_es_client(), index=self._index)
            mlt_query = s.query(
                    'more_like_this',
                    fields=self._nave_query.mlt_fields,
                    min_term_freq=1,
                    max_query_terms=12,
                    include=False,
                    docs=[{
                        "_index": self._index,
                        "_type": doc_type,
                        "_id": doc_id
                    }]
            )[:self._mlt_count]
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
            if len(self._results.results) > 0:
                es_item = self._results.results[0]
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
            self._num_found = self.es_results.count
        return self._num_found

    @property
    def paginator(self):
        if not self._paginator:
            self._paginator = ESPaginator(self.es_results.objects, self._rows, count=self.num_found)
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
                    results=self._results.results,
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
                self._results.response.get('aggregations')
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
                from void import REGISTERED_CONVERTERS
                converter = REGISTERED_CONVERTERS.get(settings.DEFAULT_V1_CONVERTER, None)
        if not converter:
            return {}
        layout_fields = converter().get_layout_fields()
        return {"layout": layout_fields}
