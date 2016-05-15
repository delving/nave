from django.conf import settings
from django.conf.urls import url, include
from django.views.generic import TemplateView
from rest_framework import routers

from lod.viewsets import CacheResourceViewSet
from search.viewsets import GroupViewSet
from search.viewsets import UserViewSet, OauthTokenViewSet
from .views import DetailResultView, FoldOutDetailImageView, \
    LegacyAPIRedirectView, SearchListHTMLView, LodRelatedSearchHTMLView, V1SearchListApiView, \
    V2SearchListApiView, BigDownloadView, KNReiseGeoView

router = routers.DefaultRouter(trailing_slash=True)
router.register(r'search/v1', V1SearchListApiView, base_name='v1-list')
router.register(r'search/v2', V2SearchListApiView, base_name='v2-list')
router.register(r'users', UserViewSet)
router.register(r'token-user', OauthTokenViewSet)
router.register(r'groups', GroupViewSet)
router.register('cacheresources', CacheResourceViewSet, base_name='cache_resource')


search_router = routers.SimpleRouter(trailing_slash=True)
search_router.register(r'search/?', SearchListHTMLView, base_name='results')
search_router.register(r'search-lod-related/?', LodRelatedSearchHTMLView, base_name='lod-results')


# Wire up our API using automatic URL routing.
urlpatterns = [
    # redirect
    url(r'^api/search/$', LegacyAPIRedirectView.as_view(), name='api_redirect'),
    url(r'^organizations/.*?/api/search$', LegacyAPIRedirectView.as_view(), name='api_redirect'),
    url(r'^api/download/task/(?P<id>(.*))/$', BigDownloadView.as_view(), name='big_download'),
    url(r'^detail/foldout/(?P<doc_type>([^/]*))/(?P<slug>(.*?))/?$', DetailResultView.as_view(), name='results_detail_foldout'),
    url(r'^detail/(?P<slug>(.*))$', DetailResultView.as_view(template_name="search-detail.html"), name='result_detail'),
    url(r'^detail/fold-out/(?P<slug>(.*))$', DetailResultView.as_view(), name='results_detail_foldout'),
    url(r'^detail/foldout/image/(?P<slug>(.*))$', FoldOutDetailImageView.as_view(), name='image_detail'),
    # url(r'^proxy/$', 'dataset.views.proxy', name='proxy'),
    url(r'/?', include(search_router.urls), name='search_routers'),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^geoviewer/$', KNReiseGeoView.as_view()),
]
