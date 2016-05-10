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
from urllib.error import HTTPError

import elasticsearch
import os
import logging
from urllib.parse import urlparse, quote

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import RDF, SKOS, RDFS, DC, FOAF

from lod import namespace_manager
from lod.utils import rdfstore

logger = logging.getLogger(__file__)
client = Elasticsearch()


Predicate = namedtuple('Predicate', ['uri', 'label', 'ns', 'prefix'])
Object = namedtuple('Object', ['value', 'is_uriref', 'is_resource', 'datatype', 'language', 'predicate'])


def get_geo_points(graph):
    try:
        lat_list = [float(str(lat)) for lat in
                    graph.objects(predicate=URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#lat"))]
        lon_list = [float(str(lon)) for lon in
                    graph.objects(predicate=URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#long"))]
    except ValueError as ve:
        logger.error("Unable to get geopoints because of {}".format(ve.args))
        return []
    zipped = zip(lat_list, lon_list)
    if not lat_list and not lon_list:
        return []
    return [list(elem) for elem in list(zipped)]


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
                                   URIRef('http://schemas.delving.eu/narthex/terms/proxyLiteralValue'))):
        self.aggregate_edm_blank_nodes = aggregate_edm_blank_nodes
        self._label_properties = label_properties
        self._allowed_properties = allowed_properties
        self._excluded_properties = excluded_properties
        self._allowed_rdf_types = allowed_rdf_types
        self._excluded_rdf_types = excluded_rdf_types
        self._graph = graph
        self._about_uri = URIRef(about_uri)
        self._resources = self._create_resources()
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

    def get_uri_from_search_label(self, search_label):
        """Convert search_label back into a URI."""
        if not search_label or '_' not in search_label:
            return None
        prefix, label = search_label.split('_')
        namespace_dict = dict(list(namespace_manager.namespaces()))
        uri = namespace_dict.get(prefix)
        return os.path.join(uri, label)

    def get_all_items(self):
        if not self._items:
            resources = [resource.get_items().values() for uri, resource in self.get_resources().items() if
                         uri not in self._inlined_resources]
            objects = list(itertools.chain.from_iterable(resources))
            self._items = list(set(itertools.chain.from_iterable(objects)))
        return self._items

    def get_all_skos_links(self):
        linked_skos_query =  """
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
                    return o.value
        return None

    def get_list(self, search_label):
        if not self._search_label_dict:
            for rdf_object in self.get_all_items():
                self._search_label_dict[rdf_object.predicate.search_label].append(rdf_object)
        return self._search_label_dict.get(search_label, [])

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
        points = get_geo_points(self._graph)
        return True if points else False

    def _add_to_call_queue(self, uri_ref, obj=None):
        if obj:
            self._call_queue[str(uri_ref)].append(obj)

    def get_resource(self, uri_ref, obj=None):
        """ Get a resource from resource dict.

        :param uri_ref:  URIRef from the graph
        :return: lod.utils.RDFResource
        """
        uri = BNode(uri_ref) if not uri_ref.startswith('http://')  else URIRef(uri_ref)
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
        thumbnail_fields = [
            URIRef('http://www.europeana.eu/schemas/edm/object'),
            FOAF.depiction,
            URIRef('http://www.europeana.eu/schemas/edm/isShownBy'),
            URIRef('http://schemas.delving.eu/nave/terms/thumbSmall'),
            URIRef('http://schemas.delving.eu/nave/terms/thumbLarge'),
            URIRef('http://schemas.delving.eu/nave/terms/thumbnail'),
        ]
        thumbnail = None
        for thumb in thumbnail_fields:
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
        points = ["{},{}".format(lat, lon) for lat, lon in get_geo_points(self._graph)]
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
        about['point'] = ["{},{}".format(lat, lon) for lat, lon in get_geo_points(self._graph)]
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

    def get_items(self, sort=True, exclude_list=None, include_list=None, as_tuples=False):
        """Dict of RDFPredicate with List of RDFObject"""
        if len(self._items) == 0:
            self._generate_rdf_objects_from_graph()
        items = self._items
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
        return RDFPredicate('http://www.w3.org/2003/01/geo/wgs84_pos#lat') in self.get_predicates()

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
            for obj in rdf_objects:
                entries[predicate.search_label].append(obj.to_index_entry())
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
            # todo: check if this works correctly
            if not RDFRecord.get_rdf_base_url() in uri:
                return get_cache_url(uri)
        return None

    @property
    def value(self):
        """ give back the value if the object_type is a literal """
        if self.is_literal:
            return self._rdf_object.value
        elif self.is_bnode:
            return str(self._rdf_object)
        elif self.is_uri:
            # todo give back label + uri
            label = self._graph.preferredLabel(
                subject=self._rdf_object,
                labelProperties=self._bindings.label_properties,
                default=[("raw", Literal(str(self._rdf_object)))]
            )
            label = label[0][1]
            if label.language:
                self._lang = label.language
            return label
        return None

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
        entry['value'] = entry['raw'] = str(self.value)
        if self.language:
            entry['lang'] = self.language
        if self.has_resource and nested:
            if inlined:
                # todo implement custom inlined views based on class
                pass
            else:
                entry['inline'] = self._bindings.get_resource(uri_ref=self.id, obj=self).to_index_entry()
        return entry


class RDFRecord:
    """"""

    DEFAULT_RDF_FORMAT = "nt" if not settings.RDF_DEFAULT_FORMAT else settings.RDF_DEFAULT_FORMAT

    def __init__(self, hub_id=None, source_uri=None, spec=None, rdf_string=None, org_id=None):
        if hub_id is None and source_uri is None and rdf_string is None:
            raise ValueError("either source_uri or hub_id or rdf_string must be given at initialisation.")
        self._hub_id = hub_id
        self._spec = spec
        self._org_id = org_id if org_id is not None else settings.ORG_ID
        self._source_uri = source_uri
        self._named_graph = None
        self._source_uri = None
        self._absolute_uri = None
        self._graph = None
        self._rdf_string = rdf_string
        self._query_response = None
        self._bindings = None
        # self._setup_rdfrecord()

    def _setup_rdfrecord(self):
        if self._hub_id:
            self.get_graph_by_id(hub_id=self._hub_id)
        elif self._source_uri:
            self.get_graph_by_source_uri(uri=self._source_uri)

    def exists(self):
        return self._graph is not None

    @staticmethod
    def get_rdf_base_url(prepend_scheme=False, scheme="http"):
        base_url = settings.RDF_BASE_URL
        stripped_url = urlparse(base_url).netloc
        if stripped_url:
            base_url = stripped_url
        if prepend_scheme:
            base_url = "{}://{}".format(scheme, base_url)
        return base_url

    def source_uri_as_hub_id(self, source_uri=None):
        if not self._hub_id:
            if source_uri is None:
                source_uri = self._source_uri
            uri_parts = source_uri.split('/')
            if self._spec is None:
                self._spec = uri_parts[-2]
            local_id = uri_parts[-1]
            self._hub_id = "{}_{}_{}".format(self._org_id, self._spec, local_id)
        return self._hub_id

    def from_rdf_string(self, named_graph=None, source_uri=None, rdf_string=None, input_format=DEFAULT_RDF_FORMAT):
        self._graph = self.parse_graph_from_string(rdf_string, named_graph, input_format)
        self._named_graph = named_graph
        self._source_uri = source_uri
        self._rdf_string = rdf_string
        return self._graph

    @staticmethod
    def parse_graph_from_string(rdf_string, graph_identifier=None, input_format=DEFAULT_RDF_FORMAT):
        g = Graph(identifier=graph_identifier)
        from lod import namespace_manager
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
        return "http://{domain}{path}".format(domain=domain, path=parsed_target.path)

    def get_graph_by_id(self, hub_id, store_name=None, as_bindings=False):
        raise NotImplementedError("Implement me")

    def get_graph_by_source_uri(self, uri, store_name=None, as_bindings=False):
        raise NotImplementedError("Implement me")

    @property
    def named_graph(self):
        return self._named_graph

    @property
    def source_uri(self):
        if not self._source_uri:
            self._source_uri = self.named_graph.replace('/graph', '')
        return self._source_uri

    @property
    def absolute_uri(self):
        pass

    @property
    def hub_id(self):
        if not self._hub_id and self.source_uri:
            self._hub_id = self.source_uri_as_hub_id()
        return self._hub_id

    def get_bindings(self):
        if not self._bindings:
            graph = self.get_graph()
            if graph:
                self._bindings = GraphBindings(self.source_uri, graph)
        return self._bindings

    def get_graph(self, **kwargs):
        return self._graph

    def get_context_graph(self, store, named_graph):
        return Graph(), 0

    def rdf_string(self):
        if not self._rdf_string and self.get_graph():
            self._rdf_string = self.get_graph().serialize(
                format=self.DEFAULT_RDF_FORMAT,
                encoding="utf-8").decode(encoding="utf-8")
        return self._rdf_string

    def get_spec_name(self):
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

    def create_es_action(self, doc_type, record_type, action="index", index=settings.SITE_NAME, store=None,
                         context=True, flat=True, exclude_fields=None, acceptance=False):

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
            graph, nr_levels = self.get_context_graph(store=store, named_graph=self.named_graph)
            graph.namespace_manager = namespace_manager

        bindings = self.get_bindings()
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
            # 'about_type': [rdf_type.qname for rdf_type in bindings.get_about_resource().get_types()]
            # 'collections': None, todo find a way to add collections via link
        }
        data_owner = self.dataset.data_owner if hasattr(self, 'dataset') else None
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
            'delving_description': bindings.get_first_literal(DC.description),
            'delving_provider': index_doc.get('edm_provider')[0].get('value') if 'edm_provider' in index_doc else None,
            'delving_hasGeoHash': "true" if bindings.has_geo() else "false",
            'delving_hasDigitalObject': "true" if thumbnail else "false",
            'delving_hasLandingePage': "true" if 'edm_isShownAt' in index_doc else "false",
            'delving_hasDeepZoom': "true" if 'nave_deepZoom' in index_doc else "false",
        }
        return mapping

    @staticmethod
    def remove_orphans(spec, timestamp):
        """
        date_string.isoformat()"""
        # make sure you don't erase things from the same second
        sleep(1)
        orphan_query = {"query": {"nested": {
            "path": "system",
            "score_mode": "avg",
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
                                "system.spec": spec
                            }
                        }

                    ]
                }
            }
        }}}
        orphan_counter = 0
        # todo later implement this as with the bulk api and es_actions
        for rec in elasticsearch.helpers.scan(client, orphan_query):
            _id = rec.get('_id')
            _index = rec.get('_index')
            _doc_type = rec.get('_type')
            client.delete(index=_index, doc_type=_doc_type, id=_id)
        return orphan_counter



    @staticmethod
    def get_geo_points(graph):
        return get_geo_points(graph)

    class Meta:
        abstract = True


class ElasticSearchRDFRecord(RDFRecord):
    """RDF resolved using ElasticSearch as its backend."""

    def get_absolute_uri(self):
        pass

    def get_named_graph(self):
        pass

    @property
    def source_uri(self):
        return self._source_uri

    def query_for_graph(self, query_type, query, store_name=None, as_bindings=False):
        if store_name is None:
            store_name = settings.SITE_NAME
        s = Search(index=store_name).using(client).query(query_type, **query)
        response = s.execute()
        if response.hits.total != 1:
            return None
        self._query_response = response.hits.hits[0]
        system_fields = self._query_response['_source']['system']
        self._rdf_string = system_fields['source_graph']
        self._named_graph = system_fields['graph_name']
        self._source_uri = system_fields['source_uri']
        self._spec = system_fields.get('delving_spec')
        self._hub_id = system_fields.get('slug')
        g = self.parse_graph_from_string(self._rdf_string, self._named_graph)
        self._graph = g
        if as_bindings:
            return GraphBindings(about_uri=self._source_uri, graph=self._graph)
        return self._graph

    def get_graph_by_id(self, hub_id, store_name=None, as_bindings=False):
        return self.query_for_graph("match", {"_id": hub_id}, store_name, as_bindings)

    def get_graph_by_source_uri(self, uri, store_name=None, as_bindings=False):
        return self.query_for_graph(
            "match",
            {"system.source_uri.raw" : uri},
            store_name=store_name,
            as_bindings=as_bindings
        )
