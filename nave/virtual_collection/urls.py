# -*- coding: utf-8 -*- 
from django.conf.urls import *  # NOQA
from rest_framework import routers

from . import views

vc_router = routers.SimpleRouter(trailing_slash=True)
vc_router.register(r'vc/(?P<slug>([^/]*?))/search/$', views.VirtualCollectionSearchView, base_name='results')
vc_router.register(r'vc/(?P<slug>([^/]*?))/api/$', views.SearchListAPIView, base_name='api-results')


urlpatterns = patterns(
    '',
    url(r'^vc/(?P<slug>([^/]*?))/search/$', views.VirtualCollectionSearchView.as_view({'get': 'get'}),
         name="virtual_collection_search"),
    url(r'^vc/(?P<slug>([^/]*?))/api/$', views.V1SearchListApiView.as_view({'get': 'list'}),
        name="virtual_collection_api"),
    url(r'^vc/(?P<slug>([^/]*?))/$', views.VirtualCollectionDetailView.as_view(),
        name="virtual_collection_detail"),
    # url(r'', include(vc_router.urls), name='vc_routers'),
    # url for oai-pmh
)
