import logging
from urllib.parse import unquote

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import ListView, RedirectView, TemplateView
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes, \
     renderer_classes
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response

from nave.search.renderers import XMLRenderer
from nave.void import tasks
from nave.void.models import ProxyResourceField, ProxyMapping
from nave.void.parsers import PlainTextParser, XMLTreeParser
from nave.void.processors import BulkApiProcessor, IndexApiProcessor


logger = logging.getLogger(__name__)


@api_view(['PUT', 'POST'])
@authentication_classes(
    (SessionAuthentication, BasicAuthentication, TokenAuthentication)
)
@parser_classes((PlainTextParser,))
@permission_classes((IsAuthenticated,))
def bulk_api(request):
    if request.method in ['PUT', 'POST']:
        content = request.data
        if not settings.BULK_API_ASYNC:
            processor = BulkApiProcessor(content)
            return Response(
                processor.process(),
                status=status.HTTP_201_CREATED
            )
        tasks.process_bulk_api_request.delay(content)
        return Response({'status': "ok"}, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'POST', 'GET'])
@parser_classes((XMLTreeParser,))
@renderer_classes((XMLRenderer,))
@permission_classes((AllowAny,))
def index_api(request):
    """Entrypoint for the hub2 index-api."""
    if request.method in ['PUT', 'POST']:
        content = request.data
        # logger.debug(content)
        processor = IndexApiProcessor(payload=content)
        response_list = processor.process()
        return Response({'indexResponse': response_list})
    else:
        return HttpResponseRedirect(reverse("index_api_docs"))


def index_api_docs(request):
    from django.http.response import HttpResponse
    content = """The Index API makes it possible to send custom items to be indexed.

        It expects to receive an XML document containing one or more items to be indexed.
        Each item must have an itemId attribute which serves as identifier for the item to be indexed,
        as well as an itemType attribute which indicates the type of the item, to be used to filter it later on.

        An item contains one or more field elements that describe the data to be indexed. A field must provide a name attribute,
        and can optionally specify:
        - a fieldType attribute which is used by the indexing mechanism (default value: "text")
        - a facet attribute which means that the field is to be made available as a facet (default value: false)

        The possible values for fieldType are: string, location, int, single, text, date, link

        For example:

        <indexRequest>
            <indexItem itemId="123" itemType="book">
                <field name="title" fieldType="string">The Hitchhiker's Guide to the Galaxy</field>
                <field name="author" fieldType="string" facet="true">Douglas Adams</field>
            </indexItem>
        </indexRequest>


        It is possible to remove existing items by specifying the delete flag:

        <indexRequest>
            <indexItem itemId="123" itemType="book" delete="true" />
        </indexRequest>


        Additionally, there is a number of optional system fields that can be specified, and that help to trigger additional functionality:

        <indexRequest>
            <indexItem itemId="123" itemType="book">
                <systemField name="thumbnail">http://path/to/thumbnail</field>
            </indexItem>
        </indexRequest>

        The possible systemField names are: collection, collectionPart, thumbnail, thumbnailLarg, thumbnailSmall, landingPage, provider, owner, title, description, fullText
        """
    return HttpResponse(content_type='text/plain', content=content)

@api_view(['PUT', 'POST', 'DELETE'])
@authentication_classes((SessionAuthentication, BasicAuthentication, TokenAuthentication))
@parser_classes((JSONParser,))
@permission_classes((IsAuthenticated,))
def toggle_proxy_field(request):
    if request.method in ['PUT', 'POST', 'DELETE']:
        try:
            content = request.data.copy()
            delete_string = content.pop("delete", 'false')
            if not isinstance(delete_string, bool):
                delete = True if delete_string.lower() in ['true'] else False
            else:
                delete = delete_string
            if not all([key in ['dataset_uri', 'property_uri'] for key in content.keys()]):
                raise ValueError("dataset_uri or property_uri must be present in the request")
            field, created = ProxyResourceField.objects.get_or_create(**content)
            if delete or request.method == "DELETE":
                field.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            elif created:
                return Response({'status': "ok"}, status=status.HTTP_201_CREATED)
            else:
                return Response({'status': "ok"}, status=status.HTTP_304_NOT_MODIFIED)
        except Exception as e:
            logger.error(e)
            return Response({'status': "not ok", 'error': e.args}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'POST', 'DELETE'])
@authentication_classes((SessionAuthentication, BasicAuthentication, TokenAuthentication))
@parser_classes((JSONParser,))
@permission_classes((IsAuthenticated,))
def toggle_proxy_mapping(request):
    if request.method in ['PUT', 'POST', 'DELETE']:
        try:
            content = request.data.copy()
            delete_string = content.pop("delete", 'false')
            if not isinstance(delete_string, bool):
                delete = True if delete_string.lower() in ['true'] else False
            else:
                delete = delete_string
            if not all([key in ['user_uri', 'skos_concept_uri', 'proxy_resource_uri'] for key in content.keys()]):
                raise ValueError("user_uri and proxy_resource_uri and skos_concept_uri must be present in the request")
            mapping, created = ProxyMapping.objects.get_or_create(**content)
            if delete or request.method == "DELETE":
                mapping.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            elif created:
                return Response({'status': "ok"}, status=status.HTTP_201_CREATED)
            else:
                return Response({'status': "ok"}, status=status.HTTP_304_NOT_MODIFIED)

        except Exception as e:
            logger.error(e)
            return Response({'status': "not ok", 'error': e.args}, status=status.HTTP_400_BAD_REQUEST)


