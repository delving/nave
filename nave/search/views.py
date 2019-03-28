""" file: search/views.py

The Django views used by the search module.


"""
import inspect
import logging
import sys
from collections import OrderedDict, defaultdict

import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse, HttpResponseNotFound
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _, activate
from django.views.generic import ListView, DetailView, RedirectView, View, TemplateView
from rest_framework.decorators import list_route
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import ViewSetMixin
from rest_framework_jsonp.renderers import JSONPRenderer

from nave.base_settings import FacetConfig
from nave.lod import EXTENSION_TO_MIME_TYPE
from nave.lod.models import RDFModel, CacheResource
from nave.lod.utils import rdfstore
from nave.lod.utils.resolver import GraphBindings, RDFRecord
from nave.lod.utils.rdfstore import UnknownGraph
from nave.lod.utils.resolver import ElasticSearchRDFRecord
from nave.search.tasks import download_all_search_results
from nave.void.models import EDMRecord


from nave.void import REGISTERED_CONVERTERS
from .renderers import N3Renderer, JSONLDRenderer, TURTLERenderer, NTRIPLESRenderer, RDFRenderer, GeoJsonRenderer, \
    XMLRenderer, KMLRenderer, GeoBufRenderer
from .search import NaveESQuery, NaveQueryResponse, NaveQueryResponseWrapper, NaveItemResponse, \
    NaveESItem
from .serializers import NaveQueryResponseWrapperSerializer, NaveESItemSerializer
from .utils import gis


logger = logging.getLogger(__file__)


def proxy(request, url):
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
    if not url:
        return HttpResponseBadRequest("URL must be defined")
    response = r(url, params=params)

    return HttpResponse(response.text, status=int(response.status_code), mimetype=response.headers['content-type'])


def drf_proxy(request, url):
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
    if not url:
        return HttpResponseBadRequest("URL must be defined")

    response = r(url, params=params)

    return response.json()


class LegacyAPIRedirectView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        params = self.request.GET
        return "/api/search/v1?{}".format(params.urlencode())


class ClusterGeoJsonView(ListView):
    def get(self, request, *args, **kwargs):
        query_factory = NaveESQuery(index_name=settings.SITE_NAME)
        query = query_factory.build_geo_query(request)
        results = query.execute()
        geo_json = gis.get_geojson(gis.get_feature_collection(results.aggregations))
        return HttpResponse(geo_json, content_type="application/json")


class BigDownloadView(View):

    def get(self, *args, **kwargs):
        task_id = kwargs.get('id')
        # todo find the task by task id
        task_result = download_all_search_results.AsyncResult(task_id)
        if not task_id:
            return JsonResponse({'status': 'error', 'msg': 'You must supply a task id.'})
        resp = {
            'status': task_result.state,
            'task_id': task_id,
            'msg': """Generating a zip file for the api request.
                        When the zip file is done a download link will appear on this page."""}
        if task_result.state in ['SUCCESS']:
            link, query, results, resp_format = task_result.result
            resp['download_link'] = link
            resp['es_query'] = query
            resp['nr_results'] = results
            resp['format'] = resp_format
        return JsonResponse(resp)


