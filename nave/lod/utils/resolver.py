# -*- coding: utf-8 -*-
"""This module implements all the bindings used by the view layers for RDF Graphs.

This module deals with all the conversion of Named Graphs or SPARQL results into Python objects
that can be used by Django views.

This code expects that each RDF resource is linked to a DataSet so that we can display provinance.

The  GraphBindings is the first iteration that does not do Graph Normalisation

The NormalisedRDFResource get as resource URI and deals with:

    * the SPARQL query
    * retrieving the named graph
    * retrieving the unbound URIs from the Cache and Skos graph
    * constructing

"""
from collections import defaultdict, Counter
from collections import namedtuple, OrderedDict
import itertools
from datetime import datetime
from time import sleep
from operator import itemgetter
from urllib.error import HTTPError

import elasticsearch
import os
import logging
from urllib.parse import urlparse, quote

import re
from django.conf import settings
from django.urls import reverse
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from rdflib import ConjunctiveGraph
from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF, SKOS, RDFS, DC, FOAF

from nave.lod import namespace_manager
from nave.lod.utils import rdfstore

from nave.search.connector import get_es_client

logger = logging.getLogger(__file__)
client = get_es_client()


Predicate = namedtuple('Predicate', ['uri', 'label', 'ns', 'prefix'])
Object = namedtuple('Object', ['value', 'is_uriref', 'is_resource', 'datatype', 'language', 'predicate'])

EDM = Namespace('http://www.europeana.eu/schemas/edm/')
NAVE = Namespace('http://schemas.delving.eu/nave/terms/')
ORE = Namespace('http://www.openarchives.org/ore/terms/')


