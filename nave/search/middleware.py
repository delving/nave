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
    """Persistence entry for API logging to ElasticSearch."""

    created_at = Date()
    # paging = Boolean()
    raw_query = Text()

    query_params = Nested()

    class Meta:
        index = "{}_apilog".format(settings.SITE_NAME)

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
        if issubclass(response.renderer_context['view'].__class__, SearchListAPIView):

            entry = APIEntry() # query_params=request.GET.lists()
            entry.query_params = dict(request.GET.lists())
            entry.raw_query = '{}'.format(request.GET.urlencode())
            entry.save()

        # Code to be executed for each request/response after
        # the view is called.

        return response
