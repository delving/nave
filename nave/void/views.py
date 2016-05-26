import logging
from urllib.parse import unquote

from django.conf import settings
from django.core.urlresolvers import resolve, reverse
from django.views.generic import ListView, RedirectView, TemplateView
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from void import tasks
from void.models import ProxyResourceField, ProxyMapping
from void.parsers import PlainTextParser
from void.processors import BulkApiProcessor


logger = logging.getLogger(__name__)


@api_view(['PUT', 'POST'])
@authentication_classes((SessionAuthentication, BasicAuthentication, TokenAuthentication))
@parser_classes((PlainTextParser,))
@permission_classes((IsAuthenticated,))
def bulk_api(request):
    if request.method in ['PUT', 'POST']:
        content = request.data
        if not settings.BULK_API_ASYNC:
            processor = BulkApiProcessor(content)
            return Response(processor.process(), status=status.HTTP_201_CREATED)
        tasks.process_bulk_api_request.delay(content)
        return Response({'status': "ok"}, status=status.HTTP_201_CREATED)


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


class DataSetStatisticsView(TemplateView):
    template_name = "statistics.html"
    total_records = 0

    from collections import namedtuple
    NarthexDataSet = namedtuple('NarthexDataSet', ['spec', 'record_count', 'invalid', 'valid', 'es_count', 'deleted'])

    def get_narthex_datasets(self):
        from SPARQLWrapper import SPARQLWrapper, JSON
        endpoint = self.request.build_absolute_uri(reverse('proxy'))

        sparql = SPARQLWrapper(endpoint)
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
        from elasticsearch import Elasticsearch
        from elasticsearch_dsl import Search, A
        client = Elasticsearch(hosts=settings.ES_URLS)
        s = Search(using=client)
        a = A('terms', field='delving_spec.raw', size=500)
        s.aggs.bucket('delving_spec', a)
        response = s.execute()
        self.total_records = response.hits.total
        return response.aggregations.delving_spec.buckets

    def get_spec_list(self):
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
                print("Spec {} missing in Narthex".format(spec.key))
            spec_list[spec_name] = dataset._replace(es_count=spec.doc_count)
        return spec_list

    def get_context_data(self, **kwargs):
        context = super(DataSetStatisticsView, self).get_context_data(**kwargs)
        spec_list = self.get_spec_list()
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
            'total_records': {'count': self.total_records, 'values': None},
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


class ImageResolveRedirectView(RedirectView):
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

