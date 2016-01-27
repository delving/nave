from django.conf.urls import *


urlpatterns = patterns(
    '',
    url(r'', include('health_check.urls')),
)
