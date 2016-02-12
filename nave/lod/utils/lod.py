# -*- coding: utf-8 -*- 
"""This module does


"""
from collections import Counter
import logging
from urllib.error import HTTPError
from urllib.parse import quote, urlparse

from django.conf import settings
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF

from lod import get_rdf_base_url

log = logging.getLogger(__name__)


def get_cache_url(uri):
    cache_url = "{}/resource/cache/{}".format(
        get_rdf_base_url(prepend_scheme=True),
        quote(uri, safe='/')
    )
    return cache_url


def _add_cache_url(url, graph):
    cache_url = get_cache_url(url)
    graph.add((
        URIRef(url),
        URIRef('http://schemas.delving.org/nave/terms/cacheUrl'),
        URIRef(cache_url)
    ))


def get_remote_lod_resource(url):
    graph = Graph()
    try:
        graph.parse(url)
    except HTTPError as he:
        log.warn("Unable to cache LoD resource: {}".format(url))
        return None
    return graph


def store_remote_cached_resource(graph, graph_store, named_graph):
    response = graph_store.put(
        named_graph=named_graph,
        data=graph
    )
    return response


def get_geo_points(graph):
    try:
        lat_list = [float(str(lat)) for lat in
                    graph.objects(predicate=URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#lat"))]
        lon_list = [float(str(lon)) for lon in
                    graph.objects(predicate=URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#long"))]
    except ValueError as ve:
        log.error("Unable to get geopoints because of {}".format(ve.args))
        return []
    zipped = zip(lat_list, lon_list)
    if not lat_list and not lon_list:
        return []
    return [list(elem) for elem in list(zipped)]


def get_external_rdf_url(internal_uri, request):
    """Convert the internal RDF base url to the external domain making the request. """
    parsed_target = urlparse(internal_uri)
    request_domain = request.get_host()
    entry_points = settings.RDF_ROUTED_ENTRY_POINTS
    if request_domain not in entry_points:
        request_domain = parsed_target.netloc
    return "http://{domain}{path}".format(domain=request_domain, path=parsed_target.path)


def get_internal_rdf_base_uri(target_uri):
    """Converted web_uri to internal RDF base_url.

    The main purpose of this function is to enable routing from multiple external urls,
    but still use a single internal base url
    """
    parsed_target = urlparse(target_uri)
    domain = parsed_target.netloc
    entry_points = settings.RDF_ROUTED_ENTRY_POINTS
    if domain in entry_points:
        domain = get_rdf_base_url()
    return "http://{domain}{path}".format(domain=domain, path=parsed_target.path)


def get_graph_statistics(graph):
    def get_counter(entries):
        return Counter(entries).most_common(50)

    def get_qname(uri):
        return graph.namespace_manager.qname(uri)

    languages = [obj.language for obj in graph.objects() if isinstance(obj, Literal) and obj.language is not None]
    rdf_class = [get_qname(obj) for obj in graph.objects(predicate=RDF.type) if isinstance(obj, URIRef)]
    properties = [get_qname(obj) for obj in graph.predicates() if
                  isinstance(obj, URIRef) and str(obj) not in settings.RDF_EXCLUDED_PROPERTIES]

    stats = {
        'language': get_counter(languages),
        'RDF class': get_counter(rdf_class),
        'property': get_counter(properties)
    }
    return stats
