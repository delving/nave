from django.conf.urls import *

from .views import DiwInstanceView, DiwConfigView, DiwDownload


urlpatterns = patterns(
    '',
    url(r'diw/(?P<slug>(.*))/$', DiwInstanceView.as_view(), name='diw_instance'),
    url(r'diw/(?P<slug>(.*))/config.js', DiwConfigView.as_view(), name='diw_config'),
    url(r'diw/(?P<slug>(.*))/download', DiwDownload.as_view(), name='diw_download'),
)
