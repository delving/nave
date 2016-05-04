from django.conf.urls import url

from void import views
from void.oaipmh import OAIProvider
from .views import VoidListView, ImageResolveRedirectView

urlpatterns = [
    url(r'^void.ttl$', VoidListView.as_view(), name='void'),
    url(r'^api/index/bulk/$', views.bulk_api, name='bulk_api'),
    url(r'^api/index/narthex/toggle/proxyfield/$', views.toggle_proxy_field, name='toggle_proxy_field'),
    url(r'^api/index/narthex/toggle/proxymapping/$', views.toggle_proxy_mapping, name='toggle_proxy_mapping'),
    url(r'^api/oai-pmh/$', OAIProvider.as_view(), name='dataset_oai'),
    url(r'^resolve/(?P<link>(.*))$', ImageResolveRedirectView.as_view(),),

    ]
