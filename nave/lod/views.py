# -*- coding: utf-8 -*-
import json
import logging
import os
import re

import requests
from django import http
from django.apps import apps
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirectBase, HttpResponse, Http404, HttpResponseNotAllowed, \
    HttpResponseBadRequest
from django.shortcuts import redirect
from django.views.generic import TemplateView, RedirectView, View
from rdflib.namespace import SKOS, RDF


import nave
from nave.lod import RDF_SUPPORTED_MIME_TYPES, USE_EDM_BINDINGS
from nave.lod.tests.resources import sparqlwrapper_result
from nave.lod import utils
from nave.lod.utils import rdfstore
from nave.lod.utils.resolver import GraphBindings, RDFRecord
from nave.lod.utils.mimetype import best_match
from nave.lod.utils.mimetype import extension_to_mime, HTML_MIME, mime_to_extension,\
    result_extension_to_mime
from nave.lod.utils.rdfstore import get_rdfstore, UnknownGraph
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from nave.lod.utils.resolver import ElasticSearchRDFRecord

from .serializers import UserGeneratedContentSerializer
from .models import SPARQLQuery, RDFPrefix, RDFModel, CacheResource, UserGeneratedContent
from .tasks import retrieve_and_cache_remote_lod_resource

logger = logging.getLogger(__name__)


def get_lod_mime_type(extension, request):
    """
    return the LoD mime-type from the request
    """
    if extension:
        file_extension, mime_type = extension_to_mime(extension)
    else:
        mime_type = best_match(RDF_SUPPORTED_MIME_TYPES, request.META.get("HTTP_ACCEPT"))
    return mime_type


class HttpResponseSeeOtherRedirect(HttpResponseRedirectBase):
    """
    HTTPResponse 303

    Status code 303 is not supported by Django out of the box and in grouped under 302.
    Since the LoD content negotiation expects an explicit 303, we will use this subclass
    in the RedirectViews
    """
    status_code = 303


class HubIDRedirectView(RedirectView):
    permanent = False
    query_string = False

    def get_redirect_url(self, *args, **kwargs):
        hub_id = self.kwargs.get('hubId')
        if not hub_id:
            if 'hubId' in self.query_string:
                hub_id = self.query_string.get('hubId')
            else:
                raise Http404()
        if 'doc_type' in self.kwargs:
            doc_type = self.kwargs.get('doc_type')
        else:
            doc_type = "void_edmrecord"
        record = ElasticSearchRDFRecord(hub_id=hub_id)
        graph = record.get_graph_by_id(hub_id=hub_id)
        if not graph:
            raise Http404()
        routed_uri = record.get_external_rdf_url(record.source_uri, self.request)
        logger.debug("Routed uri: {}".format(routed_uri))
        rdf_format = self.request.GET.get("format")
        if rdf_format and rdf_format in nave.lod.RDF_SUPPORTED_EXTENSIONS:
            routed_uri = "{}.{}".format(routed_uri, rdf_format)
        return routed_uri


