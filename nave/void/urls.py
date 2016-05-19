from django.conf.urls import url

from void import views
from .oaipmh import DjangoOAIProvider, ElasticSearchOAIProvider
from .views import VoidListView, ImageRedirectView, DataSetStatisticsView

urlpatterns = [
    url(r'^void.ttl$', VoidListView.as_view(), name='void'),
    url(r'^api/index/bulk/$', views.bulk_api, name='bulk_api'),
    url(r'^api/index/narthex/toggle/proxyfield/$', views.toggle_proxy_field, name='toggle_proxy_field'),
    url(r'^api/index/narthex/toggle/proxymapping/$', views.toggle_proxy_mapping, name='toggle_proxy_mapping'),
    # todo replace with ElasticSearch pmh provider
    url(r'^api/oai-pmh/$', DjangoOAIProvider.as_view(), name='dataset_oai'),
    url(r'^api/es-oai-pmh/$', ElasticSearchOAIProvider.as_view(), name='es_dataset_oai'),
    url(r'^resolve/(?P<link>(.*))$', ImageRedirectView.as_view(),),
    url(r'^statistics/datasets/$', DataSetStatisticsView.as_view())

    ]
