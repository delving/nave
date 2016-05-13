import logging
from urllib.parse import unquote

from django.conf import settings
from django.views.generic import ListView, RedirectView
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
            delete = True if delete_string.lower() in ['true'] else False
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
            delete = True if delete_string.lower() in ['true'] else False
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

