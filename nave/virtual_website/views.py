import logging

from django.conf import settings
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, TemplateView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework_jsonp.renderers import JSONPRenderer

from nave.search.renderers import XMLRenderer

from nave.search.views import SearchListAPIView

from nave.search.search import NaveESQuery
from nave.void.oaipmh import ElasticSearchOAIProvider
from .models import VirtualWebsite, VirtualWebsitePage

logger = logging.getLogger(__name__)


# @login_required
class VirtualWebsiteDetailView(DetailView):
    template_name = 'virtual_website/landing_page.html'
    context_object_name = 'vw'
    model = VirtualWebsite

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(VirtualWebsiteDetailView, self).get_context_data(**kwargs)
        return context


class VirtualWebsiteSearchView(SearchListAPIView):
    template_name = "virtual_website/search_page.html"
    renderer_classes = (TemplateHTMLRenderer, JSONRenderer, JSONPRenderer, XMLRenderer)

    def get(self, request, *args, **kwargs):
        slug = kwargs.get('slug', None)
        virtual_website = get_object_or_404(VirtualWebsite, slug=slug)

        self.set_hidden_query_filters(virtual_website.query.split(";;;"))
        return super().get(request, *args, **kwargs)


class V1SearchListApiView(SearchListAPIView):
    default_converter = settings.DEFAULT_V1_CONVERTER
    doc_types = []

    def get(self, request, *args, **kwargs):
        slug = kwargs.get('slug', None)
        virtual_website = get_object_or_404(VirtualWebsite, slug=slug)

        self.set_hidden_query_filters(virtual_website.query.split(";;;"))
        return super().get(request, *args, **kwargs)


class VirtualWebsitePmhProvider(ElasticSearchOAIProvider):

    def get_dataset_list(self):
        return []

    def get(self, request, *args, **kwargs):
        slug = kwargs.get('slug', None)
        virtual_website = get_object_or_404(VirtualWebsite, slug=slug)
        hidden_query_filters = [hqf.strip('"') for hqf in virtual_website.query.split(";;;")]
        query = NaveESQuery(
            index_name=settings.SITE_NAME,
            doc_types=[],
            hidden_filters=hidden_query_filters
        )
        self.query = query.build_query_from_request(request=request)
        return super(VirtualWebsitePmhProvider, self).get(request, *args, **kwargs)

class VirtualWebsitePageView(DetailView):
    template_name = 'virtual_website/cms_page.html'
    context_object_name = 'vwp'
    model = VirtualWebsitePage

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(VirtualWebsitePageView, self).get_context_data(**kwargs)
        return context

# TODO add correct mime-type
class VirtualWebsitePages(DetailView):
    template_name = 'virtual_website/pages.json'
    context_object_name = 'vw'
    model = VirtualWebsite

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(VirtualWebsiteDetailView, self).get_context_data(**kwargs)
        return context


# TODO add correct mime-type
class VirtualWebsiteCSS(DetailView):
    template_name = 'virtual_website/diw.css'
    context_object_name = 'vw'
    model = VirtualWebsite

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(VirtualWebsiteDetailView, self).get_context_data(**kwargs)
        return context


# TODO add correct mime-type
class VirtualWebsiteConfig(DetailView):
    template_name = 'virtual_website/diw-config.js'
    context_object_name = 'vw'
    model = VirtualWebsite

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(VirtualWebsiteDetailView, self).get_context_data(**kwargs)
        return context