def get_geo_points(graph, only_geohash=False):
    try:
        lat_list = [float(str(lat)) for lat in
                    graph.objects(predicate=URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#lat"))]
        lon_list = [float(str(lon)) for lon in
                    graph.objects(predicate=URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#long"))]
    except ValueError as ve:
        logger.error("Unable to get geopoints because of {}".format(ve.args))
        return []
    zipped = zip(lat_list, lon_list)
    if (not lat_list and not lon_list) or only_geohash:
        geohashes = graph.objects(predicate=NAVE.geoHash)
        points = []
        for geohash in geohashes:
            lat, lon = geohash.split(',')
            if lat and lon:
                lat = float(str(lat.strip()))
                lon = float(str(lon.strip()))
                points.append([lat, lon])
        return points
    return list(list(elem) for elem in list(zipped))


def get_cache_url(uri):
    cache_url = "{}/resource/cache/{}".format(
        RDFRecord.get_rdf_base_url(prepend_scheme=True),
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
        logger.warn("Unable to cache LoD resource: {}".format(url))
        return None
    return graph


def store_remote_cached_resource(graph, graph_store, named_graph):
    response = graph_store.put(
        named_graph=named_graph,
        data=graph
    )
    return response


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
        domain = RDFRecord.get_rdf_base_url()
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


class GraphBindings:
    def __init__(self, about_uri, graph,
                 excluded_rdf_types=None, allowed_rdf_types=None,
                 excluded_properties=None, allowed_properties=None,
                 aggregate_edm_blank_nodes=True,
                 label_properties=(SKOS.prefLabel, RDFS.label, URIRef('http://www.w3.org/2004/02/skos/core#altLabel'),
                                   FOAF.name, URIRef('http://www.geonames.org/ontology#name'), DC.title,
                                   URIRef('http://schemas.delving.eu/narthex/terms/proxyLiteralValue'),
                                   URIRef('http://dbpedia.org/ontology/name')),
                 thumbnail_fields = (
                        FOAF.depiction,
                        URIRef('http://schemas.delving.eu/nave/terms/thumbnail'),
                        URIRef('http://schemas.delving.eu/nave/terms/thumbSmall'),
                        URIRef('http://schemas.delving.eu/nave/terms/thumbLarge'),
                        URIRef('http://www.europeana.eu/schemas/edm/object'),
                        URIRef('http://www.europeana.eu/schemas/edm/isShownBy'),
                    )
                 ):
        self._thumbnail_fields = thumbnail_fields
        self.aggregate_edm_blank_nodes = aggregate_edm_blank_nodes
        self._label_properties = label_properties
        self._allowed_properties = allowed_properties
        self._excluded_properties = excluded_properties
        self._allowed_rdf_types = allowed_rdf_types
        self._excluded_rdf_types = excluded_rdf_types
        self._graph = graph
        self._about_uri = URIRef(about_uri)
        self._resources = self._create_resources()
        self._resources_by_type = None
        self._inlined_resources = []
        self._call_queue = defaultdict(list)
        self._items = None
        self._search_label_dict = defaultdict(list)

    def __getitem__(self, search_label):
        return self.get_first(search_label)

    def mark_as_inline_resource(self, uri):
        if not isinstance(uri, URIRef):
            uri = URIRef(uri)
        self._inlined_resources.append(uri)

    def get_thumbnail_fields(self):
        return self._thumbnail_fields

    def get_uri_from_search_label(self, search_label):
        """Convert search_label back into a URI."""
        if not search_label or '_' not in search_label:
            return None
        prefix, label = search_label.split('_')
        namespace_dict = dict(list(namespace_manager.namespaces()))
        uri = namespace_dict.get(prefix)
        return os.path.join(uri, label)

    def get_all_items(self):
        """Return all RDFResources as a list.

        This list is sorted by nave:resourceSortOrder. This way field access
        is sorted correctly.
        """
        if not self._items:
            webresources = []
            resources = []
            webresources = self.get_sorted_webresources()
            for uri, resource in self.get_resources().items():
                if resource.is_ore_aggregation():
                    if RDFPredicate(EDM.hasView) in resource.get_items():
                        resource.get_items()[RDFPredicate(EDM.hasView)] = webresources
                if resource.is_web_resource():
                    pass
                elif uri not in self._inlined_resources:
                    resources.append(resource.get_items().values())
            objects = list(itertools.chain.from_iterable(resources))
            self._items = list(itertools.chain.from_iterable(objects))
            for wr in webresources:
                self._items.extend(itertools.chain.from_iterable(wr.get_items().values()))
        return self._items

    def get_sorted_webresources(self, webresources=None):
        if not webresources:
            webresources = []
            for uri, resource in self.get_resources().items():
                if resource.is_web_resource():
                    webresources.append(resource)
        if webresources:
            return sorted(webresources, key=lambda wr: wr.get_sort_key())
        return []

    def get_all_skos_links(self):
        linked_skos_query = """
        select ?s {
            ?s a <http://www.w3.org/2004/02/skos/core#Concept>.
            Filter exists {?s2 <http://www.w3.org/2004/02/skos/core#exactMatch> ?s}
        } limit 20
        """
        response = self._graph.query(linked_skos_query)
        links = set([str(uri['?s']) for uri in response.bindings])
        resources = [self.get_resource(uri_ref=link) for link in links]
        filters = self._create_query_filter(links)
        return resources, filters

    def _create_query_filter(self, links):
        return " OR ".join(['rdf.object.id:%22{}%22'.format(link) for link in links])

    def get_first(self, search_label):
        objects = self.get_list(search_label)
        if objects:
            return objects[0]
        return None

    def get_first_literal(self, predicate, graph=None):
        if graph is None:
            graph = self._graph
        if not isinstance(predicate, URIRef):
            predicate = URIRef(predicate)
        for s, o in graph.subject_objects(predicate=predicate):
            if isinstance(o, Literal):
                if o.datatype == URIRef('http://www.w3.org/2001/XMLSchema#boolean'):
                    return True if o.value in ['true', 'True'] else False
                elif o.datatype == URIRef('http://www.w3.org/2001/XMLSchema#integer'):
                    return int(o.value)
                else:
                    return o.value if not len(o.value) > 32766 else o.value[:32700]
        return None

    def get_list(self, search_label, lexsort=True):
        if not self._search_label_dict:
            for rdf_object in self.get_all_items():
                self._search_label_dict[rdf_object.predicate.search_label].append(rdf_object)
        if not lexsort:
            return self._search_label_dict.get(search_label, [])
        return sorted(self._search_label_dict.get(search_label, []), key=lambda k: k.value)

    def get_resources(self):
        if not self._resources:
            self._resources = self._create_resources()
        return self._resources

    def _create_resources(self):
        """Create RDFResources from all subjects in the Graph."""
        resources = {}
        if self.aggregate_edm_blank_nodes:
            for subj in set(self._graph.subjects()):
                if isinstance(subj, BNode):
                    if any(str(obj).startswith('http://schemas.delving.eu/nave/terms/') for obj in self._graph.objects(subject=subj, predicate=RDF.type)):
                        self._graph.add((self.about_uri(), URIRef('http://www.openarchives.org/ore/terms/aggregates'), subj))
        for subject in self._graph.subjects():
            resource = RDFResource(
                subject_uri=subject,
                graph=self._graph,
                excluded_properties=self._excluded_properties,
                allowed_properties=self._allowed_properties,
                bindings=self
            )
            if self._allowed_rdf_types and resource.get_type() in self._allowed_rdf_types:
                resources[subject] = resource
            else:
                resources[subject] = resource
        return resources

    def about_uri(self):
        return self._about_uri

    def get_about_resource(self):
        uri = self.about_uri()
        return self.get_resource(uri_ref=uri, obj=None)

    def has_resource(self, uri_ref_or_bnode, call_obj=None):
        is_resource = self._resources.get(uri_ref_or_bnode, None)
        if is_resource is not None and is_resource.has_content() and is_resource.subject_uri is not self.about_uri():
            return True
        return False

    def has_geo(self):
        points = get_geo_points(self._graph, only_geohash=False)
        return True if points else False

    @staticmethod
    def is_lod_allowed(graph):
        """Check if LoD routing is allowed."""
        allowed = True
        lod_allowed = list(
            graph.objects(
                predicate=NAVE.allowLinkedOpenData
            )
        )
        if len(lod_allowed) > 0:
            allowed = all([str(o).lower() == 'true' for o in lod_allowed])
        return allowed

    def _add_to_call_queue(self, uri_ref, obj=None):
        if obj:
            self._call_queue[str(uri_ref)].append(obj)

    def get_resource(self, uri_ref, obj=None):
        """ Get a resource from resource dict.

        :param uri_ref:  URIRef from the graph
        :return: lod.utils.RDFResource
        """
        if uri_ref.startswith('http') or uri_ref.startswith('urn:'):
            uri = URIRef(uri_ref)
        else:
            uri = BNode(uri_ref)
        self._add_to_call_queue(uri_ref=uri, obj=obj)
        return self._resources.get(uri)  # later add None again

    def get_bnode(self, bnode, obj=None):
        """ Get a resource from resource dict.
        """
        if not isinstance(bnode, BNode):
            bnode = BNode(bnode)
        self._add_to_call_queue(uri_ref=bnode, obj=obj)
        return self._resources.get(bnode, None)

    @property
    def get_resource_list(self, sort=True):
        if sort:
            return sorted(self._resources.values())
        return list(self._resources.values())

    @property
    def get_available_resources_types(self):
        return set([resource.get_type().qname for resource in self.get_resource_list])

    def get_resources_by_rdftype(self, search_label):
        """Return a list of RDFResources by their RDF.type"""
        if not self._resources_by_type:
            type_dict = defaultdict(list)
            for resource in self.get_resource_list:
                search_label = resource.get_type().search_label
                type_dict[search_label].append(resource)
            self._resources_by_type = type_dict
        return self._resources_by_type.get(search_label, None)

    @property
    def label_properties(self):
        return self._label_properties

    @property
    def get_about_caption(self):
        resource = self.get_about_resource()
        if resource is None:
            return []
        return resource.get_label()

    @property
    def get_about_thumbnail(self, uri=None):
        # todo add second layer to get image.
        label = []

        thumbnail = None
        for thumb in self.get_thumbnail_fields():
            thumbnails = list(self._graph.objects(predicate=thumb))
            if len(thumbnails) == 0:
                continue
            else:
                thumbnail = [l for l in thumbnails]
                break
        return str(thumbnail[0]) if thumbnail and len(thumbnail) > 0 else None

    def to_flat_index_doc(self):
        index_doc = defaultdict(list)
        index_doc['rdf'] = {}
        index_doc['about'] = {}
        rdf_class = [RDFPredicate(str(obj)) for obj in set(list(self._graph.objects(predicate=RDF.type))) if
                     isinstance(obj, URIRef)]
        languages = {obj.language for obj in self._graph.objects() if
                     isinstance(obj, Literal) and obj.language is not None}
        predicates = {RDFPredicate(str(obj)) for obj in set(list(self._graph.predicates())) if
                      isinstance(obj, URIRef) and str(obj) not in settings.RDF_EXCLUDED_PROPERTIES}
        subjects = {str(obj) for obj in set(list(self._graph.subjects())) if isinstance(obj, URIRef)}
        rdf_objects = [obj.to_index_entry(nested=False) for obj in self.get_all_items() if
                       obj._object_type is not self._about_uri]
        # add classes
        index_doc['rdf']['class'] = [
            {'@type': "URIRef", 'id': clzz.uri_as_string, 'value': clzz.qname, 'raw': clzz.qname} for
            clzz in rdf_class]
        # add languages
        index_doc['rdf']['language'] = [{'@type': "Literal", 'value': lang, 'raw': lang} for lang in languages]

        # add subjects
        index_doc['rdf']['subject'] = [
            {'@type': "URIRef", 'id': str(subject), 'value': str(subject), 'raw': str(subject)} for subject
            in subjects]

        # add properties
        index_doc['rdf']['predicate'] = [
            {'@type': "URIRef", 'id': pred.uri_as_string, 'value': pred.qname, 'raw': pred.qname} for
            pred in predicates]

        # objects
        index_doc['rdf']['object'] = list(rdf_objects)

        # graph
        context_dict = {"{}".format(prefix): namespace for prefix, namespace in
                        self._graph.namespace_manager.namespaces()}
        # index_doc['rdf']['graph'] = self._graph.serialize(format='json-ld', context=context_dict).decode('utf-8')

        index_doc['about']['language'] = [{'@type': "Literal", 'value': lang, 'raw': lang} for lang in languages]
        points = ["{},{}".format(lat, lon) for lat, lon in get_geo_points(self._graph, only_geohash=False)]
        index_doc['about']['point'] = points
        index_doc['point'] = points
        captions = self.get_about_caption
        #  todo fix issue with lang being null
        # todo add about option
        index_doc['about']['caption'] = [
            {'@type': "Literal",
             'value': str(entry),
             'raw': str(entry),
             'lang': entry.language if entry.language else None}
            for entry in captions
            ]
        # todo remove rdf for now enable later  again
        del index_doc['rdf']
        for obj in self.get_all_items():
            index_doc[obj.predicate.search_label].append(obj.to_index_entry(nested=False))
        for key, val in index_doc.items():
            if isinstance(val, list):
                if all(isinstance(l, dict) for l in val):
                    if key in ['nave_deepZoomUrl', 'nave_thumbSmall', 'nave_thumbLarge', 'nave_thumbnail', 'edm_hasView']:
                        index_doc[key] = val
                    else:
                        index_doc[key] = sorted(val, key=itemgetter('raw'))
        return index_doc

    def to_index_doc(self):
        resource = self.get_about_resource()
        index_doc = {}
        about = defaultdict(list)

        rdf_class = [RDFPredicate(str(obj)) for obj in set(list(self._graph.objects(predicate=RDF.type))) if
                     isinstance(obj, URIRef)]
        languages = {obj.language for obj in self._graph.objects() if
                     isinstance(obj, Literal) and obj.language is not None}
        properties = {RDFPredicate(str(obj)) for obj in set(list(self._graph.predicates())) if
                      isinstance(obj, URIRef) and str(obj) not in settings.RDF_EXCLUDED_PROPERTIES}
        # add classes
        about['class'] = [{'@type': "URIRef", 'id': clzz.uri_as_string, 'value': clzz.qname, 'raw': clzz.qname} for
                          clzz in rdf_class]
        # add properties
        about['property'] = [{'@type': "URIRef", 'id': prop.uri_as_string, 'value': prop.qname, 'raw': prop.qname} for
                             prop in properties]
        # add languages
        about['language'] = [{'@type': "Literal", 'value': lang, 'raw': lang} for lang in languages]
        about['point'] = ["{},{}".format(lat, lon) for lat, lon in get_geo_points(self._graph, only_geohash=False)]
        caption = self.get_about_caption
        #  todo fix issue with lang being null
        about['caption'] = [
            {'@type': "Literal",
             'value': str(entry),
             'raw': str(entry),
             'lang': entry.language if entry.language else None}
            for entry in caption
            ]
        about['thumbnail'] = [
            {'@type': "URIRef", 'id': self.get_about_thumbnail}
        ] if self.get_about_thumbnail else []
        # add about
        index_doc['about'] = about
        if resource:
            index_doc.update(resource.to_index_entry())
        return index_doc


class RDFResource:
    """
    Each resource from a graph is represented by a resource
    """

    def __init__(self, subject_uri, graph, allowed_properties=None, excluded_properties=None,
                 bindings=None):
        self._bindings = bindings
        self.subject_uri = subject_uri if isinstance(subject_uri, URIRef) or isinstance(subject_uri, BNode) \
            else URIRef(subject_uri)
        self.graph = graph
        self._items = defaultdict(list)
        self._allowed_properties = self._as_uri(allowed_properties)
        self._excluded_properties = self._as_uri(excluded_properties)
        self._objects = None
        self._predicates = None
        self._rdf_types = None
        self._search_label_dict = defaultdict(list)

    def __getitem__(self, search_label):
        return self.get_first(search_label)

    def __str__(self):
        return self.get_uri()

    def _as_uri(self, property_list):
        if property_list:
            property_list = [URIRef(prop) for prop in property_list]
        return property_list

    def get_uri(self):
        return str(self.subject_uri)

    def get_label(self):
        label = self.graph.preferredLabel(
            subject=self.subject_uri,
            labelProperties=self._bindings.label_properties
        )
        if not label:
            langfilter = lambda l: True
            for labelProp in (DC.title, SKOS.prefLabel, RDFS.label, URIRef("http://www.geonames.org/ontology#name")):
                labels = list(filter(langfilter, self.graph.objects(predicate=labelProp)))
                if len(labels) == 0:
                    continue
                else:
                    label = [(labelProp, l) for l in labels]
                    break
        return [entry for prop, entry in label]

    def add_item(self, predicate_uri, rdf_object):
        if predicate_uri in [RDF.type]:
            return self._items
        if self._excluded_properties:
            if predicate_uri not in self._excluded_properties:
                self._items[predicate_uri].append(rdf_object)
        elif self._allowed_properties:
            if predicate_uri in self._allowed_properties:
                self._items[predicate_uri].append(rdf_object)
        else:
            self._items[predicate_uri].append(rdf_object)
        return self._items

    def _generate_rdf_objects_from_graph(self):
        """Generate dict with predicate URIRef as key and a list of RDFObject as value."""
        for predicate, rdf_object in self.graph.predicate_objects(subject=self.subject_uri):
            # todo add inline of enrichments
            self.add_item(
                predicate_uri=predicate,
                rdf_object=RDFObject(rdf_object, self.graph, RDFPredicate(predicate),
                                     bindings=self._bindings)
            )

    def get_types(self):
        if not self._rdf_types:
            types = list(set(self.graph.objects(subject=self.subject_uri, predicate=RDF.type)))
            if types:
                self._rdf_types = [RDFPredicate(rdf_type) for rdf_type in types]
            else:
                self._rdf_types = [RDFPredicate(RDF.Description)]
        return self._rdf_types

    def get_type(self):
        return self.get_types()[0]

    def is_web_resource(self):
        """Returns boolean if RDFResource is an edm:webresource"""
        return RDFPredicate(EDM.WebResource) in self.get_types()

    def is_ore_aggregation(self):
        """Returns boolean if RDFResource is an ore:aggregation"""
        return RDFPredicate(ORE.Aggregation) in self.get_types()

    def get_sort_key(self):
        """Return the nave:resourceSortOrder key."""
        order = self.get_first('nave_resourceSortOrder')
        if order:
            return int(str(order.value))
        return 0

    def get_list(self, search_label):
        if not self._search_label_dict:
            for predicate, rdf_objects in self.get_items().items():
                for rdf_object in rdf_objects:
                    self._search_label_dict[predicate.search_label].append(rdf_object)
        return self._search_label_dict.get(search_label, [])

    def get_first(self, search_label):
        objects = self.get_list(search_label)
        if objects:
            return objects[0]
        return None

    def get_first_literal(self, predicate, graph=None):
        if graph is None:
            graph = self._graph
        if not isinstance(predicate, URIRef):
            predicate = URIRef(predicate)
        for s, o in graph.subject_objects(subject=self.subject_uri, predicate=predicate):
            if isinstance(o, Literal):
                if o.datatype == URIRef('http://www.w3.org/2001/XMLSchema#boolean'):
                    return True if o.value in ['true', 'True'] else False
                elif o.datatype == URIRef('http://www.w3.org/2001/XMLSchema#integer'):
                    return int(o.value)
                else:
                    return o.value if not len(o.value) > 32766 else o.value[:32700]
        return None

    def get_items(self, sort=True, exclude_list=None, include_list=None, as_tuples=False):
        """Dict of RDFPredicate with List of RDFObject"""
        if len(self._items) == 0:
            self._generate_rdf_objects_from_graph()
        items = self._items
        for key, val in items.items():
            if isinstance(val, list):
                are_resources = all(v.get_resource for v in val )
                if key in [URIRef('http://www.europeana.eu/schemas/edm/hasView')] and are_resources:
                    items[key] = sorted(val, key=lambda k: k.get_resource.get_sort_key())
                else:
                    items[key] = sorted(val, key=lambda k: k.value)
        if sort:
            items = OrderedDict(sorted(list(items.items()), key=lambda t: t[0]))
        if include_list:
            items = {key: items[key] for key in list(items.keys()) if key in include_list}
        if exclude_list:
            items = {key: items[key] for key in list(items.keys()) if key not in exclude_list}
        if as_tuples:
            return [(RDFPredicate(predicate), rdf_object) for predicate, rdf_object in list(items.items())]
        return {RDFPredicate(predicate): rdf_object for predicate, rdf_object in list(items.items())}

    def get_predicates(self):
        if not self._predicates:
            self._predicates = [predicate for predicate in list(self.get_items().keys())]
        return self._predicates

    def get_objects(self):
        if not self._objects:
            items__values = list(self.get_items().values())
            self._objects = list(itertools.chain.from_iterable(items__values))
        return self._objects

    def has_geo(self):
        points = get_geo_points(self._graph, only_geohash=False)
        has_geoHash = NAVE.geoHash in self.get_predicates()
        return True if points or has_geoHash else False

    def has_content(self):
        return len(self.get_items()) > 0

    def get_exact_match_link(self, uri):
        if not isinstance(uri, URIRef):
            uri = URIRef(uri)
        if not self._bindings:
            return uri
        same_as = list(self._bindings._graph.objects(subject=uri, predicate=SKOS.exactMatch))
        if same_as:
            return same_as[0]
        return None

    def is_enrichment(self):
        """

        :return: Enrichment (bool), is_linked (bool)
        """
        if RDFPredicate(URIRef("http://schemas.delving.eu/narthex/terms/ProxyResource")) in self.get_types():
            available_predicates = self.get_predicates()
            if RDFPredicate(SKOS.exactMatch) in available_predicates:
                return True, True
            else:
                return True, False
        return False, False

    def __lt__(self, other):
        return self.get_type().qname < other.get_type().qname

    def get_types_as_index_entries(self):
        entries = []
        for rdf_type in self.get_types():
            entries.append(
                {
                    "@type": "URIRef",
                    "id": rdf_type.uri_as_string,
                    "value": rdf_type.qname,
                    "raw": rdf_type.qname
                }
            )
        return entries

    def to_index_entry(self):
        entries = defaultdict(list)
        entries['rdf_type'] = self.get_types_as_index_entries()
        for predicate, rdf_objects in self.get_items().items():
            obj_list = []
            for obj in rdf_objects:
                obj_list.append(obj.to_index_entry())
            obj_list = sorted(obj_list)
            entries[predicate.search_label] = obj_list
        return entries


class RDFPredicate():

    def __init__(self, uri):
        self._uri = uri
        self._manager = namespace_manager
        try:
            self._prefix, self._ns, self._label = self._manager.compute_qname(self._uri)
        except Exception as e:
            logger.error("Unable to compute qname".format(e))

    @property
    def uri(self):
        return self._uri

    @property
    def uri_as_string(self):
        return str(self._uri)

    @property
    def label(self):
        return self._label

    @property
    def ns(self):
        return str(self._ns)

    @property
    def prefix(self):
        return self._prefix

    @property
    def search_label(self):
        return self.qname.replace(':', '_')

    @property
    def qname(self):
        return self._manager.qname(self._uri)

    # def from_search_label(search_label):
    #     return

    def __str__(self):
        return self.qname

    def __eq__(self, other):
        return self.uri == other.uri

    def __lt__(self, other):
        return self.uri < other.uri

    def __hash__(self):
        return hash(self.uri)


class RDFObject:
    def __init__(self, rdf_object, graph, predicate, bindings=None):
        self._predicate = predicate
        self._rdf_object = rdf_object
        self._graph = graph
        self._object_type = None
        self._bindings = bindings
        self._is_inlined = False
        self._is_normalised = False
        self._lang = None
        self._resource = None
        self._inline_enrichment_link()

    def _inline_enrichment_link(self):
        """Inline empty enrichment links created by Narthex.

        When an skos:Concept enrichment is encountered that is inserted by Narthex without a skos:exactMatch mapping
        The link needs to be removed and the altLabel inlined as the value."""
        if self.has_resource:
            uri_id = self.id if not self.is_bnode else str(self._rdf_object)
            resource = self._bindings.get_resource(uri_ref=uri_id, obj=self)
            enrichment, is_linked = resource.is_enrichment()
            if enrichment and not is_linked:
                self._rdf_object = self.value
                self._is_normalised = True
            elif enrichment and is_linked:
                self._rdf_object = resource.get_exact_match_link(uri_id)
                self._bindings.mark_as_inline_resource(uri_id)
                self._is_inlined = True

    @property
    def object_type(self):
        """Give back the object type.

        Can be:
            * rdflib.UriRef
            * rdflib.Literal
            * rdflib.Bnode
        """
        if self._object_type is None:
            object_type = self._rdf_object.__class__
            if object_type in [URIRef, Literal, BNode]:
                self._object_type = object_type.__name__
            else:
                raise TypeError("{} is not supported as object_type".format(object_type))
        return self._object_type

    @property
    def datatype(self):
        """ give back the datatype if the object_type is a literal """
        if self.is_literal:
            return self._rdf_object.datatype
        return None

    def _get_graph_resources(self):
        if not self._graph_resources:
            self._graph_resources = set(self._graph.subjects())
        return self._graph_resources

    @property
    def predicate(self):
        return self._predicate

    @property
    def language(self):
        """ give back the language if the object_type is a literal """
        if not self._lang and self.is_literal and self._rdf_object.language:
            self._lang = self._rdf_object.language
        return self._lang

    @property
    def id(self):
        if self.is_uri or self.is_bnode:
            return str(self._rdf_object)
        return None

    @property
    def cache_url(self):
        if self.is_uri:
            uri = str(self._rdf_object)
            thumbnail_fields = self._bindings.get_thumbnail_fields()
            thumbnail_fields = thumbnail_fields + (
                URIRef('http://schemas.delving.eu/nave/terms/deepZoomUrl'),
                URIRef('http://www.europeana.eu/schemas/edm/isShownAt'),
            )
            if not RDFRecord.get_rdf_base_url() in uri and self._rdf_object not in thumbnail_fields:
                return get_cache_url(uri)
        return None

    @property
    def value(self):
        """ give back the value if the object_type is a literal """
        if self.is_literal:
            return self._rdf_object
        elif self.is_bnode:
            label = self.get_resource.get_label()
            if label:
                label = label[0]
                if label.language:
                    self._lang = label.language
                return label
            else:
                literal_string = str(self._rdf_object)
                if len(literal_string) > 32766:
                    literal_string = literal_string[:32700]
                return literal_string
        elif self.is_uri:
            return self.get_label(self._rdf_object)
        return None

    def get_label(self, rdf_object):
        label = self._graph.preferredLabel(
            subject=rdf_object,
            labelProperties=self._bindings.label_properties,
            default=[("raw", Literal(str(rdf_object)))]
        )
        label = label[0][1]
        if label.language:
            self._lang = label.language
        return label

    @property
    def resource_is_concept(self):
        if not self.has_resource:
            return False
        resource = self._bindings.get_resource(self._rdf_object)
        return RDFPredicate(SKOS.Concept) in resource.get_types()

    @property
    def resource_has_skos_definition(self):
        if not self.resource_is_concept:
            return False
        resource = self._bindings.get_resource(self._rdf_object)
        return RDFPredicate(SKOS.definition) in resource.get_predicates()

    def get_resource_field_value(self, field_name_uri):
        if not self.has_resource:
            return False
        predicate = URIRef(field_name_uri)
        graph_objects = self._graph.objects(subject=self._rdf_object, predicate=predicate)
        return [RDFObject(rdf_object, self._graph, RDFPredicate(predicate),
                          bindings=self._bindings) for rdf_object in graph_objects]

    @property
    def has_resource(self):
        # do not recurse on about
        not_follow_list = [FOAF.primaryTopic,
                           URIRef("http://www.openarchives.org/ore/terms/isAggregatedBy"),
                           URIRef("http://creativecommons.org/ns#attributionURL"),
                           URIRef("http://www.europeana.eu/schemas/edm/isShownAt")]
        try:
            about_uri = str(self._bindings.about_uri())
            if self.is_uri and URIRef(self.id) == about_uri:
                return False
            elif self.predicate.uri in not_follow_list:
                return False
        except AttributeError as ae:
            logger.debug("Bindings has not about_uri see: \n {}".format(ae))
            about_uri = None
            return False
        return self._bindings.has_resource(self._rdf_object, self) if self._bindings else False

    @property
    def get_resource(self):
        if not self.has_resource:
            return None
        if not self._resource:
            self._resource = self._bindings.get_resource(self._rdf_object)
        return self._resource

    @property
    def is_bnode(self):
        return isinstance(self._rdf_object, BNode)

    @property
    def is_literal(self):
        return isinstance(self._rdf_object, Literal)

    @property
    def is_uri(self):
        return isinstance(self._rdf_object, URIRef)

    def __str__(self):
        return "{} => {}".format(self.predicate.qname, self.value)

    def to_index_entry(self, nested=True, inlined=False):
        entry = {"@type": self.object_type}
        if self.is_uri:
            entry['id'] = self.id
        clean_value = str(self.value)
        if len(clean_value) > 32765:
            entry['value'] = str(self.value)[:32700]
        else:
            entry['value'] = str(self.value)
        raw_value = str(self.value)
        if len(raw_value) > 256:
            raw_value = raw_value[:256]
        entry['raw'] = str(raw_value).replace("\"", "'")
        if self.language:
            entry['lang'] = self.language
        if self.has_resource and nested:
            if inlined:
                # todo implement custom inlined views based on class
                pass
            else:
                entry['inline'] = self._bindings.get_resource(uri_ref=self.id, obj=self).to_index_entry()
        return entry

    def __lt__(self, other):
        """Sort function for RDFObjects."""
        return self.value < self.value


class RDFRecord:
    """"""

    DEFAULT_RDF_FORMAT = "nt" if not settings.RDF_DEFAULT_FORMAT else settings.RDF_DEFAULT_FORMAT

    def __init__(self, hub_id=None, source_uri=None,
                 spec=None, rdf_string=None,
                 org_id=None, doc_type=None,
                 named_graph_uri=None, graph=None):
        if hub_id is None and source_uri is None and rdf_string is None and named_graph_uri is None:
            raise ValueError("either source_uri or hub_id or rdf_string must be given at initialisation.")
        self._hub_id = hub_id
        self._spec = spec
        self._org_id = org_id if org_id is not None else settings.ORG_ID
        self._doc_type = doc_type
        self._source_uri = source_uri
        self._named_graph = named_graph_uri
        self._absolute_uri = None
        self._graph = graph
        self._rdf_string = rdf_string
        self._query_response = None
        self._modified_at = None
        self._bindings = None
        # self._setup_rdfrecord()

    def _setup_rdfrecord(self):
        if self._hub_id:
            self.get_graph_by_id(hub_id=self._hub_id)
        elif self._source_uri:
            self.get_graph_by_source_uri(uri=self._source_uri)

    @staticmethod
    def clean_local_id(raw_id, is_hub_id=False):
        local_id = raw_id.replace(":", "-").replace(" ", "-").replace("+", "-").replace("/", "-")
        if not is_hub_id:
            local_id = local_id.replace("_", "-")
        if "--" in local_id:
            local_id = re.sub("[-]{2,10}", "-", local_id)
        return local_id

    def exists(self):
        return self._graph is not None

    def last_modified(self):
        return self._modified_at

    @staticmethod
    def get_rdf_base_url(prepend_scheme=False, scheme="http"):
        base_url = settings.RDF_BASE_URL
        stripped_url = urlparse(base_url).netloc
        if stripped_url:
            base_url = stripped_url
        if prepend_scheme:
            base_url = "{}://{}".format(scheme, base_url)
        return base_url

    def uri_to_hub_id(self, source_uri=None):
        if not self._hub_id:
            if source_uri is None:
                source_uri = self.source_uri
            uri_parts = source_uri.split('/resource/')
            named_parts = uri_parts[-1]
            spec = local_id = None
            if len(named_parts) >= 3:
                rdf_type, spec, *local_id = named_parts.split('/')
            if self._spec is None and spec:
                self._spec = spec
            local_id = self.clean_local_id("/".join(local_id))
            self._hub_id = "{}_{}_{}".format(self._org_id, self._spec, local_id)
        return self._hub_id

    def from_rdf_string(self, named_graph=None, source_uri=None, rdf_string=None, input_format=DEFAULT_RDF_FORMAT):
        self._graph = self.parse_graph_from_string(rdf_string, named_graph, input_format)
        self._named_graph = named_graph
        self._source_uri = source_uri
        if input_format != self.DEFAULT_RDF_FORMAT:
            self._rdf_string = None
            self.rdf_string()
        else:
            self._rdf_string = rdf_string
        return self.get_graph()

    def get_triples(self, acceptance=False):
        return self.rdf_string, self.named_graph

    @staticmethod
    def parse_graph_from_string(rdf_string, graph_identifier=None, input_format=DEFAULT_RDF_FORMAT):
        g = ConjunctiveGraph(identifier=graph_identifier)
        from nave.lod import namespace_manager
        g.namespace_manager = namespace_manager
        g.parse(data=rdf_string, format=input_format)
        return g

    @staticmethod
    def get_external_rdf_url(internal_uri, request):
        """Convert the internal RDF base url to the external domain making the request. """
        parsed_target = urlparse(internal_uri)
        request_domain = request.get_host()
        entry_points = settings.RDF_ROUTED_ENTRY_POINTS
        if request_domain not in entry_points:
            request_domain = parsed_target.netloc
        return "http://{domain}{path}".format(domain=request_domain, path=parsed_target.path)

    @staticmethod
    def get_internal_rdf_base_uri(target_uri):
        """Converted web_uri to internal RDF base_url.

        The main purpose of this function is to enable routing from multiple external urls,
        but still use a single internal base url
        """
        parsed_target = urlparse(target_uri)
        domain = parsed_target.netloc
        entry_points = settings.RDF_ROUTED_ENTRY_POINTS
        if domain in entry_points:
            domain = RDFRecord.get_rdf_base_url()
        import urllib
        clean_path = urllib.parse.unquote(parsed_target.path)
        return "http://{domain}{path}".format(domain=domain, path=clean_path)

    def get_graph_by_id(self, hub_id, store_name=None, as_bindings=False):
        raise NotImplementedError("Implement me")

    def get_graph_by_source_uri(self, uri, store_name=None, as_bindings=False):
        raise NotImplementedError("Implement me")

    @property
    def named_graph(self):
        return self._named_graph

    @property
    def source_uri(self):
        if not self._source_uri and self.named_graph:
            self._source_uri = self.named_graph.replace('/graph', '')
        return self._source_uri

    @property
    def document_uri(self):
        return self.source_uri

    @property
    def absolute_uri(self, request=None):
        uri = self.source_uri
        if request:
            uri = self.get_external_rdf_url(uri, request)
        return uri

    @property
    def hub_id(self):
        if not self._hub_id and self.source_uri or self.named_graph:
            self._hub_id = self.uri_to_hub_id()
        if ":" in self._hub_id:
            self._hub_id = self._hub_id.replace(':', '-')
        return self._hub_id

    def get_bindings(self, graph=None):
        if not self._bindings:
            if graph is None:
                graph = self.get_graph()
            if graph:
                self._bindings = GraphBindings(self.source_uri, graph)
        return self._bindings

    def get_graph(self, **kwargs):
        if not self._graph and self._rdf_string:
            g = self.parse_graph_from_string(self._rdf_string)
            self._graph = g
        return self._graph

    @staticmethod
    def delete_webresource_graphs(spec, store=None):
        if not store:
            store = rdfstore.get_rdfstore()
        query = """
        DELETE {{
             GRAPH ?g {{
                ?s ?p ?o .
             }}
          }}
        WHERE {{ GRAPH ?g {{
          ?subject a <http://www.europeana.eu/schemas/edm/WebResource>;
              <http://schemas.delving.eu/narthex/terms/datasetSpec> "{spec}".
          }}
          GRAPH ?g {{
            ?s ?p ?o.
          }}}}
        """.format(spec=spec)
        return store.update(query=query)

    @staticmethod
    def get_webresource_context_graph(target_uri, store=None):
        if not store:
            store = rdfstore.get_rdfstore()
        query = """
        SELECT ?s ?p ?o ?g
        WHERE {{
          GRAPH ?g {{
                <{aggregation_uri}> <http://www.europeana.eu/schemas/edm/hasView> ?object
          }}
          GRAPH ?g {{
            ?s ?p ?o .
          }}
        }}
        """.format(aggregation_uri=target_uri)
        response = store.query(query=query)
        from nave.lod.models import RDFModel
        return RDFModel.get_graph_from_sparql_results(response, None)[0]

    @staticmethod
    def reduce_duplicates(graph: Graph, leave=0, predicates=None):
        """Reduce duplicates or all entries from a predicate from a Graph."""
        entries_removed = 0
        if predicates is None:
            predicates = [
                EDM.isShownBy, EDM.object, NAVE.thumbSmall, NAVE.thumbLarge,
                NAVE.thumbnail, NAVE.deepZoomUrl, EDM.hasView
            ]
        for predicate in predicates:
            entries = list(graph.subject_objects(predicate=predicate))
            if entries and len(entries) > leave:
                remove = entries if entries == 0 else entries[leave:]
                for s, o in remove:
                    graph.remove((s, predicate, o))
                    entries_removed += 1
        return graph, entries_removed

    @staticmethod
    def is_web_resource_api_call(uri):
        if "/api/webresource" in uri:
            base, query_params = uri.split('?', maxsplit=1)
            splitter = "&amp;" if "&amp;" in query_params else "&"
            params = query_params.split(splitter)
            query_dict = defaultdict()
            for param in params:
                k, v = param.split("=", maxsplit=1)
                query_dict[k] = v
            if 'uri' in query_dict and 'spec' in query_dict:
                uri = query_dict.get('uri')
                spec = query_dict.get('spec')
                return uri, spec
        return None

    @staticmethod
    def resolve_deepzoom_uri(graph, deepzoom_predicate=URIRef("http://schemas.delving.eu/nave/terms/deepZoomUrl")):
        """Replace API call for deepZoomUrl with direct link."""
        for s, o in graph.subject_objects(predicate=deepzoom_predicate):
            api_call = RDFRecord.is_web_resource_api_call(str(o))
            if api_call:
                from nave.webresource.webresource import WebResource
                uri, spec = api_call
                wr = WebResource(uri=uri, spec=spec)
                graph.remove((s, deepzoom_predicate, o))
                if wr.exists_source:
                    deep_zoom_url = wr.get_deepzoom_redirect()
                    if deep_zoom_url:
                        graph.add((s, deepzoom_predicate, Literal(deep_zoom_url)))
        return graph

    @staticmethod
    def resolve_webresource_uris(graph, source_check=True, bindings=None):
        """Add DeepZoom, and thumbnail derivatives to WebResource."""
        from rdflib.namespace import RDF
        web_resources = graph.subjects(
            predicate=RDF.type,
            object=URIRef("http://www.europeana.eu/schemas/edm/WebResource")
        )
        about_uri = list(
            graph.subjects(
                predicate=RDF.type,
                object=URIRef(
                    'http://www.openarchives.org/ore/terms/Aggregation'
                )
            )
        )
        if not about_uri:
            about_uri = [s for s in graph.subjects(predicate=EDM.hasView)]
        if about_uri and len(about_uri) > 0:
            about_uri = about_uri[0]
        else:
            about_uri = None
        # remove blank_nodes
        wr_list = []
        for wr in web_resources:
            if not isinstance(wr, URIRef):
                for p, o in graph.predicate_objects(subject=wr):
                    graph.remove((wr, p, o))
            else:
                wr_list.append(wr)
        has_api_call = any(str(wr).startswith('urn:') for wr in wr_list)

        if wr_list and has_api_call:
            # remove all others
            RDFRecord.reduce_duplicates(graph)
        elif wr_list:
            RDFRecord.reduce_duplicates(
                graph=graph,
                leave=0,
                predicates=[EDM.hasView]
            )
        for wr in wr_list:
            api_call = str(wr).startswith('urn:')
            if api_call and about_uri:
                uri = str(wr)
                spec = uri.split('/')[0].replace('urn:', '')
                from nave.webresource.webresource import WebResource
                web_resource = WebResource(uri=uri, spec=spec)
                if not source_check or web_resource.exists_source:
                    graph.add((
                        about_uri,
                        EDM.hasView,
                        URIRef(uri)
                    ))
                    api_call = "{}?spec={}&uri={}".format(
                        reverse('webresource'),
                        spec,
                        uri
                    )
                    if settings.WEB_RESOURCE_USE_RDF_BASE:
                        api_call = settings.RDF_BASE_URL + api_call
                    thumb_small = "{}&docType=thumbnail&width={}".format(
                        api_call,
                        settings.WEB_RESOURCE_THUMB_SMALL
                    )
                    thumb_large = "{}&docType=thumbnail&width={}".format(
                        api_call,
                        settings.WEB_RESOURCE_THUMB_LARGE
                    )
                    source_download = "{}&docType=thumbnail&width={}".format(
                        api_call,
                        settings.WEB_RESOURCE_MAX_SIZE
                    )
                    graph.add((
                        wr,
                        NAVE.thumbSmall,
                        Literal(thumb_small)
                    ))
                    graph.add((
                        wr,
                        NAVE.thumbLarge,
                        Literal(thumb_large)
                    ))
                    graph.add((
                        wr,
                        NAVE.thumbnail,
                        Literal(thumb_small)
                    ))
                    allow_source_download = graph.objects(
                        subject=wr,
                        predicate=NAVE.allowSourceDownload
                    )
                    add_source_download = all(
                        str(o).lower() == 'true' for o in allow_source_download
                    )
                    if add_source_download:
                        graph.add((
                            wr,
                            NAVE.sourceDownload,
                            Literal(source_download)
                        ))
                    deepzoom = reverse(
                        'webresource_deepzoom_resolve',
                        kwargs={'webresource': str(wr).replace('urn:', '')}
                    )
                    hosts = [
                        x for x in settings.ALLOWED_HOSTS
                        if 'hubs.delving.org' in x
                    ]
                    if settings.RDF_BASE_URL in settings.ALLOWED_HOSTS:
                        deepzoom_base = settings.RDF_BASE_URL
                    elif hosts:
                        deepzoom_base = "http://{}".format(hosts[0])
                    else:
                        deepzoom_base = 'http://localhost:8000'
                    graph.add((
                        wr,
                        NAVE.deepZoomUrl,
                        Literal(deepzoom_base + deepzoom)
                    ))
                    if isinstance(about_uri, URIRef):
                        graph.add((
                            about_uri,
                            EDM.isShownBy,
                            URIRef(thumb_large)
                        ))
                        graph.add((
                            about_uri,
                            EDM.object,
                            URIRef(thumb_small)
                        ))
            else:
                if bindings:
                    web_resources = bindings.get_sorted_webresources()
                    for wr in web_resources:
                        graph.add((
                            about_uri,
                            EDM.hasView,
                            wr.subject_uri
                        ))
        return wr_list, graph

    @staticmethod
    def get_context_graph_via_query(store=None, target_uri=None):
        if not store:
            store = rdfstore.get_rdfstore()
        bind = ""
        if target_uri:
            bind = "BIND(<{}> as ?s)".format(target_uri)
        query = """SELECT ?o ?p2 ?o2
                    WHERE
                      {{
                      {bind}
                        ?s ?p ?o
                        OPTIONAL
                          {{ ?o ?p2 ?o2 .}}
                      }}
                    LIMIT   500
               """.format(bind=bind)
        response = store.query(query=query)
        from nave.lod.models import RDFModel
        return RDFModel.get_graph_from_sparql_results(response)

    def get_context_graph(
        self, with_mappings=False, include_mapping_target=False,
        acceptance=False, target_uri=None, with_webresource=False,
        resolve_deepzoom_uri=False, with_sparql_context=False,
        source_check=False):
        """Get Graph instance with linked ProxyResources.

        :param target_uri: target_uri if you want a sub-selection of the whole graph
        :param acceptance: if the acceptance data should be listed
        :param include_mapping_target: Boolean also include the mapping target triples in graph
        :param with_mappings: Boolean integrate the ProxyMapping into the graph
        :param with_webresource: Boolean if webresources should be inserted from the triple store
        :param resolve_deepzoom_uri: Boolean add resolved webresource mapping to output
        :param with_sparql_context: Boolean if context should be resolved with a sparql query
        """
        if hasattr(settings, "RESOLVE_WEBRESOURCES_VIA_RDF") and isinstance(settings.RESOLVE_WEBRESOURCES_VIA_RDF, bool):
            with_webresource = settings.RESOLVE_WEBRESOURCES_VIA_RDF
        if hasattr(settings, "RESOLVE_CONTEXT_VIA_RDF") and isinstance(settings.RESOLVE_CONTEXT_VIA_RDF, bool):
            with_sparql_context = settings.RESOLVE_CONTEXT_VIA_RDF
        if hasattr(settings, "RESOLVE_WEBRESOURCES_VIA_MEDIAMANAGER") and isinstance(settings.RESOLVE_WEBRESOURCES_VIA_MEDIAMANAGER, bool):
            with_mediamanager = settings.RESOLVE_WEBRESOURCES_VIA_MEDIAMANAGER
        graph = self.get_graph()
        if with_mappings:
            from django.apps import apps
            ds_model = apps.get_model(app_label="void", model_name="DataSet")
            proxy_resource_model = apps.get_model(app_label="void", model_name="ProxyResource")
            ds = ds_model.objects.filter(spec=self.get_spec_name())
            if len(ds) > 0:
                ds = ds.first()
                proxy_resources, graph = proxy_resource_model.update_proxy_resource_uris(ds, graph)
                for proxy_resource in proxy_resources:
                    graph = graph + proxy_resource.to_graph(include_mapping_target=include_mapping_target)
        # todo add code for retrieving info from media manager
        if with_mediamanager:
            # use media manager
            webresource_graph = None
            for wr in graph.subjects(predicate=RDF.type, object=EDM.WebResource):
                if str(wr).startswith('urn:'):
                    full_url = '{}/api/webresource/{}/{}'.format(
                        settings.MEDIAMANAGER_URL,
                        settings.ORG_ID,
                        str(wr)
                    )
                    try:
                        #webresource_graph.parse(full_url)
                        pass
                    except Exception as ex:
                        logger.error("Unable to parse {} because of {}".format(
                            full_url,
                            ex
                        ))
            if webresource_graph:
                graph, _ = self.reduce_duplicates(graph)
                # add EDM.IsShownBy EDM.Object first from graph
                graph = graph + webresource_graph
        if with_webresource:
            webresource_graph = RDFRecord.get_webresource_context_graph(target_uri=self.source_uri)
            if webresource_graph:
                graph, _ = self.reduce_duplicates(graph)
                # clean isShownBy, object, thumbnail, thumbnailLarge, thumbnailSmall, deepZoomUrl
                graph = graph + webresource_graph
        # add context via SPARQL
        if with_sparql_context:
            context_graph, nr_levels = self.get_context_graph_via_query(target_uri=self.source_uri)
            if context_graph:
                graph = graph + context_graph

        _, graph = self.resolve_webresource_uris(
            graph,
            source_check=source_check,
            bindings=self.get_bindings())
        # reduce edm duplicates to one each
        graph, _ = self.reduce_duplicates(graph=graph, leave=1, predicates=[EDM.isShownBy, EDM.object, EDM.isShownAt])
        # create direct link to DeepZoom image
        if resolve_deepzoom_uri:
            graph = self.resolve_deepzoom_uri(graph)
        if target_uri and not target_uri.endswith("/about") and target_uri != self.source_uri:
            g = Graph(identifier=URIRef(self.named_graph))
            subject = URIRef(target_uri)
            for p, o in graph.predicate_objects(subject=subject):
                g.add((subject, p, o))
            graph = g
        return graph

    def rdf_string(self):
        if not self._rdf_string and self.get_graph():
            self._rdf_string = self.get_graph().serialize(
                format=self.DEFAULT_RDF_FORMAT,
                encoding="utf-8").decode(encoding="utf-8")
        return self._rdf_string

    def get_spec_name(self):
        if self._spec is None:
            uri_parts = self.source_uri.split('/')
            if "aggregation" in uri_parts:
                self._spec = uri_parts[-2]
        return self._spec

    def create_sparql_update_query(self, delete=False, acceptance=False):
        sparql_update = """DROP SILENT GRAPH <{graph_uri}>;
        INSERT DATA {{ GRAPH <{graph_uri}> {{
            {triples}
            }}
        }};
        """.format(
            graph_uri=self.named_graph,
            triples=self.rdf_string()
        )
        if delete:
            sparql_update = """DROP SILENT GRAPH <{graph_uri}>;""".format(graph_uri=self.named_graph)
        return sparql_update

    def create_es_action(self, doc_type, record_type, action="index",
                         index=settings.SITE_NAME, store=None,
                         context=True, flat=True, exclude_fields=None,
                         acceptance=False, content_hash=None):

        if not store:
            store = rdfstore.get_rdfstore()

        if acceptance:
            index = "{}_acceptance".format(index)

        if record_type == "http://www.openarchives.org/ore/terms/Aggregation":
            record_type = "mdr"

        if action == "delete":
            return {
                '_op_type': action,
                '_index': index,
                '_type': doc_type,
                '_id': self.hub_id
            }

        graph = None

        if not context:
            graph = self.get_graph()
        else:
            graph = self.get_context_graph()
            graph.namespace_manager = namespace_manager
            self._graph = graph
            self._rdf_string = None

        bindings = self.get_bindings(graph=graph)
        index_doc = bindings.to_flat_index_doc() if flat else bindings.to_index_doc()
        if exclude_fields:
            index_doc = {k: v for k, v in index_doc.items() if k not in exclude_fields}
        # add delving spec for default searchability
        index_doc["delving_spec"] = [
            {'@type': "Literal",
             'value': self.get_spec_name(),
             'raw': self.get_spec_name(),
             'lang': None}
        ]
        logger.debug(index_doc)
        mapping = {
            '_op_type': action,
            '_index': index,
            '_type': doc_type,
            '_id': self.hub_id,
            '_source': index_doc
        }
        thumbnail = bindings.get_about_thumbnail
        mapping['_source']['system'] = {
            'slug': self.hub_id,
            'spec': self.get_spec_name(),
            'thumbnail': thumbnail if thumbnail else "",
            'preview': "detail/foldout/{}/{}".format(doc_type, self.hub_id),
            'caption': bindings.get_about_caption if bindings.get_about_caption else "",
            'about_uri': self.source_uri,
            'source_uri': self.source_uri,
            'graph_name': self.named_graph,
            'created_at': datetime.now().isoformat(),
            'modified_at': datetime.now().isoformat(),
            'source_graph': self.rdf_string(),
            'proxy_resource_graph': None,
            'web_resource_graph': None,
            'content_hash': content_hash,
            'hasGeoHash': "true" if bindings.has_geo() else "false",
            'hasDigitalObject': "true" if thumbnail else "false",
            'hasLandingePage': "true" if 'edm_isShownAt' in index_doc else "false",
            'hasDeepZoom': "true" if 'nave_deepZoom' in index_doc else "false",
            # 'about_type': [rdf_type.qname for rdf_type in bindings.get_about_resource().get_types()]
            # 'collections': None, todo find a way to add collections via link
        }
        data_owner = bindings.get_first_literal(EDM.dataProvider)
        dataset_name = self.dataset.name if hasattr(self, 'dataset') else None
        mapping['_source']['legacy'] = {
            'delving_hubId': self.hub_id,
            'delving_recordType': record_type,
            'delving_spec': self.get_spec_name(),
            'delving_owner': data_owner,
            'delving_orgId': settings.ORG_ID,
            'delving_collection': dataset_name,
            'delving_title': bindings.get_first_literal(DC.title),
            'delving_creator': bindings.get_first_literal(DC.creator),
            # 'delving_description': bindings.get_first_literal(DC.description),
            'delving_provider': bindings.get_first_literal(EDM.provider),
            'delving_hasGeoHash': "true" if bindings.has_geo() else "false",
            'delving_hasDigitalObject': "true" if thumbnail else "false",
            'delving_hasLandingePage': "true" if 'edm_isShownAt' in index_doc else "false",
            'delving_hasDeepZoom': "true" if 'nave_deepZoom' in index_doc else "false",
        }
        return mapping

    @staticmethod
    def delete_from_index(spec, index='{}'.format(settings.SITE_NAME)):
        """Delete all dataset records from the Search Index. """
        query_string = {
            "query": {
                "simple_query_string" : {
                    "query": "\"{}\"".format(spec),
                    "fields": ["system.spec.raw"],
                    "default_operator": "and"
                }
            }
        }
        response = client.delete_by_query(index=index, body=query_string)
        logger.info("Deleted {} from Search index with message: {}".format(spec, response))
        return response

    @staticmethod
    def remove_orphans(spec, timestamp, index='{}'.format(settings.SITE_NAME)):
        """
        date_string.isoformat()"""
        # make sure you don't erase things from the same second
        logger.info("Timestamp for orphan deletion: {}".format(timestamp))
        if not settings.LEGACY_ORPHAN_CONTROL:
            return 0
        client.indices.refresh(index)
        sleep(3)
        orphan_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "system.modified_at": {"lte": timestamp}
                            }
                        },
                        {
                            "match": {
                                "system.spec.raw": spec
                            }
                        }

                    ]
                }
            }
        }
        logger.info("Delete before: {}".format(timestamp))
        response = client.delete_by_query(index=index, body=orphan_query)
        orphan_counter = response['deleted']
        logger.info(
            'Deleted {} orphans from Search index with message: {}'.format(
                spec, response
            )
        )
        return orphan_counter

    def get_more_like_this(self):
        raise NotImplementedError("implement me")

    @staticmethod
    def get_geo_points(graph):
        return get_geo_points(graph)

    class Meta:
        abstract = True