class SearchListAPIView(ViewSetMixin, ListAPIView, RetrieveAPIView):
    """
    An APIView for returning ES search results.

    This class can be used directly or sub-classed to create custom views on the data.

    Formats only for list view: geojson

    Formats only for detail view: n3, turtle, rdf, json-ld, nt

    The API query documentation can be found here: http://culture-hub-api-documentation.readthedocs.org/en/latest/
    """
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = NaveQueryResponseWrapperSerializer
    renderer_classes = (BrowsableAPIRenderer, TemplateHTMLRenderer, JSONRenderer, JSONPRenderer, XMLRenderer,
                        GeoJsonRenderer, KMLRenderer, GeoBufRenderer,
                        # rdf renders
                        N3Renderer, JSONLDRenderer, RDFRenderer, NTRIPLESRenderer, TURTLERenderer)
    registered_converters = REGISTERED_CONVERTERS
    index_name = settings.SITE_NAME
    doc_types = []
    template_name = "search/search-results.html"
    facets = settings.FACET_CONFIG
    filters = []
    hidden_filters = []
    demote = getattr(settings, 'DEMOTE', None)
    mapping_type = None
    paginate_by = None
    default_converter = None
    mlt_fields = settings.MLT_FIELDS
    lookup_value_regex = '[^/]+'
    facet_size = 50
    lookup_query_object = None

    def set_hidden_query_filters(self, filter_list):
        self.hidden_filters = [hqf.strip('"') for hqf in filter_list]

    def set_facets(self, facet_config_list):
        self.facets = facet_config_list

    def get_converter(self, converter_key=None):
        request_converter_key = self.request.GET.get("converter")
        if request_converter_key:
            converter_key = request_converter_key
        elif not converter_key and self.default_converter:
            converter_key = self.default_converter
        converter = self.registered_converters.get(converter_key, None)
        return converter

    @property
    def get_facet_config(self):
        return self.facets

    @staticmethod
    def _clean_callback(request):
        # clean callback url
        if len(request.query_params.getlist('callback', [])) > 1:
            callbacks = request.query_params.getlist('callback')
            for callback in callbacks:
                if "?" in callback:
                    callbacks.remove(callback)
        return request

    @staticmethod
    def get_record_from_doctype(doc_type, doc_id):
        module, cls_name = doc_type.split('_')
        module = '{}.models'.format(module)
        clsmembers = inspect.getmembers(sys.modules[module], inspect.isclass)
        clsmember_dict = {key.lower(): cls for key, cls in clsmembers}
        model = clsmember_dict.get(cls_name)
        if not model:
            raise ValueError("Unable to find model for doctype: {}".format(module))
        record = model.objects.get(hub_id=doc_id)
        return record

    def get_query(self, request, index_name, doc_types, facet_config_list, filters, demote, hidden_filters=None,
                  cluster_geo=False, geo_query=False, converter=None, acceptance=False, *args, **kwargs):

        if hidden_filters is None and self.hidden_filters:
            hidden_filters = self.hidden_filters
        else:
            hidden_filters = []

        if hasattr(settings, 'ES_ROWS'):
            s_rows = settings.ES_ROWS
        else:
            s_rows = 12
        # clean callback url
        self._clean_callback(request)
        try:
            rows = int(request.query_params.get('rows', s_rows))
        except ValueError as ve:
            rows = s_rows
        query = NaveESQuery(
            index_name=index_name,
            doc_types=doc_types,
            default_facets=facet_config_list,
            default_filters=filters,
            hidden_filters=hidden_filters,
            cluster_geo=cluster_geo,
            geo_query=geo_query,
            size=rows,
            converter=converter,
            facet_size=self.facet_size,
            acceptance=acceptance
        )
        if self.lookup_query_object:
            query.build_query_from_request(request=request, raw_query_string=self.lookup_query_object.query)
        else:
            query.build_query_from_request(request)
        # if demote:
            # for d in demote:
                # promote_query, demote_query, boost = d
                # query.query = query.query.query(
                    # {'boosting': {
                        # 'positive': promote_query,
                        # 'negative': demote_query,
                        # 'negative_boost': boost
                    # }}
                # )
        # TODO remove demote code
        # if demote and 'q' in request.query_params:
            # for demote in demote:
                # demote_query, amount, _ = demote
                # query.query = query.query.demote(amount, demote_query)
        # elif demote:
            # sort_fields = [demote[2] for demote in demote]
            # sort_fields.extend(['_score'])
            # query.query = query.query.order_by(*sort_fields)
        return query

    def get_queryset(self, cluster_geo=False, geo_query=False, acceptance=False, *args, **kwargs):
        query = self.get_query(
            request=self.request,
            index_name=self.get_index_name,
            doc_types=self.doc_types,
            facet_config_list=self.facets,
            filters=self.filters,
            demote=self.demote,
            cluster_geo=cluster_geo,
            geo_query=geo_query,
            converter=self.get_converter(),
            acceptance=acceptance
        )

        response = NaveQueryResponse(query=query, api_view=self, converter=self.get_converter())
        wrapped_response = NaveQueryResponseWrapper(response)
        return wrapped_response

    @property
    def acceptance_mode(self):
        mode = self.request.GET.get('mode', 'default')
        acceptance = True if mode == 'acceptance' else False
        if not acceptance:
            acceptance = self.request.COOKIES.get('NAVE_ACCEPTANCE_MODE', False)
        return acceptance

    def stream_search_results(self, request):
        import uuid
        from elasticsearch.helpers import scan
        from .connector import get_es_client
        from django.http.response import Http404

        # check if authenticated
        if not request.user.is_authenticated():
            logger.warn("Only logged in users can create a download request.")
            raise Http404()
        user = request.user
        response_format = self.request.GET.get('format', 'json')
        file_name = "{}_{}.{}".format(user.username, uuid.uuid1(), response_format)
        query = self.get_query(
            request=self.request,
            index_name=self.get_index_name,
            doc_types=self.doc_types,
            facet_config_list=self.facets,
            filters=self.filters,
            hidden_filters=self.hidden_filters,
            demote=self.demote,
            cluster_geo=False,
            converter=self.get_converter()
        )
        downloader = scan(
            client=get_es_client(),
            query=query.query,
            index=self.get_index_name,
        )

        # todo add serializer for response format
        def streaming_generator():
            yield "["
            first = True
            for result in downloader:
                if first:
                    first = False
                else:
                    yield ","
                yield self.serialize_stream(es_item=result, format="json")
            yield "]"

        generator = streaming_generator()
        ##
        # async_task_id = download_all_search_results.delay(
        #     query_dict=query.query,
        #     response_format=self.request.GET.get('format', 'json'),
        #     converter=self.get_converter(),
        #     index_name=self.get_index_name,
        #     doc_types=self.doc_types
        # )
        from django.http import StreamingHttpResponse
        response = StreamingHttpResponse(
            generator,
            content_type="text/plain"  # todo later replace with response_format
        )
        # todo add streaming gzip of search results later
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)
        return response

    def stream_geosearch_results(self, request, max=1000, as_file=True):
        """Return a streaming response with all geopoints"""
        from django.http import StreamingHttpResponse

        if hasattr(settings, 'GEO_STREAMING_RESPONSE'):
            max = settings.GEO_STREAMING_RESPONSE
        query_factory = NaveESQuery(index_name=settings.SITE_NAME)
        generator = query_factory.get_geojson_generator(request=request, max=max)
        response = StreamingHttpResponse(
            generator,
            content_type="application/json"
        )
        file_name = 'edmPoints.js'
        # todo add streaming gzip of search results later
        if as_file:
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)
        return response

    def serialize_stream(self, es_item, format="json"):
        from elasticsearch_dsl.result import Result
        item = NaveESItem(es_item=Result(es_item), converter=self.get_converter())
        serialized_item = NaveESItemSerializer(item)
        return JSONRenderer().render(serialized_item.data)

    def list(self, request, format=None, *args, **kwargs):
        # if has id redirect to detail view
        if 'id' in request.query_params:
            params = request.query_params.copy()
            id = params.pop('id')[0].rstrip('/')
            if '/' in id:
                # get hub_id and redirect
                from elasticsearch_dsl import Search
                from .connector import get_es_client
                res = Search(index=settings.SITE_NAME).using(get_es_client()).query("match", **{'dc_identifier.value': id}).execute()
                if res.hits:
                    id = res.hits[0].meta.id
                else:
                    return 404
            path = request._request.path.rstrip('/')
            return redirect("{}/{}?{}".format(path, id, params.urlencode()))
        if 'qr' in request.query_params:
            params = request.query_params.copy()
            query = params.pop('q')
            query.extend(params.pop('qr'))
            params['q'] = " ".join(query)
            return redirect("{}?{}".format(request._request.path, params.urlencode()))
        result_as_zip = True if request.query_params.get('download', 'false').lower() == "true" else False
        result_as_geo_stream = True if request.query_params.get('geostream', 'false').lower() == "true" else False
        stream_to_file = True if request.query_params.get('filestream', 'false').lower() == "true" else False
        if result_as_zip:
            return self.stream_search_results(request=request)
        elif result_as_geo_stream:
            return self.stream_geosearch_results(request=request, as_file=stream_to_file)
        elif request.accepted_renderer.format == 'geojson-clustered':
            # todo replace with normal geojson output as feature collection
            return Response(self.get_clustered_geojson(request))
        geo_query = request.accepted_renderer.format in ['geojson', 'kml']
        queryset = self.get_queryset(geo_query=geo_query)
        # HTML VIEW ##############################################################
        mode = self.request.GET.get('mode', 'default')
        if request.accepted_renderer.format == 'html':
            # set results view and add to context.
            # 1: check url param, 1: check cookie, 3: use grid as default
            view = request.GET.get('view', request.COOKIES.get('view', 'grid'))
            rows = request.GET.get('rows', settings.ES_ROWS)
            serializer_context = {
                'slug': kwargs.get('slug', None),
                'data': queryset.data,
                'rows': str(rows),
                'view': view,
                'acceptance': mode
            }
            return Response(serializer_context, template_name=self.template_name)

        serializer = NaveQueryResponseWrapperSerializer(queryset)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, format=None, *args, **kwargs):
        def get_mode(default=None):
            params = request.GET
            return params.get('schema', default)

        self._clean_callback(request)

        query = NaveESQuery(
            index_name=self.get_index_name,
            doc_types=self.doc_types,
            default_facets=self.facets,
            cluster_geo=False,
            size=1,
            converter=self.get_converter()
        )
        try:
            query = query.build_item_query(query, request.query_params, pk)
        except ValueError as ve:
            logger.error("Unable to build request because: {}".format(ve))
            # todo display error message when bad/unknown hubId is given
            return HttpResponseBadRequest()
        mlt = True if request.query_params.get('mlt', 'false') == "true" else False
        mlt_count = int(request.query_params.get('mlt.count', 5))
        mlt_filter_queries = request.query_params.getlist('mlt.qf', [])
        if not mlt_filter_queries and 'mlt.filterkey' in request.query_params:
            mlt_filter_queries = request.query_params.getlist('mlt.filterkey', [])
        mlt_fq_dict = defaultdict(list)
        for fq in mlt_filter_queries:
            if ":" in fq:
                k, v = fq.split(":", maxsplit=1)
                if not k.endswith(".raw"):
                    k = "{}.raw".format(k)
                mlt_fq_dict[k].append(v)
        response = NaveItemResponse(
            query,
            self,
            index=self.get_index_name,
            mlt=mlt,
            mlt_count=mlt_count,
            mlt_filter_query=mlt_fq_dict,
        )
        if response._results.hits.total == 0:
            return HttpResponseNotFound()
        clean_pk = response._results[0].meta.id
        record = ElasticSearchRDFRecord(hub_id=clean_pk)
        record.get_graph_by_id(hub_id=clean_pk)
        response._rdf_record = record
        renderer_format = request.accepted_renderer.format
        if renderer_format in list(EXTENSION_TO_MIME_TYPE.keys()) and renderer_format not in ['xml', 'json']:
            graph = record.get_graph()
            graph_string = graph.serialize(format=renderer_format).decode('utf-8')
            mime_type = EXTENSION_TO_MIME_TYPE.get(renderer_format)
            return Response(data=graph_string, content_type=mime_type)
        target_uri = record.document_uri
        if settings.RDF_USE_LOCAL_GRAPH:
            graph = record.get_graph()
        else:
            store = rdfstore.get_rdfstore()
            graph, _ = RDFModel.get_context_graph(store, named_graph=record.named_graph)
        if not graph:
            return HttpResponseNotFound()
        mode = get_mode(self.default_converter)
        bindings = GraphBindings(about_uri=target_uri, graph=graph)
        delving_fields = False if request.GET.get("delving_fields") == 'false' else True
        converter = None
        if mode in ['api', 'api-flat']:
            index_doc = bindings.to_index_doc() if mode == 'api' else bindings.to_flat_index_doc()
        elif mode in REGISTERED_CONVERTERS.keys():
            converter = REGISTERED_CONVERTERS.get(mode)
            index_doc = converter(
                bindings=bindings,
                graph=graph,
                about_uri=bindings.about_uri()
            ).convert(add_delving_fields=delving_fields)
        elif self.default_converter in REGISTERED_CONVERTERS.keys():
            converter = REGISTERED_CONVERTERS.get(self.default_converter)
            index_doc = converter(
                bindings=bindings,
                graph=graph,
                about_uri=bindings.about_uri()
            ).convert(add_delving_fields=delving_fields)
        else:
            logger.warn("unable to convert results to schema {}".format(mode))
            index_doc = bindings.to_index_doc()
        layout_fields = OrderedDict()
        layout_fields['layout'] = converter().get_layout_fields() if converter else []
        if response.get_mlt():
            mlt = {"item": [NaveESItemSerializer(item).data for item in response.get_mlt()]}
        else:
            mlt = ""
        result = {'result': {
            'layout': layout_fields,
            'item': {'fields': index_doc},
            "relatedItems": mlt}}
        return Response(result)

    @list_route()
    def _search(self, request, format=None):
        proxy_request = drf_proxy(request, "{}/_search".format(self.get_es_url()))
        return Response(proxy_request)

    @list_route()
    def _mapping(self, request, format=None):
        proxy_request = drf_proxy(request, "{}/_mapping".format(self.get_es_url()))
        return Response(proxy_request)

    @list_route()
    def _geojson(self, request, format=None):
        geo_json = self.get_clustered_geojson(request)
        return Response(geo_json)

    @list_route()
    def _docs(self, request, format=None):
        return HttpResponse(content="See http://culture-hub-api-documentation.readthedocs.io/en/latest/api_intro.html")

    def get_clustered_geojson(self, request, acceptance=False):
        query_factory = NaveESQuery(index_name=self.get_index_name)
        query = query_factory.build_geo_query(request)
        results = query.execute()
        geo_json = gis.get_geojson(gis.get_feature_collection(results.aggregations), as_string=False)
        return geo_json

    @property
    def get_index_name(self):
        return self.index_name if not self.acceptance_mode else "{}_acceptance".format(self.index_name)

    def get_es_url(self):
        return "http://{}/{}/".format(settings.ES_URLS[0],
                                      self.get_index_name)


