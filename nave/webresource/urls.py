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
        url(r'api/webresource_$', views.WebResourceRedirectView.as_view(),
            name="webresource"),
        # todo: include the references to statistics as well
        # for example _statistics _docs etc
        )
