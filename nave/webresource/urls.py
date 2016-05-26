"""
Note:

    Make sure this url configuration is included in your main configuration
    as follows:

    url(r'^', include('webresource.urls')),
"""
from django.conf.urls import *  # NOQA

from . import views

urlpatterns = patterns(
    '',
    url(r'api/webresource/$', views.WebResourceRedirectView.as_view(),
        name="webresource"),
    url(r'api/webresource/_docs/$', views.webresource_docs, name="webresource_docs")
    # todo: include the references to statistics as well
    # for example _statistics _docs etc
)