class LoDRedirectView(RedirectView):
    """
    The Redirect view does the content negotiation for a Linked Open Data request.

    When no content-type is requested or no content-extension specified, all traffic will be routed to the HTML view
    at '/page'.

    When a content type or extension is specified, all traffic will be routed to the data view
    """
    permanent = False
    query_string = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Do ContentNegotiation for some resource and
        redirect to the appropriate place
        """
        label = self.kwargs.get('label')
        type_ = self.kwargs.get('type_')
        url_kwargs = {'label': label}
        extension_ = self.kwargs.get('extension')
        mimetype = get_lod_mime_type(extension_, self.request)

        if mimetype and mimetype in RDF_SUPPORTED_MIME_TYPES:
            path = "lod_data_detail"
            url_kwargs['extension'] = mime_to_extension(mimetype)
        elif USE_EDM_BINDINGS and type_ in ["aggregation"]:
            path = "edm_lod_page_detail"
            return reverse(path, kwargs=url_kwargs)
        else:
            path = "lod_page_detail"

        if type_:
            path = "typed_{}".format(path)
            url_kwargs['type_'] = type_

        return reverse(path, kwargs=url_kwargs)

    def get(self, request, *args, **kwargs):
        url = self.get_redirect_url(*args, **kwargs)
        if url:
            if self.permanent:
                return http.HttpResponsePermanentRedirect(url)
            else:
                return HttpResponseSeeOtherRedirect(url)
        else:
            logger.warning('Gone: %s', self.request.path,
                           extra={
                               'status_code': 410,
                               'request': self.request
                           })


class LoDDataView(View):
    store = get_rdfstore()

    def get_graph(self, mode, **kwargs):
        if mode == "graph" and 'named_graph' in kwargs:
            graph = self.store.get_graph_store.get(named_graph=kwargs['named_graph'], as_graph=True)
        elif mode == 'describe' and 'uri' in kwargs:
            graph = self.store.describe(uri=kwargs['uri'])
        elif mode in ['context', 'api', 'api-flat']:
            if 'named_graph' in kwargs:
                graph, _ = ElasticSearchRDFRecord.get_context_graph(self.store, named_graph=kwargs['named_graph'])
            else:
                graph, _ = ElasticSearchRDFRecord.get_context_graph(self.store, target_uri=kwargs['uri'])
        else:
            raise ValueError("Mode {} not supported".format(mode))
        return graph

    def get_mode(self, request, default=None):
        params = request.GET
        return params.get('display', default)

    def get(self, request, *args, **kwargs):
        target_uri = os.path.splitext(request.build_absolute_uri())[0].replace('/data/', '/resource/')
        if not self.request.path.startswith("/data"):
            target_uri = re.sub('/[a-z]{2}/resource/', '/resource/', target_uri, count=1)
        if target_uri.endswith('graph'):
            target_uri = re.sub("/graph", "", target_uri)
        extension_ = self.kwargs.get('extension')

        rdf_format = mime_to_extension(get_lod_mime_type(extension_, self.request))
        if rdf_format == "rdf":
            rdf_format = "xml"

        resolved_uri = RDFRecord.get_internal_rdf_base_uri(target_uri)
        if "/resource/cache/" in target_uri:
            # old lookup rdfstore.get_rdfstore().get_cached_source_uri(target_uri)
            target_uri = target_uri.split('/resource/cache/')[-1]
            if 'geonames.org' in target_uri:
                target_uri = '{}/'.format(target_uri)
            if CacheResource.objects.filter(document_uri=target_uri).exists():
                cache_object = CacheResource.objects.filter(document_uri=target_uri).first()
                graph = cache_object.get_graph()
                content = graph.serialize(format=rdf_format)
            else:
                raise UnknownGraph("URI {} is not known in our graph store".format(target_uri))
        elif settings.RDF_USE_LOCAL_GRAPH:
            mode = self.request.GET.get('mode', 'default')
            acceptance = True if mode == 'acceptance' else False
            local_object = ElasticSearchRDFRecord(source_uri=resolved_uri)
            local_object.get_graph_by_source_uri(uri=resolved_uri)
            if not local_object.exists():
                # todo: temporary work around for EDMRecords not saved with subjects
                logger.warn("Unable to find graph for: {}".format(resolved_uri))
                raise UnknownGraph("URI {} is not known in our graph store".format(resolved_uri))
            mode = self.get_mode(request)
            if mode in ['context', 'api', 'api-flat', 'es-action', 'posthook']:
                # get_graph(with_mappings=True, include_mapping_target=True, acceptance=acceptance)
                graph = local_object.get_context_graph(with_mappings=True, include_mapping_target=True)
                if mode in ['api', 'api-flat']:
                    bindings = GraphBindings(about_uri=resolved_uri, graph=graph)
                    index_doc = bindings.to_index_doc() if mode == 'api' else bindings.to_flat_index_doc()
                    content = json.dumps(index_doc)
                    rdf_format = 'json-ld'
                elif mode in ['es-action']:
                    es_action = local_object.create_es_action(doc_type='test', record_type='test')
                    content = json.dumps(es_action)
                    rdf_format = 'json-ld'
                elif mode in ['posthook']:
                    for hook in settings.INDEX_POST_HOOKS:
                        content = hook(graph=graph)
                        rdf_format = 'json-ld'
                else:
                    content = graph.serialize(format=rdf_format, context=settings.JSON_LD_CONTEXT)
            else:
                graph = local_object.get_graph()
                content = graph.serialize(format=rdf_format, context=settings.JSON_LD_CONTEXT)
        elif self.store.ask(uri=resolved_uri):
            target_uri = resolved_uri
            content = self.get_content(target_uri, rdf_format, request)
        if not GraphBindings.is_lod_allowed(graph):
            raise UnknownGraph("URI {} access is not allowed in our graph store".format(resolved_uri))
        return HttpResponse(
            content,
            content_type='{}; charset=utf8'.format(result_extension_to_mime(rdf_format))
        )

    def get_content(self, target_uri, rdf_format, request):
        if '/resource/aggregation' in target_uri:
            target_named_graph = "{}/graph".format(target_uri.rstrip('/'))
            mode = self.get_mode(request, 'graph')
            describe = self.get_graph(mode=mode, named_graph=target_named_graph)
        else:
            mode = self.get_mode(request, "describe")
            describe = self.get_graph(mode=mode, uri=target_uri)
        if not describe or not GraphBindings.is_lod_allowed():
            logger.warn("Unable to find graph for: {}".format(target_uri))
            raise Http404()
        if mode in ['api', 'api-flat']:
            bindings = GraphBindings(about_uri=target_uri, graph=describe)
            index_doc = bindings.to_index_doc() if mode == 'api' else bindings.to_flat_index_doc()
            content = json.dumps(index_doc)
            rdf_format = 'json'
        else:
            content = describe.serialize(format=rdf_format)
        return content, rdf_format


class LoDHTMLView(TemplateView):
    template_name = "rdf/lod_detail.html"
    store = get_rdfstore()

    def get_content_type_template(self, about_type):
        return settings.RDF_CONTENT_DETAIL.get(about_type.lower(), None)

    def get_absolute_request_url(self):
        """Return the canonical RDF resource url for this page."""
        return self.request.build_absolute_uri().replace('/page/', '/resource/')

    def get_context_data(self, **kwargs):
        target_uri = self.get_absolute_request_url()
        if "?" in target_uri:
            target_uri = re.sub("\?.*$", '', target_uri)
        # target_uri = target_uri.split('?')[:-1]
        if not self.request.path.startswith("/page"):
            target_uri = re.sub('/[a-z]{2}/resource/', '/resource/', target_uri, count=1)
        if target_uri.endswith('graph'):
            target_uri = re.sub("/graph$", "", target_uri)
        context = super(LoDHTMLView, self).get_context_data(**kwargs)

        # default and test mode
        mode = self.request.GET.get('mode', 'default')
        acceptance = True if mode == 'acceptance' else False
        if not acceptance:
            acceptance = self.request.COOKIES.get('NAVE_ACCEPTANCE_MODE', False)

        object_local_cache = None

        cached = False

        context['about'] = target_uri
        context['ugc'] = None

        if "/resource/cache/" in target_uri:
            # lookup solution # rdfstore.get_rdfstore().get_cached_source_uri(target_uri)
            cached = True
            target_uri = target_uri.split('/resource/cache/')[-1]
            if target_uri.endswith("about.rdf"):
                target_uri = re.sub('about.rdf$', '', target_uri)
        else:
            target_uri = target_uri.rstrip('/')
            resolved_uri = RDFRecord.get_internal_rdf_base_uri(target_uri)
            if UserGeneratedContent.objects.filter(source_uri=resolved_uri).exists():
                context['ugc'] = UserGeneratedContent.objects.filter(source_uri=resolved_uri)
            if settings.RDF_USE_LOCAL_GRAPH:
                object_local_cache = ElasticSearchRDFRecord(source_uri=resolved_uri)
                object_local_cache.get_graph_by_source_uri(uri=resolved_uri)
                if not object_local_cache.exists():
                    context['source_uri'] = target_uri
                    context['unknown_graph'] = True
                    return context
                target_uri = resolved_uri
            elif self.store.ask(uri=resolved_uri):
                target_uri = resolved_uri

        context['source_uri'] = target_uri
        context['about_label'] = target_uri.split('/')[-1]
        context['about_spec'] = target_uri.split('/')[-2]

        is_white_listed = RDFRecord.is_spec_whitelist(
            context['about_spec'],
            self.request
        )
        if not is_white_listed:
            context['unknown_graph'] = True
            return context

        context['cached'] = cached

        # special query for skos
        def is_skos():
            return self.store.ask(
                query="where {{<{subject}> <{predicate}> <{object}>}}".format(
                    subject=target_uri, predicate=RDF.type, object=SKOS.Concept))

        if object_local_cache:
            graph = object_local_cache.get_context_graph(
                with_mappings=True,
                include_mapping_target=True,
                resolve_deepzoom_uri=True
            )
            nr_levels = 4
        elif cached:
            if CacheResource.objects.filter(document_uri=target_uri).exists():
                cache_object = CacheResource.objects.filter(document_uri=target_uri).first()
                graph = cache_object.get_graph()
                nr_levels = 3
            else:
                context['unknown_graph'] = True
                return context
        elif is_skos():
            graph, nr_levels = RDFModel.get_skos_context_graph(store=self.store, target_uri=target_uri)
            # nav_tree = RDFModel.get_nav_tree(target_uri=target_uri, store=self.store)
            # todo finish the nav tree implementation
            if 'skos_nav' in self.request.GET:
                return context
        elif '/resource/aggregation' in target_uri:
            target_named_graph = "{}/graph".format(target_uri.rstrip('/'))
            graph, nr_levels = RDFModel.get_context_graph(store=self.store, named_graph=target_named_graph)
        else:
            graph, nr_levels = RDFModel.get_context_graph(target_uri=target_uri, store=self.store)
        graph_contains_target = graph.query("""ASK {{ <{}> ?p ?o }} """.format(target_uri)).askAnswer

        if not graph_contains_target or len(graph) == 0:
            context['unknown_graph'] = True
            return context

        if context['about'].endswith('/'):
            context['about'] = context['about'].rstrip('/')

        context['graph'] = graph
        context['nr_levels'] = nr_levels
        context['namespaces'] = [(prefix, uri) for prefix, uri in graph.namespaces()]
        graph_bindings = GraphBindings(target_uri, graph, excluded_properties=settings.RDF_EXCLUDED_PROPERTIES)
        context['skos_links'], context['skos_filter'] = graph_bindings.get_all_skos_links()
        context['resources'] = graph_bindings
        resource = graph_bindings.get_about_resource()
        context['about_resource'] = resource
        context['items'] = resource.get_items(as_tuples=True)
        rdf_type = graph_bindings.get_about_resource().get_type()
        context['rdf_type'] = rdf_type
        context['lod_allowed'] = GraphBindings.is_lod_allowed(graph)
        context['content_template'] = self.get_content_type_template(rdf_type.search_label)
        context['graph_stats'] = RDFModel.get_graph_statistics(graph)
        context['alt'] = ""
        context['points'] = RDFModel.get_geo_points(graph)
        # DEEPZOOM VALUE(S)
        zooms = graph_bindings.get_list('nave_deepZoomUrl', False)
        if zooms:
            context['deepzoom_count'] = len(zooms)
            context['deepzoom_urls'] = [zoom.value.value for zoom in zooms]
        # EXPERT MODE
        expert_mode = self.request.COOKIES.get('NAVE_DETAIL_EXPERT_MODE', False)
        if expert_mode:
            # do expert mode stuff like more like this
            context['expert_mode'] = True
            if settings.MLT_DETAIL_ENABLE and object_local_cache:
                context['data'] = {'items': object_local_cache.get_more_like_this()}
        if settings.MLT_BANNERS and isinstance(settings.MLT_BANNERS, dict) and object_local_cache:
            from collections import OrderedDict
            context['data'] = {"mlt_banners": OrderedDict()}
            for name, config in settings.MLT_BANNERS.items():
                mlt_fields = config.get("fields", None)
                if mlt_fields and any(".raw" in field for field in mlt_fields):
                    # .raw fields don't work with MORE LIKE THIS queries so are
                    # queried directly.
                    context['data']['mlt_banners'][name] = object_local_cache.get_raw_related(
                        query_fields=mlt_fields,
                        filter_query=config.get("filter_query", None),
                        graph_bindings=graph_bindings
                    )
                else:
                    context['data']['mlt_banners'][name] = object_local_cache.get_more_like_this(
                            mlt_count=10,
                            mlt_fields=mlt_fields,
                            filter_query=config.get("filter_query", None)
                        )
        view_modes = {
            'properties': "rdf/_rdf_properties.html"
        }
        display_mode = self.request.GET.get('display')
        if display_mode:
            self.template_name = view_modes.get(display_mode, self.template_name)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if context.get('unknown_graph'):
            if context.get('cached'):
                if settings.RDF_DYNAMIC_CACHE:
                    retrieve_and_cache_remote_lod_resource.delay(context['source_uri'])
                return redirect(
                    context['source_uri']
                )
            else:
                logger.warn("unable to find graph for: {}".format(context['source_uri']))
                raise Http404()
        if context.get('skos_navtree') and 'skos_nav' in request.GET:
            return HttpResponse(context.get('skos_navtree'),
                                content_type='application/json; charset=utf8')
        return self.render_to_response(context)


def proxy(request, test_mode):
    """
    Proxy to use cross domain Ajax GET and POST requests
    request: Django request object
    """
    if request.method == 'GET':
        request = request.GET
        r = requests.get
    elif request.method == 'POST':
        request = request.POST
        r = requests.post
    else:
        return HttpResponseNotAllowed("Permitted methods are POST and GET")
    params = request.dict()
    try:
        url = rdfstore.get_sparql_query_url(test_mode)
    except KeyError:
        return HttpResponseBadRequest("URL must be defined")
    response = r(url, params=params)
    return HttpResponse(response.text, status=int(response.status_code), content_type=response.headers['content-type'])


def remote_sparql(request):
    """
    Route SPARQL queries to the endpoint configured in the settings
    """
    mime_type = get_lod_mime_type(None, request)
    if mime_type == HTML_MIME and 'query' not in request.GET:
        return redirect('snorql_main')
    logger.info("Production Mode SPARQL query: {}".format(request.META.get('QUERY_STRING')))
    return proxy(request, test_mode=False)


def remote_sparql_test(request):
    """
    Route SPARQL queries to the endpoint configured in the settings
    """
    mime_type = get_lod_mime_type(None, request)
    if mime_type == HTML_MIME and 'query' not in request.GET:
        return redirect('snorql_main')
    logger.info("Test Mode SPARQL query: {}".format(request.META.get('QUERY_STRING')))
    return proxy(request, test_mode=True)


class PropertyTemplateView(TemplateView):
    """
    A template view to load the SPARQL HTML interface.
    """
    template_name = "snorql/properties.html"

    def get_context_data(self, **kwargs):
        context = super(PropertyTemplateView, self).get_context_data(**kwargs)
        # TODO add queries to NS table later
        context['about_label'] = self.kwargs['label']
        context['about'] = self.request.build_absolute_uri()
        return context


class SnorqlTemplateView(TemplateView):
    """
    A template view to load the SPARQL HTML exploration interface.
    """
    template_name = "snorql/main.html"

    def get_context_data(self, **kwargs):
        context = super(SnorqlTemplateView, self).get_context_data(**kwargs)
        context['sparql_queries'] = SPARQLQuery.objects.all()
        context['sparql_prefixes'] = [prefix.as_sparql_prefix() for prefix in RDFPrefix.objects.all()]
        return context


class EDMHTMLMockView(TemplateView):
    template_name = "rdf/lod_detail.html"

    def get_context_data(self, **kwargs):
        target_uri = "http://localhost:8000/resource/aggregation/ton-smits-huis/454"
        target_named_graph = "{}/graph".format(target_uri.rstrip('/'))
        context = super(EDMHTMLMockView, self).get_context_data(**kwargs)
        context['about'] = target_uri
        context['about_label'] = target_uri.split('/')[-1]
        # test for modes normal, test, acceptance
        mode = self.request.GET.get('mode', 'default')
        if mode == 'test':
            print('test')
        elif mode == "acceptance":
            store = rdfstore.get_rdfstore(acceptance_mode=True)
        else:
            store = rdfstore.get_rdfstore()

        sparql_json = sparqlwrapper_result.sparql_result
        graph, nr_levels = RDFModel.get_graph_from_sparql_results(sparql_json)
        graph_contains_target = graph.query("""ASK {{ <{}> ?p ?o }} """.format(target_uri)).askAnswer

        if not graph and not graph_contains_target:
            raise Http404
        #
        context['graph'] = graph
        context['nr_levels'] = nr_levels
        context['namespaces'] = [(prefix, uri) for prefix, uri in graph.namespaces()]
        graph_bindings = GraphBindings(target_uri, graph, excluded_properties=settings.RDF_EXCLUDED_PROPERTIES)
        context['resources'] = graph_bindings
        resource = graph_bindings.get_about_resource()
        context['items'] = resource.get_items(as_tuples=True)
        context['rdf_type'] = graph_bindings.get_about_resource().get_type()
        context['graph_stats'] = RDFModel.get_graph_statistics(graph)
        context['alt'] = ""
        context['content_template'] = "rdf/content_detail/ore_aggregation.html"
        context['points'] = [[52.36, 4.9], [52.997, 6.562]]
        context['web_resources'] = [
            {
                "thumbnail": "http://media.delving.org/thumbnail/brabantcloud/ton-smits-huis/454/500",
                "deepzoom": "http://media.delving.org/iip/deepzoom/mnt/tib/tiles/brabantcloud/ton-smits-huis/454.tif.dzi",
                "mime_type": "image/jpeg",
                "source_uri": "http://media.delving.org/thumbnail/brabantcloud/ton-smits-huis/454/500",
                "metadata": {
                    "dc_title": "Zonder titel",
                    "dc_creator": "Ton Smits",
                    "dc_rights": "© L. Smits-Zoetmulder, info@tonsmitshuis.nl"
                }
            },
            {
                "thumbnail": "",
                "deepzoom": "",
                "mime_type": "audio/wav",
                "source_uri": "media/189467__speedenza__poem-darkness-voice.wav",
                "metadata": {
                    "dc_title": "Poem: Darkness (Voice)",
                    "dc_creator": "Speedenza (freesound.org)",
                    "dc_rights": "freesound.org"
                }
            },
            {
                "thumbnail": "",
                "deepzoom": "",
                "mime_type": "video/mp4",
                "source_uri": "media/NuclearExplosionwww.keepvid.com.mp4",
                "metadata": {
                    "dc_title": "Nuclear explosion",
                    "dc_creator": "Oppenheimer",
                    "dc_rights": "Destructive Commons"
                }
            }
        ]
        # Todo  add search results
        # * build query on uri or property
        # * add facets from configuration + property facet
        # * get NaveResponse
        # * add to context as data
        return context


class UserGeneratedContentList(ListCreateAPIView):
    queryset = UserGeneratedContent.objects.all()
    serializer_class = UserGeneratedContentSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)


class UserGeneratedContentDetail(RetrieveUpdateDestroyAPIView):
    queryset = UserGeneratedContent.objects.all()
    serializer_class = UserGeneratedContentSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(user=self.request._user)

    def perform_update(self, serializer):
        serializer.save(user=self.request._user)