class V1SearchListApiView(SearchListAPIView):
    default_converter = settings.DEFAULT_V1_CONVERTER
    doc_types = []


class V2SearchListApiView(SearchListAPIView):
    default_converter = settings.DEFAULT_V2_CONVERTER


class SearchListHTMLView(SearchListAPIView):
    renderer_classes = (TemplateHTMLRenderer, JSONRenderer, JSONPRenderer, XMLRenderer,
                        GeoJsonRenderer)


class LodRelatedSearchHTMLView(SearchListAPIView):
    renderer_classes = (TemplateHTMLRenderer, JSONRenderer, JSONPRenderer, XMLRenderer,
                        GeoJsonRenderer)
    template_name = "search/_search-results-linked.html"
    facets = [
        FacetConfig('system.spec.raw', _("Collection")),
        FacetConfig('system.about_type', _("RDF primary type")),
        FacetConfig('rdf.class.value', _("RDF secondary type")),
        FacetConfig('rdf.predicate.value', _("RDF predicates")),
        FacetConfig('legacy.delving_recordType', _("dc_type")),
    ]
    filters = []


class NaveDocumentTemplateView(TemplateView):
    template_name = 'rdf/content_foldout/lod-detail-foldout.html'
    context_object_name = 'detail'

    def get(self, request, *args, **kwargs):
        absolute_uri = request.build_absolute_uri()
        if absolute_uri.endswith("/"):
            redirect(absolute_uri.rstrip('/'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(NaveDocumentTemplateView, self).get_context_data(**kwargs)
        absolute_uri = self.request.build_absolute_uri()
        target_uri = RDFRecord.get_internal_rdf_base_uri(absolute_uri)

        if "detail/foldout/" in target_uri:
            slug = self.kwargs.get('slug')
            record = ElasticSearchRDFRecord(hub_id=slug)
            graph = record.get_graph_by_id(self.kwargs.get('slug'))
            if graph is not None:
                target_uri = record.source_uri
            else:
                logger.warn("Unable to find source_uri for slug: {}".format(slug))
        else:
            target_uri = RDFRecord.get_internal_rdf_base_uri(absolute_uri)
            record = ElasticSearchRDFRecord(hub_id=self.kwargs.get('slug'))
            graph = record.get_graph_by_source_uri(target_uri)
        if graph is None:
            raise UnknownGraph("URI {} is not known in our graph store".format(target_uri))
        if "/resource/cache/" in target_uri:
            target_uri = target_uri.rstrip('/')
            cache_resource = CacheResource.objects.filter(document_uri=target_uri)
            if cache_resource.exists():
                graph = cache_resource.first().get_graph()
        elif settings.RDF_USE_LOCAL_GRAPH:
            mode = self.request.GET.get('mode', 'default')
            acceptance = True if mode == 'acceptance' else False
            context['acceptance'] = acceptance

        elif '/resource/aggregation' in target_uri:
            target_named_graph = "{}/graph".format(target_uri.rstrip('/'))
            graph, nr_levels = RDFModel.get_context_graph(store=rdfstore.get_rdfstore(), named_graph=target_named_graph)
        else:
            graph, nr_levels = RDFModel.get_context_graph(
                store=rdfstore.get_rdfstore(),
                target_uri=target_uri
            )
        # todo: remove: should no longer be necessary with the addition of common.middleware.ForceLangMiddleware
        language = self.request.GET.get('lang', None)
        if language:
            activate(language)
        bindings = GraphBindings(
            about_uri=target_uri,
            graph=graph,
            excluded_properties=settings.RDF_EXCLUDED_PROPERTIES
        )
        context['resources'] = bindings
        context['absolute_uri'] = RDFRecord.get_external_rdf_url(target_uri, self.request)
        context['query'] = self.request.GET.get('q')
        if record:
            context['about_spec'] = record.get_spec_name()
        else:
            context['about_spec'] = target_uri.split("/")[-2]

        for rdf_type in bindings.get_about_resource().get_types():
            search_label = rdf_type.search_label.lower()
            content_template = settings.RDF_CONTENT_FOLDOUTS.get(search_label)
            if content_template:
                self.template_name = content_template
                break

        context['points'] = RDFModel.get_geo_points(graph)

        return context


class NaveDocumentDetailView(DetailView):
    """
    .. deprecated::
        Use NaveDocumentTemplateView instead.
    """
    template_name = 'rdf/content_foldout/lod-detail-foldout.html'
    context_object_name = 'detail'
    model = EDMRecord

    def get(self, request, *args, **kwargs):
        absolute_uri = request.build_absolute_uri()
        if absolute_uri.endswith("/"):
            redirect(absolute_uri.rstrip('/'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(NaveDocumentDetailView, self).get_context_data(**kwargs)
        target_uri = self.object.document_uri
        if "/resource/cache/" in target_uri:
            target_uri = target_uri.rstrip('/')
            cache_resource = CacheResource.objects.filter(document_uri=target_uri)
            if cache_resource.exists():
                graph = cache_resource.first().get_graph()
        elif settings.RDF_USE_LOCAL_GRAPH:
            mode = self.request.GET.get('mode', 'default')
            acceptance = True if mode == 'acceptance' else False
            context['acceptance'] = acceptance
            if isinstance(self.object, EDMRecord):
                graph = self.object.get_graph(with_mappings=True, include_mapping_target=True, acceptance=acceptance)
            else:
                graph = self.object.get_graph(acceptance=acceptance)
        elif '/resource/aggregation' in target_uri:
            target_named_graph = "{}/graph".format(target_uri.rstrip('/'))
            graph, nr_levels = RDFModel.get_context_graph(store=rdfstore.get_rdfstore(), named_graph=target_named_graph)
        else:
            graph, nr_levels = RDFModel.get_context_graph(
                store=rdfstore.get_rdfstore(),
                target_uri=target_uri
            )
        # todo: remove: should no longer be necessary with the addition of common.middleware.ForceLangMiddleware
        language = self.request.GET.get('lang', None)
        if language:
            activate(language)
        bindings = GraphBindings(
            about_uri=target_uri,
            graph=graph,
            excluded_properties=settings.RDF_EXCLUDED_PROPERTIES
        )
        context['resources'] = bindings
        for rdf_type in bindings.get_about_resource().get_types():
            search_label = rdf_type.search_label.lower()
            content_template = settings.RDF_CONTENT_FOLDOUTS.get(search_label)
            if content_template:
                self.template_name = content_template
                break

        context['points'] = RDFModel.get_geo_points(graph)

        return context

    def get_queryset(self):
        doc_type = self.kwargs['doc_type']
        app_label, model_name = doc_type.split('_')
        from django.apps import apps
        model = apps.get_model(app_label=app_label, model_name=model_name)
        return model.objects.get_queryset()


class DetailResultView(NaveDocumentTemplateView):
    template_name = 'rdf/content_foldout/lod-detail-foldout.html'
    context_object_name = 'detail'


class FoldOutDetailImageView(NaveDocumentTemplateView):
    template_name = 'search-detail-image-foldout.html'
    context_object_name = 'detail'


class KNReiseGeoView(TemplateView):
    """The KNReise clustered geoviewer."""
    template_name = 'geoviewer/geoviewer.html'
