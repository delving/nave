import logging

from django.conf import settings
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, TemplateView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework_jsonp.renderers import JSONPRenderer

from search.renderers import XMLRenderer

from search.views import SearchListAPIView

from .models import VirtualCollection

logger = logging.getLogger(__name__)


# @login_required
class VirtualCollectionDetailView(DetailView):
    template_name = 'virtual_collection/landing_page.html'
    context_object_name = 'vc'
    model = VirtualCollection

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(VirtualCollectionDetailView, self).get_context_data(**kwargs)
        return context


class VirtualCollectionSearchView(SearchListAPIView):
    template_name = "virtual_collection/search_page.html"
    renderer_classes = (TemplateHTMLRenderer, JSONRenderer, JSONPRenderer, XMLRenderer)

    def get(self, request, *args, **kwargs):
        slug = kwargs.get('slug', None)
        virtual_collection = get_object_or_404(VirtualCollection, slug=slug)
        self.set_hidden_query_filters(virtual_collection.query.split(";;;"))
        return super().get(request, *args, **kwargs)


class V1SearchListApiView(SearchListAPIView):
    default_converter = settings.DEFAULT_V1_CONVERTER
    doc_types = ["void_edmrecord"]


