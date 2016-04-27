# -*- coding: utf-8 -*- 
from django.conf.urls import *  # NOQA

from . import views

urlpatterns = patterns(
    '',
    url(r'^vc/(?P<slug>([^/]*?))/search/$', views.VirtualCollectionSearchView.as_view(),
        name="virtual_collection_search"),
    url(r'^vc/(?P<slug>([^/]*?))/$', views.VirtualCollectionDetailView.as_view(),
        name="virtual_collection_detail"),

    # url for api
    # url for oai-pmh
)
