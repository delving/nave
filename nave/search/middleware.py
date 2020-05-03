"""Middleware to log API request and response info to ElasticSearch.

The logged information can be used for Kibana Dashboards.
"""

import logging

from django.conf import settings
from datetime import datetime
from elasticsearch_dsl import DocType, Date, Text, Nested

from nave.search.views import SearchListAPIView

logger = logging.getLogger(__name__)


class APIEntry(DocType):
    """Persistence entry for API logging to ElasticSearch.
    created_at =
    host =
    nave_version =
    hub3_project hash =
    request_path =
    request_type = detail or search


    Requestor:
        ip
        google analytics meta
        google analytics request id

    Request:
        meta:
            paging: boolean
            filtered: boolean
            fielded_query: boolean
            geosearch: boolean
        query_params:
            request dict
        facet:
            facet_field
            facet_value
        query_string

    Response:
        records found
        dataprovider => list (loop)
        contentprovider => list (loop)
        spec => name
        europeana type
        dc_subject => list
        has image
        has point

    oauth protection same as narthex via nginx

    """

    created_at = Date()
    # paging = Boolean()
    raw_query = Text()

    query_params = Nested()
    requestor = Nested()
    request = Nested()
    response = Nested()

    class Meta:
        index = "{}_apilog".format(settings.ORG_ID)

    def save(self, ** kwargs):
        self.created_at = datetime.now()
        return super().save(** kwargs)


APIEntry.init()


class APILoggingMiddleware(object):
    """Middleware to log API requests."""

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Only log information for subclass of 'SearchListAPIView'
        if not hasattr(response, 'render_context'):
            return response

        if issubclass(response.renderer_context['view'].__class__, SearchListAPIView):

            entry = APIEntry() # query_params=request.GET.lists()
            entry.query_params = dict(request.GET.lists())
            # switch between django response and DRF response
            # entry.total_result = response.data.get('result')['pagination']['numFound']
            entry.raw_query = '{}'.format(request.GET.urlencode())
            entry.save()

        # Code to be executed for each request/response after
        # the view is called.

        return response
