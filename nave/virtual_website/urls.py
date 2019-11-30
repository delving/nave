# -*- coding: utf-8 -*-
from django.conf.urls import url
from rest_framework import routers

from . import views

vc_router = routers.SimpleRouter(trailing_slash=True)
vc_router.register(r'vc/(?P<slug>([^/]*?))/search/$', views.VirtualWebsiteSearchView, base_name='results')
vc_router.register(r'vc/(?P<slug>([^/]*?))/api/$', views.SearchListAPIView, base_name='api-results')
# TODO add serializer for pages


urlpatterns = [
    url(r'^vw/(?P<slug>([^/]*?))/search/$', views.VirtualWebsiteSearchView.as_view({'get': 'get'}),
         name="virtual_website_search"),
    # todo test if this search api returns the right information
    url(r'^vw/(?P<slug>([^/]*?))/api/$', views.V1SearchListApiView.as_view({'get': 'get'}),
        name="virtual_website_api"),
    url(r'^vw/(?P<slug>([^/]*?))/$', views.VirtualWebsiteDetailView.as_view(),
        name="virtual_website_detail"),
    # url(r'', include(vc_router.urls), name='vc_routers'),
    url(r'^vw/(?P<slug>([^/]*?))/oai-pmh/$', views.VirtualWebsitePmhProvider.as_view(),
        name="virtual_website_pmh"),
    url(r'^vw/(?P<slug>([^/]*?))/diw.css$', views.VirtualWebsiteCSS.as_view(),
        name="virtual_website_css"),
    url(r'^vw/(?P<slug>([^/]*?))/diw-config.js$', views.VirtualWebsiteConfig.as_view(),
        name="virtual_website_config"),
    url(r'^vw/(?P<slug>([^/]*?))/pages.json$', views.VirtualWebsitePages.as_view(),
        name="virtual_website_pages"),
    url(r'^vw/pages/$(?P<slug>([^/]*?))', views.VirtualWebsitePageView.as_view(),
        name="virtual_website_pages")
]