class DataSetStatistics:

    def __init__(self, sparql_endpoint):
        self._endpoint = sparql_endpoint

    total_records = 0

    from collections import namedtuple
    NarthexDataSet = namedtuple('NarthexDataSet', ['spec', 'record_count', 'invalid', 'valid', 'es_count', 'deleted'])

    def get_narthex_datasets(self):
        from SPARQLWrapper import SPARQLWrapper, JSON

        sparql = SPARQLWrapper(self._endpoint)
        # sparql.setCredentials('fuseki_user', 'XXX')
        sparql.setQuery("""
           SELECT * WHERE {
          graph ?g {
            ?s <http://schemas.delving.eu/narthex/terms/datasetSpec> ?spec ;
               <http://schemas.delving.eu/narthex/terms/datasetRecordCount> ?recordCount ;
               <http://schemas.delving.eu/narthex/terms/processedValid> ?processedValid;
               <http://schemas.delving.eu/narthex/terms/processedInvalid> ?processedInvalid.
                OPTIONAL { ?s <http://schemas.delving.eu/narthex/terms/deleted> ?deleted . }

                  }
                }

        LIMIT 500
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return results

    def get_indexed_datasets(self):
        from elasticsearch_dsl import Search, A
        from nave.search.connector import get_es_client
        client = get_es_client()
        s = Search(using=client).index(settings.ORG_ID)
        a = A('terms', field='delving_spec.raw', size=500)
        s.aggs.bucket('delving_spec', a)
        response = s.execute()
        self.total_records = response.hits.total
        return response.aggregations.delving_spec.buckets

    def get_spec_list(self, include_deleted=True):
        spec_list = {}
        results = self.get_narthex_datasets()
        for spec in results['results']['bindings']:
            spec_value = spec.get('spec')['value']
            dataset = self.NarthexDataSet(
                spec=spec_value,
                record_count=spec.get('recordCount')['value'],
                invalid=spec.get('processedInvalid')['value'],
                valid=spec.get('processedValid')['value'],
                deleted=spec.get('deleted', {'value': "false"})['value'],
                es_count=0
            )
            spec_list[spec_value] = dataset
        for spec in self.get_indexed_datasets():
            spec_name = spec.key
            dataset = spec_list.get(spec_name)
            if dataset is None:
                logger.info("Spec {} missing in Narthex".format(spec.key))
            else:
                spec_list[spec_name] = dataset._replace(es_count=spec.doc_count)
        if not include_deleted:
            spec_list = {k: v for k, v in spec_list.items() if v.deleted == "false"}
        return spec_list


class DataSetStatisticsView(TemplateView):
    template_name = "statistics.html"

    def get_context_data(self, **kwargs):
        context = super(DataSetStatisticsView, self).get_context_data(**kwargs)
        endpoint = self.request.build_absolute_uri(reverse('proxy'))
        stats = DataSetStatistics(endpoint)
        spec_list = stats.get_spec_list()
        # remove deleted
        deleted_specs = []
        for k, v in spec_list.copy().items():
            if v.deleted == "true":
                deleted_specs.append(v)
                del spec_list[k]
        specs = list(spec_list.keys())
        correct_datasets = [ds for ds in spec_list.values() if ds.es_count == int(ds.valid)]
        not_indexed = [ds for ds in spec_list.values() if ds.es_count == 0 and int(ds.valid) > 0]
        wrong_index_count = [ds for ds in spec_list.values() if ds.es_count != int(ds.valid) and ds.es_count > 0]
        context['counts'] = {
            'total_records': {'count': stats.total_records, 'values': None},
            'total_specs': {'count': len(specs), 'values': specs},
            'correct_datasets': {'count': len(correct_datasets), 'values': correct_datasets},
            'not_indexed': {'count': len(not_indexed), 'values': not_indexed},
            'wrong_index_count': {'count': len(wrong_index_count), 'values': wrong_index_count},
            'deleted': {'count': len(deleted_specs), 'values': deleted_specs},
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class VoidListView(ListView):
    """
    This class generates a void.ttl discovery file

    See also: http://www.w3.org/TR/void/#void-file
    """
    pass


class ImageRedirectView(RedirectView):
    """
    The Redirect view redirects Digital Object Uris that have been encoded
    as RDF valid uris in the sip-creator.

    Providers like Adlib supply API calls to provide images that are often not valid URIs.
    """
    permanent = False
    query_string = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Do ContentNegotiation for some resource and
        redirect to the appropriate place
        """
        label = self.kwargs.get('link')
        redirect_url = unquote(label)
        return redirect_url