class ElasticSearchRDFRecord(RDFRecord):
    """RDF resolved using ElasticSearch as its backend."""

    @staticmethod
    def get_rdf_records_from_query(query, response=None):
        if response is None:
            response = query.execute()
        record_list = []
        for hit in response.hits.hits:
            record = ElasticSearchRDFRecord(
                hub_id=hit['_id'],
                doc_type=hit['_type']
            )
            record.set_defaults_from_query_result(es_record=hit)
            record_list.append(record)
        return record_list

    def set_defaults_from_query_result(self, es_record):
        self._query_response = es_record
        self._doc_type = self._query_response['_type']
        system_fields = self._query_response['_source']['system']
        self._rdf_string = system_fields['source_graph']
        self._named_graph = system_fields['graph_name']
        self._source_uri = system_fields['source_uri']
        self._spec = system_fields.get('delving_spec')
        self._hub_id = system_fields.get('slug')
        self._modified_at = system_fields.get('modified_at')
        return self

    def query_for_graph(self, query_type=None, query=None, store_name=None, as_bindings=False, raw_query=None):
        if store_name is None:
            store_name = settings.SITE_NAME
        if raw_query:
            s = Search(index=store_name).using(client).query(raw_query)
        else:
            s = Search(index=store_name).using(client).query(query_type, **query)
        # s = s[:1] # todo use terminate after later
        response = s.execute()
        if response.hits.total != 1:
            return None
        self.set_defaults_from_query_result(response.hits.hits[0])
        if as_bindings:
            return GraphBindings(about_uri=self._source_uri, graph=self.get_graph())
        return self.get_graph()

    def is_indexed_content_identical(self, content_hash, hub_id=None, store_name=None):
        if hub_id is None:
            hub_id = self.hub_id
        query = Q("match", **{"_id": hub_id}) & Q("match", **{'system.content_hash': content_hash})
        exists = self.query_for_graph(raw_query=query, store_name=store_name)
        return True if exists is not None else False

    def get_graph_by_id(self, hub_id, store_name=None, as_bindings=False):
        return self.query_for_graph("match", {"_id": hub_id}, store_name, as_bindings)

    def get_graph_by_source_uri(self, uri, store_name=None, as_bindings=False):
        return self.query_for_graph(
            "match",
            {"system.source_uri.raw": uri},
            store_name=store_name,
            as_bindings=as_bindings
        )

    @staticmethod
    def get_query_value_dict(query_fields, graph_bindings):
        """Return a Dict with query fields and their value from the graph_bindings."""
        return {field: graph_bindings.get_list(field.replace('.raw', '')) for field in query_fields}

    @staticmethod
    def get_query_value_query_list(query_fields, graph_bindings):
        """Return a list of ElasticSearch Queries"""
        query_values = ElasticSearchRDFRecord.get_query_value_dict(query_fields, graph_bindings)
        query_list = []
        for k, v in query_values.items():
            for field_value in v:
                query_list.append(Q('match', **{k: str(field_value.value)}))
        return query_list

    def get_raw_related(self, query_fields, filter_query, graph_bindings, store_name=None):
        """Return a List of Nave items based on  the values from the query_fields extracted from the GraphBindings."""
        if store_name is None:
            store_name = settings.SITE_NAME
        query_list =  self.get_query_value_query_list(query_fields, graph_bindings)
        if not query_list:
            return []
        s = Search(using=client, index=store_name)
        must_not_list = []
        if self.hub_id:
            must_not_list.append(Q("match", _id=self.hub_id))
        related_query = s.query(
            'bool',
            should=query_list,
            must_not=must_not_list
        )
        if filter_query:
            for k, v in filter_query.items():
                related_query = related_query.filter("term", **{k: v})
        hits = related_query.execute()
        items = []
        for item in hits.hits:
            from nave.search.search import NaveESItemWrapper
            nave_item = NaveESItemWrapper(item)
            items.append(nave_item)
        return items

    def get_more_like_this(self, mlt_count=15, mlt_fields=None,
                           filter_query=None, wrapped=True, converter=None):
        return self.es_related_items(self.hub_id, doc_type=self._doc_type,
                                     mlt_count=mlt_count,  mlt_fields=mlt_fields,
                                     filter_query=filter_query, wrapped=wrapped,
                                     converter=converter)

    def es_related_items(self, hub_id, doc_type=None, mlt_fields=None,
                         store_name=None, mlt_count=5, filter_query=None,
                         wrapped=True, converter=None):
        if store_name is None:
            store_name = settings.SITE_NAME
        if mlt_fields is None or not isinstance(mlt_fields, list):
            mlt_fields = getattr(settings, "MLT_FIELDS", None)
            if mlt_fields is None:
                logger.warn("MLT_FIELDS should be defined for MLT functionality.")
                return ""
        s = Search(using=client, index=store_name)
        mlt_query = s.query(
            'more_like_this',
            fields=mlt_fields,
            min_term_freq=1,
            max_query_terms=12,
            include=False,
            docs=[{
                "_index": store_name,
                "_type": doc_type,
                "_id": hub_id
            }]
        )[:mlt_count]
        if filter_query:
            for k, v in filter_query.items():
                mlt_query = mlt_query.filter("term", **{k: v})
        hits = mlt_query.execute()
        items = []
        for item in hits.hits:
            if wrapped:
                from nave.search.search import NaveESItemWrapper
                nave_item = NaveESItemWrapper(item, converter=converter)
            else:
                from nave.search.search import NaveESItem
                nave_item = NaveESItem(item, converter=converter)
            items.append(nave_item)
        return items
