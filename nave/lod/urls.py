# -*- coding: utf-8 -*- 
"""
This module contains all the routing rules for the Linked Open Data app.
"""
from django.conf import settings
from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from . import RDF_SUPPORTED_EXTENSIONS
from .views import SnorqlTemplateView, remote_sparql, LoDRedirectView, LoDDataView, LoDHTMLView, remote_sparql_test, \
    PropertyTemplateView, EDMHTMLMockView, HubIDRedirectView, UserGeneratedContentList, UserGeneratedContentDetail

RDF_SUPPORTED_FORMATS = "|".join(RDF_SUPPORTED_EXTENSIONS)

urlpatterns = patterns("",
                       url(r'^lod-detail/?$', EDMHTMLMockView.as_view()),
                       url(r'^lod/statistics/$', TemplateView.as_view(template_name="lod_statistics.html")), #  mocked

                       url(r'^(?P<namespace>(.*?))/ns/(?P<label>(.*)$)', PropertyTemplateView.as_view(), name="properties"),
                       url(r'snorql/$', SnorqlTemplateView.as_view(), name="snorql_main"),
                       url(r'^sparql/$', remote_sparql, name='proxy'),
                       url(r'^sparql_test/$', remote_sparql_test),
                       url(r'^relfinder/$', TemplateView.as_view(template_name='relfinder.html'), name='relfinder'),

                       # hubId
                       url(r'^resolve/(?P<doc_type>(.*?))/(?P<hubId>(.*?))/$', HubIDRedirectView.as_view()),
                       url(r'^api/resolve/(?P<doc_type>(.*?))/(?P<hubId>(.*?))/$', HubIDRedirectView.as_view()),
                       url(r'^api/resolve/(?P<hubId>(.*?))/?$', HubIDRedirectView.as_view()),
                       url(r'^{}/(?P<spec>(.*))/(?P<local_id>(.*))$'.format(settings.ORG_ID), HubIDRedirectView.as_view(), name='hub_id_redirect'),

                       # redirects
                       url(r'^resource/(?P<type_>(.*))/(?P<label>(.*))\.(?P<extension>({}))$'.format(
                           RDF_SUPPORTED_FORMATS), LoDRedirectView.as_view()),
                       url(r'^resource/(?P<type_>(.*))/(?P<label>(.*))$', LoDRedirectView.as_view(),
                           name="typed_lod_resource_page"),
                       url(r'^resource/(?P<type_>(.*))/(?P<label>(.*))$', LoDRedirectView.as_view()),
                       url(r'^resource/(?P<label>(.*))$', LoDRedirectView.as_view()),
                       url(r'^resource/(?P<label>(.*))\.(?P<extension>({}))$'.format(RDF_SUPPORTED_FORMATS),
                           LoDRedirectView.as_view()),
                       url(r'^page/(?P<label>(.*))\.(?P<extension>({}))$'.format(RDF_SUPPORTED_FORMATS),
                           LoDRedirectView.as_view()),
                       url(r'^page/(?P<type_>(.*))/(?P<label>(.*))\.(?P<extension>({}))$'.format(RDF_SUPPORTED_FORMATS),
                           LoDRedirectView.as_view()),
                       url(r'^data/(?P<type_>(.*))/(?P<label>([^\.]*))$', LoDRedirectView.as_view()),
                       url(r'^data/(?P<label>([^\.]*))$', LoDRedirectView.as_view()),

                       # edm page view  (only for direct view)
                       url(r'page/aggregation/(?P<label>(.*))$',
                           LoDHTMLView.as_view(),
                           name="edm_lod_page_detail"),

                       # page views
                       url(r'^page/(?P<type_>(.*))/(?P<label>(.*))$',
                           LoDHTMLView.as_view(),
                           name="typed_lod_page_detail"),
                       url(r'^page/(?P<label>(.*))$',
                           LoDHTMLView.as_view(),
                           name="lod_page_detail"),


                       # data views
                       url(r'^data/(?P<type_>(.*))/(?P<label>(.*))\.(?P<extension>({}))$'.format(RDF_SUPPORTED_FORMATS),
                           LoDDataView.as_view(),
                           name="typed_lod_data_detail"),
                       url(r'^data/(?P<label>(.*))\.(?P<extension>({}))$'.format(RDF_SUPPORTED_FORMATS),
                           LoDDataView.as_view(),
                           name="lod_data_detail"),
                       # /schema
                       #url(r'^schema\.(?P<extension>(.*))$', LoDHTMLView.as_view(), name="rdf_schema"),
                       #url(r'^schema)$', LoDHTMLView.as_view(), name="rdf_schema_data"),
                       # /resource/class/id

                       url(r'^api/enrich/ugc/$', UserGeneratedContentList.as_view()),
                       url(r'^api/enrich/ugc/(?P<pk>[0-9]+)/$', UserGeneratedContentDetail.as_view()),
)
